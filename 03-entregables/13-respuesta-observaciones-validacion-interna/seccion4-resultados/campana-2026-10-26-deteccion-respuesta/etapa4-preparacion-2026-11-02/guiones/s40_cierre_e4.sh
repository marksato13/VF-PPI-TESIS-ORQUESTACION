#!/usr/bin/env bash
# shellcheck disable=SC2024  # la salida de "sudo -n journalctl" la escribe m4rk en su propio directorio: intencionado
# [SENSOR1 m4rk] ETAPA4 s40 — uso: s40_cierre_e4.sh <4b|4c>. Cierre ordenado DESPUÉS de verificar las condiciones
# 1-5 (s20 + rc=0 del replay). Para el archivador (barrido final y FIN OK persistidos), el muestreador de recursos y el
# de salud (procesos propios), y copia las fuentes definitivas: motor, ciclos, Suricata, salud, journal de los dos
# tcpdump (lecturas SIGUSR1), feed v1 y v2 (traza, señales, resumen de la vía rápida, estado) y servicios.
# Sin sudo salvo journalctl (NOPASSWD). No toca motor ni servicios: se sigue en sombra.
# Resultado esperado: "archivador rc=0", "FIN OK", 0 FALLO/PERDIDO, sha256sum -c del candidato sin errores,
# "--enforce en argv: ''". Parada: replay sin rc=0.
set -u
FASE=${1:?fase}
B=$HOME/cf-e4/$FASE; D=$B/archivo-pcap; C=$B/copias; E4=$HOME/cyberflow-e4/ec78ca5; F2=$HOME/feed-v2
echo "## s40-e4 $FASE $(date -u +%FT%T.%3NZ)"
grep -q '^rc=0' "$B/replay/rc.txt" 2>/dev/null || { echo "PARAR: la repetición no ha terminado con rc=0 ($(cat "$B/replay/rc.txt" 2>&1))"; exit 2; }
date +%s.%N > "$B/cierre.t"
P=$(cat "$D.pid"); echo "  archivador PID=$P -> TERM (barrido final)"; kill -TERM "$P"
for _ in $(seq 1 90); do [ -s "$D.rc" ] && break; sleep 1; done
echo "  archivador rc=$(cat "$D.rc" 2>/dev/null)  ESTADO: $(cat "$D/ESTADO.txt")"; tail -4 "$D/archivar.log" | sed 's/^/   | /'
echo "  pcaps archivados: $(ls "$D"/live-*.pcap | wc -l)  tamaño: $(du -sh "$D" | cut -f1)"
echo "  FALLO/PERDIDO en archivar.log: $(grep -cE ' FALLO |PERDIDO' "$D/archivar.log")"
M=$(cat "$B/recursos/muestreo.pid"); kill -TERM "$M" && echo "  muestreador de recursos $M parado ($(wc -l < "$B/recursos/muestras.jsonl") muestras)"
S=$(cat "$B/salud/muestrear.pid"); kill -TERM "$S" && echo "  muestreador de salud $S parado ($(wc -l < "$B/salud/muestras.jsonl") muestras)"
INI=$(python3 -c "import json,datetime as d;print(d.datetime.fromtimestamp(json.load(open('$B/eve/inicio.json'))['t']-120,d.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))")
sudo -n journalctl -u ppi-motor-capture --since "$INI UTC" -o short-iso-precise --no-pager > "$B/salud/tcpdump-anillo.log"
sudo -n journalctl -u ppi-via-rapida@ens37 --since "$INI UTC" -o short-iso-precise --no-pager > "$B/salud/tcpdump-via.log"
echo "  lecturas SIGUSR1: anillo $(grep -c 'packets captured' "$B/salud/tcpdump-anillo.log") / vía $(grep -c 'packets captured' "$B/salud/tcpdump-via.log")"
cp -p "$HOME/cyberflow/logs/_state-e4/ciclos.jsonl" "$C/ciclos.jsonl"
cp -p "$HOME/cyberflow/logs/motor_decision.log" "$C/motor_decision.log"
echo "  motor_decision.log: inodo $(stat -c %i "$HOME/cyberflow/logs/motor_decision.log") (inicio: $(cat "$B/eve/motor-inicio.txt"))"
cp -p "$B/eve/stats-inicio.log" "$C/stats-inicio.log"; cp -p /var/log/suricata/stats.log "$C/stats-fin.log"
cp -p "$B/recursos/muestras.jsonl" "$C/muestras.jsonl"; cp -p "$D/ESTADO.txt" "$C/archivador-ESTADO.txt"; cp -p "$D/archivar.log" "$C/archivar.log"
mkdir -p "$C/feed-v2" "$C/feed-v1"
cp -p "$F2"/feed.json "$F2"/feed.sig "$F2"/estado.json "$F2"/traza.jsonl "$F2"/senales-rapidas.jsonl "$F2"/senales-if.jsonl "$F2"/via-rapida-resumen.jsonl "$C/feed-v2/" 2>&1
cp -p "$HOME"/feed/feed.json "$HOME"/feed/feed.sig "$HOME"/feed/estado.json "$C/feed-v1/"
sha256sum "$C"/feed-v2/feed.json "$C"/feed-v2/feed.sig "$C"/feed-v2/estado.json "$C"/feed-v1/* | tee "$C/sha256-feed-final.txt" | sed 's/^/  /'
S0=$(systemctl show -p ActiveEnterTimestamp --value ppi-motor)
sudo -n journalctl --no-pager -u ppi-motor --since "$S0" -o short-iso > "$C/journal-motor.txt"
sudo -n journalctl --no-pager -u ppi-motor-capture -u suricata -u ppi-via-rapida@ens37 -u ppi-publicar-feed-v2 --since "$INI UTC" -o short-iso > "$C/journal-captura.txt"
sudo -n journalctl --no-pager -p warning --since "$INI UTC" -o short-iso > "$C/journal-avisos-sistema.txt"
echo "  journal motor: $(wc -l < "$C/journal-motor.txt") líneas, trazas: $(grep -ciE 'traceback|exception' "$C/journal-motor.txt") | avisos: $(wc -l < "$C/journal-avisos-sistema.txt")"
systemctl show -p Id -p MainPID -p NRestarts -p ActiveState -p ActiveEnterTimestamp ppi-motor ppi-motor-capture \
  ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata ppi-publicar-feed.timer > "$C/servicios-fin.txt"
for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata; do
  echo "  $u $(systemctl is-active "$u") NR=$(systemctl show -p NRestarts --value "$u") PID=$(systemctl show -p MainPID --value "$u")"; done
diff <(grep -E 'MainPID|NRestarts' "$B/estado-inicial/servicios.txt") <(grep -E 'MainPID|NRestarts' "$C/servicios-fin.txt") > /dev/null \
  && echo "  servicios: mismos PID y NRestarts que al empezar" || echo "  AVISO servicios: PID o NRestarts distintos (ver servicios-fin.txt): periodo afectado = C3"
( cd "$E4" && sha256sum -c --quiet SHA256SUMS ) && echo "  candidato: SHA256SUMS OK" || echo "  AVISO candidato: SHA256SUMS con diferencias"
P=$(systemctl show -p MainPID --value ppi-motor); echo "  --enforce en argv: '$(tr '\0' ' ' < "/proc/$P/cmdline" | grep -o -- --enforce)'"
( cd "$C" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS ); echo "## fin $(date -u +%FT%T.%3NZ)"
