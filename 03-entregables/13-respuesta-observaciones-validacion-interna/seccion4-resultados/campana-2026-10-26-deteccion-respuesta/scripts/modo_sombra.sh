#!/usr/bin/env bash
# Pone el enforcement en SOMBRA para la campaña A, de forma verificable y con fallo seguro.
#   [srv-dmz adminsrvdmz] -> lo ejecutas tú (NOPASSWD ALL disponible) — o yo, cuando se autorice A.
# Por defecto SIMULA (imprime el plan). Con --ejecutar aplica. NO edita la unidad del agente (así la
# restauración no puede duplicar argumentos): detiene y enmascara el timer del agente.
#
# Qué hace: guarda el estado original, DETIENE el agente (lo que aplica medidas), vacía los sets por si
# hubiera restricciones residuales, y verifica. No toca el publicador: detenerlo NO invalida un feed ya
# publicado (el agente podría seguir consumiéndolo), por eso lo que se detiene es el AGENTE.
set -uo pipefail
EJECUTAR=0; [ "${1:-}" = "--ejecutar" ] && EJECUTAR=1
TS=$(date -u +%Y%m%d-%H%M%S)
EST=/opt/cf-sombra-estado/$TS
run(){ echo "+ $*"; [ $EJECUTAR -eq 1 ] && "$@"; }

echo "=== MODO SOMBRA ($([ $EJECUTAR -eq 1 ] && echo EJECUTAR || echo SIMULACION)) estado->$EST"
run sudo mkdir -p "$EST"
echo "--- 1) guardar estado original"
run bash -c "systemctl is-active ppi-enforce-agent.timer > '$EST/agent-timer.active' 2>&1 || true"
run bash -c "systemctl is-enabled ppi-enforce-agent.timer > '$EST/agent-timer.enabled' 2>&1 || true"
run bash -c "sudo cp /etc/systemd/system/ppi-enforce-agent.service '$EST/' 2>/dev/null || true"
run bash -c "sudo nft list table inet cyberflow > '$EST/nft-antes.txt' 2>&1 || true"

echo "--- 2) detener el agente (impide aplicar) y enmascararlo para que no lo reactive un timer"
run sudo systemctl stop ppi-enforce-agent.timer ppi-enforce-agent.service
run sudo systemctl mask ppi-enforce-agent.service

echo "--- 3) vaciar restricciones residuales (sets a cero)"
run sudo nft flush set inet cyberflow cyberflow_bloqueados
run sudo nft flush set inet cyberflow cyberflow_limitados

echo "--- 4) verificar SOMBRA (fallo seguro)"
if [ $EJECUTAR -eq 1 ]; then
  act=$(systemctl is-active ppi-enforce-agent.service 2>/dev/null || true)
  b=$(sudo nft list set inet cyberflow cyberflow_bloqueados 2>/dev/null | grep -c 'elements')
  l=$(sudo nft list set inet cyberflow cyberflow_limitados 2>/dev/null | grep -c 'elements')
  echo "agente=$act bloqueados_con_elements=$b limitados_con_elements=$l"
  if [ "$act" = "active" ] || [ "$b" != "0" ] || [ "$l" != "0" ]; then
    echo "FALLO SEGURO: el agente sigue activo o quedan restricciones. NO iniciar la campaña A." >&2; exit 1
  fi
  echo "OK sombra verificada."
  echo "RECORDATORIO [SENSOR m4rk]: comprobar que ppi-motor NO corre con --enforce:"
  echo "   systemctl cat ppi-motor | grep -- --enforce   # no debe aparecer"
  echo "$TS" | sudo tee "$EST/../ultimo" >/dev/null
fi
echo "=== fin. Restaurar con: restaurar_enforcement.sh --ejecutar"
