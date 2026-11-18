"""Integración de D5 sin reinicio en la COPIA de banco de `d5_episodio.py` (decisión E, solo banco): publicador real como proceso, adaptador
aislado, srv-dmz y agente SINTÉTICOS (ayudante nft simulado), sin orquestador. El original se monta de solo lectura en /herramientas."""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HERR = Path(os.environ.get("CF_HERRAMIENTAS", "/herramientas"))
if not (HERR / "d5_episodio.py").exists():
    pytest.skip("herramientas de la Campaña B no montadas", allow_module_level=True)
import adaptador_banco as ab  # noqa: E402
import adaptador_banco_rot as abr  # noqa: E402
import hacer_d5_episodio_banco as hd  # noqa: E402
from test_flujo_completo import K, OTRA, PREFIJO, Pub, decision, derivado  # noqa: E402,F401


@pytest.fixture(scope="module")
def banco():
    d = Path(tempfile.mkdtemp(prefix="d5ep_"))
    assert hd.main(str(HERR / "d5_episodio.py"), str(d / "d5_episodio_banco.py")) == 0
    spec = importlib.util.spec_from_file_location("d5_episodio_banco", d / "d5_episodio_banco.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["d5_episodio_banco"] = m
    spec.loader.exec_module(m)
    m._fuente = d / "d5_episodio_banco.py"
    return m


@pytest.fixture
def llamadas(monkeypatch):
    n = []
    orig = ab.cli.solicitar_reset
    monkeypatch.setattr(ab.cli, "solicitar_reset", lambda *a, **k: (n.append(1), orig(*a, **k))[1])
    return n


class NftSimulado:
    """Ayudante de nftables SINTÉTICO (mismo contrato JSON que cf-nft-helper para listar/retirar_origen)."""

    def __init__(self):
        self.sets = {"bloqueados": {}, "limitados": {}}
        self.llamadas = []

    def __call__(self, peticion):
        op = peticion["operaciones"][0]
        self.llamadas.append(op["op"])
        if op["op"] == "listar":
            return {"ok": True, "estado": {"sets": {k: dict(v) for k, v in self.sets.items()}, "descartes_limite": {}}}
        if op["op"] == "retirar_origen":
            for v in self.sets.values():
                v.pop(op["ip"], None)
            return {"ok": True}
        return {"ok": False, "rechazo": "op_no_soportada"}


def montar(banco, pub, nft=None, auditoria=True, esperar_s=10.0, real=True):
    nft = nft if nft is not None else NftSimulado()
    traza = pub.tmp / "agente-traza.jsonl"
    traza.write_text("")
    ad = abr.AdaptadorBancoRot(pub.ctl, pub.tmp / "feed.json", pub.tmp / "estado.json", pub.tmp / "traza.jsonl",
                               (pub.tmp / "d5-auditoria.jsonl") if auditoria else None, esperar_s=esperar_s)
    rn = banco.RunnersBanco(ad, pub.tmp / "feed.json", traza, nft, real=real)
    pu = banco.PuertaBanco(rn, registro=pub.tmp / "puerta-banco.jsonl", espera_agente=2.0, espera_feed=6.0, sondeo=0.1)
    return pu, rn, nft


def nombres(res):
    return [p["paso"] for p in res["historial"][0]["pasos"]]


def reg(pub):
    return [x["evento"] for x in ab._jsonl(pub.tmp / "puerta-banco.jsonl")]


def test_el_cambio_a_la_copia_es_pequeno_y_el_original_no_se_toca(banco):
    import difflib
    a = (HERR / "d5_episodio.py").read_text(encoding="utf-8").splitlines()
    b = banco._fuente.read_text(encoding="utf-8").splitlines()
    quitadas = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] == "-" and l[:3] != "---"]
    assert len(quitadas) == 2                                                   # solo la línea del docstring y la de t_limpio
    assert hashlib.sha256((HERR / "d5_episodio.py").read_bytes()).hexdigest()   # original legible, no modificado (montado en solo lectura)


def test_flujo_completo_acuse_valido_deja_continuar_sin_reiniciar_y_conserva_las_demas_entidades(banco, derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        e0 = p.estado()
        pu, rn, nft = montar(banco, p)
        res = pu.preparar_episodio()
        assert res["lista"] is True and not res["bloqueada"] and len(llamadas) == 1
        assert nombres(res) == ["limpiar", "feed_tras_limpiar", "nft_antes", "nft_despues", "agente", "feed_final"]
        lim = res["historial"][0]["pasos"][0]
        assert lim["ok"] and lim["acuse"] and lim["hay_que_quitar"] and len(lim["quitado"]["vigentes"]) == 1 and lim["secuencia"] > 0
        assert p.vivo() and K not in p.ips() and {OTRA, PREFIJO} <= p.ips()          # sin reinicio; la Kali limpia; las demás entidades siguen
        e1 = p.estado()
        for ip in (OTRA, PREFIJO):
            assert [v for k, v in e1["vigentes"].items() if k.startswith(ip + "|")] == [v for k, v in e0["vigentes"].items() if k.startswith(ip + "|")]
        a = ab._jsonl(p.tmp / "d5-auditoria.jsonl")
        assert [x["evento"] for x in a] == ["consumido", "publicado"]
        assert reg(p) == ["puerta_lista"]
    finally:
        p.cierra()


def test_si_la_kali_esta_en_el_set_la_puerta_la_retira_y_verifica_antes_de_continuar(banco, derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        nft = NftSimulado()
        nft.sets["limitados"][K] = {"id": "abc"}
        pu, rn, _ = montar(banco, p, nft)
        res = pu.preparar_episodio()
        assert res["lista"] and nombres(res) == ["limpiar", "feed_tras_limpiar", "nft_antes", "retirar", "nft_despues", "agente", "feed_final"]
        assert K not in nft.sets["limitados"] and "retirar_origen" in nft.llamadas
    finally:
        p.cierra()


def test_acuse_no_escribible_bloquea_la_puerta_y_las_llamadas_siguientes_conservan_la_evidencia_sin_solicitar(banco, derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        os.mkdir(str(p.ctl) + ".ack")
        pu, rn, _ = montar(banco, p, esperar_s=2.0)
        r1 = pu.preparar_episodio()
        assert r1["lista"] is False and r1["bloqueada"] is True and len(llamadas) == 1
        lim = r1["historial"][0]["pasos"][0]
        assert lim["paso"] == "limpiar" and not lim["ok"] and lim["publicacion"] == "confirmada" and Path(lim["evidencia"]).exists() and Path(lim["traza_auditoria"]).is_dir()
        sigs = [pu.preparar_episodio() for _ in range(2)] + [pu.una_vez() for _ in range(2)]
        for s in sigs:
            r = s["historial"][0] if "historial" in s else s
            assert r["lista"] is False and r["bloqueada"] is True and r["pasos"] == []
        assert len(llamadas) == 1 and pu.omitidas == 4 and pu.intentos_de_puerta == 1       # 4 llamadas sin solicitud
        assert pu.bloqueada["pasos"][0]["evidencia"] == lim["evidencia"] and Path(lim["evidencia"]).exists()    # la evidencia no se tocó
        assert not p.ctl.exists() and len([x for x in ab._jsonl(p.tmp / "d5-auditoria.jsonl") if x["evento"] == "consumido"]) == 1
        assert p.vivo()
        assert reg(p) == ["puerta_bloqueada"] + ["omitida_por_puerta_bloqueada"] * 4
    finally:
        p.cierra()


def test_resultado_incierto_tambien_bloquea_y_se_conserva_como_fallido(banco, derivado, tmp_path, llamadas):
    (tmp_path / "d5-auditoria.jsonl").mkdir()                                                # la auditoría no se puede escribir
    p = Pub(derivado, tmp_path)
    try:
        os.mkdir(str(p.ctl) + ".ack")
        pu, rn, _ = montar(banco, p, esperar_s=2.0)
        r = pu.preparar_episodio()
        lim = r["historial"][0]["pasos"][0]
        assert not r["lista"] and r["bloqueada"] and lim["incierto"] is True and lim["publicacion"] == "publicación sin confirmar" and Path(lim["evidencia"]).exists()
        pu.una_vez()
        assert len(llamadas) == 1 and not p.ctl.exists() and p.vivo()
    finally:
        p.cierra()


def test_una_decision_nueva_tras_la_limpieza_falla_la_puerta_y_queda_bloqueada_sin_reintento_automatico(banco, derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        pu, rn, _ = montar(banco, p)
        orig = rn.sensor

        def con_decision_nueva(cmd, **kw):                                                   # patrón del Hallazgo 2: llega una decisión sobre la Kali justo tras limpiar
            r = orig(cmd, **kw)
            if cmd == "limpiar" and r["ok"]:
                with open(p.log, "a") as fh:
                    fh.write(json.dumps(decision(K, "brute_force", "BLOCK", 555)) + "\n")
            return r
        rn.sensor = con_decision_nueva
        r = pu.preparar_episodio()
        mot = " ".join(r["historial"][0]["motivos"])
        assert not r["lista"] and r["bloqueada"] and ("propuesta heredada" in mot or "feed final no es nuevo, vigente y limpio" in mot)   # la entrada de la Kali reaparece en el feed
        assert len(llamadas) == 1                                                            # antes, la puerta repetía la limpieza; ahora espera una decisión manual
        pu.preparar_episodio()
        assert len(llamadas) == 1
    finally:
        p.cierra()


def test_la_reanudacion_exige_decision_manual_registrada_y_entonces_se_emite_una_sola_solicitud_nueva(banco, derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        os.mkdir(str(p.ctl) + ".ack")
        pu, rn, _ = montar(banco, p, esperar_s=2.0)
        pu.preparar_episodio()
        pu.preparar_episodio()
        assert len(llamadas) == 1
        for quien, motivo in (("", "x"), ("Mark", ""), ("  ", "  ")):
            with pytest.raises(ValueError):
                pu.reanudar_manual(quien, motivo)
        assert pu.bloqueada is not None and len(llamadas) == 1                              # una reanudación inválida no desbloquea
        os.rmdir(str(p.ctl) + ".ack")                                                        # se corrige la causa
        pu.reanudar_manual("Mark (prueba de banco)", "acuse restablecido tras corregir el destino del acuse")
        rn.adaptador.esperar_s = 10.0
        r = pu.preparar_episodio()
        assert r["lista"] is True and len(llamadas) == 2 and pu.bloqueada is None
        assert reg(p) == ["puerta_bloqueada", "omitida_por_puerta_bloqueada", "reanudacion_manual", "puerta_lista"]
        rm = [x for x in ab._jsonl(p.tmp / "puerta-banco.jsonl") if x["evento"] == "reanudacion_manual"][0]
        assert rm["por"] == "Mark (prueba de banco)" and "acuse" in rm["motivo"]
    finally:
        p.cierra()


def test_la_frescura_del_feed_se_mide_desde_la_solicitud_no_desde_el_retorno(banco, derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        pu, rn, _ = montar(banco, p)
        vistos, orig = {}, rn.sensor

        def espia(cmd, **kw):
            r = orig(cmd, **kw)
            if cmd == "limpiar":
                vistos["limpiar"] = r
            if cmd == "feed" and "desde_1" not in vistos:
                vistos["desde_1"] = kw["desde"]
                vistos["feed_1"] = r
            return r
        rn.sensor = espia
        assert pu.preparar_episodio()["lista"]
        # sin reinicio el publicador republica ANTES de acusar: el feed «nuevo» es posterior a la solicitud pero anterior al retorno
        assert vistos["desde_1"] == vistos["limpiar"]["t_limpio"] and vistos["limpiar"]["t_limpio"] <= vistos["limpiar"]["t"]
        assert vistos["feed_1"]["fresco"] and vistos["feed_1"]["limpio"]
    finally:
        p.cierra()


def test_modo_seco_no_emite_solicitud(banco, derivado, tmp_path, llamadas):
    p = Pub(derivado, tmp_path)
    try:
        pu, rn, _ = montar(banco, p, real=False)
        r = rn.sensor("limpiar", origen=K)
        assert r["ok"] and r["modo"] == "seco" and len(llamadas) == 0 and K in p.ips()
        assert rn.sensor("limpiar", origen="10.10.20.99")["ok"] is False                      # solo admite el origen del experimento
    finally:
        p.cierra()
