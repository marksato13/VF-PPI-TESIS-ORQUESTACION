#!/usr/bin/env python3
"""Genera resultados/TABLAS-E2E.md a partir de resultados/presupuesto-e2e.json (solo lee el JSON)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent


def r(x):
    return "—" if x is None else ("%.1f" % x).replace(".", ",")


def rng(v):
    return "—" if not v else "%s–%s" % (r(v[0]), r(v[1]))


CLASE = {"antes_del_fin": "antes", "despues_del_fin": "**después**", "indeterminado": "indet."}


def main() -> int:
    d = json.loads((AQUI / "resultados" / "presupuesto-e2e.json").read_text(encoding="utf-8"))
    o = ["# Tablas del presupuesto temporal (generadas por herramientas/tablas_e2e.py)", "",
         "Fuente: `resultados/presupuesto-e2e.json`. Tiempos en segundos desde `t_inicio` del episodio. "
         "t_det = disponibilidad del registro (medido). t_apl = **estimado** (en sombra el agente no aplicó). "
         "Intervalo inf–sup por la fase del publicador y el arranque del agente (AccuracySec=1s). "
         "P = episodio en la población principal v2.", ""]
    o += ["## 1. Primera señal atribuible con veredicto (cualquier acción) y primer BLOCK", "",
          "| Episodio | P | Dur. obs. | Acción · motivo | t_det | V0 t_apl | V0 margen | V0 | V1 | V2 t_apl | V2 | 1.er BLOCK V0 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in sorted(d["episodios"], key=lambda e: e["episodio"]):
        p, b = e["primera_cualquiera"], e["primera_BLOCK"]
        if not p:
            o.append("| %s | %s | %s | sin señal atribuible | | | | | | | | |"
                     % (e["episodio"], "P" if e["en_poblacion_principal_v2"] else "", r(e["duracion_observada_s"])))
            continue
        bt = "—" if not b else "%s (%s)" % (rng(b["V0"]["t_apl_menos_inicio_s"]), CLASE[b["V0"]["clase"]])
        o.append("| %s | %s | %s | %s · %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            e["episodio"], "P" if e["en_poblacion_principal_v2"] else "", r(e["duracion_observada_s"]),
            p["accion"], p["motivo"].split(":")[0] if not p["motivo"].startswith("modelo") else "modelo IF",
            r(p["t_det_menos_inicio_s"]), rng(p["V0"]["t_apl_menos_inicio_s"]), rng(p["V0"]["margen_s"]),
            CLASE[p["V0"]["clase"]], CLASE[p["V1"]["clase"]], rng(p["V2"]["t_apl_menos_inicio_s"]),
            CLASE[p["V2"]["clase"]], bt))
    o += ["", "## 2. Resumen por escenario (distribución de valores por episodio; no se suman medianas)", "",
          "| Escenario | n (P) | Dur. obs. mediana | t_det mín/med/máx | V0 t_apl sup mín/med/máx | V0 antes/indet/después | V1 | V2 | Ventana con señal cierra antes del fin |",
          "|---|---|---|---|---|---|---|---|---|"]
    for esc, x in d["resumen_por_escenario"].items():
        c = x["cualquiera"]
        f = lambda k: "%d/%d/%d" % (c[k]["antes_del_fin"], c[k]["indeterminado"], c[k]["despues_del_fin"])  # noqa
        td, ta = c["t_det_menos_inicio_s"], c["V0_t_apl_menos_inicio_sup_s"]
        o.append("| %s | %d (%d) | %s | %s/%s/%s | %s/%s/%s | %s | %s | %s | %d/%d |" % (
            esc, x["episodios"], x["en_poblacion_v2"], r(x["duracion_observada_s"]["mediana"]),
            r(td["min"]), r(td["mediana"]), r(td["max"]), r(ta["min"]), r(ta["mediana"]), r(ta["max"]),
            f("V0_clases"), f("V1_clases"), f("V2_clases"), c["ventana_cierra_antes_del_fin"],
            c["con_senal_atribuible"]))
    o += ["", "## 3. Simulación secuencial: restricción ya vigente al empezar cada episodio", "",
          "| Episodio | BLOCK vigente al inicio | Restante (s) | Nivel de escalada previo |", "|---|---|---|---|"]
    for x in d["secuencial"]["estado_al_inicio_de_cada_episodio"]:
        o.append("| %s | %s | %s | %d |" % (x["episodio"], "sí" if x["block_vigente_al_inicio"] else "no",
                                            r(x["block_restante_s"]), x["nivel_escalada_previo"]))
    o += ["", "## 4. Control normal (33 min): señales y restricciones que se habrían aplicado", "",
          "| Configuración | Umbral IF | Ventanas con veredicto / %d | Señales por componente | Entidades restringidas / en control | Incidentes (por hora) | Entidades restringidas > 50 %% del control |"
          % d["control"]["ventanas_decididas"], "|---|---|---|---|---|---|---|"]
    for k in ("desplegado", "IF_0.05", "IF_0.03", "IF_0.01"):
        c = d["control"][k]
        comp = ", ".join("%s %d" % (t, n) for t, n in c["senales_ventanas"].items() if t != "ventanas_con_veredicto")
        mitad = [ip for ip, v in c["restricciones_por_entidad"].items() if v["fraccion_control_restringida"] > 0.5]
        o.append("| %s | %.4f | %d (%s %%) | %s | %d / %d | %d (%s) | %s |" % (
            k, c["umbral"], c["senales_ventanas"]["ventanas_con_veredicto"],
            r(100 * c["tasa_ventanas_con_veredicto"]), comp, len(c["entidades_restringidas"]),
            c["entidades_en_control"], c["incidentes_total"], r(c["incidentes_por_hora"]),
            ", ".join(sorted(mitad)) or "—"))
    o += ["", "Detalle por entidad (desplegado): fracción del control con restricción aplicada.", "",
          "| Entidad | Incidentes | Segundos | Fracción | BLOCK |", "|---|---|---|---|---|"]
    for ip, v in sorted(d["control"]["desplegado"]["restricciones_por_entidad"].items()):
        o.append("| %s | %d | %s | %s | %d |" % (ip, v["incidentes_restriccion"], r(v["segundos_restringida"]),
                                                 r(v["fraccion_control_restringida"]), v["BLOCK"]))
    (AQUI / "resultados" / "TABLAS-E2E.md").write_text("\n".join(o) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(o[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
