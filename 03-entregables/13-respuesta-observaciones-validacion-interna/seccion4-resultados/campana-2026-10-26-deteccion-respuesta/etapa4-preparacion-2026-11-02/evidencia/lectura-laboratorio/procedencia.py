"""Procedencia del codigo en disco de Sensor1: compara cada sha256 leido con el blob de varios commits.

Uso: python procedencia.py <s1_detalle.txt> <repo> <salida.json> <commit>...
"""
import hashlib
import json
import re
import subprocess
import sys

det, repo, salida, *commits = sys.argv[1:]
filas = []
for l in open(det, encoding="utf-8", errors="replace"):
    m = re.match(r"^([0-9a-f]{64}) (\d+) (\d+) ((scripts|configs)/\S+)$", l.strip())
    if m:
        filas.append({"ruta": m.group(4), "sha256": m.group(1), "mtime": int(m.group(2)), "ctime": int(m.group(3))})


def blob(c, ruta):
    r = subprocess.run(["git", "-C", repo, "show", f"{c}:{ruta}"], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


res = []
for f in filas:
    coincide = {}
    for c in commits:
        h = blob(c, f["ruta"])
        coincide[c] = "igual" if h == f["sha256"] else ("ausente" if h is None else "distinto")
    res.append({**f, "commits": coincide})
json.dump({"commits": commits, "ficheros": res}, open(salida, "w", encoding="utf-8"), indent=1)
inter = [r for r in res if r["ruta"].startswith(("scripts/engine/", "scripts/features/", "configs/features/", "configs/cyberflow"))]
print("fichero".ljust(52), " ".join(c[:8].ljust(9) for c in commits))
for r in inter:
    print(r["ruta"][:52].ljust(52), " ".join(r["commits"][c][:8].ljust(9) for c in commits))
for c in commits:
    n = sum(1 for r in res if r["commits"][c] == "igual")
    print(c, "iguales", n, "de", len(res))
