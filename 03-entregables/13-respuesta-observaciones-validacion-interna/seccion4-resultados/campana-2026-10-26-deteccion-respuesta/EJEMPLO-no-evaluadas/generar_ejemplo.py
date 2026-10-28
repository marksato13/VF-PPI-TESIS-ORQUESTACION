"""Genera EJEMPLO-no-evaluadas/ con fixtures de CODIGO (no resultados experimentales).
Uso (desde la carpeta de la campana): python EJEMPLO-no-evaluadas/generar_ejemplo.py EJEMPLO-no-evaluadas"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
import test_herramientas as t
an = t.cargar("analizar"); T = t.T0; K = t.K
mot = t._sin(t._mot({T + 40: {"score": -0.70, "decision": "ALERT"}}), T + 70) + [t.noev(T + 85, T + 70)]
mot += [t.rec(w + 1, w, -0.50, ip=t.OTRA) for w in range(T, T + 150, 10) if w not in (T + 110, T + 120)]
mot += [t.noev(T + 280, T + 110, "ventana_no_regenerada", ip=t.OTRA), t.noev(T + 290, T + 120, ip=t.OTRA)]
j, md = t._e2e_ne(an, mot, control=(T + 95, T + 200), etiquetas={(K, T + 40): 1, (K, T + 70): 1, (K, T + 60): 0})
e = j["episodios"][t.EID]
ext = {"nota": "FIXTURE DE CODIGO (tests/test_herramientas.py, _e2e_ne): datos sinteticos, no resultados de la campana A",
       "ventanas_no_evaluadas": {k: v for k, v in j["ventanas_no_evaluadas"].items() if k != "motivos_reconocidos"},
       "episodio": {"evaluable": e["evaluable"], "motivo_no_evaluable": e["motivo_no_evaluable"],
                    "cobertura": e["cobertura"], "IF_0.05": {k: e["IF_0.05"][k] for k in
                    ("categoria", "senal_observada", "deteccion_confirmada", "primera_fiable", "window_end_utc", "logged_at_utc")},
                    "HEUR": {k: e["HEUR"].get(k) for k in ("categoria", "senal_observada", "deteccion_confirmada")},
                    "ventanas_no_evaluadas": e["ventanas_no_evaluadas"]},
       "tabla8": j["tabla8"], "control_normal_fpr": j["control_normal_fpr"],
       "metricas_por_ventana": j["metricas_por_ventana"], "calidad_datos": j["calidad_datos"]}
s = json.dumps(ext, ensure_ascii=False, indent=1)
s = s.replace(json.dumps(j["ventanas_no_evaluadas"]["registros"][0]["respaldo"]["archivo"])[1:-1], "motor.log")
out = Path(sys.argv[1]); out.mkdir(exist_ok=True)
(out / "analisis-extracto.json").write_text(s + "\n", encoding="utf-8", newline="\n")
(out / "TABLA8.md").write_text(md, encoding="utf-8", newline="\n")
(out / "motor.log").write_text("\n".join(mot) + "\n", encoding="utf-8", newline="\n")
print(s[:200])

