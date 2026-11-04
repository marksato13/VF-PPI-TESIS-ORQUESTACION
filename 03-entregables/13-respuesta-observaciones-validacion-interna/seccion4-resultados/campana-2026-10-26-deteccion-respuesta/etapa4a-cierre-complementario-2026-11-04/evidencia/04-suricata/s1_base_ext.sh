set -u
# [Sensor1 m4rk] Contexto: tasa de episodios de descarte antes del ensayo (03-nov completo y 04-nov 00:00-05:55). Solo lectura.
C=~/cf-e4/cierre4a; PY=~/cyberflow/.venv/bin/python
r() { $PY -I $C/herr/comparar_suricata.py --stats "$1" --desde $(date -ud "$2" +%s) --hasta $(date -ud "$3" +%s) --etiqueta "$4" > "$C/$5"; \
      $PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["etiqueta"], "paq", d["paquetes"], "desc", d["descartes"], "por_M", d["descartes_por_millon"], "episodios", len(d["intervalos_con_descartes"]), "rafagas", d["rafagas_ge_umbral"], "interv", d["intervalos_validos"], "reinicios", d["reinicios_suricata_en_ventana"], "p95", d["paquetes_por_intervalo"]["p95"], "max", d["paquetes_por_intervalo"]["max"]); print("  con descartes:", [ (x["t_utc"], x["paquetes"], x["descartes"]) for x in d["intervalos_con_descartes"]][:40])' "$C/$5"; }
r /var/log/suricata/stats.log.1.gz 2026-11-03T00:00:10Z 2026-11-03T23:59:50Z "03-nov" base-03nov-suricata.json
r /var/log/suricata/stats.log 2026-11-04T00:00:10Z 2026-11-04T05:55:00Z "04-nov 00:00-05:55" base-04nov-suricata.json
