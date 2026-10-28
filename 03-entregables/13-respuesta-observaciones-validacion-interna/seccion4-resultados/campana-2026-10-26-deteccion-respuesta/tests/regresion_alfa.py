#!/usr/bin/env python3
"""No-regresión de α 0,05 y 0,03 al añadir α 0,01 (comprobación del CÓDIGO con fixtures, no resultado experimental).

Corre un analizador sobre las MISMAS entradas (tests/fixtures.py + evidencia de destino completa + integridad apta +
control + etiquetas) y proyecta solo lo que ya existía con 5 configuraciones (IF_0.05, IF_0.03, HEUR, HIB_0.05,
HIB_0.03, compartidas 0,05, control, métricas, umbrales). Los campos AÑADIDOS (IF_0.01, HIB_0.01, compartidas 0,01,
tiempo_es_emision_real, ...) se excluyen de la proyección: son aditivos y no pueden alterar lo anterior.

Golden: tests/golden-5config-fixtures.json, generado con el analizar.py ANTERIOR (último cambio en 2eb4577, vigente
hasta 0d40bdb):
  git show 0d40bdb:<carpeta>/scripts/analizar.py > /tmp/analizar_prev.py
  python3 tests/regresion_alfa.py --generar-golden --analizador /tmp/analizar_prev.py
Comparación directa (sin golden):  python3 tests/regresion_alfa.py --comparar /tmp/analizar_prev.py
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import fixtures  # noqa: E402

CONFIGS_PREVIAS = ("IF_0.05", "IF_0.03", "HEUR", "HIB_0.05", "HIB_0.03")
CLAVES_NUEVAS_REG = ("tiempo_es_emision_real",)
GOLDEN = AQUI / "golden-5config-fixtures.json"


def cargar_analizador(ruta: Path):
    spec = importlib.util.spec_from_file_location(f"an_{abs(hash(str(ruta)))}", ruta)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def correr(an) -> dict:
    """Mismas entradas para cualquier versión del analizador. Devuelve analisis.json."""
    import contextlib, io
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        with contextlib.redirect_stdout(io.StringIO()):
            fixtures.escribir(d)
        T = 1793000000
        marcas = [json.loads(x) for x in (d / "marcas.jsonl").read_text(encoding="utf-8").splitlines()]
        ini = {m["episodio_id"]: m for m in marcas if m["evento"] == "inicio"}
        fin = {m["episodio_id"]: m for m in marcas if m["evento"] == "fin"}
        filas, integ = ["episodio_id,window_end_utc,destino"], []
        for eid, m in ini.items():
            a = fixtures.datetime.fromisoformat(m["reloj"]["pared_utc"]).timestamp()
            b = fixtures.datetime.fromisoformat(fin[eid]["reloj"]["pared_utc"]).timestamp()
            filas += [f"{eid},{fixtures.iso(w)},{m['destino']}" for w in range(int(a) + 10, int(b) + 1, 10)]
            integ.append({"episodio_id": eid, "apto": True})
        (d / "dest.csv").write_text("\n".join(filas) + "\n", encoding="utf-8")
        (d / "integ.json").write_text(json.dumps({"episodios": integ}), encoding="utf-8")
        argv = ["x", "--marcas", str(d / "marcas.jsonl"), "--motor", str(d / "motor.log"),
                "--config", str(d / "cfg.json"), "--etiquetas", str(d / "etiquetas.csv"),
                "--destinos", str(d / "dest.csv"), "--integridad", str(d / "integ.json"),
                "--control", f"{T},{T + 4200}", "--salida", str(d / "out")]
        old = sys.argv; sys.argv = argv
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                an.main()
        finally:
            sys.argv = old
        return json.loads((d / "out" / "analisis.json").read_text(encoding="utf-8"))


def _reg(x):
    return {k: v for k, v in x.items() if k not in CLAVES_NUEVAS_REG} if isinstance(x, dict) else x


def proyeccion_5(j: dict) -> dict:
    """Solo lo que existía con 5 configuraciones (sin rutas temporales)."""
    eps = {}
    for eid, e in sorted(j["episodios"].items()):
        eps[eid] = {"evaluable": e["evaluable"], "motivo_no_evaluable": e["motivo_no_evaluable"],
                    "cobertura": e["cobertura"], "evidencia_destino": e["evidencia_destino"],
                    **{c: _reg(e[c]) for c in CONFIGS_PREVIAS},
                    "senales_previas_o_ambiguas": [_reg(s) for s in e["senales_previas_o_ambiguas"]
                                                   if s["configuracion"] in CONFIGS_PREVIAS],
                    "senales_observadas_sin_confirmar": [_reg(s) for s in e["senales_observadas_sin_confirmar"]
                                                         if s["configuracion"] in CONFIGS_PREVIAS],
                    "compartidas_durante_0.05": e["compartidas_durante_0.05"]}
    t8 = {f: {"evaluables": t["evaluables"], "no_evaluables": t["no_evaluables"],
              **{c: t[c] for c in CONFIGS_PREVIAS}} for f, t in sorted(j["tabla8"].items())}
    ctl = j["control_normal_fpr"]
    met = j["metricas_por_ventana"]
    return {"umbrales": {k: j["umbrales"][k] for k in ("0.05_recalibrado", "0.03_recalibrado",
                                                         "0.05_desplegado_en_vivo")},
            "tabla8": t8, "episodios": eps,
            "control_normal_fpr": {k: v for k, v in ctl.items() if k not in ("IF_0.01", "HIB_0.01")},
            "metricas_por_ventana": {k: v for k, v in met.items() if k not in ("IF_0.01", "HIB_0.01")},
            "calidad_datos": {k: v for k, v in j["calidad_datos"].items() if k != "aviso_orden_umbrales"}}


def diferencias(a, b, camino="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{camino}/{k}: solo en uno" for k in sorted(set(a) ^ set(b))]
        for k in sorted(set(a) & set(b)):
            out += diferencias(a[k], b[k], f"{camino}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{camino}: longitud {len(a)} != {len(b)}"]
        return [x for i, (p, q) in enumerate(zip(a, b)) for x in diferencias(p, q, f"{camino}[{i}]")]
    return [] if a == b else [f"{camino}: {a!r} != {b!r}"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--generar-golden", action="store_true")
    ap.add_argument("--analizador", help="analizador con el que generar el golden (el ANTERIOR)")
    ap.add_argument("--comparar", help="analizador anterior: compara su proyección con la del actual")
    a = ap.parse_args()
    actual = cargar_analizador(AQUI.parent / "scripts" / "analizar.py")
    if a.generar_golden:
        p = proyeccion_5(correr(cargar_analizador(Path(a.analizador))))
        GOLDEN.write_text(json.dumps(p, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8",
                          newline="\n")
        print(f"golden escrito: {GOLDEN.name}")
        return 0
    ref = (proyeccion_5(correr(cargar_analizador(Path(a.comparar)))) if a.comparar
           else json.loads(GOLDEN.read_text(encoding="utf-8")))
    dif = diferencias(ref, proyeccion_5(correr(actual)))
    print("\n".join(dif) if dif else "0 diferencias en IF_0.05/IF_0.03/HEUR/HIB_0.05/HIB_0.03")
    return 1 if dif else 0


if __name__ == "__main__":
    raise SystemExit(main())
