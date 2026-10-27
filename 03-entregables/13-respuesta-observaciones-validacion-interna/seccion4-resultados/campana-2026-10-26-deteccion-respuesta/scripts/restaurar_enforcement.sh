#!/usr/bin/env bash
# Restaura el enforcement en APLICAR tras la campaña A (y antes de la B), al estado EXACTO previo.
#   [srv-dmz adminsrvdmz] -> lo ejecutas tú — o yo, cuando corresponda.
# Por defecto SIMULA; con --ejecutar aplica. Como modo_sombra NO editó la unidad, aquí solo se
# desenmascara y se reactiva el timer según el estado guardado (sin añadir ni duplicar argumentos).
set -uo pipefail
EJECUTAR=0; [ "${1:-}" = "--ejecutar" ] && EJECUTAR=1
BASE=/opt/cf-sombra-estado
TS=$(cat "$BASE/ultimo" 2>/dev/null || true)
EST="$BASE/$TS"
run(){ echo "+ $*"; [ $EJECUTAR -eq 1 ] && "$@"; }

echo "=== RESTAURAR ENFORCEMENT ($([ $EJECUTAR -eq 1 ] && echo EJECUTAR || echo SIMULACION)) desde $EST"
[ -z "$TS" ] && { echo "no hay estado guardado ($BASE/ultimo); nada que restaurar" >&2; [ $EJECUTAR -eq 1 ] && exit 1; }

echo "--- 1) desenmascarar el agente"
run sudo systemctl unmask ppi-enforce-agent.service
echo "--- 2) reactivar segun el estado original guardado"
en=$(cat "$EST/agent-timer.enabled" 2>/dev/null || echo enabled)
ac=$(cat "$EST/agent-timer.active" 2>/dev/null || echo active)
[ "$en" = "enabled" ] && run sudo systemctl enable ppi-enforce-agent.timer
[ "$ac" = "active" ] && run sudo systemctl start ppi-enforce-agent.timer

echo "--- 3) verificar restauración"
if [ $EJECUTAR -eq 1 ]; then
  m=$(systemctl is-masked ppi-enforce-agent.service 2>/dev/null || true)
  t=$(systemctl is-active ppi-enforce-agent.timer 2>/dev/null || true)
  echo "enmascarado=$m timer=$t"
  if [ "$m" = "masked" ] || { [ "$ac" = "active" ] && [ "$t" != "active" ]; }; then
    echo "FALLO: el agente no quedó restaurado como estaba. Revisar manualmente." >&2; exit 1
  fi
  echo "OK enforcement restaurado al estado previo. Comprobar: journalctl -u ppi-enforce-agent -n 20"
fi
echo "=== fin"
