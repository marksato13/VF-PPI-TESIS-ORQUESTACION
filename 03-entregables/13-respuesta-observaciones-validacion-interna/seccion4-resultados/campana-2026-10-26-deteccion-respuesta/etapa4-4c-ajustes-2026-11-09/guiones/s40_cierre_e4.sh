#!/usr/bin/env bash
# shellcheck disable=SC2024  # la salida de "sudo -n journalctl" la escribe m4rk en su propio directorio: intencionado
# [SENSOR1 m4rk] ETAPA4 s40 v3 (2026-11-09) — uso: s40_cierre_e4.sh <4b|4c>. Cierre ordenado DESPUÉS de verificar las condiciones
# 1-5 (s20 + rc=0 del replay). Para el archivador (barrido final y FIN OK persistidos), el muestreador de recursos y el
# de salud (procesos propios), y copia las fuentes definitivas: motor, ciclos, Suricata, salud, journal de los dos
# tcpdump (lecturas SIGUSR1), feed v1 y v2 (traza, señales, resumen de la vía rápida, estado) y servicios.
# Sin sudo salvo journalctl (NOPASSWD). No toca motor ni servicios: se sigue en sombra.
#
# v3 (2026-11-09): las extracciones de tcpdump usan la forma permitida del sudoers (la v2 usaba `sudo -n journalctl -u … --no-pager`, que sudo
# rechaza: dejó vacíos salud/tcpdump-*.log en la 4B; se recuperó con s40b). Ver `jtcp` más abajo.
# CAMBIO RESPECTO A LA v1 (que NO comprobaba ningún cp): cada operación de copia se comprueba; antes de copiar cada fuente de
# las que crecen se anota su tamaño en copias/FUENTES-al-copiar.tsv; y SOLO si todas las copias tuvieron éxito (y cada copia es
# al menos tan grande como la fuente al empezar y empieza por los mismos bytes) se escribe copias/COPIAS-COMPLETAS.ok y se genera
# SHA256SUMS. Si algo falla: copias/COPIAS-INCOMPLETAS.txt, SIN SHA256SUMS, y sale con 1. Un SHA256SUMS ya no basta como prueba.
# Resultado esperado: "archivador rc=0", "FIN OK", 0 FALLO/PERDIDO, "COPIAS COMPLETAS", sha256sum -c del candidato sin errores,
# "--enforce en argv: ''". Parada: replay sin rc=0.
set -u
FASE=${1:?fase}
B=$HOME/cf-e4/$FASE; D=$B/archivo-pcap; C=$B/copias; E4=$HOME/cyberflow-e4/ec78ca5; F2=$HOME/feed-v2
STATS=${CF_STATS_LOG:-/var/log/suricata/stats.log}
echo "## s40-e4 $FASE $(date -u +%FT%T.%3NZ)"
grep -q '^rc=0' "$B/replay/rc.txt" 2>/dev/null || { echo "PARAR: la repetición no ha terminado con rc=0 ($(cat "$B/replay/rc.txt" 2>&1))"; exit 2; }
date +%s.%N > "$B/cierre.t"
mkdir -p "$C" || { echo "PARAR: no se puede crear $C"; exit 1; }
rm -f "$C/COPIAS-COMPLETAS.ok" "$C/COPIAS-INCOMPLETAS.txt" "$C/SHA256SUMS" "$C/FUENTES-al-copiar.tsv"
FALLOS=()
ok() { "$@" || { FALLOS+=("$*"); echo "  FALLO COPIA: $*"; }; }
P=$(cat "$D.pid"); echo "  archivador PID=$P -> TERM (barrido final)"; kill -TERM "$P"
for _ in $(seq 1 90); do [ -s "$D.rc" ] && break; sleep 1; done
echo "  archivador rc=$(cat "$D.rc" 2>/dev/null)  ESTADO: $(cat "$D/ESTADO.txt")"; tail -4 "$D/archivar.log" | sed 's/^/   | /'
echo "  pcaps archivados: $(ls "$D"/live-*.pcap | wc -l)  tamaño: $(du -sh "$D" | cut -f1)"
echo "  FALLO/PERDIDO en archivar.log: $(grep -cE ' FALLO |PERDIDO' "$D/archivar.log")"
M=$(cat "$B/recursos/muestreo.pid"); kill -TERM "$M" && echo "  muestreador de recursos $M parado ($(wc -l < "$B/recursos/muestras.jsonl") muestras)"
S=$(cat "$B/salud/muestrear.pid"); kill -TERM "$S" && echo "  muestreador de salud $S parado ($(wc -l < "$B/salud/muestras.jsonl") muestras)"
INI=$(python3 -c "import json,datetime as d;print(d.datetime.fromtimestamp(json.load(open('$B/eve/inicio.json'))['t']-120,d.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))") \
  || { FALLOS+=("calcular INI"); INI="1970-01-01 00:00:00"; }
# v3: journal de los dos tcpdump con la forma que permite el sudoers de m4rk (--no-pager PRIMERO). Se lee sin sudo (m4rk lee el journal); si eso
# falla, con `sudo -n journalctl --no-pager …`. Además el log debe traer lecturas SIGUSR1: una extracción vacía o sin «packets captured» es un FALLO.
jtcp() {  # jtcp <unidad> <salida>
  journalctl --no-pager -u "$1" --since "$INI UTC" -o short-iso-precise > "$2" 2>/dev/null \
    || sudo -n journalctl --no-pager -u "$1" --since "$INI UTC" -o short-iso-precise > "$2" || return 1
  grep -q 'packets captured' "$2"
}
ok jtcp ppi-motor-capture "$B/salud/tcpdump-anillo.log"
ok jtcp ppi-via-rapida@ens37 "$B/salud/tcpdump-via.log"
echo "  lecturas SIGUSR1: anillo $(grep -c 'packets captured' "$B/salud/tcpdump-anillo.log") / vía $(grep -c 'packets captured' "$B/salud/tcpdump-via.log")"
mkdir -p "$C/feed-v2" "$C/feed-v1" || FALLOS+=("mkdir feed")
# Fuentes que crecen: se anota su tamaño JUSTO antes de copiar y se copia una vez; la copia debe cubrir ese tamaño y empezar igual.
fuente() {  # fuente <nombre en copias/> <ruta de la fuente>
  local n=$1 f=$2 t
  t=$(stat -c %s "$f" 2>/dev/null) || { FALLOS+=("stat $f"); echo "  FALLO COPIA: no se puede leer $f"; return; }
  printf '%s\t%s\n' "$n" "$t" >> "$C/FUENTES-al-copiar.tsv"
  ok cp -p "$f" "$C/$n"
  [ "$(stat -c %s "$C/$n" 2>/dev/null || echo -1)" -ge "$t" ] && cmp -s -n "$t" "$f" "$C/$n" \
    || { FALLOS+=("copia de $n no cubre $t B"); echo "  FALLO COPIA: $n no cubre los $t B de la fuente al empezar"; }
}
fuente ciclos.jsonl "$HOME/cyberflow/logs/_state-e4/ciclos.jsonl"
fuente motor_decision.log "$HOME/cyberflow/logs/motor_decision.log"
echo "  motor_decision.log: inodo $(stat -c %i "$HOME/cyberflow/logs/motor_decision.log") (inicio: $(cat "$B/eve/motor-inicio.txt"))"
ok cp -p "$B/eve/stats-inicio.log" "$C/stats-inicio.log"; fuente stats-fin.log "$STATS"
ok cp -p "$B/recursos/muestras.jsonl" "$C/muestras.jsonl"; ok cp -p "$D/ESTADO.txt" "$C/archivador-ESTADO.txt"; ok cp -p "$D/archivar.log" "$C/archivar.log"
ok cp -p "$F2"/feed.json "$F2"/feed.sig "$F2"/estado.json "$C/feed-v2/"
for n in traza.jsonl senales-rapidas.jsonl senales-if.jsonl via-rapida-resumen.jsonl; do fuente "feed-v2/$n" "$F2/$n"; done
ok cp -p "$HOME"/feed/feed.json "$HOME"/feed/feed.sig "$HOME"/feed/estado.json "$C/feed-v1/"
ok sh -c "sha256sum '$C'/feed-v2/feed.json '$C'/feed-v2/feed.sig '$C'/feed-v2/estado.json '$C'/feed-v1/* > '$C/sha256-feed-final.txt'"
sed 's/^/  /' "$C/sha256-feed-final.txt"
S0=$(systemctl show -p ActiveEnterTimestamp --value ppi-motor)
ok sh -c "sudo -n journalctl --no-pager -u ppi-motor --since '$S0' -o short-iso > '$C/journal-motor.txt'"
ok sh -c "sudo -n journalctl --no-pager -u ppi-motor-capture -u suricata -u ppi-via-rapida@ens37 -u ppi-publicar-feed-v2 --since '$INI UTC' -o short-iso > '$C/journal-captura.txt'"
ok sh -c "sudo -n journalctl --no-pager -p warning --since '$INI UTC' -o short-iso > '$C/journal-avisos-sistema.txt'"
echo "  journal motor: $(wc -l < "$C/journal-motor.txt") líneas, trazas: $(grep -ciE 'traceback|exception' "$C/journal-motor.txt") | avisos: $(wc -l < "$C/journal-avisos-sistema.txt")"
ok sh -c "systemctl show -p Id -p MainPID -p NRestarts -p ActiveState -p ActiveEnterTimestamp ppi-motor ppi-motor-capture \
  ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata ppi-publicar-feed.timer > '$C/servicios-fin.txt'"
for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata; do
  echo "  $u $(systemctl is-active "$u") NR=$(systemctl show -p NRestarts --value "$u") PID=$(systemctl show -p MainPID --value "$u")"; done
diff <(grep -E 'MainPID|NRestarts' "$B/estado-inicial/servicios.txt") <(grep -E 'MainPID|NRestarts' "$C/servicios-fin.txt") > /dev/null \
  && echo "  servicios: mismos PID y NRestarts que al empezar" || echo "  AVISO servicios: PID o NRestarts distintos (ver servicios-fin.txt): periodo afectado = C3"
( cd "$E4" && sha256sum -c --quiet SHA256SUMS ) && echo "  candidato: SHA256SUMS OK" || echo "  AVISO candidato: SHA256SUMS con diferencias"
P=$(systemctl show -p MainPID --value ppi-motor); echo "  --enforce en argv: '$(tr '\0' ' ' < "/proc/$P/cmdline" | grep -o -- --enforce)'"
if [ "${#FALLOS[@]}" -gt 0 ]; then
  printf '%s\n' "${FALLOS[@]}" > "$C/COPIAS-INCOMPLETAS.txt"
  echo "## COPIAS INCOMPLETAS (${#FALLOS[@]} fallos, ver $C/COPIAS-INCOMPLETAS.txt): NO se genera SHA256SUMS ni COPIAS-COMPLETAS.ok; el aplazamiento NO se levanta por el camino normal"
  echo "## fin $(date -u +%FT%T.%3NZ)"; exit 1
fi
( cd "$C" && find . -type f ! -name SHA256SUMS ! -name COPIAS-COMPLETAS.ok -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS ) \
  || { echo "## FALLO al generar SHA256SUMS"; exit 1; }
echo "ok $(date -u +%FT%T.%3NZ)" > "$C/COPIAS-COMPLETAS.ok"
echo "## COPIAS COMPLETAS"; echo "## fin $(date -u +%FT%T.%3NZ)"
