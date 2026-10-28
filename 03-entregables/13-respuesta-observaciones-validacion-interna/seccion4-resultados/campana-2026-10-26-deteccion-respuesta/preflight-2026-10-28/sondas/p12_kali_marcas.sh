#!/usr/bin/env bash
# PREFLIGHT 12 — Kali: transacciones benignas IDENTIFICABLES durante la prueba del archivador (para comprobar su
# visibilidad en PCAP/EVE/log del endpoint/motor). 2 DNS lab-ppi, 1 GET :80, 3 GET /auth. Y dependencias extra.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
UA="cf-preflight-2026-10-28"
echo "## p12 kali  inicio=$(ts)  epoch=$(date +%s.%N)"
for i in 1 2; do N="pfmarca$i-$(date +%s).lab-ppi"; t=$(ts); echo "  [$t] dig $N -> $(dig +time=3 +tries=1 @10.10.10.20 "$N" A +short)"; done
t=$(ts); echo "  [$t] GET :80/ -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code}' http://10.10.30.10/)"
t=$(ts); echo "  [$t] GET :18081/auth sin credencial -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code}' http://10.10.30.10:18081/auth)"
t=$(ts); echo "  [$t] GET :18081/auth fake -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -u fake:preflight-incorrecta -w '%{http_code}' http://10.10.30.10:18081/auth)"
t=$(ts); echo "  [$t] GET :18081/auth control -> $(curl -s -o /dev/null -A "$UA" --max-time 5 -u control:control123 -w '%{http_code}' http://10.10.30.10:18081/auth)"
echo "## dependencias extra del generador"
for t in openssl seq mktemp bash; do printf '  %-8s %s\n' "$t" "$(command -v $t || echo NO)"; done
echo "  openssl rand -hex 8 -> $(openssl rand -hex 8 2>&1)"
echo "## persistencia de sesion en la Kali"; for t in tmux screen nohup setsid systemd-run; do printf '  %-12s %s\n' "$t" "$(command -v $t || echo NO)"; done
echo "  linger: $(loginctl show-user "$(id -un)" -p Linger --value 2>/dev/null)"
echo "  espacio en ~: $(df -hP ~ | awk 'NR==2{print $4" libres ("$5")"}')"
echo "## fin=$(ts)  epoch=$(date +%s.%N)"
