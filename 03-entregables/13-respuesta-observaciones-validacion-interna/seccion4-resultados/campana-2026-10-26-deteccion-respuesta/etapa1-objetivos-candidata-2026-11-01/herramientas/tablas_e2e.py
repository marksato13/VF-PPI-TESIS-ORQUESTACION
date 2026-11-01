#!/usr/bin/env python3
"""Genera resultados/TABLAS-E2E.md a partir de resultados/presupuesto-e2e.json (v2; solo lee el JSON)."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
CL = {"antes_del_fin_bajo_supuestos": "antes*", "despues_del_fin_bajo_supuestos": "**después***",
      "indeterminado": "indet.", "deteccion_posterior": "**det. posterior**"}


def r(x):
    return "—" if x is None else ("%.1f" % x).replace(".", ",")


def t(s):
    return datetime.fromisoformat(s).timestamp()


def main() -> int:
    d = json.loads((AQUI / "resultados" / "presupuesto-e2e.json").read_text(encoding="utf-8"))
    meta = {m["episodio"]: m for m in d["episodios_meta"]}
    act = d["politicas"]["actual|desplegado"]
    o = ["# Tablas del presupuesto temporal (v2; generadas por herramientas/tablas_e2e.py)", "",
         "> **Simulación sobre registros de sombra del 3B.** No es una campaña de respuesta: no modela cómo una "
         "restricción habría cambiado el ataque ni las decisiones posteriores. `t_apl_estimada` es una estimación "
         "bajo supuestos (escenarios *favorable* = p50/mínimos medidos con offsets desconocidos supuestos 0; *alto* "
         "= máximos históricos + cotas configuradas). **No son intervalos de confianza ni límites garantizados.** "
         "t_apl real y t_efecto: no aplica. «*» = bajo supuestos; además deben caber las demoras desconocidas "
         "(activación nft, efecto). «det. posterior» = t_det MEDIDO después del fin: no depende de supuestos.", "",
         "Poblaciones: campaña 3B = 25 episodios ejecutados; revisión 3B = 15 admitidos (columna A). La "
         "simulación se calcula para los 25 y cada fila indica si el episodio está admitido.", "",
         "## 1. Por episodio, política actual (IF → LIMIT) con el umbral desplegado", "",
         "| Episodio | A | Fin eval. (s) | Fuente del fin | Primera acción · origen | t_det | V0 t_apl est. fav.–alto | Margen (alto) | V0 | V1 | V2 t_det | V2 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in sorted(act["episodios"], key=lambda e: e["episodio"]):
        m, p = meta[e["episodio"]], e["primera_cualquiera"]
        fin = t(m["t_fin_eval_utc"]) - t(m["t_inicio_utc"])
        fuente = "observado" if m["t_fin_eval_utc"] == m["t_fin_observado_utc"] else "referencia"
        if not p:
            o.append("| %s | %s | %s | %s | sin señal atribuible | | | | | | | |"
                     % (e["episodio"], "sí" if m["admitido_v2"] else "no", r(fin), fuente))
            continue
        mot = "modelo IF" if p["motivo"].startswith("modelo") else p["motivo"].split(":")[0]
        a = p["V0"]["t_apl_estimada_menos_inicio_s"]
        o.append("| %s | %s | %s | %s | %s · %s | %s | %s–%s | %s | %s | %s | %s | %s |" % (
            e["episodio"], "sí" if m["admitido_v2"] else "no", r(fin), fuente, p["accion"], mot,
            r(p["t_det_menos_inicio_s"]), r(a["favorable"]), r(a["alto"]), r(p["V0"]["margen_s"]["alto"]),
            CL[p["V0"]["clase"]], CL[p["V1"]["clase"]], r(p["V2"]["t_det_menos_inicio_s"]), CL[p["V2"]["clase"]]))
    o += ["", "### 1b. Primera señal de la REGLA PREVISTA (dns_entropy / http_abuse / port_scan / brute_force)", "",
          "Una señal de otra regla (p. ej. brute_force durante un escaneo) no valida la regla prevista.", "",
          "| Episodio | A | Regla prevista: acción · t_det | V0 | Primera señal de cualquier regla | ¿Coinciden? |",
          "|---|---|---|---|---|---|"]
    for e in sorted(act["episodios"], key=lambda e: e["episodio"]):
        m, pv, pc = meta[e["episodio"]], e["primera_prevista"], e["primera_cualquiera"]
        cual = "—" if not pc else ("modelo IF" if pc["motivo"].startswith("modelo") else pc["motivo"].split(":")[0])
        o.append("| %s | %s | %s | %s | %s (%s) | %s |" % (
            e["episodio"], "sí" if m["admitido_v2"] else "no",
            "sin señal" if not pv else "%s · %s" % (pv["accion"], r(pv["t_det_menos_inicio_s"])),
            "—" if not pv else CL[pv["V0"]["clase"]], cual, "—" if not pc else r(pc["t_det_menos_inicio_s"]),
            "—" if not (pv and pc) else ("sí" if pv["t_det_utc"] == pc["t_det_utc"] else "no")))
    o += ["", "## 2. Resumen por escenario (política actual; distribuciones de valores POR EPISODIO)", "",
          "| Escenario | Ejecutados (admitidos) | Detección disponible antes del fin | t_det mín/med/máx | V0 t_apl est. alto mín/med/máx | V0 antes*/indet./después*/det. post. | V1 | V2 |",
          "|---|---|---|---|---|---|---|---|"]
    f4 = lambda c: "%d/%d/%d/%d" % tuple(c[k] for k in ("antes_del_fin_bajo_supuestos", "indeterminado", "despues_del_fin_bajo_supuestos", "deteccion_posterior"))  # noqa: E731
    for esc, x in act["resumen_por_escenario"].items():
        c = x["cualquiera"]
        td, ta = c["t_det_menos_inicio_s"], c["V0_t_apl_estimada_alto_menos_inicio_s"]
        o.append("| %s | %d (%d) | %d/%d | %s/%s/%s | %s/%s/%s | %s | %s | %s |" % (
            esc, x["episodios"], x["admitidos_v2"], c["deteccion_disponible_antes_del_fin"], x["episodios"],
            r(td["min"]), r(td["mediana"]), r(td["max"]), r(ta["min"]), r(ta["mediana"]), r(ta["max"]),
            f4(c["V0_clases"]), f4(c["V1_clases"]), f4(c["V2_clases"])))
    o += ["", "## 3. Políticas para D3 (acción del IF) × umbral: episodios y control normal (33 min)", "",
          "Restricciones **hipotéticas** (simuladas sobre el control de sombra; ninguna se aplicó). "
          "Entidades = direcciones IP del control; ventanas = registros entidad×window_end; intervalos = "
          "restricciones fusionadas por entidad; renovaciones = ampliaciones del mismo intervalo.", "",
          "| Política · umbral | Ventanas con veredicto (%) | Incidentes de señal (sin NUNCA) | Entidades con restricción hipotética | Intervalos | Renovaciones | Entidades > 50 % del control | BLOCK | V0 antes* por familia (dns/breve/sost./fb/inund.) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, v in d["politicas"].items():
        c, rs = v["control"], v["resumen_por_escenario"]
        mitad = [ip for ip, x in c["restricciones_hipoteticas_por_entidad"].items()
                 if x["fraccion_control_restringida_hipotetica"] > 0.5]
        fam = "/".join(str(rs[f]["cualquiera"]["V0_clases"]["antes_del_fin_bajo_supuestos"]) for f in
                       ("dns_inusual", "escaneo_breve", "escaneo_sostenido", "fuerza_bruta_http", "inundacion_http"))
        o.append("| %s | %d (%s %%) | %d | %d | %d | %d | %d | %d | %s |" % (
            k.replace("|", " · "), c["ventanas_con_veredicto"], r(100 * c["tasa_ventanas_con_veredicto"]),
            c["incidentes_senal_sin_nunca_bloquear"], len(c["entidades_con_restriccion_hipotetica"]),
            c["intervalos_restriccion_total"], c["renovaciones_total"], len(mitad), c["block_a_entidades"], fam))
    o += ["", "Detalle por entidad (restricción hipotética; fracción del control):", ""]
    for k in ("actual|desplegado", "actual|IF_0.01", "persist_3|desplegado", "if_senal|desplegado"):
        c = d["politicas"][k]["control"]["restricciones_hipoteticas_por_entidad"]
        o.append("- **%s**: %s" % (k.replace("|", " · "), "; ".join(
            "%s %s (%d int., %d renov.)" % (ip, r(100 * x["fraccion_control_restringida_hipotetica"]) + " %",
                                            x["intervalos_restriccion"], x["renovaciones"])
            for ip, x in sorted(c.items())) or "ninguna"))
    o += ["", "## 4. Simulación secuencial (política actual): restricción hipotética vigente al empezar", "",
          "> Riesgo bajo supuestos: con bloqueo real, los ataques y decisiones posteriores habrían sido otros.", "",
          "| Episodio | BLOCK hipotético vigente | Restante (s) | Nivel de escalada previo |", "|---|---|---|---|"]
    for x in d["secuencial"]["estado_al_inicio_de_cada_episodio"]:
        o.append("| %s | %s | %s | %d |" % (x["episodio"], "sí" if x["block_hipotetico_vigente_al_inicio"] else "no",
                                            r(x["block_restante_s"]), x["nivel_escalada_previo"]))
    (AQUI / "resultados" / "TABLAS-E2E.md").write_text("\n".join(o) + "\n", encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(o[8:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
