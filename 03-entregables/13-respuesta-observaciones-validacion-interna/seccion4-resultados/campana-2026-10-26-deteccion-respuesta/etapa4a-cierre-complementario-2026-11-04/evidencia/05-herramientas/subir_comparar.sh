set -eu
R="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-recuperacion"
S=/c/Users/markp/AppData/Local/Temp/claude/f17b3819211dc686/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad/cc
T=$(mktemp -d); cd "$R"
# Se resube TODO herr para que SHA256SUMS siga cubriendo cada fichero
for f in deploy/etapa4/cierre/*; do cp "$f" "$T/"; done
cp deploy/etapa4/sensor1/clasificar_periodo.py deploy/etapa4/sensor1/comparar_suricata.py deploy/etapa4/sensor1/ensayo_clasificar_periodo.py "$T/"
rm "$T/cierre4a_bastion.sh"
bash "$S/subir.sh" sensor /home/m4rk/cf-e4/cierre4a/herr "$T"/*
