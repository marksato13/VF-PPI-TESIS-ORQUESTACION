#!/usr/bin/env bash
# PREFLIGHT 09 — bastion: rele del feed, procesos persistentes del usuario, tmux/screen, linger. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p09 bastion  inicio=$(ts)"
systemctl list-units --all --no-pager --plain --no-legend 2>/dev/null | grep -Ei 'ppi|cyberflow|relay|tailscale' | awk '{printf "  %-36s %-9s %-9s %s\n",$1,$2,$3,$4}'
systemctl list-timers --all --no-pager --no-legend 2>/dev/null | grep -Ei 'ppi|relay' | sed 's/^/  /'
echo "  ExecStart rele: $(systemctl show ppi-relay-feed.service -p ExecStart --value 2>/dev/null | sed -E 's/.*argv\[\]=([^;]*);.*/\1/')"
echo "## herramientas de persistencia de sesion"; for t in tmux screen nohup setsid systemd-run; do printf '  %-12s %s\n' "$t" "$(command -v $t || echo NO)"; done
echo "  linger gadmin: $(loginctl show-user gadmin -p Linger --value 2>/dev/null)"
echo "## conectividad a Internet (solo para documentar dependencias; 1 consulta DNS + 1 HEAD)"
echo "  dig ntp: $(dig +time=3 +tries=1 +short pool.ntp.org A 2>&1 | head -1)"
echo "  https: $(curl -s -o /dev/null -I --max-time 5 -w '%{http_code}' https://github.com 2>&1)"
echo "## fin=$(ts)"
