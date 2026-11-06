set -u
# [SENSOR1 m4rk] SOLO LECTURA: ¿hubo tráfico de los seis perfiles legítimos (10.10.20.21-26) en la ventana fija
# 04:50-05:50Z del 06-nov? Flujos de EVE por IP de origen, dentro y fuera de la ventana. No cambia nada.
ls -la /var/log/suricata/ | grep -E 'eve' | head
python3 -I - <<'EOF'
import json, collections, datetime
D0, D1 = 1793940600, 1793944200
perf = {f"10.10.20.{i}" for i in range(20, 27)}
dentro, horas = collections.Counter(), collections.Counter()
pk, n, malas = collections.Counter(), 0, 0
def ts(s):
    return datetime.datetime.strptime(s[:26] + s[-5:], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
with open("/var/log/suricata/eve.json", encoding="utf-8", errors="replace") as f:
    for l in f:
        if '"event_type":"flow"' not in l:
            continue
        try:
            e = json.loads(l)
        except ValueError:
            malas += 1
            continue
        n += 1
        ip = e.get("src_ip")
        t = ts(e["timestamp"])
        if ip in perf:
            horas[datetime.datetime.utcfromtimestamp(t).strftime("%m-%d %H")] += 1
            if D0 <= t < D1:
                dentro[ip] += 1
                fl = e.get("flow", {})
                pk[ip] += fl.get("pkts_toserver", 0) + fl.get("pkts_toclient", 0)
print("eventos flow leídos:", n, "líneas ilegibles:", malas)
print("ventana 04:50-05:50Z, flujos con origen 10.10.20.20-26:", dict(dentro), "paquetes:", dict(pk))
print("flujos de esos orígenes por hora UTC (todo eve.json):", dict(sorted(horas.items())))
EOF
