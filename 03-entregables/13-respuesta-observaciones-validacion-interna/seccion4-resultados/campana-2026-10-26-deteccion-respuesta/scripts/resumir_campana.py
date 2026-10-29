#!/usr/bin/env python3
"""Tablas legibles de la campaña A a partir de analisis.json (analizar.py) y de las evidencias de actividad.

No reclasifica nada: las categorías, la evaluabilidad y la Tabla 8 salen tal cual de analisis.json. Lo que añade:
  - registro de los 25 episodios con estado del generador, actividad en el PCAP y respuestas del servidor (/auth);
  - Tabla 8 propuesta con totales sobre la misma población evaluable;
  - complementaria: detecciones posteriores, observadas sin confirmar y detecciones confirmadas de episodios no
    evaluables, con su motivo;
  - falsas alarmas del control con denominador y desglose por entidad;
  - compartidas/exclusivas IF vs heurísticos para los TRES α (por episodio evaluable y por ventana confirmada),
    con las mismas funciones de analizar.py (senales, atribuir);
  - tiempos: emisiones reales del IF desplegado y disponibilidad de los registros de las configuraciones derivadas.
"""
from __future__ import annotations
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402

CONFIGS = an.CONFIGS
ALFAS = an.ALFAS


def escribir_csv(path: Path, filas: list[dict]):
    if not filas:
        path.write_text("", encoding="utf-8"); return
    campos = list(dict.fromkeys(k for f in filas for k in f))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader(); w.writerows(filas)


def md_tabla(filas: list[dict], campos: list[str]) -> list[str]:
    L = ["| " + " | ".join(campos) + " |", "|" + "---|" * len(campos)]
    for f in filas:
        L.append("| " + " | ".join("" if f.get(c) is None else str(f.get(c)) for c in campos) + " |")
    return L


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analisis", required=True, type=Path)
    ap.add_argument("--actividad", required=True, type=Path)
    ap.add_argument("--marcas", required=True, type=Path)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--destinos", required=True, type=Path)
    ap.add_argument("--brute", required=True, type=Path, help="brute.log del endpoint /auth (srv-dmz)")
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--salida-dir", required=True, type=Path)
    a = ap.parse_args()
    out = a.salida_dir; out.mkdir(parents=True, exist_ok=True)

    A = json.loads(a.analisis.read_text(encoding="utf-8"))
    act = json.loads(a.actividad.read_text(encoding="utf-8"))["episodios"]
    fines = {}
    for l in a.marcas.open(encoding="utf-8"):
        e = json.loads(l)
        if e.get("evento") == "fin":
            fines[e["episodio_id"]] = e
    eps, _ = an.leer_marcas(a.marcas)
    brute = []
    for l in a.brute.open(encoding="utf-8"):
        m = re.match(r"^(\S+) (\S+) \S+ /auth user=(\S+) -> (\d+)", l)
        if m:
            brute.append((an.ep_iso(m.group(1)), m.group(2), m.group(3), int(m.group(4))))

    # ---------------------------------------------------------------- registro de episodios
    reg = []
    orden = sorted(eps, key=lambda k: eps[k]["inicio_ep"])
    for n, eid in enumerate(orden, 1):
        ep, c, ac, f = eps[eid], A["episodios"][eid], act.get(eid, {}), fines.get(eid, {})
        fila = {"n": n, "episodio_id": eid, "escenario": ep["escenario"], "repeticion": ep["repeticion"],
                "destino": ep["destino"], "inicio_utc": an.iso(ep["inicio_ep"])[11:23],
                "fin_utc": an.iso(ep["fin_ep"])[11:23] if ep["fin_ep"] else None,
                "duracion_comando_s": ac.get("duracion_comando_s"), "estado_generador": ep["estado"],
                "codigo_salida": f.get("codigo_salida"), "intentos_bucle": f.get("intentos_generador"),
                "bytes_stdout": f.get("bytes_stdout"), "bytes_stderr": f.get("bytes_stderr"),
                "pcap_paquetes_hacia_destino": ac.get("paquetes_hacia_destino_durante"),
                "pcap_syn_hacia_destino": ac.get("syn_tcp_hacia_destino_durante"),
                "pcap_actividad_observada_s": ac.get("actividad_observada_s")}
        if ep["escenario"] == "fuerza_bruta_http" and ep["fin_ep"]:
            b = [x for x in brute if x[1] == "10.10.20.30" and ep["inicio_ep"] <= x[0] <= ep["fin_ep"] + 3]
            fila["servidor_auth_401"] = sum(1 for x in b if x[3] == 401)
            fila["servidor_auth_otros"] = sum(1 for x in b if x[3] != 401)
        fila["evaluable"] = c["evaluable"]
        fila["motivo_no_evaluable"] = c["motivo_no_evaluable"]
        reg.append(fila)
    escribir_csv(out / "registro-episodios.csv", reg)

    # ---------------------------------------------------------------- Tabla 8 propuesta
    t8, tot = [], Counter()
    for fam, t in A["tabla8"].items():
        n_ev = len(t["evaluables"])
        realizados = len(t["evaluables"]) + len(t["no_evaluables"])
        fila = {"escenario": fam, "realizados": realizados, "evaluables": n_ev}
        tot["realizados"] += realizados; tot["evaluables"] += n_ev
        for cf in CONFIGS:
            # sin evaluables no hay recuento que dar: «n/a», nunca un 0 que parezca «no detectado»
            fila[cf] = t[cf] if n_ev else "n/a"; tot[cf] += t[cf]
        t8.append(fila)
    tot = dict(tot)
    if not tot["evaluables"]:
        tot.update({cf: "n/a" for cf in CONFIGS})
    t8.append({"escenario": "TOTAL (misma población evaluable)", **tot})
    escribir_csv(out / "tabla8-propuesta.csv", t8)

    # ---------------------------------------------------------------- complementaria
    comp = []
    for eid in orden:
        c = A["episodios"][eid]
        for cf in CONFIGS:
            x = c[cf]
            if not c["evaluable"]:
                if x.get("deteccion_confirmada") or x.get("senal_observada"):
                    comp.append({"episodio_id": eid, "configuracion": cf, "tipo": (
                        "deteccion_confirmada_en_episodio_no_evaluable" if x.get("deteccion_confirmada")
                        else "senal_observada_en_episodio_no_evaluable"),
                        "relacion": x.get("relacion_temporal"), "desde_inicio_s": x.get("desde_inicio_generador_s"),
                        "motivo_no_evaluable": c["motivo_no_evaluable"]})
            elif x["categoria"] in ("posterior", "observada_sin_confirmar"):
                comp.append({"episodio_id": eid, "configuracion": cf, "tipo": x["categoria"],
                             "relacion": x.get("relacion_temporal"), "desde_inicio_s": x.get("desde_inicio_generador_s"),
                             "motivo_no_evaluable": None})
    escribir_csv(out / "complementaria-tardias-no-evaluables.csv", comp)
    noev = [{"episodio_id": eid, "escenario": eps[eid]["escenario"], "motivo": A["episodios"][eid]["motivo_no_evaluable"],
             "cobertura": json.dumps(A["episodios"][eid]["cobertura"], ensure_ascii=False)}
            for eid in orden if not A["episodios"][eid]["evaluable"]]
    escribir_csv(out / "episodios-no-evaluables.csv", noev)

    # ---------------------------------------------------------------- control normal
    ctl = A["control_normal_fpr"]
    fa = [{"configuracion": cf, "falsas_alarmas": ctl[cf]["falsas_alarmas"], "denominador_ventanas": ctl["denominador"],
           "tasa": ctl[cf]["tasa"]} for cf in CONFIGS if cf in ctl]
    escribir_csv(out / "falsas-alarmas-control.csv", fa)
    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    U = an.umbrales_de(cfg)
    regs, _, _ = an.leer_motor(a.motor)
    d0, d1 = an.ep_iso(ctl["desde"]), an.ep_iso(ctl["hasta"])
    excl_txt = cfg["combinacion_real"]["exclusiones"]["NUNCA_BLOQUEAR"]
    excl_ip = {x.split()[0] for x in excl_txt}
    v = [r for r in regs if d0 <= r["_wend"] <= d1]
    por_ent = defaultdict(Counter)
    for r in v:
        g = an.senales(r, U)
        por_ent[r["entity_ip"]]["ventanas"] += 1
        for cf in CONFIGS:
            por_ent[r["entity_ip"]][cf] += int(g[cf])
    ent = [{"entity_ip": ip, "en_NUNCA_BLOQUEAR": ip in excl_ip, **dict(cn)} for ip, cn in sorted(por_ent.items())]
    escribir_csv(out / "control-por-entidad.csv", ent)

    # ---------------------------------------------------------------- compartidas / exclusivas, tres α
    destinos = defaultdict(list)
    for row in csv.DictReader(open(a.destinos, encoding="utf-8")):
        destinos[(row["episodio_id"], row["window_end_utc"])].append(row["destino"])
    origen = cfg.get("origen") or "10.10.20.30"
    kali = [r for r in regs if r["entity_ip"] == origen]
    compart = []
    for al in ALFAS:
        ep_c = Counter(); win = Counter()
        for eid in orden:
            c = A["episodios"][eid]
            if not c["evaluable"]:
                continue
            i_ = c[f"IF_{al}"]["categoria"] == "durante"; h_ = c["HEUR"]["categoria"] == "durante"
            ep_c["ambos" if i_ and h_ else "solo_IF" if i_ else "solo_HEUR" if h_ else "ninguno"] += 1
            ep = eps[eid]; ini, fin = ep["inicio_ep"], ep["fin_ep"]
            for r in kali:
                if not (ini <= r["_logged"] <= fin and r["_wend"] > ini and r["_wend"] - an.HORIZONTE_S < fin):
                    continue
                inc, _, conf = an.atribuir(destinos, eid, r["window_end_utc"], ep["destino"])
                if not inc or not conf:
                    continue
                g = an.senales(r, U)
                win["ambos" if g[f"IF_{al}"] and g["HEUR"] else "solo_IF" if g[f"IF_{al}"]
                    else "solo_HEUR" if g["HEUR"] else "ninguno"] += 1
        compart.append({"alfa": al, "nivel": "episodio evaluable (detección durante)", **dict(ep_c)})
        compart.append({"alfa": al, "nivel": "ventana con atribución confirmada, escrita durante el ataque", **dict(win)})
    escribir_csv(out / "compartidas-exclusivas.csv", compart)

    # ---------------------------------------------------------------- tiempos
    tiem = []
    for eid in orden:
        c = A["episodios"][eid]
        p = c["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"]
        fila = {"episodio_id": eid, "evaluable": c["evaluable"],
                "latencia_real_IF_desplegado_s": p["desde_inicio_generador_s"] if p else None}
        for cf in CONFIGS:
            x = c[cf]
            fila[f"disponibilidad_{cf}_s"] = (x.get("desde_inicio_generador_s")
                                              if x.get("deteccion_confirmada") and x.get("relacion_temporal") ==
                                              "durante_actividad" else None)
        tiem.append(fila)
    escribir_csv(out / "tiempos.csv", tiem)

    # ---------------------------------------------------------------- resumen md
    L = ["# Campaña A: tablas para la sección 4.2 (generadas por resumir_campana.py)", "",
         "Las categorías y la evaluabilidad salen de `analisis.json` sin cambios. Las siete configuraciones son "
         "clasificaciones comparativas derivadas sobre las mismas ventanas; no son siete detectores desplegados.", "",
         "## Registro de episodios", ""]
    L += md_tabla(reg, ["n", "episodio_id", "inicio_utc", "duracion_comando_s", "estado_generador", "codigo_salida",
                        "intentos_bucle", "pcap_paquetes_hacia_destino", "pcap_syn_hacia_destino",
                        "servidor_auth_401", "evaluable"])
    L += ["", "## Tabla 8 propuesta (detección durante / evaluables)", ""]
    L += md_tabla(t8, ["escenario", "realizados", "evaluables", *CONFIGS])
    L += ["", "## Falsas alarmas del control normal", "",
          f"Población: window_end en [{ctl['desde']}, {ctl['hasta']}]; {ctl['denominador']} ventanas evaluadas, "
          f"{ctl['ventanas_no_evaluadas']} no evaluadas explícitas; cobertura entre registradas "
          f"{ctl['cobertura_entre_registradas']} (sin inventario independiente).", ""]
    L += md_tabla(fa, ["configuracion", "falsas_alarmas", "denominador_ventanas", "tasa"])
    L += ["", "## Compartidas y exclusivas IF / heurísticos", ""]
    L += md_tabla(compart, ["alfa", "nivel", "ambos", "solo_IF", "solo_HEUR", "ninguno"])
    (out / "TABLAS-4.2.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"tablas en {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
