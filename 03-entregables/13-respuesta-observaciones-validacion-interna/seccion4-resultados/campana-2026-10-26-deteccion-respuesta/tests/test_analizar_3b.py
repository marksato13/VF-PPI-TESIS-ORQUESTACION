#!/usr/bin/env python3
"""Pruebas SIN tráfico del analizador 3B (preparación 3A, 2026-11-01) y de poblacion.py.

Datos sintéticos: comprueban el CÓDIGO, no son resultados. Ejecuta:  python3 tests/test_analizar_3b.py
Casos (encargo 3A, punto 10): señal oportuna y posterior · ventana que solapa el final · señal no atribuible ·
ventana tardía, ausente y no evaluada · ciclo sin decisiones y hueco > 20 s (no es pérdida) · detección con
observación parcial · fuente degradada · actividad del ataque solo antes del inicio · excepciones y población ·
separación entre las 7 configuraciones derivadas y las emisiones · cotas del control · extremo a extremo por CLI.
"""
from __future__ import annotations
import csv, json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "scripts"))
import analizar as an  # noqa: E402
import analizar_3b as a3  # noqa: E402
import poblacion  # noqa: E402

U = {"0.05": -0.5694578968203694, "0.03": -0.5898535710336618, "0.01": -0.6223889502095352}
DESP = -0.5693969936322356
KALI, SRV, DNS = "10.10.20.30", "10.10.30.10", "10.10.10.20"
T0 = 1793502000.0                       # múltiplo de 10
INI, FIN = T0 + 0.5, T0 + 90.3           # episodio de ~90 s
EID = "inundacion_http-r1"
EP = {"escenario": "inundacion_http", "repeticion": 1, "destino": SRV, "inicio_ep": INI, "fin_ep": FIN,
      "estado": "completo"}
ok = {"n": 0}


def check(c, m):
    assert c, "FALLA: " + m
    ok["n"] += 1


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def reg(w, disp, score=-0.40, decision="PERMIT", heur=None, ip=KALI, pk=50):
    return {"entity_ip": ip, "window_end_utc": iso(w), "_wend": w, "_logged": disp, "_disp": disp,
            "_disp_fuente": "prueba", "_score": score, "_score_estado": "ok", "_pk10": pk, "decision": decision,
            "heuristico": {"heuristico": heur, "accion": "LIMIT"} if heur else None,
            "detector_name": "if_limpio_2026_10" if decision == "ALERT" else None, "threshold": DESP, "_ln": 1}


def anclas():
    """window_end de la Kali en (INI, FIN+60): T0+10 ... T0+150 (15 ventanas)."""
    return [T0 + 10 * i for i in range(1, 16)]


def escenario(senal_en=(), disp=lambda w: w + 20, quitar=(), extra=None, dest_override=None, alerta=False):
    vivo, inv, dest = {}, {}, {}
    for w in anclas():
        k = (KALI, iso(w))
        inv[k] = {"event": "decision"}
        if w not in quitar:
            sc = -0.70 if w in senal_en else -0.40
            vivo[k] = reg(w, disp(w), score=sc, decision="ALERT" if (alerta and w in senal_en) else "PERMIT")
        en_ataque = 30 if w - 60 < FIN else 0
        dest[(EID, iso(w))] = [{"destino": SRV, "paquetes_ventana": 30, "paquetes_en_intervalo_ataque": en_ataque}]
    if dest_override:
        dest.update(dest_override)
    I = {"desde": T0 - 1000, "hasta": T0 + 2000, "esperadas": inv, "no_evaluadas_en_referencia": {},
         "fuente": "prueba", "sha256": "-"}
    return vivo, I, dest


CAL_OK = {EID: {"estado": "completa"}}


def clas(vivo, inv, dest, ne=None, integ=True, cal=CAL_OK):
    return a3.clasificar_3b(EID, EP, KALI, U, vivo, ne or {}, inv, dest, integ, cal)


# --------------------------------------------------------------------------------------------- detección
def test_oportuna_y_posterior():
    w = T0 + 30
    vivo, inv, dest = escenario(senal_en={w})
    c = clas(vivo, inv, dest)
    check(c["en_poblacion_principal"], "observación completa")
    check(c["IF_0.05"]["categoria"] == "oportuna", "señal disponible antes del fin = oportuna")
    check(c["HEUR"]["categoria"] == "ausencia_con_observacion_suficiente", "HEUR sin señal = ausencia observada")
    vivo, inv, dest = escenario(senal_en={w}, disp=lambda x: x + 70 if x == w else x + 20)
    vivo[(KALI, iso(w))]["_disp"] = FIN + 5
    c = clas(vivo, inv, dest)
    check(c["IF_0.05"]["categoria"] == "solo_posterior", "señal disponible tras el fin = solo_posterior")
    check(c["IF_0.05"]["primera"]["disponible_desde_inicio_s"] > FIN - INI, "tiempo = disponibilidad")


def test_ventana_que_solapa_el_final():
    w = T0 + 140                                         # (w-60, w] = (T0+80, T0+140] solapa [INI, FIN]
    vivo, inv, dest = escenario(senal_en={w})
    c = clas(vivo, inv, dest)
    check(c["ventanas_esperadas"] == 15, "15 ventanas esperadas en (inicio, fin+60)")
    check(c["IF_0.05"]["categoria"] == "solo_posterior", "ventana que solapa el final: solo posterior")
    check(c["ventanas_wend_inicio_fin10"] == 10, "10 ventanas con window_end en [inicio, fin+10]")


def test_senal_no_atribuible_y_actividad_previa():
    w = T0 + 30
    vivo, inv, dest = escenario(senal_en={w}, dest_override={(EID, iso(w)): [
        {"destino": "10.10.10.30", "paquetes_ventana": 60, "paquetes_en_intervalo_ataque": 0}]})
    c = clas(vivo, inv, dest)
    check(c["IF_0.05"]["categoria"] == "ausencia_con_observacion_suficiente", "señal hacia otro destino no cuenta")
    check(c["IF_0.05"]["senales_no_atribuibles"][0]["atribucion"] == "otro_destino", "se informa no atribuible")
    vivo, inv, dest = escenario(senal_en={w}, dest_override={(EID, iso(w)): [
        {"destino": SRV, "paquetes_ventana": 5, "paquetes_en_intervalo_ataque": 0}]})
    c = clas(vivo, inv, dest)
    check(c["IF_0.05"]["senales_no_atribuibles"][0]["atribucion"] == "sin_actividad_del_ataque",
          "paquetes al destino solo antes del inicio: sin actividad del ataque")
    vivo, inv, dest = escenario(senal_en={w}, dest_override={(EID, iso(w)): [
        {"destino": "", "paquetes_ventana": 0, "paquetes_en_intervalo_ataque": 0}]})
    c = clas(vivo, inv, dest)
    check(c["en_poblacion_principal"], "fila sin paquetes (formato 3b) cuenta como evidencia de destino")
    check(c["IF_0.05"]["categoria"] == "ausencia_con_observacion_suficiente", "ventana sin paquetes no atribuible")
    vivo, inv, dest = escenario(senal_en={w}, dest_override={(EID, iso(w)): [
        {"destino": SRV, "paquetes_ventana": None, "paquetes_en_intervalo_ataque": None}]})
    c = clas(vivo, inv, dest)
    check(c["IF_0.05"]["senales_no_atribuibles"][0]["atribucion"] == "actividad_no_medida",
          "destino de formato 'a' (primera campaña): actividad no medida, no atribuible")


def test_tardia_ausente_no_evaluada():
    w_t, w_a, w_n = T0 + 40, T0 + 50, T0 + 60
    vivo, inv, dest = escenario(quitar={w_a, w_n})
    vivo[(KALI, iso(w_t))]["_disp"] = w_t + 75
    ne = {(KALI, iso(w_n)): {"_clave": (KALI, iso(w_n))}}
    check(a3.estado_ventana((KALI, iso(w_t)), vivo, ne, inv) == "decidida_tardia", "tardía si > 60 s")
    check(a3.estado_ventana((KALI, iso(w_a)), vivo, ne, inv) == "ausente", "esperada sin registro = ausente")
    check(a3.estado_ventana((KALI, iso(w_n)), vivo, ne, inv) == "no_evaluada", "evento explícito = no evaluada")
    check(a3.estado_ventana((KALI, iso(w_a)), vivo, ne, None) == "evidencia_insuficiente",
          "sin inventario no se puede afirmar ausencia")
    c = clas(vivo, inv, dest, ne=ne)
    check(not c["en_poblacion_principal"], "ausente/no evaluada => observación incompleta")
    check(all(c[k]["categoria"] == "no_evaluable" for k in an.CONFIGS), "falta de datos no es FN ni TN")
    e = a3.emisiones_episodio(EID, EP, KALI, vivo, dest, DESP, "if_limpio_2026_10")
    check(e["latencia_primera_oportuna_s"] is None, "sin emisión la latencia es None, no 0")
    vivo2, inv2, dest2 = escenario()
    vivo2[(KALI, iso(w_t))]["_disp"] = w_t + 75
    check(clas(vivo2, inv2, dest2)["en_poblacion_principal"], "una ventana tardía sigue decidida (cobertura)")


def test_observacion_parcial_y_fuente_degradada():
    w = T0 + 30
    vivo, inv, dest = escenario(senal_en={w}, quitar={T0 + 100})
    c = clas(vivo, inv, dest)
    check(not c["en_poblacion_principal"] and c["IF_0.05"]["categoria"] == "oportuna",
          "detección visible con observación parcial, fuera de la población principal")
    vivo, inv, dest = escenario(senal_en={w})
    c = clas(vivo, inv, dest, cal={EID: {"estado": "degradada"}})
    check(not c["en_poblacion_principal"] and "fuente degradada" in c["observacion"]["motivos"],
          "fuente degradada: fuera de la población")
    check(c["IF_0.05"]["categoria"] == "oportuna", "fuente degradada no anula una señal observada")
    c = clas(vivo, inv, dest, integ=None)
    check(not c["en_poblacion_principal"], "integridad desconocida: fuera de la población")
    vivo, inv, dest = escenario()
    c = clas(vivo, inv, dest, cal=None)
    check(c["HEUR"]["categoria"] == "no_evaluable", "sin calidad de fuentes no se afirma ausencia")


def test_configuraciones_vs_emisiones():
    w = T0 + 30
    vivo, inv, dest = escenario(senal_en={w}, alerta=False)
    c = clas(vivo, inv, dest)
    e = a3.emisiones_episodio(EID, EP, KALI, vivo, dest, DESP, "if_limpio_2026_10")
    check(c["IF_0.05"]["categoria"] == "oportuna" and e["emisiones"] == 0,
          "señal derivada sin ALERT ni heurístico registrado no es una emisión")
    vivo, inv, dest = escenario(senal_en={w}, alerta=True)
    e = a3.emisiones_episodio(EID, EP, KALI, vivo, dest, DESP, "if_limpio_2026_10")
    check(e["oportunas"] == 1 and e["latencia_primera_oportuna_s"] == round(w + 20 - INI, 2),
          "emisión real oportuna con latencia de disponibilidad")
    check(e["detalle"][0]["configuracion_emisora"] == "confirmada", "umbral registrado = desplegado")


def test_ciclos_sin_decisiones_y_huecos():
    cs = [{"inicio_ciclo": T0 + 10 * i, "registro_escrito_en": None if i in (2, 3) else T0 + 10 * i + 1,
           "decididas": 0 if i in (2, 3) else 5, "duracion_s": 1.0} for i in range(6)]   # hueco 11 -> 41 s
    r = a3.ciclos_resumen(cs)
    check(r["sin_decisiones"] == 2, "ciclos sin decisiones contados")
    check(len(r["huecos_escritura_mayores_20s"]) == 1, "hueco > 20 s informado")
    check("NO prueba pérdida" in r["significado"], "un hueco no se declara pérdida")
    vivo, inv, dest = escenario()
    check(a3.inventario_resumen(inv, vivo, {}, lambda ip: False)["estados"]["ausente"] == 0,
          "con inventario completo no hay ausentes aunque haya huecos")


def test_disponibilidad_por_ciclo():
    r = {"inicio_ciclo": 100.123456, "_logged": 104.0}
    q = {"inicio_ciclo": 999.0, "_logged": 1004.0}
    a3.disponibilidad([r, q], [{"inicio_ciclo": 100.123456, "registro_escrito_en": 105.5}])
    check(r["_disp"] == 105.5 and r["_disp_fuente"].startswith("registro_escrito_en"), "enlaza por inicio_ciclo")
    check(q["_disp"] == 1004.0 and q["_disp_fuente"].startswith("logged_at"), "sin ciclo: logged_at declarado")


# --------------------------------------------------------------------------------------------- población y control
def test_poblacion():
    p = poblacion.cargar_poblacion({"poblacion": {"excepciones_respuesta": [{"ip": DNS, "nota": "DNS/AD"}],
                                                  "exclusiones_poblacion": []}})
    check(not poblacion.excluida(DNS, p) and poblacion.excepcion_respuesta(DNS, p), "DNS: excepción, en población")
    p = poblacion.cargar_poblacion({"poblacion": {"exclusiones_poblacion": [
        {"ip": "10.10.40.0/24", "justificacion": "fuera de alcance (prueba)"}]}})
    check(poblacion.excluida("10.10.40.7", p), "exclusión justificada por red")
    for malo, msg in [({"poblacion": {"excepciones_respuesta": [{"ip": "10.10.10.20 (DNS)"}]}}, "IP anotada"),
                      ({"poblacion": {"excepciones_respuesta": [{"ip": "10.10.10.300"}]}}, "IP inválida"),
                      ({"poblacion": {"excepciones_respuesta": ["10.10.10.20"]}}, "cadena en vez de objeto"),
                      ({"poblacion": {"exclusiones_poblacion": [{"ip": DNS}]}}, "exclusión sin justificación"),
                      ({"poblacion": {"exclusiones_poblacion": [{"ip": "10.10.40.1/24", "justificacion": "x"}]}},
                       "red no estricta"),
                      ({"poblacion": {}, "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}, "dos formatos"),
                      ({"poblacion": {"otra": []}}, "clave desconocida")]:
        try:
            poblacion.cargar_poblacion(malo)
            check(False, f"debía rechazar: {msg}")
        except poblacion.ErrorPoblacion:
            check(True, msg)
    p = poblacion.cargar_poblacion({"combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": ["10.10.10.20 (DNS/AD)"]}}})
    check(p["exclusiones_poblacion"] == [] and p["excepciones_respuesta"][0]["nota"] == "DNS/AD",
          "formato anterior: todo a excepciones, sin exclusiones (conteos sin cambio)")


def test_control_poblacion_y_cotas():
    p = poblacion.cargar_poblacion({"poblacion": {"excepciones_respuesta": [{"ip": DNS, "nota": "DNS"}],
                                                  "exclusiones_poblacion": [
                                                      {"ip": "10.10.40.5", "justificacion": "prueba"}]}})
    vivo, esp = {}, {}
    for i in range(10):
        for ip in (DNS, "10.10.20.20", "10.10.40.5"):
            w = T0 + 10 * i
            k = (ip, iso(w)); esp[k] = {}
            if not (ip == "10.10.20.20" and i == 9):
                vivo[k] = reg(w, w + 15, score=-0.70 if (ip == DNS and i < 2) else -0.40, ip=ip)
    inv = {"desde": T0 - 100, "hasta": T0 + 1000, "esperadas": esp, "no_evaluadas_en_referencia": {},
           "fuente": "-", "sha256": "-"}
    c = a3.control_3b(vivo, {}, inv, T0, T0 + 90, U, p)
    # 2026-11-01 (corrección 3A-2): la salida separa tramo_cubierto / tramos_sin_inventario; mismas comprobaciones
    t = c["tramo_cubierto"]
    check(c["historico_fpr_control"]["ventanas"] == 19 and t["decididas"] == 19,
          "población: DNS dentro, excluida fuera (10 + 9)")
    check(t["IF_0.05"]["falsas_alarmas"] == 2, "señales del DNS cuentan (excepción no borra señales)")
    check(t["sin_decision"] == 1 and t["requeridas"] == 20, "inventario detecta la ventana sin decisión")
    check(t["IF_0.05"]["cotas_sobre_requeridas"]["max"] == round(3 / 20, 6), "cota superior con la ventana faltante")
    check(t["IF_0.05"]["cotas_sobre_requeridas"]["min"] == round(2 / 20, 6), "cota inferior sobre las requeridas")
    check(c["control_dentro_del_inventario"] is True and c["tramos_sin_inventario"] == [], "control cubierto entero")
    check(c["por_entidad"][DNS]["excepcion_respuesta"] is True, "desglose por entidad anota la excepción")
    check("no se adopta" in c["umbral_cobertura"], "sin umbral automático de cobertura")


# --------------------------------------------------------------------------------------------- correcciones 3A (2026-11-01)
def test_regresion_inventario_truncado():
    """3A-1: inventario que termina en T0+100 no puede dar observación completa con 10 de 15 ventanas."""
    vivo, inv, dest = escenario(senal_en={T0 + 30})
    inv["hasta"] = T0 + 100
    inv["esperadas"] = {k: v for k, v in inv["esperadas"].items() if an.ep_iso(k[1]) <= inv["hasta"]}
    c = clas(vivo, inv, dest)
    check(c["ventanas_requeridas"] == 15, "requeridas = 15 anclas aunque el inventario se corte")
    check(not c["cobertura_inventario"]["cubre"] and len(c["cobertura_inventario"]["fuera_del_inventario"]) == 5,
          "cobertura parcial identificada (5 anclas fuera)")
    check(not c["en_poblacion_principal"], "cobertura parcial no habilita la población principal")
    check(any("no cubre 5/15" in m for m in c["observacion"]["motivos"]), "motivo explícito")
    check(c["IF_0.05"]["categoria"] == "oportuna", "la señal observada se conserva con observación incompleta")
    check(c["HEUR"]["categoria"] == "no_evaluable", "sin señal y cobertura parcial: no evaluable, no ausencia")
    fuera = [v for v in c["ventanas"] if an.ep_iso(v["window_end_utc"]) > T0 + 100]
    check(all(v["estado"] in ("decidida_a_tiempo", "evidencia_insuficiente") for v in fuera),
          "ventanas fuera del inventario conservan su identidad")


def test_limites_temporales_rejilla():
    check(a3.anclas_rejilla(T0, T0 + 30) == [T0 + 10, T0 + 20], "ambos extremos abiertos sobre la rejilla")
    check(a3.anclas_rejilla(T0 + 0.5, T0 + 30.5) == [T0 + 10, T0 + 20, T0 + 30], "extremos fuera de la rejilla")
    check(len(a3.anclas_rejilla(INI, FIN + 60)) == 15, "episodio sintético: 15 anclas en (inicio, fin+60)")
    ep_r = dict(EP, inicio_ep=T0, fin_ep=T0 + 90)                       # inicio y fin+60 caen en la rejilla
    ks, _ = a3.ventanas_esperadas_episodio(ep_r, KALI, None, {})
    check(an.ep_iso(ks[0][1]) == T0 + 10 and an.ep_iso(ks[-1][1]) == T0 + 140,
          "window_end = inicio y = fin+60 quedan fuera (intervalo abierto)")
    for hasta, cubre in ((T0 + 150, True), (T0 + 149.9, False)):
        vivo, inv, dest = escenario(); inv["hasta"] = hasta
        check(a3.ventanas_esperadas_episodio(EP, KALI, inv, vivo)[1]["cubre"] is cubre,
              f"inventario hasta {hasta - T0:+} s: cubre={cubre}")
    for desde, cubre in ((T0 + 10, True), (T0 + 10.1, False)):
        vivo, inv, dest = escenario(); inv["desde"] = desde
        check(a3.ventanas_esperadas_episodio(EP, KALI, inv, vivo)[1]["cubre"] is cubre,
              f"inventario desde {desde - T0:+} s: cubre={cubre}")
    vivo, inv, dest = escenario(); inv["hasta"] = T0 + 150
    check(clas(vivo, inv, dest)["en_poblacion_principal"], "límite exacto en la última ancla: completa")


def test_regresion_no_evaluada_en_ambas_versiones():
    """3A-2: una ventana no evaluada en la referencia y en vivo sigue siendo requerida."""
    vivo, inv, dest = escenario()
    k = (KALI, iso(T0 + 60))
    inv["no_evaluadas_en_referencia"][k] = inv["esperadas"].pop(k)
    vivo.pop(k)
    ne = {k: {"_clave": k, "_wend": T0 + 60, "entity_ip": KALI}}
    c = clas(vivo, inv, dest, ne=ne)
    check(c["ventanas_requeridas"] == 15, "15 requeridas (no 14)")
    check(not c["en_poblacion_principal"], "requerida sin decisión: observación incompleta")
    v = [x for x in c["ventanas"] if x["window_end_utc"] == k[1]][0]
    check(v["estado"] == "no_evaluada" and v["estado_referencia"] == "no_evaluada", "identidad y estado conservados")
    r = a3.inventario_resumen(inv, vivo, ne, lambda ip: False)
    check(r["requeridas"] == 15 and r["decididas_en_vivo"] == 14 and r["cobertura_total"] == round(14 / 15, 6),
          "resumen global: la no evaluada en la referencia sigue en el denominador")
    check(r["no_evaluadas_en_referencia"]["no_evaluadas_en_vivo"] == 1, "se distingue no evaluada en ambas")
    # ausente en ambas: ni la referencia ni el vivo la registran
    vivo, inv, dest = escenario()
    inv["esperadas"].pop(k); vivo.pop(k)
    c = clas(vivo, inv, dest)
    v = [x for x in c["ventanas"] if x["window_end_utc"] == k[1]][0]
    check(c["ventanas_requeridas"] == 15 and v["estado"] == "ausente" and v["estado_referencia"] == "sin_registro",
          "ancla sin registro en ninguna versión: ausente, requerida")
    check(not c["en_poblacion_principal"], "ausente en ambas: observación incompleta")
    # no evaluada en la referencia pero decidida en vivo: cuenta como decidida
    vivo, inv, dest = escenario()
    inv["no_evaluadas_en_referencia"][k] = inv["esperadas"].pop(k)
    c = clas(vivo, inv, dest)
    check(c["en_poblacion_principal"], "no evaluada en la referencia y decidida en vivo: completa")


def test_control_parcialmente_cubierto_y_no_evaluadas():
    p = poblacion.cargar_poblacion({"poblacion": {"excepciones_respuesta": [], "exclusiones_poblacion": []}})
    vivo, esp, ne_ref, ne_vivo = {}, {}, {}, {}
    for i in range(10):                                       # window_end T0 .. T0+90
        w = T0 + 10 * i
        k = (DNS, iso(w))
        if i == 3:                                            # no evaluada en la referencia y en vivo
            ne_ref[k] = {}; ne_vivo[k] = {"_clave": k, "_wend": w, "entity_ip": DNS, "motivo": "x"}
        else:
            esp[k] = {}; vivo[k] = reg(w, w + 15, score=-0.70 if i in (1, 8) else -0.40, ip=DNS)
    inv = {"desde": T0, "hasta": T0 + 50, "esperadas": esp, "no_evaluadas_en_referencia": ne_ref,
           "fuente": "-", "sha256": "-"}
    c = a3.control_3b(vivo, ne_vivo, inv, T0, T0 + 90, U, p)
    t = c["tramo_cubierto"]
    check(t["intervalo_utc"] == [iso(T0), iso(T0 + 50)], "tramo cubierto explícito")
    check(t["requeridas"] == 6 and t["decididas"] == 5 and t["sin_decision"] == 1,
          "la no evaluada en ambas sigue en el denominador del tramo cubierto")
    check(t["IF_0.05"]["falsas_alarmas"] == 1 and t["IF_0.05"]["cotas_sobre_requeridas"] ==
          {"min": round(1 / 6, 6), "max": round(2 / 6, 6)}, "cotas sobre las requeridas del tramo")
    check(len(c["tramos_sin_inventario"]) == 1 and c["tramos_sin_inventario"][0]["intervalo_utc"] ==
          [iso(T0 + 60), iso(T0 + 90)], "tramo sin inventario separado")
    s = c["tramos_sin_inventario"][0]
    check(s["decididas_en_vivo"] == 4 and s["IF_0.05"]["falsas_alarmas"] == 1 and "no determinable" in s["cobertura"],
          "fuera del inventario: solo lo decidido en vivo, cobertura no determinable")
    check(c["control_dentro_del_inventario"] is False, "el control no se declara cubierto entero")
    check(t["decididas"] + s["decididas_en_vivo"] == c["historico_fpr_control"]["ventanas"],
          "tramos disjuntos que suman lo decidido en el intervalo declarado")


# --------------------------------------------------------------------------------------------- extremo a extremo
def test_cli_extremo_a_extremo():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "marcas.jsonl").write_text(
            json.dumps({"evento": "inicio", "episodio_id": EID, "escenario": "inundacion_http", "repeticion": 1,
                        "destino": SRV, "reloj": {"pared_utc": iso(INI)}}) + "\n" +
            json.dumps({"evento": "fin", "episodio_id": EID, "estado": "completo",
                        "reloj": {"pared_utc": iso(FIN)}}) + "\n", encoding="utf-8")
        mot, rep, cic = [], [], []
        for w in anclas():
            ic = w + 3
            r = {"event": "decision", "entity_ip": KALI, "window_end_utc": iso(w), "logged_at": w + 18,
                 "inicio_ciclo": ic, "decision": "ALERT" if w == T0 + 30 else "PERMIT",
                 "detector_name": "if_limpio_2026_10", "score": -0.7 if w == T0 + 30 else -0.4,
                 "threshold": DESP, "packet_count_10s": 40, "heuristico": None}
            mot.append(r); rep.append(r)
            cic.append({"event": "ciclo", "inicio_ciclo": ic, "registro_escrito_en": w + 19, "decididas": 1,
                        "duracion_s": 1.0})
        (d / "motor.log").write_text("\n".join(map(json.dumps, mot)) + "\n", encoding="utf-8")
        (d / "replay.log").write_text("\n".join(map(json.dumps, rep)) + "\n", encoding="utf-8")
        (d / "ciclos.jsonl").write_text("\n".join(map(json.dumps, cic)) + "\n", encoding="utf-8")
        with open(d / "dest.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["episodio_id", "window_end_utc", "destino", "paquetes_ventana",
                         "paquetes_en_intervalo_ataque"])
            for w in anclas():
                wr.writerow([EID, iso(w), SRV, 30, 30 if w - 60 < FIN else 0])
        (d / "integ.json").write_text(json.dumps({"episodios": [{"episodio_id": EID, "apto": True}]}))
        (d / "cal.json").write_text(json.dumps({"episodios": CAL_OK}))
        cfg = {"origen": KALI, "umbrales": {**U, "desplegado_referencia": DESP},
               "modelo": {"detector": "if_limpio_2026_10"},
               "poblacion": {"excepciones_respuesta": [{"ip": DNS}], "exclusiones_poblacion": []},
               "protocolo_3b": {"historia_s": 230}}
        (d / "cfg.json").write_text(json.dumps(cfg))
        rc = a3.main(["--marcas", str(d / "marcas.jsonl"), "--motor", str(d / "motor.log"), "--config",
                      str(d / "cfg.json"), "--ciclos", str(d / "ciclos.jsonl"), "--inventario",
                      str(d / "replay.log"), "--inventario-rango", f"{T0 - 300},{T0 + 400}", "--destinos",
                      str(d / "dest.csv"), "--integridad", str(d / "integ.json"), "--calidad-fuentes",
                      str(d / "cal.json"), "--salida", str(d / "out")])
        s = json.loads((d / "out" / "analisis-3b.json").read_text(encoding="utf-8"))
        c = s["episodios"][EID]
        check(rc == 0 and c["en_poblacion_principal"], "CLI: episodio en población principal")
        check(c["IF_0.05"]["categoria"] == "oportuna", "CLI: oportuna")
        check(c["emisiones_reales"]["oportunas"] == 1 and
              c["emisiones_reales"]["latencia_primera_oportuna_s"] == round(T0 + 49 - INI, 2),
              "CLI: latencia por registro_escrito_en del ciclo")
        check(s["inventario"]["estados"]["ausente"] == 0 and s["inventario"]["requeridas"] == 15,
              "CLI: inventario")
        check((d / "out" / "TABLA-3B.md").exists(), "CLI: tabla Markdown")


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f()
    print(f"OK: {ok['n']} comprobaciones")
