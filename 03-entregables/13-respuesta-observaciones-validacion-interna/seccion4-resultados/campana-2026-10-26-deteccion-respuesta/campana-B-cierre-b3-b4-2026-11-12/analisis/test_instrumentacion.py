"""Instrumentación propuesta para la validación futura, verificada con DATOS SINTÉTICOS en banco (sin red; servidor del laboratorio local en 127.0.0.1).
El analizador original (`herramientas\\analizar_b.py`) se importa sin modificar."""
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analizar_b as AB  # noqa: E402  (vía analizar_b_instrumentado)
import analizar_b_instrumentado as V2  # noqa: E402
import analizar_intentos as AI  # noqa: E402
import muestreador_set as MS  # noqa: E402

T0, K = 1_000_000.0, "10.10.20.30"


# ---------------------------------------------------------------- intentos con hora (E3)
def tsv(ruta, antes, despues, t_apl, t_fin, resp_despues):
    """Registro sintético: `antes` iteraciones/s hasta t_apl; luego `despues` iteraciones/s, de las que solo `resp_despues` obtienen respuesta."""
    with open(ruta, "w") as fh:
        fh.write("# t_inicio\tt_fin\tcodigo_http\tt_conexion_s\trc_curl\tlazo\n")
        for s in range(int(T0), int(t_fin)):
            n, resp = (antes, antes) if s < t_apl else (despues, resp_despues)
            for i in range(n):
                t = s + i / max(n, 1)
                ok = i < resp
                fh.write("%.6f\t%.6f\t%s\t%s\t%d\t%d\n" % (t, t + (0.01 if ok else 2.0), "200" if ok else "000", "0.001" if ok else "0.000", 0 if ok else 28, i % 8))


def test_los_intentos_se_distinguen_de_las_peticiones_con_respuesta(tmp_path):
    f = tmp_path / "i.tsv"
    tsv(f, antes=80, despues=45, t_apl=T0 + 15, t_fin=T0 + 90, resp_despues=8)
    r = AI.resumen(f, T0 + 15, T0 + 90)
    assert r["iteraciones"] == 15 * 80 + 75 * 45 and r["con_respuesta"] == 15 * 80 + 75 * 8 and r["sin_respuesta"] == 75 * 37
    assert r["con_respuesta_por_s"] == {"previo": 80.0, "posterior": 8.0}                 # las respuestas caen ≈ 90 %…
    cs = r["continuidad_salida"]
    assert cs["b0_intentos_por_s"] == 80.0 and cs["intentos_posterior_media_por_s"] == 45.0 and cs["cumple"] is True and cs["mejor_racha"] == 75     # …y los intentos siguen
    ser = {s["t"]: s for s in r["serie"]}
    assert ser[int(T0) + 20]["intentos"] == 45 and ser[int(T0) + 20]["con_respuesta"] == 8 and ser[int(T0) + 20]["sin_respuesta"] == 37


def test_si_los_intentos_tambien_caen_por_debajo_del_umbral_no_hay_continuidad_por_salida(tmp_path):
    f = tmp_path / "i.tsv"
    tsv(f, antes=80, despues=12, t_apl=T0 + 15, t_fin=T0 + 90, resp_despues=8)
    cs = AI.resumen(f, T0 + 15, T0 + 90)["continuidad_salida"]
    assert cs["umbral_por_s"] == 40.0 and cs["cumple"] is False and cs["mejor_racha"] == 0


def test_la_racha_exige_k_bloques_consecutivos(tmp_path):
    f = tmp_path / "i.tsv"
    ser = {t: {"intentos": 10, "con_respuesta": 10, "sin_respuesta": 0} for t in range(int(T0), int(T0) + 15)}
    for t in range(int(T0) + 15, int(T0) + 40):                                          # alterna 4 bloques buenos y 1 malo: racha máxima 4 < 5
        ser[t] = {"intentos": 10 if (t - int(T0) - 15) % 5 else 0, "con_respuesta": 0, "sin_respuesta": 0}
    assert AI.continuidad_salida(ser, T0 + 15, T0 + 40)["cumple"] is False and AI.continuidad_salida(ser, T0 + 15, T0 + 40)["mejor_racha"] == 4


# ---------------------------------------------------------------- E3 con «SPAN o salida» (analizar_b sin modificar)
def ep_inundacion(aceptadas_despues=30, syn_despues=38, con_descarte=True):
    traza = [{"evento": "recepcion", "estado": "aceptado", "secuencia": 1, "recibido_en": T0 + 14.9, "t": T0 + 14.9},
             {"evento": "aplicacion", "secuencia": 1, "aplicado_en": T0 + 15, "t": T0 + 15, "nuevos": [{"ip": K, "set": "limitados", "id": "r1", "hasta": T0 + 313}]},
             {"evento": "confirmacion", "secuencia": 1, "confirmadas": ["r1"], "no_confirmadas": [], "t": T0 + 15.1}]
    if con_descarte:
        traza.append({"evento": "primer_descarte", "id": "r1", "ip": K, "t": T0 + 17})
    serie = [{"t": s, "aceptadas": 300 if s < T0 + 15 else aceptadas_despues, "resp": 300, "syn": 300 if s < T0 + 15 else syn_despues} for s in range(int(T0) - 30, int(T0) + 90)]
    return {"episodio_id": "inundacion_http-x", "escenario": "inundacion_http", "origen": K, "accion_prevista": "LIMIT", "t_inicio": T0, "t_fin_ref": T0 + 90,
            "traza_agente": traza, "serie": serie, "control": [], "lecturas_set": []}


def salida(antes, despues, t_apl=T0 + 15):
    return [{"t": s, "intentos": antes if s < t_apl else despues} for s in range(int(T0) - 30, int(T0) + 90)]


def test_sin_serie_de_salida_e3_v2_es_identico_al_analizador_original():
    for kw in ({}, {"aceptadas_despues": 200, "syn_despues": 300}, {"syn_despues": 200}, {"con_descarte": False}):
        ep = ep_inundacion(**kw)
        r2 = AB.e2(ep)
        assert V2.e3_v2(ep, r2) == AB.e3(ep, r2)
    ep = ep_inundacion()
    assert AB.e3(ep, AB.e2(ep))["resultado"] == "indeterminado" and "I2" in AB.e3(ep, AB.e2(ep))["motivo"]       # el patrón de B2: efecto, SYN 38/s < 150/s


def test_con_la_salida_continua_el_efecto_se_evalua_y_cumple_por_la_via_salida():
    ep = ep_inundacion()
    ep["intentos_salida"] = salida(antes=80, despues=45)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "cumple" and r["via_continuidad"] == "salida" and r["continuidad"] == {"span": False, "salida": True, "b0_syn": 300.0, "b0_intentos_salida": 80.0}
    assert r["t_efecto"] == T0 + 15 + 0 or r["t_efecto"] >= T0 + 15                                 # efecto sostenido tras t_apl


def test_con_la_salida_tambien_baja_sigue_indeterminado():
    ep = ep_inundacion()
    ep["intentos_salida"] = salida(antes=80, despues=10)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "indeterminado" and "ni SPAN ni salida" in r["motivo"]


def test_si_siguio_intentando_y_las_aceptadas_no_bajan_es_fallo():
    ep = ep_inundacion(aceptadas_despues=290)
    ep["intentos_salida"] = salida(antes=80, despues=70)
    assert V2.e3_v2(ep, AB.e2(ep))["resultado"] == "fallo"


def test_sin_contador_de_descartes_del_host_no_cumple_aunque_haya_continuidad():
    ep = ep_inundacion(con_descarte=False)
    ep["intentos_salida"] = salida(antes=80, despues=45)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "indeterminado" and "contador de descartes" in r["motivo"]


def test_la_via_span_sigue_valiendo_si_cumple():
    ep = ep_inundacion(syn_despues=200)
    ep["intentos_salida"] = salida(antes=80, despues=10)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "cumple" and r["via_continuidad"] == "span"


# ---------------------------------------------------------------- E3 BLOCK con «SPAN o salida» (11-nov: rama BLOCK de e3_v2; K=3, 0 respuestas, ≥ 1 intento por bloque)
def ep_block(resp_despues=0, syn_despues=20, con_descarte=True, resp_en=None):
    """BLOCK desde T0+15. `resp_en`: conjunto de segundos posteriores con respuesta (para romper la racha)."""
    traza = [{"evento": "recepcion", "estado": "aceptado", "secuencia": 1, "recibido_en": T0 + 14.9, "t": T0 + 14.9},
             {"evento": "aplicacion", "secuencia": 1, "aplicado_en": T0 + 15, "t": T0 + 15, "nuevos": [{"ip": K, "set": "bloqueados", "id": "b1", "hasta": T0 + 313}]},
             {"evento": "confirmacion", "secuencia": 1, "confirmadas": ["b1"], "no_confirmadas": [], "t": T0 + 15.1}]
    if con_descarte:
        traza.append({"evento": "primer_descarte", "id": "b1", "ip": K, "t": T0 + 17})
    serie = []
    for s in range(int(T0) - 30, int(T0) + 90):
        if s < T0 + 15:
            serie.append({"t": s, "aceptadas": 5, "resp": 5, "syn": 5})
        else:
            r = 3 if (resp_en and s in resp_en) else resp_despues
            serie.append({"t": s, "aceptadas": r, "resp": r, "syn": syn_despues})
    return {"episodio_id": "fuerza_bruta_http-x", "escenario": "fuerza_bruta_http", "origen": K, "accion_prevista": "BLOCK", "t_inicio": T0, "t_fin_ref": T0 + 90,
            "traza_agente": traza, "serie": serie, "control": [], "lecturas_set": []}


def salida_block(despues, t_apl=T0 + 15, antes=5):
    return [{"t": s, "intentos": antes if s < t_apl else despues} for s in range(int(T0) - 30, int(T0) + 90)]


def test_block_sin_serie_de_salida_e3_v2_es_identico_al_analizador_original():
    for kw in ({}, {"syn_despues": 0}, {"resp_despues": 4}, {"con_descarte": False}, {"resp_en": set(range(int(T0) + 15, int(T0) + 90, 3))}):
        ep = ep_block(**kw)
        r2 = AB.e2(ep)
        assert V2.e3_v2(ep, r2) == AB.e3(ep, r2), kw
    ep = ep_block()
    assert AB.e3(ep, AB.e2(ep))["resultado"] == "cumple"                                  # el patrón de la fuerza bruta de B2 (SPAN ≥ 1 SYN, 0 respuestas)


def test_block_con_salida_vacia_da_el_mismo_resultado_que_el_original():
    for kw in ({}, {"syn_despues": 0}, {"resp_despues": 4}, {"con_descarte": False}):
        ep = ep_block(**kw)
        ep["intentos_salida"] = []
        a, b = V2.e3_v2(ep, AB.e2(ep)), AB.e3(ep, AB.e2(ep))
        assert a["resultado"] == b["resultado"] and a.get("t_efecto") == b.get("t_efecto"), kw


def test_block_cumple_por_la_via_salida_cuando_el_span_no_ve_intentos(monkeypatch):
    monkeypatch.setattr(V2, "BLOCK_ADMITE_SALIDA", True)       # rama implementada pero DESACTIVADA por decisión de Mark; aquí se verifica activada
    ep = ep_block(syn_despues=0)                                                           # el espejo no ve SYN…
    assert AB.e3(ep, AB.e2(ep))["resultado"] == "indeterminado"                             # …y el analizador original no puede afirmar la continuidad
    ep["intentos_salida"] = salida_block(despues=8)                                        # …pero la salida del generador con hora sí muestra que siguió intentando
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "cumple" and r["via_continuidad"] == "salida" and r["continuidad"]["span"] is False and r["continuidad"]["salida"] is True


def test_block_cumple_por_span_y_registra_ambas_vias(monkeypatch):
    monkeypatch.setattr(V2, "BLOCK_ADMITE_SALIDA", True)
    ep = ep_block(syn_despues=20)
    ep["intentos_salida"] = salida_block(despues=8)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "cumple" and r["via_continuidad"] == "ambas" and r["continuidad"]["span"] and r["continuidad"]["salida"]


def test_block_sin_intentos_por_ninguna_via_es_indeterminado(monkeypatch):
    monkeypatch.setattr(V2, "BLOCK_ADMITE_SALIDA", True)
    ep = ep_block(syn_despues=0)
    ep["intentos_salida"] = salida_block(despues=0)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "indeterminado" and "ni SPAN ni salida" in r["motivo"]


def test_block_si_siguio_intentando_y_hay_respuestas_es_fallo():
    ep = ep_block(resp_despues=4)
    ep["intentos_salida"] = salida_block(despues=8)
    assert V2.e3_v2(ep, AB.e2(ep))["resultado"] == "fallo"


def test_block_la_racha_exige_k3_bloques_sin_respuesta():
    # respuestas en 2 de cada 3 segundos: nunca hay 3 bloques consecutivos sin respuesta
    ep = ep_block(resp_en={s for s in range(int(T0) + 15, int(T0) + 90) if (s - int(T0)) % 3 != 0})
    ep["intentos_salida"] = salida_block(despues=8)
    assert V2.e3_v2(ep, AB.e2(ep))["resultado"] == "fallo"
    ep = ep_block(resp_en={s for s in range(int(T0) + 15, int(T0) + 90) if (s - int(T0)) % 4 != 0})   # 1 de cada 4 sin respuesta: tampoco
    ep["intentos_salida"] = salida_block(despues=8)
    assert V2.e3_v2(ep, AB.e2(ep))["resultado"] == "fallo"


def test_block_una_sola_respuesta_por_bloque_ya_es_fallo_y_se_mide_resp_no_aceptadas(monkeypatch):
    monkeypatch.setattr(V2, "BLOCK_ADMITE_SALIDA", True)       # rama desactivada por defecto; se verifica activada
    ep = ep_block(resp_despues=1)                                                          # BLOCK exige NINGUNA respuesta: 1/s no basta
    ep["intentos_salida"] = salida_block(despues=8)
    assert V2.e3_v2(ep, AB.e2(ep))["resultado"] == "fallo"
    ep = ep_block(resp_despues=3)                                                          # respuestas que no son «aceptadas» también cuentan en BLOCK
    for b in ep["serie"]:
        if b["t"] >= T0 + 15:
            b["aceptadas"] = 0
    ep["intentos_salida"] = salida_block(despues=8)
    assert V2.e3_v2(ep, AB.e2(ep))["resultado"] == "fallo"


def test_block_sin_contador_de_descartes_del_host_no_cumple():
    ep = ep_block(con_descarte=False)
    ep["intentos_salida"] = salida_block(despues=8)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "indeterminado" and "contador de descartes" in r["motivo"]

def test_block_por_defecto_la_unica_fuente_es_span_aunque_haya_salida_con_hora():
    assert V2.BLOCK_ADMITE_SALIDA is False
    ep = ep_block(syn_despues=0)                                                           # el espejo no ve SYN; la salida (si existiera) sí vería intentos
    ep["intentos_salida"] = salida_block(despues=8)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r == AB.e3(ep, AB.e2(ep)) and r["resultado"] == "indeterminado" and "via_continuidad" not in r      # SPAN no verifica la continuidad -> indeterminado
    ep = ep_block(syn_despues=20)                                                          # SPAN sí la verifica; la salida (ausente) es irrelevante
    ep["intentos_salida"] = salida_block(despues=0)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r == AB.e3(ep, AB.e2(ep)) and r["resultado"] == "cumple"


def test_limit_sigue_admitiendo_span_o_salida_con_la_decision_de_block():
    assert V2.BLOCK_ADMITE_SALIDA is False
    ep = ep_inundacion()
    ep["intentos_salida"] = salida(antes=80, despues=45)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "cumple" and r["via_continuidad"] == "salida"


# ---------------------------------------------------------------- E4: transacciones de control con hora
def fila(t, origen="10.10.20.22", cod="200", res="ok", esp="-"):
    return {"t_fin": str(t), "origen": origen, "codigo": cod, "resultado": res, "esperado": esp}


def test_control_desde_transacciones_ok_fallo_y_atribucion():
    rest = [{"ip": "10.10.20.23", "desde": T0 + 10, "hasta": T0 + 100}]                  # un cliente restringido (caso hipotético P1)
    filas = [fila(T0 + 1), fila(T0 + 2, cod="500", esp="500"), fila(T0 + 3, cod="201", esp="201|500"), fila(T0 + 4, cod="503"),
             fila(T0 + 5, res="excepcion:TimeoutError"), fila(T0 + 20, origen="10.10.20.23", res="excepcion:TimeoutError"), fila(T0 + 120, origen="10.10.20.23", res="excepcion:OSError")]
    c = V2.control_desde_transacciones(filas, rest)
    assert [x["ok"] for x in c] == [True, True, True, False, False, False, False]        # 500 previsto no es fallo; 503 imprevisto sí
    assert [x["atribuible"] for x in c] == [False, False, False, False, False, True, False]   # solo el cliente restringido y dentro de su restricción
    ep = {"episodio_id": "e", "escenario": "x", "origen": K, "accion_prevista": "BLOCK", "t_inicio": T0, "t_fin_ref": T0 + 90, "control": c}
    assert AB.e4(ep)["resultado"] == "fallo"                                             # lo consume el analizador sin cambios
    assert AB.e4(dict(ep, control=V2.control_desde_transacciones(filas[:5], rest)))["resultado"] == "cumple"


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def test_el_envoltorio_de_clientes_registra_una_linea_por_accion_con_hora_y_resultado(tmp_path):
    lab = Path(os.environ.get("CF_LAB", "/producto-etapa3/scripts/laboratorio"))
    if not (lab / "clientes_lab.py").exists():
        pytest.skip("generador de clientes no montado")
    port = free_port()
    srv = subprocess.Popen([sys.executable, str(lab / "servidor_lab.py"), "--direccion", "127.0.0.1", "--puerto", str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        reg = tmp_path / "tx.tsv"
        p = subprocess.run([sys.executable, str(AQUI / "clientes_factor1_tx.py"), "--registro", str(reg), "--perfil", "aplicacion", "--servidor", "127.0.0.1",
                            "--puerto", str(port), "--puerto-https", str(free_port()), "--dns", "127.0.0.1", "--una-vuelta"],
                           env={**os.environ, "CF_LAB": str(lab)}, capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr[-500:]
    finally:
        srv.terminate()
    filas = V2.leer_transacciones(reg)
    assert len(filas) >= 5 and all(f["resultado"] == "ok" or f["resultado"].startswith("excepcion:") for f in filas)
    assert all(float(f["t_fin"]) >= float(f["t_inicio"]) for f in filas) and all(f["origen"] == "-" and f["perfil"] == "aplicacion" for f in filas)
    por = {f["accion"]: f for f in filas}
    assert por["api_500"]["codigo"] == "500" and por["api_500"]["esperado"] == "500" and por["api_500"]["resultado"] == "ok"      # error HTTP previsto: acción hecha, no fallo
    assert por["api_ok"]["codigo"] == "200" and por["api_ok"]["metodo"] == "GET" and por["api_ok"]["ruta"] == "/api/ok"
    assert por["api_post"]["metodo"] == "POST" and por["api_post"]["codigo"] in ("201", "500") and por["api_post"]["esperado"] == "201|500"
    ctl = V2.control_desde_transacciones(filas, [])
    assert len(ctl) == len(filas) and all(set(c) == {"t", "ok", "atribuible"} for c in ctl)      # serie `control` con el formato que espera analizar_b
    imposibles = {"dns", "dns_inexistente", "https", "ping", "puerto_cerrado", "abandono"}   # sin DNS/TLS/ICMP en el loopback sintético: la excepción ES el resultado
    assert {f["accion"] for f, c in zip(filas, ctl) if not c["ok"]} <= imposibles          # el resto (HTTP al servidor local; api_500 previsto) queda ok


# ---------------------------------------------------------------- muestreador de sets (E2/E5 con serie continua)
def test_el_muestreador_registra_la_serie_incluidos_los_fallos_del_ayudante(tmp_path):
    t = [T0]
    estados = iter([{"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": {}}}},
                    {"ok": True, "estado": {"sets": {"bloqueados": {K: {"id": "a", "timeout": 298}}, "limitados": {}}}},
                    {"ok": False, "rechazo": "tabla_ausente"},
                    {"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": {}}}}])

    def correr(orden, **kw):
        class R:
            stdout = json.dumps(next(estados))
        return R()
    out = tmp_path / "set.jsonl"
    n = MS.muestrear(["fake"], out, intervalo=2.0, duracion=7.5, ahora=lambda: t[0], dormir=lambda s: t.__setitem__(0, t[0] + s), correr=correr)
    reg = [json.loads(l) for l in out.read_text().splitlines()]
    assert n == 4 and [r["t"] for r in reg] == [T0, T0 + 2, T0 + 4, T0 + 6]
    assert [bool(r["sets"]["bloqueados"]) for r in (reg[0], reg[1])] == [False, True] and reg[1]["sets"]["bloqueados"][K]["timeout"] == 298
    assert reg[2]["ok"] is False and "tabla_ausente" in reg[2]["error"] and reg[3]["ok"] and not reg[3]["sets"]["bloqueados"]   # aplicación -> fallo registrado -> retirada


def test_ambas_vias_de_continuidad_se_registran_siempre_cuando_hay_datos():
    ep = ep_inundacion(syn_despues=200)                                                  # SPAN cumple (200 >= 150)
    ep["intentos_salida"] = salida(antes=80, despues=45)                                 # salida cumple (45 >= 40)
    r = V2.e3_v2(ep, AB.e2(ep))
    assert r["resultado"] == "cumple" and r["continuidad"]["span"] is True and r["continuidad"]["salida"] is True and r["via_continuidad"] == "ambas"
    ep2 = ep_inundacion(syn_despues=200)
    ep2["intentos_salida"] = salida(antes=80, despues=10)                                # solo SPAN
    c = V2.e3_v2(ep2, AB.e2(ep2))["continuidad"]
    assert c["span"] is True and c["salida"] is False and c["b0_intentos_salida"] == 80.0
    ep3 = ep_inundacion()
    ep3["intentos_salida"] = salida(antes=80, despues=45)                                # solo salida; el SPAN (38/s) queda por debajo y se registra como tal
    c3 = V2.e3_v2(ep3, AB.e2(ep3))["continuidad"]
    assert c3["span"] is False and c3["salida"] is True and c3["b0_syn"] == 300.0