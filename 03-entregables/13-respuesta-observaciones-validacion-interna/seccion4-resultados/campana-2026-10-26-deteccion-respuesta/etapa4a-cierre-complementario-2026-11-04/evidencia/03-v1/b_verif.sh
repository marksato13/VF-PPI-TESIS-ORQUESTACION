set -u
# [BASTIÓN gadmin] Verificación del relé v1 retirado (solo lectura).
EV=$(ls -d /home/gadmin/cierre4a/sudo-bastion-* 2>/dev/null | tail -n 1); echo "evidencia: $EV"; [ -n "$EV" ] && tail -n 15 $EV/salida.txt
for u in ppi-relay-feed.timer ppi-relay-feed.service ppi-relay-eventos.service; do
  printf '%s ' $u; systemctl show $u -p ActiveState -p UnitFileState -p MainPID --value | tr '\n' ' '; echo; done
systemctl list-timers --all --no-pager | grep relay || echo "sin temporizadores relay"
journalctl --no-pager -u ppi-relay-feed --since "-20min" | tail -n 3
journalctl --no-pager -u ppi-relay-eventos --since "-3min" | tail -n 3
