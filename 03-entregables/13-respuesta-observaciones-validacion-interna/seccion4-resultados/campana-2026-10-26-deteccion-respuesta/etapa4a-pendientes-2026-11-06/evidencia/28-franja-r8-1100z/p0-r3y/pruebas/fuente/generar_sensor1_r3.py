"""Genera bloques/sensor1_r3.sh a partir de la plantilla y del texto PUBLICADO de sensor1_muestreadores.sh .3 y .4.

  python3 -I generar_sensor1_r3.py PLANTILLA GUION_3 GUION_4 COMMIT_PRODUCTO SALIDA

Exige que la .4 sea la .3 con EXACTAMENTE tres cambios (línea 2, líneas 22-25 y líneas 63-64); copia el texto nuevo de
esos dos tramos dentro del bloque (BLOQUE_A y BLOQUE_B) y fija V4 = sha256 de la .4. El bloque, en el host, vuelve a
derivar la .4 y exige ese sha: si la plantilla o el texto copiado no coincidieran, no ejecutaría nada.
"""
import difflib
import hashlib
import sys
from pathlib import Path

plantilla, g3, g4, commit, salida = sys.argv[1:6]
t3 = Path(g3).read_text(encoding="utf-8").split("\n")
t4 = Path(g4).read_text(encoding="utf-8").split("\n")
ops = [o for o in difflib.SequenceMatcher(None, t3, t4, autojunk=False).get_opcodes() if o[0] != "equal"]
tramos = [(i1 + 1, i2) for _, i1, i2, _, _ in ops]                    # líneas 1-based de la .3 sustituidas
assert tramos == [(2, 2), (22, 25), (63, 64)], tramos
assert all(o[0] == "replace" for o in ops), ops
assert t4[1] == t3[1].replace("VERSION 2026-11-06.3.", "VERSION 2026-11-06.4."), (t3[1], t4[1])
bloque_a = "\n".join(t4[ops[1][3]:ops[1][4]])
bloque_b = "\n".join(t4[ops[2][3]:ops[2][4]])
for b, fin in ((bloque_a, "FIN_TEXTO_PUBLICADO_A"), (bloque_b, "FIN_TEXTO_PUBLICADO_B")):
    assert fin not in b and not b.endswith("\n")
v4 = hashlib.sha256(Path(g4).read_bytes()).hexdigest()
t = Path(plantilla).read_text(encoding="utf-8")
for k, v in (("@@V4@@", v4), ("@@COMMIT_PRODUCTO@@", commit), ("@@BLOQUE_A@@", bloque_a), ("@@BLOQUE_B@@", bloque_b)):
    assert k in t, k
    t = t.replace(k, v)
assert "@@" not in t.replace("\n".join([bloque_a, bloque_b]), "")
Path(salida).write_text(t, encoding="utf-8", newline="\n")
print(f"{salida}: V4={v4} commit={commit} tramos={tramos} sha={hashlib.sha256(t.encode()).hexdigest()}")
