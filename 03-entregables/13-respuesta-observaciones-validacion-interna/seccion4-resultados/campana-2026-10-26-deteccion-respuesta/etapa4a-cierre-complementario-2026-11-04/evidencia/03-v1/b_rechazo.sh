set -u
# [bastión] Cómo copia ppi-relay-eventos el feed v2 (solo lectura) y qué hizo a las 06:26:2x
systemctl cat ppi-relay-eventos | grep -E 'ExecStart|^# /'
S=$(systemctl show -p ExecStart --value ppi-relay-eventos | grep -o 'path=[^ ;]*' | cut -d= -f2)
echo "script: $S"; for a in $(systemctl show -p ExecStart --value ppi-relay-eventos | grep -o 'argv\[\]=[^;]*' | cut -d= -f2-); do [ -f "$a" ] && { echo "--- $a"; sha256sum "$a"; grep -nE 'feed|sig|rsync|scp|cat|mv|tmp|inotify|sleep' "$a" | head -n 40; }; done
journalctl --user --no-pager -o short-iso-precise -u ppi-relay-eventos --since "2026-11-04 06:26:15" --until "2026-11-04 06:26:35" 2>/dev/null | head -n 20
