#!/usr/bin/env bash
# Ensayo offline (Linux, banco Docker) de la propagación de errores de s50_analisis_e4.sh y r4.sh (defecto 4).
#   bash ensayo_errores_s50_r4.sh <dir_guiones> [<dir_guiones_antiguos>]
# Herramientas FALSAS (escriben su salida o fallan si su nombre está en FALLA), datos mínimos y un ssh FALSO que
# ejecuta en local la orden remota (cadena portátil -> bastión -> sensor de r4). Con <dir_guiones_antiguos> (los de
# d3464bf) muestra el defecto: la versión anterior devuelve rc=0 y escribe SHA256SUMS con pasos fallidos.
set -u
G=${1:?dir de guiones}; GA=${2:-}
T=$(mktemp -d); OUT=${OUT:-/out}; mkdir -p "$OUT"; LOG=$OUT/ensayo-errores-s50-r4.txt; : > "$LOG"
say() { echo "$*" | tee -a "$LOG"; }
fallo=0
ok() { if eval "$2"; then say "OK    $1"; else say "FALLO $1"; fallo=1; fi; }

preparar() {   # HOME nuevo con herramientas falsas y copias mínimas
  export HOME=$T/h-$1; local H=$HOME/cf-e4/herramientas E=$HOME/cyberflow-e4/ec78ca5/scripts/etapa4
  local B=$HOME/cf-e4/$2; local C=$B/copias
  mkdir -p "$H" "$E" "$HOME/cyberflow/.venv/bin" "$B/salud" "$B/eve" "$C/feed-v2" "$B/estado-inicial" "$B/replay" "$B/archivo-pcap"
  ln -sf "$(command -v python3)" "$HOME/cyberflow/.venv/bin/python"
  cat > "$H/falsa.py" <<'PY'
import os, sys
n = os.path.basename(sys.argv[0])
if n in os.environ.get("FALLA", "").split(","):
    sys.exit(f"{n}: fallo inducido")
a = sys.argv[1:]
v = lambda k: a[a.index(k) + 1] if k in a else None
if n == "analizar_3b.py":
    os.makedirs(v("--salida"), exist_ok=True); open(os.path.join(v("--salida"), "analisis-3b.json"), "w").write("{}\n")
else:
    for k in ("--salida", "--salida-csv", "--salida-json"):
        if v(k):
            open(v(k), "w").write("{}\n")
    if v("--salida-dir"):
        os.makedirs(v("--salida-dir"), exist_ok=True)
        open(os.path.join(v("--salida-dir"), "descriptor-integridad.json"), "w").write("{}\n")
print(n, "ok")
PY
  for f in control_4b.py extraer_evidencia_destino.py calidad_fuentes.py recalcular_caracteristicas.py \
           generar_respaldos.py verificar_integridad.py analizar_3b.py referencia_trafico_4c.py; do cp "$H/falsa.py" "$H/$f"; done
  rm "$H/falsa.py"
  cat > "$H/analizar.py" <<'PY'
import json
def leer_marcas(p):
    eps = {}
    for l in open(p):
        r = json.loads(l)
        if r.get("evento") == "inicio": eps[r["episodio_id"]] = {"inicio_ep": 100.0, "fin_ep": None}
        if r.get("evento") == "fin": eps[r["episodio_id"]]["fin_ep"] = 200.0
    return eps, None
PY
  echo '{}' > "$H/config-campana-4c.json"; echo '{}' > "$H/escenarios-4c.json"
  ( cd "$H" && sha256sum *.py *.json > herramientas-e4.sha256 )
  cat > "$E/salud_captura.py" <<'PY'
import json, os, sys
CRITERIOS = {}
def leer_tcpdump_log(p): return []
def clasificar(incs, td, d, f, crit): return {"clase": "C0", "motivos": []}
if __name__ == "__main__":
    if sys.argv[1] in os.environ.get("FALLA", "").split(","):
        raise RuntimeError("fallo inducido en " + sys.argv[1])          # excepción de Python
    if sys.argv[1] == "intervalos":
        open(sys.argv[3], "w").write('{"t": 1}\n')
    else:
        print(json.dumps({"clase": "C0"}))
PY
  cp "$E/salud_captura.py" "$E/trafico_observado.py"
  sed -i 's/^if __name__ == "__main__":/if __name__ == "__main__" and "trafico" not in sys.argv[0]:/' "$E/trafico_observado.py"
  printf 'import sys\na = sys.argv[1:]\nopen(a[a.index("--salida") + 1], "w").write("{}\\n")\n' >> "$E/trafico_observado.py"
  ( cd "$HOME/cyberflow-e4/ec78ca5" && find scripts -type f | sort | xargs sha256sum > SHA256SUMS )
  echo '{"t": 1}' > "$B/salud/muestras.jsonl"; : > "$B/salud/tcpdump-anillo.log"; : > "$B/salud/tcpdump-via.log"
  printf '{"evento":"inicio","episodio_id":"x-r1"}\n{"evento":"fin","episodio_id":"x-r1"}\n' > "$C/marcas.jsonl"
  echo '{"t": 1000}' > "$B/eve/inicio.json"; echo 1 > "$B/estado-inicial/arranque-motor.t"
  printf 'Date: 11/2/2026 -- 19:10:00 (uptime: 0d, 00h 10m 00s)\ncapture.kernel_packets | Total | 10\ncapture.kernel_drops | Total | 0\n' > "$C/stats-fin.log"
  : > "$C/motor_decision.log"
}
s50() { bash "$1/s50_analisis_e4.sh" "$2" 2026-11-02T10:00:00Z 2026-11-02T11:00:00Z 2026-11-02T10:10:00Z 2026-11-02T10:40:00Z; }
estado() { awk -F'\t' -v p="$2" '$1==p{e=$2} END{print e}' "$HOME/cf-e4/$1/analisis/ESTADO-PASOS.tsv"; }

say "## s50 corregido ($(sha256sum "$G/s50_analisis_e4.sh" | cut -c1-16)…)"
preparar ok 4c; s50 "$G" 4c > "$T/o1" 2>&1; rc=$?
A=$HOME/cf-e4/4c/analisis
ok "S1 ejecución correcta 4c: rc=0, SHA256SUMS «COMPLETO», sin PARCIAL" \
   "[ $rc = 0 ] && head -1 $A/SHA256SUMS | grep -q '^# COMPLETO' && [ ! -e $A/SHA256SUMS.PARCIAL ]"
cp "$A/ESTADO-PASOS.tsv" "$OUT/s1-ESTADO-PASOS.tsv"
ok "S2 sin REANUDAR y con análisis existente: PARAR (rc=2)" "s50 '$G' 4c > /dev/null 2>&1; [ \$? = 2 ]"
echo manipulado >> "$A/incrementos.jsonl"
ok "S3 reanudar con una salida OK alterada: PARAR (rc=2), no se reutiliza ni se sobrescribe" \
   "REANUDAR=1 s50 '$G' 4c > $T/o3 2>&1; [ \$? = 2 ] && grep -q alteradas $T/o3 && tail -1 $A/incrementos.jsonl | grep -q manipulado"

preparar f4 4c; FALLA=recalcular_caracteristicas.py s50 "$G" 4c > "$T/o4" 2>&1; rc=$?
A=$HOME/cf-e4/4c/analisis
ok "S4 fallo inducido en el paso 4 (Python sale con 1): rc=1" "[ $rc = 1 ]"
ok "S4 dependientes 5, 6, c y 9 omitidos; independientes 7 y 8 hechos" \
   "[ \$(estado 4c 4) = fallo ] && [ \$(estado 4c 5) = omitido_dependencia ] && [ \$(estado 4c 6) = omitido_dependencia ] && [ \$(estado 4c c) = omitido_dependencia ] && [ \$(estado 4c 9) = omitido_dependencia ] && [ \$(estado 4c 7) = ok ] && [ \$(estado 4c 8) = ok ]"
ok "S4 manifiesto PARCIAL etiquetado y SIN SHA256SUMS completo; salidas parciales conservadas" \
   "[ ! -e $A/SHA256SUMS ] && head -1 $A/SHA256SUMS.PARCIAL | grep -q '^# PARCIAL' && grep -q 'NO es el resultado' $A/PARCIAL.txt && [ -e $A/recalculo.stderr ]"
cp "$A/ESTADO-PASOS.tsv" "$OUT/s4-ESTADO-PASOS.tsv"; cp "$A/PARCIAL.txt" "$OUT/s4-PARCIAL.txt"
REANUDAR=1 s50 "$G" 4c > "$T/o5" 2>&1; rc=$?
ok "S5 reanudación tras corregir: rc=0, pasos OK reutilizados y verificados, el 4 repetido, COMPLETO" \
   "[ $rc = 0 ] && [ \$(estado 4c a1) = reutilizado ] && [ \$(estado 4c 4) = ok ] && [ \$(estado 4c 9) = ok ] && head -1 $A/SHA256SUMS | grep -q '^# COMPLETO' && [ ! -e $A/SHA256SUMS.PARCIAL ]"
ok "S5 las salidas del intento fallido quedan apartadas en .fallidos/ (no se sobrescriben)" \
   "ls -d $A/.fallidos/4-* > /dev/null 2>&1 && [ -e \$(ls -d $A/.fallidos/4-* | head -1)/recalculo.stderr ]"
cp "$A/ESTADO-PASOS.tsv" "$OUT/s5-ESTADO-PASOS-reanudado.tsv"

preparar fa1 4c; FALLA=intervalos s50 "$G" 4c > "$T/o6" 2>&1; rc=$?
ok "S6 excepción de Python en a1: rc=1; a2, a3, b y 7 omitidos; c (no usa la salud) hecho; resultado PARCIAL" \
   "[ $rc = 1 ] && [ \$(estado 4c a1) = fallo ] && ( for p in a2 a3 b 7; do [ \$(estado 4c \$p) = omitido_dependencia ] || exit 1; done ) && [ \$(estado 4c c) = ok ] && grep -q 'a1=fallo' $HOME/cf-e4/4c/analisis/PARCIAL.txt && [ ! -e $HOME/cf-e4/4c/analisis/SHA256SUMS ]"
preparar f3 4c; rm "$HOME/cf-e4/4c/eve/inicio.json"; s50 "$G" 4c > "$T/o7" 2>&1; rc=$?
ok "S7 orden fallida dentro de una sustitución (inicio.json ausente) en el paso 3: rc=1, 5 omitido" \
   "[ $rc = 1 ] && [ \$(estado 4c 3) = fallo ] && [ \$(estado 4c 5) = omitido_dependencia ]"
preparar b 4b; s50 "$G" 4b > "$T/o8" 2>&1; rc=$?
ok "S8 ejecución correcta 4b: rc=0 y COMPLETO" "[ $rc = 0 ] && head -1 $HOME/cf-e4/4b/analisis/SHA256SUMS | grep -q COMPLETO"

# ---------------------------------------------------------------- r4: ssh falso que ejecuta en local
mkdir -p "$T/bin"
cat > "$T/bin/ssh" <<'EOF'
#!/usr/bin/env bash
# ssh falso: ignora opciones y destino; ejecuta en local la orden remota (último argumento) con el stdin recibido
[ -n "${FAKE_SSH_RC:-}" ] && { cat > /dev/null; echo "ssh: connect to host x: Connection timed out" >&2; exit "$FAKE_SSH_RC"; }
cmd="${@: -1}"; exec bash -c "$cmd"
EOF
chmod +x "$T/bin/ssh"
R=$T/r4; mkdir -p "$R"; cp "$G/r4.sh" "$R/"; cp "$G/s50_analisis_e4.sh" "$R/"
printf '#!/usr/bin/env bash\necho hola; exit "${1:-0}"\n' > "$R/eco.sh"
r4() { PATH="$T/bin:$PATH" bash "$1/r4.sh" "${@:2}"; }
say "## r4 corregido"
ok "R1 guion remoto rc=0 -> r4 rc=0 y línea final '## r4 rc=0'" "r4 $R eco.sh bastion 0 > /dev/null; [ \$? = 0 ] && tail -1 $R/out_eco_0.txt | grep -q 'r4 rc=0'"
ok "R2 guion remoto rc=3 (en el sensor, a través del bastión) -> r4 rc=3" "r4 $R eco.sh sensor 3 > /dev/null; [ \$? = 3 ]"
ok "R3 fallo de conexión SSH (255) -> r4 rc=255" "FAKE_SSH_RC=255 r4 $R eco.sh bastion 0 > /dev/null; [ \$? = 255 ]"
preparar r4 4c
ok "R4 cadena completa r4 -> bastión -> sensor -> s50 con paso fallido: rc=1 en el portátil" \
   "FALLA=analizar_3b.py r4 $R s50_analisis_e4.sh sensor 4c 2026-11-02T10:00:00Z 2026-11-02T11:00:00Z 2026-11-02T10:10:00Z 2026-11-02T10:40:00Z > /dev/null; [ \$? = 1 ]"

if [ -n "$GA" ]; then
  say "## versiones anteriores (d3464bf): el defecto"
  preparar viejo 4c; FALLA=recalcular_caracteristicas.py bash "$GA/s50_analisis_e4.sh" 4c 2026-11-02T10:00:00Z 2026-11-02T11:00:00Z 2026-11-02T10:10:00Z 2026-11-02T10:40:00Z > "$T/o9" 2>&1; rc=$?
  A=$HOME/cf-e4/4c/analisis
  ok "V1 s50 anterior con el paso 4 fallido: rc=$rc y SHA256SUMS escrito como si estuviera completo (defecto reproducido)" \
     "[ $rc = 0 ] && [ -s $A/SHA256SUMS ]"
  RA=$T/r4a; mkdir -p "$RA"; cp "$GA/r4.sh" "$RA/"; cp "$R/eco.sh" "$RA/"
  ok "V2 r4 anterior con el guion remoto rc=3: devuelve 0 (el de tee) (defecto reproducido)" \
     "r4 $RA eco.sh bastion 3 > /dev/null; [ \$? = 0 ]"
fi
say "RESULTADO: $([ $fallo = 0 ] && echo 'todas las comprobaciones OK' || echo 'HAY FALLOS')"
exit $fallo
