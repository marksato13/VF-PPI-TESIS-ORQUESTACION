import csv, gzip, hashlib, json, math, sys
from pathlib import Path
G = Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados")
CAL = G / "4.1-modelos/calibracion-alfa-2026-10-24"
CAMP = G / "campana-2026-10-26-deteccion-respuesta"
CFG = CAMP / "etapa4-preparacion-2026-11-02/config-campana-4c.json"
V2 = CAMP / "etapa4-4c-s50-v2-2026-11-10/evidencia/analisis-v2"
out = {}
def ok(nombre, cond, detalle=""):
    print(("OK    " if cond else "FALLO ") + nombre + (f"  [{detalle}]" if detalle else ""))
    out[nombre] = bool(cond)

cal = json.loads((CAL / "umbrales-alfa-precision-completa.json").read_text(encoding="utf-8"))
cfg = json.loads(CFG.read_text(encoding="utf-8"))["umbrales"]
sk = {k: float(v) for k, v in cal["umbrales_full_precision"]["validacion_sin_kali_65553"].items()}
og = {k: float(v) for k, v in cal["umbrales_full_precision"]["validacion_original_65633"].items()}
raw = (CAL / "umbrales-alfa-precision-completa.json").read_bytes()
sha_lf = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
ok("1 sha256 (LF) de umbrales-alfa-precision-completa.json = el registrado en la config", sha_lf == cfg["fuente"]["sha256_lf"], sha_lf[:16])
ok("2a config 0.05 == calibración sin Kali 0.050 (float exacto)", cfg["0.05"] == sk["0.050"], repr(cfg["0.05"]))
ok("2b config 0.03 == calibración sin Kali 0.030 (float exacto)", cfg["0.03"] == sk["0.030"], repr(cfg["0.03"]))
ok("2c config 0.01 == calibración sin Kali 0.010 (float exacto)", cfg["0.01"] == sk["0.010"], repr(cfg["0.01"]))
ok("2d desplegado_referencia == calibración original 65 633 al 0.050", cfg["desplegado_referencia"] == og["0.050"], repr(cfg["desplegado_referencia"]))
ok("3 orden u0.01 < u0.03 < u0.05", cfg["0.01"] < cfg["0.03"] < cfg["0.05"])

# 4) recálculo independiente desde las puntuaciones crudas
filas = []
with gzip.open(CAL / "datos-sensor/scores-validacion-65633.csv.gz", "rt", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f): filas.append((r["campaign_id"], r["entity_ip"], r["window_end_utc"], float(r["score_samples"])))
with open(CAL / "validacion-kali-80-excluidas.csv", encoding="utf-8", newline="") as f:
    excl = {(r["campaign_id"], r["entity_ip"], r["window_end_utc"]) for r in csv.DictReader(f)}
sin_kali = [s for c, e, w, s in filas if (c, e, w) not in excl]
ok("4a la validación original tiene 65 633 puntuaciones", len(filas) == 65633, str(len(filas)))
ok("4b las 80 excluidas están todas en ella y quedan 65 553", len(excl) == 80 and len(sin_kali) == 65553, f"excluidas={len(excl)} restantes={len(sin_kali)}")

def cuantil(xs, q):                   # numpy.quantile(method='linear'), con su _lerp
    xs = sorted(xs); n = len(xs); pos = (n - 1) * q; lo = math.floor(pos); hi = min(lo + 1, n - 1); t = pos - lo
    a, b = xs[lo], xs[hi]; d = b - a
    return b - d * (1 - t) if t >= 0.5 else a + d * t
try:
    import numpy as np
    cu = lambda xs, q: float(np.quantile(np.array(xs), q, method="linear")); motor = "numpy " + np.__version__
except Exception:
    cu = cuantil; motor = "implementación propia de numpy.quantile linear"
print("   (cuantiles con:", motor + ")")
for a, nombre in (("0.05", "0.050"), ("0.03", "0.030"), ("0.01", "0.010")):
    v = cu(sin_kali, float(a))
    ok(f"4c cuantil {a} de las 65 553 puntuaciones == umbral de la config", v == cfg[a], f"recalculado {v!r} | config {cfg[a]!r} | dif {abs(v-cfg[a]):.3e}")
v = cu([s for *_, s in filas], 0.05)
ok("4d cuantil 0.05 de las 65 633 == umbral desplegado", v == cfg["desplegado_referencia"], f"recalculado {v!r} | desplegado {cfg['desplegado_referencia']!r}")

# 5) lo que usó s50 v2 (salidas del análisis)
a3b = json.loads((V2 / "analisis-4c/analisis-3b.json").read_text(encoding="utf-8"))
um = a3b["umbrales"]
for k in ("IF_0.05", "IF_0.03", "IF_0.01"):
    ok(f"5 analisis-3b.json {k} == config", um[k] == cfg[k.split("_")[1]], repr(um[k]))
ok("5d analisis-3b.json desplegado == desplegado_referencia", um["desplegado"] == cfg["desplegado_referencia"])
print("   procedencia en analisis-3b.json:", um.get("procedencia"), "| orden_respetado:", um.get("orden_respetado"))
print("   fuentes del análisis:", json.dumps(a3b.get("fuentes"), ensure_ascii=False)[:900])
c4b = json.loads((V2 / "control-4b.json").read_text(encoding="utf-8"))
def buscar(o, ruta=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if "umbral" in k.lower() and not isinstance(v, (str, type(None))): print("   control-4b.json", ruta + "/" + k, "=", json.dumps(v)[:200])
            buscar(v, ruta + "/" + k)
buscar(c4b)
print("RESUMEN:", sum(out.values()), "OK de", len(out))
sys.exit(0 if all(out.values()) else 1)
