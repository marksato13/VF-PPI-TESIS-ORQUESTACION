#!/usr/bin/env bash
# PASO3A b10 — desde el bastion. Restaura ppi-brute-lab (start, sin enable) y lo comprueba con 5 peticiones benignas
# marcadas como PREPARACION desde la Kali. La credencial de control se lee de la unidad en srv-dmz y se pasa por
# stdin a la Kali: no se imprime ni se guarda. Reversion: sudo systemctl stop ppi-brute-lab (estado previo: inactive/disabled).
set -u
SRV="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10"
KALI="ssh -o BatchMode=yes -i $HOME/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30"
UA="cf-preparacion-paso3a-20261101T0523Z"
echo "## b10 $(date -u +%FT%T.%3NZ)"
$SRV -n 'echo "  antes: $(systemctl is-active ppi-brute-lab)/$(systemctl is-enabled ppi-brute-lab)  lineas log=$(wc -l < /opt/brute-lab/brute.log)"; sha256sum /opt/brute-lab/app.py /etc/systemd/system/ppi-brute-lab.service | sed "s/^/  /"'
$SRV -n 'sudo -n systemctl start ppi-brute-lab; echo "  [$(date -u +%T.%3N)] start rc=$?"; sleep 2; echo "  despues: $(systemctl is-active ppi-brute-lab)/$(systemctl is-enabled ppi-brute-lab) PID=$(systemctl show -p MainPID --value ppi-brute-lab)"; echo "  escucha 18081: $(ss -ltnH "sport = :18081" | awk "{print \$4}")"'
N0=$($SRV -n 'wc -l < /opt/brute-lab/brute.log')
UC=$($SRV -n 'systemctl show -p Environment --value ppi-brute-lab' | tr ' ' '\n' | awk -F= '$1=="USUARIO"{u=$2} $1=="CLAVE"{c=$2} END{print u":"c}')
[ "${#UC}" -gt 2 ] || { echo "PARAR: no se pudo leer la credencial de control de la unidad"; exit 2; }
echo "## peticiones desde la Kali (agente $UA)"
printf '%s\n' "$UC" | $KALI "UA=$UA bash -s" <<'K'
read -r UC
p(){ t=$(date -u +%FT%T.%3NZ); r=$(curl -s -o /dev/null -A "$UA" -w '%{http_code} t=%{time_total}' --max-time 3 "$@" 2>&1); echo "  $t $r"; }
echo "  [sin credenciales]";        p http://10.10.30.10:18081/auth
echo "  [credencial ficticia]";     p -u fake:fake-paso3a http://10.10.30.10:18081/auth
echo "  [credencial de control]";   p -u "$UC" http://10.10.30.10:18081/auth
echo "  [ruta inexistente: 404, NO es fallo de auth]"; p http://10.10.30.10:18081/no-existe
echo "  [segunda sin credenciales]"; p http://10.10.30.10:18081/auth
K
unset UC
sleep 1
echo "## registro del servidor (lineas nuevas)"
$SRV -n "tail -n +$((N0+1)) /opt/brute-lab/brute.log | sed 's/^/  /'"
echo "## fin $(date -u +%FT%T.%3NZ)"
