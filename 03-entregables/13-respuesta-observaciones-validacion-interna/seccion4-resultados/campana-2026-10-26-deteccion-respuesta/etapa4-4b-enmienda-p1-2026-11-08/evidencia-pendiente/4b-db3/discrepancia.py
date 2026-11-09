import json, datetime as dt, collections
from pathlib import Path
D = Path(r"C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\db3_4b\datos")
T0 = dt.datetime(2026, 11, 8, 18, 0, 0, tzinfo=dt.timezone.utc).timestamp(); T1 = dt.datetime(2026, 11, 9, 2, 0, 0, tzinfo=dt.timezone.utc).timestamp()
grid = [T0 + 10 * i for i in range(int((T1 - T0) / 10) + 1)]
iso = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S")
def leer(p):
    out = collections.defaultdict(set)
    for l in open(p, errors="replace"):
        try: r = json.loads(l)
        except Exception: continue
        we = r.get("window_end_utc") or r.get("window_end")
        if not we or "decision" not in r: continue
        t = dt.datetime.fromisoformat(str(we).replace("Z", "+00:00")).timestamp()
        if T0 <= t <= T1: out[r.get("entity_ip")].add(t)
    return out
vivo = leer(D / "copias/motor_decision.log"); inv = leer(D / "replay/motor_decision.log")
print("rejilla de 10 s en [18:00Z, 02:00Z]:", len(grid), "ventanas posibles por entidad")
print(f"{'IP':14} {'vivo':>5} {'inventario':>10} {'solo_vivo':>9} {'solo_inv':>8}  faltan en la rejilla (vivo)")
for ip in [f"10.10.20.{n}" for n in range(21, 27)] + ["10.10.10.21"]:
    v, i = vivo.get(ip, set()), inv.get(ip, set())
    falt = [t for t in grid if t not in v]
    # agrupar huecos consecutivos
    tramos, ini, prev = [], None, None
    for t in falt:
        if ini is None: ini = prev = t
        elif t - prev <= 10.0001: prev = t
        else: tramos.append((ini, prev)); ini = prev = t
    if ini is not None: tramos.append((ini, prev))
    txt = "; ".join(f"{iso(a)}" + (f"-{iso(b)} ({int((b-a)/10)+1}v)" if b != a else "") for a, b in tramos[:6]) + (f" ... +{len(tramos)-6} tramos" if len(tramos) > 6 else "")
    print(f"{ip:14} {len(v):5} {len(i):10} {len(v-i):9} {len(i-v):8}  {len(falt)} faltan: {txt}")
