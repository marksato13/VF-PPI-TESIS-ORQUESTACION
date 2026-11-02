#!/usr/bin/env bash
# Segunda tanda de lecturas en Sensor1 (sin sudo, sin cambios).
set +e
C=/home/m4rk/cyberflow
echo "== fecha"; date -u +%FT%T.%3NZ
P=$(systemctl show -p MainPID --value ppi-motor)
echo "== arranque del proceso (segundos epoch)"
echo "btime=$(awk '/^btime/{print $2}' /proc/stat) clk_tck=$(getconf CLK_TCK) starttime_ticks=$(awk '{print $22}' /proc/$P/stat)"
systemctl show ppi-motor -p ExecMainStartTimestampMonotonic -p ExecMainStartTimestamp -p ActiveEnterTimestamp
echo "== mtime/ctime exactos de los modulos del motor"
for f in scripts/engine/motor_decision.py scripts/engine/motor_incremental.py scripts/engine/heuristicos.py scripts/engine/vista_vivo.py scripts/engine/feed.py scripts/features/*.py configs/features/multilayer-v2.json artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json; do
  stat -c '%Y %Z %s %n' "$C/$f"
done
echo "== importaciones de motor_decision.py"
grep -nE '^(from|import) |importlib|sys\.path' $C/scripts/engine/motor_decision.py | head -40
echo "== esquema: finales de linea y tamano"
wc -c $C/configs/features/multilayer-v2.json; grep -c $'\r' $C/configs/features/multilayer-v2.json
base64 -w0 $C/configs/features/multilayer-v2.json > /tmp/.e4_schema.b64; echo "b64_len=$(wc -c < /tmp/.e4_schema.b64)"; cat /tmp/.e4_schema.b64; echo; rm -f /tmp/.e4_schema.b64
echo "== motor_startup en registros rotados"
grep -a '"motor_startup"' $C/logs/motor_decision.log.1 | tail -2 | cut -c1-4000
zcat $C/logs/motor_decision.log.2.gz | grep -a '"motor_startup"' | tail -1 | cut -c1-600
echo "== _state"; ls -la $C/logs/_state | cat; tail -1 $C/logs/_state/ciclos.jsonl | cut -c1-2500
echo "== suricata stats (ultimo bloque, contadores de captura)"
tac /var/log/suricata/stats.log | awk '/^Date:/{n++} n==1' | tac | grep -E '^Date|capture\.|decoder\.pkts |decoder\.bytes |decoder\.invalid|flow\.memcap|tcp\.reassembly_gap|tcp\.ssn_memcap|stats\.' | cat
echo "== suricata stats (bloque de hace ~1 h para el incremento)"
tac /var/log/suricata/stats.log | awk '/^Date:/{n++} n==450' | tac | grep -E '^Date|capture\.kernel' | cat
echo "== suricata: arranque y version"
ps -o pid,lstart,cmd -p $(cat /run/suricata.pid 2>/dev/null) | cat; suricata -V 2>&1 | head -2
grep -n -A30 '^af-packet:' /etc/suricata/suricata.yaml | grep -vE '^\s*[0-9]+-\s*#' | head -30
grep -nE 'event-types|^\s+- (dns|http|flow|stats|alert|tls|anomaly)' /etc/suricata/suricata.yaml | head -20
echo "== eve: tipos en el ultimo minuto"
tail -c 20000000 /var/log/suricata/eve.json | grep -o '"event_type":"[a-z_]*"' | sort | uniq -c
echo "== piloto-con-dns: ultima fila con esa campana en el dataset"
tac $C/artifacts/linea-base/multilayer-v3.csv | grep -m1 '^piloto-con-dns,' | cut -c1-80
grep -c '^piloto-con-dns,' $C/artifacts/linea-base/multilayer-v3.csv
ls -la $C/artifacts/linea-base | cat
echo "== estado.json (sin claves)"; $C/.venv/bin/python -I -c 'import json;d=json.load(open("/home/m4rk/feed/estado.json"));print(json.dumps(d)[:900])'
echo "== feed.json"; $C/.venv/bin/python -I -c 'import json;d=json.load(open("/home/m4rk/feed/feed.json"));print(json.dumps(d)[:900])'
echo "== feed-v2 / via rapida (no deberian existir)"; ls -la ~/feed-v2 2>&1; ls /etc/systemd/system | grep -E 'via-rapida|feed-v2' ; echo "fin"
echo "== authorized_keys (solo comentario y opciones, sin la clave)"
awk '{for(i=1;i<=NF;i++) if($i ~ /^(ssh-|ecdsa-)/){opt=""; for(j=1;j<i;j++) opt=opt $j " "; print "opciones=[" opt "] tipo=" $i " comentario=" $(i+2); break}}' ~/.ssh/authorized_keys 2>&1
echo "== sudo de m4rk sin contrasena (lista, sin ejecutar nada)"; sudo -n -l 2>&1 | head -20
echo "== grupos"; id
