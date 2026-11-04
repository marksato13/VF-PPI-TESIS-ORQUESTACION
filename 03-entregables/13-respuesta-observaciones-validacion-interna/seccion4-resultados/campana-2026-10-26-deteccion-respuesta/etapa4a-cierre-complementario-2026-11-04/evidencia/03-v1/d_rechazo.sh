set -u
# [srv-dmz] Contexto del único rechazo del agente v2 (solo lectura)
sudo -n cat /var/lib/cyberflow/agente/traza.jsonl | python3 -c '
import json,sys,datetime as dt
r=[json.loads(l) for l in sys.stdin if l.strip()]
i=[k for k,x in enumerate(r) if x.get("evento")=="rechazo"]
f=lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3]
print("rechazos en todo el fichero:", len(i), "de", len(r), "; primera linea", f(r[0]["t"]))
for k in i:
    for x in r[max(0,k-3):k+4]:
        print(f(x["t"]), x.get("evento"), x.get("estado"), x.get("motivo"), "sec", x.get("secuencia"), "mtime_feed", f(x["mtime_feed"]) if x.get("mtime_feed") else None, "gen", f(x["generado"]) if x.get("generado") else None)'
sudo -n journalctl --no-pager -o short-iso-precise -u ppi-enforce-agent-v2-dmz --since "2026-11-04 06:26:20" --until "2026-11-04 06:26:35" 2>/dev/null | grep -v pam_unix | head -n 20
ls -la --time-style=full-iso /var/lib/cyberflow/feed/ 2>/dev/null || sudo -n ls -la --time-style=full-iso /var/lib/cyberflow/feed/ 2>&1 | head
