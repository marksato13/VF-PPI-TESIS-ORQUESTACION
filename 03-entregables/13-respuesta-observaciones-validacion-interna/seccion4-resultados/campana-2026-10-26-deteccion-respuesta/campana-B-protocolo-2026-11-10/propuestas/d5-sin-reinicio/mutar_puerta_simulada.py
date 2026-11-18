#!/usr/bin/env python3
"""Mutaciones del simulador (puerta_simulada_banco.py): cada una debe hacer fallar alguna prueba de test_puerta_simulada.py."""
import os, pathlib, shutil, subprocess, sys, tempfile

AQUI = pathlib.Path(__file__).resolve().parent
F = "puerta_simulada_banco.py"
MUT = [
    ("        if self.bloqueada is not None:", "        if False:"),
    ("        if r[\"ok\"]:", "        if True:"),
    ("        self.bloqueada = r\n", "        pass\n"),
    ("        self.bloqueada = None\n", "        pass\n"),
    ("\"omitida_por_caso_fallido\"", "\"x\""),
    ("            self.omitidas += 1", "            pass"),
    ("        self.solicitudes += 1", "        pass"),
    ("return {\"lista\": False, \"intentos\": 0}", "return {\"lista\": True, \"intentos\": 0}"),
]


def main():
    vivos = []
    src = (AQUI / F).read_text(encoding="utf-8")
    for i, (a, b) in enumerate(MUT):
        if src.count(a) < 1:
            print(f"M{i:02d} NO APLICA: {a[:60]!r}")
            vivos.append(i)
            continue
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            for g in AQUI.glob("*.py"):
                shutil.copy(g, t / g.name)
            (t / F).write_text(src.replace(a, b, 1), encoding="utf-8")
            rc = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(t / "test_puerta_simulada.py")],
                                capture_output=True, cwd=t, env={**os.environ, "CF_EVIDENCIA": ""}).returncode
        print(f"M{i:02d} {'MUERTA' if rc else 'VIVA  '} {a.strip()[:55]!r}")
        if not rc:
            vivos.append(i)
    print(f"{len(MUT) - len(vivos)}/{len(MUT)} muertas; vivas: {vivos}")
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(main())