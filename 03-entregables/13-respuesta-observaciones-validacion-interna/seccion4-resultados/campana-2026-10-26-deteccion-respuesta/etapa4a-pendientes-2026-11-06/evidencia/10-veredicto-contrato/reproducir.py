"""Reproduce los tres fallos de `evaluar_ecarga.py veredicto` (fichero indicado en argv[1]). Solo lectura, offline."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile

spec = importlib.util.spec_from_file_location("ev", sys.argv[1])
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
print("evaluar_ecarga VERSION", ev.VERSION)


def base(clase="C1", dpm=3.2, descartes=2, paquetes=625000):
    return {"K": {k: True for k in ev.K}, "S": {s: True for s in ev.S},
            "clasificacion": {"clase_periodo": clase, "motivos": ["Suricata (EVE): x"] if clase != "C0" else []},
            "suricata": {"estado": "descartes" if descartes else "cero_explicito", "paquetes": paquetes,
                         "descartes": descartes},
            "descartes_por_millon": dpm}


casos = {}
c = base(); c["K"]["K1"] = "false"; c["S"]["S1"] = "false"
casos["1. K1 y S1 como texto \"false\""] = c
c = base("no_evaluable", None, None, None); c["suricata"] = {"estado": "ausente", "paquetes": None, "descartes": None}
casos["2. clase no_evaluable con S verdaderos"] = c
casos["3. C1, 100 descartes/M y S13 verdadero"] = base("C1", 100.0, 100, 1_000_000)

fallos = 0
for nombre, d in casos.items():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(d, f)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ev.main(["veredicto", "--entrada", f.name])
    try:
        r = json.loads(out.getvalue())
    except ValueError:
        r = {"salida_no_json": out.getvalue()}
    habilita = rc == 0 or str(r.get("habilita", "")).startswith("condición (3)")
    fallos += habilita
    print(f"{nombre}: rc={rc} estabilidad={r.get('estabilidad_tecnica')!r} error={r.get('error')!r} "
          f"habilita={'SÍ (DEFECTO)' if habilita else 'no'}")
print("casos que habilitan el avance:", fallos, "de", len(casos))
