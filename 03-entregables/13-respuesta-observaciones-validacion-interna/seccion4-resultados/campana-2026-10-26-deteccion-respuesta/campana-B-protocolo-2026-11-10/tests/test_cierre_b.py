"""El cierre de B con cf_4b_rotacion (systemd FALSO): el árbol que dejaría B pasa 'cierre' con fase 4c o b,
y la ausencia del marcador del orquestador (replay/rc.txt) o un rc distinto de 0 impiden la reanudación normal."""
import importlib.util
import os
import pathlib
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent.parent
ENM = RAIZ / "etapa4-4b-enmienda-p1-2026-11-08"
os.environ.setdefault("CF_SCRIPT", str(ENM / "herramientas" / "cf_4b_rotacion.py"))
sys.path.insert(0, str(ENM / "tests"))
spec = importlib.util.spec_from_file_location("t_rot", ENM / "tests" / "test_cf_4b_rotacion.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
ent = t.ent  # fixture con systemd falso, definido en la suite de la herramienta


@pytest.mark.parametrize("fase", ["4c", "b"])
def test_arbol_de_b_pasa_el_cierre(ent, fase):
    t.armado(ent)
    t.cierre_completo(ent)
    os.rename(ent.home / "cf-e4/4b", ent.home / f"cf-e4/{fase}")
    (ent.home / f"cf-e4/{fase}/replay/rc.txt").write_text("rc=0 (orquestador de la campaña B; no hubo replay)\n")
    r = ent.run("cierre", "--fase", fase)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("marcador", ["falta", "rc1"])
def test_sin_marcador_del_orquestador_no_cierra(ent, marcador):
    t.armado(ent)
    t.cierre_completo(ent)
    os.rename(ent.home / "cf-e4/4b", ent.home / "cf-e4/b")
    m = ent.home / "cf-e4/b/replay/rc.txt"
    if marcador == "falta":
        m.unlink()
    else:
        m.write_text("rc=1 (orquestador de la campaña B)\n")
    r = ent.run("cierre", "--fase", "b")
    assert r.returncode != 0 and "replay" in (r.stdout + r.stderr)


def test_el_tope_reanuda_logrotate_aunque_B_nunca_cierre(ent):
    """Sin cierre exitoso la reanudación normal no ocurre; el tope absoluto sí devuelve logrotate."""
    t.armado(ent)
    assert ent.timer() == "inactive"
    r = ent.run("reanudar-tope")
    assert r.returncode == 0 and ent.timer() == "active"
