"""Pendiente #3 en banco aislado y con datos sintéticos: la auditoría D5 rotada entre `consumido` y `publicado` se puede reconstruir por id y
secuencia leyendo la unión de generaciones; si la evidencia no alcanza, el caso es indeterminado, conserva la traza y no emite otra solicitud.
Rotación = renombrado estilo logrotate (sin copytruncate). Todas las rutas son temporales (tmp_path). Sin integración con la puerta."""
import gzip
import json
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import adaptador_banco as ab  # noqa: E402
import adaptador_banco_rot as abr  # noqa: E402
import auditoria_d5 as A  # noqa: E402
from test_d5_sin_reinicio import correr, ctl as ctl_inproc, mod, preparar  # noqa: E402,F401  (fixtures y ayudas)
from test_flujo_completo import K, OTRA, PREFIJO, Pub, derivado  # noqa: E402,F401


def rotar(ruta, keep=10, comprimir=False):
    """Rotación estilo logrotate sin copytruncate: .N -> .N+1 (se borra lo que pase de `keep`), actual -> .1."""
    ruta = str(ruta)
    try:
        if os.path.getsize(ruta) == 0:
            return False
    except OSError:
        return False
    d, b = os.path.split(ruta)
    ex = []
    for n in os.listdir(d):
        m = re.fullmatch(re.escape(b) + r"\.(\d+)(\.gz)?", n)
        if m:
            ex.append((int(m.group(1)), m.group(2) or "", n))
    for num, suf, n in sorted(ex, reverse=True):
        if num + 1 > keep:
            os.unlink(os.path.join(d, n))
        else:
            os.rename(os.path.join(d, n), os.path.join(d, "%s.%d%s" % (b, num + 1, suf)))
    os.rename(ruta, ruta + ".1")
    if comprimir:
        with open(ruta + ".1", "rb") as f, gzip.open(ruta + ".1.gz", "wb") as g:
            shutil.copyfileobj(f, g)
        os.unlink(ruta + ".1")
    return True


def registrar(nombre, datos, aud=None):
    base = os.environ.get("CF_EVIDENCIA")
    if not base:
        return
    d = Path(base) / nombre
    d.mkdir(parents=True, exist_ok=True)
    (d / "resultado.json").write_text(json.dumps(datos, indent=1, sort_keys=True, default=str, ensure_ascii=False))
    if aud is not None:
        for p in A.generaciones(aud):
            if os.path.isfile(p):
                shutil.copy2(p, d)


def resumen(d):
    return {k: d.get(k) for k in ("categoria", "determinada", "secuencia_publicada", "trazabilidad", "motivo", "generaciones_del_id")}


def escenario(mod, tmp, id_="rot-1", entre=True, despues=0, comprimir=False, keep=10):
    """Publicador real (en el mismo hilo, determinista). Rota entre `consumido` y `publicado` envolviendo solo la escritura de auditoría."""
    clave, log = preparar(tmp)
    m = mod["publicar_feed_v2_d5"]
    aud = tmp / "d5-auditoria.jsonl"
    orig = m._auditar_d5

    def envoltura(ruta, reg):
        orig(ruta, reg)
        if reg["evento"] == "consumido" and entre:
            rotar(ruta, keep, comprimir)
        if reg["evento"] == "publicado":
            for _ in range(despues):
                rotar(ruta, keep, comprimir)
    m._auditar_d5 = envoltura
    try:
        def hook(s):
            if s == 2:
                ctl_inproc(tmp, id=id_)
        correr(m, tmp, clave, log, ["--control-d5", str(tmp / "control.json"), "--d5-origen", K, "--d5-auditoria", str(aud)], hook)
    finally:
        m._auditar_d5 = orig
    ack = json.loads((tmp / "control.json.ack").read_text())
    return aud, ack["secuencia"]


def diag(tmp, aud, id_="rot-1", **kw):
    return abr.diagnosticar_rot(tmp / "control.json", id_, K, tmp / "feed.json", tmp / "estado.json", tmp / "traza.jsonl", aud, **kw)


# ---------- rotación entre consumido y publicado (determinista, publicador real) ----------
def test_rotacion_entre_consumido_y_publicado_se_reconstruye_el_id_y_la_secuencia(mod, tmp_path):
    aud, sec = escenario(mod, tmp_path)
    g = A.generaciones(aud)
    assert [os.path.basename(x) for x in g] == ["d5-auditoria.jsonl", "d5-auditoria.jsonl.1"]
    assert [x["evento"] for x in ab._jsonl(g[0])] == ["publicado"] and [x["evento"] for x in ab._jsonl(g[1])] == ["consumido"]     # repartidas
    d = diag(tmp_path, aud)
    assert d["categoria"] == "consumida_y_publicada" and d["determinada"] and d["trazabilidad"] == "completa"
    assert d["secuencia_publicada"] == sec and d["generaciones_del_id"] == ["d5-auditoria.jsonl", "d5-auditoria.jsonl.1"]
    assert d["feed_posterior_o_igual"] and len(d["auditoria"]["generaciones"]) == 2 and d["auditoria"]["estable"] and d["publicacion"] == "confirmada"
    registrar("R1-rotacion-entre-consumido-y-publicado", {"secuencia_del_acuse": sec, "diagnostico": resumen(d)}, aud)


def test_el_lector_antiguo_de_un_solo_fichero_no_reconstruye_tras_la_rotacion(mod, tmp_path):
    aud, sec = escenario(mod, tmp_path)
    d = ab.diagnosticar(tmp_path / "control.json", "rot-1", K, tmp_path / "feed.json", tmp_path / "estado.json", tmp_path / "traza.jsonl", aud)
    assert d["categoria"] == "indeterminada" and not d["determinada"]            # el defecto que corrige la propuesta
    registrar("R2-lector-antiguo-indeterminado", {"diagnostico_antiguo": d["categoria"]})


def test_rotacion_con_compresion_y_con_dos_rotaciones_sigue_reconstruyendo(mod, tmp_path):
    aud, sec = escenario(mod, tmp_path, comprimir=True, despues=1)
    nombres = sorted(os.path.basename(x) for x in A.generaciones(aud))
    assert nombres == ["d5-auditoria.jsonl.1.gz", "d5-auditoria.jsonl.2.gz"], nombres
    d = diag(tmp_path, aud)
    assert d["categoria"] == "consumida_y_publicada" and d["secuencia_publicada"] == sec and d["determinada"]
    registrar("R3-gz-y-doble-rotacion", {"generaciones": nombres, "diagnostico": resumen(d)}, aud)


def test_si_falta_la_generacion_con_consumido_el_id_queda_indeterminado_y_se_conserva_la_traza(mod, tmp_path):
    aud, sec = escenario(mod, tmp_path)
    os.unlink(str(aud) + ".1")                                                   # generación rotada perdida
    d = diag(tmp_path, aud)
    assert d["categoria"] == "indeterminada" and not d["determinada"] and d["secuencia_publicada"] is None
    assert d["trazabilidad"] == "incompleta" and "sin `consumido`" in d["motivo"] and len(d["auditoria_del_id"]) == 1
    assert d["publicacion"] == "publicación sin confirmar"
    registrar("R4-falta-generacion-con-consumido", {"diagnostico": resumen(d)}, aud)


def test_si_falta_la_generacion_con_publicado_queda_consumido_sin_publicacion_incierto(mod, tmp_path):
    aud, sec = escenario(mod, tmp_path)
    os.unlink(str(aud))                                                          # se pierde el actual (con `publicado`)
    d = diag(tmp_path, aud)
    assert d["categoria"] == "consumida_sin_publicacion" and not d["determinada"] and d["secuencia_publicada"] is None
    assert d["publicacion"] == "publicación sin confirmar"
    registrar("R5-falta-generacion-con-publicado", {"diagnostico": resumen(d)}, aud)


@pytest.mark.parametrize("cual, esperado", [(".1", "indeterminada"), ("", "consumida_sin_publicacion")])
def test_linea_truncada_se_cuenta_y_no_se_da_por_determinado(mod, tmp_path, cual, esperado):
    aud, sec = escenario(mod, tmp_path)
    p = Path(str(aud) + cual)
    t = p.read_text().rstrip("\n")
    p.write_text(t[:-18])                                                        # línea incompleta (sin cierre ni salto de línea)
    d = diag(tmp_path, aud)
    assert d["categoria"] == esperado and not d["determinada"] and d["auditoria"]["ilegibles"] == 1
    registrar("R6-linea-truncada%s" % cual.replace(".", "-"), {"diagnostico": resumen(d), "ilegibles": d["auditoria"]["ilegibles"]}, aud)


def test_auditoria_ausente_o_fuera_de_retencion_es_indeterminada(mod, tmp_path):
    d0 = diag(tmp_path, tmp_path / "no-existe.jsonl")
    assert d0["categoria"] == "indeterminada" and "ausente" in d0["motivo"] and not d0["determinada"]
    aud, sec = escenario(mod, tmp_path)
    for _ in range(3):                                                           # retención de 1 generación: las líneas del id se pierden
        with open(aud, "a") as fh:
            fh.write(json.dumps({"evento": "consumido", "id": "otro", "ok": True}) + "\n")
        rotar(aud, keep=1)
    d = diag(tmp_path, aud)
    assert d["categoria"] == "indeterminada" and "sin líneas de ese id" in d["motivo"] and d["secuencia_publicada"] is None
    registrar("R7-ausente-y-fuera-de-retencion", {"ausente": resumen(d0), "fuera_de_retencion": resumen(d)}, aud)


def test_rotacion_durante_la_lectura_se_detecta_y_se_repite(tmp_path):
    aud = tmp_path / "d5-auditoria.jsonl"
    aud.write_text(json.dumps({"evento": "consumido", "id": "x", "ok": True}) + "\n")

    def en_medio(i):
        if i == 0:                                                               # rotación y escritura nueva durante la primera lectura
            rotar(aud)
            aud.write_text(json.dumps({"evento": "publicado", "id": "x", "secuencia": 9}) + "\n")
    r = A.leer(aud, entre_lecturas=en_medio, dormir=lambda s: None)
    assert r["estable"] and r["intentos"] == 2 and sorted(x["evento"] for x in r["lineas"]) == ["consumido", "publicado"]

    def siempre(i):
        with open(aud, "a") as fh:
            fh.write(json.dumps({"evento": "ruido", "id": "z"}) + "\n")
        rotar(aud, keep=50)
    r2 = A.leer(aud, intentos=3, entre_lecturas=siempre, dormir=lambda s: None)
    assert not r2["estable"] and r2["intentos"] == 3                             # inestable: se reporta, no se oculta
    registrar("R8-rotacion-durante-la-lectura", {"estable_tras_repetir": r["estable"], "intentos": r["intentos"], "inestable_permanente": not r2["estable"]})


# ---------- publicador como proceso real + adaptador ----------
@pytest.fixture
def llamadas(monkeypatch):
    n = []
    orig = ab.cli.solicitar_reset
    monkeypatch.setattr(ab.cli, "solicitar_reset", lambda *a, **k: (n.append(1), orig(*a, **k))[1])
    return n


def adaptador(p, aud, esperar_s=2.0):
    return abr.AdaptadorBancoRot(p.ctl, p.tmp / "feed.json", p.tmp / "estado.json", p.tmp / "traza.jsonl", aud, esperar_s=esperar_s)


def test_proceso_real_acuse_falla_con_auditoria_rotada_se_reconcilia_sin_id_nuevo(derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        aud = tmp_path / "d5-auditoria.jsonl"
        os.mkdir(str(p.ctl) + ".ack")                                            # acuse no escribible
        # la auditoría se rota justo tras `consumido` desde fuera: se reproduce con un rotador rápido
        parar = threading.Event()
        t = threading.Thread(target=lambda: [(rotar(aud, 50), time.sleep(0.001)) for _ in iter(parar.is_set, True)])
        t.start()
        try:
            r = adaptador(p, aud).limpiar(K)
        finally:
            parar.set()
            t.join()
        assert not r["ok"] and r["estado"] == "sin_acuse_procesada" and len(llamadas) == 1
        assert r["categoria"] == "consumida_y_publicada" and r["determinada"] and not r["incierto"] and r["secuencia"] > 0
        assert Path(r["evidencia"]).exists() and Path(r["traza_auditoria"]).is_dir() and os.listdir(r["traza_auditoria"])
        assert p.vivo()
        registrar("P1-proceso-real-acuse-falla-auditoria-rotada", {"operacion": {k: r.get(k) for k in ("ok", "estado", "categoria", "determinada", "secuencia", "trazabilidad")},
                                                                  "solicitudes": len(llamadas)}, aud)
    finally:
        p.cierra()


def test_proceso_real_acuse_falla_y_auditoria_no_escribible_es_indeterminada_con_traza(derivado, tmp_path, llamadas):
    (tmp_path / "d5-auditoria.jsonl").mkdir()                                    # la auditoría no se puede escribir
    p = Pub(derivado, tmp_path)
    try:
        os.mkdir(str(p.ctl) + ".ack")
        r = adaptador(p, tmp_path / "d5-auditoria.jsonl").limpiar(K)
        assert not r["ok"] and r["categoria"] == "indeterminada" and r["incierto"] and not r["determinada"] and r["secuencia"] is None
        assert len(llamadas) == 1 and Path(r["evidencia"]).exists() and "directorio" in r["motivo"]
        ev = json.loads(Path(r["evidencia"]).read_text())
        assert ev["diagnostico"]["trazabilidad"] == "incompleta" and ev["resultado_cliente"]["estado"] == "sin_acuse_procesada"
        assert p.vivo() and p.espera(lambda: K not in p.ips(), 6)                # el servicio siguió; la limpieza es indeterminada para el adaptador
        g0 = p.feed()["generado"]
        assert p.espera(lambda: p.feed()["generado"] > g0, 6)
        assert "no se pudo escribir la auditoría" in (tmp_path / "stderr.txt").read_text()
        registrar("P2-proceso-real-auditoria-no-escribible", {"operacion": {k: r.get(k) for k in ("ok", "estado", "categoria", "determinada", "incierto", "motivo", "trazabilidad")},
                                                             "solicitudes": len(llamadas), "evidencia": os.path.basename(r["evidencia"])})
        shutil.copy2(r["evidencia"], Path(os.environ["CF_EVIDENCIA"]) / "P2-proceso-real-auditoria-no-escribible") if os.environ.get("CF_EVIDENCIA") else None
    finally:
        p.cierra()


def test_proceso_real_40_solicitudes_con_rotacion_continua_todas_se_reconstruyen(derivado, tmp_path):
    import d5_control as cli
    p = Pub(derivado, tmp_path)
    aud = tmp_path / "d5-auditoria.jsonl"
    parar = threading.Event()
    t = threading.Thread(target=lambda: [(rotar(aud, 400), time.sleep(0.001)) for _ in iter(parar.is_set, True)])
    t.start()
    acuses = {}
    try:
        for i in range(40):
            r = cli.solicitar_reset(p.ctl, K, esperar_s=10, id_="s-%d" % i)
            assert r["ok"], (i, r)
            acuses["s-%d" % i] = r["secuencia"]
    finally:
        parar.set()
        t.join()
        p.cierra()
    leido = A.leer(aud)
    assert leido["estable"] and leido["ilegibles"] == 0 and len(leido["generaciones"]) >= 2
    repartidas = 0
    for id_, sec in acuses.items():
        d = abr.diagnosticar_rot(p.ctl, id_, K, tmp_path / "feed.json", tmp_path / "estado.json", tmp_path / "traza.jsonl", aud)
        assert d["categoria"] == "consumida_y_publicada" and d["determinada"] and d["secuencia_publicada"] == sec, (id_, resumen(d))
        repartidas += len(d["generaciones_del_id"]) > 1
    assert repartidas >= 1                                                       # la prueba no es vacía: hubo ids partidos entre ficheros
    registrar("P3-40-solicitudes-rotacion-continua", {"solicitudes": 40, "reconstruidas": 40, "ids_repartidos_entre_ficheros": repartidas,
                                                      "generaciones": len(leido["generaciones"])}, None)


# ---------- unidades del lector y del diagnóstico ----------
def _d(tmp, id_, aud, **kw):
    return abr.diagnosticar_rot(tmp / "control.json", id_, K, tmp / "f.json", tmp / "e.json", tmp / "t.jsonl", aud, **kw)


def test_lineas_duplicadas_entre_generaciones_cuentan_una_sola_vez(tmp_path):
    aud = tmp_path / "a.jsonl"
    linea = json.dumps({"evento": "consumido", "id": "x", "ok": True}) + "\n"
    aud.write_text(linea)
    Path(str(aud) + ".1").write_text(linea)
    assert len(A.leer(aud)["lineas"]) == 1


def test_gz_corrupto_se_reporta_como_problema_y_el_id_queda_indeterminado(tmp_path):
    aud = tmp_path / "a.jsonl"
    Path(str(aud) + ".1.gz").write_bytes(b"esto no es gzip")
    d = _d(tmp_path, "x", aud)
    assert d["categoria"] == "indeterminada" and not d["determinada"] and "gz ilegible" in d["motivo"] and d["auditoria"]["problemas"]


def test_rechazado_y_no_consumida_se_determinan_con_evidencia(tmp_path):
    aud = tmp_path / "a.jsonl"
    aud.write_text(json.dumps({"evento": "consumido", "id": "r", "ok": False, "error": "origen no permitido"}) + "\n")
    d = _d(tmp_path, "r", aud)
    assert d["categoria"] == "consumida_rechazada" and d["determinada"]
    (tmp_path / "control.json").write_text("{}")                                 # el control sigue ahí: nadie lo consumió
    assert _d(tmp_path, "q", aud)["categoria"] == "no_consumida"
    (tmp_path / "control.json").unlink()
    assert _d(tmp_path, "q", aud, retiro_del_cliente=True)["categoria"] == "no_consumida"


def test_un_fichero_que_desaparece_entre_el_listado_y_la_lectura_obliga_a_repetir(tmp_path, monkeypatch):
    aud = tmp_path / "a.jsonl"
    aud.write_text(json.dumps({"evento": "consumido", "id": "x", "ok": True}) + "\n")
    real, llamadas = A.generaciones, []

    def con_fantasma(ruta):
        llamadas.append(1)
        return ([str(tmp_path / "a.jsonl.1")] if len(llamadas) <= 2 else []) + real(ruta)     # listado con una generación que ya no existe
    monkeypatch.setattr(A, "generaciones", con_fantasma)
    r = A.leer(aud, dormir=lambda s: None)
    assert r["estable"] and r["intentos"] == 2 and len(r["lineas"]) == 1
