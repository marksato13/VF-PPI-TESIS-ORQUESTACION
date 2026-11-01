#!/usr/bin/env bash
# PASO3A s02 — srv-dmz: estado de sombra y del endpoint de fuerza bruta (solo lectura). No imprime credenciales.
set -u
echo "## s02 $(hostname) $(date -u +%FT%T.%3NZ)"
for u in ppi-enforce-agent.timer ppi-enforce-agent.service ppi-brute-lab.service lab-web-http.service lab-web-https.service; do
  echo "  $u active=$(systemctl is-active $u 2>&1) enabled=$(systemctl is-enabled $u 2>&1)"
done
echo "  tablas nft: $(sudo -n nft list tables 2>&1 | tr '\n' ' ')"
for s in cyberflow_bloqueados cyberflow_limitados; do sudo -n nft list set inet cyberflow $s >/dev/null 2>&1 && echo "  $s existe" || echo "  $s: la tabla/conjunto no existe (rc=$?)"; done
echo "## endpoint brute-lab"
ls -la /opt/brute-lab/ 2>&1 | sed 's/^/  /'
ls -la /etc/systemd/system/ppi-brute-lab.service 2>&1 | sed 's/^/  /'
[ -f /opt/brute-lab/app.py ] && echo "  app.py sha256 $(sha256sum /opt/brute-lab/app.py | cut -c1-64)"
[ -f /etc/systemd/system/ppi-brute-lab.service ] && { echo "  unidad sha256 $(sha256sum /etc/systemd/system/ppi-brute-lab.service | cut -c1-64)"; grep -vE 'CLAVE|USUARIO' /etc/systemd/system/ppi-brute-lab.service | sed 's/^/   | /'; }
[ -f /opt/brute-lab/brute.log ] && { echo "  brute.log: $(wc -l < /opt/brute-lab/brute.log) lineas; ultima: $(tail -n1 /opt/brute-lab/brute.log)"; }
echo "  escucha: $(ss -ltnH | awk '{print $4}' | tr '\n' ' ')"
echo "  python3: $(command -v python3) $(python3 -V 2>&1)"
sudo -n journalctl --no-pager -u ppi-brute-lab -n 5 2>&1 | sed 's/^/  j| /'
echo "  cortafuegos local: ufw=$(sudo -n ufw status 2>&1 | head -1)"
echo "## fin"
