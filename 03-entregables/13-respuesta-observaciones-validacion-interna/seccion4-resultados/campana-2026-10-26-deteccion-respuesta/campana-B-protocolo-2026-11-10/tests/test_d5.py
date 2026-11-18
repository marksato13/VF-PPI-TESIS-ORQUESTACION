"""Limpieza D5 por episodio en banco: publicador, relé/agente y nftables simulados sobre ficheros temporales."""
import copy
import hashlib
import json
import os
import signal
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas"))
import d5_episodio as d5  # noqa: E402

K, OTRA = "10.10.20.30", "10.10.20.99"


def entrada(ip, accion="BLOCK", hasta=5000.0):
    return {"ip": ip, "destino": "srv-dmz", "alcance": "todo", "accion": accion, "hasta": hasta, "id": "id-%s-%s" % (ip, accion)}


class Mundo:
    """Un publicador con su estado en disco, un feed, un agente con traza y un nftables, todos falsos."""

    def __init__(self, tmp, heredado=True, ignora_limpieza=False, agente_reaplica=False, helper_falla=False):
        self.t = 1000.0
        self.dir = tmp
        self.estado_p = tmp / "estado.json"
        self.feed_p = tmp / "feed.json"
        self.traza_p = tmp / "traza_agente.jsonl"
        self.aud = tmp / "d5-auditoria"
        self.registros = {n: tmp / n for n in ("traza.jsonl", "senales-if.jsonl", "via-rapida-resumen.jsonl")}
        for n, p in self.registros.items():
            p.write_text("registro de auditoría %s\n" % n)
        self.traza_p.write_text("")
        self.mem = {"secuencia": 7, "eventos": {"e1": {"tipo": "nueva", "hasta": 5000.0}},
                    "vigentes": ({"%s|srv-dmz|todo" % K: entrada(K), "%s|srv-dmz|todo" % OTRA: entrada(OTRA, "LIMIT")} if heredado else {}),
                    "escalada": {"%s@srv-dmz" % K: {"bloqueos": 3, "ultimo_visto": 900.0}, "%s@dc1" % K: {"bloqueos": 0, "ultimo_visto": 900.0},
                                 "%s@srv-dmz" % OTRA: {"bloqueos": 1, "ultimo_visto": 900.0}}}
        self.congelado = False
        self.ignora_limpieza, self.agente_reaplica, self.helper_falla = ignora_limpieza, agente_reaplica, helper_falla
        self.nft = {"bloqueados": {K: {}} if heredado else {}, "limitados": {}}
        self.llamadas_helper = []
        self.guardar()
        self.publicar()

    # publicador
    def guardar(self):
        self.estado_p.write_text(json.dumps(self.mem, sort_keys=True))

    def publicar(self):
        self.mem["secuencia"] += 1
        vig = [e for e in self.mem["vigentes"].values() if e["hasta"] > self.t]
        self.feed_p.write_text(json.dumps({"secuencia": self.mem["secuencia"], "generado": self.t, "expira": self.t + 60, "entradas": vig}))

    def senal(self, pid, sig):
        if sig == signal.SIGSTOP:
            self.congelado = True
        elif sig == signal.SIGKILL:
            if not self.congelado:
                self.guardar()                                  # un publicador en marcha escribe su estado viejo antes de morir
            self.congelado = False
            if not self.ignora_limpieza:                       # reinicio: relee su estado del disco
                self.mem = json.loads(self.estado_p.read_text())
            self.publicar()

    def tick(self, s):
        for _ in range(int(s)):
            self.t += 1
            if not self.congelado:
                if self.t % 20 == 0:
                    self.publicar()
                self.guardar()
            # agente: aplica lo que traiga el feed (si reaplica) y registra la traza
            if self.agente_reaplica:
                feed = json.loads(self.feed_p.read_text())
                for e in feed["entradas"]:
                    if e["ip"] == K and K not in self.nft["bloqueados"]:
                        self.nft["bloqueados"][K] = {}
                        with open(self.traza_p, "a") as fh:
                            fh.write(json.dumps({"evento": "aplicacion", "aplicado_en": self.t, "nuevos": [{"ip": K, "set": "bloqueados"}]}) + "\n")

    # helper de srv-dmz
    def helper(self, peticion):
        self.llamadas_helper.append(peticion)
        op = peticion["operaciones"][0]
        if self.helper_falla and op["op"] == "retirar_origen":
            return {"ok": False, "rechazo": "simulado"}
        if op["op"] == "listar":
            return {"ok": True, "estado": {"sets": {s: dict(v) for s, v in self.nft.items()}, "descartes_limite": {}}}
        for s in self.nft:
            self.nft[s].pop(op["ip"], None)
        return {"ok": True}


class Runners:
    def __init__(self, m):
        self.m = m

    def sensor(self, cmd, **kw):
        m = self.m
        if cmd == "limpiar":
            return d5.sensor_limpiar(m.estado_p, kw["origen"], m.aud, True, ahora=lambda: m.t, pid_de=lambda: 4242, senal=m.senal)
        return d5.sensor_feed(m.feed_p, kw["origen"], kw["desde"], ahora=lambda: m.t)

    def srv(self, cmd, **kw):
        m = self.m
        if cmd == "nft":
            return d5.srv_nft(kw["origen"], helper=m.helper)
        if cmd == "retirar":
            return d5.srv_retirar(kw["origen"], True, helper=m.helper)
        return d5.srv_agente(m.traza_p, kw["origen"], kw["desde"])


def puerta(m, **kw):
    return d5.Puerta(Runners(m), ahora=lambda: m.t, dormir=m.tick, **kw)


def sha_de(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ------------------------------------------------------------------ limpieza del estado
def test_limpia_solo_el_origen_y_conserva_el_resto():
    est = {"secuencia": 3, "eventos": {"e": {"hasta": 1}}, "vigentes": {"%s|srv-dmz|todo" % K: 1, "%s|dc1|dns" % K: 2, "%s|srv-dmz|todo" % OTRA: 3, "10.10.20.3|srv-dmz|todo": 5},
           "escalada": {"%s@srv-dmz" % K: 1, "%s@dc1" % K: 2, "%s@srv-dmz" % OTRA: 3, "10.10.20.3@srv-dmz": 4}}
    nuevo, q = d5.limpiar_estado(est, K)
    assert sorted(q["vigentes"]) == sorted(["%s|srv-dmz|todo" % K, "%s|dc1|dns" % K]) and len(q["escalada"]) == 2
    assert set(nuevo["vigentes"]) == {"%s|srv-dmz|todo" % OTRA, "10.10.20.3|srv-dmz|todo"} and set(nuevo["escalada"]) == {"%s@srv-dmz" % OTRA, "10.10.20.3@srv-dmz"}
    assert nuevo["eventos"] == est["eventos"] and nuevo["secuencia"] == 3          # no se toca lo demás
    assert est["escalada"]["%s@srv-dmz" % K] == 1                                   # la entrada no se muta


def test_limpiar_conserva_auditoria_y_deja_copia(tmp_path):
    m = Mundo(tmp_path)
    antes = {n: sha_de(p) for n, p in m.registros.items()}
    estado_antes = m.estado_p.read_bytes()
    r = Runners(m).sensor("limpiar", origen=K)
    assert r["ok"] and r["hay_que_quitar"] and len(r["quitado"]["vigentes"]) == 1
    assert {n: sha_de(p) for n, p in m.registros.items()} == antes                  # ni un byte de los registros
    (copia,) = [p for p in m.aud.iterdir() if p.name.startswith("estado-antes-")]
    assert copia.read_bytes() == estado_antes                                        # copia del estado anterior
    linea = json.loads((m.aud / "d5.jsonl").read_text())
    assert linea["sha_antes"] == hashlib.sha256(estado_antes).hexdigest() and linea["sha_despues"] == sha_de(m.estado_p)
    nuevo = json.loads(m.estado_p.read_text())
    assert OTRA in "".join(nuevo["vigentes"]) and K not in "".join(nuevo["vigentes"]) and "e1" in nuevo["eventos"]


def test_congelado_el_publicador_no_pisa_el_estado_limpio(tmp_path):
    """Sin SIGSTOP previo, el publicador volvería a escribir su estado viejo; congelado y matado, reinicia ya limpio."""
    m = Mundo(tmp_path)
    Runners(m).sensor("limpiar", origen=K)
    m.tick(30)
    assert K not in "".join(json.loads(m.estado_p.read_text())["vigentes"])


def test_seco_no_cambia_nada(tmp_path):
    m = Mundo(tmp_path)
    antes = m.estado_p.read_bytes()
    r = d5.sensor_limpiar(m.estado_p, K, m.aud, False, ahora=lambda: m.t)
    assert r["modo"] == "seco" and r["hay_que_quitar"] and m.estado_p.read_bytes() == antes and not m.aud.exists()


def test_estado_ilegible_o_servicio_parado_no_toca_nada(tmp_path):
    m = Mundo(tmp_path)
    m.estado_p.write_text("no es json")
    assert d5.sensor_limpiar(m.estado_p, K, m.aud, True)["rc"] == 2
    m2 = Mundo(tmp_path / "x") if (tmp_path / "x").mkdir() is None else None
    antes = m2.estado_p.read_bytes()
    r = d5.sensor_limpiar(m2.estado_p, K, m2.aud, True, pid_de=lambda: 0, senal=m2.senal)
    assert r["rc"] == 3 and m2.estado_p.read_bytes() == antes


def test_solo_admite_el_origen_del_experimento(capsys):
    assert d5.main(["srv-nft", "--origen", OTRA]) == 2
    assert "solo admite el origen del experimento" in capsys.readouterr().out


def test_feed_limpio_pero_viejo_no_es_fresco(tmp_path):
    m = Mundo(tmp_path, heredado=False)
    assert d5.sensor_feed(m.feed_p, K, m.t + 10, ahora=lambda: m.t)["fresco"] is False
    assert d5.sensor_feed(m.feed_p, K, m.t - 10, ahora=lambda: m.t)["fresco"] is True


def test_puerta_espera_si_la_propuesta_reaparece_al_final(tmp_path):
    m = Mundo(tmp_path)
    tick = m.tick

    def tick2(s):
        for _ in range(int(s)):
            tick(1)
            if m.t > 1030:                                    # el publicador la vuelve a proponer (p. ej. decisión rezagada)
                m.mem["vigentes"]["%s|srv-dmz|todo" % K] = entrada(K, hasta=m.t + 300)
    r = d5.Puerta(Runners(m), ahora=lambda: m.t, dormir=tick2).una_vez()
    assert not r["lista"] and any("feed final" in x for x in r["motivos"])


# ------------------------------------------------------------------ puerta
def test_puerta_pasa_con_estado_heredado_en_publicador_y_nftables(tmp_path):
    m = Mundo(tmp_path)
    r = puerta(m).una_vez()
    assert r["lista"], r["motivos"]
    assert K not in m.nft["bloqueados"] and any(o["operaciones"][0]["op"] == "retirar_origen" for o in m.llamadas_helper)
    pasos = [p["paso"] for p in r["pasos"]]
    assert pasos.index("limpiar") < pasos.index("feed_tras_limpiar") < pasos.index("retirar") < pasos.index("feed_final")
    assert json.loads(m.feed_p.read_text())["entradas"] and all(e["ip"] != K for e in json.loads(m.feed_p.read_text())["entradas"])


def test_puerta_sin_nada_que_limpiar_no_llama_a_retirar(tmp_path):
    m = Mundo(tmp_path, heredado=False)
    r = puerta(m).una_vez()
    assert r["lista"] and not any(o["operaciones"][0]["op"] == "retirar_origen" for o in m.llamadas_helper)


def test_puerta_espera_si_la_propuesta_heredada_sigue_en_el_feed(tmp_path):
    m = Mundo(tmp_path, ignora_limpieza=True)               # carrera perdida: el publicador reinició con el estado viejo
    r = puerta(m, espera_feed=10).una_vez()
    assert not r["lista"] and "propuesta heredada" in r["motivos"][0]
    assert not any(p["paso"] == "nft_antes" for p in r["pasos"])      # ni se mira nftables con un feed sucio


def test_puerta_espera_si_el_agente_la_vuelve_a_aplicar(tmp_path):
    m = Mundo(tmp_path, agente_reaplica=True)
    m.mem["vigentes"]["%s|srv-dmz|todo" % K]["hasta"] = 5000.0
    # el agente aún tiene cacheado un feed viejo con la entrada: la reaplica tras la retirada
    orig = m.helper

    def helper(p):
        r = orig(p)
        if p["operaciones"][0]["op"] == "retirar_origen":
            m.nft["bloqueados"][K] = {}
            m.agente_reaplica = False
            with open(m.traza_p, "a") as fh:
                fh.write(json.dumps({"evento": "aplicacion", "aplicado_en": m.t + 3, "nuevos": [{"ip": K, "set": "bloqueados"}]}) + "\n")
        return r
    m.helper = helper
    r = puerta(m).una_vez()
    assert not r["lista"] and any("volvió a aplicar" in x for x in r["motivos"]) and any("nftables aún contiene" in x for x in r["motivos"])


def test_aplicaciones_anteriores_a_la_retirada_no_cuentan(tmp_path):
    m = Mundo(tmp_path)
    m.traza_p.write_text(json.dumps({"evento": "aplicacion", "aplicado_en": 500.0, "nuevos": [{"ip": K}]}) + "\n"
                         + json.dumps({"evento": "aplicacion", "aplicado_en": 2000.0, "nuevos": [{"ip": OTRA}]}) + "\n")
    assert puerta(m).una_vez()["lista"]


def test_retirar_en_seco_no_llama_al_helper_para_cambiar(tmp_path):
    m = Mundo(tmp_path)
    r = d5.srv_retirar(K, False, helper=m.helper)
    assert r["seco"] and r["habria_retirado_de"] == ["bloqueados"]
    assert all(o["operaciones"][0]["op"] == "listar" for o in m.llamadas_helper) and K in m.nft["bloqueados"]


def test_feed_vencido_no_vale(tmp_path):
    m = Mundo(tmp_path, heredado=False)
    m.t += 500                                                # nadie lo refrescó: expiró
    r = d5.sensor_feed(m.feed_p, K, 0, ahora=lambda: m.t)
    assert r["limpio"] and not r["vigente"]


def test_puerta_espera_si_retirar_origen_falla(tmp_path):
    r = puerta(Mundo(tmp_path, helper_falla=True)).una_vez()
    assert not r["lista"] and "retirar_origen falló" in r["motivos"][0]


def test_puerta_un_feed_viejo_no_vale(tmp_path):
    m = Mundo(tmp_path)
    m.publicar_orig = m.publicar
    m.publicar = lambda: None                                 # el publicador no refresca: el feed queda del instante anterior
    m.senal = lambda pid, sig: None                           # y la limpieza ni siquiera lo reinicia
    r = d5.Puerta(Runners(m), ahora=lambda: m.t, dormir=m.tick, espera_feed=6).una_vez()
    assert not r["lista"]


def test_preparar_episodio_reintenta_y_luego_no_inicia(tmp_path):
    m = Mundo(tmp_path, ignora_limpieza=True)
    res = puerta(m, espera_feed=4).preparar_episodio(intentos=3, espera_entre=5, auditoria=tmp_path / "puertas.jsonl")
    assert not res["lista"] and res["intentos"] == 3
    assert len((tmp_path / "puertas.jsonl").read_text().splitlines()) == 3        # cada intento queda registrado


def test_preparar_episodio_se_recupera_en_el_segundo_intento(tmp_path):
    m = Mundo(tmp_path, ignora_limpieza=True)
    orig_dormir = m.tick
    cuenta = {"n": 0}

    def dormir(s):
        orig_dormir(s)
        cuenta["n"] += 1
        if s == 5:                                            # entre intentos, la carrera deja de perderse
            m.ignora_limpieza = False
    p = d5.Puerta(Runners(m), ahora=lambda: m.t, dormir=dormir, espera_feed=25)   # > un refresco de 20 s
    res = p.preparar_episodio(intentos=3, espera_entre=5)
    assert res["lista"] and res["intentos"] == 2
