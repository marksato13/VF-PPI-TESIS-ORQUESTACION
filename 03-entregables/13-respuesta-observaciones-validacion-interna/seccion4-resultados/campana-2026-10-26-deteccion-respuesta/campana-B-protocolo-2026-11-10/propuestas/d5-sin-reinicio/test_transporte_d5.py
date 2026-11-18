"""Límite DISTRIBUIDO de la integración: el bastión y el Sensor1 se representan con árboles de ficheros separados (propietarios y permisos distintos:
Sensor1 = uid 1001 «m4rk» que ejecuta el publicador y el subcomando; bastión = uid 1002 «gadmin»), datos sintéticos y SSH emulado (solo la lista blanca del comando
forzado). Hay que ejecutarlo como root en el contenedor (`--user 0`, `--network none`). El «SSH» es una función; no es red real (límite declarado)."""
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HERR = Path(os.environ.get("CF_HERRAMIENTAS", "/herramientas"))
if os.geteuid() != 0 or not (HERR / "d5_episodio.py").exists():
    pytest.skip("requiere root en el contenedor y las herramientas de la Campaña B montadas", allow_module_level=True)
import adaptador_banco as ab  # noqa: E402
import hacer_d5_episodio_banco as hd  # noqa: E402
import hacer_publicador_d5 as h  # noqa: E402
import transporte_bastion as tb  # noqa: E402
from test_flujo_completo import K, OTRA, PREFIJO, decision, motor_dir  # noqa: E402

M4RK, GADMIN = 1001, 1002


def chown_r(p, uid):
    for r, ds, fs in os.walk(p):
        for x in [r] + [os.path.join(r, n) for n in ds + fs]:
            os.chown(x, uid, uid)


@pytest.fixture(scope="module")
def derivado():
    eng = motor_dir()
    orig = eng / "publicar_feed_v2.py"
    assert hashlib.sha256(orig.read_bytes()).hexdigest().startswith("5733f17d39bfa5fe")
    d = Path(tempfile.mkdtemp(prefix="d5dist_"))
    for f in eng.glob("*.py"):
        shutil.copy(f, d / f.name)
    assert h.main(str(orig), str(d / "publicar_feed_v2_d5.py")) == 0
    os.chmod(d, 0o755)
    for f in d.iterdir():
        os.chmod(f, 0o644)
    return d


@pytest.fixture(scope="module")
def banco_mod():
    d = Path(tempfile.mkdtemp(prefix="d5ep_"))
    assert hd.main(str(HERR / "d5_episodio.py"), str(d / "d5_episodio_banco.py")) == 0
    spec = importlib.util.spec_from_file_location("d5_episodio_banco", d / "d5_episodio_banco.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["d5_episodio_banco"] = m
    spec.loader.exec_module(m)
    return m


class Sensor:
    """Árbol del Sensor1 (uid 1001, 0700) con el publicador derivado como PROCESO de ese usuario."""

    def __init__(self, derivado, raiz):
        self.raiz = Path(raiz) / "sensor"
        self.w, self.ctl, self.aud = self.raiz / "feed-v2", self.raiz / "feed-v2" / "d5" / "control", self.raiz / "feed-v2" / "d5" / "auditoria"
        for d in (self.w, self.ctl, self.aud):
            d.mkdir(parents=True)
        subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", str(self.w / "k.pem")], capture_output=True)
        if not (self.w / "k.pem").exists():
            pytest.skip("sin openssl")
        regs = [decision(K, "brute_force", "BLOCK", 1), decision(OTRA, "http_abuse", "LIMIT", 2), decision(PREFIJO, "http_abuse", "LIMIT", 3)]
        (self.w / "motor.log").write_text("".join(json.dumps(r) + "\n" for r in regs))
        chown_r(self.raiz, M4RK)
        for d in (self.raiz, self.w, self.ctl, self.aud):
            os.chmod(d, 0o700)
        os.chmod(self.w / "k.pem", 0o600)
        for anc in self.raiz.parents:                                      # atravesables (solo el árbol del Sensor1 es 0700)
            if str(anc) in ("/", "/tmp"):
                break
            os.chmod(anc, 0o755)
        self.control, self.audit = self.ctl / "control.json", self.aud / "d5-auditoria.jsonl"
        self.err = open(raiz / "sensor-stderr.txt", "w")
        w = self.w
        self.p = subprocess.Popen([sys.executable, str(derivado / "publicar_feed_v2_d5.py"), "--log", str(w / "motor.log"), "--estado", str(w / "estado.json"),
                                   "--clave-privada", str(w / "k.pem"), "--salida-feed", str(w / "feed.json"), "--salida-firma", str(w / "feed.sig"), "--traza", str(w / "traza.jsonl"),
                                   "--politica", "if_senal", "--seguir", "--sondeo-segundos", "0.05", "--refresco-segundos", "1.5", "--control-d5", str(self.control),
                                   "--d5-origen", K, "--d5-auditoria", str(self.audit)], cwd=str(derivado), stdout=subprocess.DEVNULL, stderr=self.err, user=M4RK, group=M4RK, umask=0o077)
        fin = time.time() + 15
        while time.time() < fin:
            try:
                if {e["ip"] for e in json.loads((w / "feed.json").read_text())["entradas"]} == {K, OTRA, PREFIJO}:
                    break
            except (OSError, ValueError):
                pass
            time.sleep(0.05)
        self.t0 = self.inicio()

    def inicio(self):
        return open("/proc/%d/stat" % self.p.pid).read().rsplit(")", 1)[1].split()[19]

    def vivo(self):
        return self.p.poll() is None and self.inicio() == self.t0

    def lineas_aud(self, ev=None):
        return [x for x in (ab._jsonl(self.audit) if self.audit.exists() else []) if ev is None or x.get("evento") == ev]

    def cierra(self):
        if self.p.poll() is None:
            self.p.send_signal(signal.SIGCONT)
            self.p.terminate()
            self.p.wait(5)
        self.err.close()


class Ssh:
    """«SSH» emulado: ejecuta el subcomando forzado del Sensor1 como uid 1001 con SSH_ORIGINAL_COMMAND. Inyecta cortes."""

    def __init__(self, sensor, forzado=True):
        self.s, self.llamadas, self.caido, self.cortar_tras = sensor, [], False, None
        self.base = [sys.executable, "-I", str(AQUI / "sensor_control_d5.py"), "--base", str(sensor.ctl), "--feed", str(sensor.w / "feed.json"), "--estado", str(sensor.w / "estado.json"),
                     "--traza", str(sensor.w / "traza.jsonl"), "--auditoria", str(sensor.audit), "--ssh-original"]

    def crudo(self, texto):
        p = subprocess.run(self.base, env={"SSH_ORIGINAL_COMMAND": texto, "PATH": "/usr/bin:/bin"}, capture_output=True, text=True, user=M4RK, group=M4RK)
        assert p.stdout.strip(), "el subcomando del Sensor1 no respondió: rc=%s stderr=%s" % (p.returncode, p.stderr[-400:])
        return p.returncode, json.loads(p.stdout)

    def __call__(self, args):
        self.llamadas.append(args[0])
        if self.caido:
            raise ConnectionError("ssh caído")
        rc, r = self.crudo(" ".join(args))
        if self.cortar_tras == args[0]:                                    # el comando SE EJECUTÓ en el Sensor1, pero la conexión se pierde antes de la respuesta
            self.cortar_tras, self.caido = None, True
            raise ConnectionError("ssh interrumpido tras ejecutar")
        return r

    def solicitudes(self):
        return [x for x in self.llamadas if x == "solicitar"]


class Nft:
    def __call__(self, peticion):
        op = peticion["operaciones"][0]["op"]
        return {"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": {}}, "descartes_limite": {}}} if op == "listar" else {"ok": True}


def montar(banco_mod, derivado, tmp_path, esperar_s=8.0):
    s = Sensor(derivado, tmp_path)
    ssh = Ssh(s)
    bast = tmp_path / "bastion"
    (bast / "compuerta").mkdir(parents=True)
    (bast / "agente-traza.jsonl").write_text("")
    chown_r(bast, GADMIN)
    return s, ssh, bast


def nueva_invocacion(banco_mod, ssh, bast, esperar_s=8.0):
    """Todo se construye de cero: objetos nuevos que solo comparten los FICHEROS del bastión (como un proceso nuevo)."""
    lim = tb.LimpiezaRemota(ssh, str(bast / "estado"), esperar_s=esperar_s, sondeo=0.05, fallos_consulta=2)
    rn = tb.runners_distribuidos(banco_mod, lim, ssh, Nft(), str(bast / "agente-traza.jsonl"))
    pu = banco_mod.PuertaBanco(rn, registro=str(bast / "compuerta" / "puerta-banco.jsonl"), estado_bloqueo=str(bast / "compuerta" / "puerta-bloqueo.json"),
                               espera_agente=2.0, espera_feed=6.0, sondeo=0.1)                      # > refresco del publicador (1,5 s en banco; 25 s > 20 s real)
    return pu, lim


@pytest.fixture
def entorno(banco_mod, derivado, tmp_path):
    s, ssh, bast = montar(banco_mod, derivado, tmp_path)
    yield s, ssh, bast
    s.cierra()


def test_flujo_distribuido_conserva_el_id_y_respeta_la_separacion_de_permisos(banco_mod, entorno):
    s, ssh, bast = entorno
    pu, lim = nueva_invocacion(banco_mod, ssh, bast)
    r = pu.preparar_episodio()
    assert r["lista"] is True, json.dumps(r["historial"][0], default=str)[:1500]
    assert ssh.solicitudes() == ["solicitar"] and s.vivo()
    reg =list((bast / "estado" / "limpiezas").glob("*.json"))
    ids = [x.stem for x in reg if len(x.stem) == 32]
    assert len(ids) == 1 and not (bast / "estado" / "limpieza-pendiente.json").exists()             # pendiente resuelto y archivado
    id_ = ids[0]
    assert (s.ctl / "solicitudes" / (id_ + ".json")).exists()                                         # el MISMO id en el registro del Sensor1…
    assert [x["id"] for x in s.lineas_aud("consumido")] == [id_] and [x["id"] for x in s.lineas_aud("publicado")] == [id_]       # …y en la auditoría
    assert json.loads(Path(str(s.control) + ".ack").read_text())["id"] == id_
    # el proceso del publicador es de «m4rk» y el bastión (gadmin) NO puede leer ni escribir el árbol del Sensor1
    assert [l for l in open("/proc/%d/status" % s.p.pid) if l.startswith("Uid:")][0].split()[1] == str(M4RK)
    chk = subprocess.run([sys.executable, "-c", "import os,sys\nfor p in sys.argv[1:]:\n    for m in ('r','a'):\n        try: open(p, m).close(); print('PERMITIDO', p, m)\n        except OSError as e: print(type(e).__name__)",
                          str(s.control) + ".ack", str(s.audit), str(s.ctl / "control.json")], capture_output=True, text=True, user=GADMIN, group=GADMIN)
    assert "PERMITIDO" not in chk.stdout and chk.stdout.count("PermissionError") == 6


@pytest.mark.parametrize("texto", ["solicitar --id %s --origen 10.10.20.99" % ("a" * 32), "solicitar --id ZZZ --origen 10.10.20.30", "solicitar --id %s --origen 10.10.20.30; rm -rf /" % ("a" * 32),
                                   "resultado --id %s extra" % ("a" * 32), "feed --desde abc", "cat /etc/passwd", "", "cancelar", "solicitar --id %s --origen 10.10.20.30 --x" % ("b" * 32)])
def test_comandos_fuera_de_la_lista_blanca_se_rechazan_sin_tocar_nada(entorno, texto):
    s, ssh, bast = entorno
    rc, r = ssh.crudo(texto)
    assert rc == 2 and r["estado"] == "rechazada"
    assert not s.control.exists() and not list((s.ctl / "solicitudes").glob("*.json")) if (s.ctl / "solicitudes").exists() else not s.control.exists()


def test_corte_tras_recibir_consulta_el_mismo_id_y_mantiene_el_bloqueo_entre_invocaciones(banco_mod, entorno):
    s, ssh, bast = entorno
    ssh.cortar_tras = "solicitar"                                                                    # Sensor1 recibe y procesa; la conexión se pierde; luego SSH sigue caído
    pu, lim = nueva_invocacion(banco_mod, ssh, bast)
    r1 = pu.preparar_episodio()
    assert r1["lista"] is False and r1["bloqueada"] is True
    pend = lim.pendiente()
    assert pend and len(pend["id"]) == 32 and ssh.solicitudes() == ["solicitar"]
    time.sleep(1.0)
    assert [x["id"] for x in s.lineas_aud("consumido")] == [pend["id"]]                              # el Sensor1 SÍ recibió y consumió ESA solicitud
    ev = json.loads(Path(r1["historial"][0]["pasos"][0]["evidencia"]).read_text())
    assert ev["resultado"]["incierto"] is True and ev["resultado"]["estado"] == "sin_transporte"
    n_antes = len(ssh.llamadas)
    for _ in range(3):                                                                                # nuevas invocaciones con SSH aún caído: bloqueada, sin tocar la red
        pu2, _ = nueva_invocacion(banco_mod, ssh, bast)
        r = pu2.preparar_episodio()
        assert r["lista"] is False and r["bloqueada"] is True and r["historial"][0]["pasos"] == []
    assert len(ssh.llamadas) == n_antes
    ssh.caido = False                                                                                 # SSH vuelve: sigue bloqueada (el bloqueo no se borra solo) y sin llamadas
    pu3, _ = nueva_invocacion(banco_mod, ssh, bast)
    r = pu3.preparar_episodio()
    assert r["lista"] is False and r["bloqueada"] is True and len(ssh.llamadas) == n_antes
    # decisión manual registrada -> la nueva invocación SOLO consulta el mismo id y continúa con el acuse
    pu3.reanudar_manual("Mark (prueba de banco)", "SSH restablecido; consultar el id pendiente")
    pu4, lim4 = nueva_invocacion(banco_mod, ssh, bast)
    r = pu4.preparar_episodio()
    assert r["lista"] is True and ssh.solicitudes() == ["solicitar"] and ssh.llamadas[n_antes] == "resultado"     # ninguna solicitud nueva
    assert len(s.lineas_aud("consumido")) == 1 and len(list((s.ctl / "solicitudes").glob("*.json"))) == 1       # una sola limpieza, un solo id
    assert lim4.pendiente() is None and (bast / "estado" / "limpiezas" / (pend["id"] + ".json")).exists()


def test_id_desconocido_por_el_sensor_sigue_incierto_y_solo_un_descarte_manual_permite_un_id_nuevo(banco_mod, entorno):
    s, ssh, bast = entorno
    ssh.caido = True                                                                                  # la orden nunca llegó al Sensor1
    pu, lim = nueva_invocacion(banco_mod, ssh, bast)
    assert pu.preparar_episodio()["lista"] is False
    id_ = lim.pendiente()["id"]
    n_sol = len(ssh.solicitudes())                                                                    # el intento fallido (nunca llegó al Sensor1)
    ssh.caido = False
    pu.reanudar_manual("Mark (prueba de banco)", "SSH restablecido")
    pu2, lim2 = nueva_invocacion(banco_mod, ssh, bast)
    r = pu2.preparar_episodio()
    assert r["lista"] is False and r["bloqueada"] is True and r["historial"][0]["pasos"][0]["motivo"].startswith("sin acuse válido: desconocida_en_sensor")
    assert len(ssh.solicitudes()) == n_sol and not list((s.ctl / "solicitudes").glob("*.json"))      # no se reenvió con el mismo id; el Sensor1 no tiene registro
    assert lim2.pendiente()["id"] == id_                                                              # el pendiente se conserva: no se adivina
    pu2.reanudar_manual("Mark (prueba de banco)", "se acepta que la orden nunca llegó")
    for q, m in (("", "x"), ("Mark", " ")):
        with pytest.raises(ValueError):
            lim2.descartar_pendiente(q, m)
    lim2.descartar_pendiente("Mark (prueba de banco)", "la orden nunca llegó: se descarta el pendiente")
    assert list((bast / "estado" / "limpiezas").glob("descartado-*.json"))
    reg = [x for x in ab._jsonl(bast / "estado" / "limpiezas" / "registro.jsonl") if x["evento"] == "pendiente_descartado_manual"]
    assert len(reg) == 1 and reg[0]["por"] == "Mark (prueba de banco)" and reg[0]["id"] == id_ and "nunca llegó" in reg[0]["motivo"]
    pu3, lim3 = nueva_invocacion(banco_mod, ssh, bast)
    assert pu3.preparar_episodio()["lista"] is True and len(ssh.solicitudes()) == n_sol + 1          # AHORA sí, con un id nuevo y por decisión manual
    assert lim3.pendiente() is None and len(s.lineas_aud("consumido")) == 1


def test_el_sensor_es_idempotente_por_id_no_acumula_controles_y_cancela_solo_su_id(entorno):
    s, ssh, bast = entorno
    a, b = "a" * 32, "b" * 32
    assert ssh.crudo("solicitar --id %s --origen 10.10.20.30" % a)[1]["estado"] == "recibida"
    time.sleep(1.0)
    assert ssh.crudo("solicitar --id %s --origen 10.10.20.30" % a)[1]["estado"] == "ya_recibida"       # repetida: no es otra limpieza
    assert len(s.lineas_aud("consumido")) == 1
    os.kill(s.p.pid, signal.SIGSTOP)
    try:
        assert ssh.crudo("solicitar --id %s --origen 10.10.20.30" % b)[1]["estado"] == "recibida"
        c = "c" * 32
        assert ssh.crudo("solicitar --id %s --origen 10.10.20.30" % c)[1]["estado"] == "pendiente_previa"      # no se sobrescribe ni se acumula
        assert ssh.crudo("cancelar --id %s" % c)[1]["estado"] == "desconocida"                              # no es suyo
        assert ssh.crudo("cancelar --id %s" % a)[1]["estado"] == "ya_consumida" and s.control.exists()     # un id viejo no puede retirar el control de OTRO id
        assert json.loads(s.control.read_text())["id"] == b
        assert ssh.crudo("resultado --id %s" % b)[1]["estado"] == "pendiente"
        assert ssh.crudo("cancelar --id %s" % b)[1]["estado"] == "cancelada"
        r = ssh.crudo("resultado --id %s" % b)[1]
        assert r["estado"] == "sin_acuse" and r["categoria"] == "no_consumida" and r["determinada"] is True
    finally:
        os.kill(s.p.pid, signal.SIGCONT)
    time.sleep(0.5)
    assert len(s.lineas_aud("consumido")) == 1 and s.vivo()                                           # lo cancelado no se consumió


def test_con_logrotate_real_y_el_usuario_del_publicador_el_resultado_de_un_id_viejo_se_reconstruye(banco_mod, entorno):
    if shutil.which("logrotate") is None:
        pytest.skip("sin logrotate")
    s, ssh, bast = entorno
    if subprocess.run(["id", "m4rk"], capture_output=True).returncode != 0:
        subprocess.run(["groupadd", "-g", str(M4RK), "m4rk"], capture_output=True)
        subprocess.run(["useradd", "-M", "-u", str(M4RK), "-g", str(M4RK), "-s", "/usr/sbin/nologin", "m4rk"], capture_output=True)
    if subprocess.run(["id", "m4rk"], capture_output=True).returncode != 0:
        pytest.skip("no se pudo crear el usuario m4rk")
    pu, lim = nueva_invocacion(banco_mod, ssh, bast)
    assert pu.preparar_episodio()["lista"] is True
    id1 = [x.stem for x in (bast / "estado" / "limpiezas").glob("*.json") if len(x.stem) == 32][0]
    conf = bast / "logrotate.conf"
    conf.write_text("%s {\n    su m4rk m4rk\n    daily\n    rotate 30\n    missingok\n    notifempty\n    compress\n    delaycompress\n    nocopytruncate\n    create 0640 m4rk m4rk\n}\n" % s.audit)
    os.chmod(conf, 0o644)
    for _ in range(2):
        r = subprocess.run(["logrotate", "-f", "-s", str(bast / "lr.state"), str(conf)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        os.makedirs(bast / "x", exist_ok=True)
        time.sleep(0.2)
    gens = sorted(p.name for p in s.aud.iterdir())
    assert any(g.endswith(".gz") for g in gens) or any(g.endswith(".1") for g in gens)
    # una limpieza posterior (otro id) y consulta del id VIEJO a través del subcomando del Sensor1 (usuario m4rk lee las generaciones)
    pu2, lim2 = nueva_invocacion(banco_mod, ssh, bast)
    assert pu2.preparar_episodio()["lista"] is True
    r = ssh.crudo("resultado --id %s" % id1)[1]
    assert r["estado"] == "sin_acuse" and r["categoria"] == "consumida_y_publicada" and r["publicacion"] == "confirmada" and r["secuencia"] > 0
    st = os.stat(s.audit)
    assert st.st_uid == M4RK and oct(st.st_mode & 0o777) == "0o640" and s.vivo()                       # fichero nuevo de logrotate: m4rk, 0640; el publicador sigue escribiendo
