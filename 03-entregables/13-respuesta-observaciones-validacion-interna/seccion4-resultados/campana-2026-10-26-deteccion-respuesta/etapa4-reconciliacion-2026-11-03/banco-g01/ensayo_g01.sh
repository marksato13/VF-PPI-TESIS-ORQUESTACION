#!/usr/bin/env bash
# Banco del lanzador g01 (reconciliación 2026-11-03). SOLO en un contenedor desechable: crea rutas bajo /home
# y procesos ficticios. Nada sale de la máquina: `ssh` es una simulación que ejecuta la orden «remota» en local
# con `bash -c` (como haría el shell remoto) y registra cada uso; el motor, el vigía, estado_sombra, c05, p10b y
# el generador son guiones inofensivos que solo imprimen y duermen. No hay tráfico de red.
#
#   bash ensayo_g01.sh <g01_original> <g01_corregido>
#
# Casos:
#   A  original, sin ningún generador            → para con «ya hay un generador» (el defecto: se cuenta a sí mismo)
#   B  corregido, sin generador                  → lanza; lista exactamente 1 PID y es el python del generador
#   C  corregido, con el generador de B vivo      → para con «ya hay un generador (pid N)» (verdadero positivo)
#   D  corregido, con señuelos (bash -c / sh -c con el patrón en el texto) y sin generador → lanza; 1 PID
set -u
ORIG=$(readlink -f "${1:?g01 original}"); NUEVO=$(readlink -f "${2:?g01 corregido}")
T=$(mktemp -d /tmp/banco-g01.XXXX); export SSH_LOG=$T/ssh.log
B=$HOME/cf-e4/4c; PQ=$HOME/cf-e4/paquete; K=/home/adminatacante/cf-e4-4c; KS=/home/adminatacante/cf-campana-A/scripts-4c
fallos=0; PIDS_FONDO=()
limpiar() { pkill -f "$T/" 2>/dev/null; pkill -f "$KS/generar_campana.py" 2>/dev/null; pkill -f "$PQ/scripts/etapa4/vigia_4c.py" 2>/dev/null; kill "${PIDS_FONDO[@]}" 2>/dev/null; true; }
trap limpiar EXIT

# --- simulaciones ------------------------------------------------------------------------------------------
mkdir -p "$T/bin" "$B" "$PQ/scripts/etapa4" "$PQ/deploy/etapa4/srvdmz" "$K" "$KS" "$T/cyberflow-e4/ec78ca5/scripts/engine"
cat > "$T/bin/ssh" <<'EOF'
#!/usr/bin/env bash
n=0
while [ $# -gt 0 ]; do case "$1" in -n) n=1; shift;; -o|-i|-S|-p|-l|-F) shift 2;; -*) shift;; *) break;; esac; done
host=$1; shift; cmd="$*"
printf '%s host=%s orden=%s\n' "$(date -u +%T)" "$host" "$(printf '%s' "$cmd" | head -c 140 | tr '\n' ' ')" >> "$SSH_LOG"
if [ $n = 1 ]; then exec bash -c "$cmd" < /dev/null; else exec bash -c "$cmd"; fi
EOF
cat > "$T/bin/systemctl" <<'EOF'
#!/usr/bin/env bash
case "$*" in
  "show -p MainPID --value ppi-motor") cat "$MOTOR_PID_F";;
  "show -p NRestarts --value ppi-motor") echo 0;;
  "is-active ppi-motor") echo active;;
  *) echo unknown; exit 3;;
esac
EOF
chmod +x "$T/bin/"*
printf 'import time\ntime.sleep(900)\n' > "$T/cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py"
python3 "$T/cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py" --model-path x --disparo eventos &
PIDS_FONDO+=($!); echo $! > "$T/motor.pid"; export MOTOR_PID_F=$T/motor.pid
echo '{"declarado": "banco"}' > "$B/control-declarado.json"
printf '#!/usr/bin/env bash\necho "  [sin credenciales, esperado 401] 401 t=0.01 (simulado)"\n' > "$HOME/cf-e4/c05_brute_prep_e4.sh"
printf '#!/usr/bin/env bash\necho "kali|desfase|<=1 s: SI (simulado)"\n' > "$HOME/cf-e4/p10b_relojes.sh"
printf 'print("estado=sombra (simulado)")\n' > "$PQ/deploy/etapa4/srvdmz/estado_sombra.py"
cat > "$PQ/scripts/etapa4/vigia_4c.py" <<'EOF'
import json, sys, time
d = sys.argv[sys.argv.index("--dir") + 1]
with open(d + "/vigia.jsonl", "a") as f:
    f.write(json.dumps({"evento": "ronda", "permiso": {"estado": "continuar", "causas": []}, "kali_rc": 0}) + "\n")
time.sleep(120)
EOF
cat > "$KS/generar_campana.py" <<'EOF'
import sys, time
print("generador SIMULADO: no lanza nada", " ".join(sys.argv[1:3]), flush=True)
time.sleep(60)
EOF
( cd "$KS" && sha256sum "$KS/generar_campana.py" > "$K/sha256-esperado.txt" )
export PATH="$T/bin:$PATH"

reiniciar() { rm -rf "$B/vigia" "$B/accesos-kali.log" "$B/brute-pre.log" "$B/relojes-4c.log" "$K/corrida" "$K/permiso.json" \
              "$K/comando.txt" "$K/lanzado.txt" "$K/generador."* "$K/terminado.txt"; }
comprobar() {  # nombre salida patrón_esperado
  if printf '%s' "$2" | grep -qE -- "$3"; then echo "OK    $1"; else echo "FALLO $1 (esperaba /$3/)"; fallos=$((fallos + 1)); fi
}
pids_listados() { printf '%s' "$1" | sed -n 's/.*pid(s) del generador: \([0-9 ]*\).*/\1/p' | xargs; }
es_generador() { tr '\0' ' ' < "/proc/$1/cmdline" | grep -qE '^python3 -u .*/generar_campana\.py --config '; }
HASTA=$(date -u -d '-1 min' +%FT%TZ)

echo "=== A: g01 ORIGINAL sin generador"
reiniciar; SA=$(bash "$ORIG" "$HASTA" srvdmz-banco 2>&1); printf '%s\n' "$SA" | sed 's/^/  | /'
comprobar "A para por el falso positivo de pgrep" "$SA" "PARAR: ya hay un generador"
if [ -e "$K/comando.txt" ] || printf '%s' "$SA" | grep -q '## lanzado'; then echo "FALLO A: lanzó"; fallos=$((fallos + 1))
else echo "OK    A no lanza nada (sin comando.txt)"; fi

echo "=== B: g01 CORREGIDO sin generador"
reiniciar; SB=$(bash "$NUEVO" "$HASTA" srvdmz-banco 2>&1); printf '%s\n' "$SB" | sed 's/^/  | /'
comprobar "B pasa la comprobación previa" "$SB" "sin generador previo"
comprobar "B lanza" "$SB" "## lanzado"
P=$(pids_listados "$SB"); n=$(wc -w <<< "$P")
[ "$n" = 1 ] && es_generador "$P" && echo "OK    B lista 1 PID ($P) y es python3 … generar_campana.py --config" \
  || { echo "FALLO B: PIDs listados «$P»"; fallos=$((fallos + 1)); }

echo "=== C: g01 CORREGIDO con el generador de B en ejecución"
rm -rf "$B/vigia"; SC=$(bash "$NUEVO" "$HASTA" srvdmz-banco 2>&1); printf '%s\n' "$SC" | sed 's/^/  | /'
comprobar "C para con el PID real del generador" "$SC" "PARAR: ya hay un generador \(pid $P ?\)"
pkill -f "$KS/generar_campana.py"; pkill -f "$PQ/scripts/etapa4/vigia_4c.py"; sleep 1

echo "=== D: g01 CORREGIDO con señuelos que contienen el patrón en su texto"
bash -c "sleep 40; : generar_campana.py --config señuelo" & PIDS_FONDO+=($!)
sh -c 'sleep 40 # python3 x/generar_campana.py --config' & PIDS_FONDO+=($!)
sleep 1; echo "  señuelos: $(pgrep -fc 'generar_campana.py --config') proceso(s) que pgrep -f contaría"
reiniciar; SD=$(bash "$NUEVO" "$HASTA" srvdmz-banco 2>&1); printf '%s\n' "$SD" | sed 's/^/  | /'
comprobar "D no cuenta los señuelos" "$SD" "sin generador previo"
P=$(pids_listados "$SD"); n=$(wc -w <<< "$P")
[ "$n" = 1 ] && es_generador "$P" && echo "OK    D lista 1 PID ($P), ni señuelos ni el bash -c envoltorio" \
  || { echo "FALLO D: PIDs listados «$P»"; fallos=$((fallos + 1)); }

echo "=== usos del SSH simulado"; sed 's/^/  /' "$SSH_LOG"
echo "=== accesos-kali.log (D)"; sed 's/^/  /' "$B/accesos-kali.log"
[ "$fallos" = 0 ] && echo "BANCO g01 OK" || { echo "BANCO g01 CON $fallos FALLOS"; exit 1; }
