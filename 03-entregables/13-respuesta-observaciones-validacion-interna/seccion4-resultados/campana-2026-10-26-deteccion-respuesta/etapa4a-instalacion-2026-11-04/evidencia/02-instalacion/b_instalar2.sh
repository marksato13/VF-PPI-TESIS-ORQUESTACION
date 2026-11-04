set -u
echo "### srv-dmz: reversión de la fase 1 parcial $(date -u +%FT%TZ)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
  R=$HOME/respaldos-etapa4/srvdmz-20261104T015754Z; echo "respaldo: $R"
  bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/revertir_srvdmz.sh "$R"' || { echo "PARADA reversión srv-dmz"; exit 1; }
echo "### 4.4 srv-dmz: instalación (adminsrvdmz NOPASSWD, autorizado por Mark)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
  R=$HOME/respaldos-etapa4/srvdmz-20261104T015754Z; echo "respaldo: $R"
  bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/instalar_srvdmz_sombra.sh "$R" ~/cf-e4/paquete ~/cf-e4/pub.pem ~/cf-e4/cyberflow-feed-v2-srv.pub' || { echo "PARADA srv-dmz"; exit 1; }
echo "### 4.5 Sensor1 llave del relé"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  R=$(ls -d ~/respaldos-etapa4/sensor1-* | tail -1); echo "respaldo: $R"
  bash ~/cf-e4/paquete/deploy/etapa4/sensor1/instalar_sensor1_sombra.sh llave-rele "$R" ~/cf-e4/cyberflow-feed-v2-sensor.pub' || { echo "PARADA llave-rele"; exit 1; }
echo "### 4.6 bastión relé v2"
sudo -n true && echo "sudo vigente" || { echo "PARADA sin sudo vigente en el bastión"; exit 1; }
R=$(ls -d ~/respaldos-etapa4/bastion-* | tail -1); echo "respaldo: $R"
bash ~/cf-e4/paquete/deploy/etapa4/bastion/instalar_bastion_sombra.sh instalar "$R" ~/cf-e4/paquete ~/cf-e4/pub.pem
