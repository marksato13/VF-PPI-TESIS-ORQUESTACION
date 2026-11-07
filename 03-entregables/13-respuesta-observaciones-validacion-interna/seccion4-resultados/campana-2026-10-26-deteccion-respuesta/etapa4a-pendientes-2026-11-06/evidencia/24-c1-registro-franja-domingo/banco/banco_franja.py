#!/usr/bin/env python3
"""[banco sin red] Desplaza 24 h la franja escrita en las pruebas de E-carga y corre las pruebas sobre esa copia.
No toca el producto: copia deploy/, tests/ y scripts/ a una carpeta temporal y cambia allí solo los dos módulos de prueba.
  banco_franja.py RAIZ_PRODUCTO [argumentos de pytest...]
Si algún guion del paquete dependiera de la franja anterior, el recorrido completo y los muestreadores fallarían aquí."""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

raiz = pathlib.Path(sys.argv[1])
t = pathlib.Path(tempfile.mkdtemp(prefix="franja-"))
for d in ("deploy", "tests", "scripts"):
    shutil.copytree(raiz / d, t / d)
cambios = 0
for n in ("tests/test_etapa4_ecarga_guardia_s7.py", "tests/test_etapa4_ecarga_prep.py"):
    p = t / n
    s = p.read_bytes().decode()
    s, a = re.subn(r"\b1794\d{6}\b", lambda m: str(int(m.group()) - 86400), s)
    s, b = re.subn(r"2026-11-09T", "2026-11-08T", s)
    s, c = re.subn(r"20261109T", "20261108T", s)
    p.write_bytes(s.encode())
    cambios += a + b + c
    print(f"{n}: {a} epochs, {b + c} fechas desplazadas")
    assert not re.search(r"1794(19|20)\d{4}", s), "queda un epoch de la franja anterior"
print(f"total {cambios} sustituciones; T_g de prueba 1794106800")
r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfEs", "--tb=short", "--basetemp=/tmp/bt",
                    "tests/test_etapa4_ecarga_guardia_s7.py", "tests/test_etapa4_ecarga_prep.py", *sys.argv[2:]], cwd=t)
print(f"RC_PYTEST={r.returncode}")
sys.exit(r.returncode)
