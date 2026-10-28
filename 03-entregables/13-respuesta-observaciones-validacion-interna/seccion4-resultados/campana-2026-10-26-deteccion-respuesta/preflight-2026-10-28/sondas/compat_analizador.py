"""Compatibilidad del analizador de HEAD con el motor_decision.log REAL (muestra reciente del sensor).
Comprueba: 7 configuraciones, umbrales de analisis y desplegado, lector corregido (threshold ausente/null),
separacion derivadas/emisiones, y que leer_motor() acepta la muestra real sin descartes."""
import hashlib, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
REPO = r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio"
C = "03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
muestra = Path(sys.argv[1])
src = subprocess.run(["git", "-C", REPO, "-c", "core.longpaths=true", "show", f"HEAD:{C}/scripts/analizar.py"],
                     stdout=subprocess.PIPE, check=True).stdout
cfg = json.loads(subprocess.run(["git", "-C", REPO, "-c", "core.longpaths=true", "show", f"HEAD:{C}/config-campana.json"],
                                stdout=subprocess.PIPE, check=True).stdout)
print("analizar.py HEAD sha256", hashlib.sha256(src).hexdigest())
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "analizar.py"; p.write_bytes(src)
    spec = importlib.util.spec_from_file_location("an", p); an = importlib.util.module_from_spec(spec); spec.loader.exec_module(an)
    print("CONFIGS", list(an.CONFIGS))
    U = an.umbrales_de(cfg)
    print("umbrales de analisis", {k: repr(v) for k, v in U.items()}, "| desplegado", repr(cfg["umbrales"]["desplegado_referencia"]))
    print("orden respetado", an.orden_umbrales(U))
    print("REQ_MOTOR", an.REQ_MOTOR, "| clave umbral", an.CLAVE_UMBRAL)
    print("estado umbral: ausente=%s null=%s num=%s" % (an.estado_umbral_registrado({}), an.estado_umbral_registrado({"threshold": None}),
                                                       an.estado_umbral_registrado({"threshold": -0.5693969936322356})))
    print("separacion: BASE_DERIVADA", an.BASE_DERIVADA["IF_0.05"], "| emisiones_observadas", callable(an.emisiones_observadas))
    regs, inc, dups = an.leer_motor(muestra)
    n = sum(1 for l in open(muestra, encoding="utf-8") if l.strip())
    print(f"muestra real: {n} lineas -> {len(regs)} registros leidos, {len(inc)} incidencias, {len(dups)} ventanas duplicadas")
    print("incidencias (max 5):", inc[:5])
    est = {}
    for r in regs:
        est[an.estado_umbral_registrado(r)] = est.get(an.estado_umbral_registrado(r), 0) + 1
    print("estado del umbral registrado:", est)
    alert = [r for r in regs if r.get("decision") == "ALERT"]
    print("ALERT en la muestra:", len(alert), "| emisor:", {an.emisor_de(r, cfg["modelo"]["detector"])[0] for r in alert})
    print("configuracion emisora de la primera ALERT:", an.configuracion_emisora(alert[0], "IF_desplegado", cfg["umbrales"]["desplegado_referencia"]) if alert else None)
    s = {c: 0 for c in an.CONFIGS}
    for r in regs:
        for c, v in an.senales(r, U).items():
            if c in s and v: s[c] += 1
    print("senales derivadas por configuracion en la muestra (no son emisiones):", s)
