#!/bin/bash
# SOLO LECTURA. No reinicia, no escribe fuera de /tmp, no imprime secretos.
set -u
red() { sed -E 's/((pass|token|secret|clave_privada|private|apikey|api_key)[^=]*=).*/\1<omitido>/I'; }
echo "### host"; hostname; date -Is; uptime
echo "### unidades ppi-* (todas)"
systemctl list-units --all --no-legend 'ppi-*' | awk '{print $1, $2, $3, $4}'
systemctl list-unit-files --no-legend 'ppi-*' | awk '{print $1, $2}'
echo "### timers"
systemctl list-timers --all --no-legend 'ppi-*' | awk '{print $(NF-1), $NF}'
for u in $(systemctl list-unit-files --no-legend 'ppi-*' | awk '{print $1}'); do
  echo "#### systemctl cat $u"
  systemctl cat "$u" 2>/dev/null | grep -Ev '^\s*$' | red
done
echo "### ~/cyberflow"
cd ~/cyberflow || exit 0
ls -la
echo "### git en ~/cyberflow"
git rev-parse HEAD 2>&1 | head -1; git status --short 2>/dev/null | head -20
echo "### arbol (niveles 1-2, sin logs ni datos voluminosos)"
find . -maxdepth 2 -not -path './.venv*' -not -path './logs/*' -not -path './data/*' -not -path './.git/*' | sort | head -150
