#!/usr/bin/env python3
"""Genera RESULTADOS.md (tablas) a partir del resumen.json de analizar_p1.py. Sin dependencias."""
from __future__ import annotations

import json
import sys
from pathlib import Path

COND = ["control", "normal", "otros_ataques", "inundacion", "recuperacion", "estable_total", "calentamiento", "arranque"]
NOMBRE = {"control": "Control normal (08:01–08:35)", "normal": "Normal fuera de episodios",
          "otros_ataques": "Otros escenarios (escaneos, DNS, fuerza bruta)", "inundacion": "Inundación HTTP",
          "recuperacion": "Recuperación tras inundación (230 s)", "estable_total": "Todo el funcionamiento estable",
          "calentamiento": "Calentamiento (230 s tras arrancar o reiniciar)", "arranque": "Primer ciclo tras arrancar"}
ETAPAS_REF = ["pcap_parseo_s", "deduplicacion_s", "atribucion_s", "eve_observaciones_s", "filas_s", "puntuacion_s",
              "heuristicos_s", "cola_eve_lectura_s"]


def f(x, d=2):
    return "—" if x is None else (f"{x:.{d}f}".replace(".", ","))


def tabla_ciclo(t: dict) -> list[str]:
    L = ["| Condición | n | mediana (s) | p95 (s) | máx (s) | > 9,5 s | > 10 s |", "|---|---:|---:|---:|---:|---:|---:|"]
    for c in COND:
        v = t["por_condicion"].get(c)
        if v:
            L.append(f"| {NOMBRE[c]} | {v['n']} | {f(v['p50'])} | {f(v['p95'])} | {f(v['max'])} | {v['sobre_9_5']} | {v['sobre_10']} |")
    return L


def tabla_etapas(et: dict, etapas: list[str] | None = None) -> list[str]:
    conds = [c for c in COND if c in et]
    if etapas is None:
        etapas = sorted({k for c in conds for k in et[c]}, key=lambda k: (k == "ciclo_completo_motor", k))
    L = ["| Etapa | " + " | ".join(NOMBRE[c].split(" (")[0] for c in conds) + " |",
         "|---|" + "---:|" * len(conds)]
    for k in etapas:
        celdas = []
        for c in conds:
            v = et[c].get(k)
            celdas.append(f"{f(v['p50'])} / {f(v['p95'])} / {f(v['max'])}" if v else "—")
        L.append(f"| `{k}` | " + " | ".join(celdas) + " |")
    return L


def main() -> int:
    r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    L = ["# Paso 1 — resultados de las corridas offline (generado por tablas_p1.py)", "",
         "Tiempos medidos **offline** con el arnés de replay sobre la evidencia congelada de la campaña A, en el",
         "Sensor1 (4 núcleos, `nice -n 15`, con el motor desplegado en sombra activo). No son latencias de",
         "detección en vivo ni garantizan el funcionamiento en vivo: eso se mide en el paso 2.", ""]
    L += ["## 1. Equivalencia de registros", "",
          "| A (referencia) | B (candidato) | registros A / B | claves comunes | solo A | solo B | duplicados A / B | campos distintos | mismo orden | arranques A / B | equivalente |",
          "|---|---|---:|---:|---:|---:|---:|---|---|---|---|"]
    for c in r["comparaciones"]:
        L.append(f"| {c['a']} | {c['b']} | {c['registros_a']} / {c['registros_b']} | {c['comunes']} | {c['n_solo_a']} | "
                 f"{c['n_solo_b']} | {c['duplicados_a']} / {c['duplicados_b']} | {c['campos_distintos'] or 'ninguno'} | "
                 f"{'sí' if c['mismo_orden'] else 'no'} | {c['arranques'][0]} / {c['arranques'][1]} | "
                 f"**{'sí' if c['equivalente'] else 'NO'}** |")
    L += ["", "Campos excluidos de la comparación: " + ", ".join(f"`{x}`" for x in r["comparaciones"][0]["campos_excluidos"])
          + " (solo existe en el candidato desde 9b4cf2b). Todos los demás campos, `logged_at` incluido, se comparan.", ""]
    for c in r["comparaciones"]:
        L.append(f"- {c['b']}: decisiones {c['decisiones_b']}; ventanas no evaluadas {c['no_evaluadas_b'] or 0}; "
                 f"score nulo {c['score_none_b']}; con `pendiente_desde` {c['con_pendiente_desde_b']}; "
                 f"`decidido_en` > `logged_at`: {c['decidido_en_b']['posterior_a_logged_at']} de {c['decidido_en_b']['registros']}.")
    L += ["", "## 2. Verificación etapa por etapa (`--verificar-equivalencia`)", "",
          "| Corrida | ciclos verificados | ciclos con alguna diferencia | fallos por comprobación | filas necesarias | filas candidatas | filas puntuadas en lote |",
          "|---|---:|---:|---|---:|---:|---:|"]
    for d, v in r["verificacion"].items():
        L.append(f"| {d} | {v['ciclos']} | {v['no_ok']} | {v['fallos_por_comprobacion'] or 'ninguno'} | "
                 f"{v['filas_necesarias']} | {v['filas_candidatas']} | {v['puntuadas']} |")
    L += ["", "Cada ciclo recalcula por la vía global de 7b275b8 y compara: deduplicación (mismos objetos y orden),",
          "atribución, observaciones EVE, filas (valores de las 28 características incluidos), cobertura de las",
          "ventanas que el original habría decidido y puntuación en lote frente a una llamada por fila (bit a bit).", ""]
    L += ["## 3. Duración del ciclo completo por condición", ""]
    for d, nombre in (("r1-ref-perfil", "Referencia 7b275b8 (R1, con perfil por función)"),
                      ("r3-cand", "Candidato sin verificación (R3)")):
        if d in r["tiempos"]:
            L += [f"### {nombre}", "", *tabla_ciclo(r["tiempos"][d]), ""]
    L += ["Duración = tiempo real entre el inicio del ciclo y su `sleep`, medido por el arnés. Presupuesto: paso de 10 s",
          "(se informa también > 9,5 s). Condición asignada por la hora simulada del ciclo con las marcas de la campaña;",
          "inundación = [inicio, fin + 30 s) de cada `inundacion_http`, recuperación = los 230 s siguientes.", ""]
    L += ["## 4. Etapas (mediana / p95 / máx, en s)", ""]
    if "r1-ref-perfil" in r["tiempos"]:
        L += ["### Referencia (R1): funciones envueltas por el arnés", "",
              *tabla_etapas(r["tiempos"]["r1-ref-perfil"]["etapas_arnes"]), ""]
    if "r3-cand" in r["tiempos"]:
        L += ["### Candidato (R3): etapas que registra el propio motor en `ciclos.jsonl`", "",
              *tabla_etapas(r["tiempos"]["r3-cand"]["etapas_motor"]), ""]
        L += ["### Candidato (R3): contadores máximos por condición", "", "```json",
              json.dumps(r["tiempos"]["r3-cand"]["contadores_motor_max"], indent=1, ensure_ascii=False), "```", ""]
        lentos = r["tiempos"]["r3-cand"]["lentos"]
        L += ["### Candidato (R3): ciclos > 9,5 s", ""]
        L += ([f"- {x['hora']} UTC: {f(x['dur_s'])} s" for x in lentos] if lentos else ["Ninguno."]) + [""]
    for d, nombre in (("r4-ref-reinicio", "Reinicio a las 09:05 — referencia (R4, concurrente con R2: solo orientativo)"),
                      ("r4-cand-reinicio-9b4cf2b", "Reinicio a las 09:05 — candidato 9b4cf2b con verificación (fase C, incluye el recálculo global)"),
                      ("r5-cand-reinicio-tiempos", "Reinicio a las 09:05 — candidato 9b4cf2b solo, sin verificación (R5)")):
        if d in r["tiempos"]:
            L += [f"### {nombre}", "", *tabla_ciclo(r["tiempos"][d]), ""]
    if "r5-cand-reinicio-tiempos" in r["tiempos"]:
        L += ["### R5: etapas del candidato tras el reinicio", "",
              *tabla_etapas(r["tiempos"]["r5-cand-reinicio-tiempos"]["etapas_motor"]), ""]
        lentos = r["tiempos"]["r5-cand-reinicio-tiempos"]["lentos"]
        L += ["R5, ciclos > 9,5 s: " + (", ".join(f"{x['hora']} ({f(x['dur_s'])} s)" for x in lentos) or "ninguno") + ".", ""]
    sys.stdout.write("\n".join(L) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
