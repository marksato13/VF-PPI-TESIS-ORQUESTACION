"""Pruebas offline de guardia.py con las muestras REALES del 06-nov (ventana sin incidentes) y variantes sintéticas.
  python3 -m pytest -q test_guardia.py --muestras RUTA/evidencia/06-observacion/bastion/muestras.txt
"""
import importlib.util
import os
import re
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("guardia", Path(__file__).with_name("guardia.py"))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
REAL = Path(os.environ["MUESTRAS_06NOV"]).read_text(encoding="utf-8", errors="replace")


def _cambiar(texto, desde_bloque, patron, nuevo):
    """Aplica la sustitución a partir del bloque n (las muestras anteriores quedan como estaban)."""
    partes = texto.split("### ")
    for i in range(1 + desde_bloque, len(partes)):
        partes[i] = re.sub(patron, nuevo, partes[i], flags=re.M)
    return "### ".join(partes)


def test_observacion_real_del_06nov_no_para():
    r = g.evaluar(REAL)
    assert r["muestras"] > 120 and r["parar"] is False and r["motivos"] == []


@pytest.mark.parametrize("patron,nuevo,clave", [
    (r"memdisp_kb=\d+", "memdisp_kb=900000", "MemAvailable"),
    (r"home_libre_kb=\d+", "home_libre_kb=2000000", "/home"),
    (r"enforce_aplicar=0", "enforce_aplicar=1", "--aplicar/--enforce"),
    (r"aplicar_cmd=0", "aplicar_cmd=1", "agente con --aplicar"),
    (r"^S ruleset=[0-9a-f]+$", "S ruleset=0000000000000000", "ruleset_s"),
    (r"ruleset=e3b0c44298fc1c14", "ruleset=1111111111111111", "ruleset_d"),
    (r"aplicacion=0", "aplicacion=1", "aplicacion nuevos"),
    (r"^S suricata pid=\d+", "S suricata pid=99999", "reinicio de suricata"),
    (r"^B relay pid=\d+ nr=0", "B relay pid=70246 nr=1", "reinicio de relay"),
    (r"^D agente pid=\d+", "D agente pid=1", "reinicio de agente"),
])
def test_cada_condicion_para(patron, nuevo, clave):
    r = g.evaluar(_cambiar(REAL, 40, patron, nuevo))
    assert r["parar"] is True and any(clave in m for m in r["motivos"])


def test_firma_invalida_aislada_no_para_y_sostenida_si():
    partes = REAL.split("### ")
    una = "### ".join(partes[:41] + [re.sub(r"firma_invalida=14", "firma_invalida=15", p) for p in partes[41:]])
    assert g.evaluar(una)["parar"] is False          # una subida y se detiene: no es «sostenida > 60 s»
    sost = list(partes)
    for i in range(41, len(sost)):
        sost[i] = re.sub(r"firma_invalida=14", "firma_invalida=%d" % (15 + (i - 41)), sost[i])
    r = g.evaluar("### ".join(sost))
    assert r["parar"] is True and any("firma_invalido sigue subiendo" in m for m in r["motivos"])


def test_eve_parado_mas_de_60_s_para():
    r = g.evaluar(_cambiar(REAL, 40, r"^S eve_ultimo_stats=\S+", "S eve_ultimo_stats=2026-11-06T04:00:00.000000+0000"))
    assert r["parar"] is True and any("EVE sin stats" in m for m in r["motivos"])


def test_lectura_que_falta_es_aviso_no_cumplimiento():
    r = g.evaluar(_cambiar(REAL, 40, r"^S home_libre_kb=.*$", "S home_libre_kb=ERROR"))
    assert r["parar"] is False and any(a.startswith("SIN_LECTURA") and "recursos" in a for a in r["avisos"])
    assert g.evaluar("")["avisos"] == ["SIN_LECTURA: ninguna muestra"]
