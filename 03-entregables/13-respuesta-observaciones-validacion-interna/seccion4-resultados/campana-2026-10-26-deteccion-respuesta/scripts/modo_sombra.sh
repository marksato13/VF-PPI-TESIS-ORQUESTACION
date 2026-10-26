#!/usr/bin/env bash
# Pone el enforcement en SOMBRA para la campaña A (el motor decide y registra; no se aplica nada).
# Dos opciones; elegir una y documentarla. Verifica que no queden elements.
#   opción 1 [srv-dmz adminsrvdmz] -> lo ejecutas tú (sudo con contraseña): agente en dry-run
#   opción 2 [SENSOR m4rk]        -> lo ejecuto yo: parar el publicador
set -uo pipefail
echo "== estado actual de los sets (srv-dmz) =="
echo "   sudo nft list set inet cyberflow cyberflow_bloqueados"
echo "   sudo nft list set inet cyberflow cyberflow_limitados"
echo
echo "OPCIÓN 1 (preferida, srv-dmz): editar ppi-enforce-agent.service quitando '--aplicar' y reiniciar:"
echo "   sudo sed -i 's/ --aplicar//' /etc/systemd/system/ppi-enforce-agent.service"
echo "   sudo systemctl daemon-reload && sudo systemctl restart ppi-enforce-agent.timer"
echo
echo "OPCIÓN 2 (sensor): detener el publicador mientras dure A:"
echo "   systemctl stop ppi-publicar-feed.timer"
echo
echo "Verificar que ambos sets quedan SIN elements antes de generar tráfico. Registrar la hora del cambio."
echo "ESTE SCRIPT NO APLICA NADA: imprime el procedimiento para ejecutarlo con revisión."
