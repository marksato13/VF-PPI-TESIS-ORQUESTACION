#!/usr/bin/env bash
# PASO2 s03 — clientes: estado de los seis perfiles y COMO se calcula su factor efectivo (horario, fin de semana).
# Solo lectura.
set -u
echo "## s03 clientes $(hostname) $(date -u +%FT%T.%3NZ) TZ=$(timedatectl show -p Timezone --value) local=$(date '+%a %H:%M')"
echo "  target: $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for u in $(systemctl list-dependencies --plain --no-pager cyberflow-lab.target | grep -o 'cyberflow-[a-z0-9@-]*\.service' | sort -u); do
  P=$(systemctl show -p MainPID --value $u)
  echo "  $u $(systemctl is-active $u) NR=$(systemctl show -p NRestarts --value $u) PID=$P desde=$(systemctl show -p ActiveEnterTimestamp --value $u)"
  [ "$P" != 0 ] && echo "      $(tr '\0' ' ' < /proc/$P/cmdline | cut -c1-240)"
  systemctl show -p Environment,EnvironmentFiles,FragmentPath,DropInPaths --value $u | sed 's/^/      /'
done
echo "## unidad de un perfil"
systemctl cat cyberflow-lab-ofimatica.service 2>&1 | sed 's/^/  | /'
echo "## generador: donde se calcula el factor"
P=$(systemctl show -p MainPID --value cyberflow-lab-ofimatica.service)
EXE=$(tr '\0' '\n' < /proc/$P/cmdline 2>/dev/null | grep -E '\.py$' | head -1); echo "  script: $EXE  sha=$(sha256sum "$EXE" 2>/dev/null | cut -c1-64)"
[ -n "$EXE" ] && grep -nE 'factor|hora|weekday|isoweekday|fin_de_semana|finde|horario|FACTOR|env|getenv|argparse|add_argument' "$EXE" | head -60 | sed 's/^/  /'
ls -la "$(dirname "$EXE")" 2>/dev/null | sed 's/^/  /'
echo "## journal reciente (ultimas lineas por perfil)"
for s in ofimatica navegacion descargas aplicacion ligero erratico; do journalctl -u cyberflow-lab-$s --no-pager -q -n 2 -o short-iso 2>/dev/null | cut -c1-220 | sed "s/^/  [$s] /"; done
echo "  sudo -n -l:"; sudo -n -l 2>&1 | sed 's/^/    /' | head -20
echo "  alias: $(ip -br addr | grep -oE '10\.10\.20\.[0-9]+' | tr '\n' ' ')"
echo "## fin $(date -u +%FT%T.%3NZ)"
