#!/usr/bin/env bash
# PASO3B c04 — clientes (solo lectura + directorio nuevo): estado de los seis perfiles y del mecanismo factor 1,0.
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID
[ -e "$B" ] && { echo "PARAR: ya existe $B"; exit 2; }
mkdir -p "$B"
echo "## c04 $(hostname) $(date -u +%FT%T.%3NZ) -> $B"
echo "  target: $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target 2>&1)"
for s in ofimatica navegacion descargas aplicacion ligero erratico; do
  echo "  cyberflow-lab-$s $(systemctl show -p ActiveState,MainPID,NRestarts,ActiveEnterTimestamp cyberflow-lab-$s | tr '\n' ' ')"
done | tee "$B/servicios-inicio.txt"
sha256sum ~/laboratorio/clientes_lab.py ~/cf-paso2-20261101T0254Z/clientes_factor1.py | sed 's/^/  /'
cp -p ~/cf-paso2-20261101T0254Z/clientes_factor1.py "$B/clientes_factor1.py" && echo "  envoltorio copiado: $(sha256sum $B/clientes_factor1.py | cut -c1-64) (esperado 69d79937...)"
echo "  envoltorios vivos: $(pgrep -fc 'clientes_factor1.py')  sudo -n systemctl permitido: $(sudo -n -l 2>/dev/null | grep -c 'cyberflow-lab')"
echo "  ip: $(ip -4 -o addr | awk '{print $2, $4}' | tr '\n' ' ')"
echo "## fin $(date -u +%FT%T.%3NZ)"
