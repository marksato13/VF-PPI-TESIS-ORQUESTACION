set -u
D=/home/m4rk/cf-e4/4a; S=$D/salud; PY=/home/m4rk/cyberflow/.venv/bin/python
E=/home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py
J="journalctl --no-pager -o short-iso-precise --since 2026-11-04T02:18:45Z --until 2026-11-04T03:21:00Z"
$J -u ppi-motor-capture > $S/journal-captura-margen.txt
$J -u ppi-via-rapida@ens37 > $S/journal-via-rapida-margen.txt
grep -c 'packets captured' $S/journal-captura-margen.txt $S/journal-via-rapida-margen.txt
grep 'packets dropped by kernel' $S/journal-captura-margen.txt | awk '{print $NF" "$(NF-1)" "$(NF-5)}' | sort | uniq -c | sort -nr | head -3
grep -o '[0-9]* packets dropped by kernel' $S/journal-captura-margen.txt $S/journal-via-rapida-margen.txt | sort | uniq -c | sort -nr | head
P=$(head -1 $S/muestras.jsonl | $PY -c 'import json,sys;print(json.load(sys.stdin)["t"]+0.01)')
U=$(tail -1 $S/muestras.jsonl | $PY -c 'import json,sys;print(json.load(sys.stdin)["t"]-0.01)')
$PY -I $E clasificar --incrementos $S/incrementos.jsonl --tcpdump-log $S/journal-captura-margen.txt \
   --tcpdump-log $S/journal-via-rapida-margen.txt --desde "$P" --hasta "$U" > $S/clasificacion-final.json; echo "rc=$?"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps({k:v for k,v in d.items() if k!="criterios"},indent=1)[:3000])' $S/clasificacion-final.json
sha256sum $S/* > $D/SHA256SUMS; echo manifiesto ok
