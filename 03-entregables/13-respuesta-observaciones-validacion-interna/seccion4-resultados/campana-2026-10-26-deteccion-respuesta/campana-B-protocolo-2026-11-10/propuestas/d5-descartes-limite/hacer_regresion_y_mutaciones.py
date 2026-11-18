#!/usr/bin/env python3
"""(1) Genera `test_d5_regresion_corregido.py`: la suite existente `tests\\test_d5.py` (19 pruebas de D5) ejecutada contra `d5_episodio_corregido` SIN tocarla
(solo cambia el import). (2) Mutaciones de la corrección: cada una debe hacer fallar al menos una prueba. Uso: hacer_regresion_y_mutaciones.py regresion | mutaciones <dir_de_trabajo>"""
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
MUT = [
    ("reintroduce el defecto: descartes_limite cuenta como presente",
     'donde = [s for s, el in sets.items() if s != RESIDUAL and el and origen in el]',
     'donde = [s for s, el in sets.items() if s != RESIDUAL and el and origen in el] + ([RESIDUAL] if desc and origen in desc else [])'),
    ("la puerta nunca ve restricciones (presente siempre False)", '"presente": bool(donde)', '"presente": False'),
    ("sets de aplicación ausentes dejan de fallar cerrado", 'any(not isinstance(sets.get(s), dict) for s in SETS_APLICACION)', 'False'),
    ("estado de tipo erróneo deja de fallar cerrado", 'if not isinstance(est, dict):', 'if False:'),
    ("contador mal formado deja de fallar cerrado", 'if desc is not None and not isinstance(desc, dict):', 'if False:'),
    ("el contador residual no se informa", 'residual = {RESIDUAL: desc[origen]} if desc and origen in desc else {}', 'residual = {}'),
    ("el resultado de la puerta no conserva el residual", '"residual_conservado": residual}', '"residual_conservado": {}}'),
    ("solo se mira limitados (bloqueados ignorado)", 'donde = [s for s, el in sets.items() if s != RESIDUAL and el and origen in el]', 'donde = [s for s, el in sets.items() if s == "limitados" and el and origen in el]'),
    ("el listado fallido se trata como estado vacío", 'return {"ok": False, "rc": 2, "motivo": "listar falló: %s" % (r.get("rechazo") or r.get("error_nft"))}\n    est = r.get("estado")', 'return {"ok": True, "rc": 0, "tabla": True, "presente": False, "donde": [], "residual": {}}\n    est = r.get("estado")'),
]


def regresion():
    t = (RAIZ / "tests" / "test_d5.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    a = 'sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas"))\nimport d5_episodio as d5  # noqa: E402'
    b = 'sys.path.insert(0, os.path.dirname(__file__))\nimport d5_episodio_corregido as d5  # noqa: E402   (regresión: la suite original contra el D5 corregido)'
    assert t.count(a) == 1
    (AQUI / "test_d5_regresion_corregido.py").write_text(t.replace(a, b), encoding="utf-8", newline="\n")
    print("generado test_d5_regresion_corregido.py")


def mutaciones(trabajo):
    w = Path(trabajo)
    resultados = []
    for nombre, a, b in MUT:
        if w.exists():
            shutil.rmtree(w)
        (w / "propuestas").mkdir(parents=True)
        shutil.copytree(AQUI, w / "propuestas" / "d5-descartes-limite")
        shutil.copytree(RAIZ / "tests", w / "tests")
        shutil.copytree(RAIZ / "herramientas", w / "herramientas")
        shutil.copytree(RAIZ / "propuestas" / "d5-sin-reinicio", w / "propuestas" / "d5-sin-reinicio")
        f = w / "propuestas" / "d5-descartes-limite" / "d5_episodio_corregido.py"
        t = f.read_text(encoding="utf-8")
        assert t.count(a) == 1, nombre
        f.write_text(t.replace(a, b), encoding="utf-8", newline="\n")
        r = subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", "65534", "--tmpfs", "/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", "%s:/w" % w, "-w", "/w",
                            "cyberflow-etapa3-banco:1", "python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "propuestas/d5-descartes-limite"],
                           capture_output=True, text=True)
        ult = [l for l in r.stdout.splitlines() if l.strip()][-1] if r.stdout.strip() else r.stderr[-200:]
        resultados.append((nombre, "ELIMINADA" if r.returncode != 0 else "SOBREVIVE", ult))
        print("%-70s %-10s %s" % (nombre, resultados[-1][1], ult))
    print("mutaciones eliminadas: %d de %d" % (sum(1 for x in resultados if x[1] == "ELIMINADA"), len(resultados)))
    return 0 if all(x[1] == "ELIMINADA" for x in resultados) else 1


if __name__ == "__main__":
    if sys.argv[1] == "regresion":
        regresion()
    else:
        sys.exit(mutaciones(sys.argv[2]))
