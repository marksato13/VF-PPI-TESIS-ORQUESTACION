#!/usr/bin/env python3
"""E5 de B2 con el criterio vigente (OBJETIVOS-Y-CRITERIOS E5): «La restricción caduca o se retira y se verifica que el set no contiene al origen
antes del siguiente episodio». Solo lectura de `evidencia-local\\`. Por episodio con regla: instante de la retirada explícita (agente: evento
`retirada`; puerta D5: paso `retirar` con `retirado: true`), lectura del set antes (`nft_antes`, presente) y después (`nft_despues`, ausente),
y si esa lectura ocurrió antes del inicio del siguiente episodio. Distingue retirada explícita de caducidad natural (`hasta` de la regla)."""
import datetime
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
EV = AQUI / "evidencia-local"
K = "10.10.20.30"
L = lambda n: [json.loads(l) for l in open(EV / (n + ".jsonl"), encoding="utf-8") if l.strip()]
ep = lambda s: datetime.datetime.fromisoformat(s).timestamp()
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%H:%M:%S.%f")[:-3] + "Z"


def main():
    ag, pu, mar = L("agente"), L("puertas"), L("marcas")
    orden = [m for m in mar if m["evento"] == "campana_inicio"][0]["orden"]
    ini = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "inicio"}
    fin = {m["episodio_id"]: ep(m["reloj"]["pared_utc"]) for m in mar if m["evento"] == "fin"}
    eps = [e for e in orden if e in ini]
    out = []
    for k, e in enumerate(eps):
        fam = e.rsplit("-", 1)[0]
        t0, t1 = ini[e], fin[e]
        sig = ini[eps[k + 1]] if k + 1 < len(eps) else None
        tope = sig if sig is not None else t1 + 400
        r = {"episodio": e, "familia": fam}
        if fam == "dns_inusual":
            r.update(resultado="no evaluado", motivo="sin punto de aplicación: no hubo regla que retirar")
            out.append(r)
            continue
        conj = "bloqueados" if fam == "fuerza_bruta_http" else "limitados"
        apl = [n for x in ag if x["evento"] == "aplicacion" and x.get("nuevos") and t0 - 2 <= x["aplicado_en"] <= tope for n in x["nuevos"] if n["set"] == conj]
        hasta = max(n["hasta"] for n in apl)
        ret_ag = sorted(x for x in ag if x["evento"] == "retirada" and t1 <= x["t"] <= tope and x["ip"] == K and x["set"] == conj)
        pasos = [(p["intento"], s) for p in pu for s in p["pasos"] if t1 <= s.get("t", 0) <= tope]
        antes = [s for _, s in pasos if s["paso"] == "nft_antes"]
        retir = [s for _, s in pasos if s["paso"] == "retirar" and s.get("retirado")]
        desp = [s for _, s in pasos if s["paso"] == "nft_despues"]
        ok_antes = bool(antes) and antes[-1].get("presente") and conj in antes[-1].get("donde", [])
        ok_desp = bool(desp) and desp[-1].get("presente") is False and desp[-1].get("donde") == []
        t_ret = retir[0]["t"] if retir else None
        explicita = bool(ret_ag) and t_ret is not None and t_ret < hasta
        antes_del_siguiente = bool(desp) and (sig is None or desp[-1]["t"] < sig)
        r.update(set=conj, regla_hasta=iso(hasta), retirada_agente=[iso(x["t"]) for x in ret_ag], retirar_d5=iso(t_ret) if t_ret else None,
                 nft_antes=("presente en %s a %s" % (conj, iso(antes[-1]["t"]))) if ok_antes else "sin evidencia", nft_despues=("ausente a %s (+%.1f s del fin)" % (iso(desp[-1]["t"]), desp[-1]["t"] - t1)) if ok_desp else "sin evidencia",
                 retirada_antes_de_caducar=bool(t_ret and t_ret < hasta), margen_a_la_caducidad_s=round(hasta - t_ret, 1) if t_ret else None,
                 siguiente_episodio=iso(sig) if sig else "no hubo (X1 canceló)", lectura_antes_del_siguiente=antes_del_siguiente)
        if explicita and ok_antes and ok_desp and antes_del_siguiente:
            r.update(resultado="verificado", via="retirada_explicita", motivo="retirada por D5 con evento del agente y set sin el origen antes del siguiente episodio; la regla no había caducado")
        elif not sig and explicita and ok_antes and ok_desp:
            r.update(resultado="verificado", via="retirada_explicita", motivo="retirada por D5 confirmada con lecturas del set; no hubo episodio siguiente que acotar")
        else:
            r.update(resultado="indeterminado", motivo="falta alguna evidencia: agente=%s antes=%s despues=%s" % (bool(ret_ag), ok_antes, ok_desp))
        out.append(r)
    (AQUI / "e5-retirada-b2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    for r in out:
        print(r["episodio"], r["resultado"], r.get("via"), "| agente", r.get("retirada_agente"), "| retirar", r.get("retirar_d5"), "| hasta", r.get("regla_hasta"), "| margen", r.get("margen_a_la_caducidad_s"), "| desp", r.get("nft_despues"), "| sig", r.get("siguiente_episodio"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
