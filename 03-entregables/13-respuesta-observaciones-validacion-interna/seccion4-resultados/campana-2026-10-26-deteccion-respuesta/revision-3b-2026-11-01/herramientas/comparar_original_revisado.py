#!/usr/bin/env python3
"""Compara el análisis 3B ORIGINAL con el REVISADO (revisión posterior a los resultados) y produce las tablas.

Solo lee. Entradas: los dos analisis-3b.json, el motor en vivo (para el solapamiento IF/HEUR en el control),
la configuración (umbrales congelados) y los respaldos de captura/calidad (dos criterios de Suricata).
Salidas en --salida: comparacion.json y TABLAS-REVISION.md.
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent.parent / "scripts"))
import analizar as an  # noqa: E402
import poblacion  # noqa: E402

CONFIGS = an.CONFIGS
CATS = ("oportuna", "solo_posterior", "ausencia_con_observacion_suficiente", "no_evaluable")
ABR = {"oportuna": "OP", "solo_posterior": "SP", "ausencia_con_observacion_suficiente": "AU", "no_evaluable": "NE"}


def tabla8(a: dict) -> dict:
    t = defaultdict(lambda: {"episodios": 0, **{c: Counter() for c in CONFIGS}, "emisiones_oportunas": 0})
    for eid, c in a["episodios"].items():
        if not c["en_poblacion_principal"]:
            continue
        f = t[an.familia(eid.rsplit("-r", 1)[0])]
        f["episodios"] += 1
        for cf in CONFIGS:
            f[cf][c[cf]["categoria"]] += 1
        f["emisiones_oportunas"] += int(c["emisiones_reales"]["oportunas"] > 0)
    return {k: {**v, **{cf: dict(v[cf]) for cf in CONFIGS}} for k, v in sorted(t.items())}


def control_solapamiento(motor: Path, cfg: dict, desde: float, hasta: float) -> dict:
    """Ventanas del control con señal IF, HEUR, ambas: qué añade el heurístico a las falsas alarmas del IF."""
    U = an.umbrales_de(cfg)
    pob = poblacion.cargar_poblacion(cfg)
    regs, _, _ = an.leer_motor(motor)
    v = [r for r in regs if desde <= r["_wend"] <= hasta and not poblacion.excluida(r["entity_ip"], pob)]
    out = {"ventanas_decididas": len(v)}
    for al in an.ALFAS:
        s = [an.senales(r, U) for r in v]
        i = sum(1 for g in s if g[f"IF_{al}"]); h = sum(1 for g in s if g["HEUR"])
        both = sum(1 for g in s if g[f"IF_{al}"] and g["HEUR"]); hib = sum(1 for g in s if g[f"HIB_{al}"])
        out[al] = {"IF": i, "HEUR": h, "IF_y_HEUR": both, "HEUR_sin_IF": h - both, "HIB": hib,
                   "comprobacion_HIB_igual_IF_mas_HEUR_sin_IF": hib == i + h - both}
    tipos = Counter((r.get("heuristico") or {}).get("heuristico") for r in v if r.get("heuristico"))
    out["HEUR_por_tipo"] = dict(tipos)
    out["HEUR_por_entidad"] = dict(Counter(r["entity_ip"] for r in v if an.senales(r, U)["HEUR"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", required=True, type=Path)
    ap.add_argument("--revisado", required=True, type=Path)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--calidad", required=True, type=Path)
    ap.add_argument("--respaldos-v2", required=True, type=Path)
    ap.add_argument("--integridad-original", required=True, type=Path)
    ap.add_argument("--integridad-v2", required=True, type=Path)
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args()
    O = json.load(open(a.original, encoding="utf-8")); R = json.load(open(a.revisado, encoding="utf-8"))
    cfg = json.load(open(a.config, encoding="utf-8"))
    cal = json.load(open(a.calidad, encoding="utf-8"))["episodios"]
    io = {e["episodio_id"]: e for e in json.load(open(a.integridad_original, encoding="utf-8"))["episodios"]}
    i2 = {e["episodio_id"]: e for e in json.load(open(a.integridad_v2, encoding="utf-8"))["episodios"]}

    eps = []
    for eid in O["episodios"]:
        o, r = O["episodios"][eid], R["episodios"][eid]
        cap = json.load(open(a.respaldos_v2 / eid / "captura.json", encoding="utf-8"))
        cambios = {cf: [o[cf]["categoria"], r[cf]["categoria"]] for cf in CONFIGS if o[cf]["categoria"] != r[cf]["categoria"]}
        mismas = all(o[cf].get("primera") == r[cf].get("primera") and o[cf]["senales_atribuibles"] == r[cf]["senales_atribuibles"]
                     for cf in CONFIGS) and o["emisiones_reales"] == r["emisiones_reales"]
        eps.append({
            "episodio": eid,
            "principal_original": o["en_poblacion_principal"], "principal_revisado": r["en_poblacion_principal"],
            "integridad_original_ausentes": io[eid]["resumen"]["ausente"],
            "integridad_v2_ausentes": i2[eid]["resumen"]["ausente"],
            "motivos_revisado": r["observacion"]["motivos"],
            "categorias_original": {cf: o[cf]["categoria"] for cf in CONFIGS},
            "categorias_revisado": {cf: r[cf]["categoria"] for cf in CONFIGS},
            "cambios_categoria": cambios,
            "senales_y_tiempos_identicos": mismas,
            "emisiones_reales": {"oportunas": r["emisiones_reales"]["oportunas"],
                                 "latencia_primera_oportuna_s": r["emisiones_reales"]["latencia_primera_oportuna_s"]},
            "primera_por_config_s": {cf: (r[cf]["primera"] or {}).get("disponible_desde_inicio_s") for cf in CONFIGS},
            "suricata": {"calidad_pm60": {"estado": cal[eid]["estado"], "kernel_drops": cal[eid]["suricata"].get("kernel_drops"),
                                          "muestras_utc": [cal[eid]["suricata"].get("muestra_desde_utc"),
                                                           cal[eid]["suricata"].get("muestra_hasta_utc")]},
                         "integridad_m120_p90": {"kernel_drops_delta": cap["suricata_kernel_drops_delta_periodo"],
                                                 "periodo_utc": [an.iso(cap["periodo"]["inicio"]), an.iso(cap["periodo"]["fin"])],
                                                 "mediciones": cap["suricata_mediciones_en_periodo"]}}})

    def pob(e, crit):
        # análisis ADICIONAL (no sustituye al principal): un solo intervalo para Suricata en calidad e integridad
        if crit == "principal":
            return e["principal_revisado"]
        otros = [x for x in e["integridad_v2_ausentes"] if x != "captura_sin_errores_relevantes"]
        dr = (e["suricata"]["calidad_pm60"]["kernel_drops"] if crit == "unificado_pm60"
              else e["suricata"]["integridad_m120_p90"]["kernel_drops_delta"])
        r = R["episodios"][e["episodio"]]
        resto = [m for m in r["observacion"]["motivos"] if not m.startswith("fuente") and not m.startswith("integridad")]
        return not otros and not resto and dr == 0
    adicional = {c: sorted(e["episodio"] for e in eps if pob(e, c)) for c in ("principal", "unificado_pm60", "unificado_m120_p90")}

    ctl = R["control_normal"]["tramo_cubierto"]
    d, h = map(an.ep_iso, R["control_normal"]["intervalo_declarado_utc"])
    out = {"naturaleza": "revisión posterior a conocer los resultados; no es protocolo original ni evaluación independiente",
           "poblacion_original": sorted(e["episodio"] for e in eps if e["principal_original"]),
           "poblacion_revisada": adicional["principal"],
           "analisis_adicional_suricata": {
               "nota": "no se elige: el principal conserva calidad ±60 s y captura [−120, +90] como en el original",
               **adicional},
           "tabla8_original": tabla8(O), "tabla8_revisada": tabla8(R),
           "control_original_igual_al_revisado": O["control_normal"] == R["control_normal"],
           "control": {"intervalo_utc": ctl["intervalo_utc"], "requeridas": ctl["requeridas"], "decididas": ctl["decididas"],
                       "cobertura": ctl["cobertura_total"],
                       **{cf: ctl[cf] for cf in CONFIGS}},
           "control_solapamiento_IF_HEUR": control_solapamiento(a.motor, cfg, d, h),
           "inventario": {k: R["inventario"][k] for k in ("requeridas", "estados", "decididas_en_vivo", "cobertura_total", "solo_en_vivo")},
           "episodios": eps}
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "comparacion.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (a.salida / "TABLAS-REVISION.md").write_text(md(out), encoding="utf-8")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in adicional.items()}))
    return 0


def md(o: dict) -> str:
    L = ["# Tablas de la revisión 3B (revisión posterior a conocer los resultados)", "",
         "OP oportuna · SP solo_posterior · AU ausencia_con_observacion_suficiente · NE no_evaluable. "
         "Las 7 configuraciones son clasificaciones DERIVADAS de los registros; las emisiones reales van aparte.", "",
         f"Población principal: original {len(o['poblacion_original'])}/25 → revisada {len(o['poblacion_revisada'])}/25.", "",
         "## 1. Episodios: original frente a revisado", "",
         "| Episodio | Principal orig. | Principal rev. | Requisitos no verificados (rev.) | " + " | ".join(CONFIGS)
         + " | Emisión real oportuna (s) |", "|" + "---|" * (len(CONFIGS) + 5)]
    for e in o["episodios"]:
        cats = " | ".join((ABR[e["categorias_original"][c]] + "→" if e["categorias_original"][c] != e["categorias_revisado"][c] else "")
                          + ABR[e["categorias_revisado"][c]] for c in CONFIGS)
        L.append(f"| {e['episodio']} | {'sí' if e['principal_original'] else 'no'} | {'sí' if e['principal_revisado'] else 'no'} | "
                 f"{', '.join(e['integridad_v2_ausentes']) or '—'} | {cats} | "
                 f"{e['emisiones_reales']['latencia_primera_oportuna_s'] if e['emisiones_reales']['oportunas'] else 'no'} |")
    L += ["", "Señales, primeras señales y emisiones idénticas entre original y revisado en todos los episodios: "
          + ("sí" if all(e["senales_y_tiempos_identicos"] for e in o["episodios"]) else "NO"), "",
          "## 2. Tabla 8 revisada (población principal revisada, por familia)", "",
          "| Familia | Episodios | " + " | ".join(CONFIGS) + " | Emisión real oportuna |", "|" + "---|" * (len(CONFIGS) + 3)]
    for fam, v in o["tabla8_revisada"].items():
        L.append(f"| {fam} | {v['episodios']} | " + " | ".join(
            " ".join(f"{ABR[k]}{n}" for k, n in sorted(v[c].items(), key=lambda kv: CATS.index(kv[0]))) for c in CONFIGS)
                 + f" | {v['emisiones_oportunas']}/{v['episodios']} |")
    L += ["", "Tabla 8 original (1 episodio):", ""]
    for fam, v in o["tabla8_original"].items():
        L.append(f"- {fam}: {v['episodios']} episodio(s); " + "; ".join(
            f"{c} " + " ".join(f"{ABR[k]}{n}" for k, n in v[c].items()) for c in CONFIGS))
    c = o["control"]
    L += ["", "## 3. Control normal (sin cambios entre original y revisado: "
          + ("idéntico" if o["control_original_igual_al_revisado"] else "DISTINTO") + ")", "",
          f"Tramo {c['intervalo_utc'][0]} – {c['intervalo_utc'][1]}; requeridas {c['requeridas']}, decididas {c['decididas']}, "
          f"cobertura {c['cobertura']}.", "", "| Configuración | Falsas alarmas | Tasa entre decididas | Cotas sobre requeridas |",
          "|---|---|---|---|"]
    for cf in CONFIGS:
        x = c[cf]
        L.append(f"| {cf} | {x['falsas_alarmas']} / {c['decididas']} | {100 * x['tasa_entre_decididas']:.2f} % | "
                 f"[{100 * x['cotas_sobre_requeridas']['min']:.2f}, {100 * x['cotas_sobre_requeridas']['max']:.2f}] % |")
    s = o["control_solapamiento_IF_HEUR"]
    L += ["", "Solapamiento IF/HEUR en el control (HIB = IF ∪ HEUR):", "",
          "| α | IF | HEUR | IF y HEUR | HEUR sin IF (lo que añade HIB) | HIB |", "|---|---|---|---|---|---|"]
    for al in an.ALFAS:
        x = s[al]
        L.append(f"| {al} | {x['IF']} | {x['HEUR']} | {x['IF_y_HEUR']} | {x['HEUR_sin_IF']} | {x['HIB']} |")
    L += ["", f"HEUR por tipo: {s['HEUR_por_tipo']}; por entidad: {s['HEUR_por_entidad']}", "",
          "## 4. Suricata: los dos criterios (sin elegir)", "",
          "| Episodio | Calidad ±60 s: estado | drops ±60 | Integridad [−120, +90]: drops | Periodo integridad |",
          "|---|---|---|---|---|"]
    for e in o["episodios"]:
        q, i = e["suricata"]["calidad_pm60"], e["suricata"]["integridad_m120_p90"]
        L.append(f"| {e['episodio']} | {q['estado']} | {q['kernel_drops']} | {i['kernel_drops_delta']} | "
                 f"{i['periodo_utc'][0][11:19]}–{i['periodo_utc'][1][11:19]} |")
    ad = o["analisis_adicional_suricata"]
    L += ["", f"Análisis adicional (no sustituye al principal): un solo intervalo para calidad e integridad → "
          f"±60 s: {len(ad['unificado_pm60'])}/25; [−120, +90]: {len(ad['unificado_m120_p90'])}/25; principal: {len(ad['principal'])}/25.",
          f"Diferencia ±60 frente a principal: {sorted(set(ad['unificado_pm60']) ^ set(ad['principal']))}."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
