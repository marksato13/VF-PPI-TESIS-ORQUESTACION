echo "== samba version"; /usr/sbin/samba -V 2>&1
echo "== server services"; testparm -s --parameter-name="server services" 2>/dev/null; testparm -s --parameter-name="dns forwarder" 2>/dev/null
echo "== proceso 53"; ps -eo pid,comm,args | grep -E "samba.*dns|\[dns" | grep -v grep | head -3
echo "== nft ruleset (solo lectura)"; sudo -n /usr/sbin/nft list ruleset 2>&1 | head -30; echo "lineas: $(sudo -n /usr/sbin/nft list ruleset 2>/dev/null | wc -l)"
echo "== kernel nft"; lsmod | grep -E "^nf_tables" | cut -c1-40
echo "== sshd usuarios"; ls /home
echo "== sudo dcadmin"; sudo -n -l 2>&1 | tail -4
