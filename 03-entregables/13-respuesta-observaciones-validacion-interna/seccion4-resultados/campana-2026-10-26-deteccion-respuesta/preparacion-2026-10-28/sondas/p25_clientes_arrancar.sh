#!/usr/bin/env bash
# PREP 25 — clientes: arranca cyberflow-lab.target (NOPASSWD de adminclientes) SIN tocar unidades ni parametros, y
# verifica cada uno de los seis servicios: activo, PID, IP de origen, argumentos, reinicios. No habilita al arranque.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p25  inicio=$(ts)"
S="cyberflow-lab-ofimatica cyberflow-lab-navegacion cyberflow-lab-descargas cyberflow-lab-aplicacion cyberflow-lab-ligero cyberflow-lab-erratico"
echo "  antes: target=$(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for s in $S; do systemctl cat $s.service 2>/dev/null | sha256sum | cut -c1-16 | sed "s/^/  unidad $s sha16=/"; done
sudo -n systemctl start cyberflow-lab.target; echo "  [$(ts)] start rc=$?"
sleep 20
echo "  despues: target=$(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for s in $S; do
  echo "  -- $s: $(systemctl show $s.service -p ActiveState,SubState,MainPID,NRestarts,ActiveEnterTimestamp | tr '\n' ' ')"
  echo "     ExecStart: $(systemctl show -p ExecStart --value $s.service | grep -oE 'argv\[\]=[^;]*' | head -1)"
done
echo "## conexiones por IP de origen (ss)"; ss -tnp 2>/dev/null | awk 'NR>1{print $4}' | grep -oE '10\.10\.20\.2[0-9]' | sort | uniq -c | sed 's/^/  /'
echo "## journal de los perfiles desde el arranque (errores)"; journalctl -u 'cyberflow-lab-*' --since '-1 min' --no-pager 2>/dev/null | grep -iE 'error|traceback|fail' | head -10 | sed 's/^/  /'
echo "  (lineas de error: $(journalctl -u 'cyberflow-lab-*' --since '-1 min' --no-pager 2>/dev/null | grep -ciE 'error|traceback|fail'))"
echo "## fin=$(ts)"
