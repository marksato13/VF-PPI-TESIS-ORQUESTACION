set -u
D=/home/m4rk/cf-e4/4a; S=$D/salud; PY=/home/m4rk/cyberflow/.venv/bin/python
E=/home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py
P=$(head -1 $S/muestras.jsonl | $PY -c 'import json,sys;print(json.load(sys.stdin)["t"]+0.01)')
U=$(tail -1 $S/muestras.jsonl | $PY -c 'import json,sys;print(json.load(sys.stdin)["t"]-0.01)')
echo "primera muestra $P  ultima $U"
$PY -I $E clasificar --incrementos $S/incrementos.jsonl --tcpdump-log $S/journal-captura.txt \
   --tcpdump-log $S/journal-via-rapida.txt --desde "$P" --hasta "$U" > $S/clasificacion-rango-muestras.json; echo "rc=$?"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps({k:v for k,v in d.items() if k!="criterios"},indent=1)[:3000])' $S/clasificacion-rango-muestras.json
sha256sum $S/* > $D/SHA256SUMS; echo manifiesto ok
