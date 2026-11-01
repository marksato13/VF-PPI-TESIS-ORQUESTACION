#!/usr/bin/env python3
"""Pruebas SIN tráfico de la revisión 3B (criterios v2). Datos sintéticos: comprueban el código, no son resultados.
    python3 pruebas/test_revision_3b.py        (o pytest)
Casos obligatorios (CRITERIOS-REVISION.md §4):
  1 dos ventanas presentes escritas con 20,2 s de diferencia no cuentan como perdidas
  2 una ventana ausente sigue detectándose
  3 una ventana no evaluada no sale del denominador
  4 se detecta la falta de historia previa o de cobertura posterior
  5 un inventario truncado no permite observación completa
  6 una fuente degradada no pasa a completa por coincidir con el replay
Además: respaldo v1 sin desglose -> no verificado; selección de PCAP del recálculo v2; extremo a extremo con el
verificador v2 sobre ficheros reales temporales.
"""
from __future__ import annotations
import ast, json, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "herramientas"))
sys.path.insert(0, str(AQUI.parent.parent / "scripts"))
import analizar as an  # noqa: E402
import analizar_3b as a3  # noqa: E402
import generar_respaldos as gr  # noqa: E402
import generar_respaldos_v2 as g2  # noqa: E402
import verificar_integridad_v2 as v2  # noqa: E402

U = {"0.05": -0.5694578968203694, "0.03": -0.5898535710336618, "0.01": -0.6223889502095352}
KALI, SRV = "10.10.20.30", "10.10.30.10"
T0 = 1793502000.0
INI, FIN = T0 + 0.5, T0 + 90.3
EID = "inundacion_http-r1"
EP = {"escenario": "inundacion_http", "repeticion": 1, "destino": SRV, "inicio_ep": INI, "fin_ep": FIN,
      "estado": "completo"}
ok = {"n": 0}


def check(c, m):
    assert c, "FALLA: " + m
    ok["n"] += 1


def mundo(desde=T0 - 400, hasta=T0 + 500, inv_hasta=None, escritura=lambda w: w + 6.0):
    """Inventario y vivo idénticos (todas las entidades), PCAP cada 15 s, stats EVE cada 8 s."""
    vivo, inv_dec = {}, {}
    w = desde
    while w <= hasta:
        for ip in (KALI, SRV):
            k = (ip, an.iso(w))
            inv_dec[k] = {"event": "decision"}
            vivo[k] = {"entity_ip": ip, "window_end_utc": k[1], "_wend": w, "_logged": escritura(w),
                       "_disp": escritura(w), "_disp_fuente": "prueba", "marca_pcap": w + 3.0, "marca_eve": w + 3.0,
                       "_score": -0.4, "_score_estado": "ok", "_pk10": 10, "decision": "PERMIT",
                       "heuristico": None, "detector_name": None, "threshold": -0.5694, "_ln": 1}
        w += 10
    inv = {"desde": desde, "hasta": inv_hasta if inv_hasta is not None else hasta, "esperadas": inv_dec,
           "no_evaluadas_en_referencia": {}, "fuente": "prueba", "sha256": "-"}
    tp = [desde - 30 + 15 * i for i in range(int((hasta - desde + 60) / 15) + 1)]
    ts = [desde - 30 + 8 * i for i in range(int((hasta - desde + 60) / 8) + 1)]
    return vivo, inv, tp, ts


BASE = {"campana": "c", "episodio": EID, "periodo": {"inicio": INI - 120, "fin": FIN + 90}, "origen": "prueba"}


def cob(vivo, inv, tp, ts, ne=None, tlog=None):
    tlog = tlog if tlog is not None else [r["_logged"] for r in vivo.values()]
    return g2.cobertura_v2(BASE, EP, KALI, tp, ts, inv, vivo, ne or {}, tlog)


# ------------------------------------------------------------------------------------------------ caso 1
def test_1_hueco_escritura_20_2_no_es_perdida():
    import math
    vivo, inv, tp, ts = mundo()
    # todas las ventanas presentes, pero escritas en lotes cada 20,2 s: cada escritura lleva DOS ventanas juntas
    w0 = T0 - 400                                           # primera ventana del mundo
    for r in vivo.values():                                 # ventanas w0+20j y w0+20j+10 -> escritas en w0+20,2j+15
        r["_logged"] = r["_disp"] = w0 + 20.2 * math.floor((r["_wend"] - w0) / 20) + 15
    tlog2 = sorted(r["_logged"] for r in vivo.values())
    escrituras = sorted(set(tlog2))
    huecos = {round(b - a, 1) for a, b in zip(escrituras, escrituras[1:])}
    check(huecos == {20.2}, f"caso 1: escrituras separadas 20,2 s ({huecos})")
    por_escritura = {t: sum(1 for r in vivo.values() if r["_logged"] == t and r["entity_ip"] == KALI) for t in escrituras}
    check(set(por_escritura.values()) <= {1, 2} and list(por_escritura.values()).count(2) >= 40, "caso 1: dos ventanas de la Kali escritas juntas en cada lote")
    c = cob(vivo, inv, tp, ts, tlog=tlog2)
    check(c["continuidad"]["verificado"], "caso 1: continuidad v2 verificada con huecos de escritura de 20,2 s")
    check(all(c["intervalos"][n]["verificado"] for n in ("previa", "durante", "posterior")),
          "caso 1: previa/durante/posterior verificadas")
    check(c["informativo"]["hueco_escritura_max_s"] >= 20.2 - 1e-6, "caso 1: el hueco de escritura se informa")
    # la v1 (tolerancia 20 s sobre la escritura) lo contaba como pérdida: contradicción documentada
    _, _, h = gr.continuidad(tlog2, INI, FIN + 60, gr.TOL)
    check(h is not None and h > gr.TOL, "caso 1: con v1 el mismo registro supera la tolerancia de 20 s")


# ------------------------------------------------------------------------------------------------ caso 2
def test_2_ausente_se_detecta():
    vivo, inv, tp, ts = mundo()
    k = (SRV, an.iso(T0 - 50))                                # en la previa, de otra entidad
    del vivo[k]
    c = cob(vivo, inv, tp, ts)
    p = c["intervalos"]["previa"]["procesamiento"]
    check(not p["ok"] and p["n_ausentes"] == 1, "caso 2: ventana requerida ausente detectada en la previa")
    check(not c["intervalos"]["previa"]["verificado"] and not c["continuidad"]["verificado"],
          "caso 2: previa y continuidad no verificadas")
    check(c["intervalos"]["durante"]["verificado"], "caso 2: durante no se ve afectada")
    vivo2, inv2, tp2, ts2 = mundo()
    del vivo2[(KALI, an.iso(T0 + 40))]
    c2 = cob(vivo2, inv2, tp2, ts2)
    check(not c2["intervalos"]["durante"]["anclas_kali"]["ok"], "caso 2: ancla de la Kali ausente durante el ataque")


# ------------------------------------------------------------------------------------------------ caso 3
def test_3_no_evaluada_no_sale_del_denominador():
    vivo, inv, tp, ts = mundo()
    k = (KALI, an.iso(T0 + 150))                              # dentro de la posterior [fin, fin+90]
    r = vivo.pop(k)
    ne = {k: {"_clave": k, "_wend": r["_wend"], "_logged": r["_logged"], "motivo": "x"}}
    c0 = cob(*mundo())
    c = cob(vivo, inv, tp, ts, ne=ne)
    p, p0 = c["intervalos"]["posterior"]["procesamiento"], c0["intervalos"]["posterior"]["procesamiento"]
    check(p["requeridas"] == p0["requeridas"], "caso 3: el denominador (requeridas) no cambia")
    check(p["decididas"] == p0["decididas"] - 1 and p["n_no_evaluadas"] == 1 and not p["ok"],
          "caso 3: la no evaluada cuenta como no decidida y la posterior no verifica")
    # y en el analizador 3B (sin modificar) la no evaluada en la referencia sigue requerida
    inv["no_evaluadas_en_referencia"][k] = inv["esperadas"].pop(k)
    check(k in a3.requeridas_inventario(inv), "caso 3: analizar_3b mantiene la no evaluada como requerida")


# ------------------------------------------------------------------------------------------------ caso 4
def test_4_falta_previa_o_posterior():
    vivo, inv, tp, ts = mundo()
    tp_corto = [t for t in tp if t >= INI - 60]                # PCAP empiezan 60 s antes del ataque
    c = cob(vivo, inv, tp_corto, ts)
    check(not c["intervalos"]["previa"]["pcap"]["ok"] and not c["intervalos"]["previa"]["verificado"],
          "caso 4: previa sin PCAP suficientes")
    ts_corto = [t for t in ts if t <= FIN + 40]                # pulso EVE se corta antes de fin+90
    c = cob(vivo, inv, tp, ts_corto)
    check(not c["intervalos"]["posterior"]["eve"]["ok"] and not c["intervalos"]["posterior"]["verificado"],
          "caso 4: posterior sin pulso EVE")
    ts_hueco = [t for t in ts if not (INI - 100 < t < INI - 80)]   # hueco de 24 s en la previa
    c = cob(vivo, inv, tp, ts_hueco)
    check(not c["intervalos"]["previa"]["eve"]["ok"], "caso 4: hueco >= 16 s del pulso EVE en la previa")
    vivo2 = {k: v for k, v in vivo.items() if not (FIN + 50 < v["_wend"] <= FIN + 90)}
    c = cob(vivo2, inv, tp, ts)
    check(not c["intervalos"]["posterior"]["procesamiento"]["ok"], "caso 4: posterior sin ventanas decididas")
    vivo3, inv3, tp3, ts3 = mundo()
    vivo3[(SRV, an.iso(T0 - 30))]["marca_pcap"] = T0 - 35      # decidida antes de tener el PCAP de su ventana
    c = cob(vivo3, inv3, tp3, ts3)
    check(c["intervalos"]["previa"]["procesamiento"]["n_sin_marcas"] == 1 and not c["intervalos"]["previa"]["verificado"],
          "caso 4: marca_pcap < window_end detectada")


# ------------------------------------------------------------------------------------------------ caso 5
def test_5_inventario_truncado():
    vivo, inv, tp, ts = mundo(inv_hasta=FIN + 40)
    c = cob(vivo, inv, tp, ts)
    po = c["intervalos"]["posterior"]["procesamiento"]
    check(not po["ok"] and po.get("fuera_del_inventario"), "caso 5: posterior fuera del inventario -> no verificada")
    check(not c["intervalos"]["durante"]["verificado"], "caso 5: durante (hasta fin+60) fuera del inventario")
    r = a3.clasificar_3b(EID, EP, KALI, U, vivo, {}, inv, None, True, {EID: {"estado": "completa"}})
    check(not r["observacion"]["completa"] and not r["en_poblacion_principal"],
          "caso 5: analizar_3b no da observación completa con inventario truncado")
    c = cob(vivo, None, tp, ts)
    check(not c["continuidad"]["verificado"], "caso 5: sin inventario no se verifica la continuidad")


# ------------------------------------------------------------------------------------------------ caso 6
def test_6_fuente_degradada_no_pasa_por_coincidir_con_replay():
    vivo, inv, tp, ts = mundo()                               # vivo == inventario (replay) en todas las claves
    ts_deg = [t for t in ts if not (INI + 20 < t < INI + 50)]  # Suricata deja de escribir 30 s
    c = cob(vivo, inv, tp, ts_deg)
    check(c["intervalos"]["durante"]["procesamiento"]["ok"], "caso 6: el procesamiento coincide con el replay")
    check(not c["intervalos"]["durante"]["verificado"], "caso 6: pero la fuente EVE degradada impide verificar")
    r = a3.clasificar_3b(EID, EP, KALI, U, vivo, {}, inv, None, True, {EID: {"estado": "degradada"}})
    check(not r["observacion"]["completa"], "caso 6: analizar_3b: calidad degradada -> observación incompleta")
    # kernel_drops de Suricata en el periodo -> captura no apta aunque todo lo demás verifique (v1 sin cambios)
    with tempfile.TemporaryDirectory() as d:
        e = _descriptor(Path(d), cob(*mundo()), drops=5)
        res = v2.evaluar_episodio(e)
        check(res["requisitos"]["continuidad"]["estado"] == "verificado"
              and res["requisitos"]["captura_sin_errores_relevantes"]["estado"] == "ausente" and not res["apto"],
              "caso 6: kernel_drops > 0 -> no apto aunque continuidad v2 verifique")


# ------------------------------------------------------------------------------------------------ extra
def _descriptor(d: Path, cobertura: dict, drops=0) -> dict:
    f = d / "f.bin"; f.write_bytes(b"x")
    h = gr.sha256(f)
    rel = {**BASE, "tolerancia_s": 1.0, "requeridos": ["sensor"],
           "mediciones": [{"host": "sensor", "referencia": "r", "momento": INI, "desfase_s": 0.01,
                           "incertidumbre_s": 0.01}]}
    cap = {**BASE, "errores": ([{"desc": f"Suricata kernel_drops +{drops}", "afecta_fuentes": True}] if drops else []),
           "paquetes_descartados": 0}
    rein = {**BASE, "reinicios": {"motor": [], "captura": [], "suricata": []}}
    rutas = {}
    for n, doc in (("cobertura", cobertura), ("captura", cap), ("reinicios", rein), ("relojes", rel)):
        (d / f"{n}.json").write_text(json.dumps(doc), encoding="utf-8"); rutas[n] = {"ruta": str(d / f"{n}.json")}
    return {"episodio_id": EID, "campana": "c", "intervalo": {"inicio": INI, "fin": FIN},
            "rutas": {k: str(f) for k in ("pcap", "eve", "decisiones", "caracteristicas")},
            "hashes_esperados": {k: h for k in ("pcap", "eve", "decisiones", "caracteristicas")},
            "respaldos": rutas}


def test_extremo_a_extremo_verificador_v2():
    with tempfile.TemporaryDirectory() as d:
        res = v2.evaluar_episodio(_descriptor(Path(d), cob(*mundo())))
        check(res["apto"], "e2e: mundo completo -> apto con v2: " + json.dumps(res["resumen"]))
    with tempfile.TemporaryDirectory() as d:
        vivo, inv, tp, ts = mundo()
        del vivo[(SRV, an.iso(T0 + 120))]
        res = v2.evaluar_episodio(_descriptor(Path(d), cob(vivo, inv, tp, ts)))
        check(not res["apto"] and "cobertura_posterior" in res["resumen"]["ausente"]
              and "continuidad" in res["resumen"]["ausente"], "e2e: ausente -> posterior y continuidad no verificadas")


def test_respaldo_v1_sin_desglose_no_verifica():
    v1 = {**BASE, "previa_s": 500.0, "posterior_s": 500.0, "durante_completa": True, "continuidad_sin_huecos": True,
          "faltantes": []}
    with tempfile.TemporaryDirectory() as d:
        res = v2.evaluar_episodio(_descriptor(Path(d), v1))
        for r in ("cobertura_previa", "cobertura_durante", "cobertura_posterior", "continuidad"):
            check(res["requisitos"][r]["estado"] == "ausente", f"v1 sin desglose: {r} no verificado")
        check(not res["apto"], "v1 sin desglose: no apto")


def _cargar_seleccionar():
    src = (AQUI.parent / "herramientas" / "recalcular_caracteristicas_v2.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "seleccionar")
    ns: dict = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "seleccionar", "exec"), ns)
    return ns["seleccionar"]


def test_recalculo_v2_selecciona_por_ultimo_decodificado():
    sel = _cargar_seleccionar()
    mp = 1141.691678
    # fichero real del caso dns_inusual-r3 08:18:50: último decodificado = marca_pcap, 2 tramas finales hasta 1141,948
    a = (1127.0, 1141.691678, ["p"], 1141.948)
    b = (1112.0, 1126.9, ["q"], 1126.95)
    c = (1142.0, 1156.0, ["r"], 1156.1)                       # posterior: no leído
    cerr, nuevo = sel([a, b, c, None], mp)
    check(a in cerr and b in cerr and c not in cerr, "recálculo v2: incluye el fichero con tramas finales no decodificadas")
    check(abs(nuevo - mp) < 1e-9, "recálculo v2: la poda parte de marca_pcap (máximo decodificado)")
    v1 = [x for x in (a, b, c) if x[3] <= mp + 1e-6]
    check(a not in v1, "recálculo v1 (última trama) excluía ese fichero: defecto reproducido")


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_") and callable(f):
            f()
    print(f"OK: {ok['n']} comprobaciones")
