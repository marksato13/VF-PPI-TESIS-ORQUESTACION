set -u
echo "##### Sensor1 $(hostname) $(date -u +%FT%TZ)"
for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata ppi-dashboard; do echo "$u $(systemctl is-active $u) NR=$(systemctl show -p NRestarts --value $u) PID=$(systemctl show -p MainPID --value $u) desde=$(systemctl show -p ActiveEnterTimestamp --value $u | cut -c5-24)"; done
P=$(systemctl show -p MainPID --value ppi-motor); C=$(tr '\0' ' ' < /proc/$P/cmdline)
echo "motor: manifiesto alfa=0,01: $(echo "$C" | grep -c 'limpio-alfa001-B') ; --enforce: $(echo "$C" | grep -c -- --enforce) ; candidato ec78ca5: $(echo "$C" | grep -c 'cyberflow-e4/ec78ca5')"
echo "último motor_startup: $(grep motor_startup ~/cyberflow/logs/motor_decision.log | tail -1 | python3 -I -c "import sys,json;d=json.loads(sys.stdin.read());print(d.get('logged_at'),d.get('threshold'))" 2>/dev/null)"
echo "últimas 200 decisiones: umbrales distintos = $(tail -200 ~/cyberflow/logs/motor_decision.log | python3 -I -c "
import sys,json
s=set()
for l in sys.stdin:
    try: d=json.loads(l)
    except Exception: continue
    if 'threshold' in d and d['threshold'] is not None: s.add(d['threshold'])
print(sorted(s))")"
echo "--- captura (anillo tcpdump)"; ls /var/lib/ppi-motor-capture | wc -l; ls -t /var/lib/ppi-motor-capture | head -1; echo "edad del último pcap: $(( $(date +%s) - $(stat -c %Y /var/lib/ppi-motor-capture/$(ls -t /var/lib/ppi-motor-capture | head -1)) )) s"
echo "--- Suricata EVE (stats recientes)"; tail -c 3000000 /var/log/suricata/eve.json | grep '"event_type":"stats"' | tail -1 | cut -c1-120; echo "edad eve.json: $(( $(date +%s) - $(stat -c %Y /var/log/suricata/eve.json) )) s"
echo "--- carpetas 4c"; ls -d ~/cf-e4/4c ~/cf-e4/4c-* 2>&1 | sed 's|/home/m4rk|~|' | head -12
echo "--- disco"; df -h / | tail -1
echo "--- herramientas requeridas por s10"; sha256sum ~/bin/archivar_captura.sh | cut -c1-16; (cd ~/cyberflow-e4/ec78ca5 && sha256sum -c --quiet SHA256SUMS && echo "ec78ca5 OK"); (cd ~/cyberflow-e4/herramientas-20261106 && sha256sum -c --quiet SHA256SUMS && echo "herramientas P1 OK"); sha256sum ~/cyberflow-e4/herramientas-20261106/salud_captura.py | cut -c1-16
echo "--- vigía B en el Sensor1"; sha256sum ~/cf-e4/vigia-20261106/vigia_4c_b.py ~/cf-e4/vigia-20261106/vigia_4c.py ~/cf-e4/vigia-20261106/salud_captura.py 2>&1 | cut -c1-16,65-
echo "--- logrotate"; systemctl list-timers logrotate.timer --no-pager --plain | sed -n 2p | cut -c1-110; echo "cf-4b: $(systemctl is-active cf-4b-vigia 2>&1) $(systemctl is-active cf-4b-tope.timer 2>&1)"
echo "--- procesos de campaña previos (no debe haber)"; ps -eo args | grep -E '[a]rchivar_captura|[s]ensor_muestrear|[s]alud_captura.py muestrear|[e]spejo' | cut -c1-100
echo "--- relé/feed"; ls -l --time-style=long-iso ~/feed-v2/feed.json | awk '{print $6,$7}'
echo "--- verif-B"; ls ~/cf-b/verif-B/sensor1 2>&1 | head -3
