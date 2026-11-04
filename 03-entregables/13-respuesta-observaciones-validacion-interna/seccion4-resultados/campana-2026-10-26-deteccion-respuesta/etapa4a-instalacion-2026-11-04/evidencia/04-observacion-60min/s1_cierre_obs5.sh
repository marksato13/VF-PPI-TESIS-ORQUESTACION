set -u
D=/home/m4rk/cf-e4/4a; S=$D/salud; PY=/home/m4rk/cyberflow/.venv/bin/python
E=/home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py
P=$(head -1 $S/muestras.jsonl | $PY -c 'import json,sys;print(json.load(sys.stdin)["t"]+0.01)')
U=$(tail -1 $S/muestras.jsonl | $PY -c 'import json,sys;print(json.load(sys.stdin)["t"]-0.01)')
for x in captura via-rapida; do
  $PY -I $E clasificar --incrementos $S/incrementos.jsonl --tcpdump-log $S/journal-$x-margen.txt \
     --desde "$P" --hasta "$U" > $S/clasificacion-final-$x.json; echo "== $x rc=$?"
  $PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["clase"], d["motivos"], json.dumps(d["info"].get("tcpdump"))[:400])' $S/clasificacion-final-$x.json
done
sha256sum $S/* > $D/SHA256SUMS; echo manifiesto ok