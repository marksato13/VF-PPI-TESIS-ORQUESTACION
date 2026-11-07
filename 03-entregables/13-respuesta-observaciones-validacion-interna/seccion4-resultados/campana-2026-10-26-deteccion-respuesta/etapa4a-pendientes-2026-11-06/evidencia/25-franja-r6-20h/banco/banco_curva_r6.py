#!/usr/bin/env python3
"""[banco sin red] Curva factor_horario en cada minuto de la franja r6, con el generador del producto. Sin hosts.
  banco_curva_r6.py RAIZ_PRODUCTO"""
import datetime
import hashlib
import importlib.util
import pathlib
import sys

f = pathlib.Path(sys.argv[1]) / "scripts" / "laboratorio" / "clientes_lab.py"
print("clientes_lab.py", hashlib.sha256(f.read_bytes()).hexdigest())
e = importlib.util.spec_from_file_location("clientes_lab_banco", f)
m = importlib.util.module_from_spec(e)
sys.modules["clientes_lab_banco"] = m
e.loader.exec_module(m)
ini = datetime.datetime(2026, 11, 8, 1, 0)
mins = [ini + datetime.timedelta(minutes=i) for i in range(78)]  # 01:00–02:17 UTC
assert all(d.weekday() == 6 for d in mins)
con = {m.factor_horario(d, True) for d in mins}
sin = {round(m.factor_horario(d, False), 6) for d in mins}
print("con la opción", con, "sin la opción", sin, "minutos", len(mins), mins[0], mins[-1])
assert con == {0.12} and sin == {0.036}
print("RC=0")
