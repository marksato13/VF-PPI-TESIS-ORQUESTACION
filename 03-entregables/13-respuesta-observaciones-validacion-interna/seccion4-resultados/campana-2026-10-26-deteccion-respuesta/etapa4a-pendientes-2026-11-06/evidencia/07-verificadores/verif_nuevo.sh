set -u
# [BASTIÓN gadmin] SOLO LECTURAS: verificadores corregidos (paquete a1cea5e) en bastión, Sensor1 y srv-dmz.
# No reinstala, no reinicia, no cambia nada. Cada bloque termina con su código de salida.
P=cf-e4/paquete-a1cea5e
echo "######## paquete $P  $(date -u +%FT%TZ)"
echo "######## verificar_bastion.sh (gadmin, sin sudo)"
bash ~/$P/deploy/etapa4/bastion/verificar_bastion.sh; echo "rc=$?"
echo "######## verificar_sensor1.sh (m4rk, sin sudo)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "date -u +%FT%TZ; bash ~/$P/deploy/etapa4/sensor1/verificar_sensor1.sh; echo rc=\$?"
echo "######## verificar_srvdmz.sh (sin cambios; CON_SUDO=1 solo lecturas, respaldo fase C)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 "date -u +%FT%TZ; CON_SUDO=1 bash ~/$P/deploy/etapa4/srvdmz/verificar_srvdmz.sh /home/adminsrvdmz/respaldos-etapa4/srvdmz-p4-fase-c-20261106T043944Z; echo rc=\$?"
echo "######## fin $(date -u +%FT%TZ)"
