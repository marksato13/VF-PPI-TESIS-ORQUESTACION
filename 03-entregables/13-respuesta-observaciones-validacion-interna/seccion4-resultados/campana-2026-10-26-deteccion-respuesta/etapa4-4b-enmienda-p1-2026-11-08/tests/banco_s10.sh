#!/usr/bin/env bash
# Banco de s10 enmendado (contenedor sin red, usuario sin privilegios, /var/log/suricata y /var/lib/ppi-motor-capture en tmpfs).
# Un Sensor1 SIMULADO: systemctl falso, motor falso (cmdline del candidato), archivador de prueba, EVE sintético y el muestreador
# REAL de P1 (salud_captura 2026-11-06.1). Único cambio del guion probado: la línea que fija el hash del archivador, sustituida
# por el hash del archivador de prueba (el archivador real 2181af5f… no se puede ejecutar aquí). Todo lo demás es el guion publicado.
# Montajes: /e (enmienda), /herr (herramientas planas con salud_captura P1), /out.
set -u
OUT=${OUT:-/out}; mkdir -p "$OUT"; LOG=$OUT/banco-s10.txt; : > "$LOG"
export AQUI=/e/tests
say() { echo "$*" | tee -a "$LOG"; }
fallo=0
ok() { if eval "$2"; then say "OK    $1"; else say "FALLO $1"; fallo=1; fi; }
T=$(mktemp -d)
mkdir -p "$T/bin"
cat > "$T/bin/systemctl" <<'EOF'
#!/usr/bin/env bash
# systemctl falso: PID del motor desde $FAKE_PIDFILE; el resto, valores fijos
a="$*"
if [[ "$a" == *"--value"* && "$a" == *"MainPID"* ]]; then cat "$FAKE_PIDFILE"; exit 0; fi
if [[ "$a" == show* ]]; then
  u=$(echo "$a" | awk '{print $2}')
  printf 'Id=%s\nMainPID=%s\nNRestarts=0\nActiveState=active\nExecMainStartTimestampMonotonic=1000\nActiveEnterTimestamp=Thu 2026-11-05 23:59:01 UTC\n' "$u" "$(cat "$FAKE_PIDFILE")"
  exit 0
fi
exit 0
EOF
chmod +x "$T/bin/systemctl"
export PATH="$T/bin:$PATH"

preparar() {   # preparar nombre  -> HOME simulado listo
  export HOME=$T/h-$1; mkdir -p "$HOME"/{cyberflow/.venv/bin,cyberflow/logs/_state-e4,bin,feed-v2,feed,cyberflow-e4/ec78ca5/scripts/engine,cyberflow-e4/herramientas-20261106}
  ln -sf "$(command -v python3)" "$HOME/cyberflow/.venv/bin/python"
  echo x > "$HOME/cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py"
  ( cd "$HOME/cyberflow-e4/ec78ca5" && find scripts -type f | sort | xargs sha256sum > SHA256SUMS )
  cp /herr/salud_captura.py "$HOME/cyberflow-e4/herramientas-20261106/"
  ( cd "$HOME/cyberflow-e4/herramientas-20261106" && sha256sum salud_captura.py > SHA256SUMS )
  cat > "$HOME/bin/archivar_captura.sh" <<'EOF'
#!/usr/bin/env bash
# archivador de prueba: ESTADO.txt OK y una línea OK en archivar.log; sigue vivo
D=$1; mkdir -p "$D"; echo OK > "$D/ESTADO.txt"; echo "$(date -u +%FT%TZ) OK live-20261108000000.pcap" > "$D/archivar.log"
while :; do sleep 5; done
EOF
  chmod +x "$HOME/bin/archivar_captura.sh"
  : > "$HOME/cyberflow/logs/motor_decision.log"; : > "$HOME/cyberflow/logs/_state-e4/ciclos.jsonl"
  echo '{}' > "$HOME/feed-v2/estado.json"; echo '{}' > "$HOME/feed/estado.json"
  printf '{"bloque_hasta": %s, "paquetes_tcp": 5}\n' "$(date +%s)" > "$HOME/feed-v2/via-rapida-resumen.jsonl"
  # motor falso con la línea de órdenes del candidato
  ( exec -a "/x/python $HOME/cyberflow-e4/ec78ca5/scripts/engine/motor_decision.py --eve-path /var/log/suricata/eve.json --disparo eventos" sleep 600 ) &
  echo $! > "$T/pid-$1"; export FAKE_PIDFILE="$T/pid-$1"; sleep 0.5
  rm -f /var/log/suricata/eve.json /var/log/suricata/stats.log; : > /var/log/suricata/stats.log
  touch /var/lib/ppi-motor-capture/live-20261108000000.pcap 2>/dev/null
}
eve() {   # eve <opciones de datos_sinteticos.eve_stats en python> : EVE hasta «ahora + 60 s»
  python3 - "$@" <<'PY'
import sys, time
sys.path.insert(0, "/e/tests")
import datos_sinteticos as ds
ahora = time.time()
kw = eval("dict(" + (sys.argv[1] if len(sys.argv) > 1 else "") + ")", {"ahora": ahora})
t1 = kw.pop("hasta", ahora + 60)
open("/var/log/suricata/eve.json", "wb").write(ds.eve_stats(ahora - 1800, t1, arranque=ahora - 7200, **kw))
PY
}
s10() {   # s10 con SOLO el hash del archivador sustituido (diff comprobado más abajo)
  local h; h=$(sha256sum "$HOME/bin/archivar_captura.sh" | cut -c1-64)
  sed "s/2181af5f8406e3aa4f41a26e24d7ec83bfaf72eee06aa3ee564e2dbba5639eb6/$h/" /e/guiones/s10_sensor_archivo_e4.sh > "$T/s10-banco.sh"
  bash "$T/s10-banco.sh" "$@"
}
parar_todo() { pkill -f motor_decision.py 2>/dev/null; pkill -f 'salud_captura.py muestrear' 2>/dev/null; pkill -f sensor_muestrear.sh 2>/dev/null; pkill -f 'archivar_captura.sh' 2>/dev/null; true; }


say "## 1. Sensor1 sano (EVE con cero descartes)"
preparar sano; eve ""
s10 4b > "$T/o1" 2>&1; rc=$?; cp "$T/o1" "$OUT/s10-sano.txt"
B=$HOME/cf-e4/4b
ok "S0 el guion de banco difiere del publicado en UNA línea (el hash del archivador)" "[ \$(diff /e/guiones/s10_sensor_archivo_e4.sh $T/s10-banco.sh | grep -c '^<') = 1 ]"
ok "S1 s10 termina con rc 0 y '## fin'" "[ $rc = 0 ] && grep -q '^## fin' $T/o1"
ok "S2 mide Suricata por EVE antes de empezar: cero_explicito" "grep -q 'Suricata medido por EVE stats (10 min previos): cero_explicito' $T/o1"
ok "S3 el muestreador es el de P1 (VERSION 2026-11-06.1) y escribe muestras" "[ -s $B/salud/muestras.jsonl ] && grep -q '\"version\": \"2026-11-06.1\"' $B/salud/muestras.jsonl"
ok "S4 guarda la medida EVE inicial" "python3 -c \"import json;d=json.load(open('$B/salud/suricata-eve-inicio.json'));assert d['estado']=='cero_explicito' and d['descartes']==0\""
ok "S5 el muestreador en marcha usa herramientas-20261106 y no ec78ca5" "ps -eo args | grep -v grep | grep 'salud_captura.py muestrear' | grep -q 'herramientas-20261106' && ! ps -eo args | grep -v grep | grep 'salud_captura.py muestrear' | grep -q 'ec78ca5'"
ok "S6 el archivador y el muestreador de recursos están vivos" "grep -q 'vivo=si' $T/o1 && [ -s $B/recursos/muestras.jsonl ]"
ok "S7 la línea final imprime la herramienta, su sha y el estado de Suricata" "grep -q 'salud: .*herramientas-20261106/salud_captura.py (sha 274b4d61' $T/o1 && grep -q 'Suricata inicial (EVE): cero_explicito' $T/o1"
parar_todo

say "## 2. Casos en que s10 NO debe empezar"
preparar sin; eve "sin_drops=[(ahora - 900, ahora + 120)]"
s10 4b > "$T/o2" 2>&1; rc=$?; cp "$T/o2" "$OUT/s10-ausente.txt"
ok "S8 EVE sin kernel_drops (ausente): rc 2, PARAR, no crea la carpeta de la fase" "[ $rc = 2 ] && grep -q \"PARAR: Suricata no medible por EVE stats ('ausente')\" $T/o2 && [ ! -e $HOME/cf-e4/4b ]"
parar_todo
preparar viejo; eve "hasta=ahora - 300"
s10 4b > "$T/o3" 2>&1; rc=$?; cp "$T/o3" "$OUT/s10-desactualizada.txt"
ok "S9 EVE que dejó de producir (desactualizada): rc 2 y no crea la carpeta" "[ $rc = 2 ] && grep -q \"('desactualizada')\" $T/o3 && [ ! -e $HOME/cf-e4/4b ]"
parar_todo
preparar hueco; eve "huecos=[(ahora - 400, ahora - 200)]"
s10 4b > "$T/o4" 2>&1; rc=$?; cp "$T/o4" "$OUT/s10-hueco.txt"
ok "S10 hueco de EVE en los 10 min previos (cobertura insuficiente): rc 2" "[ $rc = 2 ] && grep -q 'cobertura_insuficiente' $T/o4 && [ ! -e $HOME/cf-e4/4b ]"
parar_todo
preparar hash; eve ""
echo "# alterada" >> "$HOME/cyberflow-e4/herramientas-20261106/salud_captura.py"
( cd "$HOME/cyberflow-e4/herramientas-20261106" && sha256sum salud_captura.py > SHA256SUMS )
s10 4b > "$T/o5" 2>&1; rc=$?; cp "$T/o5" "$OUT/s10-hash.txt"
ok "S11 salud_captura con hash distinto del fijado (aunque su SHA256SUMS cuadre): rc 2" "[ $rc = 2 ] && grep -q 'salud_captura de P1 con hash distinto' $T/o5 && [ ! -e $HOME/cf-e4/4b ]"
parar_todo
preparar rep; eve ""
mkdir -p "$HOME/cf-e4/4b"
s10 4b > "$T/o6" 2>&1; rc=$?
ok "S12 carpeta de la fase ya existente: rc 2 (no se pisa)" "[ $rc = 2 ] && grep -q 'PARAR: ya existe' $T/o6"
parar_todo
say "RESULTADO: $([ $fallo = 0 ] && echo 'todas las comprobaciones OK' || echo 'HAY FALLOS')"
exit $fallo
