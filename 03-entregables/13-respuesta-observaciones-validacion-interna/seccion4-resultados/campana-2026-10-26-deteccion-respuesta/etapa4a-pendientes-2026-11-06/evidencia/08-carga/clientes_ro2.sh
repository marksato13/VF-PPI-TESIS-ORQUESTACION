set -u
# [CLIENTES adminclientes] SOLO LECTURAS: perfiles legítimos disponibles (argumentos, servicios) — no arranca nada.
D=~/cf-3b-20261101T0721Z
for f in $D/argv-*.txt; do echo "== $f"; cat "$f" | tr '\0' ' ' | cut -c1-400; echo; done
echo "== servicios-inicio"; head -30 $D/servicios-inicio.txt
echo "== servicios-fin"; head -30 $D/servicios-fin.txt
echo "== restaurar.sh"; head -40 $D/clientes_restaurar.sh
echo "== laboratorio/clientes_lab.py (cabecera)"; head -60 ~/laboratorio/clientes_lab.py
echo "== IPs"; ip -4 -o addr | awk '{print $2, $4}'
echo "== servicios del sistema con clientes"; systemctl list-unit-files --no-pager 2>/dev/null | grep -iE 'client|lab' | head
