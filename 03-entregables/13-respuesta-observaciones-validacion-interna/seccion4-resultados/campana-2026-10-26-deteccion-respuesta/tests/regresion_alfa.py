#!/usr/bin/env python3
"""No-regresión de DETECCIÓN y COBERTURA del analizador (comprobación del CÓDIGO con fixtures, no resultado
experimental).

Corre un analizador sobre las MISMAS entradas (tests/fixtures.py + evidencia de destino completa + integridad apta +
control + etiquetas) y proyecta lo que no debe cambiar: evaluable, cobertura, evidencia de destino, categoría,
primera señal (ventana, logged_at, tiempos, score, atribución) por configuración, señales previas/observadas,
solapamiento, Tabla 8, control FPR, métricas por ventana y calidad de datos.

Exclusiones EXPLÍCITAS (lo único que la corrección de procedencia de 2026-10-28.2 debe cambiar):
  - base                   etiqueta de procedencia; antes IF_0.05 podía decir 'emitido_por_modelo_desplegado' y HEUR
                           'emitido_ALERT(auth_heredada)'/'registrada_en_vivo'; ahora todas son 'derivado(...)'
  - tiempo_es_emision_real campo de a6dc5ab, retirado (afirmaba emisión real para IF_0.05 recalibrado)
  - tiempo_significado     campo nuevo: disponibilidad del registro, no latencia de emisión
  - evidencia_registrada   campo nuevo: lo que el registro muestra (decisión/detector/heurístico)
  - emisiones_observadas   bloque nuevo, aparte de las configuraciones
Con --comparar se listan además, separadas, las diferencias en esas claves, para que no queden ocultas.

Exclusiones EXPLÍCITAS de #59 (ventana_no_evaluada, 2026-10-28; CLAVES_NO_EVALUADAS): solo claves NUEVAS de
cobertura en control_normal_fpr, metricas_por_ventana y calidad_datos. Las claves existentes (ventanas, denominador,
conteos, tasas) se siguen comparando. test_herramientas.py comprueba aparte que, sin eventos, las nuevas son neutras
(0 no evaluadas, cobertura 1,0) y que episodios/cobertura no cambian.

Goldens (generados con analizadores ANTERIORES, sobre estas mismas entradas):
  tests/golden-5config-fixtures.json  analizar.py de 0d40bdb (5 configuraciones)
  tests/golden-7config-fixtures.json  analizar.py de a6dc5ab (7 configuraciones, antes de corregir la procedencia)
  git show <commit>:<carpeta>/scripts/analizar.py > /tmp/analizar_prev.py
  python3 tests/regresion_alfa.py --generar-golden 7 --analizador /tmp/analizar_prev.py
Comparación directa:  python3 tests/regresion_alfa.py --comparar /tmp/analizar_prev.py [--configs 5|7]
"""
from __future__ import annotations
import argparse, contextlib, importlib.util, io, json, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import fixtures  # noqa: E402

CONFIGS = {5: ("IF_0.05", "IF_0.03", "HEUR", "HIB_0.05", "HIB_0.03"),
           7: ("IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01")}
COMPARTIDAS = {5: ("0.05",), 7: ("0.05", "0.01")}
CLAVES_PROCEDENCIA = ("base", "tiempo_es_emision_real", "tiempo_significado", "evidencia_registrada")
CLAVES_NO_EVALUADAS = ("ventanas_no_evaluadas", "ventanas_no_evaluadas_por_motivo", "ventanas_no_evaluadas_criterio",
                       "cobertura_evaluada", "denominador_significado", "etiquetadas_no_evaluadas",
                       "etiquetadas_sin_registro", "cobertura_etiquetadas")
GOLDEN = {5: AQUI / "golden-5config-fixtures.json", 7: AQUI / "golden-7config-fixtures.json"}


def cargar_analizador(ruta: Path):
    spec = importlib.util.spec_from_file_location(f"an_{abs(hash(str(ruta)))}", ruta)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def correr(an) -> dict:
    """Mismas entradas para cualquier versión del analizador. Devuelve analisis.json."""
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


def sin_procedencia(x):
    """Quita, a cualquier profundidad, las claves de procedencia/etiquetado temporal (exclusiones documentadas)."""
    if isinstance(x, dict):
        return {k: sin_procedencia(v) for k, v in x.items() if k not in CLAVES_PROCEDENCIA}
    if isinstance(x, list):
        return [sin_procedencia(v) for v in x]
    return x


def proyeccion(j: dict, n: int) -> dict:
    """Detección y cobertura de las n configuraciones (sin rutas temporales ni claves de procedencia)."""
    C = CONFIGS[n]
    eps = {}
    for eid, e in sorted(j["episodios"].items()):
        eps[eid] = {"evaluable": e["evaluable"], "motivo_no_evaluable": e["motivo_no_evaluable"],
                    "cobertura": e["cobertura"], "evidencia_destino": e["evidencia_destino"],
                    **{c: e[c] for c in C},
                    "senales_previas_o_ambiguas": [s for s in e["senales_previas_o_ambiguas"]
                                                   if s["configuracion"] in C],
                    "senales_observadas_sin_confirmar": [s for s in e["senales_observadas_sin_confirmar"]
                                                         if s["configuracion"] in C],
                    **{f"compartidas_durante_{a}": e[f"compartidas_durante_{a}"] for a in COMPARTIDAS[n]}}
    t8 = {f: {"evaluables": t["evaluables"], "no_evaluables": t["no_evaluables"], **{c: t[c] for c in C}}
          for f, t in sorted(j["tabla8"].items())}
    ctl, met = j["control_normal_fpr"], j["metricas_por_ventana"]
    otras = [c for c in CONFIGS[7] if c not in C]
    return sin_procedencia({
        "umbrales": {k: j["umbrales"][k] for k in ("0.05_recalibrado", "0.03_recalibrado", "0.05_desplegado_en_vivo")
                     + (("0.01_recalibrado",) if n == 7 else ())},
        "tabla8": t8, "episodios": eps,
        "control_normal_fpr": {k: v for k, v in ctl.items() if k not in otras and k not in CLAVES_NO_EVALUADAS},
        "metricas_por_ventana": {k: v for k, v in met.items() if k not in otras and k not in CLAVES_NO_EVALUADAS},
        "calidad_datos": {k: v for k, v in j["calidad_datos"].items()
                          if k != "aviso_orden_umbrales" and k not in CLAVES_NO_EVALUADAS}})


def procedencia(j: dict) -> dict:
    """Solo las claves excluidas, por episodio y configuración (para mostrarlas aparte)."""
    return {eid: {c: {k: e[c].get(k) for k in CLAVES_PROCEDENCIA if k in e[c]}
                  for c in CONFIGS[7] if isinstance(e.get(c), dict)}
            for eid, e in sorted(j["episodios"].items())}


def diferencias(a, b, camino="") -> list:
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
    ap.add_argument("--generar-golden", type=int, choices=(5, 7))
    ap.add_argument("--analizador", help="analizador ANTERIOR con el que generar el golden")
    ap.add_argument("--comparar", help="analizador anterior: compara directamente con el actual")
    ap.add_argument("--configs", type=int, choices=(5, 7), default=7)
    a = ap.parse_args()
    actual = cargar_analizador(AQUI.parent / "scripts" / "analizar.py")
    if a.generar_golden:
        n = a.generar_golden
        p = proyeccion(correr(cargar_analizador(Path(a.analizador))), n)
        GOLDEN[n].write_text(json.dumps(p, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8",
                             newline="\n")
        print(f"golden escrito: {GOLDEN[n].name}")
        return 0
    n = a.configs
    j_act = correr(actual)
    if a.comparar:
        j_prev = correr(cargar_analizador(Path(a.comparar)))
        ref = proyeccion(j_prev, n)
        dp = diferencias(procedencia(j_prev), procedencia(j_act))
        print(f"diferencias EXCLUIDAS (procedencia/etiquetado temporal): {len(dp)}")
        for x in dp:
            print("  [excluida] " + x)
    else:
        ref = sin_procedencia(json.loads(GOLDEN[n].read_text(encoding="utf-8")))
    dif = diferencias(ref, proyeccion(j_act, n))
    print("\n".join(dif) if dif else f"0 diferencias de detección/cobertura en {n} configuraciones")
    return 1 if dif else 0


if __name__ == "__main__":
    raise SystemExit(main())
