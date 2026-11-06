"""Reproducción exacta del defecto de S14 (hueco inmediatamente anterior al primer par saturado), con las funciones del
banco tests/test_etapa4_ecarga_prep.py. Uso: ECARGA_DIRS=<dir> python3 repro_s14.py
Imprime S14 con todas las lecturas y con psi=None en D+100 <= t < D+103, y el recorrido completo hasta veredicto."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/repo/tests")
import test_etapa4_ecarga_prep as b  # noqa: E402

D = b.D
print("herramientas:", os.environ.get("ECARGA_DIRS"))
print("evaluar_s14 VERSION:", b.modulo("evaluar_s14").VERSION)
sat = b.entre(100, 108, cpu=100, psi_cpu=50)
r = b.s14(b.completo(sat))
print("A) lecturas completas: S14 =", r["S14"]["valor"], "| cpu =", r["componentes"]["cpu"]["valor"],
      "|", r["componentes"]["cpu"]["motivo"])


def hueco(t, m):
    if D + 100 <= t < D + 103:
        m["psi"] = None


ls = b.completo(sat, extra=hueco)
r = b.s14(ls)
c = r["componentes"]["cpu"]
print("B) psi=None en [D+100, D+103): S14 =", r["S14"]["valor"], "| cpu =", c["valor"], "|", c["motivo"])
print("   cobertura cpu:", c["ventana"]["cobertura"], "| episodios:", c["ventana"]["episodios"],
      "| dudosos:", c["ventana"].get("dudosos"))
with tempfile.TemporaryDirectory() as t:
    rc, v, e, tr = b.e2e(Path(t) / "e2e", b.lineas(b.serie(D - 3, b.H + 20)), ls, pcap_log=Path(t) / "obs_pcap.log")
    print("C) punta a punta: S14 =", e["S"]["S14"], "| veredicto =", v["estabilidad_tecnica"],
          "| habilita_condicion_3 =", v["habilita_condicion_3"], "| rc =", rc)
