"""Integración del D5 CORREGIDO en la variante exacta que usará el lanzador (`d5_episodio_banco.py` derivado por `hacer_d5_episodio_banco.py` del corregido, que el banco monta
como /herramientas/d5_episodio.py): publicador derivado como PROCESO real, adaptador aislado, srv-dmz y agente SINTÉTICOS con el JSON/contrato real del helper (incluido el
contador `descartes_limite`). Comprueba: limpieza sin reiniciar el publicador, residual registrado y conservado, y que la puerta SIGUE bloqueando ante restricción activa,
reaplicación o estado ilegible. Se ejecuta con CF_HERRAMIENTAS=/herramientas (corregido) y las pruebas de `d5-sin-reinicio` en la ruta de módulos."""
import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "d5-sin-reinicio"))
sys.path.insert(0, str(AQUI))
import test_integracion_d5 as TI  # noqa: E402  (fixtures banco/derivado/llamadas y montar())
from test_integracion_d5 import banco, derivado, llamadas, montar, nombres, reg, ab, K, OTRA, PREFIJO  # noqa: E402,F401

RESIDUAL = {K: {"bytes": 5546, "expira_s": 3248, "id": None, "paquetes": 74}}      # el contador real del episodio 6 (B3)


class NftResidual:
    """Contrato del helper real: listar -> sets + descartes_limite; retirar_origen SOLO limpia los sets de aplicación (nunca el contador)."""

    def __init__(self, limitados=False, bloqueados=False, residual=True, retirar_efectivo=True, listar_ilegible_desde=None, listar_falla_desde=None):
        self.sets = {"bloqueados": {K: {"id": "b"}} if bloqueados else {}, "limitados": {K: {"id": "l"}} if limitados else {}}
        self.descartes = {i: dict(v) for i, v in RESIDUAL.items()} if residual else {}
        self.llamadas, self.n_listar = [], 0
        self.retirar_efectivo, self.ilegible_desde, self.falla_desde = retirar_efectivo, listar_ilegible_desde, listar_falla_desde
        self.reaplicar = None                                  # callback tras retirar_origen (simula al agente)

    def __call__(self, peticion):
        op = peticion["operaciones"][0]
        self.llamadas.append(op["op"])
        if op["op"] == "listar":
            self.n_listar += 1
            if self.falla_desde and self.n_listar >= self.falla_desde:
                return {"ok": False, "rechazo": "simulado"}
            if self.ilegible_desde and self.n_listar >= self.ilegible_desde:
                return {"ok": True, "estado": {"sets": {}, "descartes_limite": {}}}
            return {"ok": True, "estado": {"sets": {k: dict(v) for k, v in self.sets.items()}, "descartes_limite": {i: dict(v) for i, v in self.descartes.items()}, "reglas": []}}
        if op["op"] == "retirar_origen":
            if self.retirar_efectivo:
                for v in self.sets.values():
                    v.pop(op["ip"], None)
            if self.reaplicar:
                self.reaplicar(self)
            return {"ok": True}
        return {"ok": False, "rechazo": "op_no_soportada"}


def test_episodio_6_residual_la_puerta_pasa_sin_reiniciar_y_registra_el_contador(banco, derivado, tmp_path, llamadas):
    p = TI.Pub(derivado, tmp_path)
    try:
        nft = NftResidual(limitados=True)
        pu, rn, _ = montar(banco, p, nft)
        res = pu.preparar_episodio()
        assert res["lista"] is True and not res["bloqueada"] and len(llamadas) == 1                      # una sola solicitud real
        assert nombres(res) == ["limpiar", "feed_tras_limpiar", "nft_antes", "retirar", "nft_despues", "agente", "feed_final"]
        pasos = {x["paso"]: x for x in res["historial"][0]["pasos"]}
        assert pasos["nft_antes"]["donde"] == ["limitados"] and pasos["nft_despues"]["donde"] == [] and pasos["nft_despues"]["presente"] is False
        assert pasos["nft_despues"]["residual"] == {"descartes_limite": RESIDUAL[K]}                       # registrado en el paso…
        assert res["historial"][0]["residual_conservado"] == {"descartes_limite": RESIDUAL[K]}             # …y en el resultado
        assert nft.descartes == RESIDUAL and nft.llamadas.count("retirar_origen") == 1                      # el contador NO se tocó
        assert p.vivo() and K not in p.ips() and {OTRA, PREFIJO} <= p.ips()                                # sin reiniciar el publicador; demás entidades intactas
        assert [x["evento"] for x in ab._jsonl(p.tmp / "d5-auditoria.jsonl")] == ["consumido", "publicado"]
        assert reg(p) == ["puerta_lista"]
    finally:
        p.cierra()


def test_el_contador_residual_queda_en_la_evidencia_de_puertas_d5_jsonl(banco, derivado, tmp_path, llamadas):
    p = TI.Pub(derivado, tmp_path)
    try:
        pu, rn, _ = montar(banco, p, NftResidual(limitados=True))
        aud = tmp_path / "puertas-D5.jsonl"
        pu.preparar_episodio(auditoria=str(aud))
        linea = json.loads(aud.read_text().splitlines()[-1])
        assert linea["lista"] is True and linea["residual_conservado"] == {"descartes_limite": RESIDUAL[K]}
        assert any(x.get("residual") for x in linea["pasos"] if x["paso"] in ("nft_antes", "nft_despues"))
    finally:
        p.cierra()


def test_restriccion_activa_que_no_se_retira_bloquea_y_las_llamadas_siguientes_no_solicitan(banco, derivado, tmp_path, llamadas):
    p = TI.Pub(derivado, tmp_path)
    try:
        nft = NftResidual(limitados=True, retirar_efectivo=False)
        pu, rn, _ = montar(banco, p, nft)
        r1 = pu.preparar_episodio()
        assert r1["lista"] is False and r1["bloqueada"] and any("limitados" in m for m in r1["historial"][0]["motivos"])
        r2 = pu.preparar_episodio()
        assert r2["lista"] is False and len(llamadas) == 1                                                  # no se emite otra solicitud
        assert p.vivo()
    finally:
        p.cierra()


def test_restriccion_en_bloqueados_tambien_bloquea(banco, derivado, tmp_path, llamadas):
    p = TI.Pub(derivado, tmp_path)
    try:
        pu, rn, _ = montar(banco, p, NftResidual(bloqueados=True, retirar_efectivo=False))
        r = pu.preparar_episodio()
        assert r["lista"] is False and any("bloqueados" in m for m in r["historial"][0]["motivos"])
    finally:
        p.cierra()


def test_reaplicacion_tras_la_limpieza_bloquea(banco, derivado, tmp_path, llamadas):
    p = TI.Pub(derivado, tmp_path)
    try:
        nft = NftResidual(limitados=True)
        traza = p.tmp / "agente-traza.jsonl"

        def reaplicar(n):
            def tarea():
                time.sleep(0.4)
                n.sets["limitados"][K] = {"id": "re"}
                with open(traza, "a") as fh:
                    fh.write(json.dumps({"evento": "aplicacion", "aplicado_en": time.time(), "nuevos": [{"ip": K, "set": "limitados"}]}) + "\n")
            threading.Thread(target=tarea, daemon=True).start()
        nft.reaplicar = reaplicar
        pu, rn, _ = montar(banco, p, nft)
        r = pu.preparar_episodio()
        assert r["lista"] is False and r["bloqueada"]
        motivos = " ".join(r["historial"][0]["motivos"])
        assert "limitados" in motivos or "volvió a aplicar" in motivos
    finally:
        p.cierra()


@pytest.mark.parametrize("kw,esperado", [({"listar_falla_desde": 3}, "no se pudo leer"), ({"listar_ilegible_desde": 3}, "no se pudo leer")])
def test_estado_ilegible_en_la_lectura_posterior_bloquea(banco, derivado, tmp_path, llamadas, kw, esperado):
    p = TI.Pub(derivado, tmp_path)
    try:
        pu, rn, _ = montar(banco, p, NftResidual(limitados=True, **kw))                       # 1.ª lectura = nft_antes, 2.ª = srv_retirar, 3.ª = nft_despues
        r = pu.preparar_episodio()
        assert r["lista"] is False and r["bloqueada"] and any(esperado in m for m in r["historial"][0]["motivos"])
    finally:
        p.cierra()


def test_estado_ilegible_desde_el_principio_bloquea_sin_retirar(banco, derivado, tmp_path, llamadas):
    p = TI.Pub(derivado, tmp_path)
    try:
        nft = NftResidual(limitados=True, listar_ilegible_desde=1)
        pu, rn, _ = montar(banco, p, nft)
        r = pu.preparar_episodio()
        assert r["lista"] is False and r["bloqueada"] and "retirar_origen" not in nft.llamadas
    finally:
        p.cierra()
