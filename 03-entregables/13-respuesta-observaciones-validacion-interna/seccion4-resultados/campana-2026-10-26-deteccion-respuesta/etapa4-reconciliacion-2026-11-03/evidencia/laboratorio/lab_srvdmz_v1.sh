#!/bin/bash
# SOLO LECTURA en srv-dmz (via bastion): estado de la cadena v1 y de las tablas nft. Sin escribir nada.
set -u
ssh -o BatchMode=yes -o ConnectTimeout=8 srvdmz 'bash -s' <<'REMOTO'
set -u
date -Is
for u in ppi-enforce-agent.timer ppi-enforce-agent.service ppi-enforce-agent-v2-dmz.service ppi-brute-lab.service; do
  printf '%s enabled=%s active=%s\n' "$u" "$(systemctl is-enabled "$u" 2>/dev/null)" "$(systemctl is-active "$u" 2>/dev/null)"
done
systemctl show ppi-enforce-agent.timer -p ActiveEnterTimestamp -p UnitFileState 2>/dev/null
echo "#### tablas nft (sudo -n, lectura)"
sudo -n nft list tables 2>&1 | head -20
echo "#### elementos por set en tablas cyberflow*"
for t in $(sudo -n nft list tables 2>/dev/null | awk '$3 ~ /cyberflow/ {print $2" "$3}' | tr ' ' ':'); do
  fam=${t%%:*}; tab=${t#*:}
  sudo -n nft -j list table "$fam" "$tab" 2>/dev/null | python3 -c '
import json,sys
d=json.load(sys.stdin)
for o in d.get("nftables",[]):
    if "set" in o:
        s=o["set"]; print("set", s.get("table"), s.get("name"), "elementos=", len(s.get("elem",[]) or []))
    if "chain" in o:
        c=o["chain"]; print("chain", c.get("table"), c.get("name"), "hook=", c.get("hook"), "prio=", c.get("prio"))
'
done
echo "#### ultimas lineas del registro del agente v1 (sin claves)"
ls -la ~/enforce 2>/dev/null | head -15
for f in ~/enforce/*.log ~/enforce/estado*.json; do [ -f "$f" ] && { echo "== $f"; tail -n 3 "$f" | cut -c1-300; }; done
journalctl -u ppi-enforce-agent.service --since "-36h" --no-pager 2>/dev/null | grep -iE 'aplic|block|limit|liber' | tail -8 | cut -c1-250
REMOTO
