echo "== publicador: timer y ExecStart"
systemctl cat ppi-publicar-feed.timer ppi-publicar-feed.service 2>/dev/null | grep -Ei "OnCalendar|OnUnitActive|ExecStart|ventana-segundos|umbrales" | head -10
echo "== feed/"; ls -la --time-style=full-iso ~/feed/ 2>/dev/null | head
echo "== estado.json (si existe, enforcement vivo)"; cat ~/feed/estado.json 2>/dev/null | head -c 400; echo