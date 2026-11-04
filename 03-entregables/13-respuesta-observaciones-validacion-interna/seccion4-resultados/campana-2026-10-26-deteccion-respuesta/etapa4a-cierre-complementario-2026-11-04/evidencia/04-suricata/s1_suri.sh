set -u
Y=/etc/suricata/suricata.yaml
sed -n '614,720p' $Y | grep -nE 'ring-size|block-size|block-timeout|tpacket|use-mmap|mmap|buffer-size|threads|interface|max-pending|emergency'
echo "### comentarios de ring-size"; grep -n -B6 -A3 'ring-size' $Y | head -40
grep -nE '^\s*#?\s*max-pending-packets' $Y
echo "### dump-config (sin root)"; suricata --dump-config -c $Y 2>&1 | grep -iE '^af-packet|^max-pending|^runmode|^stats\.' | head -40
echo "### suricata.log del arranque 30-oct"
ls -l /var/log/suricata/ | head;
for f in /var/log/suricata/suricata.log*; do echo "== $f"; (zcat -f $f 2>&1 | grep -iE 'af.?packet|ring|tpacket|mmap|threads|workers|runmode|max-pending|block' | head -25); done 2>&1 | head -80
echo "### outputs stats"; grep -n -A8 -- '- stats:' $Y | head -20
echo "### packets/sockets"; cat /proc/net/packet | head -12
ps -L -o tid,comm,psr,pcpu -p $(systemctl show -p MainPID --value suricata) | head -20
cat /proc/sys/net/core/rmem_max /proc/sys/net/core/rmem_default
tail -c 30000 /var/log/suricata/stats.log | grep -E 'capture\.|tcp.memuse|flow.memuse|^Date' | tail -12
