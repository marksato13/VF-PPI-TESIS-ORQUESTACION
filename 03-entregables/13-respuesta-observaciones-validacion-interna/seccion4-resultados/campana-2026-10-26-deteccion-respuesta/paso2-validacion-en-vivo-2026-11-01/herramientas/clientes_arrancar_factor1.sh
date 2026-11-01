#!/usr/bin/env bash
# PASO2 — clientes: arranca los seis perfiles con factor 1,0 (envoltorio clientes_factor1.py) como procesos del
# usuario, con los MISMOS argumentos que sus unidades. Aborta si cyberflow-lab.target esta activo (evita perfiles
# duplicados). Reinicio automatico a los 5 s como Restart=always/RestartSec=5 de las unidades.
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; W=$B/clientes_factor1.py; G=$HOME/laboratorio/clientes_lab.py
echo "## arrancar factor1 $(date -u +%FT%T.%3NZ)"
[ "$(systemctl is-active cyberflow-lab.target)" = inactive ] || { echo "ABORTO: cyberflow-lab.target no esta inactivo"; exit 2; }
[ -e "$B/pids" ] && { echo "ABORTO: ya hay $B/pids"; exit 2; }
echo "  generador sha=$(sha256sum $G | cut -c1-64) (esperado ae5134a7...)"; echo "  envoltorio sha=$(sha256sum $W | cut -c1-64)"
mkdir -p "$B/perfiles"
for u in ofimatica navegacion descargas aplicacion ligero erratico; do
  A=$(systemctl show -p ExecStart --value cyberflow-lab-$u.service | grep -oE 'argv\[\]=[^;]*' | head -1 | sed 's/^argv\[\]=//')
  ARGS=$(echo "$A" | sed 's#^/usr/bin/python3 /home/adminclientes/laboratorio/clientes_lab.py ##')
  echo "  $u: unidad -> $A"
  echo "$ARGS" | grep -q -- "--perfil $u " || { echo "ABORTO: argumentos inesperados para $u"; exit 3; }
  setsid nohup bash -c 'W="$1"; LOG="$2"; shift 2; cd /home/adminclientes/laboratorio
    while :; do python3 -u "$W" "$@" >> "$LOG.out" 2>> "$LOG.err"; echo "$(date -u +%FT%T) salida rc=$?" >> "$LOG.err"; sleep 5; done' \
    _ "$W" "$B/perfiles/$u" $ARGS > /dev/null 2>&1 < /dev/null &
  echo "$u $!" >> "$B/pids"
done
sleep 8
while read u p; do echo "  $u pgid=$p vivo=$(kill -0 $p 2>/dev/null && echo si || echo NO) hijos=$(pgrep -g $p -c)"; done < "$B/pids"
echo "  errores: $(cat $B/perfiles/*.err 2>/dev/null | grep -v '^PASO2' | head -5)"; head -1 $B/perfiles/ofimatica.err
sleep 20; echo "## conexiones por origen (ss)"; ss -tn 2>/dev/null | awk 'NR>1{print $4}' | grep -oE '10\.10\.20\.2[0-9]' | sort | uniq -c | sed 's/^/  /'
echo "## fin $(date -u +%FT%T.%3NZ)"
