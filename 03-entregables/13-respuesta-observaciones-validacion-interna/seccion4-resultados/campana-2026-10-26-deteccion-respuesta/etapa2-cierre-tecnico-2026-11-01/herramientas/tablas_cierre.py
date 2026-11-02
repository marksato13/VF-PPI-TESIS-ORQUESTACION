"""Tablas Markdown del cierre: 25 episodios (vivo revisado frente a replay candidato) y escaneos breves.

Uso: python tablas_cierre.py comparacion-25-episodios.json analisis-3b-cand.json \
         desglose-escaneos-breves.json marcas.jsonl
Falla (assert) si alguna categoria difiere entre el 3B en vivo revisado y el replay candidato.
"""
import datetime as dt
import json
import sys

cmp_, cand, breves = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:4])


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def hora(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-4]


fin = {}
for linea in open(sys.argv[4], encoding="utf-8"):
    r = json.loads(linea)
    if r.get("evento") == "fin" and r.get("episodio_id"):
        fin[r["episodio_id"]] = ts(r["reloj"]["pared_utc"])

CLAVES = ("principal", "IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01")
print("| Episodio | Principal | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 | HIB 0,03 | HIB 0,01 | 1.ª IF 0,05 vivo / cand (s) | 1.ª HEUR vivo / cand (s) |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for f in cmp_["episodios"]:
    v, c = f["vivo_revisado"], f["replay_cand"]
    assert all(v[k] == c[k] for k in CLAVES), f["episodio"]
    principal = "sí" if c["principal"] else "no"
    print(f"| {f['episodio']} | {principal} | {c['IF_0.05']} | {c['IF_0.03']} | {c['IF_0.01']} | {c['HEUR']} | "
          f"{c['HIB_0.05']} | {c['HIB_0.03']} | {c['HIB_0.01']} | "
          f"{v['primera_IF_0.05_s']} / {c['primera_IF_0.05_s']} | {v['primera_HEUR_s']} / {c['primera_HEUR_s']} |")
print()
print("| Escaneo | Ráfaga principal (UTC) | Fin (marca) | 1.ª ventana port_scan | Disponible (cand) | Respecto al fin | Otras señales disponibles antes del fin |")
print("|---|---|---|---|---|---|---|")
for b in sorted(breves, key=lambda x: x["episodio"]):
    e = b["episodio"]
    ep = cand["episodios"][e]
    ps = sorted((v for v in ep["ventanas"] if v.get("heuristico") == "port_scan" and v.get("disponible_utc")),
                key=lambda v: v["disponible_utc"])
    otras = sorted({(v.get("heuristico") or "IF") for v in ep["ventanas"]
                    if v.get("senales") and v.get("disponible_utc") and ts(v["disponible_utc"]) <= fin[e]
                    and v.get("heuristico") != "port_scan"})
    rafaga = f"{b['rafaga_principal_inicio']}–{b['rafaga_principal_fin']} ({b['rafaga_principal_s']} s, {b['rafaga_principal_syn']} SYN)"
    if ps:
        p = ps[0]
        d = ts(p["disponible_utc"]) - fin[e]
        print(f"| {e} | {rafaga} | {hora(fin[e])} | {p['window_end_utc'][11:19]} | {p['disponible_utc'][11:22]} | "
              f"{d:+.1f} s | {', '.join(otras) or '—'} |")
    else:
        print(f"| {e} | {rafaga} | {hora(fin[e])} | — | — | — | {', '.join(otras) or '—'} |")
