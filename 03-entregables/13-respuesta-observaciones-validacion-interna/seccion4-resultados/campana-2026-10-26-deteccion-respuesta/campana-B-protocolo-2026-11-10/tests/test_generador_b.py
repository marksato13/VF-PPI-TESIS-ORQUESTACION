"""El permiso de la variante queda ligado al episodio Y a la corrida (nonce + arranque); el original no cambia su comportamiento."""
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pytest

GEN = Path(__file__).resolve().parent.parent / "generador"
sys.path.insert(0, str(GEN))


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, GEN / (nombre + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B, ORIG = cargar("generar_campana_b"), cargar("generar_campana_original")
T = 1_000_000.0


def permiso(tmp, **kw):
    p = {"nonce": "corrida-2", "estado": "continuar", "causas": [], "emitido_epoch": T, "valido_hasta_epoch": T + 150, "episodio": "ep-r1"}
    p.update(kw)
    ruta = tmp / "permiso.json"
    ruta.write_text(json.dumps({k: v for k, v in p.items() if v is not None}))
    return ruta


def leer(m, ruta, siguiente="ep-r1", por_ep=True, nonce="corrida-2", arranque=T - 10, ahora=T + 5):
    return m.leer_permiso(ruta, nonce, arranque, ahora, siguiente, por_ep)


def test_valido_para_ese_episodio_y_esa_corrida(tmp_path):
    assert leer(B, permiso(tmp_path))[0] == "continuar"


def test_mismo_episodio_de_OTRA_corrida_no_sirve(tmp_path):
    e, motivo = leer(B, permiso(tmp_path, nonce="corrida-1"))
    assert e == "pausa" and "otra corrida" in motivo


def test_mismo_episodio_y_nonce_pero_emitido_antes_del_arranque_no_sirve(tmp_path):
    e, motivo = leer(B, permiso(tmp_path, emitido_epoch=T - 3600, valido_hasta_epoch=T + 150), arranque=T - 10)
    assert e == "pausa" and "antes del arranque" in motivo


def test_otro_episodio_o_sin_episodio_no_sirve(tmp_path):
    assert leer(B, permiso(tmp_path, episodio="otro-r2"))[0] == "pausa"
    assert leer(B, permiso(tmp_path, episodio=None))[0] == "pausa"


def test_caducado_no_sirve(tmp_path):
    assert leer(B, permiso(tmp_path), ahora=T + 151)[0] == "pausa"


def test_cancelar_vale_siempre_y_pausa_sigue_siendo_pausa(tmp_path):
    assert leer(B, permiso(tmp_path, estado="cancelar", episodio="otro", nonce="corrida-2"))[0] == "cancelar"
    assert leer(B, permiso(tmp_path, estado="pausa"))[0] == "pausa"


def test_sin_la_opcion_la_variante_se_comporta_como_el_original(tmp_path):
    r = permiso(tmp_path, episodio="otro")
    for caso in (dict(), dict(nonce="x"), dict(ahora=T + 999), dict(arranque=T + 100)):
        kw = dict(por_ep=False, **caso)
        assert leer(B, r, **kw) == leer(ORIG, r, **kw) if False else B.leer_permiso(r, kw.get("nonce", "corrida-2"), kw.get("arranque", T - 10), kw.get("ahora", T + 5)) == \
            ORIG.leer_permiso(r, kw.get("nonce", "corrida-2"), kw.get("arranque", T - 10), kw.get("ahora", T + 5))


def test_corrida_real_con_permiso_viejo_del_mismo_episodio_no_lanza_nada(tmp_path):
    """Generador completo, una ejecución nueva (nonce nuevo) con un permiso de la corrida anterior para el MISMO primer episodio."""
    g = cargar("generar_campana_b")
    g.esq.validar = lambda cfg, exigir_herramientas=False: []
    g.esq.comando_de = lambda cfg, s: ["true"]
    lanzados = []
    g.correr_episodio = lambda *a, **k: lanzados.append(1) or "completo"
    cfg = {"semilla": 1, "repeticiones": 1, "escenarios": [{"id": "e", "habilitado": True, "destino": "x", "servicio": "y", "timeout_s": 1}],
           "tiempos_s": {"calentamiento_inicial": 0, "contexto_antes": 0, "observacion_despues": 0}}
    (tmp_path / "c.json").write_text(json.dumps(cfg))
    ahora = time.time()
    permiso(tmp_path, nonce="corrida-ANTERIOR", episodio="e-r1", emitido_epoch=ahora, valido_hasta_epoch=ahora + 3600)
    rc = g.main(["--config", str(tmp_path / "c.json"), "--salida-dir", str(tmp_path / "o"), "--autorizado", "--permiso", str(tmp_path / "permiso.json"),
                 "--nonce", "corrida-NUEVA", "--permiso-por-episodio", "--permiso-sondeo", "0.05", "--permiso-max-espera", "0.5"])
    assert rc == 3 and not lanzados                                   # cancelada por falta de permiso válido; no se lanzó el episodio
    marcas = [json.loads(l) for l in (tmp_path / "o" / "marcas.jsonl").read_text().splitlines()]
    assert any(m["evento"] == "pausa" and "otra corrida" in m["motivo"] for m in marcas)


def test_hashes_documentados():
    h = lambda n: hashlib.sha256((GEN / n).read_bytes()).hexdigest()
    assert h("generar_campana_original.py").startswith("99e6bdae1f76b873")      # el firmado de A
    assert h("esquema_campana.py").startswith("45f743d2ef35f769")                 # el de scripts-4c
