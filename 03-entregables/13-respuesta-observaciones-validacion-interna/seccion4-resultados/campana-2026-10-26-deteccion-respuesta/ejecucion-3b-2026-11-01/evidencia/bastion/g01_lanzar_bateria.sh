#!/usr/bin/env bash
# PASO3B g01 — bastion: lanza la bateria de 25 episodios DESPUES del control normal (>= 08:05:00Z).
#  1) comprueba la hora (aborta si es antes del fin del control);
#  2) comprueba la sombra en sensor y srv-dmz (solo lectura);
#  3) comprobacion MINIMA del endpoint de fuerza bruta desde el bastion (activo + 401), marcada como PREPARACION;
#  4) relojes p10b (incluye una sesion SSH corta a la Kali, registrada);
#  5) UNA sesion SSH a la Kali para lanzar el generador autorizado en sesion persistente (setsid nohup) y salir;
#  6) programa en el bastion una segunda comprobacion minima del endpoint para el hueco tras el episodio 9 (desde el
#     bastion, no desde la Kali; no es trafico de la Kali).
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; HASTA=$(date -d 2026-11-01T08:05:00Z +%s)
[ "$(date +%s)" -ge "$HASTA" ] || { echo "PARAR: el control termina a las 08:05:00Z; ahora $(date -u +%T)"; exit 2; }
echo "## g01 $(date -u +%FT%T.%3NZ)"
echo "## sombra (sensor)"
ssh -n sensor1 'P=$(systemctl show -p MainPID --value ppi-motor); echo "  ppi-motor $(systemctl is-active ppi-motor) PID=$P NR=$(systemctl show -p NRestarts --value ppi-motor) --enforce=$(tr "\0" " " < /proc/$P/cmdline | grep -c -- --enforce)"'
echo "## sombra (srv-dmz) y endpoint"
ssh -n srvdmz 'echo "  timer $(systemctl is-active ppi-enforce-agent.timer)/$(systemctl is-enabled ppi-enforce-agent.timer) servicio $(systemctl is-active ppi-enforce-agent.service)"; T=$(sudo -n nft list tables 2>&1); echo "  nft rc=$? inet cyberflow: $(echo "$T" | grep -c "inet cyberflow")"'
bash $B/c05_brute_prep.sh minima
echo "## relojes (p10b)"
bash $B/p10b_relojes.sh | tee -a $B/relojes-3b.log
echo "## lanzamiento en la Kali [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): lanzar el generador]"
ssh -o BatchMode=yes kali 'set -u; K=$HOME/cf-3b-20261101T0721Z; cd $HOME/cf-campana-A/scripts
sha256sum -c $K/sha256-esperado.txt | sed "s/^/  /"
[ -e $K/corrida ] && { echo "PARAR: ya existe $K/corrida"; exit 2; }
CMD="python3 -u /home/adminatacante/cf-campana-A/scripts/generar_campana.py --config /home/adminatacante/cf-campana-A/escenarios/escenarios.json --salida-dir $K/corrida --autorizado"
echo "$CMD" > $K/comando.txt; date -u +%FT%T.%3NZ > $K/lanzado.txt
setsid nohup bash -c "$CMD > $K/generador.stdout 2> $K/generador.stderr; echo \$? > $K/generador.rc; date -u +%FT%T.%3NZ > $K/terminado.txt" > /dev/null 2>&1 < /dev/null &
sleep 3; echo "  comando: $CMD"; echo "  pid(s): $(pgrep -f "generar_campana.py --config" | tr "\n" " ")"; head -3 $K/generador.stdout | sed "s/^/  | /"'
echo "## fin acceso Kali $(date -u +%FT%T.%3NZ)"
# segunda comprobacion minima del endpoint (desde el bastion) a los 2600 s: hueco estimado tras el episodio 9
setsid nohup bash -c "sleep 2600; bash $B/c05_brute_prep.sh minima >> $B/brute-pre-ep10.log 2>&1" > /dev/null 2>&1 < /dev/null &
echo "  comprobacion programada (PID $!) para ~$(date -u -d @$(( $(date +%s) + 2600 )) +%T)Z en $B/brute-pre-ep10.log"
echo "## fin $(date -u +%FT%T.%3NZ)"
