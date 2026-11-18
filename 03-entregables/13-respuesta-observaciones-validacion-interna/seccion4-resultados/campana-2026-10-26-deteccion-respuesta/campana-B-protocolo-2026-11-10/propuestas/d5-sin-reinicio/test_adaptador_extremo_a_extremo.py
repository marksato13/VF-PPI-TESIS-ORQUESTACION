"""Banco aislado y datos sintéticos: adaptador de prueba de punta a punta (cliente -> publicador real como proceso -> limpieza -> acuse).
NO se conecta a d5_episodio.py ni al orquestador. Regla probada: ante acuse ausente o incierto NO se emite otra solicitud (ni con id
nuevo); el caso es FALLIDO, se conserva la evidencia y se distingue con la auditoría del publicador si la solicitud original se
consumió y qué secuencia se publicó. Si no se puede determinar, queda «incierto»."""
import json
import os
import signal
import sys
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import adaptador_banco as ab  # noqa: E402
from test_flujo_completo import K, OTRA, PREFIJO, Pub, decision, derivado  # noqa: E402,F401  (fixtures)


@pytest.fixture
def pub(derivado, tmp_path):
    p = Pub(derivado, tmp_path)
    yield p
    p.cierra()


def adaptador(pub, auditoria=True, esperar_s=1.5):
    return ab.AdaptadorBanco(pub.ctl, pub.tmp / "feed.json", pub.tmp / "estado.json", pub.tmp / "traza.jsonl",
                             (pub.tmp / "d5-auditoria.jsonl") if auditoria else None, esperar_s=esperar_s)


def audit(pub):
    return ab._jsonl(pub.tmp / "d5-auditoria.jsonl")


@pytest.fixture
def llamadas(monkeypatch):
    n = []
    orig = ab.cli.solicitar_reset
    monkeypatch.setattr(ab.cli, "solicitar_reset", lambda *a, **k: (n.append(k.get("id_")), orig(*a, **k))[1])
    return n


def test_flujo_extremo_a_extremo_con_acuse(pub, llamadas):
    e0 = pub.estado()
    r = adaptador(pub, esperar_s=10).limpiar(K)
    assert r["ok"] and r["estado"] == "acuse" and not r["incierto"] and r["secuencia"] > 0 and len(llamadas) == 1
    a = audit(pub)
    assert [x["evento"] for x in a] == ["consumido", "publicado"] and a[1]["secuencia"] == r["secuencia"] and a[0]["ok"]
    assert K not in pub.ips() and {OTRA, PREFIJO} <= pub.ips() and pub.vivo()
    assert not list(pub.tmp.glob("control.json.evidencia-*"))                 # con acuse no hay caso fallido que conservar
    e1 = pub.estado()
    assert [v for k, v in e1["vigentes"].items() if k.startswith(OTRA + "|")] == [v for k, v in e0["vigentes"].items() if k.startswith(OTRA + "|")]


def test_acuse_falla_tras_limpiar_se_reconcilia_sin_emitir_id_nuevo(pub, llamadas):
    os.mkdir(str(pub.ctl) + ".ack")                                           # el acuse no se puede escribir
    r = adaptador(pub).limpiar(K)
    assert not r["ok"] and r["estado"] == "sin_acuse_procesada" and r["rc"] == 6
    assert r["categoria"] == "consumida_y_publicada" and r["determinada"] and not r["incierto"]
    a = audit(pub)
    pubs = [x for x in a if x["evento"] == "publicado"]
    assert r["secuencia"] == pubs[-1]["secuencia"] and [x["evento"] for x in a] == ["consumido", "publicado", "ack_fallido"]
    assert len(llamadas) == 1                                                  # UNA sola solicitud: no hubo reintento con id nuevo
    time.sleep(1.0)
    assert len([x for x in audit(pub) if x["evento"] == "consumido"]) == 1 and not pub.ctl.exists()
    ev = json.loads(Path(r["evidencia"]).read_text())
    assert ev["diagnostico"]["categoria"] == "consumida_y_publicada" and ev["resultado_cliente"]["estado"] == "sin_acuse_procesada"
    assert ev["diagnostico"]["estado"] == {"vigentes": [], "escalada": []}      # el estado persistido ya no tiene a la Kali
    assert pub.feed()["secuencia"] >= r["secuencia"] and pub.vivo()


def test_limpieza_ocurrio_acuse_fallo_y_la_propuesta_nueva_se_conserva(pub, llamadas):
    os.mkdir(str(pub.ctl) + ".ack")
    r = adaptador(pub).limpiar(K)
    assert not r["ok"] and r["categoria"] == "consumida_y_publicada"
    with open(pub.log, "a") as fh:                                             # después llega una propuesta NUEVA legítima sobre la Kali
        fh.write(json.dumps(decision(K, "brute_force", "BLOCK", 321)) + "\n")
    assert pub.espera(lambda: K in pub.ips(), 8)
    nueva = [x["id"] for x in pub.feed()["entradas"] if x["ip"] == K]
    assert nueva
    # La reconciliación de la solicitud ORIGINAL sigue diciendo lo mismo (por la auditoría) y NO se vuelve a limpiar a la Kali
    d = ab.diagnosticar(pub.ctl, r["id"], K, pub.tmp / "feed.json", pub.tmp / "estado.json", pub.tmp / "traza.jsonl",
                        pub.tmp / "d5-auditoria.jsonl")
    assert d["categoria"] == "consumida_y_publicada" and d["secuencia_publicada"] == r["secuencia"]
    assert d["feed"]["secuencia"] > r["secuencia"] and d["feed"]["entradas_origen"] == nueva    # feed posterior: contiene lo nuevo
    time.sleep(1.0)
    assert [x["id"] for x in pub.feed()["entradas"] if x["ip"] == K] == nueva and len(llamadas) == 1
    assert len([x for x in audit(pub) if x["evento"] == "consumido"]) == 1 and pub.vivo()


def test_acuse_ausente_con_publicador_detenido_no_consumida_y_sin_id_nuevo(pub, llamadas):
    os.kill(pub.p.pid, signal.SIGSTOP)
    try:
        r = adaptador(pub, esperar_s=0.6).limpiar(K)
        assert not r["ok"] and r["estado"] == "sin_acuse_no_procesada" and r["categoria"] == "no_consumida" and r["determinada"]
        assert not r["incierto"] and len(llamadas) == 1 and not pub.ctl.exists() and Path(r["evidencia"]).exists()
    finally:
        os.kill(pub.p.pid, signal.SIGCONT)
    time.sleep(1.0)
    assert audit(pub) == [] and K in pub.ips() and pub.vivo()                  # nada se consumió: el estado de la Kali sigue ahí


def test_sin_auditoria_no_se_puede_determinar_es_incierto_y_fallido_y_se_conserva_la_evidencia(pub, llamadas):
    os.mkdir(str(pub.ctl) + ".ack")
    r = adaptador(pub, auditoria=False).limpiar(K)                             # sin la auditoría del publicador no hay con qué afirmar nada
    assert not r["ok"] and r["categoria"] == "indeterminada" and not r["determinada"] and r["incierto"] and r["secuencia"] is None
    assert len(llamadas) == 1 and Path(r["evidencia"]).exists()
    ev = json.loads(Path(r["evidencia"]).read_text())
    assert ev["diagnostico"]["auditoria_disponible"] is False and "feed" in ev["diagnostico"] and "estado" in ev["diagnostico"]


def test_otros_casos_independientes_siguen_tras_un_caso_incierto(derivado, tmp_path_factory):
    resultados = []
    for i in range(2):                                                         # el caso incierto no impide el siguiente caso independiente
        tmp = tmp_path_factory.mktemp("caso%d" % i)
        p = Pub(derivado, tmp)
        try:
            if i == 0:
                os.mkdir(str(p.ctl) + ".ack")
            resultados.append(adaptador(p, auditoria=(i == 1), esperar_s=1.5).limpiar(K))
        finally:
            p.cierra()
    assert resultados[0]["categoria"] == "indeterminada" and resultados[0]["incierto"] and not resultados[0]["ok"]
    assert resultados[1]["ok"] and resultados[1]["estado"] == "acuse"


def test_si_la_auditoria_no_se_puede_escribir_el_publicador_sigue_y_el_acuse_llega(derivado, tmp_path):
    (tmp_path / "d5-auditoria.jsonl").mkdir()                                  # el destino de la auditoría es un directorio: escribirlo falla
    p = Pub(derivado, tmp_path)
    try:
        r = adaptador(p, auditoria=False, esperar_s=10).limpiar(K)
        assert r["ok"] and r["estado"] == "acuse" and K not in p.ips() and p.vivo()
        assert "no se pudo escribir la auditoría" in (tmp_path / "stderr.txt").read_text()
    finally:
        p.cierra()


def test_pendiente_previa_no_escribe_nada_ni_emite_otra_solicitud(pub, llamadas):
    os.kill(pub.p.pid, signal.SIGSTOP)
    try:
        pub.ctl.write_text(json.dumps({"accion": "reset_origen", "origen": K, "id": "primero"}))
        r = adaptador(pub, esperar_s=0.3).limpiar(K)
        assert not r["ok"] and r["estado"] == "pendiente_previa" and r["evidencia"] is None
        assert json.loads(pub.ctl.read_text())["id"] == "primero"
    finally:
        os.kill(pub.p.pid, signal.SIGCONT)


def test_diagnostico_con_auditoria_sintetica_cubre_las_categorias(tmp_path):
    aud, ctl = tmp_path / "a.jsonl", tmp_path / "c.json"
    f = tmp_path / "f.json"
    f.write_text(json.dumps({"secuencia": 7, "generado": 1, "entradas": []}))

    def diag(lineas, **kw):
        aud.write_text("".join(json.dumps(x) + "\n" for x in lineas))
        return ab.diagnosticar(ctl, "i1", K, f, tmp_path / "e.json", tmp_path / "t.jsonl", aud, **kw)
    assert diag([{"evento": "consumido", "id": "i1", "ok": False, "error": "x"}])["categoria"] == "consumida_rechazada"
    d = diag([{"evento": "consumido", "id": "i1", "ok": True}])
    assert d["categoria"] == "consumida_sin_publicacion" and not d["determinada"]           # consumida pero sin publicación: incierta
    d = diag([{"evento": "consumido", "id": "i1", "ok": True}, {"evento": "publicado", "id": "i1", "secuencia": 5}])
    assert d["categoria"] == "consumida_y_publicada" and d["secuencia_publicada"] == 5 and d["feed_posterior_o_igual"]
    d = diag([{"evento": "consumido", "id": "otro", "ok": True}, {"evento": "publicado", "id": "otro", "secuencia": 6}])
    assert d["categoria"] == "indeterminada" and not d["determinada"]                       # la auditoría de OTRO id no cuenta
    ctl.write_text("{}")
    assert diag([])["categoria"] == "no_consumida"                                          # el control sigue ahí


def test_la_evidencia_nunca_se_sobrescribe(tmp_path):
    c = tmp_path / "control.json"
    rutas = {ab._guardar_evidencia(c, "x", {"n": i}) for i in range(3)}
    assert len(rutas) == 3 and sorted(json.loads(Path(r).read_text())["n"] for r in rutas) == [0, 1, 2]
