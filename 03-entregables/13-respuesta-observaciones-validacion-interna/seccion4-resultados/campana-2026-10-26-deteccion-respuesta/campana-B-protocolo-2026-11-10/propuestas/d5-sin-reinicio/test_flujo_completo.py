"""Banco aislado y datos sintéticos: flujo COMPLETO solicitud -> limpieza -> acuse con el publicador derivado corriendo como PROCESO
real (no se llama a main en el mismo hilo). Comprueba que el proceso sigue activo y sin reiniciar, que las demás entidades se
conservan y que una solicitud duplicada, un acuse ausente o un acuse que no se puede escribir se manejan de forma segura."""
import hashlib
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
import d5_control as cli  # noqa: E402
import hacer_publicador_d5 as h  # noqa: E402

K, OTRA, PREFIJO = "10.10.20.30", "10.10.20.99", "10.10.20.3"


def motor_dir():
    for c in (Path(os.environ.get("CF_PRODUCTO", "/nonexistent")), Path("/producto-etapa3"), *[p / "producto-etapa3" for p in AQUI.parents]):
        if (c / "scripts" / "engine" / "publicar_feed_v2.py").exists():
            return c / "scripts" / "engine"
    pytest.skip("el producto desplegado no está disponible en el banco")


@pytest.fixture(scope="module")
def derivado():
    eng = motor_dir()
    orig = eng / "publicar_feed_v2.py"
    assert hashlib.sha256(orig.read_bytes()).hexdigest().startswith("5733f17d39bfa5fe")
    d = Path(tempfile.mkdtemp(prefix="d5flujo_"))
    for f in eng.glob("*.py"):
        shutil.copy(f, d / f.name)
    assert h.main(str(orig), str(d / "publicar_feed_v2_d5.py")) == 0
    return d


def decision(ip, regla, accion, n):
    return {"event": "decision", "entity_ip": ip, "decision_id": "d%s|%s" % (n, ip), "window_end_utc": None, "logged_at": time.time(),
            "decidido_en": time.time(), "detector_name": "if_limpio_2026_10", "score": -0.1, "decision": "PERMIT",
            "heuristicos": [{"heuristico": regla, "accion": accion, "motivo": "sintético"}]}


class Pub:
    def __init__(self, derivado, tmp, origen=K):
        self.tmp = tmp
        subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", str(tmp / "k.pem")], capture_output=True)
        if not (tmp / "k.pem").exists():
            pytest.skip("sin openssl")
        self.log = tmp / "motor.log"
        self.log.write_text("".join(json.dumps(decision(ip, r, a, n)) + "\n" for n, (ip, r, a) in enumerate(
            [(K, "brute_force", "BLOCK"), (OTRA, "http_abuse", "LIMIT"), (PREFIJO, "http_abuse", "LIMIT")])))
        self.ctl = tmp / "control.json"
        self.err = open(tmp / "stderr.txt", "w")
        self.p = subprocess.Popen([sys.executable, str(derivado / "publicar_feed_v2_d5.py"), "--log", str(self.log), "--estado", str(tmp / "estado.json"),
                                   "--clave-privada", str(tmp / "k.pem"), "--salida-feed", str(tmp / "feed.json"), "--salida-firma", str(tmp / "feed.sig"),
                                   "--traza", str(tmp / "traza.jsonl"), "--politica", "if_senal", "--seguir", "--sondeo-segundos", "0.05",
                                   "--refresco-segundos", "1.5", "--control-d5", str(self.ctl), "--d5-origen", origen,
                                   "--d5-auditoria", str(tmp / "d5-auditoria.jsonl")],
                                  cwd=derivado, stdout=subprocess.DEVNULL, stderr=self.err)
        self.espera(lambda: self.ips() == {K, OTRA, PREFIJO}, 10)
        self.t0 = self.inicio()

    def inicio(self):
        return open("/proc/%d/stat" % self.p.pid).read().rsplit(")", 1)[1].split()[19]      # starttime: cambia si el proceso se reinicia

    def vivo(self):
        return self.p.poll() is None and self.inicio() == self.t0

    def feed(self):
        try:
            return json.loads((self.tmp / "feed.json").read_text())
        except (OSError, ValueError):
            return {"entradas": [], "secuencia": 0, "generado": 0}

    def ips(self):
        return {e["ip"] for e in self.feed()["entradas"]}

    def estado(self):
        return json.loads((self.tmp / "estado.json").read_text())

    def espera(self, cond, s):
        fin = time.time() + s
        while time.time() < fin:
            try:
                if cond():
                    return True
            except (OSError, ValueError, KeyError):
                pass
            time.sleep(0.05)
        return False

    def cierra(self):
        if self.p.poll() is None:
            self.p.send_signal(signal.SIGCONT)
            self.p.terminate()
            self.p.wait(5)
        self.err.close()


@pytest.fixture
def pub(derivado, tmp_path):
    p = Pub(derivado, tmp_path)
    yield p
    p.cierra()


def test_flujo_completo_solicitud_limpieza_acuse(pub):
    e0 = pub.estado()
    r = cli.solicitar_reset(pub.ctl, K, esperar_s=10)
    assert r["ok"] and r["estado"] == "acuse" and r["rc"] == 0 and not r["duplicada"] and r["secuencia"] > 0
    assert len(r["quitado"]["vigentes"]) == 1 and len(r["quitado"]["escalada"]) == 1
    # el acuse significa: feed ya republicado (secuencia >= la del acuse) SIN la Kali, estado persistido limpio
    f = pub.feed()
    assert f["secuencia"] >= r["secuencia"] and K not in {e["ip"] for e in f["entradas"]}
    e1 = pub.estado()
    assert {k.split("|")[0] for k in e1["vigentes"]} == {OTRA, PREFIJO} and {k.split("@")[0] for k in e1["escalada"]} == {OTRA, PREFIJO}
    for ip in (OTRA, PREFIJO):                                        # entidades que NO son la Kali: idénticas, no «parecidas»
        assert [v for k, v in e1["vigentes"].items() if k.startswith(ip + "|")] == [v for k, v in e0["vigentes"].items() if k.startswith(ip + "|")]
        assert [v for k, v in e1["escalada"].items() if k.startswith(ip + "@")] == [v for k, v in e0["escalada"].items() if k.startswith(ip + "@")]
    assert set(e0["eventos"]) <= set(e1["eventos"])                   # los eventos (dedupe/auditoría) se conservan
    assert not pub.ctl.exists() and not (pub.tmp / "control.json.cli.tmp").exists()
    # el proceso sigue activo, es el MISMO (starttime igual) y sigue publicando
    assert pub.vivo()
    g0 = pub.feed()["generado"]
    assert pub.espera(lambda: pub.feed()["generado"] > g0, 6) and pub.vivo()


def test_la_escalera_de_la_kali_vuelve_a_nivel_1_con_el_proceso_vivo(pub):
    assert cli.solicitar_reset(pub.ctl, K, esperar_s=10)["ok"]
    with open(pub.log, "a") as fh:
        fh.write(json.dumps(decision(K, "brute_force", "BLOCK", 99)) + "\n")
    assert pub.espera(lambda: K in pub.ips(), 8)
    e = [x for x in pub.feed()["entradas"] if x["ip"] == K][0]
    assert e["nivel"] == 1 and 290 <= e["hasta"] - time.time() <= 302 and pub.vivo()


def test_solicitud_duplicada_es_un_no_op_y_no_borra_lo_nuevo(pub):
    r1 = cli.solicitar_reset(pub.ctl, K, esperar_s=10, id_="req-1")
    assert r1["ok"]
    with open(pub.log, "a") as fh:                                    # tras la limpieza llega una propuesta NUEVA legítima sobre la Kali
        fh.write(json.dumps(decision(K, "brute_force", "BLOCK", 77)) + "\n")
    assert pub.espera(lambda: K in pub.ips(), 8)
    nueva = [x["id"] for x in pub.feed()["entradas"] if x["ip"] == K]
    ack = Path(str(pub.ctl) + ".ack")
    ack.unlink()                                                      # para observar la respuesta del PUBLICADOR a la repetición
    pub.ctl.write_text(json.dumps({"accion": "reset_origen", "origen": K, "id": "req-1"}))      # misma solicitud, repetida
    assert pub.espera(ack.exists, 6)
    a = json.loads(ack.read_text())
    assert a["ok"] and a["duplicada"] and a["quitado"] == {"vigentes": [], "escalada": []}
    assert [x["id"] for x in pub.feed()["entradas"] if x["ip"] == K] == nueva         # la propuesta nueva NO se borró
    assert pub.vivo() and not pub.ctl.exists()
    # y el cliente es idempotente con el mismo id: devuelve acuse sin dañar nada
    r2 = cli.solicitar_reset(pub.ctl, K, esperar_s=5, id_="req-1")
    assert r2["ok"] and [x["id"] for x in pub.feed()["entradas"] if x["ip"] == K] == nueva


def test_control_pendiente_no_se_sobrescribe_ni_se_acumula(pub):
    os.kill(pub.p.pid, signal.SIGSTOP)
    try:
        pub.ctl.write_text(json.dumps({"accion": "reset_origen", "origen": K, "id": "primero"}))
        r = cli.solicitar_reset(pub.ctl, K, esperar_s=0.3)
        assert not r["ok"] and r["estado"] == "pendiente_previa"
        assert json.loads(pub.ctl.read_text())["id"] == "primero"
    finally:
        os.kill(pub.p.pid, signal.SIGCONT)
    assert pub.espera(lambda: not pub.ctl.exists(), 6) and pub.vivo()


def test_acuse_ausente_publicador_detenido_falla_seguro_y_retira_el_control(pub):
    os.kill(pub.p.pid, signal.SIGSTOP)                                # publicador no responde
    try:
        r = cli.solicitar_reset(pub.ctl, K, esperar_s=0.6, sondeo=0.05)
        assert not r["ok"] and r["estado"] == "sin_acuse_no_procesada" and r["rc"] == 5
        assert not pub.ctl.exists()                                   # no queda un control que actúe más tarde
    finally:
        os.kill(pub.p.pid, signal.SIGCONT)
    time.sleep(1.0)
    assert K in pub.ips() and pub.vivo()                              # nada se limpió: la puerta debe fallar, no suponer limpio


def test_acuse_que_no_se_puede_escribir_no_tumba_el_publicador_y_el_cliente_no_asume_limpio(pub):
    os.mkdir(str(pub.ctl) + ".ack")                                   # el destino del acuse es un directorio: escribirlo falla
    r = cli.solicitar_reset(pub.ctl, K, esperar_s=1.5, sondeo=0.05)
    assert not r["ok"] and r["estado"] == "sin_acuse_procesada" and r["rc"] == 6      # INCIERTO para el cliente: la puerta falla
    assert pub.vivo() and pub.espera(lambda: K not in pub.ips(), 6)  # el publicador sí limpió, siguió vivo y publicando
    g0 = pub.feed()["generado"]
    assert pub.espera(lambda: pub.feed()["generado"] > g0, 6)
    assert "no se pudo escribir el acuse" in (pub.tmp / "stderr.txt").read_text()


def test_acuse_antiguo_de_otro_id_se_ignora(pub):
    Path(str(pub.ctl) + ".ack").write_text(json.dumps({"id": "viejo", "ok": True, "secuencia": 1, "quitado": {}}))
    os.kill(pub.p.pid, signal.SIGSTOP)
    try:
        r = cli.solicitar_reset(pub.ctl, K, esperar_s=0.4)
        assert not r["ok"] and r["estado"] == "sin_acuse_no_procesada"
    finally:
        os.kill(pub.p.pid, signal.SIGCONT)


@pytest.mark.parametrize("contenido, error", [({"accion": "reset_origen", "origen": OTRA, "id": "x"}, "origen no permitido"),
                                               ({"accion": "borrar", "origen": K, "id": "x"}, "control mal formado"),
                                               ("{no es json", "control ilegible")])
def test_controles_invalidos_se_rechazan_con_el_proceso_vivo_y_el_estado_intacto(pub, contenido, error):
    e0 = pub.estado()
    pub.ctl.write_text(contenido if isinstance(contenido, str) else json.dumps(contenido))
    ack = Path(str(pub.ctl) + ".ack")
    assert pub.espera(ack.exists, 6)
    a = json.loads(ack.read_text())
    assert not a["ok"] and a["error"].startswith(error)
    assert pub.vivo() and pub.estado()["vigentes"].keys() == e0["vigentes"].keys() and pub.ips() == {K, OTRA, PREFIJO}
