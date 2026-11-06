set -u
# [BASTIÓN gadmin] Solo lecturas: hueco de secuencias 3654→3713 frente a los arranques de cada host.
echo "arranque bastión: $(uptime -s) ($(date +%Z))"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'echo "arranque Sensor1: $(uptime -s) ($(date +%Z))"'
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'echo "arranque srv-dmz: $(uptime -s) ($(date +%Z))"'
echo "traza del relé alrededor del hueco y bytes NUL:"
python3 - ~/relay-v2/traza.jsonl <<'EOF'
import json, sys, datetime as dt
f = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4] + "Z"
lin = open(sys.argv[1], "rb").read().split(b"\n")
for i, l in enumerate(lin):
    nul = l.count(b"\0")
    try:
        r = json.loads(l.strip(b"\0"))
    except ValueError:
        if nul: print("  línea %d: %d NUL, no es JSON" % (i, nul))
        continue
    s = r.get("secuencia")
    if nul or (isinstance(s, int) and 3650 <= s <= 3716) or r.get("evento") not in ("reenvio",):
        t = r.get("traido_en") or r.get("t") or 0
        print("  línea %d %s seq=%s evento=%s NUL=%d" % (i, f(t), s, r.get("evento"), nul))
EOF
