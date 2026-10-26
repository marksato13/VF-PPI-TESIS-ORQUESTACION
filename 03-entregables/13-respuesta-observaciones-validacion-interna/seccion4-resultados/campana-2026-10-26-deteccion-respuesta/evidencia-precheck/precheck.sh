echo "===== RELOJES"
echo "-- sensor:"; date -u +%Y-%m-%dT%H:%M:%S.%N%z; (command -v chronyc >/dev/null && chronyc tracking 2>/dev/null | grep -Ei 'Reference|System time|Last offset|RMS' ) || echo "chrony: no disponible"
echo "-- bastion (desde el sensor via ssh):"
ssh -n -o BatchMode=yes -o ConnectTimeout=6 -i ~/.ssh/cyberflow-to-sensor gadmin@10.10.10.30 'date -u +%Y-%m-%dT%H:%M:%S.%N%z' 2>&1 | head -1 || echo "sin ruta inversa (normal)"
echo "===== INSTRUMENTACION SENSOR"
echo "-- servicios motor/captura/acumulador:"; systemctl is-active ppi-motor ppi-captura cyberflow-captura ppi-acumular 2>/dev/null
systemctl list-units --type=service --all --no-pager 2>/dev/null | grep -Ei 'ppi|cyberflow|suricata|capture' | awk '{print $1,$3,$4}'
echo "-- anillo de PCAP:"; ls -la /var/lib/ppi-motor-capture/ 2>/dev/null | tail -3; echo "ficheros:"; ls /var/lib/ppi-motor-capture/live-*.pcap 2>/dev/null | wc -l
echo "-- EVE:"; ls -la /var/log/suricata/eve.json 2>/dev/null
echo "-- motor_decision.log:"; ls -la ~/cyberflow/logs/motor_decision.log 2>/dev/null; tail -1 ~/cyberflow/logs/motor_decision.log 2>/dev/null | cut -c1-120
echo "-- acumulador csv:"; ls -la ~/cyberflow/artifacts/linea-base/multilayer-v3.csv 2>/dev/null
echo "-- espacio en disco:"; df -h / /var 2>/dev/null | awk '{print $1,$4,$5,$6}'
echo "===== ALCANCE A SERVICIOS (desde el bastion, benigno, sin atacar)"
ssh -n -o BatchMode=yes -o ConnectTimeout=6 -i ~/.ssh/cyberflow-to-sensor gadmin@10.10.10.30 '
  echo "-- DNS 10.10.10.20: resolver un nombre del laboratorio"
  dig +time=2 +tries=1 @10.10.10.20 srv-dmz.lab +short 2>&1 | head -3 || echo "dig no disponible"
  echo "-- TCP connect srv-dmz 10.10.30.10 (80/443/8081), sin enviar carga:"
  for pt in 80 443 8081; do timeout 3 bash -c "echo > /dev/tcp/10.10.30.10/$pt" 2>/dev/null && echo "  $pt ABIERTO" || echo "  $pt cerrado/filtrado"; done
' 2>&1
echo "===== RESTRICCIONES RESIDUALES (srv-dmz, via llave cyberflow-to-srv)"
ssh -n -o BatchMode=yes -o ConnectTimeout=6 -i ~/.ssh/cyberflow-to-sensor gadmin@10.10.10.30 '
ssh -n -o BatchMode=yes -o ConnectTimeout=6 -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 "
  echo agente:; systemctl is-active ppi-enforce-agent.timer ppi-enforce-agent.service 2>/dev/null
  echo nft-sets:; sudo -n nft list set inet cyberflow cyberflow_bloqueados 2>/dev/null | grep -E \"elements|timeout\" || echo \"  bloqueados: sin elements o sin permiso\"
  sudo -n nft list set inet cyberflow cyberflow_limitados 2>/dev/null | grep -E \"elements|timeout\" || echo \"  limitados: sin elements o sin permiso\"
" 2>&1 | head -12
' 2>&1 | head -15
echo "===== FIN"