#!/usr/bin/env python3
"""Registros HTTP existentes de srv-dmz para el intervalo de B2 (17:50:00–18:32:00Z): son los del endpoint de fuerza bruta `ppi-brute-lab`
(journal de la unidad). El servidor web del laboratorio (`servidor_lab.py`, :80 y :443) NO registra peticiones (`log_message` es `pass`).
Solo lectura de la copia local `C:\\Users\\markp\\cf-b2-pcap\\srvdmz\\ppi-brute-lab-journal-B2.txt` y de `evidencia-local\\`.
Extrae hora (con zona), origen, método, ruta, usuario y código; los relaciona con los episodios y con las marcas de aplicación y retirada."""
import collections
import datetime
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
EV = AQUI / "evidencia-local"
LOG = Path(r"C:\Users\markp\cf-b2-pcap\srvdmz\ppi-brute-lab-journal-B2.txt")
KALI = "10.10.20.30"
PAT = re.compile(r"^(?P<jts>\S+) srv-dmz python3\[(?P<pid>\d+)\]: (?P<ts>\S+) (?P<ip>\S+) (?P<met>[A-Z]+) (?P<ruta>\S+) user=(?P<user>\S+) -> (?P<cod>\d+)\s*$")


def jl(n):
    return [json.loads(l) for l in open(EV / (n + ".jsonl"), encoding="utf-8", errors="replace") if l.strip()]


def ep_(s):
    return datetime.datetime.fromisoformat(s).timestamp()


def main():
    reg, otras = [], []
    for l in open(LOG, encoding="utf-8"):
        m = PAT.match(l)
        if m:
            d = m.groupdict()
            d["t"] = ep_(d["ts"])
            d["zona"] = d["ts"][-6:]
            reg.append(d)
        elif l.strip() and not l.startswith("-- "):
            otras.append(l.strip()[:200])
    mar, ag, pu = jl("marcas"), jl("agente"), jl("puertas")
    ini = {m["episodio_id"]: ep_(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "inicio"}
    fin = {m["episodio_id"]: ep_(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "fin"}
    eps = list(ini)
    por_origen = collections.Counter((d["ip"], d["met"], d["ruta"], d["cod"]) for d in reg)
    res = {"fuente": "journal de ppi-brute-lab.service en srv-dmz (cuenta adminsrvdmz), 17:50:00–18:32:00Z", "lineas": len(reg), "lineas_no_reconocidas": len(otras),
           "zonas_horarias": sorted({d["zona"] for d in reg}), "por_origen_metodo_ruta_codigo": [[list(k), v] for k, v in por_origen.most_common()], "episodios": []}
    for e in eps:
        t0, t1 = ini[e], fin[e]
        fam = e.rsplit("-", 1)[0]
        r = {"episodio": e, "familia": fam}
        dentro = [d for d in reg if t0 <= d["t"] <= t1]
        r["peticiones_en_[inicio,fin]"] = dict(collections.Counter((d["ip"], d["cod"]) for d in dentro).most_common(8) and
                                               {"%s %s" % k: v for k, v in collections.Counter((d["ip"], d["cod"]) for d in dentro).items()})
        if fam == "fuerza_bruta_http":
            ap = [x["aplicado_en"] for x in ag if x.get("evento") == "aplicacion" and x.get("nuevos") and t0 - 2 <= x["aplicado_en"] <= t1 + 400 and any(n["set"] == "bloqueados" for n in x["nuevos"])]
            t_apl = min(ap)
            retiros = [p_s["t"] for p in pu for p_s in p["pasos"] if p_s.get("paso") == "retirar" and p_s.get("retirado") and t1 <= p_s["t"] <= t1 + 400]
            kali = sorted((d for d in reg if d["ip"] == KALI and t0 - 5 <= d["t"] <= t1 + 400), key=lambda d: d["t"])
            antes = [d for d in kali if d["t"] < t_apl]
            despues = [d for d in kali if d["t"] >= t_apl]
            por_seg = collections.Counter(int(d["t"] - t0) for d in kali)
            r.update(t_apl_menos_t_inicio=round(t_apl - t0, 2), retirada_d5_menos_t_fin=[round(x - t1, 1) for x in retiros],
                     kali_primera_peticion_menos_t_inicio=round(kali[0]["t"] - t0, 3) if kali else None,
                     kali_ultima_peticion_menos_t_inicio=round(kali[-1]["t"] - t0, 3) if kali else None,
                     kali_peticiones_antes_de_t_apl=len(antes), kali_peticiones_desde_t_apl=len(despues),
                     kali_peticiones_por_segundo_desde_inicio=[por_seg.get(s, 0) for s in range(0, 12)],
                     codigos_kali=dict(collections.Counter(d["cod"] for d in kali)),
                     ultima_peticion_antes_de_t_apl_s=round(t_apl - antes[-1]["t"], 3) if antes else None)
        out_ep = [d for d in reg if d["ip"] != KALI and t0 <= d["t"] <= t1]
        r["peticiones_de_otros_origenes_en_el_episodio"] = {k: v for k, v in collections.Counter(d["ip"] for d in out_ep).items()}
        res["episodios"].append(r)
    # peticiones fuera de los episodios (para ubicar el resto de las 1156 líneas)
    fuera = collections.Counter()
    for d in reg:
        if not any(ini[e] <= d["t"] <= fin[e] for e in eps):
            fuera[d["ip"]] += 1
    res["peticiones_fuera_de_los_episodios_por_origen"] = dict(fuera)
    clientes = [d for d in reg if d["ip"].startswith("10.10.20.") and d["ip"] != KALI]
    res["peticiones_de_clientes_legitimos_10.10.20.21-26"] = len(clientes)
    (AQUI / "resultado-srvdmz.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print("lineas", len(reg), "no reconocidas", len(otras), "zonas", res["zonas_horarias"])
    print("por origen/metodo/ruta/codigo:", res["por_origen_metodo_ruta_codigo"][:8])
    for r in res["episodios"]:
        print(r["episodio"], {k: v for k, v in r.items() if k not in ("episodio", "familia")})
    print("fuera de episodios:", res["peticiones_fuera_de_los_episodios_por_origen"], "| clientes legitimos:", res["peticiones_de_clientes_legitimos_10.10.20.21-26"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
