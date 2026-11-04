set -u
echo "== sección stats de outputs y global"
grep -nE '^\s*(- stats:|stats:|null-values|totals|threads|interval|filename: stats)' /etc/suricata/suricata.yaml | head -n 20
suricata --dump-config 2>/dev/null | grep -E '^(stats|outputs\.[0-9]+\.stats)' | head -n 20
echo "== último bloque completo de stats.log"
awk '/^Date:/{n++} {if(n>0) b[n]=b[n] $0 "\n"} END{printf "%s", b[n-1]}' /var/log/suricata/stats.log | head -n 40
echo "== bloques desde el reinicio con y sin kernel_drops"
awk '/^Date:/{if(d!="") print d, p, k; d=$0; p=0; k=0} /capture.kernel_packets/{p=1} /capture.kernel_drops/{k=1} END{print d,p,k}' /var/log/suricata/stats.log | grep 'uptime: 0d' | awk '{c[$NF]++} END{for(x in c) print "kernel_drops_presente=" x, c[x]}'
grep -E 'event_type":"stats' /var/log/suricata/eve.json | tail -n 1 | head -c 600; echo
