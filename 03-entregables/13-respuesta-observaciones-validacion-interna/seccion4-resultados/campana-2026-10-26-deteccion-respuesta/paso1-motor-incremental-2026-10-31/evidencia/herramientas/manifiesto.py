"""Manifiesto sha256 de la carpeta del paso 1 (rutas relativas, una por linea). --verificar lo comprueba."""
import hashlib
import pathlib
import sys

b = pathlib.Path(sys.argv[1])
m = b / "MANIFIESTO.sha256"
if len(sys.argv) > 2 and sys.argv[2] == "--verificar":
    lineas = m.read_text(encoding="utf-8").splitlines()
    malos = [l for l in lineas if hashlib.sha256((b / l[66:]).read_bytes()).hexdigest() != l[:64]]
    print(len(lineas), "entradas,", len(malos), "fallos")
    sys.exit(1 if malos else 0)
viejo = b / "evidencia" / "MANIFIESTO.sha256"
if viejo.exists():
    viejo.unlink()
fs = sorted(p for p in b.rglob("*") if p.is_file() and p.name != "MANIFIESTO.sha256")
m.write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(b).as_posix()}\n" for p in fs),
             encoding="utf-8", newline="\n")
print(len(fs), "archivos", round(sum(p.stat().st_size for p in fs) / 1e6, 1), "MB")
