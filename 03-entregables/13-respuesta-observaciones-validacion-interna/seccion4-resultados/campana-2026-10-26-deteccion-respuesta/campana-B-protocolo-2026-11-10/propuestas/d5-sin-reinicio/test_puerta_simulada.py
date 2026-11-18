"""Verificación del SIMULADOR (puerta D5 simulada del arnés) con el adaptador aislado, publicador real como proceso y datos sintéticos.
`compuerta_b` (herramientas de la Campaña B) se monta de solo lectura en /herramientas y solo se importa; no se modifica ni se instala."""
import json
import os
import shutil
import signal
import sys
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
import puerta_simulada_banco as ps  # noqa: E402
from test_flujo_completo import K, Pub, derivado  # noqa: E402,F401


@pytest.fixture
def pub(derivado, tmp_path):
    p = Pub(derivado, tmp_path)
    yield p
    p.cierra()


@pytest.fixture
def llamadas(monkeypatch):
    ids = []
    orig = ab.cli.solicitar_reset
    monkeypatch.setattr(ab.cli, "solicitar_reset", lambda *a, **k: (ids.append(k.get("id_")), orig(*a, **k))[1])
    return ids


def montar(pub, auditoria=True, esperar_s=1.5):
    gate = str(pub.tmp / "compuerta")
    with cb.Estado(gate) as st:                                   # estado de la compuerta: puerta pendiente, un episodio ya terminado
        st.update(pendiente=True, en_episodio=False, n_inicios=1, fin_en=None)
    ad = abr.AdaptadorBancoRot(pub.ctl, pub.tmp / "feed.json", pub.tmp / "estado.json", pub.tmp / "traza.jsonl",
                               (pub.tmp / "d5-auditoria.jsonl") if auditoria else None, esperar_s=esperar_s)
    fn = ps.PuertaSimulada(ad, K, pub.tmp / "puerta-simulada.jsonl")
    return gate, fn


def estado(gate):
    with cb.Estado(gate) as st:
        return dict(st)


def registrar(nombre, pub, gate, datos):
    base = os.environ.get("CF_EVIDENCIA")
    if not base:
        return
    d = Path(base) / nombre
    d.mkdir(parents=True, exist_ok=True)
    (d / "resultado.json").write_text(json.dumps(datos, indent=1, sort_keys=True, default=str, ensure_ascii=False))
    for f in ("puerta-simulada.jsonl", "d5-auditoria.jsonl", "traza.jsonl"):
        if (pub.tmp / f).is_file():
            shutil.copy2(pub.tmp / f, d)
    shutil.copy2(Path(gate) / "gate.json", d)
    for g in pub.tmp.glob("control.json.evidencia-*"):
        if g.is_file():
            shutil.copy2(g, d)
        else:
            shutil.copytree(g, d / g.name, dirs_exist_ok=True)


def test_acuse_valido_la_puerta_simulada_libera_y_el_episodio_continua(pub, llamadas):
    gate, fn = montar(pub, esperar_s=10)
    r = cb.paso_puerta(gate, fn, espera_fin=0)
    st = estado(gate)
    assert r == "liberada" and st["pendiente"] is False and st["liberada_en"] is not None      # el simulador puede lanzar el siguiente episodio
    assert fn.solicitudes == 1 and fn.bloqueada is None and len(llamadas) == 1
    assert K not in pub.ips() and pub.vivo()
    registrar("T1-acuse-valido", pub, gate, {"paso_puerta": r, "gate": st, "solicitudes": fn.solicitudes})


def test_acuse_no_escribible_deja_el_caso_fallido_conserva_la_traza_y_no_repite(pub, llamadas):
    os.mkdir(str(pub.ctl) + ".ack")
    gate, fn = montar(pub)
    rs = [cb.bucle(gate, fn, sondeo=0, dormir=lambda s: None, max_iter=1, espera_fin=0) for _ in range(1)]
    r2 = [cb.paso_puerta(gate, fn, espera_fin=0) for _ in range(3)]                             # la compuerta insiste: 3 turnos más
    st = estado(gate)
    assert rs == ["fallida"] and r2 == ["fallida"] * 3 and st["pendiente"] is True            # el episodio NO continúa
    assert fn.solicitudes == 1 and fn.omitidas == 3 and len(llamadas) == 1                    # NO se emitió otra solicitud
    b = fn.bloqueada
    assert not b["ok"] and b["estado"] == "sin_acuse_procesada" and b["categoria"] == "consumida_y_publicada" and b["publicacion"] == "confirmada"
    assert Path(b["evidencia"]).exists() and Path(b["traza_auditoria"]).is_dir() and os.listdir(b["traza_auditoria"])
    assert not pub.ctl.exists() and len([x for x in ab._jsonl(pub.tmp / "d5-auditoria.jsonl") if x["evento"] == "consumido"]) == 1
    reg = ab._jsonl(pub.tmp / "puerta-simulada.jsonl")
    assert [x["evento"] for x in reg] == ["solicitud", "omitida_por_caso_fallido", "omitida_por_caso_fallido", "omitida_por_caso_fallido"]
    registrar("T2-acuse-no-escribible", pub, gate, {"pasos": rs + r2, "gate": st, "solicitudes": fn.solicitudes, "omitidas": fn.omitidas,
                                                       "caso": {k: b.get(k) for k in ("ok", "estado", "categoria", "determinada", "publicacion", "secuencia")}})


def test_acuse_ausente_publicador_detenido_falla_retira_el_control_y_no_repite(pub, llamadas):
    gate, fn = montar(pub, esperar_s=0.6)
    os.kill(pub.p.pid, signal.SIGSTOP)
    try:
        r = [cb.paso_puerta(gate, fn, espera_fin=0) for _ in range(3)]
    finally:
        os.kill(pub.p.pid, signal.SIGCONT)
    time.sleep(1.0)
    assert r == ["fallida"] * 3 and estado(gate)["pendiente"] is True and fn.solicitudes == 1 and len(llamadas) == 1
    assert fn.bloqueada["categoria"] == "no_consumida" and not pub.ctl.exists() and K in pub.ips()      # no se limpió nada y no quedó control vivo
    registrar("T3-acuse-ausente-publicador-detenido", pub, gate, {"pasos": r, "solicitudes": fn.solicitudes})


def test_evidencia_indeterminada_queda_fallida_con_traza_y_sin_solicitud_nueva(pub, llamadas):
    os.mkdir(str(pub.ctl) + ".ack")
    gate, fn = montar(pub, auditoria=False)                                                       # sin auditoría: no se puede determinar
    r = [cb.paso_puerta(gate, fn, espera_fin=0) for _ in range(3)]
    b = fn.bloqueada
    assert r == ["fallida"] * 3 and estado(gate)["pendiente"] is True and fn.solicitudes == 1 and len(llamadas) == 1
    assert b["categoria"] == "indeterminada" and b["incierto"] and b["publicacion"] == "publicación sin confirmar" and Path(b["evidencia"]).exists()
    registrar("T4-indeterminado", pub, gate, {"pasos": r, "caso": {k: b.get(k) for k in ("ok", "estado", "categoria", "incierto", "publicacion", "motivo")}})


def test_solo_una_reanudacion_manual_permite_otra_solicitud_y_con_id_distinto(pub, llamadas):
    os.mkdir(str(pub.ctl) + ".ack")
    gate, fn = montar(pub)
    cb.paso_puerta(gate, fn, espera_fin=0)
    cb.paso_puerta(gate, fn, espera_fin=0)
    assert len(llamadas) == 1
    os.rmdir(str(pub.ctl) + ".ack")                                                             # Mark corrige la causa y decide reanudar
    fn.reanudar_manual("Mark (prueba de banco)")
    r = cb.paso_puerta(gate, fn, espera_fin=0)
    assert len(llamadas) == 2 and fn.solicitudes == 2
    reg = [x["evento"] for x in ab._jsonl(pub.tmp / "puerta-simulada.jsonl")]
    assert reg == ["solicitud", "omitida_por_caso_fallido", "reanudacion_manual", "solicitud"]
    assert r == "liberada" and estado(gate)["pendiente"] is False                               # corregida la causa, la nueva solicitud sí obtiene acuse
    registrar("T5-reanudacion-manual", pub, gate, {"registro": reg, "paso_tras_reanudar": r})


def test_hallazgo_el_cableado_ingenuo_repite_la_solicitud_con_id_nuevo_en_cada_turno(pub, llamadas):
    os.mkdir(str(pub.ctl) + ".ack")
    gate, _ = montar(pub)
    ad = abr.AdaptadorBancoRot(pub.ctl, pub.tmp / "feed.json", pub.tmp / "estado.json", pub.tmp / "traza.jsonl", pub.tmp / "d5-auditoria.jsonl", esperar_s=0.8)
    ingenua = lambda: {"lista": ad.limpiar(K)["ok"], "intentos": 1}                          # sin bloqueo tras el fallo
    for _ in range(3):
        cb.paso_puerta(gate, ingenua, espera_fin=0)
        if pub.ctl.exists():
            pub.ctl.unlink()
    assert len(llamadas) == 3                                                                   # 3 solicitudes reales en 3 turnos
    assert len(list(pub.tmp.glob("control.json.evidencia-*.json"))) == 3                       # cada una con su propio id (un fichero de evidencia por id)
    registrar("T6-hallazgo-cableado-ingenuo", pub, gate, {"solicitudes_reales": len(llamadas)})
