#!/usr/bin/env bash
# [SENSOR1 m4rk] ETAPA4 s40b (2026-11-09) — uso: s40b_completar_copias_e4.sh <4b|4c>. Sin sudo.
# Completa UN s40 v2 que terminó con «COPIAS INCOMPLETAS» cuando lo único que falló fueron las dos extracciones del journal de
# tcpdump (salud/tcpdump-anillo.log y salud/tcpdump-via.log): el sudoers de m4rk no permite `sudo -n journalctl ... -o short-iso-precise`,
# pero el journal se lee sin sudo. NO repite nada de s40: no toca cierre.t, no para ni reinicia procesos, no vuelve a copiar fuentes.
#
# Se ejecuta UNA vez (s40b-ejecutado.txt). Solo escribe copias/COPIAS-COMPLETAS.ok y copias/SHA256SUMS si, por separado:
#   1) journalctl terminó con rc=0 para cada unidad;
#   2) cada extracción es no vacía y todas sus lecturas SIGUSR1 pertenecen a procesos del cgroup de SU unidad
#      (ppi-motor-capture -> anillo; ppi-via-rapida@ens37 -> vía rápida; el tcpdump de la vía es hijo del servicio), y los dos archivos son distintos;
#   3) cubre la ventana requerida: primera lectura <= inicio del archivo + 40 s y última >= cierre.t - 60 s;
#   4) las copias ya tomadas por s40 siguen cubriendo FUENTES-al-copiar.tsv y empiezan por los bytes de su fuente.
# Los hashes de los dos logs quedan APARTE (salud/SHA256SUMS-tcpdump), fuera de copias/SHA256SUMS. La evidencia del s40 fallido se conserva.
set -u
FASE=${1:?fase}
B=$HOME/cf-e4/$FASE; C=$B/copias; S=$B/salud; F2=$HOME/feed-v2
STATS=${CF_STATS_LOG:-/var/log/suricata/stats.log}
U_ANILLO=ppi-motor-capture; U_VIA=ppi-via-rapida@ens37
echo "## s40b $FASE $(date -u +%FT%T.%3NZ)"
parar() { echo "PARAR: $*"; exit 2; }
fallo() { echo "FALLO: $*"; FALLOS+=("$*"); }
FALLOS=()
# ---- precondiciones (nada se escribe todavía)
[ -e "$B/cierre.t" ] || parar "no hay cierre.t: s40 no se ejecutó"
[ "$(cat "$B/archivo-pcap.rc" 2>/dev/null)" = 0 ] || parar "el archivador no terminó con rc=0"
[ -e "$C/COPIAS-INCOMPLETAS.txt" ] || parar "no hay un s40 fallido que completar (falta COPIAS-INCOMPLETAS.txt)"
[ ! -e "$C/COPIAS-COMPLETAS.ok" ] && [ ! -e "$C/SHA256SUMS" ] || parar "las copias ya están declaradas completas"
[ ! -e "$C/s40b-ejecutado.txt" ] || parar "s40b ya se ejecutó una vez ($(cat "$C/s40b-ejecutado.txt"))"
[ "$(wc -l < "$C/COPIAS-INCOMPLETAS.txt")" = 2 ] && grep -q 'tcpdump-anillo.log' "$C/COPIAS-INCOMPLETAS.txt" \
  && grep -q 'tcpdump-via.log' "$C/COPIAS-INCOMPLETAS.txt" && [ "$(grep -vc -e 'tcpdump-anillo.log' -e 'tcpdump-via.log' "$C/COPIAS-INCOMPLETAS.txt")" = 0 ] \
  || parar "el s40 fallido tuvo OTROS fallos además de las dos extracciones de tcpdump: no es el caso que s40b resuelve"
[ ! -s "$S/tcpdump-anillo.log" ] && [ ! -s "$S/tcpdump-via.log" ] || parar "salud/tcpdump-*.log ya tienen contenido"
[ -s "$C/FUENTES-al-copiar.tsv" ] || parar "falta FUENTES-al-copiar.tsv"
read -r T_INI T_CIERRE < <(python3 -c "import json;print(json.load(open('$B/eve/inicio.json'))['t'], open('$B/cierre.t').read().strip())") || parar "no se pueden leer inicio.json / cierre.t"
INI=$(python3 -c "import datetime as d;print(d.datetime.fromtimestamp($T_INI-120,d.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))")
DESDE_REQ=$(python3 -c "print($T_INI+40)"); HASTA_REQ=$(python3 -c "print($T_CIERRE-60)")
pids_de() {  # PIDs del cgroup de una unidad, separados por comas (vacío si no se pueden leer)
  local cg; cg=$(systemctl show -p ControlGroup --value "$1" 2>/dev/null); [ -n "$cg" ] || return 0
  tr '\n' ',' < "${CF_CGROUP_ROOT:-/sys/fs/cgroup}${cg}/cgroup.procs" 2>/dev/null | sed 's/,$//'
}
PID_ANILLO=$(pids_de "$U_ANILLO"); PID_VIA=$(pids_de "$U_VIA")
[ -n "$PID_ANILLO" ] && [ -n "$PID_VIA" ] || parar "no se pueden leer los procesos de las unidades ($U_ANILLO='$PID_ANILLO' $U_VIA='$PID_VIA')"
[ -z "$(comm -12 <(echo "$PID_ANILLO" | tr ',' '\n' | sort) <(echo "$PID_VIA" | tr ',' '\n' | sort))" ] || parar "las dos unidades comparten procesos"
# ---- desde aquí, una sola vez
echo "$(date -u +%FT%TZ) s40b iniciado" > "$C/s40b-ejecutado.txt"
mkdir -p "$C/s40-fallido" || parar "no se puede crear copias/s40-fallido"
cp -p "$C/COPIAS-INCOMPLETAS.txt" "$C/s40-fallido/COPIAS-INCOMPLETAS.txt"
{ echo "# estado de los dos logs cuando falló s40 (antes de s40b)"; stat -c '%n %s bytes %y' "$S/tcpdump-anillo.log" "$S/tcpdump-via.log" 2>&1; echo "cierre.t=$T_CIERRE"; } > "$C/s40-fallido/estado-antes.txt"
echo "  ventana requerida: desde <= $DESDE_REQ (inicio+40 s) hasta >= $HASTA_REQ (cierre.t-60 s); INI journal '$INI UTC'; PID anillo=$PID_ANILLO vía=$PID_VIA"
VERIF=$(cat <<'PY'
import re, sys, json
f, pids_ok, desde, hasta = sys.argv[1], {int(x) for x in sys.argv[2].split(",") if x}, float(sys.argv[3]), float(sys.argv[4])
import datetime as dt
cap, parciales, pids, ts, drop_ult = 0, 0, set(), [], None
# Formato REAL (Sensor1, journalctl -o short-iso-precise): una sola línea por lectura SIGUSR1; el identificador es tcpdump[PID] en el anillo
# y bash[PID] en la vía rápida (el tcpdump de la vía es hijo del script del servicio).
pat = re.compile(r"^(\S+)\s+\S+\s+[^\s\[]+\[(\d+)\]:\s+tcpdump:\s+(\d+) packets captured, (\d+) packets received by filter, (\d+) packets dropped by kernel\s*$")
for l in open(f, encoding="utf-8", errors="replace"):
    if "packets captured" not in l:
        continue
    m = pat.match(l)
    if not m:
        parciales += 1
        continue
    cap += 1; pids.add(int(m.group(2))); ts.append(dt.datetime.fromisoformat(m.group(1)).timestamp()); drop_ult = int(m.group(5))
bad = []
if cap == 0: bad.append("sin lecturas SIGUSR1 completas")
if parciales: bad.append(f"{parciales} lecturas truncadas o con formato inesperado")
if pids and not pids <= pids_ok: bad.append(f"lecturas de PID {sorted(pids - pids_ok)} que no pertenecen a la unidad (procesos de la unidad: {sorted(pids_ok)})")
if ts and min(ts) > desde: bad.append(f"la primera lectura ({min(ts):.0f}) es posterior al inicio requerido ({desde:.0f})")
if ts and max(ts) < hasta: bad.append(f"la última lectura ({max(ts):.0f}) es anterior al fin requerido ({hasta:.0f})")
gaps = [b - a for a, b in zip(sorted(ts), sorted(ts)[1:])]
print(json.dumps({"lecturas": cap, "primera": min(ts) if ts else None, "ultima": max(ts) if ts else None,
                  "pids": sorted(pids), "descartes_ultima_lectura": drop_ult, "hueco_max_s": round(max(gaps), 1) if gaps else None}))
for b in bad: print("MOTIVO: " + b)
sys.exit(1 if bad else 0)
PY
)
extraer() {  # extraer <unidad> <nombre> <pids de la unidad, con comas>
  local u=$1 n=$2 pid=$3 tmp="$S/$2.s40b-tmp" rc
  journalctl -u "$u" --since "$INI UTC" -o short-iso-precise --no-pager > "$tmp" 2> "$tmp.err"; rc=$?
  echo "  journalctl -u $u -> rc=$rc, $(wc -c < "$tmp") bytes" | tee -a "$C/s40-fallido/extraccion.txt"
  [ "$rc" = 0 ] || { fallo "journalctl de $u terminó con rc=$rc"; return; }
  [ -s "$tmp" ] || { fallo "la extracción de $u está vacía"; return; }
  local salida; salida=$(python3 -c "$VERIF" "$tmp" "$pid" "$DESDE_REQ" "$HASTA_REQ"); local vr=$?
  echo "$salida" | sed "s/^/    [$n] /" | tee -a "$C/s40-fallido/extraccion.txt"
  [ "$vr" = 0 ] || fallo "la extracción de $u no cumple (ver MOTIVO)"
}
extraer "$U_ANILLO" tcpdump-anillo.log "$PID_ANILLO"
extraer "$U_VIA" tcpdump-via.log "$PID_VIA"
if [ -s "$S/tcpdump-anillo.log.s40b-tmp" ] && [ -s "$S/tcpdump-via.log.s40b-tmp" ] && cmp -s "$S/tcpdump-anillo.log.s40b-tmp" "$S/tcpdump-via.log.s40b-tmp"; then
  fallo "los dos logs son idénticos: no corresponden a dos unidades distintas"
fi
# ---- las copias que tomó s40 siguen cubriendo lo anotado y empiezan por los bytes de su fuente
fuente_de() { case "$1" in
  ciclos.jsonl) echo "$HOME/cyberflow/logs/_state-e4/ciclos.jsonl";; motor_decision.log) echo "$HOME/cyberflow/logs/motor_decision.log";;
  stats-fin.log) echo "$STATS";; feed-v2/*) echo "$F2/${1#feed-v2/}";; *) echo "";; esac; }
while IFS=$'\t' read -r n t; do
  f=$(fuente_de "$n"); [ -n "$f" ] || { fallo "FUENTES-al-copiar.tsv trae un nombre desconocido: $n"; continue; }
  [ "$(stat -c %s "$C/$n" 2>/dev/null || echo -1)" -ge "$t" ] && cmp -s -n "$t" "$f" "$C/$n" || fallo "la copia de $n no cubre los $t B anotados o no empieza por los bytes de su fuente"
done < "$C/FUENTES-al-copiar.tsv"
# ---- veredicto
if [ "${#FALLOS[@]}" -gt 0 ]; then
  rm -f "$S"/*.s40b-tmp "$S"/*.s40b-tmp.err
  printf '%s\n' "${FALLOS[@]}" > "$C/s40-fallido/s40b-fallos.txt"
  echo "## s40b NO COMPLETÓ (${#FALLOS[@]} fallos): no se escribió COPIAS-COMPLETAS.ok ni SHA256SUMS; los logs de salud/ quedan como estaban"
  echo "## fin $(date -u +%FT%T.%3NZ)"; exit 1
fi
mv -f "$S/tcpdump-anillo.log.s40b-tmp" "$S/tcpdump-anillo.log" && mv -f "$S/tcpdump-via.log.s40b-tmp" "$S/tcpdump-via.log" || { echo "## FALLO al instalar los logs"; exit 1; }
rm -f "$S"/*.s40b-tmp.err
( cd "$S" && sha256sum tcpdump-anillo.log tcpdump-via.log > SHA256SUMS-tcpdump ) || { echo "## FALLO al calcular los hashes de salud/"; exit 1; }
cat "$S/SHA256SUMS-tcpdump" | sed 's/^/  hash (aparte, fuera de copias\/SHA256SUMS) /'
cat > "$C/COPIAS-RECUPERADAS-s40b.txt" <<EOF
s40b $(date -u +%FT%TZ): el s40 v2 de $T_CIERRE terminó con COPIAS INCOMPLETAS por las dos extracciones de journal con sudo (ver s40-fallido/).
Se recuperaron sin sudo: salud/tcpdump-anillo.log (unidad $U_ANILLO, PID $PID_ANILLO) y salud/tcpdump-via.log (unidad $U_VIA, PID $PID_VIA).
Sus hashes están en ../salud/SHA256SUMS-tcpdump, no en SHA256SUMS de esta carpeta. cierre.t y las demás copias no se tocaron.
EOF
( cd "$C" && find . -type f ! -name SHA256SUMS ! -name COPIAS-COMPLETAS.ok -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS ) \
  || { echo "## FALLO al generar SHA256SUMS"; exit 1; }
echo "ok s40b $(date -u +%FT%T.%3NZ)" > "$C/COPIAS-COMPLETAS.ok"
echo "## COPIAS COMPLETAS (recuperadas por s40b)"; echo "## fin $(date -u +%FT%T.%3NZ)"
