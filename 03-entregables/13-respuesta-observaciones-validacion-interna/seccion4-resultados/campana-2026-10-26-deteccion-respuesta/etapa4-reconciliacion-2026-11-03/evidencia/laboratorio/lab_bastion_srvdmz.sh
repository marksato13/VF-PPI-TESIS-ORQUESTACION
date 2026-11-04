#!/bin/bash
# SOLO LECTURA en el bastion y, a traves de el, en srv-dmz. Sin sudo, sin secretos.
set -u
red() { sed -E 's/((pass|token|secret|clave|private|apikey|api_key)[^=]*=).*/\1<omitido>/I'; }
blob() { local n; n=$(stat -c %s "$1"); { printf 'blob %s\0' "$n"; cat "$1"; } | sha1sum | cut -c1-40; }
echo "### BASTION $(hostname) $(date -Is)"
systemctl list-units --all --no-legend '*relay*' '*feed*' 'ppi-*' 'cyberflow*' 2>/dev/null | awk '{print $1, $3, $4}'
systemctl list-timers --all --no-legend 2>/dev/null | grep -iE 'relay|feed|ppi|cyber' | awk '{print $(NF-1), $NF}'
for u in $(systemctl list-unit-files --no-legend '*relay*' 2>/dev/null | awk '{print $1}'); do echo "#### $u"; systemctl cat "$u" | grep -Ev '^\s*$' | red; done
echo "#### crontab (lineas con relay/feed)"; crontab -l 2>/dev/null | grep -iE 'relay|feed' | red
echo "#### ficheros del relay"
for f in $(ls ~/cyberflow-relay/* ~/relay/* ~/cf-relay/* /usr/local/bin/*relay* /opt/cyberflow/* 2>/dev/null); do [ -f "$f" ] && printf '%s %s %s\n' "$(blob "$f")" "$(stat -c '%y' "$f" | cut -c1-16)" "$f"; done
ls -la ~/cf-demo 2>/dev/null | head -5
echo
echo "### SRV-DMZ (via bastion)"
ssh -o BatchMode=yes -o ConnectTimeout=8 srvdmz 'bash -s' <<'REMOTO'
set -u
red() { sed -E 's/((pass|token|secret|clave|private|apikey|api_key)[^=]*=).*/\1<omitido>/I'; }
blob() { local n; n=$(stat -c %s "$1"); { printf 'blob %s\0' "$n"; cat "$1"; } | sha1sum | cut -c1-40; }
hostname; date -Is
systemctl list-units --all --no-legend 'ppi-*' '*enforce*' 2>/dev/null | awk '{print $1, $3, $4}'
systemctl list-timers --all --no-legend 2>/dev/null | grep -iE 'enforce|ppi' | awk '{print $(NF-1), $NF}'
for u in $(systemctl list-unit-files --no-legend 'ppi-*' '*enforce*' 2>/dev/null | awk '{print $1}'); do echo "#### $u"; systemctl cat "$u" | grep -Ev '^\s*$' | red; done
echo "#### ficheros del agente"
for f in $(find ~ /opt /usr/local/bin /etc/cyberflow* -maxdepth 3 -type f \( -name 'agente_enforce*.py' -o -name 'alcance*.json' -o -name 'feed.py' -o -name '*.pub' -o -name 'helper*nft*' -o -name '*nft*.sh' \) 2>/dev/null | grep -v '\.bak'); do printf '%s %s %s\n' "$(blob "$f")" "$(stat -c '%y' "$f" | cut -c1-16)" "$f"; done
echo "#### alcance.json"; for a in $(find ~ /etc/cyberflow* -maxdepth 3 -name 'alcance*.json' 2>/dev/null); do echo "$a"; cat "$a"; echo; done
echo "#### estado del agente (ficheros de estado, sin claves)"; ls -la ~/enforce* ~/.cyberflow* /var/lib/cyberflow* 2>/dev/null | head -30
echo "#### sudoers visibles para el agente (sin sudo: sudo -n -l)"; sudo -n -l 2>&1 | grep -iE 'nft|NOPASSWD' | head -5
REMOTO

