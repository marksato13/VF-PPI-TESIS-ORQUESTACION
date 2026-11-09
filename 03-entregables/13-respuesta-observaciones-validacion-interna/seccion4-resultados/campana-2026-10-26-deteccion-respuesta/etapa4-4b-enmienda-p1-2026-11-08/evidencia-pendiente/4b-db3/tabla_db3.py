import json, sys
from pathlib import Path
S = Path(r"C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\db3_4b\salida")
j = json.loads((S / "db3-4b.json").read_text(encoding="utf-8"))
print("version:", j["version"], "| intervalo:", j["intervalo_utc"], "| min C0 h:", j["min_c0_horas"], "| limites:", j["limites_propuestos"])
print("seleccion:", j["poblacion_seleccion"])
print()
def f(x, n=3): return "-" if x is None else (f"{x:.{n}f}")
for al in ("0.05", "0.03", "0.01"):
    a = j["alfas"][al]; v = a["veredicto_alfa"]
    print(f"=== alfa {al}: veredicto {v['alfa']} elegible={v['elegible']}")
    print("IP | req | C0 | faltan | horasC0 | L1 obs [min-max] | L1 | L2 obs [min-max] | L2 | decision")
    for ip, e in a["seleccion"].items():
        l1, l2 = e["L1_avisos_por_hora"], e["L2_fraccion_en_alerta"]
        print(f"{ip} | {e['ventanas_requeridas']} | {e['ventanas_c0_decididas']} | {e['ventanas_faltantes']} | {e['horas_c0']} | "
              f"{f(l1['observado'])} [{f(l1['minimo'])}-{f(l1['maximo'])}] | {l1['decision']} | "
              f"{f(l2['observado'],4)} [{f(l2['minimo'],4)}-{f(l2['maximo'],4)}] | {l2['decision']} | {e['decision']}" + (f" ({e['motivo_extra']})" if e.get("motivo_extra") else ""))
    print("aparte:", {ip: (e["ventanas_requeridas"], e["ventanas_c0_decididas"], e["decision"]) for ip, e in a["reportadas_aparte"].items()})
    print()
