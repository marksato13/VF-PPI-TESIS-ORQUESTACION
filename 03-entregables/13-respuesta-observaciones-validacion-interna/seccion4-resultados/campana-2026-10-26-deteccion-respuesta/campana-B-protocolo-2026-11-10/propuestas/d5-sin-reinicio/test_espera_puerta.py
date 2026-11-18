"""Hallazgo 2 — propuesta A (puerta a fin + 75 s) probada en banco con el MISMO mecanismo (`compuerta_b.paso_puerta` con su `espera_fin`, la puerta integrada y el
publicador real como proceso) a ESCALA 1/60 de tiempo (15 s -> 0,25 s; 50,6 s -> 0,84 s; 75 s -> 1,25 s). Prueba la LÓGICA de la espera, no las duraciones reales.
Una decisión nueva sobre la Kali (cola de la ventana de 60 s del episodio anterior) llega a `t_tardia` s del fin. Datos sintéticos."""
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HERR = Path(os.environ.get("CF_HERRAMIENTAS", "/herramientas"))
if not (HERR / "compuerta_b.py").exists():
    pytest.skip("herramientas de la Campaña B no montadas", allow_module_level=True)
sys.path.insert(0, str(HERR))
import adaptador_banco as ab  # noqa: E402
import adaptador_banco_rot as abr  # noqa: E402
import compuerta_b as cb  # noqa: E402
import hacer_d5_episodio_banco as hd  # noqa: E402
from test_flujo_completo import K, Pub, decision, derivado  # noqa: E402,F401

E = 60.0


@pytest.fixture(scope="module")
def banco_mod():
    d = Path(tempfile.mkdtemp(prefix="d5w_"))
    assert hd.main(str(HERR / "d5_episodio.py"), str(d / "d5_episodio_banco.py")) == 0
    spec = importlib.util.spec_from_file_location("d5_episodio_banco", d / "d5_episodio_banco.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["d5_episodio_banco"] = m
    spec.loader.exec_module(m)
    return m


class Nft:
    def __call__(self, peticion):
        op = peticion["operaciones"][0]["op"]
        return {"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": {}}, "descartes_limite": {}}} if op == "listar" else {"ok": True}


def episodio(banco_mod, derivado, tmp_path, espera_fin_s, tardia_s):
    """Devuelve (resultado de paso_puerta, puerta, publicador, nº de solicitudes). Un episodio acaba AHORA; la puerta corre a fin + espera_fin."""
    p = Pub(derivado, tmp_path)
    gate = tmp_path / "compuerta"
    t_fin = time.time()
    with cb.Estado(str(gate)) as st:
        st.update(pendiente=True, en_episodio=False, n_inicios=1, fin_en=t_fin)
    (tmp_path / "agente-traza.jsonl").write_text("")

    def tardia():
        time.sleep(max(0.0, t_fin + tardia_s / E - time.time()))
        with open(p.log, "a") as fh:
            fh.write(json.dumps(decision(K, "http_abuse", "BLOCK", 777)) + "\n")
    hilo = threading.Thread(target=tardia, daemon=True)
    hilo.start()
    ad = abr.AdaptadorBancoRot(p.ctl, p.tmp / "feed.json", p.tmp / "estado.json", p.tmp / "traza.jsonl", p.tmp / "d5-auditoria.jsonl", esperar_s=10.0)
    rn = banco_mod.RunnersBanco(ad, p.tmp / "feed.json", tmp_path / "agente-traza.jsonl", Nft())
    pu = banco_mod.PuertaBanco(rn, registro=str(gate / "puerta-banco.jsonl"), estado_bloqueo=str(gate / "puerta-bloqueo.json"), espera_agente=2.0, espera_feed=6.0, sondeo=0.1)
    r = cb.paso_puerta(str(gate), pu.preparar_episodio, espera_fin=espera_fin_s / E)
    hilo.join()
    return r, pu, p, len([x for x in ab._jsonl(p.tmp / "d5-auditoria.jsonl") if x["evento"] == "consumido"])


def test_con_la_puerta_a_fin_mas_15_s_la_decision_tardia_hace_fallar_y_bloquea(banco_mod, derivado, tmp_path):
    p = None
    try:
        r, pu, p, n = episodio(banco_mod, derivado, tmp_path, espera_fin_s=15.0, tardia_s=50.6)       # el patrón de B2 (#7: fin + 50,6 s)
        assert r == "fallida" and pu._bloqueo_actual() is not None and n == 1                         # una solicitud; la puerta queda bloqueada
    finally:
        if p:
            p.cierra()


def test_con_la_puerta_a_fin_mas_75_s_la_decision_tardia_ya_esta_y_se_limpia_sin_ignorarla(banco_mod, derivado, tmp_path):
    p = None
    try:
        r, pu, p, n = episodio(banco_mod, derivado, tmp_path, espera_fin_s=75.0, tardia_s=50.6)
        assert r == "liberada" and pu._bloqueo_actual() is None and n == 1                            # pasa, con UNA sola solicitud
        pubs = [x for x in ab._jsonl(p.tmp / "traza.jsonl") if x.get("evento") == "publicacion"]
        nuevas_k = [n_ for x in pubs for n_ in x.get("nuevos", []) if n_["ip"] == K]
        assert len(nuevas_k) >= 2                                                                     # la señal tardía SE VIO (no se ignoró)…
        ack = json.loads((p.tmp / "control.json.ack").read_text())
        assert ack["ok"] and len(ack["quitado"]["vigentes"]) == 1                                     # …y la limpieza la quitó (un estado vigente de la Kali)
        assert K not in p.ips() and p.vivo()
    finally:
        if p:
            p.cierra()


def test_limite_una_decision_posterior_a_fin_mas_75_s_vuelve_a_bloquear(banco_mod, derivado, tmp_path):
    p = None
    try:
        r, pu, p, n = episodio(banco_mod, derivado, tmp_path, espera_fin_s=75.0, tardia_s=85.0)       # llega durante la comprobación del agente
        assert r == "fallida" and pu._bloqueo_actual() is not None and n == 1                         # el límite de la propuesta: no elimina TODAS las colas posibles
    finally:
        if p:
            p.cierra()
