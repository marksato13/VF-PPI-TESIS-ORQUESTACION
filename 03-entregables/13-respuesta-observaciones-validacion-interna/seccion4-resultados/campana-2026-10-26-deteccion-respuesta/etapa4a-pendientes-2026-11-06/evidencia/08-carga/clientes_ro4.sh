set -u
# [CLIENTES adminclientes] SOLO LECTURAS: arranque del host, historial de los generadores y función factor_horario.
echo "arranque del host: $(uptime -s) (UTC)"; last -x reboot shutdown 2>/dev/null | head -8
echo "== journal de cyberflow-lab desde el 03-nov (arranques/paradas)"
journalctl --no-pager -o short-iso -u cyberflow-lab.target -u 'cyberflow-lab-*' --since 2026-11-03 2>/dev/null \
  | grep -E 'Started|Stopped|Stopping|Starting|Deactivated' | tail -30
echo "== factor_horario"
sed -n '84,125p' ~/laboratorio/clientes_lab.py
echo "== erratico"; sed -n '61,82p' ~/laboratorio/clientes_lab.py; sed -n '325,360p' ~/laboratorio/clientes_lab.py
