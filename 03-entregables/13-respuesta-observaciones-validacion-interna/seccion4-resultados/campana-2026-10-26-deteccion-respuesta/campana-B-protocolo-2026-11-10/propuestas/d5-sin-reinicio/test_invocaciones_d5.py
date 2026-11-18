"""Límite de la integración: la puerta real se invoca creando una instancia (y un proceso) NUEVOS en cada llamada. Con el emulador, el bloqueo tras el
primer fallo se conserva entre procesos distintos, entre procesos simultáneos y ante un fichero de bloqueo ilegible; una nueva solicitud exige una
reanudación manual registrada. Publicador real como proceso, srv-dmz sintético. Solo las pruebas necesarias para este límite."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HERR = Path(os.environ.get("CF_HERRAMIENTAS", "/herramientas"))
if not (HERR / "d5_episodio.py").exists():
    pytest.skip("herramientas de la Campaña B no montadas", allow_module_level=True)
import adaptador_banco as ab  # noqa: E402
import hacer_d5_episodio_banco as hd  # noqa: E402
from test_flujo_completo import Pub, derivado  # noqa: E402,F401


@pytest.fixture(scope="module")
def modulo():
    d = Path(tempfile.mkdtemp(prefix="d5inv_"))
    assert hd.main(str(HERR / "d5_episodio.py"), str(d / "d5_episodio_banco.py")) == 0
    return d / "d5_episodio_banco.py"


def preparar_entorno(pub, modulo, esperar_s=2.5):
    gate = pub.tmp / "compuerta"
    gate.mkdir()
    (pub.tmp / "agente-traza.jsonl").write_text("")
    cfg = {"ctl": str(pub.ctl), "feed": str(pub.tmp / "feed.json"), "estado": str(pub.tmp / "estado.json"), "traza": str(pub.tmp / "traza.jsonl"),
           "auditoria": str(pub.tmp / "d5-auditoria.jsonl"), "agente_traza": str(pub.tmp / "agente-traza.jsonl"), "esperar_s": esperar_s,
           "espera_agente": 2.0, "espera_feed": 6.0}
    (pub.tmp / "cfg.json").write_text(json.dumps(cfg))
    return gate


def invocar(pub, modulo, gate, *args, espera=True):
    cmd = [sys.executable, "-I", str(AQUI / "emulador_compuerta_d5.py"), "--modulo", str(modulo), "--cfg", str(pub.tmp / "cfg.json"), "--dir", str(gate), *args]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p if not espera else (p.wait(120), p)[1]


def salida(p):
    out = p.stdout.read()
    assert out.strip(), p.stderr.read()
    return json.loads(out.strip().splitlines()[-1])


def solicitudes(pub):
    return len([x for x in ab._jsonl(pub.tmp / "d5-auditoria.jsonl") if x["evento"] == "consumido"])


def evidencias(pub):
    return sorted(x.name for x in pub.tmp.glob("control.json.evidencia-*.json"))


def eventos(gate):
    return [x["evento"] for x in ab._jsonl(gate / "puerta-banco.jsonl")]


def test_el_bloqueo_se_conserva_entre_procesos_nuevos_y_una_nueva_solicitud_exige_reanudacion_manual(modulo, derivado, tmp_path):
    p = Pub(derivado, tmp_path)
    try:
        gate = preparar_entorno(p, modulo)
        os.mkdir(str(p.ctl) + ".ack")                                                     # el acuse no se puede escribir
        r1 = salida(invocar(p, modulo, gate, "preparar"))
        assert r1["lista"] is False and r1["bloqueada"] is True and solicitudes(p) == 1
        ev1 = evidencias(p)
        assert len(ev1) == 1 and (gate / "puerta-bloqueo.json").exists()
        for _ in range(3):                                                                # TRES procesos nuevos más: cada uno construye una puerta nueva
            r = salida(invocar(p, modulo, gate, "preparar"))
            assert r["lista"] is False and r["bloqueada"] is True and r["pasos"] == []
        assert solicitudes(p) == 1 and evidencias(p) == ev1                               # ninguna solicitud nueva; la evidencia intacta
        assert eventos(gate) == ["puerta_bloqueada"] + ["omitida_por_puerta_bloqueada"] * 3
        # una reanudación sin quién o sin por qué se rechaza (proceso nuevo) y no desbloquea
        for args in (("--quien", "", "--motivo", "x"), ("--quien", "Mark", "--motivo", "")):
            pr = invocar(p, modulo, gate, "reanudar", *args)
            assert pr.returncode == 2 and salida(pr)["reanudado"] is False
        assert salida(invocar(p, modulo, gate, "preparar"))["bloqueada"] is True and solicitudes(p) == 1
        # reanudación manual registrada (se corrige la causa) y UNA solicitud nueva
        os.rmdir(str(p.ctl) + ".ack")
        pr = invocar(p, modulo, gate, "reanudar", "--quien", "Mark (prueba de banco)", "--motivo", "acuse restablecido")
        assert pr.returncode == 0 and salida(pr)["reanudado"] is True
        assert not (gate / "puerta-bloqueo.json").exists() and list(gate.glob("puerta-bloqueo.json.reanudado-*.json"))     # el caso bloqueado queda ARCHIVADO
        rm = [x for x in ab._jsonl(gate / "puerta-banco.jsonl") if x["evento"] == "reanudacion_manual"]
        assert len(rm) == 1 and rm[0]["por"] == "Mark (prueba de banco)" and len(rm[0]["caso_bloqueado"]) == 1 and Path(rm[0]["caso_bloqueado"][0]).exists()
        r2 = salida(invocar(p, modulo, gate, "preparar"))
        assert r2["lista"] is True and solicitudes(p) == 2 and p.vivo()
    finally:
        p.cierra()


def test_dos_procesos_simultaneos_emiten_una_sola_solicitud(modulo, derivado, tmp_path):
    p = Pub(derivado, tmp_path)
    try:
        gate = preparar_entorno(p, modulo)
        os.mkdir(str(p.ctl) + ".ack")
        a = invocar(p, modulo, gate, "preparar", espera=False)
        b = invocar(p, modulo, gate, "preparar", espera=False)
        a.wait(120), b.wait(120)
        ra, rb = salida(a), salida(b)
        assert solicitudes(p) == 1 and len(evidencias(p)) == 1                            # el cerrojo serializa: la segunda ve el bloqueo de la primera
        assert not ra["lista"] and not rb["lista"] and ra["bloqueada"] and rb["bloqueada"]
        assert sorted(eventos(gate)) == ["omitida_por_puerta_bloqueada", "puerta_bloqueada"]
    finally:
        p.cierra()


def test_un_fichero_de_bloqueo_ilegible_cuenta_como_bloqueado_y_no_solicita(modulo, derivado, tmp_path):
    p = Pub(derivado, tmp_path)
    try:
        gate = preparar_entorno(p, modulo, esperar_s=10.0)
        (gate / "puerta-bloqueo.json").write_text("{no es json")
        r = salida(invocar(p, modulo, gate, "preparar"))
        assert r["lista"] is False and r["bloqueada"] is True and solicitudes(p) == 0     # ante la duda, bloqueado y sin solicitud
    finally:
        p.cierra()


def test_sin_fallo_previo_un_proceso_nuevo_continua_con_acuse_valido(modulo, derivado, tmp_path):
    p = Pub(derivado, tmp_path)
    try:
        gate = preparar_entorno(p, modulo, esperar_s=10.0)
        r = salida(invocar(p, modulo, gate, "preparar"))
        assert r["lista"] is True and r["bloqueada"] is False and solicitudes(p) == 1
        assert not (gate / "puerta-bloqueo.json").exists()
    finally:
        p.cierra()
