"""Excepción de X3 acotada al NTP de la Kali (vigia_4c_b.py): qué exime y qué NO exime; el resto del vigía no cambia."""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest

GEN = Path(__file__).resolve().parent.parent / "generador"


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, GEN / (nombre + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = m
    spec.loader.exec_module(m)
    return m


B, O = cargar("vigia_4c_b"), cargar("vigia_4c_original")
KALI, SERVIDOR = "10.10.20.30", "200.25.3.17"
BLANCA = {"10.10.10.20", "10.10.30.10"}


def flow(dest=SERVIDOR, port=123, proto="UDP", tipo="flow", pts=1, ptc=1, bts=94, btc=94, ts="2026-11-10T16:09:28.000000+0000"):
    e = {"timestamp": ts, "event_type": tipo, "src_ip": KALI, "src_port": 33310, "dest_ip": dest, "dest_port": port, "proto": proto}
    if tipo == "flow":
        e["flow"] = {"pkts_toserver": pts, "pkts_toclient": ptc, "bytes_toserver": bts, "bytes_toclient": btc, "start": ts}
    return e


def eve(tmp, *evs):
    p = tmp / "eve.json"
    p.write_bytes(b"".join(json.dumps(e, separators=(",", ":")).encode() + b"\n" for e in evs))
    return p


def leer(m, p, ntp=None):
    return m.eve_fuera_lista(p, 0, KALI, BLANCA, 1 << 20, *([] if ntp is None else [ntp]))


def test_el_consulta_ntp_real_observada_queda_exenta_y_contada(tmp_path):
    r = leer(B, eve(tmp_path, flow()), {SERVIDOR})
    assert r["fuera"] == [] and r["fuera_total"] == 0 and r["ntp_excepcion_total"] == 1


def test_sin_la_lista_el_comportamiento_es_el_del_original(tmp_path):
    p = eve(tmp_path, flow(), flow(dest="8.8.8.8", port=53))
    rb, ro = leer(B, p), leer(O, p)
    assert rb["fuera"] == ro["fuera"] and rb["fuera_total"] == ro["fuera_total"] == 2 and rb["ntp_excepcion_total"] == 0


@pytest.mark.parametrize("caso, ev", [
    ("otro servidor NTP no listado", flow(dest="1.2.3.4")),
    ("mismo servidor, puerto 53", flow(port=53)),
    ("mismo servidor, puerto 80 TCP", flow(port=80, proto="TCP")),
    ("TCP al 123", flow(proto="TCP")),
    ("flujo grande (amplificación)", flow(pts=500, ptc=500, bts=40000, btc=40000)),
    ("muchos paquetes", flow(pts=5)),
    ("muchos paquetes de respuesta", flow(ptc=5)),
    ("muchos bytes", flow(bts=401)),
    ("respuesta grande", flow(btc=401)),
    ("evento alert, no flow", flow(tipo="alert")),
    ("evento anomaly", flow(tipo="anomaly")),
])
def test_lo_que_no_es_ese_trafico_sigue_contando_para_x3(tmp_path, caso, ev):
    r = leer(B, eve(tmp_path, ev), {SERVIDOR})
    assert r["fuera_total"] == 1 and r["ntp_excepcion_total"] == 0, caso


def test_evento_que_no_es_flow_no_se_exime_aunque_traiga_tamanos_pequenos(tmp_path):
    e = flow()
    e["event_type"] = "alert"
    assert leer(B, eve(tmp_path, e), {SERVIDOR})["fuera_total"] == 1


def test_flow_sin_tamanos_no_se_exime(tmp_path):
    e = flow()
    e["flow"] = {"start": e["timestamp"]}
    assert leer(B, eve(tmp_path, e), {SERVIDOR})["fuera_total"] == 1


def test_la_lista_blanca_sigue_igual(tmp_path):
    assert leer(B, eve(tmp_path, flow(dest="10.10.10.20", port=53)), {SERVIDOR})["fuera_total"] == 0


def test_mezcla_solo_el_ntp_se_exime(tmp_path):
    r = leer(B, eve(tmp_path, flow(), flow(dest="9.9.9.9", port=123), flow(dest=SERVIDOR, port=22, proto="TCP")), {SERVIDOR})
    assert r["fuera_total"] == 2 and r["ntp_excepcion_total"] == 1


# ---- X3 completo en la decisión del vigía
def x_de(m, evs, tmp, ntp, en_episodio=True):
    t = m._iso_epoch(evs[0]["timestamp"])
    st = m.estado_inicial(25)
    st["intervalos"] = {"dns_inusual-r3": [t - 30, t + 30 if en_episodio else t - 10]}
    obs = {"sensor": {"ok": True, "unidades": {}, "eve": leer(m, eve(tmp, *evs), ntp)}}
    return m.condiciones(st, obs, t + 5, m.CRIT)[1]


def test_x3_reproduce_la_cancelacion_del_10_nov_con_el_original(tmp_path):
    x = x_de(O, [flow()], tmp_path, None)
    assert x and "200.25.3.17:123" in x[0] and "durante un episodio" in x[0]


def test_x3_con_la_excepcion_ya_no_cancela_el_ntp_pero_si_lo_demas(tmp_path):
    assert x_de(B, [flow()], tmp_path, {SERVIDOR}) == []
    assert x_de(B, [flow(), flow(dest="9.9.9.9", port=123)], tmp_path, {SERVIDOR})             # otro destino: cancela
    assert x_de(B, [flow(dest="10.10.20.99", port=443, proto="TCP")], tmp_path, {SERVIDOR})   # ataque a un destino no listado: cancela
    assert x_de(B, [flow(port=53)], tmp_path, {SERVIDOR})                                     # mismo servidor, otro servicio: cancela


def test_x3_fuera_de_episodio_no_cancelaba_antes_ni_ahora(tmp_path):
    assert x_de(O, [flow()], tmp_path, None, en_episodio=False) == []


def test_el_resto_del_codigo_es_identico_al_original():
    import difflib
    a = (GEN / "vigia_4c_original.py").read_text(encoding="utf-8").splitlines()
    b = (GEN / "vigia_4c_b.py").read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    quitadas = [l for l in cambios if l[0] == "-"]
    assert len(quitadas) <= 8 and len(cambios) <= 40                           # el cambio es pequeño y acotado
    assert hashlib.sha256((GEN / "vigia_4c_original.py").read_bytes()).hexdigest().startswith("2fe00200e755fd02")
    assert B.VERSION.endswith("+B-ntp") and O.VERSION == "2026-11-06.1"
    assert B.CRIT == O.CRIT
