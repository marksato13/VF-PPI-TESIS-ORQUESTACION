O=~/cf-r42; mkdir -p $O
zcat /var/log/syslog.4.gz | grep 'publicar_feed.py' | grep CMD | cut -c1-32 > $O/runs4.txt
zcat /var/log/syslog.3.gz | grep 'publicar_feed.py' | grep CMD | cut -c1-32 > $O/runs3.txt
cat $O/runs4.txt $O/runs3.txt > $O/runs.txt
echo "runs total: $(wc -l < $O/runs.txt)  log lineas: $(wc -l < ~/feed/publicar.log)  bytes: $(stat -c %s ~/feed/publicar.log)"
echo "== primera y ultima ejecucion"; sed -n '1p;$p' $O/runs.txt
echo "== huecos > 70 s entre ejecuciones"
python3 - <<'PY'
from datetime import datetime
r=[datetime.fromisoformat(l.strip()) for l in open('/home/m4rk/cf-r42/runs.txt')]
for a,b in zip(r,r[1:]):
    if (b-a).total_seconds()>70: print(a.isoformat()[:19], '->', b.isoformat()[:19])
PY
echo "== lineas no JSON del log (num:prefijo)"; grep -anv '^{' ~/feed/publicar.log | cut -c1-120 | head
echo "== lineas con la Kali"; grep -an '10.10.20.30' ~/feed/publicar.log | cut -c1-300
echo "== publicar.log lineas 2700-2760"; sed -n '2700,2760{=;p}' ~/feed/publicar.log | paste - - | cut -c1-160
grep -n '2026-10-05T20:2[0-9]' $O/runs.txt | head -3
