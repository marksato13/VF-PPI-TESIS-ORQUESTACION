#!/usr/bin/env bash
# Guarda el desfase de reloj de un host (correr en cada uno: sensor, bastión, Kali, srv-dmz),
# antes y después de la campaña. Solo lectura.
#   [<host> <cuenta>] -> lo ejecuto yo donde haya llave; donde no, lo ejecutas tú
set -uo pipefail
echo "host: $(hostname)  utc: $(date -u +%Y-%m-%dT%H:%M:%S.%N%z)  monotonico: $(cat /proc/uptime | cut -d' ' -f1)"
if command -v chronyc >/dev/null 2>&1; then
  chronyc tracking 2>/dev/null | grep -Ei 'Reference ID|System time|Last offset|RMS offset'
else
  echo "chrony: NO disponible (reloj sin disciplina NTP) -> hay que corregir antes de la campaña"
fi
