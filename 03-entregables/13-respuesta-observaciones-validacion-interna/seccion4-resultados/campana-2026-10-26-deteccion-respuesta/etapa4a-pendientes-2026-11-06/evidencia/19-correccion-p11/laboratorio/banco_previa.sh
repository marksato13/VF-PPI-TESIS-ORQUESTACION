#!/usr/bin/env bash
# [LAPTOP Docker, sin red] Banco de previa_host.sh antes de usarlo en el laboratorio. Procesos reales del contenedor.
set -u
G=/l/previa_host.sh; f=0
ok() { echo "PASA  $1"; }; mal() { echo "FALLA $1"; f=$((f+1)); }
chk() {  # chk NOMBRE N RC_ESPERADO PATRON
  local o r; o=$(N=$2 bash -s < "$G" 2>&1); r=$?
  if [ "$r" = "$3" ] && grep -qE "$4" <<<"$o"; then ok "$1 (rc $r)"; else mal "$1 (rc $r)"; printf '%s\n' "$o" | tail -8; fi
}
chk "sensor1 sin procesos: cribado y argv sin nada" sensor1 0 '^ARGV ausencia confirmada'
chk "clientes sin procesos" clientes 0 '^CRIBADO ninguno'
mkdir -p /tmp/d; printf 'import time\ntime.sleep(60)\n' > /tmp/d/muestreo_fino.py; printf 'import time\ntime.sleep(60)\n' > /tmp/d/clientes_lab.py
bash -c 'sleep 60; : muestreo_fino.py' & A=$!
sleep 0.3
chk "texto incrustado: el cribado conservador lo señala (detiene, no aprueba); argv: ausencia" sensor1 1 'ARGV ausencia confirmada'
kill $A; wait $A 2>/dev/null
python3 -I /tmp/d/muestreo_fino.py & M=$!; sleep 0.3
chk "muestreador real: cribado y argv lo detectan" sensor1 1 '^ARGV MUESTREADOR pid='"$M"' muestreo_fino.py'
kill $M; wait $M 2>/dev/null
python3 -I /tmp/d/clientes_lab.py & C=$!; sleep 0.3
chk "generador real en clientes: lo detecta" clientes 1 "^CRIBADO_PRESENTE +$C "
kill $C; wait $C 2>/dev/null
echo "RESULTADO_BANCO fallos=$f"; exit $((f > 0))
