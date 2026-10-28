#!/usr/bin/env bash
# PREFLIGHT 08 — sensor: feed publicado, estado de escalada, reglas nft del sensor, publicador. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p08 sensor feed  inicio=$(ts)"
F=$HOME/feed
ls -la "$F" 2>&1 | sed 's/^/  /'
echo "## feed.json (entradas)"
python3 - "$F/feed.json" "$F/estado.json" <<'PY'
import json,sys,time
try:
    f=json.load(open(sys.argv[1]))
    ent=f.get("entradas") or f.get("entries") or f.get("decisiones") or []
    print("  claves:",sorted(f.keys()))
    for k in ("emitido","generado","version","umbrales","expira","publicado_en"):
        if k in f: print("  ",k,"=",f[k])
    print("  entradas:",len(ent))
    for e in ent[:10]: print("    ",json.dumps(e,ensure_ascii=False)[:220])
except Exception as ex: print("  feed.json ilegible:",ex)
try:
    s=json.load(open(sys.argv[2]))
    print("## estado.json (escalada)")
    print("  claves:",sorted(s.keys()) if isinstance(s,dict) else type(s).__name__)
    print("  ",json.dumps(s,ensure_ascii=False)[:900])
except Exception as ex: print("  estado.json ilegible:",ex)
PY
echo "## por que 10.10.50.52: ultimas decisiones del motor para esa IP"
grep '"entity_ip": "10.10.50.52"' "$HOME/cyberflow/logs/motor_decision.log" | tail -n 3 | cut -c1-300 | sed 's/^/  /'
echo "  ALERT de 10.10.50.52 hoy: $(grep '"entity_ip": "10.10.50.52"' "$HOME/cyberflow/logs/motor_decision.log" | grep -c '"ALERT"')"
echo "## publicador"; systemctl show ppi-publicar-feed.service -p ExecStart --value 2>/dev/null | sed -E 's/.*argv\[\]=([^;]*);.*/  \1/'
sudo -n journalctl --no-pager -u ppi-publicar-feed.service -n 4 2>&1 | sed 's/^/  /'
echo "## nftables del SENSOR (consulta real)"
if o=$(sudo -n nft list ruleset 2>&1); then echo "  consulta OK; tablas:"; echo "$o" | grep -E '^table' | sed 's/^/    /'; echo "$o" | grep -E 'elements' | sed 's/^/    elementos: /' | head -5; echo "  (sin 'elements' => sin elementos)"; else echo "  CONSULTA FALLIDA: $o -> DESCONOCIDO"; fi
echo "## fin=$(ts)"
