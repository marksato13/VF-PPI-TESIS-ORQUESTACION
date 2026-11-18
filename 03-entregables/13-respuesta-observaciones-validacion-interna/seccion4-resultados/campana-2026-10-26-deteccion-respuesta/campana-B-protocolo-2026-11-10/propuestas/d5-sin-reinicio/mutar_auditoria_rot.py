#!/usr/bin/env python3
"""Mutaciones del #3 (auditoria_d5.py y adaptador_banco_rot.py): cada una debe hacer fallar alguna prueba de test_auditoria_rotacion.py."""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

AQUI = pathlib.Path(__file__).resolve().parent
L, R = "auditoria_d5.py", "adaptador_banco_rot.py"
MUT = [
    (L, "(?:\\.gz)?$\")", "$\")"),
    (L, "h.append((p, s.st_dev, s.st_ino))", "h.append((s.st_dev, s.st_ino))"),
    (L, "g[\"leida\"] = False", "g[\"leida\"] = True"),
    (L, "g[\"ilegibles\"] += 1", "pass"),
    (L, "if k not in vistos:", "if True:"),
    (L, "except (OSError, EOFError) as ex:", "except ZeroDivisionError as ex:"),
    (L, "if os.path.isdir(p):", "if False:"),
    (L, "if _huella(generaciones(ruta)) == antes and all(g[\"leida\"] for g in gens):", "if True:"),
    (L, "def leer(ruta, intentos=5,", "def leer(ruta, intentos=1,"),
    (L, "\"problemas\": [g[\"ruta\"] + \": \" + g[\"error\"] for g in gens if g[\"error\"]]", "\"problemas\": []"),
    (R, "elif cons and pub:", "elif False:"),
    (R, "elif pub:", "elif False:"),
    (R, "elif cons and not cons[-1].get(\"ok\"):", "elif False:"),
    (R, "if r[\"control_presente\"] or retiro_del_cliente:", "if False:"),
    (R, "trazabilidad=\"completa\", generaciones_del_id", "trazabilidad=\"incompleta\", generaciones_del_id"),
    (R, "r[\"publicacion\"] = (\"confirmada\" if r[\"categoria\"] == \"consumida_y_publicada\"", "r[\"publicacion\"] = (\"confirmada\" if True"),
    (R, "shutil.copy2(p, copia)", "pass"),
    (R, "\"incierto\": not d[\"determinada\"]", "\"incierto\": False"),
    (R, "determinada=False, secuencia_publicada=None, trazabilidad=\"incompleta\",\n                 motivo=\"hay `publicado`", "determinada=True, secuencia_publicada=None, trazabilidad=\"incompleta\",\n                 motivo=\"hay `publicado`"),
]


def main():
    vivos = []
    for i, (f, a, b) in enumerate(MUT):
        src = (AQUI / f).read_text(encoding="utf-8")
        if src.count(a) < 1:
            print(f"M{i:02d} NO APLICA ({f}): {a[:60]!r}")
            vivos.append(i)
            continue
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            for g in AQUI.glob("*.py"):
                shutil.copy(g, t / g.name)
            (t / f).write_text(src.replace(a, b, 1), encoding="utf-8")
            rc = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(t / "test_auditoria_rotacion.py")],
                                capture_output=True, cwd=t, env={**os.environ, "CF_PRODUCTO": os.environ.get("CF_PRODUCTO", "/producto-etapa3"), "CF_EVIDENCIA": ""}).returncode
        print(f"M{i:02d} {'MUERTA' if rc else 'VIVA  '} {f}: {a.strip()[:55]!r}")
        if not rc:
            vivos.append(i)
    print(f"{len(MUT) - len(vivos)}/{len(MUT)} muertas; vivas: {vivos}")
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(main())

