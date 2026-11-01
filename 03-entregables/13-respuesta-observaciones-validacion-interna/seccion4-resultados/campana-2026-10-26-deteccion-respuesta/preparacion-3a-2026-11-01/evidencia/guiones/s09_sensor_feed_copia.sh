#!/usr/bin/env bash
# PASO3A s09 — sensor (solo lectura): copia con hashes del feed y del estado de escalada; contenido del estado.
set -u
B=$HOME/cf-paso3a-20261101T0523Z/escalada; mkdir -p $B; T=$(date -u +%Y%m%dT%H%M%SZ)
echo "## s09 $(date -u +%FT%T.%3NZ)"
systemctl cat ppi-publicar-feed.service | sed -n '/ExecStart/,/^$/p' | sed 's/^/  /'
for f in feed.json feed.sig estado.json; do cp -p $HOME/feed/$f $B/$f.$T; done
sha256sum $B/*.$T
python3 - $B/estado.json.$T $B/feed.json.$T <<'PY'
import json, sys, time
e = json.load(open(sys.argv[1])); now = time.time()
print("  estado.json: %d IP" % len(e))
for ip, st in sorted(e.items()):
    print("   %-14s bloqueos=%s ultimo_visto=%s (hace %.0f s) %s" % (ip, st.get("bloqueos"), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.get("ultimo_visto", 0))), now - st.get("ultimo_visto", 0), {k: v for k, v in st.items() if k not in ("bloqueos", "ultimo_visto")}))
f = json.load(open(sys.argv[2]))
ents = f.get("entradas") or f.get("entries") or (f.get("payload") or {}).get("entradas") or []
print("  feed: claves=%s entradas=%d" % (sorted(f)[:10], len(ents)))
for x in ents[:10]: print("   ", json.dumps(x, ensure_ascii=False)[:220])
PY
echo "## fin"
