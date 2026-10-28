"""Genera EJEMPLO-cobertura/ con fixtures de CODIGO (no resultados experimentales): cobertura del conjunto
etiquetado (50 % y 1/3) y control por window_end con una decisión registrada después del final del control.
Uso (desde la carpeta de la campana): python EJEMPLO-cobertura/generar_ejemplo.py EJEMPLO-cobertura"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
import test_herramientas as t
an = t.cargar("analizar"); T = t.T0; K = t.K
NOTA = "FIXTURE DE CODIGO (tests/test_herramientas.py, _e2e_ne): datos sinteticos, no resultados de la campana A"
base = t._mot({T + 40: {"score": -0.70, "decision": "ALERT"}})     # decisiones de la Kali T..T+140

# caso 50 %: T+40 con decisión, T+150 sin decisión ni evento
mot_a = base
j_a, _ = t._e2e_ne(an, mot_a, etiquetas={(K, T + 40): 1, (K, T + 150): 1})
# caso 1/3: T+40 con decisión, T+50 no evaluada explícita, T+150 sin registro
mot_b = t._sin(base, T + 50) + [t.noev(T + 220, T + 50)]
# control [T+100, T+200] (perfil legítimo 10.10.20.21): T+90 escrita a T+101 (fuera), T+200 escrita a T+230 (dentro)
mot_b += [t.rec(T + 101, T + 90, -0.70, ip=t.OTRA), t.rec(T + 111, T + 100, -0.50, ip=t.OTRA),
          t.rec(T + 151, T + 150, -0.50, ip=t.OTRA), t.rec(T + 230, T + 200, -0.70, ip=t.OTRA),
          t.noev(T + 330, T + 160, ip=t.OTRA)]
j_b, md_b = t._e2e_ne(an, mot_b, control=(T + 100, T + 200),
                      etiquetas={(K, T + 40): 1, (K, T + 50): 1, (K, T + 150): 1})


def met(j):
    m = j["metricas_por_ventana"]
    return {"denominador": m["denominador"], "conjunto_etiquetado": m["conjunto_etiquetado"],
            "IF_0.05": m["IF_0.05"], "HEUR": m["HEUR"]}


tarde = next(json.loads(x) for x in mot_b if '"window_end_utc": "%s"' % t.iso(T + 200) in x)
ctl = j_b["control_normal_fpr"]
ext = {"nota": NOTA,
       "caso_50": {"etiquetas": "T+40 (decision), T+150 (sin decision ni evento)", "metricas_por_ventana": met(j_a)},
       "caso_1_3": {"etiquetas": "T+40 (decision), T+50 (ventana_no_evaluada), T+150 (sin registro)",
                    "metricas_por_ventana": met(j_b)},
       "control_por_window_end": {
           "intervalo": "[T+100, T+200], ambos extremos incluidos",
           "decision_registrada_tarde": {"window_end_utc": tarde["window_end_utc"], "logged_at": tarde["logged_at"],
                                          "logged_at_utc": t.iso(tarde["logged_at"]),
                                          "efecto": "cuenta en el control (su ventana pertenece a el) aunque se "
                                                    "escribio 30 s despues de 'hasta'; logged_at sin cambios"},
           "decision_fuera": {"window_end_utc": t.iso(T + 90), "logged_at_utc": t.iso(T + 101),
                              "efecto": "no cuenta: su ventana cierra antes de 'desde' aunque se escribio dentro"},
           "control_normal_fpr": {k: v for k, v in ctl.items() if k in (
               "ventanas", "denominador", "desde", "hasta", "seleccion", "decisiones_escritas_tras_hasta",
               "ventanas_no_evaluadas", "cobertura_entre_registradas", "cobertura_entre_registradas_significado",
               "inventario_esperado", "IF_0.05", "HEUR")}}}
out = Path(sys.argv[1]); out.mkdir(exist_ok=True)
(out / "analisis-extracto.json").write_text(json.dumps(ext, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                           newline="\n")
(out / "TABLA8-caso-1_3-y-control.md").write_text(md_b, encoding="utf-8", newline="\n")
(out / "motor-caso-1_3-y-control.log").write_text("\n".join(mot_b) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"50": ext["caso_50"]["metricas_por_ventana"]["conjunto_etiquetado"]["cobertura_total"],
                  "1/3": ext["caso_1_3"]["metricas_por_ventana"]["conjunto_etiquetado"]["cobertura_total"],
                  "control": {k: ctl[k] for k in ("ventanas", "ventanas_no_evaluadas", "cobertura_entre_registradas",
                                                  "decisiones_escritas_tras_hasta")},
                  "FA_IF_0.05": ctl["IF_0.05"]}))
