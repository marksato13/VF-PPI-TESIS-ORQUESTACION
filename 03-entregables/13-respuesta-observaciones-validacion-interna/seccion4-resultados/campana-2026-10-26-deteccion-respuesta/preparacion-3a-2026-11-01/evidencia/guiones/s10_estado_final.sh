#!/usr/bin/env bash
# PASO3A s10 — desde el bastion, SOLO LECTURA: estado final del 3A en sensor, srv-dmz, Kali y clientes.
set -u
echo "## s10 $(date -u +%FT%T.%3NZ)"
ssh -n -o BatchMode=yes sensor1 '
cd ~/cyberflow
for u in ppi-motor ppi-motor-capture suricata ppi-publicar-feed.timer; do echo "  $u $(systemctl show -p ActiveState,MainPID,NRestarts,UnitFileState $u | tr "\n" " ")"; done
P=$(systemctl show -p MainPID --value ppi-motor)
echo "  --enforce en argv: $(tr "\0" " " < /proc/$P/cmdline | grep -c -- --enforce)  en unidad: $(systemctl cat ppi-motor | grep -c -- --enforce)"
sha256sum scripts/engine/motor_decision.py scripts/engine/motor_incremental.py scripts/engine/heuristicos.py scripts/engine/publicar_feed.py scripts/engine/escalada.py artifacts/preliminar/limpio-2026-10/*.joblib | cut -c1-16,65- | sed "s/^/  /"
echo "  trazas journal motor desde 05:20Z: $(sudo -n journalctl --no-pager -u ppi-motor --since "2026-11-01 05:20:00 UTC" | grep -ciE "traceback|exception")"
echo "  ultimo ciclo: $(tail -n1 logs/_state/ciclos.jsonl | python3 -c "import json,sys,time; c=json.loads(sys.stdin.read()); print(\"hace %.0f s, dur %.2f s, pendientes %s\" % (time.time()-c[\"fin_ciclo\"], c[\"duracion_s\"], c[\"ventanas_pendientes\"]))")"
echo "  herramientas3b: $(cd ~/cf-paso3a-20261101T0523Z/herramientas3b && sha256sum *.py | cut -c1-16,65- | tr "\n" " ")"
'
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '
for u in ppi-enforce-agent.timer ppi-brute-lab.service lab-web-http.service lab-web-https.service; do echo "  srv $u active=$(systemctl is-active $u) enabled=$(systemctl is-enabled $u 2>&1)"; done
echo "  srv tabla inet cyberflow: $(sudo -n nft list tables 2>&1 | grep -c "inet cyberflow")"
echo "  srv brute.log: $(wc -l < /opt/brute-lab/brute.log) lineas"'
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'echo "  kali carga: $(ps -eo comm= | grep -cE "^(curl|nmap|dig|hping3)$")  generador vivo: $(ps -eo args= | grep -E "^python3 .*generar_campana" | grep -vc grep)"'
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'echo "  clientes target=$(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target) perfiles_activos=$(for s in ofimatica navegacion descargas aplicacion ligero erratico; do systemctl is-active cyberflow-lab-$s; done | grep -c ^active) envoltorio=$(ps -eo args= | grep -E "^/usr/bin/python3 .*clientes_factor1" | grep -vc grep)"'
echo "  dns $(dig +time=2 +tries=1 @10.10.10.20 final$(date +%s).lab-ppi +short | tr "\n" " ") http $(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://10.10.30.10/) https $(curl -sk -o /dev/null -w "%{http_code}" --max-time 3 https://10.10.30.10/) auth_sin_cred $(curl -s -o /dev/null -w "%{http_code}" --max-time 3 -A cf-preparacion-paso3a-estado-final http://10.10.30.10:18081/auth)"
echo "## fin"
