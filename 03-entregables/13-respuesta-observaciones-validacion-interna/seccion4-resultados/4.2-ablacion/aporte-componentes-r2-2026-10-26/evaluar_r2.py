#!/usr/bin/env python3
"""Seccion 4.2, revision r2: aporte de los componentes con historia real y criterio temporal separado.

Offline y de solo lectura. Reglas en config-r2.json (registrado antes de calcular, commit d60495f).
Reutiliza el nucleo de ../aporte-componentes-2026-10-26/evaluar_componentes.py (entorno, senales,
umbrales y metricas por ventana) sin modificarlo.

    python evaluar_r2.py --datos DIR [--salida resultados]

DIR es la misma copia de solo lectura del sensor que usa la version anterior.
"""
from __future__ import annotations

import argparse
import ast
import csv
import gzip
import importlib.util
import ipaddress
import json
import math
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
if sys.platform == "win32" and not str(AQUI).startswith("\\\\?\\"):
    AQUI = Path("\\\\?\\" + str(AQUI))      # rutas > 260 caracteres en Windows
ANTERIOR = AQUI.parent / "aporte-componentes-2026-10-26"
EVID = AQUI / "evidencia" / "sensor-05oct"
BASTION, KALI = "10.10.10.30", "10.10.20.30"
HORIZONTE_S = 60
PASO_S = 10
SYN, ACK, FIN = 0x02, 0x10, 0x01
TOL_EQUIV = 1e-9
# publicar.log: la linea 2630 empieza con bytes NUL (perdida de la cola del 02-oct). 3 312 ejecuciones del
# cron frente a 3 311 lineas: a partir de esa linea, la linea L corresponde a la ejecucion L + 1.
LINEA_DESFASE = 2630


def cargar(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


B = cargar("evaluar_componentes", ANTERIOR / "evaluar_componentes.py")
ep, iso, sha256, escribir_csv, guardar_json = B.ep, B.iso, B.sha256, B.escribir_csv, B.guardar_json
CONFIGS, ALFAS, FAMILIAS, EPISODIOS = B.CONFIGS, B.ALFAS, B.FAMILIAS, B.EPISODIOS


def hms(t: float | None) -> str:
    return "" if t is None else datetime.fromtimestamp(t, timezone.utc).strftime("%H:%M:%S.%f")[:-4]


def r1(x):
    return None if x is None else round(x, 1)


# ----------------------------------------------------------------------------- datos de un episodio
def leer_episodio(env, d: Path) -> dict:
    v2, v3 = env.v2, env.v3
    ctx = []
    for ruta in sorted(d.glob("live-*.pcap")):
        for marca, trama in v2.iter_pcap_frames(ruta):
            c = v3.parse_con_contexto(marca, trama)
            if c is not None:
                ctx.append(c)
    utiles = [c for c in ctx if c.packet.protocol not in B.PROTOCOLOS_EXCLUIDOS]
    paquetes, dups = v3.deduplicar_espejo(utiles)
    paquetes.sort(key=lambda p: p.timestamp)
    eve_ts = []
    with open(d / "eve.json", encoding="utf-8") as f:
        for linea in f:
            try:
                eve_ts.append(v2.parse_eve_timestamp(json.loads(linea)["timestamp"]))
            except (ValueError, KeyError):
                pass
    return {"paquetes": paquetes, "dups": dups, "tramas": len(ctx),
            "pcap_ini": min(c.packet.timestamp for c in ctx), "pcap_fin": max(c.packet.timestamp for c in ctx),
            "eve_ini": min(eve_ts) if eve_ts else None, "eve_fin": max(eve_ts) if eve_ts else None,
            "eve_eventos": len(eve_ts)}


def sesiones_auth() -> list[dict]:
    """Sesiones SSH del bastion en el sensor (auth.log.3.gz, reloj del sensor)."""
    ab, out = {}, []
    for linea in open(EVID / "auth-sshd-20h15-21h09.txt", encoding="utf-8"):
        partes = linea.split()
        if len(partes) < 5:
            continue
        t = ep(partes[0])
        if "Accepted" in linea and f"from {BASTION}" in linea:
            ab[partes[partes.index("port") + 1]] = t
        elif "Disconnected from user" in linea and BASTION in linea:
            puerto = partes[partes.index("port") + 1]
            if puerto in ab:
                out.append({"puerto": puerto, "ini": ab.pop(puerto), "fin": t})
    return sorted(out, key=lambda s: s["ini"])


def marcas(info: dict, fam: str, t0: float, auth: list[dict]) -> dict:
    pk = info["paquetes"]
    ctrl = [p for p in pk if p.protocol == 6 and {p.src_ip, p.dst_ip} == {BASTION, KALI}
            and 22 in (p.src_port, p.dst_port)]
    syn = [p.timestamp for p in ctrl if p.src_ip == BASTION and p.tcp_flags & SYN and not p.tcp_flags & ACK]
    fin = [p.timestamp for p in ctrl if p.src_ip == BASTION and p.tcp_flags & FIN]
    assert len(syn) == 1 and fin, ("sesion de control ambigua", len(syn), len(fin))
    g_ini, g_fin = syn[0], fin[0]
    atq = [p.timestamp for p in pk if p.src_ip == KALI and FAMILIAS[fam]["ataque"](p)]
    previa = max((s for s in auth if s["ini"] <= g_ini), key=lambda s: s["ini"], default=None)
    post = min((s for s in auth if s["ini"] >= g_fin), key=lambda s: s["ini"], default=None)
    return {"T0_features": t0, "gen_ini": g_ini, "gen_fin": g_fin,
            "atq_ini": min(atq), "atq_fin": max(atq), "atq_paquetes": len(atq),
            "tsf_sesion_date": previa and previa["ini"], "tef_sesion_date": post and post["ini"]}


# ----------------------------------------------------------------------------- filas y evaluabilidad
def filas_replay(env, info: dict, cs_real: float) -> list[dict]:
    """build_rows con el inicio REAL de los datos; se descartan observaciones anteriores (no hay contexto)."""
    obs = env.v2.attribute_packets(info["paquetes"], B.RED)
    apps = [a for a in env.v2.load_app_observations(info["dir"] / "eve.json", B.RED) if a.timestamp >= cs_real]
    obs = [o for o in obs if o.timestamp >= cs_real]
    return env.v2.build_rows("r2-" + info["dir"].name, obs, apps, step_seconds=PASO_S, capture_start=cs_real)


def anclas(ini: float, fin: float) -> list[int]:
    return list(range(math.ceil(ini / PASO_S) * PASO_S, math.floor(fin / PASO_S) * PASO_S + 1, PASO_S))


def acotar(fila: dict) -> dict:
    """Transformacion exacta a6d287a -> 2d854a9: las dos razones DNS acotadas a 1.0."""
    g = dict(fila)
    for c in ("dns_nxdomain_ratio_60s", "unique_dns_name_ratio_60s"):
        g[c] = min(1.0, float(g[c] or 0))
    return g


def estado_anclas(fuente: str, a_list, kali_rows: dict, sen: dict, info=None, cs_real=None,
                  cubiertas: set | None = None) -> dict:
    """Por ancla: ('fila'|'sin_fila'|'NE', senales). sin_fila = la Kali no tiene ventana ahi (tampoco en operacion)."""
    out = {}
    for a in a_list:
        if fuente == "replay":
            ok = a - HORIZONTE_S >= cs_real and a <= info["pcap_fin"]
        else:
            ok = a in kali_rows or a in cubiertas
        if not ok:
            out[a] = ("NE", None)
        elif a in kali_rows:
            out[a] = ("fila", sen[a])
        else:
            out[a] = ("sin_fila", None)
    return out


def categoria(est: dict, m: dict, cfg: str) -> dict:
    dur = [a for a in est if m["gen_ini"] <= a <= m["gen_fin"]]
    pos = [a for a in est if m["gen_fin"] < a <= m["gen_fin"] + HORIZONTE_S]
    con = lambda a: est[a][0] == "fila" and est[a][1][cfg]
    dur_ok = all(est[a][0] != "NE" for a in dur)
    hit_d = [a for a in dur if con(a)]
    hit_p = [a for a in pos if con(a)]
    if hit_d:
        cat, a = "D", hit_d[0]
    elif dur_ok and hit_p:
        cat, a = "P", hit_p[0]
    elif dur_ok and all(est[x][0] != "NE" for x in pos):
        cat, a = "N", None
    else:
        cat, a = "NE", None
    r = {"categoria": cat, "evaluable_durante": dur_ok,
         "anclas_durante": len(dur), "anclas_durante_NE": sum(est[x][0] == "NE" for x in dur),
         "anclas_post": len(pos), "anclas_post_NE": sum(est[x][0] == "NE" for x in pos),
         "senal_en_ventana_evaluable_no_concluyente": "" if cat != "NE" else
         ",".join(hms(x) for x in dur + pos if con(x))}
    if a is not None:
        g = est[a][1]
        alfa = cfg.split("_")[-1]
        comp = []
        if cfg != "HEUR" and g["IF_" + alfa]:
            comp.append("IF")
        if (cfg == "HEUR" or cfg.startswith("HIB")) and g["heur"]:
            comp.append(g["heur"])
        r.update({"primera_window_end": iso(a), "desde_inicio_generador_s": r1(a - m["gen_ini"]),
                  "desde_primer_paquete_s": r1(a - m["atq_ini"]), "tras_fin_generador_s": r1(a - m["gen_fin"]),
                  "componente": "+".join(comp),
                  "accion_propuesta": (g["accion_HIB_" + alfa] if cfg.startswith("HIB")
                                       else ("LIMIT" if cfg.startswith("IF") else g["heur_accion"])),
                  "score_samples": round(g["score"], 6), "heuristico": g["heur"]})
    return r


# ----------------------------------------------------------------------------- respuesta del 05-oct
def feed_05oct() -> list[dict]:
    runs = {}
    for linea in open(EVID / "cron-publicar-feed-ejecuciones-2600-2800.txt", encoding="utf-8"):
        n, t = linea.split()
        runs[int(n)] = ep(t)
    out = []
    for linea in open(EVID / "publicar-log-lineas-2600-2800.txt", encoding="utf-8"):
        n, js = linea.strip().split(None, 1)
        n = int(n)
        if n < LINEA_DESFASE or n + 1 not in runs:
            continue
        d = json.loads(js.strip().lstrip("\x00 "))
        out.append({"linea_publicar_log": n, "ejecucion_cron": n + 1, "publicado": runs[n + 1],
                    "entradas": d["entradas"], "limit": d["limit"], "block": d["block"],
                    "revisar_humano": ",".join(d["revisar_humano"])})
    return out


def efecto_pcap(info: dict, fam: str, m: dict) -> dict:
    tgt = "10.10.10.20" if fam == "e3" else "10.10.30.10"
    pk = [p for p in info["paquetes"] if m["gen_ini"] <= p.timestamp <= m["gen_fin"] + 1]
    if fam == "e3":
        q = sum(1 for p in pk if p.src_ip == KALI and p.dst_ip == tgt and p.protocol == 17)
        r = sum(1 for p in pk if p.src_ip == tgt and p.dst_ip == KALI and p.protocol == 17)
        return {"envios": q, "respuestas": r, "tipo": "consultas DNS / respuestas"}
    s = sum(1 for p in pk if p.src_ip == KALI and p.dst_ip == tgt and p.protocol == 6
            and p.tcp_flags & SYN and not p.tcp_flags & ACK)
    sa = sum(1 for p in pk if p.src_ip == tgt and p.dst_ip == KALI and p.protocol == 6
             and p.tcp_flags & SYN and p.tcp_flags & ACK)
    rst = sum(1 for p in pk if p.src_ip == tgt and p.dst_ip == KALI and p.protocol == 6 and p.tcp_flags & 0x04)
    return {"envios": s, "respuestas": sa, "rst": rst, "tipo": "SYN de la Kali / SYN-ACK del destino"}


def nunca_bloquear(ruta: Path) -> set[str]:
    """NUNCA_BLOQUEAR_POR_DEFECTO de publicar_feed.py leido sin importarlo (sus dependencias no estan en la copia)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for n in arbol.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "NUNCA_BLOQUEAR_POR_DEFECTO" for t in n.targets):
            return set(ast.literal_eval(n.value))
    raise ValueError("NUNCA_BLOQUEAR_POR_DEFECTO no encontrado")


# ----------------------------------------------------------------------------- principal
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--salida", type=Path, default=AQUI / "resultados")
    a = ap.parse_args()
    S = a.salida
    S.mkdir(parents=True, exist_ok=True)
    env = B.Entorno(a.datos)
    u = B.paso_umbrales(S)
    umbrales = {k: v["umbral_score_samples"] for k, v in u["umbrales"].items()}
    print("umbrales", umbrales, flush=True)

    auth = sesiones_auth()
    feed = feed_05oct()
    acum_todas = list(csv.DictReader(open(a.datos / "acum-20261005.csv", encoding="utf-8")))
    cubiertas = {int(round(ep(r["window_end_utc"]))) for r in acum_todas}
    acum_k = {int(round(ep(r["window_end_utc"]))): acotar(r) for r in acum_todas if r["entity_ip"] == KALI}
    claves = sorted(acum_k)
    sen_acum = dict(zip(claves, B.senales(env, [acum_k[k] for k in claves], umbrales)))

    contexto, cat_rows, equiv, compart, resp, por_ancla = [], [], {}, [], [], []
    ant_fin = None
    for i in EPISODIOS:
        fam = i[:2]
        d = a.datos / "piloto" / i
        orig = list(csv.DictReader(open(d / "features.csv", encoding="utf-8")))
        cs_orig, t0 = B.t0_de_features(orig)
        info = leer_episodio(env, d)
        info["dir"] = d
        m = marcas(info, fam, t0, auth)
        cs_real = max(info["pcap_ini"], cs_orig)
        filas = filas_replay(env, info, cs_real)
        rk = {int(round(ep(f["window_end_utc"]))): f for f in filas if f["entity_ip"] == KALI}
        kk = sorted(rk)
        sen_rep = dict(zip(kk, B.senales(env, [rk[k] for k in kk], umbrales)))
        a_list = anclas(m["gen_ini"], m["gen_fin"] + HORIZONTE_S)
        est = {"replay": estado_anclas("replay", a_list, rk, sen_rep, info=info, cs_real=cs_real),
               "acumulador": estado_anclas("acumulador", a_list, acum_k, sen_acum, cubiertas=cubiertas)}

        # equivalencia acumulador vs replay en ventanas comunes evaluables
        comunes = [x for x in a_list if est["replay"][x][0] == "fila" and x in acum_k]
        difs = {c: max((abs(float(rk[x][c]) - float(acum_k[x][c])) for x in comunes), default=None)
                for c in env.features}
        iguales = [x for x in comunes if all(abs(float(rk[x][c]) - float(acum_k[x][c])) <= TOL_EQUIV
                                             for c in env.features)]
        equiv[i] = {"ventanas_comunes": len(comunes), "identicas_28_variables": len(iguales),
                    "variables_distintas": {c: v for c, v in difs.items() if v and v > TOL_EQUIV},
                    "misma_senal": {cfg: sum(sen_rep[x][cfg] == sen_acum[x][cfg] for x in comunes) for cfg in CONFIGS}}
        # combinado: replay donde es evaluable, acumulador donde no (solo se usara si la equivalencia es total)
        est["replay+acumulador"] = {x: (est["replay"][x] if est["replay"][x][0] != "NE" else est["acumulador"][x])
                                    for x in a_list}

        dur_anclas = [x for x in a_list if m["gen_ini"] <= x <= m["gen_fin"]]
        contexto.append({
            "episodio": i, "familia": FAMILIAS[fam]["nombre"],
            "inicio_generador": iso(m["gen_ini"]), "fin_generador": iso(m["gen_fin"]),
            "duracion_generador_s": r1(m["gen_fin"] - m["gen_ini"]),
            "primer_paquete_ataque": iso(m["atq_ini"]), "ultimo_paquete_ataque": iso(m["atq_fin"]),
            "fin_generador_menos_ultimo_paquete_s": round(m["gen_fin"] - m["atq_fin"], 3),
            "paquetes_ataque": m["atq_paquetes"],
            "T0_features_Tsf": iso(t0), "sesion_date_previa_auth": iso(m["tsf_sesion_date"]),
            "sesion_date_posterior_auth": iso(m["tef_sesion_date"]),
            "pcap_desde": iso(info["pcap_ini"]), "pcap_hasta": iso(info["pcap_fin"]),
            "eve_recorte_desde": iso(cs_orig), "eve_primer_evento": iso(info["eve_ini"]),
            "eve_ultimo_evento": iso(info["eve_fin"]),
            "historia_antes_inicio_s": r1(m["gen_ini"] - cs_real),
            "datos_tras_fin_s": r1(info["pcap_fin"] - m["gen_fin"]),
            "hueco_con_episodio_anterior_s": r1(info["pcap_ini"] - ant_fin) if ant_fin else "",
            "primera_ventana_evaluable_replay": iso(math.ceil((cs_real + HORIZONTE_S) / PASO_S) * PASO_S),
            "anclas_durante": len(dur_anclas),
            "anclas_durante_evaluables_replay": sum(est["replay"][x][0] != "NE" for x in dur_anclas),
            "anclas_durante_evaluables_acumulador": sum(est["acumulador"][x][0] != "NE" for x in dur_anclas),
            "duplicados_espejo": info["dups"]})
        ant_fin = info["pcap_fin"]

        for fuente, e in est.items():
            for cfg in CONFIGS:
                cat_rows.append({"fuente": fuente, "episodio": i, "familia": FAMILIAS[fam]["nombre"],
                                 "configuracion": cfg, **categoria(e, m, cfg)})
            for alfa in ALFAS:
                ev = [e[x][1] for x in dur_anclas if e[x][0] == "fila"]
                compart.append({"fuente": fuente, "episodio": i, "alfa": alfa,
                                "ventanas_durante_evaluables_con_fila": len(ev),
                                "ambos": sum(g["IF_" + alfa] and g["HEUR"] for g in ev),
                                "solo_IF": sum(g["IF_" + alfa] and not g["HEUR"] for g in ev),
                                "solo_heur": sum(g["HEUR"] and not g["IF_" + alfa] for g in ev),
                                "ninguno": sum(not g["HEUR"] and not g["IF_" + alfa] for g in ev)})
        for x in a_list:
            fila = {"episodio": i, "window_end_utc": iso(x), "fase": "durante" if x <= m["gen_fin"] else "posterior",
                    "desde_inicio_generador_s": r1(x - m["gen_ini"])}
            for fuente in ("replay", "acumulador"):
                st, g = est[fuente][x]
                fila[f"{fuente}_estado"] = st
                fila[f"{fuente}_score"] = round(g["score"], 6) if g else ""
                for cfg in CONFIGS:
                    fila[f"{fuente}_{cfg}"] = int(g[cfg]) if g else ""
                fila[f"{fuente}_heuristico"] = g["heur"] if g else ""
            por_ancla.append(fila)

        # cadena de respuesta (solo evidencia del 05-oct; motor de entonces, no el IF limpio)
        en_ep = [f for f in feed if m["gen_ini"] - 60 <= f["publicado"] <= m["gen_fin"] + 60]
        pulls = [s for s in auth if m["gen_ini"] <= s["ini"] <= m["gen_fin"] and 36 <= datetime.fromtimestamp(
            s["ini"], timezone.utc).second < 40]
        resp.append({"episodio": i, **{"efecto_" + k: v for k, v in efecto_pcap(info, fam, m).items()},
                     "feed_publicado_en_[ini-60,fin+60]": " | ".join(
                         f"{hms(f['publicado'])[:8]} L{f['limit']}/B{f['block']}" + (f" rev:{f['revisar_humano']}" if f["revisar_humano"] else "")
                         for f in en_ep),
                     "lecturas_relay_durante": " ".join(hms(s["ini"])[:8] for s in pulls)})
        print(i, "listo", flush=True)

    # ------------------------------------------------------------------ tablas
    equivalente_total = all(e["identicas_28_variables"] == e["ventanas_comunes"] for e in equiv.values())
    fuentes = ("replay", "acumulador") + (("replay+acumulador",) if equivalente_total else ())
    cat_rows = [r for r in cat_rows if r["fuente"] in fuentes]
    compart = [r for r in compart if r["fuente"] in fuentes]
    escribir_csv(S / "contexto-episodios.csv", contexto)
    escribir_csv(S / "categorias-episodio.csv", cat_rows, list(dict.fromkeys(k for r in cat_rows for k in r)))
    escribir_csv(S / "senales-compartidas-durante.csv", compart)
    escribir_csv(S / "anclas-por-episodio.csv.gz", por_ancla)
    escribir_csv(S / "respuesta-05oct-por-episodio.csv", resp)
    escribir_csv(S / "feed-05oct-por-minuto.csv",
                 [dict(f, publicado=iso(f["publicado"])) for f in feed
                  if ep("2026-10-05T20:15:00+00:00") <= f["publicado"] <= ep("2026-10-05T21:00:00+00:00")])
    guardar_json(S / "equivalencia-acumulador.json", {
        "criterio": "28 variables identicas (|dif| <= 1e-9) en todas las ventanas comunes evaluables de 10.10.20.30",
        "equivalente_total": equivalente_total,
        "uso": "tabla complementaria replay+acumulador" if equivalente_total else "solo sensibilidad",
        "episodios": equiv})

    tablas = {}
    for fuente in fuentes:
        t = {}
        for fam in ("e3", "e4", "e1"):
            eps = [x for x in EPISODIOS if x.startswith(fam)]
            filas_f = [r for r in cat_rows if r["fuente"] == fuente and r["episodio"] in eps]
            evaluables = sorted({r["episodio"] for r in filas_f if r["evaluable_durante"]})
            t[fam] = {"evaluables": evaluables,
                      "no_evaluables": sorted(set(eps) - set(evaluables)),
                      **{cfg: sum(1 for r in filas_f if r["configuracion"] == cfg and r["episodio"] in evaluables
                                  and r["categoria"] == "D") for cfg in CONFIGS}}
        tablas[fuente] = t
    guardar_json(S / "tabla8-r2.json", {"celda": "episodios con deteccion durante la ejecucion / episodios evaluables",
                                        "principal": "replay", "tablas": tablas,
                                        "complementaria_publicable": equivalente_total})

    def md(fuente: str) -> list[str]:
        t = tablas[fuente]
        out = ["| Familia | Episodios evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |",
               "|---|---|---|---|---|---|---|"]
        tot = {c: 0 for c in CONFIGS}
        n_tot = 0
        for fam in ("e3", "e4", "e1"):
            n = len(t[fam]["evaluables"])
            n_tot += n
            celdas = [f"{t[fam][c]}/{n}" if n else "—" for c in CONFIGS]
            for c in CONFIGS:
                tot[c] += t[fam][c]
            out.append(f"| {FAMILIAS[fam]['nombre']} | {n} de 3 | " + " | ".join(celdas) + " |")
        out.append(f"| **Total** | **{n_tot} de 9** | " + " | ".join(
            f"**{tot[c]}/{n_tot}**" if n_tot else "—" for c in CONFIGS) + " |")
        out.append("| Fuerza bruta HTTP | 0 (no ejecutada) | — | — | — | — | — |")
        return out

    lineas = ["# Tabla 8 r2 — detección durante la ejecución (generada por evaluar_r2.py)", "",
              "Celda: episodios con señal de 10.10.20.30 en una ventana evaluable con window_end entre el inicio y el",
              "fin del generador, sobre los episodios cuyas ventanas durante el ataque son **todas** evaluables.", "",
              "## Principal: replay con historia real", ""] + md("replay")
    lineas += ["", "## Sensibilidad: filas del acumulador en vivo (extractor del 05-oct + acotación exacta)", ""] + md("acumulador")
    if equivalente_total:
        lineas += ["", "## Complementaria: replay + acumulador (equivalencia verificada)", ""] + md("replay+acumulador")
    else:
        lineas += ["", "La tabla combinada replay + acumulador **no se publica**: el acumulador no es equivalente al",
                   "replay en todas las ventanas comunes (`equivalencia-acumulador.json`)."]
    lineas += ["", "## Categoría por episodio y configuración", "",
               "D durante, P posterior (≤ 60 s tras el fin), N sin detección, NE no evaluable. Entre paréntesis, window_end",
               "de la primera señal menos el inicio del generador (no es el instante de emisión).", "",
               "| Fuente | Episodio | IF 0,05 | IF 0,03 | Heur. | Híb. 0,05 | Híb. 0,03 |", "|---|---|---|---|---|---|---|"]
    for fuente in ("replay", "acumulador"):
        for i in EPISODIOS:
            cel = []
            for cfg in CONFIGS:
                r = next(x for x in cat_rows if x["fuente"] == fuente and x["episodio"] == i and x["configuracion"] == cfg)
                s = r["categoria"]
                if r["categoria"] in ("D", "P"):
                    s += f" ({r['desde_inicio_generador_s']:g} s)"
                elif r["senal_en_ventana_evaluable_no_concluyente"]:
                    s += " (señal parcial)"
                cel.append(s)
            lineas.append(f"| {fuente} | {i} | " + " | ".join(cel) + " |")
    (S / "TABLA8-r2.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------ ventanas de la Tabla 7
    vent = B.paso_ventanas(env, S, umbrales)
    nunca = nunca_bloquear(env.rutas_codigo["engine/publicar_feed.py"])
    excl = [ipaddress.ip_network(t, strict=False) for t in B.EXCLUIR.split(",")]
    with gzip.open(S / "ventanas-predicciones.csv.gz", "rt", encoding="utf-8") as f:
        pred = list(csv.DictReader(f))
    y = np.array([int(r["etiqueta"]) for r in pred])
    verif, fp_clase = {}, {}
    anterior = json.loads((ANTERIOR / "resultados/ventanas-metricas.json").read_text(encoding="utf-8"))
    for cfg in CONFIGS:
        for modo, col in (("principal", cfg), ("operativa_motor", "oper_" + cfg)):
            p = np.array([int(r[col]) for r in pred])
            mm = B.metricas(y, p)
            prev = anterior[modo][cfg]
            verif[f"{modo}/{cfg}"] = {**mm, "igual_a_version_anterior": all(
                mm[k] == prev[k] for k in ("TP", "FP", "TN", "FN"))}
        c = Counter()
        for r in pred:
            if r["etiqueta"] == "0" and r[cfg] == "1":
                ipx = r["entity_ip"]
                if ipx in nunca:
                    c["NUNCA_BLOQUEAR (senal sin medida)"] += 1
                elif any(ipaddress.ip_address(ipx) in n for n in excl):
                    c["--excluir del motor (no se evaluaria en vivo)"] += 1
                elif ipx == KALI:
                    c["10.10.20.30 normal incierta"] += 1
                else:
                    c["medida aplicable (LIMIT/BLOCK posible)"] += 1
        fp_clase[cfg] = dict(c)
    assert all(v["igual_a_version_anterior"] for v in verif.values())
    guardar_json(S / "ventanas-verificacion-r2.json", {
        "fuente": "ventanas-predicciones.csv.gz (recalculado aqui) contra ../aporte-componentes-2026-10-26/resultados/ventanas-metricas.json",
        "metricas": verif, "falsas_alarmas_por_tipo_de_entidad": fp_clase,
        "nunca_bloquear_vigente": sorted(nunca)})

    # ------------------------------------------------------------------ manifiesto
    entradas = {f"piloto/{i}/{p.name}": sha256(p) for i in EPISODIOS
                for p in sorted((a.datos / "piloto" / i).iterdir()) if p.suffix in (".pcap", ".json", ".csv")}
    entradas["acum-20261005.csv"] = sha256(a.datos / "acum-20261005.csv")
    for rel, p in env.rutas_codigo.items():
        entradas["cyberflow/scripts/" + rel] = sha256(p)
    propios = {str(p.relative_to(AQUI)).replace("\\", "/"): sha256(p)
               for p in sorted(AQUI.rglob("*")) if p.is_file() and p.name != "MANIFIESTO-R2.json"
               and "__pycache__" not in p.parts}
    guardar_json(AQUI / "MANIFIESTO-R2.json", {
        "generado_utc": datetime.now(timezone.utc).isoformat(), "entradas_externas_sha256": entradas,
        "archivos_sha256": propios,
        "entorno": {"python": platform.python_version(), "sklearn": __import__("sklearn").__version__,
                    "numpy": np.__version__}})
    print(json.dumps({"equivalente_total": equivalente_total, "tablas": tablas}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
