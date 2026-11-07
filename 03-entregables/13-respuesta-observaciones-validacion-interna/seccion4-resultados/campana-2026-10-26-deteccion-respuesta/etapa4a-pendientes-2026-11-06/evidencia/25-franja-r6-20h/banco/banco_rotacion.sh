#!/usr/bin/env bash
# [banco sin red] Casos de comprobar_rotacion_host.sh con systemctl simulado y un eve.json real alimentado por un proceso de prueba.
#   banco_rotacion.sh RUTA_DEL_GUION
set -u -o pipefail
G=${1:?}; T=$(mktemp -d); mkdir "$T/bin"; f=0
cat > "$T/bin/systemctl" <<'FIN'
#!/usr/bin/env bash
case "$1" in
  is-active) cat "$CF_DOBLE/suricata"; exit 0;;
  show) cat "$CF_DOBLE/${2%.service}";;
esac
FIN
chmod +x "$T/bin/systemctl"
ser() {  # nombre estado result status inicio fin
  { echo "ActiveState=$2"; echo "Result=$3"; echo "ExecMainStatus=$4"; echo "ExecMainStartTimestamp=$(date -u -d @"$5" '+%a %F %T UTC')"; echo "InactiveEnterTimestamp=$(date -u -d @"$6" '+%a %F %T UTC')"; } > "$T/$1"
}
ahora=$(date +%s); R=$((ahora - 600)); export CF_DOBLE="$T" CF_EVE="$T/eve.json" CF_ESPERA=2 PATH="$T/bin:$PATH"
evento() { printf '{"timestamp":"%s","event_type":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%S.000000+0000)" "$1" >> "$T/eve.json"; }
vivo() { while :; do evento stats; sleep 0.3; done & P=$!; }
base() {
  : > "$T/eve.json"; : > "$T/eve.json.1.gz"; touch -d @"$((R + 5))" "$T/eve.json.1.gz"; echo active > "$T/suricata"
  ser logrotate inactive success 0 "$((R + 1))" "$((R + 9))"; ser cyberflow-aprendizaje inactive success 0 "$((R + 1))" "$((R + 90))"
}
caso() {  # nombre rc_esperado texto modo
  local o r; o=$(bash "$G" "$4" "$R" 2>&1); r=$?
  if [ "$r" = "$2" ] && grep -q "$3" <<<"$o"; then echo "OK    $1 rc=$r"; else echo "FALLO $1 rc=$r (esperado $2)"; tail -3 <<<"$o"; f=$((f + 1)); fi
}
base; vivo; sleep 1; caso "todo normal" 0 "REQ ROTACION.rotacion CUMPLE" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; vivo; sleep 1; ser logrotate activating "" 0 "$((R + 1))" 0; caso "rotación en curso" 1 "sigue en estado activating" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; vivo; sleep 1; ser logrotate inactive success 0 "$((R - 86400))" "$((R - 86390))"; caso "rotación de ayer" 1 "no ha corrido" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; vivo; sleep 1; ser logrotate failed exit-code 1 "$((R + 1))" "$((R + 9))"; caso "rotación fallida" 1 "sigue en estado failed" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; vivo; sleep 1; touch -d @"$((R - 100))" "$T/eve.json.1.gz"; caso "gz sin rotar" 1 "es anterior al mínimo" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; vivo; sleep 1; echo failed > "$T/suricata"; caso "suricata caído" 1 "suricata en estado failed" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; evento stats; caso "eve parado" 1 "no creció" rotacion
base; (while :; do printf '{"timestamp":"2026-01-01T00:00:00.000000+0000","event_type":"flow"}\n' >> "$T/eve.json"; sleep 0.3; done) & P=$!; sleep 1; caso "eve crece sin eventos nuevos" 1 "sin eventos nuevos" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; (evento stats; while :; do evento flow; sleep 0.3; done) & P=$!; sleep 1; CF_MAX_STATS=1 caso "sin stats recientes" 1 "sin stats recientes" rotacion; kill "$P"; wait "$P" 2>/dev/null
base; caso "aprendizaje terminado" 0 "REQ ROTACION.aprendizaje CUMPLE" aprendizaje
base; ser cyberflow-aprendizaje activating "" 0 "$((R + 1))" 0; caso "aprendizaje en marcha" 1 "sigue en estado activating" aprendizaje
base; ser cyberflow-aprendizaje inactive success 0 "$((R - 86400))" "$((R - 86300))"; caso "aprendizaje sin correr" 1 "no ha corrido" aprendizaje
caso "uso" 2 "uso" otro
echo "FALLOS=$f"; exit "$f"
