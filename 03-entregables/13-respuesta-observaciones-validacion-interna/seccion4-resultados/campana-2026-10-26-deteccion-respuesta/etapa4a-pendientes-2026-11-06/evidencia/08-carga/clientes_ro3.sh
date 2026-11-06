set -u
# [CLIENTES adminclientes] SOLO LECTURAS: estado de los generadores ahora, curva diaria y envoltorio factor1.
echo "target: $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for s in ofimatica navegacion descargas aplicacion ligero erratico; do
  echo "cyberflow-lab-$s $(systemctl show -p ActiveState -p MainPID -p NRestarts -p ActiveEnterTimestamp cyberflow-lab-$s | tr '\n' ' ')"; done
echo "sha256 clientes_lab.py: $(sha256sum ~/laboratorio/clientes_lab.py | cut -c1-64)  timedatectl: $(timedatectl show -p Timezone --value)"
echo "== curva y perfiles restantes"
grep -nE 'def curva|hora|HORA|ritmo|factor|"(aplicacion|ligero|erratico)"' ~/laboratorio/clientes_lab.py | head -40
sed -n '/def curva/,/^def /p' ~/laboratorio/clientes_lab.py | head -40
echo "== clientes_factor1.py (cabecera)"; head -30 ~/cf-3b-20261101T0721Z/clientes_factor1.py
