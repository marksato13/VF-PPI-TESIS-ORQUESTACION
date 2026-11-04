set -u
# [Sensor1 m4rk] Línea base de Suricata en la ventana de la 4A (mismo método que el ensayo). Solo lectura.
C=~/cf-e4/cierre4a; PY=~/cyberflow/.venv/bin/python
D=$(date -ud 2026-11-04T02:19:45Z +%s); H=$(date -ud 2026-11-04T03:19:51Z +%s)
$PY -I $C/herr/comparar_suricata.py --stats /var/log/suricata/stats.log --eve /var/log/suricata/eve.json \
   --desde $D --hasta $H --etiqueta 4A > $C/base-4a-suricata.json; echo "rc=$?"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); [print(k, json.dumps(d[k], ensure_ascii=False)[:700]) for k in d if k!="flujos_grandes_top"]; print("top", json.dumps(d["flujos_grandes_top"][:5])[:900])' $C/base-4a-suricata.json
echo "--- stats.log cubre desde:"; head -3 /var/log/suricata/stats.log | grep Date; ls -l /var/log/suricata/stats.log*
