#!/usr/bin/env python3
"""Resume la salida de analizar_3b.py (paso 3B) en tablas CSV/MD. SOLO LEE: no recalcula categorías, población,
cobertura ni integridad; copia lo que dicen analisis-3b.json, integridad.json, calidad-fuentes.json, captura.json de
los respaldos, ciclos.jsonl y marcas.jsonl, y los agrega por escenario, configuración, α, entidad y tramo.

Uso (desde ejecucion-3b-2026-11-01/):
  python -I herramientas-informe/resumir_3b.py --evidencia evidencia/sensor --umbrales-alfa <umbrales-alfa-precision-completa.json> --salida tablas
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

CFG = ["IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01"]
CATS = ["oportuna", "solo_posterior", "ausencia_con_observacion_suficiente", "no_evaluable"]
FAM = {"escaneo_sostenido": "Escaneo sostenido", "inundacion_http": "Inundación HTTP", "dns_inusual": "DNS inusual",
       "escaneo_breve": "Escaneo breve", "fuerza_bruta_http": "Fuerza bruta HTTP"}
TRAMOS = [("previo (motor activo, antes del control)", "2026-11-01T03:14:01Z", "2026-11-01T07:32:00Z"),
          ("control normal", "2026-11-01T07:32:00Z", "2026-11-01T08:05:00Z"),
          ("entre control y batería", "2026-11-01T08:05:00Z", "2026-11-01T08:08:39Z"),
          ("batería (1.er inicio - último fin)", "2026-11-01T08:08:39Z", "2026-11-01T10:02:05.818Z"),
          ("cierre (fin + espera, hasta el último ciclo copiado)", "2026-11-01T10:02:05.818Z", "2026-11-01T10:40:00Z")]


def ep(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pct(q, xs):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def w(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)


def md(rows: list[dict], cols=None) -> str:
    cols = cols or list(rows[0])
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidencia", type=Path, required=True)
    ap.add_argument("--umbrales-alfa", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args()
    E, O = a.evidencia, a.salida
    O.mkdir(parents=True, exist_ok=True)
    A = json.loads((E / "analisis/analisis-3b/analisis-3b.json").read_text(encoding="utf-8"))
    I = {e["episodio_id"]: e for e in json.loads((E / "analisis/integridad.json").read_text(encoding="utf-8"))["episodios"]}
    Q = json.loads((E / "analisis/calidad-fuentes.json").read_text(encoding="utf-8"))["episodios"]
    marcas = [json.loads(l) for l in (E / "copias/marcas.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    T = defaultdict(dict)
    for m in marcas:
        if m.get("episodio_id") and "reloj" in m:
            T[m["episodio_id"]][m["evento"]] = ep(m["reloj"]["pared_utc"])
            if m["evento"] == "fin":
                T[m["episodio_id"]]["estado"] = m.get("estado")
    orden = sorted(A["episodios"], key=lambda k: T[k]["inicio"])
    fuentes = {"analisis-3b.json": sha(E / "analisis/analisis-3b/analisis-3b.json"),
               "integridad.json": sha(E / "analisis/integridad.json"),
               "calidad-fuentes.json": sha(E / "analisis/calidad-fuentes.json")}

    # --- 1. episodios × configuración ------------------------------------------------------------------------
    filas_ep, filas_int, filas_sur, filas_em, filas_emd, filas_ven = [], [], [], [], [], []
    for n, k in enumerate(orden, 1):
        e = A["episodios"][k]
        ini, fin = T[k]["inicio"], T[k]["fin"]
        integ = I[k]
        no_ver = [r for r, v in integ["requisitos"].items() if v["estado"] != "verificado"]
        r = {"orden": n, "episodio": k, "escenario": FAM[k.rsplit("-", 1)[0]], "inicio_utc": iso(ini), "fin_utc": iso(fin),
             "duracion_s": round(fin - ini, 1), "estado_generador": T[k].get("estado"),
             "ventanas_requeridas": e["ventanas_requeridas"],
             "a_tiempo": e["estados_ventana"].get("decidida_a_tiempo", 0),
             "tardias": e["estados_ventana"].get("decidida_tardia", 0),
             "no_evaluadas": e["estados_ventana"].get("no_evaluada", 0), "ausentes": e["estados_ventana"].get("ausente", 0),
             "inventario_cubre": e["cobertura_inventario"]["cubre"], "calidad_fuente": e["observacion"]["calidad_fuente"],
             "integridad_apta": e["observacion"]["integridad_apta"], "requisitos_no_verificados": ";".join(no_ver),
             "poblacion_principal": "sí" if e["en_poblacion_principal"] else "no",
             "motivos_fuera": "; ".join(e["observacion"]["motivos"])}
        for c in CFG:
            r[c] = e[c]["categoria"]
        em = e["emisiones_reales"]
        r["emisiones_oportunas"] = em["oportunas"]
        r["latencia_1a_emision_oportuna_s"] = em["latencia_primera_oportuna_s"]
        filas_ep.append(r)
        for c in CFG:
            p = e[c].get("primera") or {}
            filas_ven.append({"episodio": k, "configuracion": c, "categoria": e[c]["categoria"],
                              "poblacion_principal": r["poblacion_principal"],
                              "senales_atribuibles": e[c]["senales_atribuibles"], "senales_oportunas": e[c]["oportunas"],
                              "senales_no_atribuibles": len(e[c]["senales_no_atribuibles"]),
                              "primera_window_end_utc": p.get("window_end_utc"), "primera_disponible_utc": p.get("disponible_utc"),
                              "primera_disponible_desde_inicio_s": p.get("disponible_desde_inicio_s")})
        filas_int.append({"episodio": k, "apto": integ["apto"],
                          **{req: v["estado"] + (f" ({v['razon']})" if v["estado"] != "verificado" else "")
                             for req, v in integ["requisitos"].items()}})
        cap = json.loads((E / f"analisis/respaldos/{k}/captura.json").read_text(encoding="utf-8"))
        cov = json.loads((E / f"analisis/respaldos/{k}/cobertura.json").read_text(encoding="utf-8"))
        q = Q[k]
        filas_sur.append({"episodio": k, "calidad_fuente(±60s)": q["estado"],
                          "suricata_kernel_drops(±60s)": q["suricata"].get("kernel_drops"),
                          "suricata_kernel_packets(±60s)": q["suricata"].get("kernel_packets"),
                          "suricata_kernel_drops(-120/+90s,integridad)": cap["suricata_kernel_drops_delta_periodo"],
                          "tcpdump_descartes": cap["paquetes_descartados"], "tcpdump_alcance": cap["alcance_descartes"],
                          "ens37_rx_dropped(±60s,sin clasificar)": q["interfaz_ens37"].get("rx_dropped"),
                          "pcap_continuo": q["archivo"]["continuo"], "pcap_ficheros": q["archivo"]["ficheros"],
                          "hueco_registro_motor_max_s": round(cov["detalle"]["hueco_motor_max_s"], 2)})
        filas_em.append({"episodio": k, "escenario": r["escenario"], "poblacion_principal": r["poblacion_principal"],
                         "emisiones": em["emisiones"], "atribuibles": em["atribuibles"], "oportunas": em["oportunas"],
                         "latencia_1a_oportuna_s": em["latencia_primera_oportuna_s"],
                         "1a_oportuna_componente": (em["primera_oportuna"] or {}).get("componente_emisor"),
                         "1a_oportuna_window_end_utc": (em["primera_oportuna"] or {}).get("window_end_utc")})
        for d in em["detalle"]:
            filas_emd.append({"episodio": k, **d})

    w(O / "episodios-configuraciones.csv", filas_ep)
    w(O / "senales-por-configuracion.csv", filas_ven)
    w(O / "integridad-requisitos.csv", filas_int)
    w(O / "calidad-fuentes-suricata.csv", filas_sur)
    w(O / "emisiones-reales.csv", filas_em)
    w(O / "emisiones-reales-detalle.csv", filas_emd)

    # --- 2. Tabla 8 propuesta ----------------------------------------------------------------------------------
    t8 = []
    for fam in FAM.values():
        eps = [f for f in filas_ep if f["escenario"] == fam]
        pp = [f for f in eps if f["poblacion_principal"] == "sí"]
        row = {"Escenario": fam, "Realizados": len(eps), "Población principal": len(pp)}
        for c in CFG:
            cp = Counter(f[c] for f in pp)
            cf = Counter(f[c] for f in eps if f["poblacion_principal"] == "no")
            row[c] = (f"{cp['oportuna']}/{len(pp)} op." + (f" ({cp['solo_posterior']} post.)" if cp["solo_posterior"] else "")
                      if pp else "n/a") + f" · fuera: {cf['oportuna']} op., {cf['solo_posterior']} post., {cf['no_evaluable']} n/e"
        row["Emisiones reales (episodios con ≥1 oportuna)"] = f"{sum(1 for f in eps if f['emisiones_oportunas'])}/{len(eps)}"
        t8.append(row)
    w(O / "tabla8-propuesta.csv", t8)

    # --- 3. control normal -------------------------------------------------------------------------------------
    C = A["control_normal"]
    tc = C["tramo_cubierto"]
    ctrl = [{"configuracion": c, "falsas_alarmas": tc[c]["falsas_alarmas"], "decididas": tc["decididas"],
             "requeridas_inventario": tc["requeridas"], "sin_decision": tc["sin_decision"],
             "cobertura": tc["cobertura_total"], "tasa": tc[c]["tasa_entre_decididas"],
             "cota_min": tc[c]["cotas_sobre_requeridas"]["min"], "cota_max": tc[c]["cotas_sobre_requeridas"]["max"]}
            for c in CFG]
    w(O / "control-falsas-alarmas.csv", ctrl)
    ent = [{"entidad": ip, **v} for ip, v in C["por_entidad"].items()]
    w(O / "control-por-entidad.csv", ent)
    # sin el DNS (solo informativo; el DNS está DENTRO de la población por protocolo)
    dns = C["por_entidad"]["10.10.10.20"]
    ctrl_sin_dns = [{"configuracion": c, "falsas_alarmas_sin_DNS": tc[c]["falsas_alarmas"] - dns[c],
                     "decididas_sin_DNS": tc["decididas"] - dns["ventanas"],
                     "tasa_sin_DNS": round((tc[c]["falsas_alarmas"] - dns[c]) / (tc["decididas"] - dns["ventanas"]), 6),
                     "nota": "INFORMATIVO: el DNS 10.10.10.20 está en la población (excepción de respuesta, no de población)"}
                    for c in CFG]
    w(O / "control-informativo-sin-dns.csv", ctrl_sin_dns)

    # --- 4. comparación de α -----------------------------------------------------------------------------------
    U = json.loads(a.umbrales_alfa.read_text(encoding="utf-8"))["umbrales_full_precision"]
    sk = U["validacion_sin_kali_65553"]
    alfa = []
    for c, al, k in (("IF_0.05", 0.05, "0.050"), ("IF_0.03", 0.03, "0.030"), ("IF_0.01", 0.01, "0.010")):
        for base, h in ((c, None), ("HIB_" + c[3:], None)):
            cat_all = Counter(f[base] for f in filas_ep)
            cat_pp = Counter(f[base] for f in filas_ep if f["poblacion_principal"] == "sí")
            lat = [x["primera_disponible_desde_inicio_s"] for x in filas_ven
                   if x["configuracion"] == base and x["categoria"] == "oportuna" and x["primera_disponible_desde_inicio_s"] is not None]
            alfa.append({"configuracion": base, "alfa": al, "umbral": A["umbrales"][c],
                         "umbral_igual_a_calibracion_sin_kali": float(sk[k]) == A["umbrales"][c],
                         "pp_oportuna": f"{cat_pp['oportuna']}/{sum(cat_pp.values())}",
                         "pp_solo_posterior": cat_pp["solo_posterior"],
                         "pp_ausencia_obs_suficiente": cat_pp["ausencia_con_observacion_suficiente"],
                         "todos_oportuna": f"{cat_all['oportuna']}/25", "todos_solo_posterior": cat_all["solo_posterior"],
                         "todos_no_evaluable": cat_all["no_evaluable"],
                         "mediana_disponibilidad_1a_senal_oportuna_s": round(pct(.5, lat), 2) if lat else None,
                         "control_falsas_alarmas": tc[base]["falsas_alarmas"], "control_tasa": tc[base]["tasa_entre_decididas"],
                         "control_cobertura": tc["cobertura_total"], "control_decididas": tc["decididas"]})
    w(O / "comparacion-alfa.csv", alfa)

    # --- 5. ciclos del motor y puntualidad por tramo -----------------------------------------------------------
    cic = [json.loads(l) for l in (E / "copias/ciclos.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    gaps = A["ciclos"]["huecos_escritura_mayores_20s"]
    regs = []
    with gzip.open(E / "copias/motor_decision.log.gz", "rt", encoding="utf-8", errors="replace") as fh:
        for l in fh:
            if '"window_end_utc"' in l and '"logged_at"' in l:
                try:
                    d = json.loads(l)
                    if d.get("event") == "decision":
                        regs.append(float(d["logged_at"]))
                except Exception:
                    pass
    regs.sort()
    esc = sorted(set(regs))
    tramos = []
    for nom, d0, d1 in TRAMOS:
        t0, t1 = ep(d0), ep(d1)
        cc = [x for x in cic if t0 <= float(x["inicio_ciclo"]) < t1]
        dur = [float(x["duracion_s"]) for x in cc if x.get("duracion_s") is not None]
        es = [t for t in esc if t0 <= t < t1]
        hu = [b - a_ for a_, b in zip(es, es[1:])]
        g = [x for x in gaps if t0 <= ep(x["desde_utc"]) < t1]
        tramos.append({"tramo": nom, "desde": d0, "hasta": d1, "ciclos": len(cc),
                       "ciclo_dur_p50_s": round(pct(.5, dur), 2) if dur else None,
                       "ciclo_dur_p95_s": round(pct(.95, dur), 2) if dur else None, "ciclo_dur_max_s": round(max(dur), 2) if dur else None,
                       "instantes_escritura_decisiones": len(es),
                       "hueco_escritura_p50_s": round(pct(.5, hu), 2) if hu else None,
                       "hueco_escritura_p95_s": round(pct(.95, hu), 2) if hu else None,
                       "hueco_escritura_max_s": round(max(hu), 2) if hu else None,
                       "huecos_escritura_>20s(analizador)": len(g),
                       "huecos_>20s_max_s": max((x["s"] for x in g), default=None)})
    w(O / "ciclos-y-huecos-por-tramo.csv", tramos)

    # --- 6. MD resumen -----------------------------------------------------------------------------------------
    inv = A["inventario"]
    txt = [f"# Tablas del paso 3B — campaña A repetida 2026-11-01 (generadas por resumir_3b.py)\n",
           "Fuentes (sha256): " + ", ".join(f"`{k}` {v[:12]}…" for k, v in fuentes.items()) + "\n",
           "Las 7 configuraciones son clasificaciones **derivadas** de los registros (no detectores desplegados). Las "
           "emisiones reales (ALERT del IF desplegado y heurísticos registrados en vivo) van aparte.\n",
           "## Tabla 8 propuesta (población principal; los episodios fuera se cuentan aparte)\n", md(t8),
           "\nLectura: «x/n op.» = episodios de la población principal con categoría `oportuna`; «fuera:» = episodios con "
           "observación incompleta, cuyas detecciones se publican pero no entran en la tabla principal "
           "(op. = oportuna, post. = solo_posterior, n/e = no_evaluable).\n",
           "## Categorías por episodio y configuración\n",
           md(filas_ep, ["orden", "episodio", "poblacion_principal", "calidad_fuente", "integridad_apta", "ventanas_requeridas",
                         "tardias"] + CFG + ["emisiones_oportunas", "latencia_1a_emision_oportuna_s"]),
           "\n## Control normal (07:32:00–08:05:00, inventario)\n", md(ctrl),
           f"\nInventario completo de la ejecución: {inv['requeridas']} ventanas requeridas, cobertura {inv['cobertura_total']}, "
           f"a tiempo {inv['estados']['decidida_a_tiempo']}, tardías {inv['estados']['decidida_tardia']}, "
           f"no evaluadas {inv['estados']['no_evaluada']}, ausentes {inv['estados']['ausente']}; retraso de disponibilidad "
           f"p50 {inv['puntualidad']['retraso_disponibilidad_s']['p50']} s, p95 {inv['puntualidad']['retraso_disponibilidad_s']['p95']} s, "
           f"máx {round(inv['puntualidad']['retraso_disponibilidad_s']['max'], 1)} s.\n",
           "### Control por entidad\n", md(ent),
           "\n### Informativo: control sin el DNS 10.10.10.20 (no sustituye a la tabla anterior)\n", md(ctrl_sin_dns),
           "\n## Comparación de α (mismo tráfico)\n", md(alfa),
           "\n## Emisiones reales por episodio\n", md(filas_em),
           "\n## Calidad de fuentes y descartes de Suricata (por separado)\n", md(filas_sur),
           "\n## Ciclos del motor y huecos entre escrituras por tramo\n", md(tramos)]
    (O / "TABLAS-3B.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print(json.dumps({"tablas": sorted(p.name for p in O.iterdir()), "fuentes": fuentes}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
