import os
import subprocess
from pathlib import Path

G = Path(__file__).resolve().parent.parent / "guiones" / "b_preflight_apartar_A.sh"


def corre(donde, env):
    r = subprocess.run(["bash", str(G), donde], env={**os.environ, **env}, capture_output=True, text=True)
    return r.returncode, r.stdout


def kali(tmp):
    k = tmp / "k"
    (k / "corrida" / "salidas").mkdir(parents=True)
    for f in ("comando.txt", "generador.rc", "permiso.json", "sha256-esperado.txt", "sha256-esperado.txt.antes-B"):
        (k / f).write_text("x")
    return k, {"CF_K": str(k), "CF_KALI_APARTADA": str(tmp / "apartada"), "CF_TS": "T"}


def test_kali_seco_no_mueve_y_real_conserva_el_manifiesto(tmp_path):
    k, env = kali(tmp_path)
    rc, out = corre("kali", env)
    assert rc == 0 and "SECO" in out and (k / "corrida").exists() and not (tmp_path / "apartada").exists()
    rc, out = corre("kali", {**env, "CF_MODO": "real"})
    assert rc == 0, out
    assert sorted(os.listdir(k)) == ["sha256-esperado.txt", "sha256-esperado.txt.antes-B"]
    assert (tmp_path / "apartada" / "corrida" / "salidas").is_dir() and (tmp_path / "apartada" / "permiso.json").exists()


def test_kali_se_niega_si_el_destino_existe_o_falta_el_manifiesto(tmp_path):
    k, env = kali(tmp_path)
    (tmp_path / "apartada").mkdir()
    assert corre("kali", {**env, "CF_MODO": "real"})[0] == 2 and (k / "corrida").exists()
    (tmp_path / "apartada").rmdir()
    (k / "sha256-esperado.txt").unlink()
    assert corre("kali", {**env, "CF_MODO": "real"})[0] == 2


def test_sensor_aparta_la_fase_completa_y_no_borra(tmp_path):
    o = tmp_path / "4c"
    (o / "replay").mkdir(parents=True)
    (o / "cierre.t").write_text("1")
    (o / "replay" / "rc.txt").write_text("rc=0")
    env = {"CF_FASE_DIR": str(o), "CF_FASE_APARTADA": str(tmp_path / "4c-A"), "CF_TS": "T"}
    assert corre("sensor", env)[0] == 0 and o.exists()
    assert corre("sensor", {**env, "CF_MODO": "real"})[0] == 0
    assert not o.exists() and (tmp_path / "4c-A" / "replay" / "rc.txt").exists()
    assert corre("sensor", {**env, "CF_MODO": "real"})[0] == 0         # ya no hay nada: no falla


def test_modo_invalido(tmp_path):
    assert corre("sensor", {"CF_MODO": "x"})[0] == 2
