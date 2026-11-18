P=~/cf-e4/paquete-a1cea5e/deploy/etapa4/sensor1; PY=~/cyberflow/.venv/bin/python; S=~/cf-e4/4c
echo "$(date -u +%FT%TZ)"
$PY $P/clasificar_periodo.py --salud-captura ~/cyberflow-e4/herramientas-20261106/salud_captura.py --muestras $S/salud/muestras.jsonl --salida $S/clasificacion-control --desde 1794372300 --hasta 1794374100 --suricata-eve /var/log/suricata/eve.json 2>&1 | tail -30
echo "--- salud: hueco máximo"; python3 - <<'PY'
import json,os
t=[json.loads(l)["t"] for l in open(os.path.expanduser("~/cf-e4/4c/salud/muestras.jsonl")) if l.strip()]
print("muestras",len(t),"hueco máx %.1f s"%max(b-a for a,b in zip(t,t[1:])))
PY
echo "--- ciclos del motor (máx duración en la ventana)"; python3 - <<'PY'
import json,os
c=[json.loads(l) for l in open(os.path.expanduser("~/cyberflow/logs/_state-e4/ciclos.jsonl")) if l.strip()]
c=[x for x in c if 1794372300<=x.get("fin_ciclo",0)<=1794374100]; print("ciclos",len(c),"máx %.2f s"%max(x["duracion_s"] for x in c))
PY
echo "--- verificador sensor1 (umbral alfa 0,01)"; bash ~/cf-b/verif-B/sensor1/verificar_sensor1.sh 2>&1 | tail -8
