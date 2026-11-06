set -u
# [SENSOR1 m4rk] SOLO LECTURA: intensidad de la ventana fija 04:50-05:50Z del 06-nov con el MISMO método y los mismos
# parámetros que el ensayo del anillo (comparar_suricata.py del candidato, ráfaga 5000/8 s, flujo grande 1000).
# Es una medida retrospectiva y descriptiva: O12 sigue siendo «carga insuficiente» y no se reevalúa.
C=~/cyberflow-e4/ec78ca5/deploy/etapa4/sensor1/comparar_suricata.py
[ -f "$C" ] || C=~/cf-e4/paquete-a1cea5e/deploy/etapa4/sensor1/comparar_suricata.py
echo "herramienta: $C $(sha256sum "$C" | cut -c1-16)"
python3 -I "$C" --stats-eve /var/log/suricata/eve.json --eve /var/log/suricata/eve.json \
  --desde 1793940600 --hasta 1793944200 --etiqueta obs-06nov-0450; echo "rc=$?"
