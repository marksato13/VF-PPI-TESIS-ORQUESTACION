M=~/cyberflow/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json
sha256sum $M | cut -c1-64
python3 - <<PY
import json
j = json.load(open("$M"))
def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items(): walk(v, p + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o[:6]): walk(v, p + f"[{i}]")
    elif isinstance(o, float) and -0.7 < o < -0.5: print("  ", p, "=", repr(o))
    elif isinstance(o, str) and ("umbral" in p.lower() or "threshold" in p.lower() or "sha" in p.lower() or "model" in p.lower()) and len(o) < 140: print("  ", p, "=", o)
walk(j)
PY
echo "== servicio: unidad ppi-motor activa desde"; systemctl show ppi-motor -p ActiveEnterTimestamp --value
echo "== umbral que aparece en cada decisión vs arranque del motor"; head -c 600 ~/cf-e4/4c/copias/motor_decision.log | head -2 | cut -c1-300
