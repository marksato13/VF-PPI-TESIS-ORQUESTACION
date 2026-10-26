echo "== crontab m4rk (sensor)"; crontab -l 2>&1 | grep -vE '^\s*#' | grep -E 'publicar|acumular|motor|feed|captura'
echo "== timers activos (sensor)"; systemctl list-timers --all --no-pager 2>/dev/null | grep -Ei 'ppi|cyberflow|acumular' | awk '{print $NF,$1}'
echo "== agente: modo (aplicar vs sombra) en srv-dmz"
ssh -n -o BatchMode=yes -o ConnectTimeout=6 -i ~/.ssh/cyberflow-to-sensor gadmin@10.10.10.30 'crontab -l 2>&1 | grep -vE "^\s*#" | grep -Ei "relay|feed"' 2>&1 | head -5