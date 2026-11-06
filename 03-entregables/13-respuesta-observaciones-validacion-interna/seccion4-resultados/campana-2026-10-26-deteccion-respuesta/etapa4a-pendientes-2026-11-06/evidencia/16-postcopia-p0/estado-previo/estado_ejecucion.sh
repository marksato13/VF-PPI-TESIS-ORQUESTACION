#!/usr/bin/env bash
# [LAPTOP Git Bash] -> bastión -> clientes / Sensor1 / srv-dmz. SOLO LECTURA: estado de generadores, muestreadores,
# servicios, temporizadores, cron y at relacionados con E-carga. No arranca, no para y no escribe nada.
set -uo pipefail
K="$HOME/.ssh/id_ed25519"; B="gadmin@10.10.10.30"; SO=(-o BatchMode=yes -o ConnectTimeout=10)
LECTURA='
echo "== $(hostname) $(whoami) $(date -u +%FT%TZ)"
echo "-- procesos E-carga (pgrep -af)"
pgrep -af "clientes_lab|salud_captura|obs_pcap|muestreo_fino|muestreo_s14|muestreo_bastion|sensor1_muestreadores|generadores\.sh|obs_muestreo|ecarga" | grep -v pgrep || echo "(ninguno)"
echo "-- temporizadores (todos)"; systemctl list-timers --all --no-pager --no-legend 2>&1 | grep -iE "cyberflow|ecarga|lab|muestreo|obs" || echo "(ninguno relacionado)"
echo "-- unidades transitorias run-*"; systemctl list-units --all --no-pager --no-legend "run-*" 2>&1 | grep . || echo "(ninguna)"
echo "-- unidades de usuario"; systemctl --user list-units --all --no-pager --no-legend 2>&1 | grep -iE "cyberflow|ecarga|lab|muestreo" || echo "(ninguna relacionada)"
echo "-- crontab"; crontab -l 2>&1 | grep -v "^#" | grep . || echo "(vacío)"
echo "-- at"; if command -v atq >/dev/null; then atq 2>&1 | grep . || echo "(vacía)"; else echo "(at no instalado)"; fi
'
CLIENTES='
for u in cyberflow-lab.target cyberflow-lab-ofimatica cyberflow-lab-navegacion cyberflow-lab-descargas cyberflow-lab-aplicacion cyberflow-lab-ligero cyberflow-lab-erratico; do
  printf "%-28s active=%s enabled=%s\n" "$u" "$(systemctl is-active $u 2>&1)" "$(systemctl is-enabled $u 2>&1)"; done
'
ssh "${SO[@]}" -i "$K" "$B" "bash -s" <<EOF
set -u
O="-o BatchMode=yes -o ConnectTimeout=10"
echo "######## BASTIÓN"; bash -c '$LECTURA'; echo "rc=\$?"
echo "######## CLIENTES"; ssh \$O -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'bash -s' <<'X'; echo "rc=\$?"
$LECTURA
$CLIENTES
X
echo "######## SENSOR1"; ssh \$O -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'bash -s' <<'X'; echo "rc=\$?"
$LECTURA
X
echo "######## SRV-DMZ"; ssh \$O -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'bash -s' <<'X'; echo "rc=\$?"
$LECTURA
X
EOF
echo "rc_bastion_ssh=$?"
