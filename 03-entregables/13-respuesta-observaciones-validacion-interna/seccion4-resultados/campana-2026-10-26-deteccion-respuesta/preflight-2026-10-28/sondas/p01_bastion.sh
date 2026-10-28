#!/usr/bin/env bash
# PREFLIGHT 01 — bastion: identidad, reloj, llaves, conectividad L3/L4 hacia las maquinas de la campana. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p01 bastion  inicio=$(ts)  host=$(hostname)  user=$(id -un)  kernel=$(uname -r)"
echo "## chrony"; chronyc tracking 2>&1 | grep -E 'Reference|System time|Last offset|RMS|Leap'
echo "## llaves ssh (nombres, sin contenido)"; ls -1 ~/.ssh/ 2>&1 | grep -v -E '\.pub$|known_hosts|authorized'
echo "## ~/.ssh/config (Host/HostName/User/IdentityFile)"; grep -E '^\s*(Host|HostName|User|IdentityFile)\b' ~/.ssh/config 2>/dev/null || echo "(sin config)"
echo "## herramientas"; for t in ping nc nmap dig curl tcpdump; do printf '%s=%s ' "$t" "$(command -v $t || echo NO)"; done; echo
echo "## vecinos ARP antes"; ip neigh 2>/dev/null | grep -E '10\.10\.(10|20|30|60)\.' | sort
for ip in 10.10.60.11 10.10.20.30 10.10.30.10 10.10.10.20 10.10.20.21 10.10.20.22 10.10.20.23 10.10.20.24 10.10.20.25 10.10.20.26; do
  t=$(ts); p=$(ping -c2 -W1 -q "$ip" 2>&1 | grep -E 'received' | sed 's/,.*time.*//')
  ports=""
  for pt in 22 53 80 443 18081; do
    if timeout 2 bash -c "exec 3<>/dev/tcp/$ip/$pt" 2>/dev/null; then ports="$ports $pt:abierto"
    else rc=$?; ports="$ports $pt:$([ $rc -eq 124 ] && echo timeout || echo rechazado)"; fi
  done
  echo "[$t] $ip ping={$p} tcp={$ports }"
done
echo "## vecinos ARP despues (REACHABLE/STALE = hay host en L2; FAILED/INCOMPLETE = no responde a ARP)"; ip neigh 2>/dev/null | grep -E '10\.10\.(10|20|30|60)\.' | sort
echo "## fin=$(ts)"
