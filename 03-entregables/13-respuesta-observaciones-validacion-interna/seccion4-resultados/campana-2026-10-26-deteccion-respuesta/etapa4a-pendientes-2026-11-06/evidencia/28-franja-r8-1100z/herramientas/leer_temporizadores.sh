#!/usr/bin/env bash
# [LAPTOP Git Bash] A0c de la r8, INFORMATIVO y de SOLO LECTURA: temporizadores, cron y estado de apt-daily en los cuatro hosts.
# No decide nada por sí solo: si algún temporizador cae entre T_g-600 y T_g+4680, Claude avisa a Mark antes de la puerta G.
#   leer_temporizadores.sh SALIDA_NUEVA      VERSION 2026-11-08.1
set -u -o pipefail
S="${1:?uso: leer_temporizadores.sh SALIDA_NUEVA}"; [ ! -e "$S" ] || { echo "ya existe $S"; exit 2; }
mkdir "$S" || exit 2
cd "$HOME" || exit 2
O="-n -o BatchMode=yes -o ConnectTimeout=10"; K="$HOME/.ssh/id_ed25519"; B=gadmin@10.10.10.30
Q='date -u +%FT%TZ; timedatectl show -p Timezone 2>/dev/null; systemctl list-timers --all --no-pager 2>/dev/null | cut -c1-150; echo "-- activos"; systemctl is-active apt-daily.service apt-daily-upgrade.service e2scrub_all.service 2>/dev/null | tr "\n" " "; echo; echo "-- crontab"; grep -hvE "^\s*(#|$)" /etc/crontab 2>/dev/null | head; ls -l --time-style=+%FT%T%z /var/lib/apt/periodic/ 2>/dev/null'
ssh $O -i "$K" "$B" "$Q" > "$S/bastion.txt" 2>&1; echo "bastion rc=$?" | tee "$S/rc.txt"
ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 '$Q'" > "$S/sensor1.txt" 2>&1; echo "sensor1 rc=$?" | tee -a "$S/rc.txt"
ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 '$Q'" > "$S/clientes.txt" 2>&1; echo "clientes rc=$?" | tee -a "$S/rc.txt"
ssh $O -i "$K" "$B" "ssh $O -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 '$Q'" > "$S/srvdmz.txt" 2>&1; echo "srvdmz rc=$?" | tee -a "$S/rc.txt"
echo "FIN_TEMPORIZADORES (informativo)"
