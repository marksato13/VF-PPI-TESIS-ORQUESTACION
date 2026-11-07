#!/usr/bin/env python3
"""[banco sin red] Desplaza 26 h la franja de las pruebas de E-carga (lunes 03:00Z → domingo 01:00Z) y las corre sobre esa copia.
No toca el producto: copia deploy/, tests/ y scripts/ a una carpeta temporal y cambia allí solo los dos módulos de prueba.
  banco_franja_r6.py RAIZ_PRODUCTO [argumentos de pytest...]
Si algún guion del paquete dependiera de la franja o de la hora anterior, el recorrido completo y los muestreadores fallarían aquí."""
import datetime as dt
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

D = 93600
raiz = pathlib.Path(sys.argv[1])
t = pathlib.Path(tempfile.mkdtemp(prefix="franja-"))
for d in ("deploy", "tests", "scripts"):
    shutil.copytree(raiz / d, t / d)
cambios = 0


def iso(m):
    return (dt.datetime.strptime(m.group(), "%Y-%m-%dT%H:%M:%SZ") - dt.timedelta(seconds=D)).strftime("%Y-%m-%dT%H:%M:%SZ")


def comp(m):
    return (dt.datetime.strptime(m.group(), "%Y%m%dT%H%MZ") - dt.timedelta(seconds=D)).strftime("%Y%m%dT%H%MZ")


for n in ("tests/test_etapa4_ecarga_guardia_s7.py", "tests/test_etapa4_ecarga_prep.py"):
    p = t / n
    s = p.read_bytes().decode()
    s, a = re.subn(r"\b1794\d{6}\b", lambda m: str(int(m.group()) - D), s)
    s, b = re.subn(r"2026-11-09T\d\d:\d\d:\d\dZ", iso, s)
    s, c = re.subn(r"20261109T\d{4}Z", comp, s)
    s, e = re.subn(r"2026-11-09T03:00:0(?=\")", "2026-11-08T01:00:0", s)  # prefijo de T_g en una aserción del recorrido
    b += e
    q = len(re.findall(r"2026-11-09T|20261109T", s))
    assert q == 0, "queda una fecha de la franja anterior"
    p.write_bytes(s.encode())
    cambios += a + b + c
    print(f"{n}: {a} epochs, {b + c} fechas desplazadas, {q} fechas sin hora completa")
    assert not re.search(r"1794(19|20)\d{4}", s), "queda un epoch de la franja anterior"
print(f"total {cambios} sustituciones; T_g de prueba 1794099600")
r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfEs", "--tb=short", "--basetemp=/tmp/bt",
                    "tests/test_etapa4_ecarga_guardia_s7.py", "tests/test_etapa4_ecarga_prep.py", *sys.argv[2:]], cwd=t)
print(f"RC_PYTEST={r.returncode}")
sys.exit(r.returncode)
