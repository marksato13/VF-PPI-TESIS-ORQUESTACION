"""Tabla de casos temporales de S14 con el valor OBTENIDO (no solo «pasa»), usando los mismos datos sintéticos del banco
tests/test_etapa4_ecarga_prep.py. Uso (banco Docker, sin red): ECARGA_DIRS=<dir> python3 tabla_casos.py
Columnas: caso | esperado | obtenido | coincide | tramo posible | motivo (recortado)."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/repo/tests")
import test_etapa4_ecarga_prep as b  # noqa: E402

D, H, BD = b.D, b.H, b.BD
V = {True: "true", False: "false", None: "null"}
filas, fallos = [], 0


def fila(caso, esperado, obtenido, tramo, motivo, ok=None):
    global fallos
    ok = esperado == obtenido if ok is None else ok
    fallos += not ok
    tramo = tramo.replace("|", "·")
    filas.append(f"| {caso} | {esperado} | {obtenido} | {'sí' if ok else '**NO**'} | {tramo} | {motivo[:90]} |")


print("herramientas:", os.environ.get("ECARGA_DIRS"))
print("evaluar_s14 VERSION:", b.modulo("evaluar_s14").VERSION)
print()
print("| caso | esperado | obtenido | coincide | tramo | motivo |")
print("|---|---|---|---|---|---|")

for cid, sat, miss, esp, explica in b.CASOS_TIEMPO:
    r = b.s14(b.completo(b.tasas(*sat, **b.SAT_CPU), extra=b.falla_en("psi", D + miss[0], D + miss[1])))
    c = r["componentes"]["cpu"]
    fila(f"ventana: {cid}", f"cpu {V[esp]} / S14 {V[esp]}", f"cpu {V[c['valor']]} / S14 {V[r['S14']['valor']]}",
         explica, c["motivo"], ok=c["valor"] is esp and r["S14"]["valor"] is esp)

for cid, sat, quitar, esp, explica in [
        ("borde inicio ventana, 8 s", (2, 8), (D - 2, D + 2), None, "U[D,D+2)+S6 = 8 s"),
        ("borde inicio ventana, 7 s", (1, 7), (D - 3, D + 1), True, "U[D,D+1)+S6 = 7 s"),
        ("borde fin ventana, 9 s", (3591, 3597), (H - 2, H + 2), None, "S6+U[H-3,H) = 9 s"),
        ("borde fin ventana, 7 s", (3593, 3597), (H - 2, H + 2), True, "S4+U[H-3,H) = 7 s")]:
    c = b.s14(b.completo(b.tasas(sat, **b.SAT_CPU), quitar=[quitar]))["componentes"]["cpu"]
    fila(cid, f"cpu {V[esp]}", f"cpu {V[c['valor']]}", explica, c["motivo"])

for cid, args, esp, explica in [
        ("base limpia + episodio en ventana", ([],), False, "«nueva» demostrada"),
        ("base dudosa, hueco antes", ([(13, 18)], b.falla_en("psi", BD + 11, BD + 13)), None, "base U3+S5 = 8 s"),
        ("base dudosa, hueco después", ([(10, 15)], b.falla_en("psi", BD + 16, BD + 18)), None, "base S5+U3 = 8 s"),
        ("base dudosa en su borde de inicio", ([(2, 8)], None, [(BD - 2, BD + 2)]), None, "base U2+S6 = 8 s"),
        ("base con hueco aislado", ([], b.falla_en("psi", BD + 100, BD + 102)), False, "hueco entre N: base válida")]:
    c = b._con_base(*args)
    fila(cid, f"cpu {V[esp]}", f"cpu {V[c['valor']]}", explica, c["motivo"])

for comp, campo, r in b.COMPONENTES_TIEMPO:
    v5 = b.s14(b.completo(b.tasas((104, 109), **r)))["componentes"][comp]["valor"]
    v8 = b.s14(b.completo(b.tasas((104, 112), **r)))["componentes"][comp]["valor"]
    c = b.s14(b.completo(b.tasas((104, 109), **r), extra=b.falla_en(campo, D + 101, D + 104)))["componentes"][comp]
    fila(f"componente {comp} ({campo} ausente)", "true / false / null",
         f"{V[v5]} / {V[v8]} / {V[c['valor']]}", "S5 / S8 / U4+S5 = 9 s", c["motivo"])

print("\n".join(filas))
print()
print("Punta a punta (construir_entrada.py -> evaluar_ecarga.py veredicto):")
print("| caso | S14 | veredicto | habilita_condicion_3 | rc |")
print("|---|---|---|---|---|")
pc = lambda: b.lineas(b.serie(D - 3, H + 20))
e2e_casos = [
    ("evidencia completa sin saturación", lambda: b.completo(), (True, "estable con carga suficiente", True, 0)),
    ("saturación demostrada de 8 s exactos", lambda: b.completo(b.entre(100, 108, cpu=100, psi_cpu=50)),
     (False, "no estable", False, 1)),
    ("saturación demostrada de 30 s", lambda: b.completo(b.entre(100, 130, cpu=100, psi_cpu=50)),
     (False, "no estable", False, 1)),
    ("reproducción: psi ausente en [D+100, D+103) antes de la saturación",
     lambda: b.completo(b.entre(100, 108, cpu=100, psi_cpu=50), extra=b.falla_en("psi", D + 100, D + 103)),
     (None, "no demostrable", False, 1)),
]
for cid, muestras, esp in e2e_casos:
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        rc, r, e, _ = b.e2e(t, pc(), muestras(), pcap_log=t / "obs_pcap.log")
        obt = (e["S"]["S14"], r["estabilidad_tecnica"], r["habilita_condicion_3"], rc)
        fallos += obt != esp
        print(f"| {cid} | {V[obt[0]]} | {obt[1]} | {V[obt[2]]} | {obt[3]} |" + ("" if obt == esp else f" **esperado {esp}**"))
print()
print("DISCREPANCIAS:", fallos)
