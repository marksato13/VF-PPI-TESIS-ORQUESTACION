set -u
T=/var/lib/cyberflow/agente/traza.jsonl
ls -la --time-style=full-iso $T 2>&1
sudo -n tail -n 400 $T 2>/dev/null | python3 -c '
import json,sys,collections
r=[json.loads(l) for l in sys.stdin if l.strip()]
print("lineas", len(r)); c=collections.Counter((x.get("evento") or x.get("event"), x.get("resultado") or x.get("estado"), x.get("aplicada")) for x in r[-200:]); print(c.most_common(8))
print("ultima", {k: r[-1].get(k) for k in list(r[-1])[:12]})' || echo "traza no legible sin sudo"
ls -la --time-style=full-iso /var/lib/cyberflow/feed/ 2>&1 | tail -n 3
