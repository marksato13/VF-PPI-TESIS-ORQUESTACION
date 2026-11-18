#!/usr/bin/env python3
"""Mutaciones de la integración (hacer_d5_episodio_banco.py): cada una debe hacer fallar alguna prueba de test_integracion_d5.py."""
import os, pathlib, shutil, subprocess, sys, tempfile

AQUI = pathlib.Path(__file__).resolve().parent
F = "hacer_d5_episodio_banco.py"
MUT = [
    ("            if b is not None:\n                self.bloqueada = b", "            if False:\n                self.bloqueada = b"),
    ("        self.bloqueada = res\n        if self.estado_bloqueo:", "        if self.estado_bloqueo:"),
    ("        if not str(quien).strip() or not str(motivo).strip():", "        if False:"),
    ("            self._log({\"evento\": \"reanudacion_manual\", \"por\": quien", "            self._log({\"evento\": \"x\", \"por\": quien"),
    ("    if r[\"ok\"]:\n        q = r.get", "    if True:\n        q = r.get"),
    ("r.get(\"t_limpio\", self.ahora())", "self.ahora()"),
    ("    if not real:\n        return dict(base, ok=True", "    if False:\n        return dict(base, ok=True"),
    ("\"bloqueada\": self._bloqueo_actual() is not None}", "\"bloqueada\": False}"),
    ("            self.omitidas += 1", "            pass"),
    ("    if origen != ORIGEN:\n        return {\"ok\": False, \"rc\": 2, \"motivo\": \"la limpieza D5 solo", "    if False:\n        return {\"ok\": False, \"rc\": 2, \"motivo\": \"la limpieza D5 solo"),
    ("acuse=True, duplicada", "acuse=False, duplicada"),
    ("        self.intentos_de_puerta += 1\n", "        pass\n"),
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
            rc = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(t / "test_integracion_d5.py")],
                                capture_output=True, cwd=t, env={**os.environ, "CF_EVIDENCIA": ""}).returncode
        print(f"M{i:02d} {'MUERTA' if rc else 'VIVA  '} {a.strip()[:55]!r}")
        if not rc:
            vivos.append(i)
    print(f"{len(MUT) - len(vivos)}/{len(MUT)} muertas; vivas: {vivos}")
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(main())