set -u
# [SENSOR1 m4rk] Solo lecturas, sin sudo. Estado efectivo tras el reinicio del 5-nov ~23:57 UTC.
echo "fecha=$(date -u +%FT%TZ) arranque=$(uptime -s) ntp=$(timedatectl show -p NTPSynchronized --value)"
E4=$HOME/cyberflow-e4/ec78ca5
echo "--- codigo ec78ca5"; ( cd $E4 && sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS OK ($(wc -l < SHA256SUMS) ficheros)"; sha256sum SHA256SUMS )
echo "--- modelo/escalador/features/manifiesto"
for f in $(cd $HOME/cyberflow && ls models/*limpio* models/*manifest* models/*scaler* models/*feature* 2>/dev/null | sort -u); do sha256sum $HOME/cyberflow/$f; done
grep -rho 'if_limpio[^"]*joblib' $HOME/cyberflow/config/*.toml 2>/dev/null | sort -u
echo "--- unidades"
for u in suricata ppi-motor ppi-motor-capture ppi-via-rapida@ens37 ppi-publicar-feed-v2 ppi-publicar-feed.timer ppi-publicar-feed cf-tcpdump-estadisticas.timer ppi-dashboard cf-primer-pcap.service cf-primer-pcap.path; do
  printf '%-32s %s/%s\n' $u "$(systemctl is-active $u 2>/dev/null)" "$(systemctl is-enabled $u 2>/dev/null)"; done
systemctl list-units --all --plain --no-legend 'cf-*' 'ppi-*' | awk '{print "  "$1, $3, $4}'
echo "--- cmdlines"
for u in ppi-motor ppi-motor-capture ppi-via-rapida@ens37 ppi-publicar-feed-v2 suricata; do
  p=$(systemctl show -p MainPID --value $u); echo "$u pid=$p inicio=$(systemctl show -p ActiveEnterTimestamp --value $u) NRestarts=$(systemctl show -p NRestarts --value $u)"
  [ "$p" != 0 ] && tr '\0' ' ' < /proc/$p/cmdline | cut -c1-400 && echo
done
echo "--enforce/--aplicar en procesos: $(ps -eo args | grep -E -- '--(enforce|aplicar)' | grep -vc grep)"
echo "--- drop-ins"
for d in /etc/systemd/system/ppi-motor.service.d /etc/systemd/system/ppi-motor-capture.service.d /etc/systemd/system/suricata.service.d; do
  ls $d 2>/dev/null | while read f; do sha256sum $d/$f; done; done
echo "--- suricata"
sha256sum /etc/suricata/suricata.yaml
grep -nE '^\s*(ring-size|null-values|interval|filename: (eve|stats))' /etc/suricata/suricata.yaml | head -20
suricata -V 2>/dev/null | head -1
e=/var/log/suricata/eve.json; echo "eve ultima escritura hace $(( $(date +%s) - $(stat -c %Y $e) )) s; tamano $(stat -c %s $e)"
ls -la /var/log/suricata/ | head -20
tail -c 400000 $e | grep '"event_type":"stats"' | tail -1 | python3 -c 'import json,sys; e=json.load(sys.stdin); c=e["stats"]["capture"]; print("ultimo stats EVE:", e["timestamp"], "uptime", e["stats"]["uptime"], c)'
echo "--- primer pcap / anillo"
ls /usr/local/bin/cf-primer-pcap* /usr/local/sbin/cf-primer-pcap* 2>/dev/null | xargs -r sha256sum
ls /var/lib/ppi-motor-capture | head -2; ls /var/lib/ppi-motor-capture | wc -l
echo "--- feed-v2"; ls -la --time-style=+%FT%T $HOME/feed-v2 | head
echo "--- nic"; ip -s -s link show ens37 | head -12; for c in rx_dropped rx_missed_errors rx_fifo_errors rx_over_errors rx_packets; do printf '%s=%s ' $c $(cat /sys/class/net/ens37/statistics/$c); done; echo
ethtool -i ens37 2>/dev/null; ethtool -S ens37 2>/dev/null | head -60
cat /sys/class/net/ens37/flags /sys/class/net/ens37/promiscuity 2>/dev/null
ip -d link show ens37 | head -4
echo "--- kernel"; uname -r
