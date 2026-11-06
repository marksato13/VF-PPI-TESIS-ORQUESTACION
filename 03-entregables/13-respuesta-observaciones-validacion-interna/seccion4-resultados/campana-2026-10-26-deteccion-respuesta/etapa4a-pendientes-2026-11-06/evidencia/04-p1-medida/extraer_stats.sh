set -u
# [SENSOR1 m4rk] Solo lectura de /var/log/suricata (0644). Extrae los eventos stats de EVE entre DESDE y HASTA
# (epoch) a ~/cf-e4p/, reducidos a timestamp + uptime + capture, con el sha256 de las líneas originales.
DESDE=${1:?desde}; HASTA=${2:?hasta}; NOMBRE=${3:?nombre}
mkdir -p ~/cf-e4p
cd /var/log/suricata
for f in eve.json.1-2026110600.backup eve.json; do
  echo "== $f primera/ultima stats:"
  grep -m1 '"event_type":"stats"' $f | cut -c1-60
  tail -c 3000000 $f | grep '"event_type":"stats"' | tail -1 | cut -c1-60
done
python3 - "$DESDE" "$HASTA" ~/cf-e4p/$NOMBRE eve.json.1-2026110600.backup eve.json <<'EOF'
import json, sys, hashlib, datetime as dt
desde, hasta, salida = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
h = hashlib.sha256(); n = 0
with open(salida + ".jsonl", "w") as out:
    for f in sys.argv[4:]:
        with open(f, "rb") as fh:
            for l in fh:
                if b'"event_type":"stats"' not in l:
                    continue
                e = json.loads(l)
                ts = e["timestamp"]
                t = dt.datetime.strptime(ts[:26] + ts[-5:], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
                if not (desde <= t <= hasta):
                    continue
                h.update(l); n += 1
                r = {"timestamp": ts, "event_type": "stats",
                     "stats": {"uptime": e["stats"]["uptime"], "capture": e["stats"].get("capture")}}
                out.write(json.dumps(r, separators=(",", ":")) + "\n")
print("lineas", n, "sha256_lineas_originales", h.hexdigest())
EOF
sha256sum ~/cf-e4p/$NOMBRE.jsonl
