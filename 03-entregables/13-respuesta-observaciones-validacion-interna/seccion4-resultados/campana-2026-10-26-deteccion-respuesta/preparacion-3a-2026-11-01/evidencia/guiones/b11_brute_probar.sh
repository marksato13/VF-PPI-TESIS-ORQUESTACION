#!/usr/bin/env bash
# PASO3A b11 — desde el bastion: 5 peticiones benignas de PREPARACION desde la Kali al endpoint ya arrancado en b10.
# La credencial de control se lee de la unidad en srv-dmz y viaja como primera linea de stdin: no se imprime ni se guarda.
set -u
SRV="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10"
KALI="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30"
UA="cf-preparacion-paso3a-20261101T0523Z"
echo "## b11 $(date -u +%FT%T.%3NZ)"
$SRV -n 'echo "  servicio: $(systemctl is-active ppi-brute-lab)/$(systemctl is-enabled ppi-brute-lab) PID=$(systemctl show -p MainPID --value ppi-brute-lab)"'
N0=$($SRV -n 'wc -l < /opt/brute-lab/brute.log')
UC=$($SRV -n 'systemctl show -p Environment --value ppi-brute-lab' | tr ' ' '\n' | awk -F= '$1=="USUARIO"{u=$2} $1=="CLAVE"{c=$2} END{print u":"c}')
[ "${#UC}" -gt 2 ] || { echo "PARAR: no se pudo leer la credencial de control"; exit 2; }
echo "## peticiones desde la Kali (agente $UA)"
CUERPO='p(){ t=$(date -u +%FT%T.%3NZ); r=$(curl -s -o /dev/null -A "$UA" -w "%{http_code} t=%{time_total}" --max-time 3 "$@" 2>&1); echo "  $t $r"; }
echo "  [sin credenciales]"; p http://10.10.30.10:18081/auth
echo "  [credencial ficticia]"; p -u fake:fake-paso3a http://10.10.30.10:18081/auth
echo "  [credencial de control]"; p -u "$UC" http://10.10.30.10:18081/auth
echo "  [ruta inexistente: 404, NO es fallo de auth]"; p http://10.10.30.10:18081/no-existe
echo "  [segunda sin credenciales]"; p http://10.10.30.10:18081/auth'
{ printf '%s\n' "$UC"; printf '%s\n' "$CUERPO"; } | $KALI "read -r UC; export UC; export UA=$UA; bash -s"
unset UC
sleep 1
echo "## registro del servidor (lineas nuevas)"
$SRV -n "tail -n +$((N0+1)) /opt/brute-lab/brute.log | sed 's/^/  /'"
echo "## fin $(date -u +%FT%T.%3NZ)"
