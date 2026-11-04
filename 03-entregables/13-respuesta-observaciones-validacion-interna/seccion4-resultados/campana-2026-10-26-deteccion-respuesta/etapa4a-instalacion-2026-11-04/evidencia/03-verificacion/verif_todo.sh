set -u
echo "######## SENSOR1 $(date -u +%FT%TZ)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
  R=$(ls -d ~/respaldos-etapa4/sensor1-* | tail -1)
  bash ~/cf-e4/paquete/deploy/etapa4/sensor1/verificar_sensor1.sh "$R"'
echo "######## BASTION"
bash ~/cf-e4/paquete/deploy/etapa4/bastion/verificar_bastion.sh
echo "######## SRV-DMZ (CON_SUDO=1, NOPASSWD)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
  R=$HOME/respaldos-etapa4/srvdmz-20261104T015754Z
  CON_SUDO=1 bash ~/cf-e4/paquete/deploy/etapa4/srvdmz/verificar_srvdmz.sh "$R"
  echo "--- traza agente (eventos)"; sudo -n grep -o "\"evento\": \"[a-z_]*\"" /var/lib/cyberflow/agente/traza.jsonl | sort | uniq -c
  sudo -n tail -2 /var/lib/cyberflow/agente/traza.jsonl | cut -c1-400
  echo "--- v1"; systemctl is-enabled ppi-enforce-agent.timer; systemctl is-active ppi-enforce-agent.timer; sudo -n nft list tables; echo tablas-fin'
