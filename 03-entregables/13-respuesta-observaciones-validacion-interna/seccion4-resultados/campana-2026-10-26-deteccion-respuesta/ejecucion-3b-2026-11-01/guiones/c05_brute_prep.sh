#!/usr/bin/env bash
# PASO3B c05 — bastion: comprobacion de PREPARACION del endpoint de fuerza bruta desde el BASTION (10.10.10.30,
# excluido del motor), no desde la Kali. Uso: c05_brute_prep.sh [completa|minima]
#   completa: sin credencial (401), ficticia (401), UNA de control (200), ruta inexistente (404)
#   minima  : servicio activo + una sin credencial (401)  -> antes del primer episodio de fuerza bruta
# La credencial de control se lee de la unidad en srv-dmz a una variable y no se imprime ni se guarda.
set -u
MODO=${1:-completa}
SRV="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10"
UA="cf-preparacion-paso3b-20261101T0721Z"
echo "## c05 $MODO $(date -u +%FT%T.%3NZ)  [PREPARACION, origen bastion 10.10.10.30, agente $UA]"
$SRV -n 'echo "  servicio: $(systemctl is-active ppi-brute-lab)/$(systemctl is-enabled ppi-brute-lab) PID=$(systemctl show -p MainPID --value ppi-brute-lab)"'
N0=$($SRV -n 'wc -l < /opt/brute-lab/brute.log')
p(){ t=$(date -u +%FT%T.%3NZ); r=$(curl -s -o /dev/null -A "$UA" -w "%{http_code} t=%{time_total}" --max-time 3 "$@" 2>&1); echo "  $t $r"; }
echo "  [sin credenciales, esperado 401]"; p http://10.10.30.10:18081/auth
if [ "$MODO" = completa ]; then
  UC=$($SRV -n 'systemctl show -p Environment --value ppi-brute-lab' | tr ' ' '\n' | awk -F= '$1=="USUARIO"{u=$2} $1=="CLAVE"{c=$2} END{print u":"c}')
  [ "${#UC}" -gt 2 ] || { echo "PARAR: no se pudo leer la credencial de control"; exit 2; }
  echo "  [credencial ficticia, esperado 401]"; p -u fake:fake-paso3b http://10.10.30.10:18081/auth
  echo "  [UNA credencial de control, esperado 200]"; p -u "$UC" http://10.10.30.10:18081/auth
  unset UC
  echo "  [ruta inexistente, esperado 404]"; p http://10.10.30.10:18081/no-existe
fi
sleep 1
echo "## registro del servidor (lineas nuevas; sin credenciales)"
$SRV -n "tail -n +$((N0+1)) /opt/brute-lab/brute.log | sed 's/^/  /'"
echo "## fin $(date -u +%FT%T.%3NZ)"
