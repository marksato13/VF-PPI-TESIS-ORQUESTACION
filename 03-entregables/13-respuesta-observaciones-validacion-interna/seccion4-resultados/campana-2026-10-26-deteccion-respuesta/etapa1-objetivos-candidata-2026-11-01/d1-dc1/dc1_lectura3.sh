echo "== fecha"; date -u +%FT%TZ
echo "== openssl"; command -v openssl && openssl version
echo "== nft version"; /usr/sbin/nft --version 2>&1
echo "== testparm dns"; testparm -sv 2>/dev/null | grep -iE "^\s*(dns|allow dns)"
echo "== escucha53"; ss -lnu | grep -E ":53 "; ss -lnt | grep -E ":53 "
echo "== nft ruleset lineas"; sudo -n /usr/sbin/nft list ruleset 2>/dev/null | wc -l
echo "== nftables.service"; systemctl is-enabled nftables 2>&1; systemctl is-active nftables 2>&1
echo "== samba-ad-dc"; systemctl is-active samba-ad-dc; /usr/sbin/samba -V
echo "== os"; . /etc/os-release; echo "$PRETTY_NAME"; uname -r
echo "== python"; python3 -V
echo "== ntp"; timedatectl show -p NTPSynchronized
