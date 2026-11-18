"""Copia de banco del lanzador del bastión: su llamada a la puerta integrada con OpenSSH real y datos sintéticos (srv-dmz sintético). El lanzador corre como el usuario
del bastión (uid 1002) en un proceso nuevo en cada invocación; `compuerta_b` se importa de solo lectura (no se modifica). Requiere root (como test_ssh_real_d5)."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import adaptador_banco as ab  # noqa: E402
import hacer_d5_episodio_banco as hd  # noqa: E402
import test_ssh_real_d5 as S  # noqa: E402
from test_ssh_real_d5 import red, sensor, autorizar, banco_mod, derivado  # noqa: E402,F401
HERR = Path(os.environ.get("CF_HERRAMIENTAS", "/herramientas"))
import compuerta_b as cb  # noqa: E402  (herramientas en solo lectura)

G = "/home/gadmin"


@pytest.fixture
def d5_banco(tmp_path):
    d = Path(tempfile.mkdtemp(prefix="d5l_"))
    assert hd.main(str(HERR / "d5_episodio.py"), str(d / "d5_episodio_banco.py")) == 0
    os.chmod(d, 0o755)
    os.chmod(d / "d5_episodio_banco.py", 0o644)
    return d / "d5_episodio_banco.py"


def puerta_dir(tmp_path):
    g = Path(G) / ("compuerta-%s" % tmp_path.name[-12:])
    g.mkdir(parents=True, exist_ok=True)
    os.chown(g, 1002, 1002)
    with cb.Estado(str(g)) as st:
        st.update(pendiente=True, en_episodio=False, n_inicios=1, fin_en=time.time())
    for f in g.iterdir():
        os.chown(f, 1002, 1002)
    return g


def lanzador(g, d5, sensor, kh="known_hosts_ok", puerto=S.PUERTO, extra=(), modo="ejecutar", timeout=120):
    base = [sys.executable, "-I", str(AQUI / "lanzador_puerta_banco.py")]
    if modo == "ejecutar":
        args = base + ["ejecutar", "--dir", str(g), "--d5-banco", str(d5), "--sensor", "m4rk@127.0.0.1", "--clave", G + "/.ssh/id_bastion", "--known-hosts", G + "/.ssh/" + kh,
                       "--puerto", str(puerto), "--herramientas", str(HERR), "--srv-sintetico", "--espera-fin", "0.2", "--espera-agente", "2", "--espera-feed", "6", "--sondeo-puerta", "0.1",
                       "--sondeo-bucle", "0.1", "--esperar-limpieza", "4", "--sondeo-consulta", "0.1", "--fallos-consulta", "2", "--timeout-ssh", "6", "--uid-pruebas", "1002",
                       "--home-pruebas", G, *extra]
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, user=1002, group=1002, env={"HOME": G, "PATH": "/usr/bin:/bin"})
    return subprocess.run(base + [modo, "--dir", str(g), "--d5-banco", str(d5), *extra], capture_output=True, text=True, timeout=timeout, user=1002, group=1002, env={"HOME": G, "PATH": "/usr/bin:/bin"})


def log_gate(g):
    p = Path(g) / "compuerta.log"
    return [l.split()[1] for l in p.read_text().splitlines()] if p.exists() else []


def conexiones(red):
    return Path(red["log"]).read_text().count("Accepted publickey")


def test_el_lanzador_llama_a_la_puerta_integrada_y_libera_con_acuse(red, sensor, d5_banco, tmp_path):
    autorizar(sensor)
    g = puerta_dir(tmp_path)
    t = time.perf_counter()
    r = lanzador(g, d5_banco, sensor, extra=("--max-iter", "1"))
    S.TIEMPOS["lanzador_una_puerta_con_ssh_real_s"] = round(time.perf_counter() - t, 3)
    assert r.returncode == 0, r.stderr[-600:]
    assert log_gate(g) == ["liberada"] and cb.Estado(str(g)).__enter__()["pendiente"] is False
    assert len(sensor.lineas_aud("consumido")) == 1 and not (g / "puerta-bloqueo.json").exists()
    pasos = [json.loads(l) for l in (g / "puertas-D5.jsonl").read_text().splitlines()]
    assert pasos[0]["lista"] is True and [x["paso"] for x in pasos[0]["pasos"]][:2] == ["limpiar", "feed_tras_limpiar"]
    assert sensor.vivo()


def test_fallo_de_transporte_bloquea_y_el_bloqueo_sobrevive_a_nuevas_ejecuciones_del_lanzador(red, sensor, d5_banco, tmp_path):
    autorizar(sensor)
    g = puerta_dir(tmp_path)
    # identidad del servidor NO fijada correctamente: ssh se niega y ninguna orden llega al Sensor1
    r = lanzador(g, d5_banco, sensor, kh="known_hosts_vacio", extra=("--max-iter", "3"))
    assert r.returncode == 0 and log_gate(g) == ["fallida"] * 3                                  # la compuerta insiste 3 veces
    assert (g / "puerta-bloqueo.json").exists() and (g / "estado" / "limpieza-pendiente.json").exists()
    id_ = json.loads((g / "estado" / "limpieza-pendiente.json").read_text())["id"]
    reg = [x["evento"] for x in ab._jsonl(g / "puerta-banco.jsonl")]
    assert reg == ["puerta_bloqueada", "omitida_por_puerta_bloqueada", "omitida_por_puerta_bloqueada"]       # 1 intento real, 2 omitidos: sin solicitudes nuevas
    c0 = conexiones(red)
    r = lanzador(g, d5_banco, sensor, extra=("--max-iter", "2"))                                 # ssh YA funciona, pero el bloqueo persiste (proceso nuevo)
    assert log_gate(g)[-2:] == ["fallida", "fallida"] and conexiones(red) == c0
    assert not (sensor.ctl / "solicitudes").exists() or not list((sensor.ctl / "solicitudes").glob("*.json"))
    # reanudar manual (solo registra) -> la siguiente ejecución CONSULTA el id pendiente (el Sensor1 no lo conoce): sigue incierto y bloqueado, sin reenviar
    assert lanzador(g, d5_banco, sensor, modo="reanudar", extra=("--quien", "", "--motivo", "x")).returncode == 2
    assert lanzador(g, d5_banco, sensor, modo="reanudar", extra=("--quien", "Mark (prueba de banco)", "--motivo", "SSH y huésped corregidos")).returncode == 0
    r = lanzador(g, d5_banco, sensor, extra=("--max-iter", "1"))
    assert log_gate(g)[-1] == "fallida" and json.loads((g / "estado" / "limpieza-pendiente.json").read_text())["id"] == id_
    assert not (sensor.ctl / "solicitudes").exists() or not list((sensor.ctl / "solicitudes").glob("*.json"))     # no se reenvió con el mismo id
    # descarte manual del pendiente + reanudación -> UN id nuevo, la puerta se libera
    assert lanzador(g, d5_banco, sensor, modo="descartar-pendiente", extra=("--quien", "Mark (prueba de banco)", "--motivo", "la orden nunca llegó")).returncode == 0
    assert lanzador(g, d5_banco, sensor, modo="reanudar", extra=("--quien", "Mark (prueba de banco)", "--motivo", "id nuevo autorizado")).returncode == 0
    r = lanzador(g, d5_banco, sensor, extra=("--max-iter", "1"))
    assert log_gate(g)[-1] == "liberada" and len(sensor.lineas_aud("consumido")) == 1 and not (g / "estado" / "limpieza-pendiente.json").exists()
    ev = [x["evento"] for x in ab._jsonl(g / "puerta-banco.jsonl")]
    assert ev.count("reanudacion_manual") == 2 and ev[-1] == "puerta_lista"
