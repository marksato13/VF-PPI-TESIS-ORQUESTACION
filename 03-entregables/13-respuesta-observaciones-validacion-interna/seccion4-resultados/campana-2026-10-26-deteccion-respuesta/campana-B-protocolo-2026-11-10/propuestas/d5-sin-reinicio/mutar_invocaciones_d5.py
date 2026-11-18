#!/usr/bin/env python3
"""Mutaciones de la persistencia del bloqueo (hacer_d5_episodio_banco.py): cada una debe hacer fallar alguna prueba de test_invocaciones_d5.py."""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

AQUI = pathlib.Path(__file__).resolve().parent
F = "hacer_d5_episodio_banco.py"
MUT = [
    ("        if self.estado_bloqueo and os.path.exists(self.estado_bloqueo):\n            try:", "        if False:\n            try:"),
    ("            os.replace(tmp, self.estado_bloqueo)\n", "            pass\n"),
    ("        fcntl.flock(fh, fcntl.LOCK_EX)\n", "        pass\n"),
    ("                return {\"motivos\": [\"fichero de bloqueo ilegible", "                return None  # {\"motivos\": [\"fichero de bloqueo ilegible"),
    ("            if self.estado_bloqueo and os.path.exists(self.estado_bloqueo):                  # el caso bloqueado", "            if False:                  # el caso bloqueado"),
    ("            if not res[\"lista\"]:\n                self._fijar_bloqueo(res)", "            if False:\n                self._fijar_bloqueo(res)"),
    ("        if not str(quien).strip() or not str(motivo).strip():", "        if False:"),
    ("            self._log({\"evento\": \"reanudacion_manual\", \"por\": quien", "            self._log({\"evento\": \"x\", \"por\": quien"),
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
            rc = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(t / "test_invocaciones_d5.py")],
                                capture_output=True, cwd=t, env={**os.environ, "CF_EVIDENCIA": ""}).returncode
        print(f"M{i:02d} {'MUERTA' if rc else 'VIVA  '} {a.strip()[:55]!r}")
        if not rc:
            vivos.append(i)
    print(f"{len(MUT) - len(vivos)}/{len(MUT)} muertas; vivas: {vivos}")
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(main())
