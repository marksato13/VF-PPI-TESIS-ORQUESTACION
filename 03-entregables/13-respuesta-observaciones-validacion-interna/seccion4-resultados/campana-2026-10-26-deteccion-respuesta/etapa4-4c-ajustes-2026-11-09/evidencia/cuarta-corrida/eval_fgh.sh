ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'python3 - <<PY
import os, datetime as dt
T = lambda s: dt.datetime.strptime(s, "%H:%M:%S")
def cargar(p):
    p = os.path.expanduser(p)
    if not os.path.exists(p): return {}
    L = [l.split() for l in open(p) if len(l.split()) == 3]
    return {L[i][0]: (int(L[i][1]) - int(L[i-1][1])) / max(1, (T(L[i][0]) - T(L[i-1][0])).total_seconds()) for i in range(1, len(L))}
r = cargar("~/espejo-1s-f-20261109.log"); r.update(cargar("~/espejo-1s-g-20261109.log")); r.update(cargar("~/espejo-1s-h-20261109.log"))
k = sorted(r)
cortes = []
for h in k:
    if r[h] < 20:
        if cortes and (T(h) - T(cortes[-1][1])).total_seconds() <= 3: cortes[-1][1] = h
        else: cortes.append([h, h])
ultimo = cortes[-1][1] if cortes else k[0]
racha = (T(k[-1]) - T(ultimo)).total_seconds()
print("registro continuo:", k[0], "->", k[-1], "| cortes:", len(cortes), cortes[-3:])
print(f"racha limpia tras el último corte ({ultimo}): {int(racha)} s ({racha/60:.1f} min); 30 min a las " + (T(ultimo)+dt.timedelta(minutes=30)).strftime("%H:%M:%S") + "Z")
PY'

