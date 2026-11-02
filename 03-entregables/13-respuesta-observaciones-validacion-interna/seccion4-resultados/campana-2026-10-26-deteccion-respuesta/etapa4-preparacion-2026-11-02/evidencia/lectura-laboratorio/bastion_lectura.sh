#!/usr/bin/env bash
# Lecturas en el bastion y, por SSH con las llaves existentes, en srv-dmz, cliente y DC1. Sin sudo, sin cambios.
set +e
mask() { sed -E 's/(([A-Za-z_]*(KEY|TOKEN|PASS|SECRET|PWD)[A-Za-z_]*)=)[^ "]*/\1***/Ig'; }
echo "== BASTION $(hostname) $(date -u +%FT%T.%3NZ)"
echo "-- hosts del ssh config"; awk '/^Host /{h=$2} /HostName/{print h, $2} /^ *User /{print "   user", $2}' ~/.ssh/config
echo "-- unidades ppi/cyberflow"
systemctl list-units --all --no-legend --plain 'ppi-*' 'cyberflow*' | cat
systemctl list-unit-files --no-legend 'ppi-*' 'cyberflow*' | cat
for u in $(systemctl list-units --all --no-legend --plain 'ppi-*' 'cyberflow*' | awk '{print $1}'); do
  echo "---- $u"; systemctl show "$u" -p UnitFileState -p ActiveState -p SubState -p ExecMainStartTimestamp -p FragmentPath -p DropInPaths | cat
  systemctl cat "$u" 2>&1 | grep -vE '^\s*#' | mask
done
echo "-- ficheros del rele"; ls -la ~/relay* ~/cyberflow-relay* /opt/cyberflow 2>&1 | head -40
for f in $(systemctl cat ppi-relay-feed.service 2>/dev/null | grep -oE '/[^ ]+\.(py|sh)' | sort -u); do sha256sum "$f" 2>&1; done
journalctl -u ppi-relay-feed --since -2min --no-pager -o short-iso 2>&1 | tail -4 | cut -c1-400
timedatectl 2>&1 | grep -E 'synchronized|NTP service|Universal'

for H in srvdmz; do
  echo; echo "== $H"
  ssh -o BatchMode=yes -o ConnectTimeout=8 $H 'bash -s' <<'EOS'
set +e
mask() { sed -E 's/(([A-Za-z_]*(KEY|TOKEN|PASS|SECRET|PWD)[A-Za-z_]*)=)[^ "]*/\1***/Ig'; }
hostname; date -u +%FT%T.%3NZ; id
systemctl list-units --all --no-legend --plain 'ppi-*' 'cyberflow*' | cat
systemctl list-unit-files --no-legend 'ppi-*' 'cyberflow*' | cat
for u in $(systemctl list-units --all --no-legend --plain 'ppi-*' 'cyberflow*' | awk '{print $1}'); do
  echo "---- $u"; systemctl show "$u" -p UnitFileState -p ActiveState -p SubState -p ExecMainStartTimestamp -p FragmentPath -p DropInPaths -p User | cat
  systemctl cat "$u" 2>&1 | grep -vE '^\s*#' | mask
done
for f in $(systemctl cat 'ppi-*' 2>/dev/null | grep -oE '/[^ ]+\.(py|sh|json|pem)' | sort -u); do printf '%s ' "$f"; sha256sum "$f" 2>&1 | cut -c1-64; done
echo "-- traza/estado del agente (cola)"
for f in $(ls -t ~/enforce*/*.log ~/enforce*/*.jsonl ~/enforce*/estado* 2>/dev/null | head -4); do echo "# $f"; tail -3 "$f" | cut -c1-400; done
ls -la ~ | head -40
journalctl -u 'ppi-enforce-agent*' --since -3min --no-pager -o short-iso 2>&1 | tail -6 | cut -c1-400
echo "-- sudo listado (no ejecuta)"; sudo -n -l 2>&1 | head -12
echo "-- tablas nft visibles sin privilegios"; nft list tables 2>&1 | head -5
timedatectl 2>&1 | grep -E 'synchronized|NTP service|Universal'
EOS
done
