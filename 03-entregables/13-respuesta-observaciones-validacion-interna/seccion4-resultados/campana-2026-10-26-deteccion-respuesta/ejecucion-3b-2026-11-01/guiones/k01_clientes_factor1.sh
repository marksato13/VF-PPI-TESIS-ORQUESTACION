#!/usr/bin/env bash
# PASO3B k01 — clientes: procedimiento aprobado del paso 2. Para cyberflow-lab.target (curva horaria) y arranca los
# seis perfiles con factor 1,0 mediante el envoltorio clientes_factor1.py (69d79937...), con los MISMOS argumentos
# que sus unidades. No modifica clientes_lab.py. Deja los guiones de parada/restauracion en el directorio.
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID; W=$B/clientes_factor1.py; G=$HOME/laboratorio/clientes_lab.py
echo "## k01 $(date -u +%FT%T.%3NZ)"
[ "$(sha256sum $W | cut -c1-64)" = 69d79937f2fee84d8d63a38eb1171ed822858a54fa48d5a1e9266fb4e5a4c6c6 ] || { echo "PARAR: hash del envoltorio"; exit 2; }
[ -e "$B/pids" ] && { echo "PARAR: ya hay $B/pids"; exit 2; }
cat > $B/clientes_parar_factor1.sh <<'EOS'
#!/usr/bin/env bash
set -u
B=$(cd "$(dirname "$0")" && pwd)
echo "## parar factor1 $(date -u +%FT%T.%3NZ)"
while read u p; do kill -TERM -- -$p 2>/dev/null; echo "  $u pgid=$p TERM"; done < "$B/pids"
sleep 3
while read u p; do pgrep -g $p >/dev/null && { kill -KILL -- -$p; echo "  $u KILL"; }; done < "$B/pids"
echo "  quedan: $(pgrep -fc clientes_factor1.py)"; mv "$B/pids" "$B/pids.parado-$(date -u +%H%M%S)"
for f in $B/perfiles/*.out; do echo "  $(basename $f): $(tail -1 $f)"; done
EOS
cat > $B/clientes_restaurar.sh <<'EOS'
#!/usr/bin/env bash
set -u
B=$(cd "$(dirname "$0")" && pwd)
bash $B/clientes_parar_factor1.sh
echo "  generador sin cambios: $(sha256sum $HOME/laboratorio/clientes_lab.py | cut -c1-64)"
sudo -n systemctl start cyberflow-lab.target; echo "  [$(date -u +%FT%T.%3NZ)] start cyberflow-lab.target rc=$?"
sleep 15
echo "  target: $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for s in ofimatica navegacion descargas aplicacion ligero erratico; do echo "  cyberflow-lab-$s $(systemctl is-active cyberflow-lab-$s) NR=$(systemctl show -p NRestarts --value cyberflow-lab-$s)"; done
echo "  envoltorios vivos: $(pgrep -fc clientes_factor1.py)"
EOS
# argumentos de las unidades ANTES de pararlas
for u in ofimatica navegacion descargas aplicacion ligero erratico; do
  systemctl show -p ExecStart --value cyberflow-lab-$u.service | grep -oE 'argv\[\]=[^;]*' | head -1 | sed 's/^argv\[\]=//' > $B/argv-$u.txt
done
sudo -n systemctl stop cyberflow-lab.target; echo "  [$(date -u +%FT%T.%3NZ)] stop cyberflow-lab.target rc=$?"
sleep 3
echo "  target: $(systemctl is-active cyberflow-lab.target); unidades activas: $(for s in ofimatica navegacion descargas aplicacion ligero erratico; do systemctl is-active cyberflow-lab-$s; done | grep -c '^active')"
echo "  generador sha=$(sha256sum $G | cut -c1-64)"
mkdir -p "$B/perfiles"
for u in ofimatica navegacion descargas aplicacion ligero erratico; do
  A=$(cat $B/argv-$u.txt)
  ARGS=$(echo "$A" | sed 's#^/usr/bin/python3 /home/adminclientes/laboratorio/clientes_lab.py ##')
  echo "  $u: unidad -> $A"
  echo "$ARGS" | grep -q -- "--perfil $u " || { echo "PARAR: argumentos inesperados para $u"; exit 3; }
  setsid nohup bash -c 'W="$1"; LOG="$2"; shift 2; cd /home/adminclientes/laboratorio
    while :; do python3 -u "$W" "$@" >> "$LOG.out" 2>> "$LOG.err"; echo "$(date -u +%FT%T) salida rc=$?" >> "$LOG.err"; sleep 5; done' \
    _ "$W" "$B/perfiles/$u" $ARGS > /dev/null 2>&1 < /dev/null &
  echo "$u $!" >> "$B/pids"
done
sleep 8
while read u p; do echo "  $u pgid=$p vivo=$(kill -0 $p 2>/dev/null && echo si || echo NO) hijos=$(pgrep -g $p -c)"; done < "$B/pids"
echo "  errores: $(cat $B/perfiles/*.err 2>/dev/null | head -5)"
sleep 30; echo "## conexiones por origen (ss)"; ss -tn 2>/dev/null | awk 'NR>1{print $4}' | grep -oE '10\.10\.20\.2[0-9]' | sort | uniq -c | sed 's/^/  /'
for f in $B/perfiles/*.out; do echo "  $(basename $f): $(wc -l < $f) lineas; $(tail -1 $f | cut -c1-140)"; done
echo "## fin $(date -u +%FT%T.%3NZ)"
