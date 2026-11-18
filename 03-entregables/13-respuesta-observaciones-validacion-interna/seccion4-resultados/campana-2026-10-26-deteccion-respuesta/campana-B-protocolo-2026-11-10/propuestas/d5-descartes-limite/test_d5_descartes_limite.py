"""Banco: D5 distingue los sets de aplicación del contador `descartes_limite`. Reproduce el estado del episodio 6 de la corrida B3 (11-nov-2026): sets vacíos y
contador residual de 10.10.20.30 (74 paquetes, 5.546 B), con el JSON REAL que devolvió el helper de srv-dmz. Control: el D5 desplegado (herramientas\\d5_episodio.py)
bloquea en ese estado; el corregido pasa y conserva el contador. Y sigue bloqueando con una restricción activa o si el estado no se puede verificar."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
HERR = AQUI.parent.parent / "herramientas"
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(HERR))
import d5_episodio as VIEJO  # noqa: E402  (el desplegado en B2/B3)
import d5_episodio_corregido as NUEVO  # noqa: E402
sys.path.insert(0, str(AQUI.parent.parent / "tests"))
import test_d5 as T  # noqa: E402  (Mundo/Runners del banco)

K, OTRA = T.K, T.OTRA
# JSON REAL de `listar` del helper de srv-dmz a las 06:03Z (EVIDENCIA-ANTES-REVERSION…/listar-antes.json), tras el episodio 6 y la retirada de D5
LISTAR_EP6 = json.loads("""{"estado": {"descartes_limite": {"10.10.20.30": {"bytes": 5546, "expira_s": 3248, "id": null, "paquetes": 74}},
 "reglas": [{"contador": {"bytes": 9360, "packets": 156}, "handle": 6}, {"contador": {"bytes": 458956, "packets": 6041}, "handle": 7}],
 "sets": {"bloqueados": {}, "limitados": {}}}, "ok": true, "perfil": "dmz"}""")
MODULOS = [NUEVO]


def cargar_derivado():
    """El derivado de banco (`hacer_d5_episodio_banco.py`) del d5 corregido: la corrección sobrevive a la derivación."""
    sys.path.insert(0, str(AQUI.parent / "d5-sin-reinicio"))
    spec = importlib.util.spec_from_file_location("hdb", str(AQUI.parent / "d5-sin-reinicio" / "hacer_d5_episodio_banco.py"))
    return spec


class MundoDesc(T.Mundo):
    """Como Mundo, pero `listar` devuelve el contador `descartes_limite` y `retirar_origen` solo limpia los sets (como el helper real, línea 60/216)."""

    def __init__(self, tmp, descartes=None, nft=None, **kw):
        super().__init__(tmp, heredado=False, **kw)
        self.descartes = dict(descartes if descartes is not None else {})
        if nft is not None:
            self.nft = nft
        self.retirar_sin_efecto = False

    def helper(self, peticion):
        self.llamadas_helper.append(peticion)
        op = peticion["operaciones"][0]
        if op["op"] == "listar":
            return {"ok": True, "estado": {"sets": {s: dict(v) for s, v in self.nft.items()}, "descartes_limite": {i: dict(v) for i, v in self.descartes.items()}, "reglas": []}}
        if self.retirar_sin_efecto:
            return {"ok": True}
        for s in self.nft:
            self.nft[s].pop(op["ip"], None)                    # SETS = (bloqueados, limitados); descartes_limite NO se toca
        return {"ok": True}


RESIDUAL_K = {K: {"bytes": 5546, "expira_s": 3248, "id": None, "paquetes": 74}}


def puerta(mod, m):
    class R(T.Runners):
        def srv(self, cmd, **kw):
            if cmd == "nft":
                return mod.srv_nft(kw["origen"], helper=m.helper)
            if cmd == "retirar":
                return mod.srv_retirar(kw["origen"], True, helper=m.helper)
            return mod.srv_agente(m.traza_p, kw["origen"], kw["desde"])

        def sensor(self, cmd, **kw):
            if cmd == "limpiar":
                return mod.sensor_limpiar(m.estado_p, kw["origen"], m.aud, True, ahora=lambda: m.t, pid_de=lambda: 4242, senal=m.senal)
            return mod.sensor_feed(m.feed_p, kw["origen"], kw["desde"], ahora=lambda: m.t)
    return mod.Puerta(R(m), ahora=lambda: m.t, dormir=m.tick)


# ------------------------------------------------------------------ srv_nft con el JSON real del episodio 6
def test_el_d5_desplegado_cuenta_el_contador_como_presente_defecto_reproducido():
    r = VIEJO.srv_nft(K, helper=lambda p: LISTAR_EP6)
    assert r["presente"] is True and r["donde"] == ["descartes_limite"]


def test_el_corregido_distingue_sets_de_aplicacion_y_conserva_el_contador():
    r = NUEVO.srv_nft(K, helper=lambda p: LISTAR_EP6)
    assert r["ok"] and r["presente"] is False and r["donde"] == []
    assert r["residual"] == {"descartes_limite": {"bytes": 5546, "expira_s": 3248, "id": None, "paquetes": 74}}


def test_el_contador_de_otra_ip_no_se_atribuye_al_origen():
    lst = json.loads(json.dumps(LISTAR_EP6))
    lst["estado"]["descartes_limite"] = {OTRA: {"paquetes": 5, "bytes": 1, "expira_s": 1, "id": None}}
    r = NUEVO.srv_nft(K, helper=lambda p: lst)
    assert r["ok"] and not r["presente"] and r["residual"] == {}


# ------------------------------------------------------------------ puerta completa: estado del episodio 6
def estado_ep6(tmp_path, **kw):
    """Antes de la puerta: la Kali en `limitados` (regla del episodio) Y con contador residual; el publicador con la señal heredada."""
    m = MundoDesc(tmp_path, descartes=RESIDUAL_K, nft={"bloqueados": {}, "limitados": {K: {}}}, **kw)
    m.mem["vigentes"] = {"%s|srv-dmz|todo" % K: T.entrada(K, "LIMIT")}
    m.mem["escalada"] = {"%s@srv-dmz" % K: {"bloqueos": 0, "ultimo_visto": 900.0}}
    m.guardar()
    m.publicar()
    return m


def test_puerta_en_el_estado_del_episodio_6_con_el_d5_desplegado_se_bloquea(tmp_path):
    m = estado_ep6(tmp_path)
    r = puerta(VIEJO, m).una_vez()
    assert r["lista"] is False and any("descartes_limite" in x for x in r["motivos"])          # reproduce el bloqueo real de las 05:56:55Z


def test_puerta_corregida_pasa_en_el_estado_del_episodio_6_y_conserva_el_contador(tmp_path):
    m = estado_ep6(tmp_path)
    r = puerta(NUEVO, m).una_vez()
    assert r["lista"] is True and r["motivos"] == []
    pasos = {p["paso"]: p for p in r["pasos"]}
    assert pasos["nft_antes"]["presente"] is True and pasos["nft_antes"]["donde"] == ["limitados"]       # había regla en el set: se retira
    assert pasos["retirar"]["retirado"] is True
    assert pasos["nft_despues"]["presente"] is False and pasos["nft_despues"]["donde"] == []
    assert pasos["nft_despues"]["residual"] == {"descartes_limite": RESIDUAL_K[K]}                        # el contador queda como evidencia en el paso
    assert r["residual_conservado"] == {"descartes_limite": RESIDUAL_K[K]}
    assert m.descartes == RESIDUAL_K                                                                      # y NO se borró del nftables
    assert all(c["operaciones"][0]["op"] in ("listar", "retirar_origen") for c in m.llamadas_helper)      # ninguna operación toca el contador
    assert [c["operaciones"][0]["op"] for c in m.llamadas_helper].count("retirar_origen") == 1


def test_solo_el_contador_residual_sin_regla_activa_la_puerta_pasa_sin_retirar(tmp_path):
    m = MundoDesc(tmp_path, descartes=RESIDUAL_K, nft={"bloqueados": {}, "limitados": {}})
    r = puerta(NUEVO, m).una_vez()
    assert r["lista"] is True and r["residual_conservado"] == {"descartes_limite": RESIDUAL_K[K]}
    assert [c["operaciones"][0]["op"] for c in m.llamadas_helper].count("retirar_origen") == 0


# ------------------------------------------------------------------ SIGUE bloqueando
def test_restriccion_activa_que_no_se_retira_en_limitados_sigue_bloqueando(tmp_path):
    m = estado_ep6(tmp_path)
    m.retirar_sin_efecto = True                                  # el helper dice ok pero el origen sigue en limitados
    r = puerta(NUEVO, m).una_vez()
    assert r["lista"] is False and any("limitados" in x for x in r["motivos"])


def test_restriccion_activa_en_bloqueados_sigue_bloqueando(tmp_path):
    m = MundoDesc(tmp_path, descartes=RESIDUAL_K, nft={"bloqueados": {K: {}}, "limitados": {}})
    m.retirar_sin_efecto = True
    r = puerta(NUEVO, m).una_vez()
    assert r["lista"] is False and any("bloqueados" in x for x in r["motivos"])


def test_el_agente_que_reaplica_tras_la_limpieza_sigue_bloqueando(tmp_path):
    m = MundoDesc(tmp_path, descartes=RESIDUAL_K, nft={"bloqueados": {K: {}}, "limitados": {}}, agente_reaplica=True, ignora_limpieza=True)   # la limpieza no surte efecto: el feed aún trae al origen
    m.mem["vigentes"] = {"%s|srv-dmz|todo" % K: T.entrada(K)}
    m.guardar()
    m.publicar()
    r = puerta(NUEVO, m).una_vez()
    assert r["lista"] is False


def malo(mod_estado):
    return lambda p: mod_estado


@pytest.mark.parametrize("respuesta", [
    {"ok": False, "rechazo": "simulado"},                                                   # helper falla
    {"ok": True},                                                                           # sin estado
    {"ok": True, "estado": "texto"},                                                        # estado de tipo erróneo
    {"ok": True, "estado": {"sets": {}, "descartes_limite": {}}},                           # sets de aplicación ausentes
    {"ok": True, "estado": {"sets": {"bloqueados": {}}, "descartes_limite": {}}},           # falta limitados
    {"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": None}, "descartes_limite": {}}},   # set ilegible
    {"ok": True, "estado": {"descartes_limite": {}}},                                       # sin clave sets
    {"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": {}}, "descartes_limite": [1]}},    # contador mal formado
])
def test_si_el_estado_no_se_puede_verificar_srv_nft_falla_cerrado(respuesta):
    r = NUEVO.srv_nft(K, helper=malo(respuesta))
    assert r["ok"] is False and r["rc"] == 2


def test_puerta_no_pasa_si_la_lectura_posterior_a_la_retirada_falla(tmp_path):
    m = estado_ep6(tmp_path)
    original = m.helper
    estado = {"n": 0}

    def helper(p):
        if p["operaciones"][0]["op"] == "listar":
            estado["n"] += 1
            if estado["n"] >= 3:                                 # 1.ª = nft_antes, 2.ª = comprobación de srv_retirar, 3.ª = nft_despues: esa falla
                return {"ok": False, "rechazo": "simulado"}
        return original(p)
    m.helper = helper
    r = puerta(NUEVO, m).una_vez()
    assert r["lista"] is False and any("no se pudo leer" in x for x in r["motivos"])


def test_srv_estado_sin_cambios_ajena_en_descartes_no_cuenta_como_set():
    """srv_estado (P1) ya ignoraba el contador: se comprueba que la corrección no lo cambió."""
    lst = json.loads(json.dumps(LISTAR_EP6))
    assert VIEJO.srv_estado(K, helper=lambda p: lst, ahora=lambda: 1.0) == NUEVO.srv_estado(K, helper=lambda p: lst, ahora=lambda: 1.0)
    lst["estado"]["sets"]["limitados"] = {OTRA: {"id": "x"}}
    assert NUEVO.srv_estado(K, helper=lambda p: lst, ahora=lambda: 1.0)["rc"] == 1


def test_la_correccion_sobrevive_a_la_derivacion_de_banco(tmp_path):
    spec = cargar_derivado()
    assert os.path.exists(spec.origin)
    src = (AQUI.parent / "d5-sin-reinicio" / "hacer_d5_episodio_banco.py").read_text(encoding="utf-8")
    assert "def srv_nft" not in src or "descartes_limite" not in src.split("def srv_nft")[0]        # la derivación no reescribe srv_nft
    assert "SETS_APLICACION" in (AQUI / "d5_episodio_corregido.py").read_text(encoding="utf-8")
