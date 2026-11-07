"""Muestras legibles del banco (mismo entorno que test_p0_r2.py): imprime
  1) la salida del bloque sensor1_r2 en modo derivado sobre un paquete escribible, con el inventario antes/después;
  2) el resumen.txt del manejador ANTIGUO y de la r2 con los 9 ssh fallidos;
  3) el resumen.txt de la r2 con todo correcto (anticipado).
Uso (dentro del contenedor): python3 muestras.py DIR_TEMPORAL"""
import sys
from pathlib import Path

import test_p0_r2 as t

base = Path(sys.argv[1])
d = base / "m1"; d.mkdir(parents=True)
pkg, sumas = t.paquete(d)
antes = t.inventario(pkg)
rc, reqs, out = t.bloque("sensor1_r2.sh", t.host(d), "p0-muestra", "banco", sumas, "0", "9999999999")
despues = t.inventario(pkg)
print("######## 1) sensor1_r2.sh (paquete escribible con la .2 de 902991e; mecanismo derivado), rc", rc)
print(out)
print(f"inventario del paquete: {len(antes)} entradas antes, {len(despues)} después, idéntico={antes == despues}")
print("__pycache__ en el paquete:", sorted(str(p.relative_to(pkg)) for p in pkg.rglob("__pycache__")) or "ninguno")
for nombre, kw in (("ANTIGUO p0_anticipado.sh", {"driver": t.P16 / "p0" / "p0_anticipado.sh"}), ("r2 p0_r2.sh", {})):
    d = base / nombre.split()[0]; d.mkdir()
    r, s = t.correr(d, todos_255=True, **kw)
    print(f"######## 2) {nombre} con ssh rc 255 en los 9 bloques -> rc del proceso = {r.returncode}")
    print((s / "resumen.txt").read_text())
d = base / "ok"; d.mkdir()
r, s = t.correr(d)
print(f"######## 3) r2 anticipado, todo correcto -> rc = {r.returncode}")
print((s / "resumen.txt").read_text())
