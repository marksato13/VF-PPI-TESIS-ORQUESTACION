import json, datetime as dt, bisect
from pathlib import Path
D = Path(r"C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\db3_4b\datos")
T0 = dt.datetime(2026, 11, 8, 18, 0, 0, tzinfo=dt.timezone.utc).timestamp(); T1 = dt.datetime(2026, 11, 9, 2, 0, 0, tzinfo=dt.timezone.utc).timestamp()
grid = [T0 + 10 * i for i in range(int((T1 - T0) / 10) + 1)]
def vivo(ip):
    s = set()
    for l in open(D / "copias/motor_decision.log", errors="replace"):
        if ip not in l: continue
        try: r = json.loads(l)
        except Exception: continue
        if r.get("entity_ip") != ip or "decision" not in r: continue
        we = r.get("window_end_utc") or r.get("window_end")
        s.add(dt.datetime.fromisoformat(str(we).replace("Z", "+00:00")).timestamp())
    return s
IPS = ["10.10.20.23", "10.10.20.25"]
VIVO = {ip: vivo(ip) for ip in IPS}
falt = {ip: sorted(t for t in grid if t not in VIVO[ip]) for ip in IPS}
ev = {ip: [] for ip in IPS}; tipos = {ip: {} for ip in IPS}
with open(D / "copias/eve-segmento.json", errors="replace") as fh:
    for l in fh:
        for ip in IPS:
            if ip in l:
                try: j = json.loads(l)
                except Exception: continue
                if j.get("src_ip") != ip and j.get("dest_ip") != ip: continue
                try: t = dt.datetime.fromisoformat(j["timestamp"]).timestamp()
                except Exception: continue
                ev[ip].append(t); tipos[ip][j.get("event_type")] = tipos[ip].get(j.get("event_type"), 0) + 1
for ip in IPS:
    e = sorted(ev[ip]); print(f"{ip}: {len(e)} eventos EVE con esa IP; por tipo {tipos[ip]}")
    # una ventana con window_end=w cubre (w-10, w]; se cuentan eventos en (w-10, w] y, por holgura de inicio de flujo, en (w-60, w]
    con10 = con60 = 0
    for w in falt[ip]:
        a = bisect.bisect_right(e, w - 10); b = bisect.bisect_right(e, w); a60 = bisect.bisect_right(e, w - 60)
        con10 += (b - a) > 0; con60 += (b - a60) > 0
    print(f"   ventanas faltantes: {len(falt[ip])}; con algún evento EVE en (w-10, w]: {con10}; en (w-60, w]: {con60}")
