"""Ensayo de BANCO de los guiones del paquete (instalación, aceptación y reversión por host) sobre árboles FALSOS (HOME y /etc en una carpeta temporal; sin systemd, sin sudo,
sin red). No toca ningún host. Uso: CF_PAQUETE_FUENTE=<paquete-despliegue> CF_PRODUCTO=<producto-etapa3> CF_HERRAMIENTAS=<herramientas> pytest."""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

FUENTE = Path(os.environ.get("CF_PAQUETE_FUENTE", Path(__file__).resolve().parent))
PRODUCTO = Path(os.environ.get("CF_PRODUCTO", "/producto-etapa3"))
HERR = Path(os.environ.get("CF_HERRAMIENTAS", "/herramientas"))
ORIG_SHA = "5733f17d39bfa5fe667ee13aecd133ea4859834899c5f4f6ea21360ebe4002a2"
CLAVE_EXISTENTE = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEXISTENTEEXISTENTEEXISTENTEEXISTENTEEXIS clave-del-laboratorio-existente"
EXEC = ("ExecStart={h}/cyberflow/.venv/bin/python {h}/cyberflow-e4/ec78ca5/scripts/engine/publicar_feed_v2.py \\\n    --log {h}/cyberflow/logs/motor_decision.log \\\n    --estado {h}/feed-v2/estado.json \\\n    --politica if_senal --vigencia-segundos 60 --refresco-segundos 20 --seguir")


def sh(script, *args, env=None, cwd=None):
    e = {**os.environ, **(env or {})}
    return subprocess.run(["bash", str(script), *args], capture_output=True, text=True, env=e, cwd=cwd)


def snapshot(raiz):
    return sorted((str(p.relative_to(raiz)), hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "dir") for p in Path(raiz).rglob("*"))


@pytest.fixture
def pq(tmp_path):
    d = tmp_path / "paquete"
    shutil.copytree(FUENTE, d, ignore=shutil.ignore_patterns("test_guiones_paquete.py", "__pycache__", "pendiente-sudo"))
    for s in d.glob("*.sh"):
        s.chmod(0o755)
    return d


@pytest.fixture
def sensor(tmp_path, pq):
    home = tmp_path / "m4rk"
    eng = home / "cyberflow-e4" / "ec78ca5" / "scripts" / "engine"
    eng.mkdir(parents=True)
    shutil.copy(PRODUCTO / "scripts" / "engine" / "publicar_feed_v2.py", eng / "publicar_feed_v2.py")
    (home / ".ssh").mkdir(mode=0o700)
    (home / ".ssh" / "authorized_keys").write_text(CLAVE_EXISTENTE + "\n")
    os.chmod(home / ".ssh" / "authorized_keys", 0o600)
    (home / "feed-v2").mkdir()
    os.chmod(eng, 0o555)                                                        # como el Sensor1 real: el árbol candidato es de solo lectura
    etc = tmp_path / "etc"
    etc.mkdir()
    (tmp_path / "pub.pub").write_text("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBASTIONBASTIONBASTIONBASTIONBASTIONBASTION cf-bastion-d5\n")
    (tmp_path / "execstart").write_text(EXEC.format(h=home))
    env = {"CF_HOME": str(home), "CF_ETC": str(etc), "CF_PAQUETE": str(pq), "CF_PUBKEY": str(tmp_path / "pub.pub"), "CF_SIN_SYSTEMD": "1", "CF_FROM": "10.10.10.30", "CF_EXECSTART_FILE": str(tmp_path / "execstart")}
    return home, etc, env, pq


def test_todos_los_guiones_tienen_sintaxis_valida(pq):
    for s in pq.glob("*.sh"):
        assert subprocess.run(["bash", "-n", str(s)], capture_output=True).returncode == 0, s.name


def test_modo_seco_de_todos_los_guiones_y_aceptar_no_escriben_nada(sensor, tmp_path, pq):
    home, etc, env, _ = sensor
    gh = tmp_path / "gadmin"
    (gh / "cf-b" / "herramientas").mkdir(parents=True)
    for f in ("d5_episodio.py", "compuerta_b.py", "orquestar_b.py"):
        shutil.copy(HERR / f, gh / "cf-b" / "herramientas" / f)
    envb = {"CF_HOME": str(gh), "CF_PAQUETE": str(pq), "CF_HOSTKEY": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOS"}
    antes = snapshot(tmp_path)
    for script, accion, e in (("cf_d5_sensor1.sh", "instalar", env), ("cf_d5_sensor1.sh", "revertir", env), ("cf_d5_sensor1.sh", "aceptar", env), ("cf_d5_bastion.sh", "clave", envb),
                              ("cf_d5_bastion.sh", "instalar", envb), ("cf_d5_bastion.sh", "revertir", envb), ("cf_d5_bastion.sh", "aceptar", envb)):
        sh(pq / script, accion, env=e)
        assert snapshot(tmp_path) == antes, (script, accion)
    for host in ("kali", "clientes", "srvdmz"):
        for accion in ("instalar", "revertir", "aceptar"):
            sh(pq / "cf_d5_instrumentacion.sh", host, accion, env={"CF_HOME": str(tmp_path / host), "CF_PAQUETE": str(pq)})
    assert not (tmp_path / "kali").exists() and not (tmp_path / "clientes").exists() and not (tmp_path / "srvdmz").exists()


def test_el_paquete_coincide_con_su_sha256sums_y_el_derivado_es_el_validado(pq):
    assert subprocess.run(["sha256sum", "-c", "SHA256SUMS", "--quiet"], cwd=pq, capture_output=True).returncode == 0
    assert hashlib.sha256((pq / "publicar_feed_v2_d5.py").read_bytes()).hexdigest().startswith("58e2a0b2b0690892")


def test_sensor1_en_seco_no_cambia_nada(sensor):
    home, etc, env, pq = sensor
    antes = snapshot(home.parent)
    r = sh(pq / "cf_d5_sensor1.sh", "instalar", env=env)
    assert r.returncode == 0 and "[seco]" in r.stdout and snapshot(home.parent) == antes


def test_sensor1_instalar_aceptar_y_revertir_sobre_arbol_falso(sensor):
    home, etc, env, pq = sensor
    ak = home / ".ssh" / "authorized_keys"
    original_ak = ak.read_text()
    orig_pub = hashlib.sha256((home / "cyberflow-e4" / "ec78ca5" / "scripts" / "engine" / "publicar_feed_v2.py").read_bytes()).hexdigest()
    assert orig_pub == ORIG_SHA
    r = sh(pq / "cf_d5_sensor1.sh", "instalar", "--aplicar", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    t = ak.read_text().splitlines()
    mia = [l for l in t if "cf-bastion-d5" in l]
    assert t[0] == CLAVE_EXISTENTE and len(mia) == 1 and mia[0].startswith('from="10.10.10.30",command="/usr/bin/python3 -I ') and '",restrict ssh-ed25519 ' in mia[0] and "--ssh-original" in mia[0]
    assert oct(ak.stat().st_mode & 0o777) == "0o600" and oct((home / "feed-v2/d5/control").stat().st_mode & 0o777) == "0o700" and oct((home / "feed-v2/d5/auditoria").stat().st_mode & 0o777) == "0o750"
    assert list((home / "cf-b" / "respaldo-d5").glob("*/authorized_keys")) and list((home / "cf-b" / "respaldo-d5").glob("*/authorized_keys.sha256"))
    assert hashlib.sha256((home / "cyberflow-e4/ec78ca5/scripts/engine/publicar_feed_v2.py").read_bytes()).hexdigest() == orig_pub        # el original NO se tocó
    assert (home / "cf-b/d5/publicar_feed_v2_d5.py").exists() and not (home / "cyberflow-e4/ec78ca5/scripts/engine/publicar_feed_v2_d5.py").exists()      # fuera del árbol candidato (de solo lectura)
    dp = (pq / "pendiente-sudo" / "zz-d5-sin-reinicio.conf").read_text()
    assert dp.startswith("[Service]\nEnvironment=PYTHONPATH=%s/cyberflow-e4/ec78ca5/scripts/engine\nExecStart=\nExecStart=" % home) and "cf-b/d5/publicar_feed_v2_d5.py" in dp and "--control-d5 %s/feed-v2/d5/control/control.json" % home in dp and "--d5-origen 10.10.20.30" in dp and "publicar_feed_v2.py " not in dp and "\\\n" not in dp.split("ExecStart=\n")[1] and "--estado %s/feed-v2/estado.json" % home in dp and dp.count("ExecStart=") == 2     # el ExecStart multilínea se une entero
    assert "SUDO PENDIENTE" in r.stdout
    # idempotencia: repetir no duplica la clave
    assert sh(pq / "cf_d5_sensor1.sh", "instalar", "--aplicar", env=env).returncode == 0 and len([l for l in ak.read_text().splitlines() if "cf-bastion-d5" in l]) == 1
    # aceptación: sin el sudo de Mark FALLAN exactamente el drop-in y logrotate; con él, pasa
    r = sh(pq / "cf_d5_sensor1.sh", "aceptar", env=env)
    assert r.returncode != 0 and r.stdout.count("FALLA ") == 2 and "drop-in" in r.stdout and "logrotate presente" in r.stdout
    (etc / "systemd/system/ppi-publicar-feed-v2.service.d").mkdir(parents=True)
    (etc / "logrotate.d").mkdir(parents=True)
    shutil.copy(pq / "pendiente-sudo" / "zz-d5-sin-reinicio.conf", etc / "systemd/system/ppi-publicar-feed-v2.service.d/zz-d5-sin-reinicio.conf")
    shutil.copy(pq / "pendiente-sudo" / "cf-d5-auditoria", etc / "logrotate.d/cf-d5-auditoria")
    r = sh(pq / "cf_d5_sensor1.sh", "aceptar", env=env)
    assert r.returncode == 0 and "0 FALLAN" in r.stdout, r.stdout
    assert "comando fuera de la lista blanca rechazado" in r.stdout
    # reversión: authorized_keys vuelve EXACTAMENTE al original; el derivado se retira; lo de d5 se ARCHIVA con hash
    (home / "feed-v2/d5/auditoria/d5-auditoria.jsonl").write_text('{"evento": "consumido"}\n')
    r = sh(pq / "cf_d5_sensor1.sh", "revertir", "--aplicar", env=env)
    assert r.returncode == 0 and ak.read_text() == original_ak and "SUDO PENDIENTE" in r.stdout
    assert not (home / "cf-b/d5/publicar_feed_v2_d5.py").exists() and not (home / "feed-v2" / "d5").exists() and list((home / "cf-b" / "respaldo-d5").glob("publicar_feed_v2_d5.py.retirado-*"))
    arch = [x for x in (home / "feed-v2").glob("d5-archivado-*") if x.is_dir()]
    assert len(arch) == 1 and (arch[0] / "auditoria" / "d5-auditoria.jsonl").exists() and list((home / "feed-v2").glob("d5-archivado-*.sha256"))


def test_si_un_artefacto_no_coincide_con_sha256sums_no_se_instala_nada(sensor):
    home, etc, env, pq = sensor
    (pq / "sensor_control_d5.py").write_text("# manipulado\n")
    antes = snapshot(home.parent)
    r = sh(pq / "cf_d5_sensor1.sh", "instalar", "--aplicar", env=env)
    assert r.returncode == 3 and "NO coinciden" in r.stdout and snapshot(home.parent) == antes


def test_si_el_publicador_original_no_es_el_conocido_no_se_instala(sensor):
    home, etc, env, pq = sensor
    (home / "cyberflow-e4/ec78ca5/scripts/engine/publicar_feed_v2.py").write_text("# otro\n")
    assert sh(pq / "cf_d5_sensor1.sh", "instalar", "--aplicar", env=env).returncode == 3


def test_bastion_clave_instalar_aceptar_y_revertir(tmp_path, pq):
    home = tmp_path / "gadmin"
    herr = home / "cf-b" / "herramientas"
    herr.mkdir(parents=True)
    for f in ("d5_episodio.py", "compuerta_b.py", "orquestar_b.py"):
        shutil.copy(HERR / f, herr / f)
    orig = {f: hashlib.sha256((herr / f).read_bytes()).hexdigest() for f in ("d5_episodio.py", "compuerta_b.py", "orquestar_b.py")}
    env = {"CF_HOME": str(home), "CF_PAQUETE": str(pq), "CF_HOSTKEY": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOSTHOS"}
    assert sh(pq / "cf_d5_bastion.sh", "instalar", env=env).returncode == 0                       # seco
    assert not (herr / "lanzador_puerta_banco.py").exists()
    r = sh(pq / "cf_d5_bastion.sh", "clave", "--aplicar", env=env)
    assert r.returncode == 0 and "ssh-ed25519 " in r.stdout and oct((home / ".ssh/cyberflow-d5-sensor").stat().st_mode & 0o777) == "0o600"
    kid = (home / ".ssh/cyberflow-d5-sensor").read_bytes()
    assert sh(pq / "cf_d5_bastion.sh", "clave", "--aplicar", env=env).returncode == 0 and (home / ".ssh/cyberflow-d5-sensor").read_bytes() == kid     # no se sobrescribe
    env["CF_HOSTKEY"] = (tmp_path / "hk.pub").write_text("") or ""
    hk = subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(tmp_path / "hk")], capture_output=True)
    env["CF_HOSTKEY"] = " ".join((tmp_path / "hk.pub").read_text().split()[:2])
    r = sh(pq / "cf_d5_bastion.sh", "instalar", "--aplicar", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    r = sh(pq / "cf_d5_bastion.sh", "aceptar", env=env)
    assert r.returncode == 0 and "0 FALLAN" in r.stdout, r.stdout
    assert {f: hashlib.sha256((herr / f).read_bytes()).hexdigest() for f in orig} == orig                  # los originales del bastión NO se modificaron
    r = sh(pq / "cf_d5_bastion.sh", "revertir", "--aplicar", env=env)
    assert r.returncode == 0 and not (herr / "lanzador_puerta_banco.py").exists() and not (home / ".ssh/cyberflow-d5-sensor").exists()
    assert list((home / "cf-b" / "respaldo-d5").glob("cyberflow-d5-sensor.retirada-*")) and {f: hashlib.sha256((herr / f).read_bytes()).hexdigest() for f in orig} == orig


@pytest.mark.parametrize("host", ["kali", "clientes", "srvdmz"])
def test_instrumentacion_por_host_instalar_aceptar_y_revertir(tmp_path, pq, host):
    home = tmp_path / host
    home.mkdir()
    env = {"CF_HOME": str(home), "CF_PAQUETE": str(pq)}
    s = pq / "cf_d5_instrumentacion.sh"
    assert sh(s, host, "instalar", env=env).returncode == 0 and not (home / "cf-b" / "instrumentacion").exists()      # seco
    assert sh(s, host, "instalar", "--aplicar", env=env).returncode == 0
    r = sh(s, host, "aceptar", env=env)
    assert r.returncode == 0 and "0 FALLAN" in r.stdout, r.stdout
    assert sh(s, host, "revertir", "--aplicar", env=env).returncode == 0
    assert not (home / "cf-b" / "instrumentacion").exists() and list((home / "cf-b" / "respaldo-d5").glob("instrumentacion.retirada-*"))
