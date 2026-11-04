"""Cruza los blobs del Sensor1 con commits de referencia del producto (solo lectura)."""
import subprocess
import sys
from pathlib import Path

REPO = r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-as-deployed"
REFS = [
    ("snap1029", "f57ca00"),   # snapshot as-deployed 29-oct (motor 7b275b8)
    ("antesDemo", "e41480a"),  # as-deployed justo antes de 866ebbf
    ("demoAC", "3f1bd9c"),     # demo completa (politica A+C + GUI)
    ("actual", "ca66db5"),     # as-deployed publicado ahora
    ("main", "7b275b8"),
    ("c24f8a80", "24f8a80"),   # candidato motor incremental (paso 1/2)
    ("e2_6b6ef82", "6b6ef82"),
    ("e3_ec78ca5", "ec78ca5"),
    ("cand3a9f26b", "3a9f26b"),
]


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, encoding="utf-8").stdout.strip()


def main(entrada, salida):
    filas = []
    for ln in Path(entrada).read_text(encoding="utf-8", errors="replace").splitlines():
        p = ln.split(" ", 5)
        if len(p) == 6 and len(p[0]) == 40 and all(c in "0123456789abcdef" for c in p[0]):
            filas.append((p[0], p[5].strip()))
    out = ["ruta | blob_sensor | coincide_con | primer_commit_con_ese_blob"]
    cache = {}
    for blob, ruta in filas:
        coinc = []
        for nombre, c in REFS:
            k = (c, ruta)
            if k not in cache:
                cache[k] = git("rev-parse", "--verify", "-q", f"{c}:{ruta}")
            if cache[k] == blob:
                coinc.append(nombre)
        if coinc:
            prim = ""
        else:
            prim = git("log", "--all", "--format=%h %ad %s", "--date=short", f"--find-object={blob}", "-1") or "NO ESTA EN NINGUN COMMIT"
        enrepo = any(cache[(c, ruta)] for _, c in REFS)
        out.append(f"{ruta} | {blob[:10]} | {','.join(coinc) or '-'} | {prim if not coinc else ''}{'' if enrepo else ' (ruta ausente en refs)'}")
    Path(salida).write_text("\n".join(out), encoding="utf-8")
    print(f"{len(filas)} ficheros -> {salida}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

