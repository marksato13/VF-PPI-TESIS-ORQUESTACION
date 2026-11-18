"""OpenSSH REAL en un banco aislado (contenedor `--network none`, solo loopback 127.0.0.1): `sshd` de OpenSSH con claves de huésped y de usuario EXCLUSIVAS DE PRUEBA
generadas aquí (ninguna clave ni conexión del laboratorio entra en el banco). Bastión = usuario `gadmin` (uid 1002, su cliente ssh); Sensor1 = usuario `m4rk` (uid 1001,
árbol 0700, publicador como proceso suyo). Se ejerce el comando forzado, `restrict`, la lista permitida, la identidad del servidor fijada, el corte tras recibir y la
reconexión. Requiere root. Los tiempos observados se escriben en CF_EVIDENCIA/tiempos-ssh.json (si está definida)."""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import test_transporte_d5 as TT  # noqa: E402  (módulo hermano; hereda el salto si no es root)
import transporte_bastion as tb  # noqa: E402
from test_transporte_d5 import Nft, Sensor, banco_mod, derivado  # noqa: E402,F401
import adaptador_banco as ab  # noqa: E402

if not Path("/usr/sbin/sshd").exists():
    pytest.skip("sin sshd en el contenedor", allow_module_level=True)

PUERTO, PUERTO2 = 2222, 2223
TIEMPOS = {}


def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)


def esperar_puerto(p, s=10):
    fin = time.time() + s
    while time.time() < fin:
        try:
            socket.create_connection(("127.0.0.1", p), timeout=0.3).close()
            return True
        except OSError:
            time.sleep(0.1)
    return False


@pytest.fixture(scope="module")
def red():
    """sshd real x2 (host key propia y host key distinta), usuarios, claves de prueba y known_hosts fijado."""
    base = Path("/srv/sshtest")
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    for nombre, uid in (("m4rk", 1001), ("gadmin", 1002)):
        sh("groupadd", "-g", str(uid), nombre)
        sh("useradd", "-m", "-u", str(uid), "-g", str(uid), "-s", "/bin/bash", nombre)
        sh("usermod", "-p", "*", nombre)
    Path("/run/sshd").mkdir(exist_ok=True)
    assert sh("id", "sshd").returncode == 0, "falta el usuario sshd"
    for k in ("host_a", "host_b"):
        assert sh("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(base / k)).returncode == 0
    ssh_g = Path("/home/gadmin/.ssh")
    shutil.rmtree(ssh_g, ignore_errors=True)                                        # claves de prueba NUEVAS en cada montaje del banco
    ssh_g.mkdir(mode=0o700, exist_ok=True)
    for k in ("id_bastion", "id_intruso"):
        assert sh("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(ssh_g / k)).returncode == 0
    pub_a = (base / "host_a.pub").read_text().split()
    pub_b = (base / "host_b.pub").read_text().split()
    (ssh_g / "known_hosts_ok").write_text("[127.0.0.1]:%d %s %s\n" % (PUERTO, pub_a[0], pub_a[1]))
    (ssh_g / "known_hosts_mal").write_text("[127.0.0.1]:%d %s %s\n" % (PUERTO2, pub_a[0], pub_a[1]))     # fija la clave de A para el puerto del servidor B (suplantado)
    (ssh_g / "known_hosts_vacio").write_text("")
    sh("chown", "-R", "gadmin:gadmin", str(ssh_g))
    for f in ssh_g.iterdir():
        os.chmod(f, 0o600)
    procs = []
    for puerto, host in ((PUERTO, "host_a"), (PUERTO2, "host_b")):
        cfg = base / ("sshd_%d.conf" % puerto)
        cfg.write_text("Port %d\nListenAddress 127.0.0.1\nHostKey %s\nPidFile %s\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPubkeyAuthentication yes\n"
                       "UsePAM no\nStrictModes yes\nLogLevel VERBOSE\nAllowUsers m4rk\nAuthorizedKeysFile /home/m4rk/.ssh/authorized_keys\n" % (puerto, base / host, base / ("sshd_%d.pid" % puerto)))
        log = open(base / ("sshd_%d.log" % puerto), "w")
        procs.append(subprocess.Popen(["/usr/sbin/sshd", "-D", "-e", "-f", str(cfg)], stderr=log, stdout=subprocess.DEVNULL))
        assert esperar_puerto(puerto), "sshd no arrancó en %d" % puerto
    m = Path("/home/m4rk/.ssh")
    m.mkdir(mode=0o700, exist_ok=True)
    sh("chown", "m4rk:m4rk", str(m))
    yield {"base": base, "g": ssh_g, "log": base / "sshd_2222.log", "log2": base / "sshd_2223.log"}
    for p in procs:
        p.terminate()
        p.wait(5)
    ev = os.environ.get("CF_EVIDENCIA")
    if ev:
        Path(ev).mkdir(parents=True, exist_ok=True)
        (Path(ev) / "tiempos-ssh.json").write_text(json.dumps(TIEMPOS, indent=1, sort_keys=True))
        shutil.copy2(base / "sshd_2222.log", Path(ev) / "sshd_2222.log")
        shutil.copy2(base / "sshd_2223.log", Path(ev) / "sshd_2223.log")
        shutil.copy2(base / "host_a.pub", Path(ev) / "host_a.pub")                       # solo las PÚBLICAS de prueba se conservan como evidencia
        shutil.copy2(base / "host_b.pub", Path(ev) / "host_b.pub")
        shutil.copy2(Path("/home/gadmin/.ssh/id_bastion.pub"), Path(ev) / "id_bastion.pub")


def forzado(sensor, envoltorio=None):
    c = "%s -I %s --base %s --feed %s --estado %s --traza %s --auditoria %s --ssh-original" % (
        sys.executable, AQUI / "sensor_control_d5.py", sensor.ctl, sensor.w / "feed.json", sensor.w / "estado.json", sensor.w / "traza.jsonl", sensor.audit)
    return ("%s %s" % (envoltorio, c)) if envoltorio else c


def autorizar(sensor, clave_pub="/home/gadmin/.ssh/id_bastion.pub", envoltorio=None, restrict=True):
    pub = Path(clave_pub).read_text().split()
    linea = 'command="%s"%s %s %s cf-bastion-d5-prueba\n' % (forzado(sensor, envoltorio), ',restrict' if restrict else '', pub[0], pub[1])
    Path("/home/m4rk/.ssh/authorized_keys").write_text(linea)
    sh("chown", "m4rk:m4rk", "/home/m4rk/.ssh/authorized_keys")
    os.chmod("/home/m4rk/.ssh/authorized_keys", 0o600)


def cliente(red, kh="known_hosts_ok", puerto=PUERTO, clave="id_bastion", extra=(), timeout=20):
    return ["ssh", "-i", "/home/gadmin/.ssh/" + clave, "-p", str(puerto), "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=yes", "-o", "IdentitiesOnly=yes",
            "-o", "IdentityAgent=none", "-o", "UserKnownHostsFile=/home/gadmin/.ssh/" + kh, "-o", "GlobalKnownHostsFile=/dev/null", *extra, "m4rk@127.0.0.1"]


def como_gadmin(args, timeout=30):
    t = time.perf_counter()
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, user=1002, group=1002, env={"HOME": "/home/gadmin", "PATH": "/usr/bin:/bin"})
    return p, time.perf_counter() - t


@pytest.fixture
def sensor(banco_mod, derivado, tmp_path):
    s = Sensor(derivado, tmp_path)
    yield s
    s.cierra()


ID_A, ID_B = "a" * 32, "b" * 32


def test_comando_forzado_y_lista_permitida_con_openssh_real(red, sensor):
    autorizar(sensor)
    ssh_real = tb.SshReal("m4rk@127.0.0.1", "/home/gadmin/.ssh/id_bastion", timeout=15, puerto=PUERTO, known_hosts="/home/gadmin/.ssh/known_hosts_ok", uid=1002, home="/home/gadmin")
    t = time.perf_counter()
    assert ssh_real(["resultado", "--id", ID_A])["estado"] == "desconocida"
    TIEMPOS["orden_permitida_solo_lectura_s"] = round(time.perf_counter() - t, 3)
    assert ssh_real(["feed", "--desde", "0"])["limpio"] in (True, False)
    t = time.perf_counter()
    assert ssh_real(["solicitar", "--id", ID_A, "--origen", "10.10.20.30"])["estado"] == "recibida"
    TIEMPOS["solicitar_s"] = round(time.perf_counter() - t, 3)
    time.sleep(1.0)
    assert ssh_real(["resultado", "--id", ID_A])["estado"] == "acuse" and len(sensor.lineas_aud("consumido")) == 1
    assert ssh_real(["cancelar", "--id", ID_A])["estado"] == "ya_consumida"
    # órdenes FUERA de alcance: la lista blanca las rechaza (rc 2 del subcomando) sin ejecutar nada
    fuera = ["cat /etc/passwd", "id", "solicitar --id %s --origen 10.10.20.99" % ID_B, "solicitar --id %s --origen 10.10.20.30; id" % ID_B, "bash -c 'echo hola'", "resultado --id ../../etc/passwd"]
    for orden in fuera:
        p, _ = como_gadmin(cliente(red) + [orden])
        r = json.loads(p.stdout)
        assert p.returncode == 2 and r["estado"] == "rechazada" and "root:" not in p.stdout, (orden, p.stdout, p.stderr)
    p, _ = como_gadmin(cliente(red))                                                  # sin orden = sesión interactiva: la fuerza el comando y se rechaza
    assert p.returncode == 2 and json.loads(p.stdout)["estado"] == "rechazada"
    assert not (sensor.ctl / "solicitudes" / (ID_B + ".json")).exists()              # nada se creó para las órdenes rechazadas
    assert len(sensor.lineas_aud("consumido")) == 1


def test_restrict_impide_pty_reenvios_y_subsistemas(red, sensor):
    autorizar(sensor)
    p, _ = como_gadmin(cliente(red, extra=("-tt",)) + ["resultado --id %s" % ID_A], timeout=20)
    assert "PTY allocation request failed" in p.stderr or "not allocated" in p.stderr or "administratively" in p.stderr.lower(), p.stderr   # restrict: sin pty
    p, _ = como_gadmin(cliente(red, extra=("-o", "ExitOnForwardFailure=yes", "-R", "4444:127.0.0.1:22")) + ["resultado --id %s" % ID_A])
    assert p.returncode == 255 and "forward" in p.stderr.lower()                      # restrict: sin reenvío remoto (con ExitOnForwardFailure la conexión muere)
    p, _ = como_gadmin(cliente(red, extra=("-s",)) + ["sftp"])                        # subsistema pedido: la orden forzada lo sustituye y se rechaza
    assert p.returncode != 0 and "root:" not in p.stdout
    p, _ = como_gadmin(cliente(red, extra=("-A", "-X")) + ["cat /etc/shadow"])        # agente y X11 no habilitan nada
    assert json.loads(p.stdout)["estado"] == "rechazada"
    reg = Path(red["log"]).read_text()
    assert "Accepted publickey for m4rk" in reg                                        # el servidor real autenticó por clave


def test_la_identidad_del_servidor_esta_fijada_y_las_claves_ajenas_no_entran(red, sensor):
    autorizar(sensor)
    antes = len(list((sensor.ctl / "solicitudes").glob("*.json"))) if (sensor.ctl / "solicitudes").exists() else 0
    p, _ = como_gadmin(cliente(red) + ["resultado --id %s" % ID_A])
    assert p.returncode == 0                                                           # host key A fijada en known_hosts_ok: acepta
    # servidor SUPLANTADO (clave de huésped distinta en 2223, pero el known_hosts fija la de A para ese puerto): se niega ANTES de ejecutar nada
    p, _ = como_gadmin(cliente(red, kh="known_hosts_mal", puerto=PUERTO2) + ["solicitar --id %s --origen 10.10.20.30" % ID_B])
    assert p.returncode == 255 and ("host key verification failed" in p.stderr.lower() or "identification has changed" in p.stderr.lower()), p.stderr
    assert not (sensor.ctl / "solicitudes" / (ID_B + ".json")).exists() and "Accepted publickey" not in Path(red["log2"]).read_text()
    # servidor desconocido con known_hosts vacío y StrictHostKeyChecking=yes
    p, _ = como_gadmin(cliente(red, kh="known_hosts_vacio") + ["resultado --id %s" % ID_A])
    assert p.returncode == 255 and "host key verification failed" in p.stderr.lower()
    # clave de usuario que no figura en authorized_keys
    p, _ = como_gadmin(cliente(red, clave="id_intruso") + ["resultado --id %s" % ID_A])
    assert p.returncode == 255 and "permission denied" in p.stderr.lower()
    assert (len(list((sensor.ctl / "solicitudes").glob("*.json"))) if (sensor.ctl / "solicitudes").exists() else 0) == antes


def test_corte_tras_recibir_reconexion_mismo_id_y_bloqueo_hasta_la_reanudacion_manual(red, banco_mod, sensor, tmp_path):
    demora = tmp_path / "demora.sh"
    demora.write_text('#!/bin/bash\nr=$("$@")\nrc=$?\nsleep 3\necho "$r"\nexit $rc\n')                                # ejecuta la orden REAL y retrasa la RESPUESTA 3 s
    os.chmod(demora, 0o755)
    os.chmod(tmp_path, 0o755)
    autorizar(sensor, envoltorio="/bin/bash " + str(demora))
    bast = tmp_path / "bastion"
    (bast / "compuerta").mkdir(parents=True)
    (bast / "agente-traza.jsonl").write_text("")
    ssh_real = tb.SshReal("m4rk@127.0.0.1", "/home/gadmin/.ssh/id_bastion", timeout=1.2, puerto=PUERTO, known_hosts="/home/gadmin/.ssh/known_hosts_ok", uid=1002, home="/home/gadmin")
    cuenta = lambda: Path(red["log"]).read_text().count("Accepted publickey")

    def invocacion(ssh):
        lim = tb.LimpiezaRemota(ssh, str(bast / "estado"), esperar_s=4.0, sondeo=0.1, fallos_consulta=2)
        rn = tb.runners_distribuidos(banco_mod, lim, ssh, Nft(), str(bast / "agente-traza.jsonl"))
        pu = banco_mod.PuertaBanco(rn, registro=str(bast / "compuerta" / "puerta-banco.jsonl"), estado_bloqueo=str(bast / "compuerta" / "puerta-bloqueo.json"),
                                   espera_agente=2.0, espera_feed=6.0, sondeo=0.1)
        return pu, lim
    c0 = cuenta()
    pu, lim = invocacion(ssh_real)
    t = time.perf_counter()
    r1 = pu.preparar_episodio()
    TIEMPOS["corte_tras_recibir_hasta_bloqueo_s"] = round(time.perf_counter() - t, 3)
    assert r1["lista"] is False and r1["bloqueada"] is True
    id_ = lim.pendiente()["id"]
    assert (sensor.ctl / "solicitudes" / (id_ + ".json")).exists()                      # el Sensor1 SÍ recibió la solicitud (ejecutó el comando real)
    time.sleep(3.5)
    assert [x["id"] for x in sensor.lineas_aud("consumido")] == [id_]                  # y el publicador la consumió: una limpieza
    ev = json.loads(Path(r1["historial"][0]["pasos"][0]["evidencia"]).read_text())
    assert ev["resultado"]["estado"] == "sin_transporte" and ev["resultado"]["incierto"] is True
    c1 = cuenta()
    # reconexión REAL sin retraso: el bloqueo se conserva y no hay NINGUNA conexión nueva mientras no haya reanudación manual
    autorizar(sensor)
    ssh_ok = tb.SshReal("m4rk@127.0.0.1", "/home/gadmin/.ssh/id_bastion", timeout=10, puerto=PUERTO, known_hosts="/home/gadmin/.ssh/known_hosts_ok", uid=1002, home="/home/gadmin")
    for _ in range(3):
        pu2, _l = invocacion(ssh_ok)
        r = pu2.preparar_episodio()
        assert r["lista"] is False and r["bloqueada"] is True and r["historial"][0]["pasos"] == []
    assert cuenta() == c1                                                                # 0 conexiones nuevas durante el bloqueo
    pu2.reanudar_manual("Mark (prueba de banco)", "SSH restablecido; consultar el id pendiente")
    pu3, lim3 = invocacion(ssh_ok)
    t = time.perf_counter()
    r = pu3.preparar_episodio()
    TIEMPOS["reconexion_consulta_mismo_id_hasta_continuar_s"] = round(time.perf_counter() - t, 3)
    assert r["lista"] is True and lim3.pendiente() is None
    assert len(sensor.lineas_aud("consumido")) == 1 and len(list((sensor.ctl / "solicitudes").glob("*.json"))) == 1       # el MISMO id, una sola limpieza
    assert (bast / "estado" / "limpiezas" / (id_ + ".json")).exists() and sensor.vivo()
    TIEMPOS["conexiones_aceptadas_en_el_caso"] = cuenta() - c0


def test_control_negativo_sin_restrict_el_reenvio_si_se_concede(red, sensor):
    """Demuestra que la comprobación de `restrict` discrimina: con la misma clave y el mismo comando forzado pero SIN `restrict`, el reenvío remoto SÍ se concede."""
    autorizar(sensor, restrict=False)
    p, _ = como_gadmin(cliente(red, extra=("-o", "ExitOnForwardFailure=yes", "-R", "4445:127.0.0.1:22")) + ["resultado --id %s" % ID_A])
    assert p.returncode == 0 and json.loads(p.stdout)["estado"] == "desconocida"
    autorizar(sensor, restrict=True)
    p, _ = como_gadmin(cliente(red, extra=("-o", "ExitOnForwardFailure=yes", "-R", "4445:127.0.0.1:22")) + ["resultado --id %s" % ID_A])
    assert p.returncode == 255