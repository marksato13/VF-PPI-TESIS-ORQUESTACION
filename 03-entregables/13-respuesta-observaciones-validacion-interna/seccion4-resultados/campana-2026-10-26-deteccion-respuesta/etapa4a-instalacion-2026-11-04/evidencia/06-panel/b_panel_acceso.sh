echo "--- desde el BASTION"
curl -sk --max-time 10 -o - -w '\nGET /api/status -> HTTP %{http_code}\n' https://10.10.60.11:8788/api/status | tail -c 300
curl -sk --max-time 10 -o - -w '\nPOST /api/demo/preparar -> HTTP %{http_code}\n' -X POST -H 'X-CyberFlow: 1' -d '' https://10.10.60.11:8788/api/demo/preparar | tail -c 300
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'systemctl cat cyberflow-panel-acceso | grep -vE "^\s*#" | grep -v "^$" | head -20; sudo -n nft list ruleset 2>/dev/null | grep -n -B2 -A2 8788 | head -20; ls -l ~/feed/peticiones/'
