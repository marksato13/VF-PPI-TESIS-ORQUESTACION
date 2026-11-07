set -u
# [BASTIÓN gadmin] Solo lecturas en Sensor1, bastión y srv-dmz (srv-dmz con sudo -n para leer nft y la traza).
ETQ=${1:-precheck}
echo "######## $ETQ $(date -u +%FT%TZ)"
echo "## SENSOR1"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '
p=$(systemctl show -p MainPID --value ppi-motor); A=$(tr "\0" "\n" < /proc/$p/cmdline)
echo "$A" | grep -E "^/home/.*\.(joblib|json|pkl|npy|toml)$" | while read f; do sha256sum "$f"; done
for f in $(echo "$A" | grep -A1 -E "^--(model-path|manifest-path|scaler-path|features-path|config)$" | grep "^/"); do :; done
d=$(dirname $(echo "$A" | grep -A1 -- "--model-path" | tail -1)); ls $d; sha256sum $d/* 2>/dev/null
echo "$A" | tr "\n" " " | cut -c1-900; echo
( cd ~/cyberflow-e4/ec78ca5 && sha256sum -c --quiet SHA256SUMS && echo "ec78ca5 SHA256SUMS OK" )
sha256sum /etc/suricata/suricata.yaml
sudo -n nft list ruleset | sed -E "s/counter packets [0-9]+ bytes [0-9]+/counter/" | sha256sum | sed "s/-$/ruleset-sensor1-normalizado/"
for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 suricata ppi-publicar-feed-v2 ppi-dashboard; do echo "$u pid=$(systemctl show -p MainPID --value $u) NRestarts=$(systemctl show -p NRestarts --value $u) $(systemctl is-active $u)"; done
for u in ppi-publicar-feed.timer ppi-publicar-feed; do echo "v1 $u $(systemctl is-enabled $u 2>/dev/null)/$(systemctl is-active $u)"; done
echo "procesos con --enforce/--aplicar: $(ps -eo args | grep -E -- "--(enforce|aplicar)( |$)" | grep -vc grep)"
echo "feed-v2 secuencia: $(python3 -c "import json;print(json.load(open(\"/home/m4rk/feed-v2/feed.json\"))[\"secuencia\"])")"
df -h --output=avail /home | tail -1; uptime'
echo "## BASTION"
for u in ppi-relay-eventos ppi-relay-feed.timer; do echo "$u $(systemctl is-enabled $u)/$(systemctl is-active $u) pid=$(systemctl show -p MainPID --value $u) NRestarts=$(systemctl show -p NRestarts --value $u)"; done
tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-relay-eventos)/cmdline; echo
sha256sum /opt/cyberflow/relay-v2/* /etc/systemd/system/ppi-relay-eventos.service
echo "panel desde bastion: $(curl -sk -m 6 -o /dev/null -w '%{http_code}' https://10.10.60.11:8788/)"
echo "## SRV-DMZ"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
for u in ppi-enforce-agent-v2-dmz ppi-enforce-agent.timer ppi-enforce-agent ppi-brute-lab; do echo "$u $(systemctl is-enabled $u 2>/dev/null)/$(systemctl is-active $u) pid=$(systemctl show -p MainPID --value $u) NRestarts=$(systemctl show -p NRestarts --value $u)"; done
tr "\0" " " < /proc/$(systemctl show -p MainPID --value ppi-enforce-agent-v2-dmz)/cmdline; echo
sudo -n sha256sum /opt/cyberflow/agente-v2/* /usr/local/bin/cf-feed-ssh.sh /usr/local/sbin/cf-nft-helper /etc/systemd/system/ppi-enforce-agent-v2-dmz.service
echo "tablas: [$(sudo -n nft list tables)]"; sudo -n nft list ruleset | sha256sum | sed "s/-$/ruleset-srvdmz/"
echo "eventos aplicacion: $(sudo -n grep -c "\"evento\": \"aplicacion\"" /var/lib/cyberflow/agente/traza.jsonl)"
echo "rechazos: $(sudo -n grep -o "\"motivo\": \"[a-z_][a-z_]*\"" /var/lib/cyberflow/agente/traza.jsonl | sort | uniq -c | tr "\n" " ")"
sudo -n ls -la --time-style=+%T /var/lib/cyberflow/feed'
