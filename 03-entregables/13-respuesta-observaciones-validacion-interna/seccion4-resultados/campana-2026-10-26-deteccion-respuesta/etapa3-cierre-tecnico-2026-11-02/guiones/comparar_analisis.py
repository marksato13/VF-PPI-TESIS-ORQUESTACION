"""Compara dos analisis-3b.json: poblacion, excluidos con motivo, clasificacion por episodio y control."""
import json
import sys

a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
print("excepciones (b):", json.dumps(b["poblacion"]["excepciones_respuesta"], ensure_ascii=False)[:1500])
print("tramo control (b):", json.dumps(b["control_normal"]["tramo_cubierto"], ensure_ascii=False)[:1500])
ta, tb = a["control_normal"]["tramo_cubierto"], b["control_normal"]["tramo_cubierto"]
print("control iguales:", ta == tb)
pa, pb = 0, 0
dif = []
for esc, v in b["tabla_principal"].items():
    va = a["tabla_principal"][esc]
    pb += len(v["poblacion_principal"])
    pa += len(va["poblacion_principal"])
    if va["poblacion_principal"] != v["poblacion_principal"] or va["fuera_de_poblacion"] != v["fuera_de_poblacion"]:
        dif.append(esc)
    print(esc, "principal", len(v["poblacion_principal"]), "fuera", v["fuera_de_poblacion"],
          {k: v[k] for k in v if k.startswith(("HEUR", "HIB", "IF"))})
print("poblacion principal a/b:", pa, pb, "escenarios con poblacion distinta:", dif)
ep_dif = [e for e in b["episodios"] if json.dumps(a["episodios"][e], sort_keys=True) != json.dumps(b["episodios"][e], sort_keys=True)]
print("episodios con algun campo distinto:", ep_dif)
for e in ep_dif[:6]:
    for k in b["episodios"][e]:
        if json.dumps(a["episodios"][e].get(k), sort_keys=True) != json.dumps(b["episodios"][e][k], sort_keys=True):
            print("  ", e, k, json.dumps(a["episodios"][e].get(k), ensure_ascii=False)[:300], "->",
                  json.dumps(b["episodios"][e][k], ensure_ascii=False)[:300])
