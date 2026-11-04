set -u
# [Sensor1 m4rk] Hashes congelados y arranque del motor tras el reinicio de las 06:12:46. Solo lectura.
cd /home/m4rk/cyberflow-e4/ec78ca5 && sha256sum -c --quiet SHA256SUMS && echo "ec78ca5 SHA256SUMS OK ($(wc -l < SHA256SUMS) ficheros)"
M=/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10
sha256sum $M/manifest-if-limpio-2026-10.json $M/*.joblib 2>/dev/null
/home/m4rk/cyberflow/.venv/bin/python - <<'EOF'
import json, hashlib, pathlib
m = json.load(open("/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json"))
base = pathlib.Path("/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10")
def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from walk(v, p + "." + k)
    elif isinstance(o, (str, int, float)): yield p, o
for k, v in walk(m):
    if any(s in k.lower() for s in ("sha256", "umbral", "threshold", "n_features", "detector")): print(k, v)
EOF
grep '"event": "motor_startup"' /home/m4rk/cyberflow/logs/motor_decision.log | tail -n 1 | /home/m4rk/cyberflow/.venv/bin/python -c '
import json,sys; d=json.loads(sys.stdin.read()); print({k: d.get(k) for k in ("logged_at","detector_name","threshold","umbral","disparo","modo","manifest","n_features","politica","enforce","aplicar") if k in d}); print(sorted(d)[:40])'
tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-motor)/cmdline | grep -oE -- '--(enforce|aplicar|threshold|manifest[^ ]*|disparo)[= ][^ ]*' || echo "cmdline del motor sin --enforce/--aplicar"
