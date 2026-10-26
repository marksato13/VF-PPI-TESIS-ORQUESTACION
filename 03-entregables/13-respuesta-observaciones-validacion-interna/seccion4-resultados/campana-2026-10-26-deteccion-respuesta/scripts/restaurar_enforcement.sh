#!/usr/bin/env bash
# Restaura el enforcement en modo APLICAR tras la campaña A (y antes de la campaña B).
#   opción 1 [srv-dmz adminsrvdmz] -> lo ejecutas tú (sudo con contraseña)
#   opción 2 [SENSOR m4rk]        -> lo ejecuto yo
set -uo pipefail
echo "OPCIÓN 1 (srv-dmz): devolver '--aplicar' al agente:"
echo "   sudo sed -i 's#agente_enforce.py#agente_enforce.py --aplicar#' /etc/systemd/system/ppi-enforce-agent.service  # si se había quitado"
echo "   (o restaurar el fichero desde su copia) ; sudo systemctl daemon-reload && sudo systemctl restart ppi-enforce-agent.timer"
echo
echo "OPCIÓN 2 (sensor): reactivar el publicador:"
echo "   systemctl start ppi-publicar-feed.timer"
echo
echo "Comprobar que vuelve a aplicar (journalctl -u ppi-enforce-agent) y registrar la hora."
echo "ESTE SCRIPT NO APLICA NADA: imprime el procedimiento."
