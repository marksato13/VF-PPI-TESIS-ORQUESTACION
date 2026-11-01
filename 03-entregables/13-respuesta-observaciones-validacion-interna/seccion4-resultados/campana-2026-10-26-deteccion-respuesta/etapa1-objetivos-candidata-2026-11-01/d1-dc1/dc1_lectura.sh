echo "== os"; . /etc/os-release; echo "$PRETTY_NAME"; uname -r; hostname
echo "== samba"; samba -V 2>&1; systemctl is-active samba-ad-dc; systemctl is-enabled samba-ad-dc
echo "== smbconf"; grep -iE "server role|server services|dns forwarder|dns update|bind interfaces|interfaces|allow dns updates" /etc/samba/smb.conf
echo "== bind9"; dpkg -l bind9 2>/dev/null | grep ^ii | cut -c1-60; systemctl is-active named 2>&1
echo "== escucha53"; ss -lnu | grep -E ":53 "; ss -lnt | grep -E ":53 "
echo "== nft"; command -v nft; dpkg -l nftables iptables ufw firewalld 2>/dev/null | grep ^ii | cut -c1-70; echo "nftables enabled: $(systemctl is-enabled nftables 2>&1) active: $(systemctl is-active nftables 2>&1)"
echo "== python"; python3 -V; command -v curl
echo "== ip"; ip -br a
echo "== sudo"; sudo -n true 2>&1 | head -1; id
echo "== timers"; systemctl list-timers --all --no-pager 2>/dev/null | head -12
echo "== ntp"; timedatectl show -p NTPSynchronized -p Timezone
echo "== recursos"; nproc; free -m | head -2
