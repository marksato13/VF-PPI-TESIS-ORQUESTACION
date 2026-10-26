#!/usr/bin/env python3
"""Aporte de los componentes del detector hibrido de CyberFlow (seccion 4.2).

Offline y de solo lectura: no toca el sensor, sus reglas ni sus artefactos.

Pasos (cada uno escribe en --salida):
  umbrales    recalcula los umbrales alfa 0,03/0,05 sobre las 65 553 ventanas de
              validacion y comprueba que coinciden con los de 4.1
  original    reproduce los veredictos historicos de la bateria del 05-oct
              (modelo if_recalibrado_2026_09 + heuristicos 2026-09-30.1 con DNS 0,45)
              desde los features.csv guardados, y los compara con orq_results.csv
  episodios   re-procesa los PCAP de los 9 episodios con el procesamiento del
              motor vigente y evalua IF 0,05/0,03, heuristicos e hibrido
  ventanas    metricas por ventana sobre la poblacion de la Tabla 7 (65 505)
  consolidar  Tabla 8, complementariedad y resumen
  todo        todo lo anterior

    python evaluar_componentes.py --datos DIR --salida resultados todo

DIR contiene (copia de solo lectura del sensor):
  piloto/{e3,e4,e1}-r{1,2,3}/{live-*.pcap,eve.json,features.csv}, piloto/BASE/
  cyberflow/scripts/{engine,features}/..., cyberflow/configs/features/multilayer-v2.json
  cyberflow/artifacts/preliminar/limpio-2026-10/{if_limpio_2026_10_desplegable.joblib,...}
  cyberflow/artifacts/preliminar/{if_recalibrado_desplegable.joblib,manifest-if-recalibrado.json}
  cyberflow/artifacts/aprendizaje/{oro/oro.csv,ataques/ataques-nota-M.csv}
  acum-20261005.csv (filas del acumulador en vivo, 05-oct 19:40-20:55 UTC)
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import ipaddress
import json
import math
import platform
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
CALIB = AQUI.parent.parent / "4.1-modelos" / "calibracion-alfa-2026-10-24"
COMP = AQUI.parent.parent / "4.1-modelos" / "comparacion-metodos-2026-10-25"
ANTECEDENTE = AQUI / "antecedente"

ALFAS = ("0.05", "0.03")
UMBRAL_ESPERADO = {"0.03": -0.5898535710336618, "0.05": -0.5694578968203694}
UMBRAL_DESPLEGADO = -0.5693969936322356
SHA_MODELO = "df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60"
KALI = "10.10.20.30"
RED = ipaddress.ip_network("10.10.0.0/16")
PROTOCOLOS_EXCLUIDOS = {112, 240}
# --excluir del motor vigente (24-oct). No afecta a la Kali; solo a las senales no atribuibles.
EXCLUIR = ("10.10.60.11/32,10.10.10.30/32,10.10.60.2/32,10.10.60.3/32,10.10.60.10/32,"
           "10.10.60.20/32,10.10.60.21/32,10.10.60.30/32,10.10.60.40/32,10.10.60.41/32,10.10.60.50/32")
AUTH_MIN_REQ, AUTH_MIN_RATIO = 5, 0.8          # motor_decision.py
HORIZONTE_S = 60                                # variable mas larga (60 s)
FAMILIAS = {
    "e3": {"nombre": "DNS inusual (alta entropia)", "mitre": "T1568.002",
           "ataque": lambda p: p.protocol == 17 and p.dst_ip == "10.10.10.20" and p.dst_port == 53},
    "e4": {"nombre": "Inundacion HTTP", "mitre": "T1498/T1499",
           "ataque": lambda p: p.protocol == 6 and p.dst_ip == "10.10.30.10" and p.dst_port == 80},
    "e1": {"nombre": "Escaneo de puertos", "mitre": "T1046",
           "ataque": lambda p: p.protocol == 6 and p.dst_ip == "10.10.30.10"},
}
EPISODIOS = [f"{f}-r{r}" for f in ("e3", "e4", "e1") for r in (1, 2, 3)]
CONFIGS = ("IF_0.05", "IF_0.03", "HEUR", "HIB_0.05", "HIB_0.03")
EVIDENCIA = ("packet_count_10s", "flow_attempt_count_30s", "http_request_count_60s",
             "dns_query_count_60s", "unique_dst_port_ratio_30s", "syn_completion_ratio_10s",
             "dns_nxdomain_ratio_60s", "unique_dns_name_ratio_60s", "http_auth_failure_ratio_60s")


# ----------------------------------------------------------------------------- utilidades
def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ep(s: str) -> float:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def iso(t: float | None) -> str:
    return "" if t is None else datetime.fromtimestamp(t, timezone.utc).isoformat()


def cargar_modulo(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


def escribir_csv(ruta: Path, filas: list[dict], campos: list[str] | None = None) -> None:
    campos = campos or list(filas[0].keys())
    op = gzip.open if ruta.suffix == ".gz" else open
    with op(ruta, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


def guardar_json(ruta: Path, obj) -> None:
    ruta.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


class Entorno:
    """Carga el codigo del sensor (copia) y los modelos una sola vez."""

    def __init__(self, datos: Path):
        self.datos = datos
        cf = datos / "cyberflow"
        sys.path.insert(0, str(cf / "scripts" / "features"))
        sys.path.insert(0, str(cf / "scripts" / "engine"))
        import extract_multilayer_v2 as v2  # noqa: E402
        import extract_multilayer_v3 as v3  # noqa: E402
        import heuristicos  # noqa: E402
        import joblib  # noqa: E402
        self.v2, self.v3, self.H, self.joblib = v2, v3, heuristicos, joblib
        esquema = json.loads((cf / "configs/features/multilayer-v2.json").read_text(encoding="utf-8"))
        self.features = tuple(i["name"] for i in sorted(esquema["features"], key=lambda i: i["order"]))
        assert self.features == v2.FEATURE_NAMES, "esquema != extractor (motor_decision.py aborta igual)"
        ruta = cf / "artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib"
        assert sha256(ruta) == SHA_MODELO, "el joblib no es el desplegado"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.pipe = joblib.load(ruta)
        self.avisos_carga = sorted({str(x.message)[:90] for x in w})
        self.rutas_codigo = {n: cf / "scripts" / n for n in (
            "engine/heuristicos.py", "engine/motor_decision.py", "engine/publicar_feed.py",
            "features/extract_multilayer_v2.py", "features/extract_multilayer_v3.py")}

    def score(self, filas: list[dict]) -> np.ndarray:
        if not filas:
            return np.zeros(0)
        X = np.array([[float(f[c] or 0) for c in self.features] for f in filas], dtype=float)
        return self.pipe.score_samples(X)

    def heur(self, fila: dict) -> dict | None:
        """heuristicos.evaluar + la regla heredada auth_failure_heuristic del motor."""
        v = self.H.evaluar(fila)
        if v is None and (float(fila.get("http_request_count_60s") or 0) >= AUTH_MIN_REQ
                          and float(fila.get("http_auth_failure_ratio_60s") or 0) >= AUTH_MIN_RATIO):
            v = {"heuristico": "auth_failure_heuristic", "accion": "BLOCK",
                 "motivo": "regla heredada del motor (>=5 req, >=80 % 401/403)"}
        return v


# ----------------------------------------------------------------------------- 1. umbrales
def paso_umbrales(salida: Path) -> dict:
    kali80 = set()
    with open(CALIB / "validacion-kali-80-excluidas.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            kali80.add((r["campaign_id"], r["entity_ip"], r["window_end_utc"]))
    ss, n_total, quitadas = [], 0, 0
    with gzip.open(CALIB / "datos-sensor/scores-validacion-65633.csv.gz", "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n_total += 1
            if (r["campaign_id"], r["entity_ip"], r["window_end_utc"]) in kali80:
                quitadas += 1
                continue
            ss.append(float(r["score_samples"]))
    ss = np.asarray(ss)
    res = {"n_validacion_total": n_total, "quitadas_kali": quitadas, "n_calibracion": int(ss.size),
           "orientacion": "score_samples: mayor = mas normal; puntuacion de anomalia = -score_samples",
           "operador": "senal si score_samples < umbral (estricto) <=> -score_samples > cuantil",
           "umbrales": {}}
    assert n_total == 65633 and quitadas == 80 and ss.size == 65553
    for a in ALFAS:
        q = float(np.quantile(-ss, 1 - float(a), method="linear"))
        u = -q
        res["umbrales"][a] = {"cuantil_menos_score": q, "umbral_score_samples": u,
                              "esperado_4_1": UMBRAL_ESPERADO[a], "dif": abs(u - UMBRAL_ESPERADO[a]),
                              "validacion_con_senal": int((ss < u).sum()),
                              "validacion_empates": int((ss == u).sum())}
        assert abs(u - UMBRAL_ESPERADO[a]) < 1e-12, (a, u)
    res["desplegado_referencia"] = UMBRAL_DESPLEGADO
    guardar_json(salida / "umbrales-verificados.json", res)
    return res


# ----------------------------------------------------------------------------- 2. original
def leer_orq() -> dict:
    """orq_results.csv del bastion -> veredicto original por episodio."""
    out = {}
    with open(ANTECEDENTE / "orq_results.csv", encoding="utf-8") as f:
        for linea in f:
            if not linea.startswith("e"):
                continue
            cf = linea.split("[RESULT ")[1].split("]")[0].split()
            d = dict(x.split("=") for x in cf[1:])
            out[cf[0]] = d
    return out


def t0_de_features(filas: list[dict]) -> tuple[float, float]:
    """capture_start = window_end - history_coverage (cobertura < 60); T0 = CS + 25 s (orq.sh/proc.sh)."""
    cs = {round(ep(x["window_end_utc"]) - float(x["history_coverage_s"]), 3)
          for x in filas if float(x["history_coverage_s"]) < 60}
    assert len(cs) == 1, cs
    c = cs.pop()
    return c, c + 25


def paso_original(env: Entorno, salida: Path) -> list[dict]:
    cf = env.datos / "cyberflow/artifacts/preliminar"
    mani = json.loads((cf / "manifest-if-recalibrado.json").read_text(encoding="utf-8"))
    cal = mani["detectors"]["if_recalibrado_2026_09"]["calibration"]
    assert cal["comparison"] == "score < threshold"
    umb, feats = float(cal["threshold"]), mani["feature_names"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pipe = env.joblib.load(cf / "if_recalibrado_desplegable.joblib")
    hv = cargar_modulo("heur_20260930", ANTECEDENTE / "heuristicos_2026-09-30.1_a6d287a.py")
    hv.UMBRALES_POR_DEFECTO["dns_entropy"]["min_unique_dns_name_ratio_60s"] = 0.45   # como score.py
    orq = leer_orq()
    filas_out = []
    for i in EPISODIOS:
        filas = list(csv.DictReader(open(env.datos / "piloto" / i / "features.csv", encoding="utf-8")))
        cs, t0 = t0_de_features(filas)
        k = sorted((x for x in filas if x["entity_ip"] == KALI), key=lambda x: x["window_end_utc"])
        X = np.array([[float(x.get(c) or 0) for c in feats] for x in k])
        sc = pipe.score_samples(X)
        mfirst = next((round(ep(x["window_end_utc"]) - t0, 1) for x, s in zip(k, sc)
                       if s < umb and ep(x["window_end_utc"]) >= t0), None)
        hname = hacc = hfirst = None
        for x in k:
            v = hv.evaluar(x)
            if v and ep(x["window_end_utc"]) >= t0:
                hname, hacc, hfirst = v["heuristico"], v["accion"], round(ep(x["window_end_utc"]) - t0, 1)
                break
        o = orq[i]
        rec = {
            "episodio": i, "capture_start": iso(cs), "T0": iso(t0), "ventanas_kali": len(k),
            "modelo_alertas": int((sc < umb).sum()), "modelo_primera_s": mfirst,
            "heur": hname, "accion": hacc, "heur_primera_s": hfirst,
            "orig_ventanas_kali": int(o["kaliwin"]), "orig_modelo_alertas": int(o["model_alerts"]),
            "orig_modelo_primera_s": None if o["model_first"] == "-" else float(o["model_first"]),
            "orig_heur": None if o["heur"] == "-" else o["heur"],
            "orig_heur_primera_s": None if o["heur_first"] == "-" else float(o["heur_first"]),
        }
        rec["coincide"] = (rec["ventanas_kali"] == rec["orig_ventanas_kali"]
                           and rec["modelo_alertas"] == rec["orig_modelo_alertas"]
                           and rec["modelo_primera_s"] == rec["orig_modelo_primera_s"]
                           and rec["heur"] == rec["orig_heur"]
                           and rec["heur_primera_s"] == rec["orig_heur_primera_s"])
        rec["det_modelo"] = mfirst is not None
        rec["det_heur"] = hname is not None
        rec["det_combinado"] = rec["det_modelo"] or rec["det_heur"]
        filas_out.append(rec)
    escribir_csv(salida / "reproduccion-original.csv", filas_out)
    resumen = {k: sum(r[k] for r in filas_out) for k in ("det_modelo", "det_heur", "det_combinado", "coincide")}
    resumen.update({"umbral_if_recalibrado_2026_09": umb, "heuristicos": "2026-09-30.1 (a6d287a) + dns unique 0,45 (score.py)"})
    guardar_json(salida / "reproduccion-original.json", {"resumen": resumen, "episodios": filas_out})
    return filas_out


# ----------------------------------------------------------------------------- 3. episodios
def procesar_pcap(env: Entorno, dir_ep: Path, historia_completa: bool):
    """Procesamiento del motor vigente sobre los PCAP + eve.json de un episodio."""
    v2, v3 = env.v2, env.v3
    contextos = []
    for ruta in sorted(dir_ep.glob("live-*.pcap")):
        for marca, trama in v2.iter_pcap_frames(ruta):
            c = v3.parse_con_contexto(marca, trama)
            if c is not None:
                contextos.append(c)
    n_tramas = len(contextos)
    utiles = [c for c in contextos if c.packet.protocol not in PROTOCOLOS_EXCLUIDOS]
    paquetes, dups = v3.deduplicar_espejo(utiles)
    obs = v2.attribute_packets(paquetes, RED)
    apps = v2.load_app_observations(dir_ep / "eve.json", RED)
    marcas = [o.timestamp for o in obs] + [a.timestamp for a in apps]
    primera = min(marcas)
    cs = primera - HORIZONTE_S if historia_completa else primera
    filas = v2.build_rows("replay-" + dir_ep.name, obs, apps, step_seconds=10, capture_start=cs)
    meta = {"tramas_ip": n_tramas, "plano_control_descartado": n_tramas - len(utiles),
            "duplicados_espejo": dups, "paquetes": len(paquetes), "observaciones_paquete": len(obs),
            "observaciones_app": len(apps), "primer_paquete": iso(min(p.timestamp for p in paquetes)),
            "ultimo_paquete": iso(max(p.timestamp for p in paquetes)), "primera_observacion": iso(primera),
            "capture_start_usado": iso(cs)}
    return filas, paquetes, meta


def senales(env: Entorno, filas: list[dict], umbrales: dict, guarda: bool = True,
            elegibilidad: bool = False) -> list[dict]:
    """Anota por ventana la senal de cada componente con la regla del motor."""
    sc = env.score(filas)
    out = []
    for f, s in zip(filas, sc):
        evaluada = (not elegibilidad) or bool(f["eligible_training"])
        sin_pk = float(f["packet_count_10s"]) == 0
        h = env.heur(f) if evaluada else None
        g = {"score": float(s), "evaluada": evaluada, "if_puntuado": evaluada and not (guarda and sin_pk),
             "heur": h["heuristico"] if h else "", "heur_accion": h["accion"] if h else "",
             "heur_motivo": h["motivo"] if h else ""}
        for a in ALFAS:
            g["IF_" + a] = bool(g["if_puntuado"] and s < umbrales[a])
            g["HIB_" + a] = bool(g["IF_" + a] or h)
            acc = [("BLOCK" if (h and h["accion"] == "BLOCK") else "LIMIT")] if g["HIB_" + a] else []
            g["accion_HIB_" + a] = acc[0] if acc else ""
        g["HEUR"] = bool(h)
        out.append(g)
    return out


def paso_episodios(env: Entorno, salida: Path, umbrales: dict) -> dict:
    excl = [ipaddress.ip_network(t, strict=False) for t in EXCLUIR.split(",")]
    registros, por_ventana, metas, fuera = [], [], {}, []
    for i in EPISODIOS:
        fam = i[:2]
        d = env.datos / "piloto" / i
        orig = list(csv.DictReader(open(d / "features.csv", encoding="utf-8")))
        cs_orig, t0 = t0_de_features(orig)
        res_var = {}
        for variante, hist, eleg in (("principal", True, False), ("historia_truncada", False, True)):
            filas, paquetes, meta = procesar_pcap(env, d, hist)
            ataque = sorted(p.timestamp for p in paquetes if p.src_ip == KALI and FAMILIAS[fam]["ataque"](p))
            t_ini, t_fin = ataque[0], ataque[-1]
            lim = t_fin + HORIZONTE_S
            sen = senales(env, filas, umbrales, guarda=True, elegibilidad=eleg)
            ventanas = []
            for f, g in zip(filas, sen):
                w = ep(f["window_end_utc"])
                atrib = f["entity_ip"] == KALI and t0 <= w <= lim
                ventanas.append({"f": f, "sen": g, "w": w, "atribuible": atrib})
                if variante == "principal":
                    por_ventana.append({
                        "episodio": i, "entity_ip": f["entity_ip"], "window_end_utc": f["window_end_utc"],
                        "t_desde_T0_s": round(w - t0, 1), "atribuible": int(atrib),
                        "history_coverage_s": f["history_coverage_s"], "packet_count_10s": f["packet_count_10s"],
                        "score_samples": round(g["score"], 6), "if_puntuado": int(g["if_puntuado"]),
                        "IF_0.05": int(g["IF_0.05"]), "IF_0.03": int(g["IF_0.03"]), "HEUR": int(g["HEUR"]),
                        "heuristico": g["heur"], "accion_heur": g["heur_accion"],
                        "HIB_0.05": int(g["HIB_0.05"]), "HIB_0.03": int(g["HIB_0.03"]),
                        **{c: f[c] for c in EVIDENCIA}})
                    if not atrib and t0 <= w <= lim and (g["IF_0.05"] or g["HEUR"]):
                        direccion = ipaddress.ip_address(f["entity_ip"])
                        fuera.append({"episodio": i, "entity_ip": f["entity_ip"], "window_end_utc": f["window_end_utc"],
                                      "excluida_en_motor": int(any(direccion in r for r in excl)),
                                      "IF_0.05": int(g["IF_0.05"]), "IF_0.03": int(g["IF_0.03"]),
                                      "heuristico": g["heur"]})
            ventanas.sort(key=lambda v: v["w"])
            atr = [v for v in ventanas if v["atribuible"]]
            res = {}
            for cfg in CONFIGS:
                hit = [v for v in atr if v["sen"][cfg]]
                if hit:
                    v = hit[0]
                    a = cfg.split("_")[-1]
                    comp = []
                    if cfg != "HEUR" and v["sen"]["IF_" + a]:
                        comp.append("IF")
                    if cfg in ("HEUR", "HIB_0.05", "HIB_0.03") and v["sen"]["heur"]:
                        comp.append(v["sen"]["heur"])
                    res[cfg] = {
                        "detectado": True, "ventanas_con_senal": len(hit), "ventanas_atribuibles": len(atr),
                        "primera_window_end": v["f"]["window_end_utc"], "lat_T0_s": round(v["w"] - t0, 1),
                        "lat_primer_paquete_s": round(v["w"] - t_ini, 1),
                        "antes_fin_ataque": v["w"] <= t_fin + 10,
                        "componente": "+".join(comp),
                        "accion": (v["sen"]["accion_HIB_" + a] if cfg.startswith("HIB")
                                   else ("LIMIT" if cfg.startswith("IF") else v["sen"]["heur_accion"])),
                        "score": round(v["sen"]["score"], 6),
                        "umbral": umbrales.get(a) if cfg != "HEUR" else None,
                        "heur_motivo": v["sen"]["heur_motivo"],
                        "history_coverage_s": v["f"]["history_coverage_s"],
                        "evidencia": {c: v["f"][c] for c in EVIDENCIA}}
                else:
                    res[cfg] = {"detectado": False, "ventanas_con_senal": 0, "ventanas_atribuibles": len(atr)}
            res_var[variante] = {"res": res, "meta": meta, "t_ini": t_ini, "t_fin": t_fin,
                                 "n_paquetes_ataque": len(ataque)}
        p = res_var["principal"]
        metas[i] = {"familia": FAMILIAS[fam]["nombre"], "mitre": FAMILIAS[fam]["mitre"],
                    "origen": KALI, "destino": "10.10.10.20:53/udp" if fam == "e3" else
                    ("10.10.30.10:80/tcp" if fam == "e4" else "10.10.30.10 tcp/1-1000"),
                    "T0_orquestador": iso(t0), "capture_start_original": iso(cs_orig),
                    "primer_paquete_ataque": iso(p["t_ini"]), "ultimo_paquete_ataque": iso(p["t_fin"]),
                    "duracion_ataque_s": round(p["t_fin"] - p["t_ini"], 1),
                    "paquetes_ataque": p["n_paquetes_ataque"],
                    "intervalo_atribucion": [iso(t0), iso(p["t_fin"] + HORIZONTE_S)],
                    "procesamiento": p["meta"]}
        for cfg in CONFIGS:
            r = p["res"][cfg]
            s = res_var["historia_truncada"]["res"][cfg]
            registros.append({
                "episodio": i, "familia": FAMILIAS[fam]["nombre"], "configuracion": cfg,
                "detectado": "si" if r["detectado"] else "no",
                "primera_senal_window_end": r.get("primera_window_end", ""),
                "latencia_desde_T0_s": r.get("lat_T0_s", ""),
                "latencia_desde_primer_paquete_s": r.get("lat_primer_paquete_s", ""),
                "componente": r.get("componente", ""), "accion": r.get("accion", ""),
                "ventanas_con_senal": r["ventanas_con_senal"], "ventanas_atribuibles": r["ventanas_atribuibles"],
                "score_samples": r.get("score", ""), "umbral": r.get("umbral", "") or "",
                "heuristico_motivo": r.get("heur_motivo", ""),
                "history_coverage_s": r.get("history_coverage_s", ""),
                "evidencia": json.dumps(r.get("evidencia", {}), ensure_ascii=False),
                "detectado_sensibilidad_historia_truncada": "si" if s["detectado"] else "no",
                "origen_resultado": "recalculado offline (replay PCAP 05-oct, if_limpio_2026_10, heuristicos 2026-10-06.2)"})
    escribir_csv(salida / "episodios-registro.csv", registros)
    escribir_csv(salida / "episodios-ventanas.csv.gz", por_ventana)
    escribir_csv(salida / "episodios-senales-no-atribuibles.csv",
                 fuera or [{"episodio": "", "entity_ip": "", "window_end_utc": "", "excluida_en_motor": "",
                            "IF_0.05": "", "IF_0.03": "", "heuristico": ""}])
    guardar_json(salida / "episodios-metadatos.json", metas)
    return {"registros": registros, "metas": metas, "no_atribuibles": fuera}


def paso_control_base(env: Entorno, salida: Path, umbrales: dict) -> dict:
    """Control normal del mismo procesamiento (BASE, 05-oct antes de la bateria). No comparable con la Tabla 7."""
    excl = [ipaddress.ip_network(t, strict=False) for t in EXCLUIR.split(",")]
    filas, paquetes, meta = procesar_pcap(env, env.datos / "piloto" / "BASE", True)
    sen = senales(env, filas, umbrales)
    def dentro(ip):
        return any(ipaddress.ip_address(ip) in r for r in excl)
    w = [(f, g) for f, g in zip(filas, sen) if not dentro(f["entity_ip"])]
    p0 = min(p.timestamp for p in paquetes)
    p1 = max(p.timestamp for p in paquetes)
    # solo ventanas con la historia real completa (>= 60 s de PCAP antes) y sin el borde final
    w = [(f, g) for f, g in w if p0 + HORIZONTE_S <= ep(f["window_end_utc"]) <= p1]
    res = {"duracion_pcap_s": round(p1 - p0, 1), "desde": iso(p0), "hasta": iso(p1),
           "criterio_ventana": "entidad no excluida por el motor; window_end en [primer paquete + 60 s, ultimo paquete]",
           "criterio_falsa_alarma": "cualquier senal del componente en una ventana del control",
           "ventanas_elegibles": len(w), "entidades": len({f["entity_ip"] for f, _ in w}),
           "kali_en_control": sum(1 for f, _ in w if f["entity_ip"] == KALI), "procesamiento": meta}
    for cfg in CONFIGS:
        n = sum(1 for _, g in w if g[cfg])
        res[cfg] = {"falsas_alarmas": n, "tasa": n / len(w) if w else None,
                    "entidades": sorted({f["entity_ip"] for f, g in w if g[cfg]})}
    guardar_json(salida / "control-base-05oct.json", res)
    return res


def paso_contraste_acumulador(env: Entorno, salida: Path, umbrales: dict, ep_meta: dict) -> dict:
    """Ventanas que el acumulador escribio EN VIVO el 05-oct (codigo de esa fecha) vs replay."""
    ruta = env.datos / "acum-20261005.csv"
    acum = [r for r in csv.DictReader(open(ruta, encoding="utf-8")) if r["entity_ip"] == KALI]
    sen = senales(env, acum, umbrales)
    vent = {}
    with gzip.open(salida / "episodios-ventanas.csv.gz", "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["entity_ip"] == KALI:
                vent[(r["episodio"], r["window_end_utc"])] = r
    out = {"fuente": "artifacts/linea-base/multilayer-v3.csv (acumulador en vivo), filas de 05-oct 19:40-20:55",
           "sha256_extracto": sha256(ruta), "episodios": {}}
    for i, m in ep_meta.items():
        t0 = ep(m["T0_orquestador"])
        lim = ep(m["intervalo_atribucion"][1])
        sel = [(r, g) for r, g in zip(acum, sen) if t0 <= ep(r["window_end_utc"]) <= lim]
        e = {"ventanas_acumulador": len(sel)}
        for cfg in CONFIGS:
            hit = [ep(r["window_end_utc"]) - t0 for r, g in sel if g[cfg]]
            e[cfg] = {"detectado": bool(hit), "lat_T0_s": round(min(hit), 1) if hit else None}
        comunes = [(r, vent[(i, r["window_end_utc"])]) for r, _ in sel if (i, r["window_end_utc"]) in vent]
        e["ventanas_comunes_con_replay"] = len(comunes)
        dif = {}
        for c in ("packet_count_10s", "flow_attempt_count_30s", "http_request_count_60s", "dns_query_count_60s"):
            dd = [abs(float(a[c]) - float(b[c])) for a, b in comunes]
            dif[c] = {"max_abs": max(dd) if dd else None, "iguales": sum(x == 0 for x in dd)}
        e["diferencias_replay_vs_vivo"] = dif
        out["episodios"][i] = e
    guardar_json(salida / "contraste-acumulador-vivo.json", out)
    return out


# ----------------------------------------------------------------------------- 4. ventanas
def leer_poblacion(env: Entorno):
    base = env.datos / "cyberflow/artifacts/aprendizaje"
    oro = list(csv.DictReader(open(base / "oro/oro.csv", encoding="utf-8")))
    atq = list(csv.DictReader(open(base / "ataques/ataques-nota-M.csv", encoding="utf-8")))
    for r in oro:
        r["_etiqueta"] = 0
    for r in atq:
        r["_etiqueta"] = 1
    return oro, atq


def metricas(y: np.ndarray, p: np.ndarray) -> dict:
    tp = int(((p == 1) & (y == 1)).sum()); fp = int(((p == 1) & (y == 0)).sum())
    tn = int(((p == 0) & (y == 0)).sum()); fn = int(((p == 0) & (y == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (tp and prec + rec) else 0.0
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn, "precision": prec, "recall": rec, "F1": f1,
            "FPR": fp / (fp + tn) if fp + tn else float("nan"), "n": int(y.size)}


def paso_ventanas(env: Entorno, salida: Path, umbrales: dict) -> dict:
    oro, atq = leer_poblacion(env)
    filas = oro + atq
    claves = [(r["campaign_id"], r["entity_ip"], r["window_end_utc"]) for r in filas]
    aud = {"n_oro": len(oro), "n_ataques": len(atq), "n_total": len(filas),
           "claves_unicas": len(set(claves)), "duplicados": len(claves) - len(set(claves)),
           "solape_oro_ataques": len({c for c in claves[:len(oro)]} & {c for c in claves[len(oro):]}),
           "kali_en_oro": sum(r["entity_ip"] == KALI for r in oro)}
    # puntuaciones y etiquetas de la Tabla 7 (4.1) para comprobar igualdad de claves y etiquetas
    t7 = {}
    with gzip.open(COMP / "salidas/puntuaciones-IF.csv.gz", "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["conjunto"] in ("prueba_normal", "ataque"):
                t7[(r["campaign_id"], r["entity_ip"], r["window_end_utc"])] = (int(r["etiqueta"]), float(r["puntuacion_anomalia"]))
    y = np.array([r["_etiqueta"] for r in filas])
    ss = env.score(filas)
    aud["claves_iguales_tabla7"] = set(claves) == set(t7)
    aud["etiquetas_iguales_tabla7"] = all(t7[c][0] == e for c, e in zip(claves, y))
    aud["max_abs_dif_score_vs_tabla7"] = float(max(abs(-t7[c][1] - s) for c, s in zip(claves, ss)))
    aud["predicciones_cubren_todas"] = True
    sin_pk = np.array([float(r["packet_count_10s"]) == 0 for r in filas])
    eleg = np.array([str(r["eligible_training"]) == "True" for r in filas])
    aud["sin_paquetes_10s"] = {"oro": int(sin_pk[y == 0].sum()), "ataques": int(sin_pk[y == 1].sum())}
    aud["no_elegibles"] = {"oro": int((~eleg)[y == 0].sum()), "ataques": int((~eleg)[y == 1].sum())}
    hs = [env.heur(r) for r in filas]
    heur = np.array([h is not None for h in hs])
    kali = np.array([r["entity_ip"] == KALI for r in filas]) & (y == 0)
    preds = {"HEUR": heur}
    for a in ALFAS:
        preds["IF_" + a] = ss < umbrales[a]
        preds["HIB_" + a] = preds["IF_" + a] | heur
    oper = {"HEUR": heur & eleg}
    for a in ALFAS:
        oper["IF_" + a] = (ss < umbrales[a]) & eleg & ~sin_pk
        oper["HIB_" + a] = oper["IF_" + a] | oper["HEUR"]
    res = {"auditoria": aud, "principal": {}, "operativa_motor": {}, "sensibilidad_sin_74_kali": {},
           "fp_en_74_kali": {}, "heuristicos_disparados": {}}
    for cfg in CONFIGS:
        res["principal"][cfg] = metricas(y, preds[cfg].astype(int))
        res["operativa_motor"][cfg] = metricas(y, oper[cfg].astype(int))
        m = ~kali
        res["sensibilidad_sin_74_kali"][cfg] = metricas(y[m], preds[cfg][m].astype(int))
        res["fp_en_74_kali"][cfg] = int(preds[cfg][kali].sum())
    for etq, nombre in ((0, "oro"), (1, "ataques")):
        c = {}
        for h, e in zip(hs, y):
            if h is not None and e == etq:
                c[h["heuristico"]] = c.get(h["heuristico"], 0) + 1
        res["heuristicos_disparados"][nombre] = c
    for a in ALFAS:
        i_ = preds["IF_" + a]
        res["solape_ataques_" + a] = {"ambos": int((i_ & heur & (y == 1)).sum()),
                                      "solo_IF": int((i_ & ~heur & (y == 1)).sum()),
                                      "solo_heur": int((~i_ & heur & (y == 1)).sum()),
                                      "ninguno": int((~i_ & ~heur & (y == 1)).sum())}
        res["solape_falsas_alarmas_" + a] = {"ambos": int((i_ & heur & (y == 0)).sum()),
                                             "solo_IF": int((i_ & ~heur & (y == 0)).sum()),
                                             "solo_heur": int((~i_ & heur & (y == 0)).sum())}
    # comprobacion contra la Tabla 7 (4.1)
    esperado = {"0.03": (54, 1723), "0.05": (54, 2955)}
    for a, (tp, fp) in esperado.items():
        m = res["principal"]["IF_" + a]
        assert (m["TP"], m["FP"]) == (tp, fp), ("IF no coincide con la Tabla 7", a, m)
    pred_filas = []
    for k, r in enumerate(filas):
        pred_filas.append({"campaign_id": r["campaign_id"], "entity_ip": r["entity_ip"],
                           "window_end_utc": r["window_end_utc"], "etiqueta": int(y[k]),
                           "kali_normal_incierta": int(kali[k]), "eligible_training": int(eleg[k]),
                           "packet_count_10s": r["packet_count_10s"], "score_samples": repr(float(ss[k])),
                           **{c: int(preds[c][k]) for c in CONFIGS},
                           **{"oper_" + c: int(oper[c][k]) for c in CONFIGS},
                           "heuristico": hs[k]["heuristico"] if hs[k] else ""})
    escribir_csv(salida / "ventanas-predicciones.csv.gz", pred_filas)
    guardar_json(salida / "ventanas-metricas.json", res)
    return res


# ----------------------------------------------------------------------------- 5. consolidar
def pct(x):
    return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.2f} %"


def paso_consolidar(salida: Path, umbrales: dict, original: list[dict], epis: dict,
                    vent: dict, base: dict, contraste: dict, env: Entorno) -> dict:
    reg = epis["registros"]
    det = {(r["episodio"], r["configuracion"]): r["detectado"] == "si" for r in reg}
    filas_t8 = []
    for fam in ("e3", "e4", "e1"):
        eps = [e for e in EPISODIOS if e.startswith(fam)]
        fila = {"Familia": FAMILIAS[fam]["nombre"], "Episodios evaluados": len(eps)}
        for cfg, col in zip(CONFIGS, ("IF 0,05", "IF 0,03", "Heuristicos", "Hibrido 0,05", "Hibrido 0,03")):
            fila[col] = f"{sum(det[(e, cfg)] for e in eps)}/{len(eps)}"
        filas_t8.append(fila)
    tot = {"Familia": "Total", "Episodios evaluados": len(EPISODIOS)}
    for cfg, col in zip(CONFIGS, ("IF 0,05", "IF 0,03", "Heuristicos", "Hibrido 0,05", "Hibrido 0,03")):
        tot[col] = f"{sum(det[(e, cfg)] for e in EPISODIOS)}/{len(EPISODIOS)}"
    filas_t8.append(tot)
    filas_t8.append({"Familia": "Fuerza bruta HTTP", "Episodios evaluados": 0, "IF 0,05": "no evaluado",
                     "IF 0,03": "no evaluado", "Heuristicos": "no evaluado", "Hibrido 0,05": "no evaluado",
                     "Hibrido 0,03": "no evaluado"})
    escribir_csv(salida / "TABLA8-componentes.csv", filas_t8)
    comp = []
    for a in ALFAS:
        for e in EPISODIOS:
            i_, h = det[(e, "IF_" + a)], det[(e, "HEUR")]
            comp.append({"alfa": a, "episodio": e, "familia": FAMILIAS[e[:2]]["nombre"],
                         "clase": "ambos" if i_ and h else ("solo IF" if i_ else ("solo heuristicos" if h else "ninguno"))})
    escribir_csv(salida / "complementariedad-episodios.csv", comp)
    resumen_comp = {a: {k: [c["episodio"] for c in comp if c["alfa"] == a and c["clase"] == k]
                        for k in ("ambos", "solo IF", "solo heuristicos", "ninguno")} for a in ALFAS}
    # Markdown
    cols = list(filas_t8[0].keys())
    md = ["# Tabla 8 — Aporte de los componentes por episodio (recalculado offline)", "",
          "Bateria del 05-oct-2026 (N = 3 por familia), re-procesada desde los PCAP originales con el procesamiento",
          "del motor vigente, el IF congelado `if_limpio_2026_10` y los heuristicos `2026-10-06.2`. Un episodio cuenta",
          "como detectado si hay al menos una senal atribuible (ventana de 10.10.20.30 con fin en [T0, ultimo paquete",
          "de ataque + 60 s]). Es una reproduccion offline, no una prueba nueva en vivo.", "",
          "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for f in filas_t8:
        md.append("| " + " | ".join(str(f[c]) for c in cols) + " |")
    md += ["", f"Umbrales del IF (score_samples, cuantil 1-alfa sobre 65 553 ventanas de validacion): "
           f"alfa 0,05 -> {umbrales['0.05']:.10f}; alfa 0,03 -> {umbrales['0.03']:.10f}.", "",
           "## Complementariedad por episodio", "",
           "| alfa | ambos | solo IF | solo heuristicos | ninguno |", "|---|---|---|---|---|"]
    for a in ALFAS:
        r = resumen_comp[a]
        md.append(f"| {a.replace('.', ',')} | " + " | ".join(
            (f"{len(r[k])}: " + ", ".join(r[k])) if r[k] else "0" for k in ("ambos", "solo IF", "solo heuristicos", "ninguno")) + " |")
    md += ["", "## Resultado historico (no recalculado, 05-oct, modelo contaminado `if_recalibrado_2026_09`)", "",
           f"Modelo {sum(r['det_modelo'] for r in original)}/9 · heuristicos {sum(r['det_heur'] for r in original)}/9 · "
           f"combinado {sum(r['det_combinado'] for r in original)}/9 — reproducido offline en "
           f"{sum(r['coincide'] for r in original)}/9 episodios a partir de los `features.csv` guardados. No es comparable",
           "con las columnas de arriba: otro modelo, otra version de heuristicos y otro procesamiento (PCAP sin deduplicar).", "",
           "## Metricas por ventana sobre la poblacion de la Tabla 7 (65 421 normales + 84 ataques)", "",
           "| Configuracion | TP | FP | TN | FN | Precision | Recall | F1 | FPR |", "|---|---|---|---|---|---|---|---|---|"]
    for cfg in CONFIGS:
        m = vent["principal"][cfg]
        md.append(f"| {cfg} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | {m['precision']:.4f} | "
                  f"{m['recall']:.4f} | {m['F1']:.4f} | {pct(m['FPR'])} |")
    md += ["", "ROC-AUC y AP solo existen para el IF (Tabla 7); el hibrido es una regla OR sin puntuacion continua.", ""]
    (salida / "TABLA8-componentes.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    md2 = ["# Metricas por ventana (poblacion de la Tabla 7)", ""]
    for nombre, clave in (("Principal (IF con la regla de la Tabla 7; heuristicos en todas las ventanas)", "principal"),
                          ("Operativa del motor (no elegibles sin evaluar; sin paquetes en 10 s el IF no se puntua)", "operativa_motor"),
                          ("Sensibilidad: sin las 74 ventanas normales inciertas de 10.10.20.30 (65 431)", "sensibilidad_sin_74_kali")):
        md2 += [f"## {nombre}", "", "| Configuracion | TP | FP | TN | FN | Precision | Recall | F1 | FPR |",
                "|---|---|---|---|---|---|---|---|---|"]
        for cfg in CONFIGS:
            m = vent[clave][cfg]
            md2.append(f"| {cfg} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | {m['precision']:.4f} | "
                       f"{m['recall']:.4f} | {m['F1']:.4f} | {pct(m['FPR'])} |")
        md2.append("")
    md2 += ["## Auditoria", "", "```json", json.dumps(vent["auditoria"], indent=1, ensure_ascii=False), "```", "",
            "Falsas alarmas dentro de las 74 ventanas inciertas: " + json.dumps(vent["fp_en_74_kali"]), "",
            "Heuristicos disparados: " + json.dumps(vent["heuristicos_disparados"], ensure_ascii=False), ""]
    for a in ALFAS:
        md2.append(f"Solape en ataques alfa {a}: " + json.dumps(vent["solape_ataques_" + a]) +
                   f" · en falsas alarmas: " + json.dumps(vent["solape_falsas_alarmas_" + a]))
    (salida / "VENTANAS-metricas.md").write_text("\n".join(md2) + "\n", encoding="utf-8")
    escribir_csv(salida / "VENTANAS-metricas.csv", [
        {"poblacion": k, "configuracion": cfg, **vent[k][cfg]}
        for k in ("principal", "operativa_motor", "sensibilidad_sin_74_kali") for cfg in CONFIGS])
    resumen = {"tabla8": filas_t8, "complementariedad": resumen_comp, "umbrales": umbrales,
               "original_reproducido": {k: sum(r[k] for r in original) for k in ("det_modelo", "det_heur", "det_combinado", "coincide")},
               "control_base": {c: base[c] for c in CONFIGS} | {"ventanas": base["ventanas_elegibles"], "duracion_s": base["duracion_pcap_s"]},
               "contraste_acumulador": {i: {c: e[c]["detectado"] for c in CONFIGS} for i, e in contraste["episodios"].items()},
               "no_atribuibles": len(epis["no_atribuibles"]),
               "entorno": {"python": platform.python_version(), "sklearn": __import__("sklearn").__version__,
                           "numpy": np.__version__, "sistema": platform.platform(), "avisos_carga_modelo": env.avisos_carga}}
    guardar_json(salida / "resultados-aporte.json", resumen)
    return resumen


def manifiesto(env: Entorno, salida: Path) -> None:
    entradas = {}
    for i in EPISODIOS + ["BASE"]:
        d = env.datos / "piloto" / i
        for p in sorted(d.iterdir()):
            if p.suffix in (".pcap", ".json", ".csv"):
                entradas[f"piloto/{i}/{p.name}"] = sha256(p)
    cf = env.datos / "cyberflow"
    for rel in ("artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib",
                "artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json",
                "artifacts/preliminar/if_recalibrado_desplegable.joblib",
                "artifacts/preliminar/manifest-if-recalibrado.json",
                "artifacts/aprendizaje/oro/oro.csv", "artifacts/aprendizaje/ataques/ataques-nota-M.csv",
                "configs/features/multilayer-v2.json"):
        entradas["cyberflow/" + rel] = sha256(cf / rel)
    for rel, p in env.rutas_codigo.items():
        entradas["cyberflow/scripts/" + rel] = sha256(p)
    entradas["acum-20261005.csv"] = sha256(env.datos / "acum-20261005.csv")
    entradas["4.1/scores-validacion-65633.csv.gz"] = sha256(CALIB / "datos-sensor/scores-validacion-65633.csv.gz")
    entradas["4.1/validacion-kali-80-excluidas.csv"] = sha256(CALIB / "validacion-kali-80-excluidas.csv")
    entradas["4.1/puntuaciones-IF.csv.gz"] = sha256(COMP / "salidas/puntuaciones-IF.csv.gz")
    propios = {}
    for p in sorted(list(AQUI.glob("*.py")) + list(AQUI.glob("*.json")) + list(AQUI.glob("*.md"))
                    + list(ANTECEDENTE.glob("*"))
                    + list(salida.glob("*"))):
        if p.is_file() and p.name != "MANIFIESTO-APORTE.json":
            propios[str(p.relative_to(AQUI)).replace("\\", "/")] = sha256(p)
    guardar_json(AQUI / "MANIFIESTO-APORTE.json", {
        "generado_utc": datetime.now(timezone.utc).isoformat(), "entradas_externas_sha256": entradas,
        "archivos_publicados_sha256": propios,
        "entorno": {"python": platform.python_version(), "sklearn": __import__("sklearn").__version__,
                    "numpy": np.__version__}})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--salida", type=Path, default=AQUI / "resultados")
    ap.add_argument("paso", choices=("todo",))
    a = ap.parse_args()
    a.salida.mkdir(parents=True, exist_ok=True)
    env = Entorno(a.datos)
    u = paso_umbrales(a.salida)
    umbrales = {k: v["umbral_score_samples"] for k, v in u["umbrales"].items()}
    print("umbrales", umbrales, flush=True)
    original = paso_original(env, a.salida)
    print("original reproducido", sum(r["coincide"] for r in original), "/9", flush=True)
    epis = paso_episodios(env, a.salida, umbrales)
    print("episodios listos", flush=True)
    base = paso_control_base(env, a.salida, umbrales)
    contraste = paso_contraste_acumulador(env, a.salida, umbrales, epis["metas"])
    vent = paso_ventanas(env, a.salida, umbrales)
    print("ventanas listas", flush=True)
    res = paso_consolidar(a.salida, umbrales, original, epis, vent, base, contraste, env)
    manifiesto(env, a.salida)
    print(json.dumps({"tabla8": res["tabla8"], "complementariedad": res["complementariedad"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
