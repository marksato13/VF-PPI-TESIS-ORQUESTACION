#!/usr/bin/env bash
# PREFLIGHT 05b — clientes: argumentos de las 6 unidades y UNA VUELTA benigna por perfil (una accion de cada tipo).
# No arranca ni habilita cyberflow-lab.target; los procesos terminan solos.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p05b clientes  inicio=$(ts)  epoch=$(date +%s.%N)"
cd ~/laboratorio || exit 2
for p in ofimatica navegacion descargas aplicacion ligero erratico; do
  u=cyberflow-lab-$p.service
  ex=$(systemctl cat "$u" 2>/dev/null | grep -E '^ExecStart=' | sed 's/^ExecStart=//')
  echo "## $u"; echo "  ExecStart: $ex"
  args=$(echo "$ex" | sed -E 's#^.*clientes_lab\.py##')
  orig=$(echo "$args" | grep -oE -- '--origen [0-9.]+' | awk '{print $2}')
  srv=$(echo "$args" | grep -oE -- '--servidor [0-9.]+' | awk '{print $2}'); srv=${srv:-10.10.30.10}
  dns=$(echo "$args" | grep -oE -- '--dns [0-9.]+' | awk '{print $2}'); dns=${dns:-10.10.10.20}
  t0=$(ts)
  timeout 120 python3 clientes_lab.py --perfil "$p" --origen "$orig" --servidor "$srv" --dns "$dns" --una-vuelta 2>&1 | sed 's/^/    /'
  echo "  rc=${PIPESTATUS[0]}  ventana=[$t0, $(ts)]"
done
echo "## target sigue como estaba: $(systemctl is-active cyberflow-lab.target) / $(systemctl is-enabled cyberflow-lab.target)"
echo "## fin=$(ts)  epoch=$(date +%s.%N)"
