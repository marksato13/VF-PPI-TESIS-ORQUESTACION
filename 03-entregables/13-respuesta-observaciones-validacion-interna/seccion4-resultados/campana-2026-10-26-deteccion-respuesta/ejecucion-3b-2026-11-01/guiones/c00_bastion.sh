#!/usr/bin/env bash
# PASO3B c00 — bastion (solo lectura): alcance de todos los hosts, servicios del laboratorio (HTTP, HTTPS, DNS) y
# relojes (metodo p10b: sesion SSH persistente, 9 muestras). Peticiones de PREPARACION desde el bastion
# (10.10.10.30, excluido del motor por --excluir); se registran con su hora para dejarlas fuera del control.
set -u
echo "## c00 bastion $(hostname) $(date -u +%FT%T.%3NZ)  [PREPARACION]"
for h in sensor1 kali srvdmz clientes admin; do
  o=$(ssh -n -o BatchMode=yes -o ConnectTimeout=6 $h 'echo "$(hostname) $(whoami) up=$(uptime -p) load=$(cut -d" " -f1-3 /proc/loadavg)"' 2>&1); echo "  $h rc=$? $o"
done
echo "## servidor protegido y DNS desde el bastion [PREPARACION $(date -u +%FT%T.%3NZ)]"
curl -s -o /dev/null -m 5 -w '  http://10.10.30.10/ %{http_code} %{time_total}s\n' http://10.10.30.10/
curl -sk -o /dev/null -m 5 -w '  https://10.10.30.10/ %{http_code} %{time_total}s\n' https://10.10.30.10/
echo "  dig @10.10.10.20 prep3b.lab-ppi -> '$(dig +time=2 +tries=1 @10.10.10.20 prep3b.lab-ppi +short 2>&1 | tr '\n' ' ')' (esperado 10.10.30.10)"
echo "  dig @10.10.10.20 noexiste-$(date +%s).lab-ppi status: $(dig +time=2 +tries=1 @10.10.10.20 noexiste-$(date +%s).lab-ppi 2>&1 | grep -o 'status: [A-Z]*')"
echo "## fin alcance $(date -u +%FT%T.%3NZ)"
