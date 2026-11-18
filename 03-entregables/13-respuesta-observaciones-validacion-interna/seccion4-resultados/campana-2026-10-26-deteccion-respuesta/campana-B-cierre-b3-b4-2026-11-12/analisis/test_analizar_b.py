import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas"))
import analizar_b as a  # noqa: E402

KALI = "10.10.20.30"
T0 = 1000.0


def traza(t_rec=1001.0, t_apl=1001.4, conf="confirmada", ip=KALI, set_="bloqueados", extra_nuevos=(), descarte=True):
    nuevos = [{"id": "r1", "evento_id": "e1", "ip": ip, "set": set_, "hasta": t_apl + 300, "timeout": 300}, *extra_nuevos]
    ev = [{"evento": "recepcion", "t": t_rec, "recibido_en": t_rec, "secuencia": 7, "estado": "aceptado", "ids": ["r1"]},
          {"evento": "aplicacion", "t": t_apl, "secuencia": 7, "aplicado_en": t_apl, "nuevos": nuevos}]
    if conf == "confirmada":
        ev.append({"evento": "confirmacion", "secuencia": 7, "confirmadas": ["r1"], "no_confirmadas": []})
    elif conf == "no_confirmada":
        ev.append({"evento": "confirmacion", "secuencia": 7, "confirmadas": [], "no_confirmadas": ["r1"]})
    if descarte:
        ev.append({"evento": "primer_descarte", "t": t_apl + 0.6, "set": set_, "ip": ip, "id": "r1", "descartes": 4})
    return ev


def serie_block(t_apl=1002, t_fin=1090, intento=True, hueco=False):
    s = []
    for t in range(1000, 1090):
        activo = t >= t_apl + 1
        if hueco and 1010 <= t < 1030:
            continue
        s.append({"t": float(t), "aceptadas": 0, "resp": 0 if activo else 5, "syn": 20 if intento else 0})
    return s


def serie_limit(reduce=True, base=True):
    """Regla cargada en 1011,0: el ruido de arranque no entra en la base (bloques 1001..1010)."""
    s = []
    for t in range(1000, 1090):
        activo = t >= 1012 and reduce
        if not base and t < 1008:
            continue
        s.append({"t": float(t), "aceptadas": 5.0 if activo else 40.0, "resp": 0, "syn": 40})
    return s


def ep(**kw):
    e = {"episodio_id": "x", "escenario": "fuerza_bruta_http", "origen": KALI, "accion_prevista": "BLOCK",
         "t_inicio": T0, "t_fin_ref": T0 + 90, "t_det": T0 + 0.3, "t_siguiente": T0 + 400, "u": 0.02,
         "traza_agente": traza(), "serie": serie_block(),
         "lecturas_set": [{"t": T0 + 120, "bloqueados": [], "limitados": []}],
         "control": [{"t": T0 + i, "ok": True, "atribuible": False} for i in range(-30, 100, 10)]}
    e.update(kw)
    return e


def r(e, c):
    return a.evaluar(e)[c]["resultado"]


# ---- E2: confirmada, tardía, ambigua, sin evidencia
def test_e2_confirmada_a_tiempo():
    x = a.evaluar(ep())
    assert x["E2"]["resultado"] == "cumple" and x["E2"]["confirmacion"] == "confirmada"
    assert x["metricas"]["t_apl_menos_t_inicio"] == pytest.approx(1.4)
    assert x["metricas"]["margen"] == pytest.approx(88.6)


def test_e2_tardia_es_fallo():
    assert r(ep(traza_agente=traza(1095.0, 1095.2)), "E2") == "fallo"


def test_e2_ambigua_es_indeterminado():
    assert r(ep(traza_agente=traza(1089.9, 1090.1)), "E2") == "indeterminado"


def test_e2_sin_evidencia_con_traza_es_fallo():
    t = [e for e in traza() if e["evento"] == "recepcion"]
    assert r(ep(traza_agente=t), "E2") == "fallo"


def test_e2_sin_traza_es_fallo_del_experimento():
    assert r(ep(traza_agente=[]), "E2") == "fallo_experimento"


def test_e2_no_confirmada_fallo_y_sin_confirmacion_indeterminado():
    assert r(ep(traza_agente=traza(conf="no_confirmada")), "E2") == "fallo"
    assert r(ep(traza_agente=traza(conf="ninguna")), "E2") == "indeterminado"


def test_e2_restriccion_ajena_es_fallo_p1():
    extra = [{"id": "r2", "evento_id": "e2", "ip": "10.10.20.99", "set": "bloqueados", "hasta": 1400, "timeout": 300}]
    x = a.evaluar(ep(traza_agente=traza(extra_nuevos=extra)))
    assert x["E2"]["resultado"] == "fallo" and x["E2"]["violaciones"][0]["ip"] == "10.10.20.99"


def test_e2_set_equivocado_es_fallo():
    assert r(ep(traza_agente=traza(set_="limitados")), "E2") == "fallo"


def test_e2_usa_el_minimo_de_fin_observado():
    assert r(ep(t_fin_observado=1000.5), "E2") == "fallo"  # el episodio terminó antes de la regla
    assert r(ep(t_fin_observado=1001.0), "E2") == "indeterminado"  # recepción en el borde: no se decide


def test_dns_sin_punto_de_aplicacion_no_aplica():
    x = a.evaluar(ep(accion_prevista=None, escenario="dns_inusual", traza_agente=[]))
    assert x["E2"]["resultado"] == x["E3"]["resultado"] == x["E5"]["resultado"] == "no_aplica"
    assert x["E4"]["resultado"] == "cumple"


# ---- E3
def test_e3_block_cumple():
    x = a.evaluar(ep())
    assert x["E3"]["resultado"] == "cumple" and x["E3"]["t_efecto"] == 1003.0


def test_e3_block_generador_no_intenta_es_indeterminado():
    assert r(ep(serie=serie_block(intento=False)), "E3") == "indeterminado"


def test_e3_block_ventana_corta_es_indeterminado_i1():
    s = [b for b in serie_block() if b["t"] < 1005]
    e = ep(traza_agente=traza(1001.0, 1002.5), serie=s, t_fin_ref=1005.0, t_inicio=1000.0)
    x = a.evaluar(e)["E3"]
    assert x["resultado"] == "indeterminado" and "I1" in x["motivo"]


def test_e3_block_sigue_respondiendo_es_fallo():
    s = [{**b, "resp": 5} for b in serie_block()]
    assert r(ep(serie=s), "E3") == "fallo"


def test_e3_serie_con_huecos_es_indeterminado_i3():
    assert "I3" in a.evaluar(ep(serie=serie_block(hueco=True)))["E3"]["motivo"]


def test_e3_depende_de_e2():
    assert r(ep(traza_agente=traza(1095, 1095.2)), "E3") == "fallo"
    assert r(ep(traza_agente=traza(1089.9, 1090.1)), "E3") == "indeterminado"
    assert r(ep(traza_agente=[]), "E3") == "fallo_experimento"


def test_e3_limit_cumple_fallo_y_sin_linea_base():
    base = dict(accion_prevista="LIMIT", escenario="inundacion_http",
                traza_agente=traza(1010.5, 1011.0, set_="limitados"))
    assert r(ep(serie=serie_limit(), **base), "E3") == "cumple"
    assert r(ep(serie=serie_limit(reduce=False), **base), "E3") == "fallo"
    x = a.evaluar(ep(serie=serie_limit(base=False), **base))["E3"]
    assert x["resultado"] == "indeterminado" and "I5" in x["motivo"]


def test_e3_limit_linea_base_baja_es_indeterminado():
    s = [{**b, "aceptadas": 1.0} for b in serie_limit()]
    assert "I5" in a.evaluar(ep(serie=s, accion_prevista="LIMIT",
                                traza_agente=traza(1010.5, 1011.0, set_="limitados")))["E3"]["motivo"]


def test_e3_limit_aplicada_antes_de_diez_segundos_no_tiene_base():
    """Con t_apl a 1,4 s del inicio no hay 10 bloques previos: indeterminado (I5), no cumple."""
    x = a.evaluar(ep(serie=serie_limit(), accion_prevista="LIMIT", traza_agente=traza(set_="limitados")))["E3"]
    assert x["resultado"] == "indeterminado" and "I5" in x["motivo"]


# ---- E4 / E5
def test_e4():
    assert r(ep(), "E4") == "cumple"
    mal = ep()["control"] + [{"t": T0 + 50, "ok": False, "atribuible": True}]
    assert r(ep(control=mal), "E4") == "fallo"
    ajeno = ep()["control"] + [{"t": T0 + 50, "ok": False, "atribuible": False}]
    assert r(ep(control=ajeno), "E4") == "cumple"
    fuera = [{"t": T0 + 500, "ok": True, "atribuible": False}]
    assert r(ep(control=fuera), "E4") == "fallo_experimento"


def test_e5():
    assert r(ep(), "E5") == "cumple"
    persiste = [{"t": T0 + 120, "bloqueados": [KALI], "limitados": []}]
    assert r(ep(lecturas_set=persiste), "E5") == "fallo"
    assert r(ep(lecturas_set=[]), "E5") == "indeterminado"
    tarde = [{"t": T0 + 500, "bloqueados": [], "limitados": []}]
    assert r(ep(lecturas_set=tarde), "E5") == "indeterminado"
    assert r(ep(traza_agente=[e for e in traza() if e["evento"] == "recepcion"]), "E5") == "no_aplica"


# ---- qué prueba cada evidencia: helper ok != regla cargada != efecto
def test_regla_confirmada_sin_descartes_en_el_host_no_prueba_el_efecto():
    x = a.evaluar(ep(traza_agente=traza(descarte=False)))
    assert x["E2"]["resultado"] == "cumple"                  # la regla está cargada (releída en el set con su id)
    assert x["E3"]["resultado"] == "indeterminado" and "contador de descartes" in x["E3"]["motivo"]
    base = dict(accion_prevista="LIMIT", escenario="inundacion_http")
    y = a.evaluar(ep(serie=serie_limit(), traza_agente=traza(1010.5, 1011.0, set_="limitados", descarte=False), **base))
    assert y["E3"]["resultado"] == "indeterminado"


def test_el_descarte_debe_ser_de_la_misma_regla_y_del_origen():
    otro_id = [{**e, "id": "otra"} if e["evento"] == "primer_descarte" else e for e in traza()]
    otra_ip = [{**e, "ip": "10.10.20.99"} if e["evento"] == "primer_descarte" else e for e in traza()]
    antes = [{**e, "t": 900.0} if e["evento"] == "primer_descarte" else e for e in traza()]
    for t in (otro_id, otra_ip, antes):
        assert r(ep(traza_agente=t), "E3") == "indeterminado"
    assert a.evaluar(ep())["E3"]["primer_descarte_host"] == pytest.approx(1002.0)


def test_el_retorno_del_helper_sin_confirmacion_no_cumple_e2():
    """Un 'aplicacion' sin releer el set es solo un retorno ok: E2 no puede ser cumple."""
    assert r(ep(traza_agente=traza(conf="ninguna")), "E2") == "indeterminado"


# ---- fronteras exactas (mutaciones)
def test_e2_fronteras_de_la_incertidumbre():
    # t_sup + u == t_fin  -> no es "antes": indeterminado
    assert r(ep(u=0.5, traza_agente=traza(1089.5, 1089.5)), "E2") == "indeterminado"
    # la incertidumbre cuenta: 1089,9 + 0,5 > 1090
    assert r(ep(u=0.5, traza_agente=traza(1089.9, 1089.9)), "E2") == "indeterminado"
    # t_inf - u == t_fin -> ya es fallo
    assert r(ep(u=0.5, traza_agente=traza(1090.5, 1090.5)), "E2") == "fallo"
    assert r(ep(u=0.5, traza_agente=traza(1090.2, 1090.5)), "E2") == "indeterminado"


def test_e3_limit_reduccion_insuficiente_es_fallo():
    base = dict(accion_prevista="LIMIT", escenario="inundacion_http", traza_agente=traza(1010.5, 1011.0, set_="limitados"))
    s = [{**b, "aceptadas": 30.0 if b["t"] >= 1012 else b["aceptadas"]} for b in serie_limit()]
    assert r(ep(serie=s, **base), "E3") == "fallo"  # 30 > (1-0,5)*40


def test_e3_limit_efecto_no_sostenido_es_fallo():
    base = dict(accion_prevista="LIMIT", escenario="inundacion_http", traza_agente=traza(1010.5, 1011.0, set_="limitados"))
    s = [{**b, "aceptadas": 5.0 if 1012 <= b["t"] < 1015 else 40.0} for b in serie_limit()]  # 3 bloques y vuelve
    assert r(ep(serie=s, **base), "E3") == "fallo"


def test_e3_limit_generador_que_reduce_sus_intentos_es_indeterminado():
    base = dict(accion_prevista="LIMIT", escenario="inundacion_http", traza_agente=traza(1010.5, 1011.0, set_="limitados"))
    s = [{**b, "syn": 5} if b["t"] >= 1012 else b for b in serie_limit()]  # 5 < 0,5*40
    x = a.evaluar(ep(serie=s, **base))["E3"]
    assert x["resultado"] == "indeterminado" and "I2" in x["motivo"]


def test_e3_no_mejora_a_e2_indeterminada():
    x = a.evaluar(ep(traza_agente=traza(conf="ninguna")))  # regla sin confirmar, efecto visible
    assert x["E2"]["resultado"] == "indeterminado" and x["E3"]["resultado"] == "indeterminado"


def test_e3_solo_cuenta_bloques_completos_antes_del_fin():
    s = [{**b, "resp": 5 if b["t"] < 1005 else 0} for b in serie_block()]
    e = ep(traza_agente=traza(1001.0, 1001.4), serie=s, t_fin_ref=1006.0)
    assert r(e, "E3") == "fallo"  # en la ventana útil (1002..1005) no se sostuvo el efecto


def test_e4_ventana_incluye_60_s_antes_y_90_despues():
    antes = ep()["control"] + [{"t": T0 - 30, "ok": False, "atribuible": True}]
    despues = ep()["control"] + [{"t": T0 + 90 + 60, "ok": False, "atribuible": True}]
    fuera = ep()["control"] + [{"t": T0 - 90, "ok": False, "atribuible": True}]
    assert r(ep(control=antes), "E4") == "fallo" and r(ep(control=despues), "E4") == "fallo"
    assert r(ep(control=fuera), "E4") == "cumple"


def test_e5_ignora_lecturas_previas_al_fin_y_usa_la_ultima():
    previa = [{"t": T0 + 10, "bloqueados": [], "limitados": []}]
    assert r(ep(lecturas_set=previa), "E5") == "indeterminado"
    dos = [{"t": T0 + 95, "bloqueados": [KALI], "limitados": []}, {"t": T0 + 120, "bloqueados": [], "limitados": []}]
    assert r(ep(lecturas_set=dos), "E5") == "cumple"
    dos_rev = [{"t": T0 + 95, "bloqueados": [], "limitados": []}, {"t": T0 + 120, "bloqueados": [KALI], "limitados": []}]
    assert r(ep(lecturas_set=dos_rev), "E5") == "fallo"


# ---- retirada explícita y caducidad natural se publican por separado
def test_e5_distingue_retirada_explicita_de_caducidad_natural():
    nat = a.evaluar(ep())["E5"]
    assert nat["resultado"] == "cumple" and nat["via"] == "caducidad_natural"
    exp = a.evaluar(ep(d5_retirada_en=T0 + 100.0))["E5"]            # hasta = t_apl + 300: la regla seguía vigente
    assert exp["resultado"] == "cumple" and exp["via"] == "retirada_explicita"
    tarde = a.evaluar(ep(d5_retirada_en=T0 + 2000.0))["E5"]         # D5 llegó cuando ya había expirado sola
    assert tarde["via"] == "caducidad_natural"


def test_resumen_no_mezcla_las_dos_vias():
    eps = [ep(episodio_id="n1"), ep(episodio_id="n2"), ep(episodio_id="x1", d5_retirada_en=T0 + 100.0)]
    s = a.resumen({"episodios": eps})
    assert s["e5_por_via"] == {"caducidad_natural": {"cumple": 2}, "retirada_explicita": {"cumple": 1}}


# ---- conjunto
def test_clopper_pearson_valores_conocidos():
    lo, hi = a.clopper_pearson(5, 5)
    assert lo == pytest.approx(0.4782, abs=1e-3) and hi == 1.0
    lo, hi = a.clopper_pearson(0, 5)
    assert lo == 0.0 and hi == pytest.approx(0.5218, abs=1e-3)
    lo, hi = a.clopper_pearson(3, 5)
    assert (lo, hi) == (pytest.approx(0.1466, abs=1e-3), pytest.approx(0.9473, abs=1e-3))


def test_contabilidad_y_exclusion():
    eps = [ep(episodio_id=f"e{i}") for i in range(4)] + [copy.deepcopy(ep(episodio_id="ex", excluido="corte de red"))]
    s = a.resumen({"episodios": eps, "planificados": 6})
    assert s["contabilidad"] == {"planificados": 6, "ejecutados": 5, "admitidos": 4,
                                 "excluidos": [{"episodio_id": "ex", "motivo": "corte de red"}]}
    assert s["tabla"]["fuerza_bruta_http"]["E2"] == {"cumple": 4}
    assert s["clopper_pearson"]["fuerza_bruta_http/E2"]["n"] == 4
