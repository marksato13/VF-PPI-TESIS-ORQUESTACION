set -u
echo "### srv-dmz $(date -u +%FT%TZ)"
systemctl list-units --all --no-pager '*ppi*' '*cyberflow*' '*enforce*' | cat
systemctl list-unit-files --no-pager '*ppi*' '*cyberflow*' '*enforce*' | cat
systemctl list-timers --all --no-pager | grep -iE 'ppi|enforce|cyberflow'
sudo -n nft list tables; sudo -n nft list ruleset | sha256sum
ls -la /var/lib/cyberflow/ 2>&1; sudo -n ls -la /var/lib/cyberflow/feed 2>&1
T=$(sudo -n ls /var/log/cyberflow/ 2>/dev/null); echo "logs: $T"
ps -eo pid,user,args | grep -E 'agente|enforce|ppi' | grep -v grep
