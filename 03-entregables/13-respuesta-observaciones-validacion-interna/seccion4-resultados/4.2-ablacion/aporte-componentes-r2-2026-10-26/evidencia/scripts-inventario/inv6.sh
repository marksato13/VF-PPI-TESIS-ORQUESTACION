L=~/feed/publicar.log
head -2 $L | cut -c1-400; echo; tail -1 $L | cut -c1-400; echo
echo "== claves de la primera linea"; head -1 $L | python3 -c 'import json,sys; print(sorted(json.loads(sys.stdin.readline()).keys()))' 2>&1
echo "== lineas con 10.10.20.30"; grep -c '10.10.20.30' $L; grep -n '10.10.20.30' $L | head -5 | cut -c1-400
echo "== cron publicar en syslog.3.gz 05-oct (primera/ultima)"; zcat /var/log/syslog.3.gz | grep 'publicar_feed.py' | sed -n '1p;$p' | cut -c1-40
zcat /var/log/syslog.3.gz | grep -c 'publicar_feed.py'
for g in /var/log/syslog.4.gz /var/log/syslog.5.gz /var/log/syslog.6.gz /var/log/syslog.7.gz; do [ -f $g ] && echo "$g $(zcat $g | grep -c publicar_feed.py) $(zcat $g | grep publicar_feed.py | sed -n '1p' | cut -c1-32)"; done
ls -la --time-style=full-iso ~/cyberflow/logs/ | head -20
