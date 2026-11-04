set -u
# [Sensor1 m4rk] Base 4A recalculada con eventos stats de EVE y contraste con stats.log. Solo lectura.
C=/home/m4rk/cf-e4/cierre4a; PY=/home/m4rk/cyberflow/.venv/bin/python
ls -la --time-style=full-iso /var/log/suricata/ | grep -E 'eve|stats'
head -c 300 /var/log/suricata/eve.json | cut -c1-60
D=$(date -ud 2026-11-04T02:19:45Z +%s); H=$(date -ud 2026-11-04T03:19:51Z +%s)
$PY -I $C/herr/comparar_suricata.py --stats-eve /var/log/suricata/eve.json --desde $D --hasta $H --etiqueta "4A (eve stats)" > $C/base-4a-suricata-eve.json
$PY -c 'import json,sys
for f in sys.argv[1:]:
    d=json.load(open(f)); print(f.split("/")[-1], d.get("fuente_contadores","stats.log"), "bloques", d["bloques_stats"], "interv", d["intervalos_validos"], "hueco_max", d.get("hueco_max_entre_bloques_s"), "paq", d["paquetes"], "desc", d["descartes"], "por_M", d["descartes_por_millon"], "episodios", [(x["t_utc"],x["descartes"]) for x in d["intervalos_con_descartes"]], "rafagas", d["rafagas_ge_umbral"], "p50/p95/max", d["paquetes_por_intervalo"]["p50"], d["paquetes_por_intervalo"]["p95"], d["paquetes_por_intervalo"]["max"])' $C/base-4a-suricata.json $C/base-4a-suricata-eve.json
echo "== desde el reinicio (06:16:55) hasta ahora, solo contexto de calentamiento"
$PY -I $C/herr/comparar_suricata.py --stats-eve /var/log/suricata/eve.json --desde $(date -ud 2026-11-04T06:16:55Z +%s) --hasta $(date +%s) --etiqueta calentamiento > $C/calentamiento-suricata-eve.json
$PY -c 'import json; d=json.load(open("'$C'/calentamiento-suricata-eve.json")); print("bloques", d["bloques_stats"], "reinicios", d["reinicios_suricata_en_ventana"], "paq", d["paquetes"], "desc", d["descartes"], "rafagas", d["rafagas_ge_umbral"])'
