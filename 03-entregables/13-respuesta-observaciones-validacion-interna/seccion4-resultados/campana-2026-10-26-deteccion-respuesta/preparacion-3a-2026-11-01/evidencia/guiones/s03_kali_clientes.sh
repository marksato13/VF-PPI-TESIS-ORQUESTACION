#!/usr/bin/env bash
# PASO3A s03 — desde el bastion: Kali sin carga y estado de clientes (solo lectura)
set -u
echo "## s03 $(date -u +%FT%T.%3NZ)"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'echo "  kali: procesos de carga (curl, nmap, dig, python3 generar): $(ps -eo comm= | grep -cE "^(curl|nmap|dig)$") $(pgrep -fc "python3 .*generar_campana")  ip=$(hostname -I)  date=$(date -u +%T)"; ls -d ~/cf-* | tr "\n" " "; echo; sha256sum ~/cf-campana-A/scripts/generar_campana.py ~/cf-campana-A/scripts/esquema_campana.py ~/cf-campana-A/escenarios/escenarios.json 2>&1 | sed "s/^/  /"; ls ~/cf-campana-A ~/cf-campana-A/* 2>&1 | head -30 | sed "s/^/   /"'
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'echo "  clientes: target=$(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target) TZ=$(date +%Z) local=$(date "+%a %H:%M")"; for s in ofimatica navegacion descargas aplicacion ligero erratico; do echo "   cyberflow-lab-$s $(systemctl is-active cyberflow-lab-$s) NR=$(systemctl show -p NRestarts --value cyberflow-lab-$s)"; done; echo "  envoltorio factor1: $(ls -la ~/cf-paso2-20261101T0254Z/clientes_factor1.py 2>&1)"; sha256sum ~/cf-paso2-20261101T0254Z/clientes_factor1.py ~/laboratorio/clientes_lab.py ~/cf-paso2-20261101T0254Z/*.sh 2>&1 | sed "s/^/   /"; echo "  procesos envoltorio vivos: $(pgrep -fc "[c]lientes_factor1.py")"'
echo "## dns lab-ppi y web desde el bastion"
for n in prueba1.lab-ppi x$(date +%s).lab-ppi; do echo "  dig @10.10.10.20 $n -> $(dig +time=2 +tries=1 @10.10.10.20 $n +short 2>&1 | tr '\n' ' ')"; done
echo "  http $(curl -s -o /dev/null -w '%{http_code} %{time_total}s' --max-time 3 http://10.10.30.10/)  https $(curl -sk -o /dev/null -w '%{http_code} %{time_total}s' --max-time 3 https://10.10.30.10/)"
echo "## fin"
