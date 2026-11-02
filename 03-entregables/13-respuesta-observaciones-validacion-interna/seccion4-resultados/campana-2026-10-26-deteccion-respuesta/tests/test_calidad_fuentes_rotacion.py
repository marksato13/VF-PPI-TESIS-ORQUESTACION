"""calidad_fuentes.py con la rotación del anillo de la Etapa 4 (-G 5): un fichero de 5 s que falta es un hueco.

Con la duración fija de 15 s del 3B, un hueco de 10 s entre inicios (un fichero de 5 s perdido) quedaba por debajo
de 15 + 2 s y no se detectaba. Ejecutar: python -m pytest tests/test_calidad_fuentes_rotacion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import calidad_fuentes as cf  # noqa: E402

T0 = 1793700000.0


def _arch(inicios):
    return {"inicios": [T0 + s for s in inicios], "fallos": []}


def test_por_defecto_sigue_siendo_15_s():
    assert cf.DURACION_PCAP_S == 15.0
    r = cf.continuidad(_arch(range(0, 120, 15)), T0 + 10, T0 + 100)
    assert r["continuo"] is True


def test_rotacion_5_s_continua():
    r = cf.continuidad(_arch(range(0, 120, 5)), T0 + 10, T0 + 100, duracion=5.0)
    assert r["continuo"] is True and r["huecos"] == []


def test_rotacion_5_s_detecta_un_fichero_perdido():
    inicios = [s for s in range(0, 120, 5) if s != 50]          # falta live-...(T0+50).pcap
    assert cf.continuidad(_arch(inicios), T0 + 10, T0 + 100)["continuo"] is True       # con 15 s: no se ve
    r = cf.continuidad(_arch(inicios), T0 + 10, T0 + 100, duracion=5.0)
    assert r["continuo"] is False and len(r["huecos"]) == 1 and r["huecos"][0]["s"] == 10.0


def test_rotacion_5_s_cubre_fin_con_5_s():
    r = cf.continuidad(_arch(range(0, 100, 5)), T0 + 10, T0 + 100, duracion=5.0)
    assert r["cubre_fin"] is True                                 # último inicio 95 + 5 = 100
    r = cf.continuidad(_arch(range(0, 95, 5)), T0 + 10, T0 + 100, duracion=5.0)
    assert r["cubre_fin"] is False                                # último inicio 90 + 5 < 100
