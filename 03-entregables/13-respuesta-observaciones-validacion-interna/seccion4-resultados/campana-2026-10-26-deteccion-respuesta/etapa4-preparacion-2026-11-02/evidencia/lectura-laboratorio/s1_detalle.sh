#!/usr/bin/env bash
# Lecturas detalladas de Sensor1 (sin sudo, sin cambios). No lee claves privadas.
set +e
C=/home/m4rk/cyberflow
echo "== fecha"; date -u +%FT%T.%3NZ
echo "== proceso ppi-motor"
P=$(systemctl show -p MainPID --value ppi-motor)
echo "PID=$P"; ps -o pid,lstart,etimes,rss,vsz,pcpu,cmd -p "$P" | cat
echo "exe=$(readlink /proc/$P/exe)"; echo "cwd=$(readlink /proc/$P/cwd)"
echo "cmdline:"; tr '\0' '\n' < /proc/$P/cmdline
echo "start_utc=$(date -u -d "$(ps -o lstart= -p $P)" +%FT%TZ)"
echo "fds:"; ls -l /proc/$P/fd 2>&1 | awk '{print $NF}' | sort | uniq -c | sort -rn | head -30
echo "threads=$(ls /proc/$P/task | wc -l)"
echo "== interprete"
readlink -f $C/.venv/bin/python
$C/.venv/bin/python -I -c 'import sys,sklearn,numpy,joblib;print(sys.version.split()[0],"sklearn",sklearn.__version__,"numpy",numpy.__version__,"joblib",joblib.__version__)' 2>&1
echo "== ficheros de codigo (sha256, mtime, ctime)"
cd $C
find scripts configs -type f \( -name '*.py' -o -name '*.toml' -o -name '*.json' \) ! -name '*.bak*' ! -name '*.anterior' ! -name '*.candidate*' ! -path '*/__pycache__/*' -printf '%p\n' \
 | sort | while read -r f; do printf '%s %s %s %s\n' "$(sha256sum "$f" | cut -c1-64)" "$(stat -c %Y "$f")" "$(stat -c %Z "$f")" "$f"; done
echo "== artefactos del modelo"
for f in artifacts/preliminar/limpio-2026-10/*; do printf '%s %s %s\n' "$(sha256sum "$f" | cut -c1-64)" "$(stat -c '%s %Y' "$f")" "$f"; done
echo "== manifiesto del modelo (claves y umbral)"
$C/.venv/bin/python -I - <<'PY'
import json
m=json.load(open("/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json"))
def plano(d,p=""):
    for k,v in d.items():
        if isinstance(v,dict): plano(v,p+k+".")
        elif isinstance(v,list): print(p+k,"[lista",len(v),"]", (v[:3] if len(v)<=40 else ""))
        else: print(p+k,"=",v)
plano(m)
PY
echo "== config local (sin valores sensibles)"
sed -E 's/((key|token|pass|secret|clave)[a-z_]*[[:space:]]*=[[:space:]]*).*/\1***/I' configs/cyberflow.local.toml
echo "== motor_startup y ultima decision"
L=$C/logs/motor_decision.log
ls -la $C/logs | cat
grep -a '"motor_startup"' $L | tail -2 | cut -c1-3000
tail -1 $L | cut -c1-2500
echo; echo "claves de la ultima decision:"; tail -1 $L | $C/.venv/bin/python -I -c 'import sys,json;d=json.loads(sys.stdin.read());print(sorted(d.keys()))'
echo "== estado feed v1"
ls -la ~/feed | cat
$C/.venv/bin/python -I -c 'import json;d=json.load(open("/home/m4rk/feed/feed.json"));print({k:(v if not isinstance(v,list) else len(v)) for k,v in d.items()})' 2>&1
echo "acciones:"; $C/.venv/bin/python -I -c 'import json;d=json.load(open("/home/m4rk/feed/feed.json"));[print(a) for a in d.get("acciones",[])[:10]]' 2>&1
echo "== publicador: ultimo journal"
journalctl -u ppi-publicar-feed --since -2min --no-pager -o short-iso 2>&1 | tail -4
echo "== feed-keys (solo metadatos)"; ls -la $C/artifacts/feed-keys | cat
echo "== captura PCAP"
P2=$(systemctl show -p MainPID --value ppi-motor-capture); ps -o pid,user,lstart,cmd -p $P2 | cat
ls -la /var/lib/ppi-motor-capture | head -3; echo "ficheros=$(ls /var/lib/ppi-motor-capture | wc -l)"; ls -t /var/lib/ppi-motor-capture | head -3
journalctl -u ppi-motor-capture --no-pager -o short-iso 2>&1 | tail -8
echo "== tcpdump/libpcap"; tcpdump --version 2>&1 | head -3; command -v tcpdump
tcpdump -d -y EN10MB 'tcp or (vlan and tcp)' 2>&1 | head -12
getcap /usr/bin/tcpdump 2>&1
echo "== interfaz ens37"
ip -s -s link show ens37 2>&1
cat /sys/class/net/ens37/statistics/{rx_packets,rx_dropped,rx_missed_errors,rx_fifo_errors,rx_over_errors} 2>&1 | paste -sd' '
ethtool -S ens37 2>&1 | head -40
ethtool -k ens37 2>&1 | grep -E 'generic-receive|large-receive|tcp-segmentation|generic-segmentation|rx-vlan-offload|rx-vlan-filter'
ethtool -i ens37 2>&1
echo "== suricata"
ls -la /var/log/suricata | cat
grep -n -E 'stats|interval|kernel|af-packet|interface|eve-log|enabled' /etc/suricata/suricata.yaml 2>&1 | head -60
tail -60 /var/log/suricata/stats.log 2>&1 | grep -E 'Date|capture\.|decoder\.pkts|flow\.memcap|tcp\.reassembly_gap|detect\.alert' | head -40
echo "== relojes"; timedatectl 2>&1 | head -8; timedatectl show-timesync 2>&1 | head -6
echo "== logrotate"; ls -la /etc/logrotate.d | cat; cat /etc/logrotate.d/suricata /etc/logrotate.d/cyberflow* 2>&1 | head -60
echo "== acumulador / campaña"
tail -n 3000 $C/artifacts/linea-base/multilayer-v3.csv | cut -d, -f1 | sort | uniq -c
head -1 $C/artifacts/linea-base/multilayer-v3.csv | cut -c1-300
stat -c '%y %s' $C/artifacts/linea-base/multilayer-v3.csv
tail -3 $C/logs/acumular.log 2>&1 | cut -c1-400
