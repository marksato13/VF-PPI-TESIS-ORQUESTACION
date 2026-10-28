#!/usr/bin/env bash
# PREFLIGHT 05c — clientes: UNA VUELTA benigna por perfil DESDE SU IP (argv completo de la unidad via systemctl show).
# Corrige p05b (que leyo solo la 1.a linea de ExecStart y salio desde la IP por omision 10.10.20.20).
# No arranca ni habilita cyberflow-lab.target; los procesos terminan solos.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p05c clientes  inicio=$(ts)  epoch=$(date +%s.%N)"
cd ~/laboratorio || exit 2
for p in ofimatica navegacion descargas aplicacion ligero erratico; do
  u=cyberflow-lab-$p.service
  argv=$(systemctl show "$u" -p ExecStart --value 2>/dev/null | sed -E 's/.*argv\[\]=([^;]*);.*/\1/')
  echo "## $u"; echo "  argv unidad: $argv"
  orig=$(echo "$argv" | grep -oE -- '--origen [0-9.]+' | awk '{print $2}')
  srv=$(echo "$argv" | grep -oE -- '--servidor [0-9.]+' | awk '{print $2}')
  dns=$(echo "$argv" | grep -oE -- '--dns [0-9.]+' | awk '{print $2}')
  [ -z "$orig" ] && { echo "  SIN --origen en la unidad: no se ejecuta"; continue; }
  t0=$(ts)
  timeout 120 python3 clientes_lab.py --perfil "$p" --origen "$orig" --servidor "${srv:-10.10.30.10}" --dns "${dns:-10.10.10.20}" --una-vuelta 2>&1 | sed 's/^/    /'
  echo "  rc=${PIPESTATUS[0]}  origen=$orig  ventana=[$t0, $(ts)]"
done
echo "## target sigue como estaba: $(systemctl is-active cyberflow-lab.target) / $(systemctl is-enabled cyberflow-lab.target)"
echo "## fin=$(ts)  epoch=$(date +%s.%N)"
