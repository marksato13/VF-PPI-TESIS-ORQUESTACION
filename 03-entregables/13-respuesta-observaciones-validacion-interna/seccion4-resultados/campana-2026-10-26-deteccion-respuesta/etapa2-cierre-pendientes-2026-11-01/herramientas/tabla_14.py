"""Tabla Markdown individual de las 14 a partir de diagnostico_14.py.
Uso: python tabla_14.py diagnostico-14.json salida.md"""
import json, sys
f = json.load(open(sys.argv[1], encoding="utf-8"))
si = lambda b: "sí" if b else "no"
L = ["| # | Entidad | Fin de ventana A | Alta (953a436) | Expiró (953a436) | Corte de alta | Corte propio (A−230) | Obs. PCAP de E en (A−60, A]: alta / propio | Obs. EVE | Propietarios, en el horizonte propio, de los paquetes de E en (A−60, A] | Cambio de propietario | Todos excluidos | Regla causal | Estado con 6b6ef82 | Coincide |",
     "|" + "---|" * 15]
for i, x in enumerate(f, 1):
    ha, hp = x["horizonte_alta"], x["horizonte_propio"]
    a = ", ".join(f"{k}: {v}" for k, v in hp["paquetes_de_E_atribuidos_a"].items())
    L.append(f"| {i} | {x['entidad']} | {x['fin_ventana'][11:19]} | {x['alta_pendiente_anterior']} | {x['expiro_anterior']} | {ha['corte']} | {hp['corte']} | {ha['obs_pcap_E_60s']} / {hp['obs_pcap_E_60s']} | {x['obs_eve_E_60s']} | {a} | {si(x['cambio_propietario'])} | {si(x['propietario_excluido'])} | {x['estado_regla_causal']} | {x['estado_corregido']} | {si(x['coincide_motor'])} |")
L += ["", "| # | Entidad | A | Inicio del flujo más antiguo de E: alta → propio | E es primer emisor de algún flujo: alta / propio |", "|---|---|---|---|---|"]
for i, x in enumerate(f, 1):
    e = x["entidad"]
    L.append(f"| {i} | {e} | {x['fin_ventana'][11:19]} | {x['horizonte_alta']['inicio_flujos_min']} → {x['horizonte_propio']['inicio_flujos_min']} | {si(e in x['horizonte_alta']['primer_emisor'])} / {si(e in x['horizonte_propio']['primer_emisor'])} |")
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
