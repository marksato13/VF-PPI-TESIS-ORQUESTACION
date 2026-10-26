echo "===== RELOJ bastion"; date -u +%Y-%m-%dT%H:%M:%S.%N%z; (command -v chronyc >/dev/null && chronyc tracking 2>/dev/null | grep -Ei 'Reference|System time|Last offset') || echo "chrony: no disponible"
echo "===== DNS 10.10.10.20 (benigno, un nombre de laboratorio)"
dig +time=2 +tries=1 @10.10.10.20 srv-dmz.lab +short 2>&1 | head -3 || echo "dig no disponible"
dig +time=2 +tries=1 @10.10.10.20 www.example.com +short 2>&1 | head -2
echo "===== TCP connect a srv-dmz 10.10.30.10 (sin carga)"
for pt in 80 443 8081; do timeout 3 bash -c "echo > /dev/tcp/10.10.30.10/$pt" 2>/dev/null && echo "  $pt ABIERTO" || echo "  $pt cerrado/filtrado"; done
echo "===== HTTP HEAD a 10.10.30.10 (recurso de prueba, 1 peticion)"
curl -s -o /dev/null -w "  / -> %{http_code}\n" --max-time 4 http://10.10.30.10/ 2>&1 || echo "  curl fallo"
curl -s -o /dev/null -w "  /login -> %{http_code}\n" --max-time 4 http://10.10.30.10/login 2>&1
curl -s -o /dev/null -w "  :8081/ -> %{http_code}\n" --max-time 4 http://10.10.30.10:8081/ 2>&1
echo "===== KALI 10.10.20.30 (debe estar apagada en preparacion)"
timeout 3 bash -c "echo > /dev/tcp/10.10.20.30/22" 2>/dev/null && echo "  22 ABIERTO (encendida)" || echo "  sin ruta/apagada (esperado)"
echo "===== AGENTE / nft en srv-dmz (via cyberflow-to-srv)"
ssh -n -o BatchMode=yes -o ConnectTimeout=6 -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
  echo agente_timer:; systemctl is-active ppi-enforce-agent.timer 2>/dev/null
  echo nft_bloqueados:; sudo -n nft list set inet cyberflow cyberflow_bloqueados 2>/dev/null | grep -E "elements" || echo "  sin elements o sin sudo"
  echo nft_limitados:; sudo -n nft list set inet cyberflow cyberflow_limitados 2>/dev/null | grep -E "elements" || echo "  sin elements o sin sudo"
' 2>&1 | head -12
echo "===== relay del feed en el bastion"
systemctl is-active ppi-relay-feed.timer ppi-relay-feed.service 2>/dev/null; ls -la ~/relay-feed.sh 2>/dev/null
echo "===== FIN"