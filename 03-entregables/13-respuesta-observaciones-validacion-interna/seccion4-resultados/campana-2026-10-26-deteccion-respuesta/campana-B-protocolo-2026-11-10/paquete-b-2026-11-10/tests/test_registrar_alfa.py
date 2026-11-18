import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas"))
import registrar_alfa as r  # noqa: E402

PUB = '''UMBRALES_ALFA = {"0.05": -0.5694578968203694, "0.03": -0.5898535710336618,
                 "0.01": -0.6223889502095352}
RETENCION = 1
'''


def arch(tmp, pub=PUB, thr=-0.5693969936322356):
    (tmp / "pub.py").write_text(pub)
    (tmp / "man.json").write_text(json.dumps({"detectors": {"if_limpio_2026_10": {"calibration": {"threshold": thr, "alpha": 0.05}}},
                                               "evaluation": {"if_limpio_2026_10": {"threshold_used": thr}}}))
    (tmp / "m.joblib").write_bytes(b"modelo")
    return str(tmp / "pub.py"), str(tmp / "man.json"), str(tmp / "m.joblib")


def test_motor_con_alfa_001_y_esperado_001(tmp_path):
    x = r.registrar(*arch(tmp_path, thr=-0.6223889502095352), motor_alfa="0.01")
    assert x["ok"] and x["motor"]["umbral"] == -0.6223889502095352 and not x["motor"]["distinto_a_proposito"]
    assert not r.registrar(*arch(tmp_path), motor_alfa="0.01")["ok"]                  # manifiesto viejo con α=0,01 esperado


def test_registro_conforme(tmp_path):
    x = r.registrar(*arch(tmp_path))
    assert x["ok"] and x["motor"]["distinto_a_proposito"] and x["umbral_alfa_experimento"] == -0.6223889502095352
    assert x["motor"]["umbral"] == -0.5693969936322356 and len(x["sha256"]["modelo"]) == 64


def test_detecta_umbral_alfa_modificado(tmp_path):
    x = r.registrar(*arch(tmp_path, PUB.replace("-0.6223889502095352", "-0.60")))
    assert not x["ok"] and "α=0,01" in x["errores"][0]


def test_detecta_que_el_motor_cambio(tmp_path):
    x = r.registrar(*arch(tmp_path, thr=-0.6223889502095352))
    assert not x["ok"] and "motor desplegado cambió" in x["errores"][0]


def test_cli_escribe_el_registro_y_rc(tmp_path):
    p, m, mo = arch(tmp_path)
    assert r.main(["--publicador", p, "--manifiesto", m, "--modelo", mo, "--salida", str(tmp_path / "o.json"), "--motor-alfa", "0.05"]) == 0
    assert r.main(["--publicador", p, "--manifiesto", m, "--modelo", mo, "--salida", str(tmp_path / "o3.json")]) == 1      # por omisión B exige α=0,01 en el motor
    assert json.loads((tmp_path / "o.json").read_text())["ok"]
    (tmp_path / "man.json").write_text(json.dumps({"detectors": {"if_limpio_2026_10": {"calibration": {"threshold": -1.0}}}}))
    assert r.main(["--publicador", p, "--manifiesto", m, "--modelo", mo, "--salida", str(tmp_path / "o2.json")]) == 1
