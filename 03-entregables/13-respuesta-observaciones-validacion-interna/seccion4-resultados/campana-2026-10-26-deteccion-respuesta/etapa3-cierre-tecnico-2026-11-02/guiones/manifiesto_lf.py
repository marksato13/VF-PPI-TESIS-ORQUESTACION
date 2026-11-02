"""Pasa a LF los ficheros de texto de la carpeta (lo que git guarda con autocrlf=true) y
regenera MANIFIESTO.sha256 sobre el contenido publicado. Los .gz no se tocan."""
import hashlib
import sys
from pathlib import Path

D = Path(sys.argv[1])
n = 0
for p in sorted(D.rglob("*")):
    if not p.is_file() or p.name == "MANIFIESTO.sha256" or p.suffix == ".gz":
        continue
    b = p.read_bytes()
    if b"\r\n" in b and b"\0" not in b:
        p.write_bytes(b.replace(b"\r\n", b"\n"))
        n += 1
print("convertidos a LF:", n)
lineas = []
for p in sorted((q for q in D.rglob("*") if q.is_file() and q.name != "MANIFIESTO.sha256"),
                key=lambda q: q.relative_to(D).as_posix().encode()):
    lineas.append("%s  %s\n" % (hashlib.sha256(p.read_bytes()).hexdigest(), p.relative_to(D).as_posix()))
(D / "MANIFIESTO.sha256").write_bytes("".join(lineas).encode())
print("ficheros en el manifiesto:", len(lineas))
