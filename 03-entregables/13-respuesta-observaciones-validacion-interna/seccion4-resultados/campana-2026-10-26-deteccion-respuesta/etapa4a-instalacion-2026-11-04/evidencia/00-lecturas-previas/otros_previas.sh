set -u
echo "### BASTION $(date -u +%FT%TZ)"; ls -ld ~/cf-e4 ~/respaldos-etapa4 ~/relay-v2 2>&1; timedatectl show -p NTPSynchronized
systemctl list-units --all --no-legend '*relay*' | awk '{print $1,$3,$4}'
sudo -n -l 2>&1 | head -8
echo "### SRV-DMZ"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'date -u +%FT%TZ; ls -ld ~/cf-e4 ~/respaldos-etapa4 /var/lib/cyberflow 2>&1; timedatectl show -p NTPSynchronized; sudo -n nft list tables; echo "nft rc=$?"; id cfagente 2>&1; sudo -n grep -h requiretty /etc/sudoers /etc/sudoers.d/* 2>&1 | head -3; df -h /home | tail -1'
echo "### KALI"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'date -u +%FT%T.%3NZ; pgrep -af "nmap|hping|curl|dig|hydra|generar_campana" || echo sin-procesos-de-ataque'
