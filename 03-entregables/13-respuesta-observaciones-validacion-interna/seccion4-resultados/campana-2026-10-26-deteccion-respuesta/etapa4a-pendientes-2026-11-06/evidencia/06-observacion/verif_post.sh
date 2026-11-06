set -u
# [BASTIÓN gadmin] Solo lecturas tras la observación: verificar_*.sh del paquete instalado (criterios §3) en los tres
# hosts, motivos no-firma del agente con su hora, e I5 informativo en Sensor1 (no inicia nada).
P=cf-e4/paquete-b18c286
echo "######## verificar_bastion $(date -u +%FT%TZ)"; bash ~/$P/deploy/etapa4/bastion/verificar_bastion.sh; echo "rc=$?"
echo "######## verificar_sensor1"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "bash ~/$P/deploy/etapa4/sensor1/verificar_sensor1.sh; echo rc=\$?
echo '######## I5 informativo (30 min hasta la última muestra)'
/home/m4rk/cyberflow/.venv/bin/python -I ~/cyberflow-e4/herramientas-20261106/salud_captura.py i5 --eve /var/log/suricata/eve.json; echo rc=\$?"
echo "######## verificar_srvdmz (CON_SUDO=1, respaldo fase C)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 "CON_SUDO=1 bash ~/$P/deploy/etapa4/srvdmz/verificar_srvdmz.sh /home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z; echo rc=\$?
echo '######## motivos distintos de firma_invalida en la traza del agente'
sudo -n grep -nE 'feed_caducado|misma_secuencia|paquete_invalido|\"estado\": \"rechazado\"' /var/lib/cyberflow/agente/traza.jsonl | cut -c1-330"
