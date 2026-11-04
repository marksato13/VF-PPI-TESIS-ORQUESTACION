set -eu
R="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-recuperacion"
S=/c/Users/markp/AppData/Local/Temp/claude/f17b3819211dc686/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad/cc
T=$(mktemp -d); cd "$R"; git archive fc55674 deploy/etapa4/cierre deploy/etapa4/sensor1 | tar -x -C "$T"
C="$T/deploy/etapa4/cierre"; S1="$T/deploy/etapa4/sensor1"
echo "== Sensor1 herr"
bash "$S/subir.sh" sensor /home/m4rk/cf-e4/cierre4a/herr "$C/cf-primer-pcap.sh" "$C/etapa4-primer-pcap.conf" "$C/modo-panel-v2.conf" \
  "$C/cierre4a_sensor1.sh" "$C/revertir_cierre4a.sh" "$C/muestreo_fino.py" "$C/CRITERIOS-ENSAYO-ANILLO.md" \
  "$S1/clasificar_periodo.py" "$S1/comparar_suricata.py" "$S1/ensayo_clasificar_periodo.py"
echo "== Bastión"
bash "$S/subir.sh" bastion /home/gadmin/cierre4a "$C/cierre4a_bastion.sh" "$C/revertir_cierre4a.sh"
