#!/usr/bin/env bash
# PASO2 s04 — Kali: herramientas, scripts de la campana y ausencia de carga en curso. Solo lectura.
set -u
echo "## s04 kali $(hostname) $(date -u +%FT%T.%3NZ) ip=$(ip -br addr | grep -oE '10\.10\.20\.[0-9]+' | tr '\n' ' ')"
echo "  curl: $(curl --version | head -1)"; echo "  python: $(python3 -V 2>&1)"
echo "  procesos de carga: $(ps -eo args | grep -cE '^[c]url |[n]map |[d]ig |generar_campana')"
ls -la ~ | sed 's/^/  /'
for d in ~/cf-campana*; do echo "  -- $d"; ls -la "$d" | head -20 | sed 's/^/     /'; done
sha256sum ~/cf-campana*/generar_campana.py ~/cf-campana*/esquema_campana.py ~/cf-campana*/escenarios.json ~/cf-campana*/*/escenarios.json 2>/dev/null | sed 's/^/  /'
echo "  http directo: $(curl -s -o /dev/null -m 5 -w '%{http_code} %{time_total}s' http://10.10.30.10/)"
echo "## fin $(date -u +%FT%T.%3NZ)"
