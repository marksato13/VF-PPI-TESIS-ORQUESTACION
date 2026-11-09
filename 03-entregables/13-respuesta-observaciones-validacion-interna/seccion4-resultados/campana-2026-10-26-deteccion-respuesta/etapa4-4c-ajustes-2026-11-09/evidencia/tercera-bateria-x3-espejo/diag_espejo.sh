echo "## $(date -u +%FT%TZ)"
S="ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i $HOME/.ssh/cyberflow-to-sensor m4rk@10.10.60.11"
echo "== Sensor1 ens37"
$S 'ip -s link show ens37 | head -8; echo "carrier=$(cat /sys/class/net/ens37/carrier) operstate=$(cat /sys/class/net/ens37/operstate)"; echo "-- rx_packets cada 2 s:"; for i in 1 2 3; do cat /sys/class/net/ens37/statistics/rx_packets; sleep 2; done; echo "-- kernel (journalctl -k) desde 15:20:"; journalctl -k --no-pager --since "15:20:00" 2>&1 | tail -8 | cut -c1-200; echo "-- cyberflow-capture-nic:"; systemctl is-active cyberflow-capture-nic; journalctl --no-pager -u cyberflow-capture-nic --since "15:00:00" 2>&1 | tail -4 | cut -c1-200'
echo "== Clientes: perfiles y conexiones"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i $HOME/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'echo "$(ps -eo args | grep -c "[c]lientes_factor1.py") procesos de perfil; conexiones a 10.10.30.10: $(ss -tn 2>/dev/null | grep -c 10.10.30.10)"; tail -n 1 ~/cf-e4/4c/*.out 2>/dev/null | tail -4 | cut -c1-160' 2>&1 | head -8
echo "== Kali: dig en curso"
ssh -n -o BatchMode=yes -o ConnectTimeout=8 -i $HOME/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'echo "dig activos: $(pgrep -fc "[d]ig +time")"; ip -s link show eth0 | sed -n 3,5p' 2>&1 | head -5
echo "== alcance desde el bastión"
for h in 10.10.20.30 10.10.20.20 10.10.30.10 10.10.10.20 10.10.60.11; do printf "%s " $h; ping -c1 -W2 $h >/dev/null 2>&1 && echo ok || echo SIN_RESPUESTA; done
