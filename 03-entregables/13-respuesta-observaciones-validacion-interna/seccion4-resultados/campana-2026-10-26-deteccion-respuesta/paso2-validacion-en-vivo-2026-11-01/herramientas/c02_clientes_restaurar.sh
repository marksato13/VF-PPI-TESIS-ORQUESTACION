#!/usr/bin/env bash
# PASO2 c02 — clientes: para los perfiles a factor 1,0 y restaura la programacion habitual (cyberflow-lab.target,
# curva horaria original de clientes_lab.py). El target sigue sin habilitarse al arranque, como estaba.
set -u
B=$HOME/cf-paso2-20261101T0254Z
bash $B/clientes_parar_factor1.sh
echo "  generador sin cambios: $(sha256sum $HOME/laboratorio/clientes_lab.py | cut -c1-64)"
sudo -n systemctl start cyberflow-lab.target; echo "  [$(date -u +%FT%T.%3NZ)] start cyberflow-lab.target rc=$?"
sleep 15
echo "  target: $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for s in ofimatica navegacion descargas aplicacion ligero erratico; do echo "  cyberflow-lab-$s $(systemctl is-active cyberflow-lab-$s) NR=$(systemctl show -p NRestarts --value cyberflow-lab-$s)"; done
echo "  envoltorios vivos: $(pgrep -fc clientes_factor1.py)"
