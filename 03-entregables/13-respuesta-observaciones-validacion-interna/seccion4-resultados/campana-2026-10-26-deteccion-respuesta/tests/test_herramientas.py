#!/usr/bin/env python3
"""Verificación SIN ataques de las herramientas de la campaña (no mide el desempeño de CyberFlow).

Usa fixtures con resultados conocidos. Ejecuta:  python3 tests/test_herramientas.py
Comprueba: validación de config (válida/ inválida, placeholders, destino fuera de lista), construcción de
comandos sin marcadores, simulación por defecto, timeout con muerte del grupo de procesos (hijos incluidos),
clasificación temporal por logged_at, separación emitido/derivado, duplicados/discontinuidades, control FPR y
métricas por ventana solo con etiquetas. α 0,01 (2026-10-28): lectura y procedencia del umbral completo, comparación
estricta, escala de anomalía, 7 configuraciones sin duplicar HEUR, no-regresión de 0,05/0,03 y anidamiento por α.
Todos los datos son sintéticos o fixtures: comprueban el CÓDIGO, no son resultados experimentales.
"""
from __future__ import annotations
import importlib.util, json, math, os, random, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SCRIPTS = AQUI.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import esquema_campana as esq  # noqa: E402


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, SCRIPTS / f"{nombre}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


U05, U03, U01 = -0.5694578968203694, -0.5898535710336618, -0.6223889502095352
UM = {"0.05": U05, "0.03": U03, "0.01": U01}
UDESP = -0.5693969936322356
ok = {"n": 0}


def check(cond, msg):
    assert cond, "FALLA: " + msg
    ok["n"] += 1


def iso(ep):
    return datetime.fromtimestamp(ep, timezone.utc).isoformat()


# --------------------------------------------------------------- 1. validación de config
def config_buena():
    return {"version_esquema": 2, "origen": "10.10.20.30",
            "lista_blanca_destinos": ["10.10.10.20", "10.10.30.10"], "semilla": 1, "repeticiones": 5,
            "tiempos_s": {"calentamiento_inicial": 60, "contexto_antes": 120, "observacion_despues": 90},
            "escenarios": [
                {"id": "dns_inusual", "habilitado": True, "destino": "10.10.10.20", "servicio": "UDP/53",
                 "herramienta": "dig", "duracion_objetivo_s": 90, "duracion_descripcion": "x", "timeout_s": 150,
                 "params": {"sleep_entre_consultas_s": 0.4, "zona_dns": "lab.test"}},
                {"id": "inundacion_http", "habilitado": True, "destino": "10.10.30.10", "servicio": "TCP/80",
                 "herramienta": "curl", "duracion_objetivo_s": 90, "duracion_descripcion": "x", "timeout_s": 150,
                 "params": {"concurrencia": 8, "max_time_s": 2, "recurso": "http://10.10.30.10/"}},
                {"id": "escaneo_breve", "habilitado": True, "destino": "10.10.30.10", "servicio": "TCP",
                 "herramienta": "nmap", "duracion_objetivo_s": None, "duracion_descripcion": "x", "timeout_s": 180,
                 "params": {"rango": "1-1000", "timing": "-T4", "max_retries": 1}},
                {"id": "escaneo_sostenido", "habilitado": True, "destino": "10.10.30.10", "servicio": "TCP",
                 "herramienta": "nmap", "duracion_objetivo_s": None, "duracion_descripcion": "x", "timeout_s": 900,
                 "params": {"rango": "1-65535", "timing": "-T4", "max_retries": 0, "max_rate": 1500}},
                {"id": "fuerza_bruta_http", "habilitado": True, "destino": "10.10.30.10", "servicio": "HTTP",
                 "herramienta": "curl", "duracion_objetivo_s": 90, "duracion_descripcion": "x", "timeout_s": 150,
                 "params": {"brute_puerto": 18081, "brute_ruta": "/auth", "usuario_ficticio": "fake", "max_time_s": 2}},
            ]}


def test_validacion():
    buena = config_buena()
    check(esq.validar(buena) == [], "la config buena debe validar sin problemas")
    # comandos de los 5, sin marcadores
    for s in buena["escenarios"]:
        cmd = esq.comando_de(buena, s)
        check(not any("<" in str(x) and ">" in str(x) for x in cmd), f"comando de {s['id']} sin marcadores")
    # inválidas
    c = config_buena(); c["escenarios"][2]["timeout_s"] = "natural (texto)"
    check(any("timeout_s" in p for p in esq.validar(c)), "debe rechazar timeout_s de texto (TypeError original)")
    c = config_buena(); c["escenarios"][0]["params"]["zona_dns"] = "<ZONA_LAB>"
    check(any("marcador" in p.lower() for p in esq.validar(c)), "debe rechazar marcador <ZONA_LAB>")
    c = config_buena(); c["escenarios"][1]["destino"] = "8.8.8.8"
    check(any("lista blanca" in p for p in esq.validar(c)), "debe rechazar destino fuera de la lista blanca")
    c = config_buena(); c["escenarios"][4]["params"]["brute_puerto"] = None
    check(any("brute_puerto" in p for p in esq.validar(c)), "debe rechazar brute_puerto nulo si está habilitado")
    c = config_buena(); c["tiempos_s"]["contexto_antes"] = 30
    check(any("contexto_antes" in p for p in esq.validar(c)), "debe exigir contexto_antes >= 120")


# --------------------------------------------------------------- 2. generador: simulación y timeout/hijos
def test_generador_simulacion():
    gen = cargar("generar_campana")
    with tempfile.TemporaryDirectory() as d:
        cfgp = Path(d) / "cfg.json"; cfgp.write_text(json.dumps(config_buena()), encoding="utf-8")
        sd = Path(d) / "out"
        sys.argv = ["x", "--config", str(cfgp), "--salida-dir", str(sd)]
        rc = gen.main()
        check(rc == 0, "simulación por defecto termina 0")
        marcas = (sd / "marcas.jsonl").read_text(encoding="utf-8").splitlines()
        inicios = [json.loads(x) for x in marcas if '"inicio"' in x]
        check(len(inicios) == 25, f"25 episodios de inicio en simulación (hay {len(inicios)})")
        check(all("simulado" not in json.dumps(i) for i in inicios), "simulación no marca fin (no hay tráfico)")
        check(not (sd / "salidas").exists() or not any((sd / "salidas").iterdir()),
              "simulación no crea salidas de procesos")
        # orden reproducible por semilla
        orden = [json.loads(x)["orden"] for x in marcas if '"campana_inicio"' in x][0]
        sys.argv = ["x", "--config", str(cfgp), "--salida-dir", str(Path(d) / "out2")]
        gen.main()
        orden2 = [json.loads(x)["orden"] for x in (Path(d) / "out2" / "marcas.jsonl").read_text().splitlines()
                  if '"campana_inicio"' in x][0]
        check(orden == orden2, "el orden es reproducible con la misma semilla")


def test_generador_timeout_mata_hijos():
    gen = cargar("generar_campana")
    cfg = config_buena()
    with tempfile.TemporaryDirectory() as d:
        testigo = (Path(d) / "hijo_vivo").as_posix()
        # padre que lanza un hijo; si el hijo sobrevive al timeout, crea el testigo a los 6 s (portable)
        hijo = Path(d) / "hijo.py"; hijo.write_text("import sys,time\ntime.sleep(6)\nopen(sys.argv[1],'w').close()\n")
        padre = Path(d) / "padre.py"; padre.write_text(
            "import subprocess,sys,time\nsubprocess.Popen([sys.executable,sys.argv[1],sys.argv[2]])\ntime.sleep(30)\n")
        orig = esq.comando_de
        esq.comando_de = lambda c, s: [sys.executable, str(padre), str(hijo), testigo]
        gen_esq = sys.modules["esquema_campana"]
        gen_esq.comando_de = esq.comando_de
        try:
            s = dict(cfg["escenarios"][1]); s["timeout_s"] = 2
            marcas = open(Path(d) / "m.jsonl", "a", encoding="utf-8")
            estado = gen.correr_episodio(cfg, s, 1, Path(d), marcas, autorizado=True)
            marcas.close()
            check(estado == "incompleto_timeout", f"timeout marca incompleto (fue {estado})")
            time.sleep(9)  # si el hijo sobrevivió al kill de grupo, crearía el testigo a los 6 s
            check(not os.path.exists(testigo), "el grupo de procesos (incluido el hijo) fue terminado")
            ev = [json.loads(x) for x in (Path(d) / "m.jsonl").read_text().splitlines()]
            check(any(e["evento"] == "inicio" for e in ev) and any(e["evento"] == "fin" for e in ev),
                  "inicio y fin se registran por separado")
        finally:
            esq.comando_de = orig; gen_esq.comando_de = orig


# --------------------------------------------------------------- 3. analizador
K = "10.10.20.30"


def rec(logged, wend_ep, score, decision="PERMIT", heur=None, pk10=5, det="if_limpio_2026_10", ip=K, thr=UDESP):
    # thr = umbral que REGISTRA el motor (el desplegado); no interviene en la detección comparativa
    return json.dumps({"event": "decision", "logged_at": logged, "entity_ip": ip, "window_end_utc": iso(wend_ep),
                       "score": score, "threshold": thr, "decision": decision, "packet_count_10s": pk10,
                       "history_coverage_s": 60, "detector_name": det, "heuristico": heur})


def marca(eid, esc, dst, ini, fin, estado="completo"):
    return [json.dumps({"evento": "inicio", "episodio_id": eid, "escenario": esc, "repeticion": 1,
                        "destino": dst, "reloj": {"pared_utc": iso(ini)}}),
            json.dumps({"evento": "fin", "episodio_id": eid, "estado": estado, "reloj": {"pared_utc": iso(fin)}})]


def clasif(an, lineas_marca, lineas_motor, eid, destinos=None, integridad_apto=None):
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "m").write_text("\n".join(lineas_marca), encoding="utf-8")
        (Path(d) / "x").write_text("\n".join(lineas_motor), encoding="utf-8")
        eps, _ = an.leer_marcas(Path(d) / "m")
        regs, inc, dups = an.leer_motor(Path(d) / "x")
        return an.clasificar(eps[eid], regs, K, UM, destinos, integridad_apto), regs, dups


def test_analizador_basico():
    an = cargar("analizar")
    T = 1793000000
    # episodio con cobertura CONTINUA (ventanas cada 10 s en [T, T+150]); IF+ALERT durante en T+40
    mot = []
    for w in range(T, T + 150, 10):
        mot.append(rec(w + 1, w, -0.70 if w == T + 40 else -0.50, "ALERT" if w == T + 40 else "PERMIT",
                       {"heuristico": "http_abuse", "accion": "LIMIT"} if w == T + 40 else None))
    mot.append(rec(T + 41, T + 40, -0.70, "ALERT", {"heuristico": "http_abuse", "accion": "LIMIT"}))  # duplicado
    # evidencia de destino COMPLETA: todas las ventanas del ataque (T+10..T+90) hacia el destino del escenario
    dok = {("inundacion_http-r1", iso(w)): ["10.10.30.10"] for w in range(T + 10, T + 91, 10)}
    c, regs, dups = clasif(an, marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                           "inundacion_http-r1", destinos=dok, integridad_apto=True)
    check(len(dups) == 1, f"detecta 1 ventana duplicada (hay {len(dups)})")
    check(c["evaluable"] and c["IF_0.05"]["categoria"] == "durante", "http-r1: evaluable y IF durante")
    check(c["IF_0.05"]["deteccion_confirmada"] is True, "detección con atribución confirmada")
    check(c["IF_0.05"]["desde_inicio_generador_s"] == 41.0, "clasifica por logged_at (41 s), no window_end")
    check(c["IF_0.05"]["base"].startswith("derivado"),
          "IF 0,05 recalibrado => derivado aunque el registro sea un ALERT del modelo (corregido 2026-10-28.2)")
    check(c["IF_0.05"]["evidencia_registrada"]["decision_registrada"] == "ALERT",
          "el ALERT registrado se conserva como evidencia de la ventana, no como procedencia de la configuración")
    check(c["IF_0.03"]["base"].startswith("derivado"), "IF 0,03 => derivado (umbral no desplegado)")
    # métricas por ventana solo con etiquetas; dedup evita doble conteo
    check(an.metricas_por_ventana(regs, {}, UM)["calculadas"] is False, "sin etiquetas: no métricas")
    m2 = an.metricas_por_ventana(regs, {(K, iso(T + 40)): "1", (K, iso(T + 50)): "0"}, UM)
    check(m2["IF_0.05"]["TP"] == 1 and m2["IF_0.05"]["FP"] == 0, "etiquetas conocidas: TP=1, FP=0")
    f = an.fpr_control(regs, T, T + 150, UM, set())
    check(f["denominador"] == f["ventanas"] and f["IF_0.05"]["falsas_alarmas"] >= 1, "control FPR con denominador")


def test_cobertura_una_ventana_insuficiente():
    an = cargar("analizar")
    T = 1793000000
    # motor CONTINUO gracias a otra entidad, pero la Kali solo tiene UNA ventana durante el ataque (90 s)
    mot = [rec(w + 1, w, -0.50, ip="10.10.40.10") for w in range(T, T + 150, 10)]
    mot.append(rec(T + 41, T + 40, -0.70, "ALERT"))   # única ventana de la Kali
    # destino e integridad OK para aislar que la ÚNICA causa de no-evaluable es la cobertura
    dok = {("inundacion_http-r9", iso(T + 40)): ["10.10.30.10"]}
    c, _, _ = clasif(an, marca("inundacion_http-r9", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                     "inundacion_http-r9", destinos=dok, integridad_apto=True)
    check(c["evaluable"] is False, "una sola ventana de la Kali NO es cobertura suficiente")
    check(c["cobertura"]["suficiente"] is False and "anclas" in c["cobertura"]["motivo"],
          "el motivo indica anclas de la Kali faltantes (pérdida)")
    check(c["IF_0.05"]["senal_observada"] is True and c["IF_0.05"]["categoria"] == "no_evaluable",
          "la señal existe aunque el episodio no sea íntegramente evaluable")
    check(c["IF_0.05"].get("primera_fiable") is False, "la primera detección NO es fiable sin cobertura")


def test_score_nulo_con_heuristico():
    an = cargar("analizar")
    T = 1793000000
    with tempfile.TemporaryDirectory() as d:
        mot = [rec(w + 1, w, -0.50) for w in range(T, T + 150, 10)]
        # ventana sin paquetes, score null y señal heurística (window_end distinto, sin choque de dedup)
        mot.append(rec(T + 501, T + 500, None, "PERMIT", {"heuristico": "dns_entropy", "accion": "LIMIT"}, pk10=0))
        (Path(d) / "x").write_text("\n".join(mot), encoding="utf-8")
        regs, inc, _ = an.leer_motor(Path(d) / "x")
        fila = [r for r in regs if r["window_end_utc"] == iso(T + 500)]
        check(len(fila) == 1, "la fila con score null NO se descarta")
        check(fila[0]["_score_estado"] == "no_aplicable", "score null = IF no aplicable (no error)")
        g = an.senales(fila[0], UM)
        check(g["HEUR"] and not g["IF_0.05"], "score null: HEUR dispara, IF no")
        check(not g["IF_0.01"] and g["HIB_0.01"], "score null: IF 0,01 no aplica; híbrido 0,01 = HEUR")


def _tabla8_e2e(an, tmp, destinos_csv, con_senal=True):
    """Recorre main() hasta analisis.json/TABLA8.md. destinos_csv=None => sin --destinos. Devuelve (tabla8, episodio)."""
    T = 1793000000
    d = Path(tmp)
    (d / "marcas.jsonl").write_text("\n".join(
        marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90)), encoding="utf-8")
    mot = [rec(w + 1, w, (-0.70 if (con_senal and w == T + 40) else -0.50),
               ("ALERT" if (con_senal and w == T + 40) else "PERMIT")) for w in range(T, T + 150, 10)]
    (d / "motor.log").write_text("\n".join(mot), encoding="utf-8")
    (d / "cfg.json").write_text(json.dumps({"umbrales": {"0.05": U05, "0.03": U03, "0.01": U01, "desplegado_referencia": UDESP},
                                            "origen": K, "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}),
                                encoding="utf-8")
    (d / "integ.json").write_text(json.dumps({"episodios": [{"episodio_id": "inundacion_http-r1", "apto": True}]}),
                                  encoding="utf-8")
    argv = ["x", "--marcas", str(d / "marcas.jsonl"), "--motor", str(d / "motor.log"),
            "--config", str(d / "cfg.json"), "--integridad", str(d / "integ.json"), "--salida", str(d / "out")]
    if destinos_csv is not None:
        (d / "dest.csv").write_text(destinos_csv, encoding="utf-8")
        argv += ["--destinos", str(d / "dest.csv")]
    old = sys.argv; sys.argv = argv
    try:
        an.main()
    finally:
        sys.argv = old
    j = json.loads((d / "out" / "analisis.json").read_text(encoding="utf-8"))
    return j["tabla8"]["Inundación HTTP"], j["episodios"]["inundacion_http-r1"]


def _csv_cubre(T, destino, eid="inundacion_http-r1"):
    filas = "".join(f"{eid},{iso(w)},{destino}\n" for w in range(T + 10, T + 91, 10))  # todas las ventanas del ataque
    return "episodio_id,window_end_utc,destino\n" + filas


def test_tabla8_evidencia_y_denominador():
    an = cargar("analizar")
    T = 1793000000
    # (caso, csv, con_senal) -> (num_esperado, evaluable_esperado, categoria_IF)
    casos = [
        ("sin --destinos", None, True, 0, False, "no_evaluable"),
        ("archivo vacío", "episodio_id,window_end_utc,destino\n", True, 0, False, "no_evaluable"),
        ("evidencia de otro episodio", "episodio_id,window_end_utc,destino\notro-r1," + iso(T + 40) + ",10.10.30.10\n",
         True, 0, False, "no_evaluable"),
        ("evidencia incompleta", "episodio_id,window_end_utc,destino\ninundacion_http-r1," + iso(T + 40) + ",10.10.30.10\n",
         True, 0, False, "no_evaluable"),
        ("completa con señal atribuible", _csv_cubre(T, "10.10.30.10"), True, 1, True, "durante"),
        ("completa sin señal atribuible", _csv_cubre(T, "10.10.30.10"), False, 0, True, "sin_deteccion"),
        ("señal hacia otro destino", _csv_cubre(T, "10.10.99.99"), True, 0, True, "sin_deteccion"),
    ]
    for nombre, csvd, con_senal, num, evaluable, cat_if in casos:
        with tempfile.TemporaryDirectory() as tmp:
            t8, epi = _tabla8_e2e(an, tmp, csvd, con_senal=con_senal)
            den = "inundacion_http-r1" in t8["evaluables"]
            check(t8["IF_0.05"] == num, f"{nombre}: numerador IF 0,05 = {num} (fue {t8['IF_0.05']})")
            check(den == evaluable, f"{nombre}: denominador/evaluable = {evaluable} (fue {den})")
            check(epi["IF_0.05"]["categoria"] == cat_if, f"{nombre}: categoría IF = {cat_if} (fue {epi['IF_0.05']['categoria']})")
            if not evaluable:
                check(epi["IF_0.05"]["categoria"] != "sin_deteccion",
                      f"{nombre}: evidencia ausente/incompleta NO se presenta como 'sin detección'")
            if nombre == "señal hacia otro destino":
                # la señal hacia otro destino se observa pero no cuenta como detección del ataque
                check(epi["IF_0.05"]["senal_observada"] is False, "señal a otro destino: excluida (no es este ataque)")


import hashlib
INI, FIN = 1793000000, 1793000090
EID = "inundacion_http-r1"


def _doc(d, nombre, **campos):
    """Escribe un respaldo/informe JSON (fixture de herramienta, NO captura de campaña) y devuelve su ruta."""
    base = {"campana": "c", "episodio": EID, "periodo": {"inicio": INI - 10, "fin": FIN + 100}, "origen": "local"}
    base.update(campos)
    p = Path(d) / nombre
    p.write_text(json.dumps(base), encoding="utf-8")
    return str(p)


def _fix_apto(d):
    """Descriptor APTO: 4 ficheros reales con hash + respaldos accesibles y correspondientes. Fixtures de herramienta."""
    archivos = {}
    for campo in ("pcap", "eve", "decisiones", "caracteristicas"):
        p = Path(d) / f"{campo}.bin"; p.write_bytes(campo.encode())
        archivos[campo] = {"ruta": str(p), "sha256": hashlib.sha256(campo.encode()).hexdigest()}
    cob = _doc(d, "cobertura.json", previa_s=130, durante_completa=True, posterior_s=95,
               continuidad_sin_huecos=True, faltantes=[])
    cap = _doc(d, "captura.json", paquetes_descartados=0, errores=[])
    rei = _doc(d, "reinicios.json", reinicios={})
    rel = _doc(d, "relojes.json", requeridos=["sensor"], tolerancia_s=1,
               mediciones=[{"host": "sensor", "referencia": "bastion/NTP", "momento": INI + 50,
                            "desfase_s": 0.1, "incertidumbre_s": 0.05}])
    return {"episodio_id": EID, "campana": "c", "intervalo": {"inicio": INI, "fin": FIN},
            "rutas": {k: v["ruta"] for k, v in archivos.items()},
            "hashes_esperados": {k: v["sha256"] for k, v in archivos.items()},
            "respaldos": {"cobertura": {"ruta": cob}, "captura": {"ruta": cap},
                          "reinicios": {"ruta": rei}, "relojes": {"ruta": rel}}}


def test_integridad_backing():
    vi = cargar("verificar_integridad")
    with tempfile.TemporaryDirectory() as d:
        # Evidencia local válida -> apto (todos verificado)
        ap = vi.evaluar_episodio(_fix_apto(d))
        check(ap["apto"] is True and len(ap["resumen"]["verificado"]) == 12, "evidencia local válida => apto (12 verificado)")
        # Cobertura declarada sin respaldo -> declarado_sin_verificar, no apto
        e = _fix_apto(d); del e["respaldos"]["cobertura"]; e["declaraciones"] = {"cobertura": True}
        r = vi.evaluar_episodio(e)
        check(r["requisitos"]["cobertura_previa"]["estado"] == "declarado_sin_verificar" and not r["apto"],
              "cobertura declarada sin respaldo => no apto")
        # Continuidad declarada sin respaldo -> no apto
        e = _fix_apto(d); del e["respaldos"]["cobertura"]; e["declaraciones"] = {"continuidad": True}
        check(vi.evaluar_episodio(e)["requisitos"]["continuidad"]["estado"] == "declarado_sin_verificar",
              "continuidad declarada sin respaldo => declarado_sin_verificar")
        # Respaldo cuyo contenido NO corresponde (otro episodio) -> ausente
        e = _fix_apto(d); e["respaldos"]["cobertura"]["ruta"] = _doc(d, "cob-otro.json", episodio="otro-r9",
                                                                     previa_s=130, durante_completa=True, posterior_s=95,
                                                                     continuidad_sin_huecos=True, faltantes=[])
        check(vi.evaluar_episodio(e)["requisitos"]["cobertura_previa"]["estado"] == "ausente",
              "respaldo de otro episodio => ausente (no corresponde)")
        # Respaldo de periodo que NO cubre el intervalo -> ausente
        e = _fix_apto(d); e["respaldos"]["relojes"]["ruta"] = _doc(d, "rel-perido.json",
                           periodo={"inicio": INI + 1000, "fin": FIN + 2000}, requeridos=["sensor"], tolerancia_s=1,
                           mediciones=[{"host": "sensor", "referencia": "b", "momento": INI + 50, "desfase_s": 0.1, "incertidumbre_s": 0.05}])
        check(vi.evaluar_episodio(e)["requisitos"]["relojes"]["estado"] == "ausente",
              "respaldo con periodo que no cubre => ausente")
        # Ficheros: hash inválido / marcador / no coincide -> ausente
        e = _fix_apto(d); e["hashes_esperados"]["pcap"] = "<sha256 real>"
        check(vi.evaluar_episodio(e)["requisitos"]["pcap"]["estado"] == "ausente", "marcador de hash => ausente")
        e = _fix_apto(d); e["hashes_esperados"]["eve"] = "0" * 64
        check(vi.evaluar_episodio(e)["requisitos"]["eve"]["estado"] == "ausente", "hash que no coincide => ausente")
        # Relojes sin mediciones en el respaldo -> desconocido
        e = _fix_apto(d); e["respaldos"]["relojes"]["ruta"] = _doc(d, "rel-sinmed.json", requeridos=["sensor"], tolerancia_s=1)
        check(vi.evaluar_episodio(e)["requisitos"]["relojes"]["estado"] == "desconocido",
              "respaldo de relojes con solo tolerancia => desconocido")
        # Reinicio sin historia suficiente -> ausente ; con recuperación+calentamiento -> verificado
        e = _fix_apto(d); e["respaldos"]["reinicios"]["ruta"] = _doc(d, "rei-malo.json",
                           reinicios={"captura": [{"recuperado": True, "historia_tras_s": 30, "calentamiento_s": 5}]})
        check(vi.evaluar_episodio(e)["requisitos"]["reinicios"]["estado"] == "ausente", "reinicio sin historia => ausente")
        e = _fix_apto(d); e["respaldos"]["reinicios"]["ruta"] = _doc(d, "rei-ok.json",
                           reinicios={"captura": [{"recuperado": True, "historia_tras_s": 150, "calentamiento_s": 30}]})
        check(vi.evaluar_episodio(e)["requisitos"]["reinicios"]["estado"] == "verificado", "reinicio recuperado => verificado")
        # Error de captura relevante -> ausente
        e = _fix_apto(d); e["respaldos"]["captura"]["ruta"] = _doc(d, "cap-err.json", paquetes_descartados=0,
                           errores=[{"afecta_fuentes": True, "desc": "PCAP truncado en el ataque"}])
        check(vi.evaluar_episodio(e)["requisitos"]["captura_sin_errores_relevantes"]["estado"] == "ausente",
              "error de captura relevante => ausente")


def test_integridad_informe_externo():
    vi = cargar("verificar_integridad")
    with tempfile.TemporaryDirectory() as d:
        base = _fix_apto(d)
        real = hashlib.sha256(b"pcap").hexdigest()
        # Informe externo ACCESIBLE y CORRESPONDIENTE con sha256 que coincide -> verificado
        ref_ok = _doc(d, "ev-ok.json", fuente="pcap", archivos={"pcap": {"sha256": real}})
        e = dict(base); e["rutas"] = {k: v for k, v in base["rutas"].items() if k != "pcap"}
        e["informe_externo"] = {"pcap": {"maquina": "sensor", "herramienta": "sha256sum", "resultado": "ok",
                                         "referencia": ref_ok, "sha256": real}}
        check(vi.evaluar_episodio(e)["requisitos"]["pcap"]["estado"] == "verificado",
              "informe externo accesible y correspondiente => verificado")
        # Referencia inexistente -> declarado_sin_verificar (pendiente)
        e2 = dict(e); e2["informe_externo"] = {"pcap": dict(e["informe_externo"]["pcap"], referencia=str(Path(d) / "no.json"))}
        check(vi.evaluar_episodio(e2)["requisitos"]["pcap"]["estado"] == "declarado_sin_verificar",
              "referencia externa inexistente => pendiente, no apto")
        # Referencia accesible cuyo contenido NO respalda (sin sha del archivo) -> ausente
        ref_mal = _doc(d, "ev-mal.json", fuente="pcap", archivos={})
        e3 = dict(e); e3["informe_externo"] = {"pcap": dict(e["informe_externo"]["pcap"], referencia=ref_mal)}
        check(vi.evaluar_episodio(e3)["requisitos"]["pcap"]["estado"] == "ausente",
              "referencia que no respalda el resultado => ausente")
        # Informe de OTRO episodio -> ausente
        ref_otro = _doc(d, "ev-otro.json", episodio="otro-r9", fuente="pcap", archivos={"pcap": {"sha256": real}})
        e4 = dict(e); e4["informe_externo"] = {"pcap": dict(e["informe_externo"]["pcap"], referencia=ref_otro)}
        check(vi.evaluar_episodio(e4)["requisitos"]["pcap"]["estado"] == "ausente",
              "informe de otro episodio => ausente")


def test_integridad_descriptor_ilustrativo():
    vi = cargar("verificar_integridad")
    # Descriptor sin ficheros ni respaldos (solo identificación) -> todo desconocido/declarado -> NO apto
    e = {"episodio_id": EID, "campana": "c", "intervalo": {"inicio": INI, "fin": FIN}}
    r = vi.evaluar_episodio(e)
    check(r["apto"] is False and not r["resumen"]["verificado"],
          "descriptor ilustrativo sin archivos => no apto (nada verificado)")


def test_integridad_gate_analizador():
    an = cargar("analizar")
    T = 1793000000
    mot = [rec(w + 1, w, -0.70 if w == T + 40 else -0.50, "ALERT" if w == T + 40 else "PERMIT")
           for w in range(T, T + 150, 10)]
    dok = {("inundacion_http-r1", iso(w)): ["10.10.30.10"] for w in range(T + 10, T + 91, 10)}
    c, _, _ = clasif(an, marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                     "inundacion_http-r1", destinos=dok, integridad_apto=False)
    check(c["evaluable"] is False and c["IF_0.05"]["categoria"] == "no_evaluable",
          "motor continuo + atribución confirmable pero integridad NO apta => no evaluable")
    c2, _, _ = clasif(an, marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                      "inundacion_http-r1", destinos=dok, integridad_apto=None)
    check(c2["evaluable"] is False, "integridad DESCONOCIDA (None) => no evaluable (desconocido != apto)")


def test_integridad_e2e_no_habilita_denominador():
    """verificar_integridad.py (no apto) -> integridad.json -> analizar.py: el episodio NO entra en el denominador."""
    vi = cargar("verificar_integridad"); an = cargar("analizar")
    T = 1793000000
    with tempfile.TemporaryDirectory() as d:
        # descriptor NO apto (cobertura declarada sin respaldo)
        e = _fix_apto(d); del e["respaldos"]["cobertura"]; e["declaraciones"] = {"cobertura": True}
        (Path(d) / "desc.json").write_text(json.dumps({"episodios": [e]}), encoding="utf-8")
        old = sys.argv; sys.argv = ["x", "--descriptor", str(Path(d) / "desc.json"), "--salida", str(Path(d) / "integ.json")]
        try:
            vi.main()
        finally:
            sys.argv = old
        rep = json.loads((Path(d) / "integ.json").read_text(encoding="utf-8"))
        check(rep["resumen"]["no_aptos"] == [EID], "integridad.json marca el episodio como NO apto")
        # analizar consume ese integridad.json
        (Path(d) / "marcas.jsonl").write_text("\n".join(marca(EID, "inundacion_http", "10.10.30.10", T, T + 90)), encoding="utf-8")
        mot = [rec(w + 1, w, -0.70 if w == T + 40 else -0.50, "ALERT" if w == T + 40 else "PERMIT") for w in range(T, T + 150, 10)]
        (Path(d) / "motor.log").write_text("\n".join(mot), encoding="utf-8")
        (Path(d) / "cfg.json").write_text(json.dumps({"umbrales": {"0.05": U05, "0.03": U03, "0.01": U01, "desplegado_referencia": UDESP},
                                                      "origen": K, "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}), encoding="utf-8")
        (Path(d) / "dest.csv").write_text("episodio_id,window_end_utc,destino\n"
                                          + "".join(f"{EID},{iso(w)},10.10.30.10\n" for w in range(T + 10, T + 91, 10)), encoding="utf-8")
        sys.argv = ["x", "--marcas", str(Path(d) / "marcas.jsonl"), "--motor", str(Path(d) / "motor.log"),
                    "--config", str(Path(d) / "cfg.json"), "--destinos", str(Path(d) / "dest.csv"),
                    "--integridad", str(Path(d) / "integ.json"), "--salida", str(Path(d) / "out")]
        try:
            an.main()
        finally:
            sys.argv = old
        j = json.loads((Path(d) / "out" / "analisis.json").read_text(encoding="utf-8"))
        t8 = j["tabla8"]["Inundación HTTP"]
        check(EID in t8["no_evaluables"] and EID not in t8["evaluables"] and t8["IF_0.05"] == 0,
              "integridad no apta => episodio fuera del denominador y numerador 0")


def test_integridad_gate_analizador():
    an = cargar("analizar")
    T = 1793000000
    mot = [rec(w + 1, w, -0.70 if w == T + 40 else -0.50, "ALERT" if w == T + 40 else "PERMIT")
           for w in range(T, T + 150, 10)]
    dok = {("inundacion_http-r1", iso(w)): ["10.10.30.10"] for w in range(T + 10, T + 91, 10)}
    c, _, _ = clasif(an, marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                     "inundacion_http-r1", destinos=dok, integridad_apto=False)
    check(c["evaluable"] is False and c["IF_0.05"]["categoria"] == "no_evaluable",
          "motor continuo + atribución confirmable pero integridad NO apta => no evaluable")
    c2, _, _ = clasif(an, marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                      "inundacion_http-r1", destinos=dok, integridad_apto=None)
    check(c2["evaluable"] is False, "integridad DESCONOCIDA (None) => no evaluable (desconocido != apto)")


def test_ventana_previa():
    an = cargar("analizar")
    T = 1793000000
    mot = [rec(w + 1, w, -0.50) for w in range(T, T + 150, 10)]
    # ventana PREVIA (window_end antes del inicio) pero emitida (logged_at) tras el inicio, con IF disparado
    mot.append(rec(T + 5, T - 10, -0.70, "ALERT"))
    c, _, _ = clasif(an, marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                     "inundacion_http-r1", destinos={}, integridad_apto=True)
    check(c["IF_0.05"]["categoria"] != "durante", "ventana previa emitida tras el inicio NO cuenta como 'durante'")
    previas = [p for p in c["senales_previas_o_ambiguas"] if p["relacion_temporal"] == "previa"]
    check(len(previas) >= 1, "la señal previa se informa aparte, sin forzar su clasificación")


def test_emitido_vs_derivado():
    """Expectativa corregida (2026-10-28.2): ninguna configuración comparativa es «emitida»; lo observado en el
    registro va en evidencia_registrada (y, en main, en emisiones_observadas)."""
    an = cargar("analizar")
    # ALERT solo por IF (modelo): la configuración IF_0.05 sigue siendo derivada; HEUR no
    g = an.senales({"_score": -0.70, "_pk10": 5, "decision": "ALERT", "detector_name": "if_limpio_2026_10",
                    "heuristico": None}, UM)
    check(g["IF_0.05"] and not g["HEUR"] and g["base"]["IF_0.05"].startswith("derivado")
          and g["evidencia_registrada"]["decision_registrada"] == "ALERT",
          "ALERT solo por IF: IF_0.05 derivado, el ALERT queda como evidencia registrada; HEUR no")
    # señal solo heurística (PERMIT): la evidencia dice que se registró en vivo; la configuración HEUR es derivada
    g = an.senales({"_score": -0.50, "_pk10": 5, "decision": "PERMIT", "detector_name": "if_limpio_2026_10",
                    "heuristico": {"heuristico": "http_abuse", "accion": "LIMIT"}}, UM)
    check(g["HEUR"] and not g["IF_0.05"] and g["base"]["HEUR"].startswith("derivado")
          and g["evidencia_registrada"]["heuristico_registrado"] == "http_abuse"
          and g["evidencia_registrada"]["decision_registrada"] == "PERMIT",
          "heurístico LIMIT en PERMIT: registrado en vivo (evidencia), sin ALERT; HEUR comparativo derivado")
    # compartida
    g = an.senales({"_score": -0.70, "_pk10": 5, "decision": "ALERT", "detector_name": "if_limpio_2026_10",
                    "heuristico": {"heuristico": "http_abuse", "accion": "LIMIT"}}, UM)
    check(g["IF_0.05"] and g["HEUR"] and g["HIB_0.05"], "señal compartida IF+HEUR")
    # alternativa no desplegada: IF_0.03 derivado; score intermedio dispara 0,05 y no 0,03
    g = an.senales({"_score": -0.58, "_pk10": 5, "decision": "PERMIT", "heuristico": None}, UM)
    check(g["IF_0.05"] and not g["IF_0.03"] and g["base"]["IF_0.03"].startswith("derivado"),
          "IF 0,03 es derivado (umbral no desplegado); -0.58 no lo dispara")
    # α 0,01: siempre derivado, aunque el modelo desplegado emitiera ALERT en esa ventana
    g = an.senales({"_score": -0.70, "_pk10": 5, "decision": "ALERT", "detector_name": "if_limpio_2026_10",
                    "heuristico": None}, UM)
    check(g["IF_0.01"] and g["base"]["IF_0.01"].startswith("derivado") and g["base"]["HIB_0.01"].startswith("derivado"),
          "IF 0,01 e híbrido 0,01 son derivados aunque el modelo emitiera ALERT")


# --------------------------------------------------------------- 4. α 0,01 (comprobaciones del código)
CAL = (AQUI.parent.parent / "4.1-modelos" / "calibracion-alfa-2026-10-24" / "umbrales-alfa-precision-completa.json")
CFG_REAL = AQUI.parent / "config-campana.json"


def test_umbral_001_procedencia():
    an = cargar("analizar")
    cfg = json.loads(CFG_REAL.read_text(encoding="utf-8"))
    U = an.umbrales_de(cfg)
    check(U["0.01"] == float("-0.6223889502095352") and repr(U["0.01"]) == "-0.6223889502095352",
          "config: umbral 0,01 leído con precisión completa (-0.6223889502095352)")
    check(repr(U["0.05"]) == "-0.5694578968203694" and repr(U["0.03"]) == "-0.5898535710336618",
          "config: umbrales 0,05 y 0,03 conservados")
    check(cfg["umbrales"]["desplegado_referencia"] == UDESP and UDESP != U["0.05"],
          "el umbral desplegado (65 633) se conserva y es distinto del 0,05 recalibrado (65 553)")
    col = json.loads(CAL.read_text(encoding="utf-8"))["umbrales_full_precision"]["validacion_sin_kali_65553"]
    for a, k in (("0.05", "0.050"), ("0.03", "0.030"), ("0.01", "0.010")):
        check(float(col[k]) == U[a], f"umbral {a} == calibración 4.1 [validacion_sin_kali_65553][{k}] (igualdad exacta)")
    p = an.verificar_procedencia(cfg, CFG_REAL, U)
    check(p["estado"] == "verificada" and p["sha256_coincide_con_config"], "procedencia verificada (valores y sha256)")
    # config con 0,01 distinto de la calibración => aborta (no clasifica con un umbral sin procedencia)
    malo = json.loads(json.dumps(cfg)); malo["umbrales"]["0.01"] = -0.62238895
    try:
        an.verificar_procedencia(malo, CFG_REAL, an.umbrales_de(malo)); abortó = False
    except SystemExit:
        abortó = True
    check(abortó, "umbral 0,01 redondeado (-0.62238895) != calibración => aborta")
    # sin 0,01, o como texto: aborta (sin valor por defecto)
    for v in (None, "-0.6223889502095352"):
        c = {"umbrales": {"0.05": U05, "0.03": U03, **({} if v is None else {"0.01": v})}}
        try:
            an.umbrales_de(c); abortó = False
        except SystemExit:
            abortó = True
        check(abortó, f"umbral 0,01 {'ausente' if v is None else 'de texto'} => aborta (sin valor por defecto)")


def test_comparacion_estricta():
    an = cargar("analizar")
    for a, u in UM.items():
        en = an.senales({"_score": u, "_pk10": 5, "decision": "PERMIT", "heuristico": None}, UM)
        bajo = an.senales({"_score": math.nextafter(u, -math.inf), "_pk10": 5, "decision": "PERMIT",
                           "heuristico": None}, UM)
        check(not en[f"IF_{a}"], f"score == umbral {a} NO genera señal IF (estricto)")
        check(bajo[f"IF_{a}"], f"score 1 ULP por debajo del umbral {a} SÍ genera señal IF")
    # un valor que solo dispararía con el umbral redondeado a 8 decimales no dispara con el completo
    r8 = round(U01, 8)                       # -0.62238895 > U01
    entre = (r8 + U01) / 2                   # U01 < entre < r8
    check(U01 < entre < r8 and not an.senales({"_score": entre, "_pk10": 5}, UM)["IF_0.01"],
          "score entre el umbral completo y el redondeado: no hay señal 0,01 (no se usa el redondeado)")


def test_escala_anomalia():
    an = cargar("analizar")
    check(an.umbral_escala_anomalia(U01) == 0.6223889502095352, "umbral_anomalia 0,01 = -umbral = 0.6223889502095352")
    check(an.umbral_escala_anomalia(U01) != 0.6223889502095351,
          "no se usa el cuantil recalculado en escala de anomalía (difiere 1 ULP)")
    rng = random.Random(20261028)
    scores = [rng.uniform(-0.75, -0.45) for _ in range(5000)] + [U05, U03, U01] + \
             [math.nextafter(u, s) for u in (U05, U03, U01) for s in (-math.inf, math.inf)]
    for a, u in UM.items():
        ua = an.umbral_escala_anomalia(u)
        check(all((s < u) == ((-s) > ua) for s in scores),
              f"α {a}: score < umbral <=> anomalía > umbral_anomalía en {len(scores)} scores (incl. fronteras)")


def _e2e_siete(an, tmp):
    T = 1793000000
    d = Path(tmp)
    (d / "marcas.jsonl").write_text("\n".join(marca(EID, "inundacion_http", "10.10.30.10", T, T + 90)), encoding="utf-8")
    sc = {T + 30: -0.60, T + 50: -0.63}      # 0,05+0,03 / los tres
    mot = [rec(w + 1, w, sc.get(w, -0.50), "ALERT" if sc.get(w, 0) < UDESP else "PERMIT",
               {"heuristico": "http_abuse", "accion": "LIMIT"} if w == T + 70 else None) for w in range(T, T + 150, 10)]
    (d / "motor.log").write_text("\n".join(mot), encoding="utf-8")
    (d / "cfg.json").write_text(json.dumps({"umbrales": {**UM, "desplegado_referencia": UDESP}, "origen": K,
                                            "modelo": {"detector": "if_limpio_2026_10"},
                                            "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}), encoding="utf-8")
    (d / "integ.json").write_text(json.dumps({"episodios": [{"episodio_id": EID, "apto": True}]}), encoding="utf-8")
    (d / "dest.csv").write_text(_csv_cubre(T, "10.10.30.10"), encoding="utf-8")
    old = sys.argv
    sys.argv = ["x", "--marcas", str(d / "marcas.jsonl"), "--motor", str(d / "motor.log"), "--config", str(d / "cfg.json"),
                "--destinos", str(d / "dest.csv"), "--integridad", str(d / "integ.json"),
                "--control", f"{T},{T + 150}", "--salida", str(d / "out")]
    try:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            an.main()
    finally:
        sys.argv = old
    return (json.loads((d / "out" / "analisis.json").read_text(encoding="utf-8")),
            (d / "out" / "TABLA8.md").read_text(encoding="utf-8"))


def test_siete_configuraciones():
    an = cargar("analizar")
    ORDEN = ["IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01"]
    check(list(an.CONFIGS) == ORDEN and list(esq.CONFIGS) == ORDEN, "CONFIGS = 7 en el orden pedido (analizar y esquema)")
    with tempfile.TemporaryDirectory() as tmp:
        j, md = _e2e_siete(an, tmp)
    t8 = j["tabla8"]["Inundación HTTP"]
    check([k for k in t8 if k not in ("evaluables", "no_evaluables")] == ORDEN, "tabla8: 7 columnas en orden")
    check(j["configuraciones"] == ORDEN, "analisis.json declara las 7 configuraciones en orden")
    cab = [l for l in md.splitlines() if l.startswith("| Familia")][0]
    check([c.strip() for c in cab.strip("|").split("|")][2:] ==
          ["IF 0,05", "IF 0,03", "IF 0,01", "Heurísticos", "Híbrido 0,05", "Híbrido 0,03", "Híbrido 0,01"],
          "TABLA8.md: cabecera con las 7 columnas en orden")
    check("-0.6223889502095352" in md and "-0.5693969936322356" in md,
          "TABLA8.md muestra el umbral 0,01 completo y el desplegado, por separado")
    claves_heur = [k for k in j["episodios"][EID] if "HEUR" in k]
    check(claves_heur == ["HEUR"], f"HEUR una sola vez por episodio, sin variantes por α (hay {claves_heur})")
    epi = j["episodios"][EID]
    check(t8["IF_0.05"] == t8["IF_0.03"] == t8["IF_0.01"] == 1 and t8["HEUR"] == 1, "fixture: 0,05/0,03/0,01 y HEUR durante")
    check(epi["IF_0.05"]["window_end_utc"] == iso(T0 + 30) and epi["IF_0.01"]["window_end_utc"] == iso(T0 + 50),
          "primera señal atribuible por α: 0,05 en T+30, 0,01 en T+50 (score -0.60 no dispara 0,01)")
    check(all(epi[c]["tiempo_significado"].startswith("disponibilidad_del_registro") for c in ORDEN
              if epi[c]["categoria"] == "durante") and all("tiempo_es_emision_real" not in epi[c] for c in ORDEN),
          "las 7 configuraciones: tiempo = disponibilidad del registro (ninguna se presenta como emisión real)")
    p = epi["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"]
    check(p is not None and p["window_end_utc"] == iso(T0 + 30) and p["desde_inicio_generador_s"] == 31.0,
          "la latencia real sale aparte: primera alerta del IF desplegado en T+30 (logged_at T+31)")
    comp = epi["compartidas_durante_0.01"]
    check(comp["solo_IF_0.01"] == 1 and comp["solo_HEUR"] == 1 and comp["ambos_0.01"] == 0,
          "solapamiento/exclusivas 0,01 sobre ventanas confirmadas (solo_IF=1, solo_HEUR=1)")
    f = j["control_normal_fpr"]
    check(all(c in f for c in ORDEN) and f["IF_0.01"]["falsas_alarmas"] == 1 and f["denominador"] == f["ventanas"],
          "control FPR con las 7 configuraciones y denominador explícito")
    check(j["umbrales"]["orden_respetado"] is True and j["umbrales"]["0.01_recalibrado"] == U01,
          "analisis.json: orden de umbrales respetado y umbral 0,01 completo")


T0 = 1793000000


def test_no_regresion_005_003():
    """Detección y cobertura idénticas a los analizadores anteriores (0d40bdb: 5 configs; a6dc5ab: 7 configs).
    Solo se excluyen las claves de procedencia/etiquetado temporal documentadas en regresion_alfa.CLAVES_PROCEDENCIA."""
    import regresion_alfa as rg
    an = cargar("analizar")
    j = rg.correr(an)
    for n in (5, 7):
        ref = rg.sin_procedencia(json.loads(rg.GOLDEN[n].read_text(encoding="utf-8")))
        dif = rg.diferencias(ref, rg.proyeccion(j, n))
        check(not dif, f"{n} configs: detección/cobertura idénticas al golden anterior: " + "; ".join(dif[:3]))
        check(len(ref["episodios"]) == 5 and any(e["evaluable"] for e in ref["episodios"].values()),
              f"golden {n}: 5 episodios con evaluables (no es una comparación vacía)")
    check(set(rg.CLAVES_PROCEDENCIA) == {"base", "tiempo_es_emision_real", "tiempo_significado",
                                         "evidencia_registrada"},
          "las exclusiones de la comparación son solo las de procedencia/etiquetado temporal")


def test_anidamiento_por_alfa():
    an = cargar("analizar")
    check(an.orden_umbrales(UM), "los umbrales de la config respetan u_0.01 <= u_0.03 <= u_0.05")
    rng = random.Random(7)
    filas = [{"_score": (None if rng.random() < 0.05 else rng.uniform(-0.72, -0.50)), "_pk10": rng.choice([0, 5, 5, 5]),
              "decision": "PERMIT", "heuristico": ({"heuristico": "x"} if rng.random() < 0.1 else None)}
             for _ in range(5000)] + [{"_score": u, "_pk10": 5} for u in UM.values()]
    S = {c: {i for i, r in enumerate(filas) if an.senales(r, UM)[c]} for c in an.CONFIGS}
    check(S["IF_0.01"] <= S["IF_0.03"] <= S["IF_0.05"], "IF: señales 0,01 ⊆ 0,03 ⊆ 0,05 (mismos scores)")
    check(S["HIB_0.01"] <= S["HIB_0.03"] <= S["HIB_0.05"], "híbrido: 0,01 ⊆ 0,03 ⊆ 0,05")
    check(len(S["IF_0.01"]) < len(S["IF_0.03"]) < len(S["IF_0.05"]), "los subconjuntos no son triviales")
    malo = {"0.05": U05, "0.03": U01, "0.01": U03}
    check(not an.orden_umbrales(malo), "umbrales en orden invertido: se detecta (no se afirma el anidamiento)")


# --------------------------------------------------------------- 5. procedencia: derivadas vs emisiones observadas
# Comprobaciones del CÓDIGO con registros sintéticos (no son resultados experimentales).
def _e2e_mot(an, mot, modelo=True):
    """Episodio inundacion_http-r1 [T, T+90] con evidencia de destino completa e integridad apta; devuelve analisis."""
    T = T0
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "marcas.jsonl").write_text("\n".join(marca(EID, "inundacion_http", "10.10.30.10", T, T + 90)),
                                        encoding="utf-8")
        (d / "motor.log").write_text("\n".join(mot), encoding="utf-8")
        cfg = {"umbrales": {**UM, "desplegado_referencia": UDESP}, "origen": K,
               "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}
        if modelo:
            cfg["modelo"] = {"detector": "if_limpio_2026_10"}
        (d / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
        (d / "integ.json").write_text(json.dumps({"episodios": [{"episodio_id": EID, "apto": True}]}), encoding="utf-8")
        (d / "dest.csv").write_text(_csv_cubre(T, "10.10.30.10"), encoding="utf-8")
        old = sys.argv
        sys.argv = ["x", "--marcas", str(d / "marcas.jsonl"), "--motor", str(d / "motor.log"),
                    "--config", str(d / "cfg.json"), "--destinos", str(d / "dest.csv"),
                    "--integridad", str(d / "integ.json"), "--salida", str(d / "out")]
        try:
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                an.main()
        finally:
            sys.argv = old
        return json.loads((d / "out" / "analisis.json").read_text(encoding="utf-8"))


def _mot(especial):
    """Ventanas cada 10 s en [T, T+150] con score -0.50 PERMIT, salvo {window_end: kwargs de rec}."""
    return [rec(w + 1, w, **especial.get(w, {"score": -0.50})) for w in range(T0, T0 + 150, 10)]


def test_procedencia_emisiones():
    an = cargar("analizar")
    T = T0
    # 1) ALERT real del IF desplegado que cruza los tres umbrales: las 7 configuraciones siguen siendo derivadas y la
    #    emisión real se registra aparte, con sus campos
    j = _e2e_mot(an, _mot({T + 40: {"score": -0.70, "decision": "ALERT"}}))
    e = j["episodios"][EID]
    check(all(e[c]["categoria"] == "durante" for c in ("IF_0.05", "IF_0.03", "IF_0.01")),
          "caso 1: -0.70 cruza los tres umbrales (clasificación comparativa durante)")
    check(all(e[c]["base"].startswith("derivado") and e[c]["tiempo_significado"].startswith("disponibilidad")
              for c in ("IF_0.05", "IF_0.03", "IF_0.01", "HIB_0.05")),
          "caso 1: las clasificaciones siguen siendo derivadas (base y tiempo)")
    em = j["emisiones_observadas"]["registros"]
    check(len(em) == 1 and em[0]["componente_emisor"] == "IF_desplegado" and em[0]["tipo"] == "alerta_emitida"
          and em[0]["decision_emitida"] == "ALERT", "caso 1: una emisión real, del IF desplegado, ALERT")
    x = em[0]
    check(x["logged_at_utc"] == iso(T + 41) and x["window_end_utc"] == iso(T + 40),
          "caso 1: logged_at y window_end diferenciados")
    check(x["modelo_registrado"] == "if_limpio_2026_10" and x["score_registrado"] == -0.70
          and x["configuracion_emisora"]["umbral_registrado"] == UDESP
          and x["configuracion_emisora"]["estado"] == "confirmada", "caso 1: modelo, score y umbral REGISTRADOS")
    check(x["episodio_id"] == EID and x["relacion_temporal"] == "durante_actividad" and x["atribucion_confirmada"]
          and x["atribucion"] == "origen+destino", "caso 1: relación con el episodio y atribución origen+destino")
    check(x["registro_id"].startswith("motor:") and x["respaldo"]["linea"] == 5 and len(x["respaldo"]["sha256"]) == 64,
          "caso 1: referencia al registro de respaldo (línea + sha256 del log)")
    check("emisiones_observadas" not in j["tabla8"]["Inundación HTTP"] and j["configuraciones"] == list(an.CONFIGS),
          "caso 1: la emisión NO es una octava configuración de la Tabla 8")
    check(e["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"]["desde_inicio_generador_s"]
          == 41.0, "caso 1: latencia real = logged_at de la emisión - inicio (41 s)")
    # 2) score entre el 0,05 desplegado y el 0,05 recalibrado: alerta real SIN señal en IF_0.05 recalibrado
    s = -0.56942
    check(U05 < s < UDESP, "caso 2: el score está entre el recalibrado (-0.569458) y el desplegado (-0.569397)")
    j = _e2e_mot(an, _mot({T + 40: {"score": s, "decision": "ALERT"}}))
    e = j["episodios"][EID]
    check(e["IF_0.05"]["categoria"] == "sin_deteccion" and j["tabla8"]["Inundación HTTP"]["IF_0.05"] == 0,
          "caso 2: IF_0.05 recalibrado sin señal (Tabla 8 = 0)")
    p = e["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"]
    check(p is not None and p["window_end_utc"] == iso(T + 40),
          "caso 2: la alerta real del desplegado existe y se registra aparte")
    # 3) clasificación alternativa positiva SIN emisión: no se inventa alerta ni latencia real
    j = _e2e_mot(an, _mot({T + 40: {"score": -0.63, "decision": "PERMIT"}}))
    e = j["episodios"][EID]
    check(e["IF_0.01"]["categoria"] == "durante" and j["emisiones_observadas"]["registros"] == []
          and e["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"] is None,
          "caso 3: IF_0.01 positivo derivado, sin emisión ni latencia real inventadas")
    # 4) heurístico registrado en vivo (PERMIT): procedencia heurística, no emisión del IF
    j = _e2e_mot(an, _mot({T + 40: {"score": -0.50, "heur": {"heuristico": "dns_entropy", "accion": "LIMIT"}}}))
    e = j["episodios"][EID]
    x = j["emisiones_observadas"]["registros"]
    check(e["HEUR"]["categoria"] == "durante" and e["HEUR"]["evidencia_registrada"]["heuristico_registrado"]
          == "dns_entropy" and e["HEUR"]["base"].startswith("derivado"),
          "caso 4: HEUR comparativo derivado; la evidencia conserva el heurístico registrado en vivo")
    check(len(x) == 1 and x[0]["componente_emisor"] == "heuristico:dns_entropy"
          and x[0]["tipo"].startswith("senal_heuristica_registrada") and x[0]["decision_emitida"] == "PERMIT"
          and x[0]["accion_heuristica_registrada"] == "LIMIT", "caso 4: evento heurístico observado, sin ALERT")
    check(e["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"] is None,
          "caso 4: no se atribuye una emisión del IF a un heurístico")
    # 5) identificación insuficiente: se declara desconocido, no se rellena con el valor esperado
    casos = [("ALERT sin detector_name", {"score": -0.70, "decision": "ALERT", "det": None}, True),
             ("umbral no registrado", {"score": -0.70, "decision": "ALERT", "thr": None}, True),
             ("umbral registrado != desplegado", {"score": -0.70, "decision": "ALERT", "thr": U05}, True),
             ("config sin modelo.detector", {"score": -0.70, "decision": "ALERT"}, False)]
    for nombre, kw, modelo in casos:
        j = _e2e_mot(an, _mot({T + 40: kw}), modelo=modelo)
        x = j["emisiones_observadas"]["registros"][0]
        ce = x["configuracion_emisora"]
        e = j["episodios"][EID]
        check(ce["estado"] == "desconocida" and "configuracion" not in ce,
              f"caso 5 ({nombre}): configuración DESCONOCIDA, sin rellenar")
        check(e["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"] is None
              and e["emisiones_observadas"]["eventos_con_emisor_o_configuracion_desconocida"] == 1,
              f"caso 5 ({nombre}): no hay latencia real; la incertidumbre se cuenta")
        check(e["IF_0.05"]["categoria"] == "durante", f"caso 5 ({nombre}): la clasificación comparativa no cambia")
        if nombre in ("umbral no registrado",):
            check(ce["umbral_registrado"].startswith("desconocido"), "caso 5: umbral ausente => 'desconocido'")
        if nombre == "umbral registrado != desplegado":
            check(ce["umbral_registrado"] == U05, "caso 5: se informa el umbral REGISTRADO, no el esperado")
        if nombre in ("ALERT sin detector_name", "config sin modelo.detector"):
            check(x["componente_emisor"] == "desconocido" and x.get("motivo_emisor_desconocido"),
                  f"caso 5 ({nombre}): emisor desconocido con motivo (no se atribuye al IF)")


def _sin_clave(lineas, w, clave):
    """Elimina REALMENTE la clave del JSON de la ventana w (no la reemplaza por null)."""
    out = []
    for x in lineas:
        r = json.loads(x)
        if r["window_end_utc"] == iso(w):
            del r[clave]
        out.append(json.dumps(r))
    return out


def test_umbral_registrado_ausente():
    """Registro de decisión sin la clave threshold: se conserva como evidencia incompleta (comprobación del CÓDIGO)."""
    an = cargar("analizar")
    T = T0
    alerta = {T + 40: {"score": -0.70, "decision": "ALERT"}}
    completo = _mot(alerta)
    sin_thr = _sin_clave(completo, T + 40, "threshold")
    check('"threshold"' not in sin_thr[4] and "threshold" not in json.loads(sin_thr[4]),
          "ausente: la línea de la alerta no contiene la clave threshold (ni como null)")
    j_ok, j = _e2e_mot(an, completo), _e2e_mot(an, sin_thr)
    em = j["emisiones_observadas"]["registros"]
    check(len(em) == 1 and em[0]["decision_emitida"] == "ALERT" and em[0]["componente_emisor"] == "IF_desplegado"
          and em[0]["score_registrado"] == -0.70 and em[0]["logged_at_utc"] == iso(T + 41)
          and em[0]["window_end_utc"] == iso(T + 40) and em[0]["modelo_registrado"] == "if_limpio_2026_10",
          "ausente: la alerta permanece en emisiones_observadas con decisión, emisor, score y tiempos")
    x = em[0]
    check(x["respaldo"]["linea"] == 5 and len(x["respaldo"]["sha256"]) == 64 and x["registro_id"] == "motor:5",
          "ausente: conserva la referencia al registro original (línea + sha256)")
    inc = j["calidad_datos"]["incidencias_motor"]
    check(any(s.startswith("motor:5 (") and "motor.log" in s and "falta la clave 'threshold'" in s for s in inc)
          and x["incidencias_registro"] == ["falta la clave 'threshold'"],
          "ausente: incidencia explícita con archivo y línea, también en la emisión")
    ce = x["configuracion_emisora"]
    check(ce["umbral_registrado"] == "desconocido (el registro no contiene la clave threshold)"
          and ce["umbral_registrado_estado"] == "clave_ausente" and ce["estado"] == "desconocida"
          and "configuracion" not in ce and ce["coherencia_score_umbral"] is None,
          "ausente: umbral y configuración DESCONOCIDOS (ni desplegado, ni esperado, ni calculado)")
    eo = j["episodios"][EID]["emisiones_observadas"]
    check(eo["primera_alerta_IF_desplegado_confirmada_durante"] is None
          and eo["eventos_con_emisor_o_configuracion_desconocida"] == 1 and eo["registros"] == ["motor:5"],
          "ausente: no es la primera alerta confirmada del IF desplegado; la incertidumbre se cuenta")
    e, e_ok = j["episodios"][EID], j_ok["episodios"][EID]
    check(all(str(e[c].get("base")).startswith("derivado") for c in ("IF_0.05", "IF_0.03", "IF_0.01", "HIB_0.05"))
          and not any(str(e[c].get("base", "")).startswith("emitido") for c in an.CONFIGS)
          and j["configuraciones"] == list(an.CONFIGS),
          "ausente: las siete configuraciones siguen siendo derivadas")
    check(all(e[c] == e_ok[c] for c in an.CONFIGS) and e["IF_0.01"]["categoria"] == "durante"
          and e["cobertura"] == e_ok["cobertura"] and e["evaluable"] == e_ok["evaluable"] is True
          and j["tabla8"] == j_ok["tabla8"],
          "ausente: clasificaciones comparativas, cobertura y Tabla 8 iguales que con el registro completo")
    # el registro completo mantiene su resultado y no genera incidencia
    ok_x = j_ok["emisiones_observadas"]["registros"][0]
    check(ok_x["configuracion_emisora"]["estado"] == "confirmada" and "incidencias_registro" not in ok_x
          and ok_x["configuracion_emisora"]["umbral_registrado_estado"] == "numerico"
          and not j_ok["calidad_datos"]["incidencias_motor"]
          and j_ok["episodios"][EID]["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"]
          ["desde_inicio_generador_s"] == 41.0, "completo: confirmada, sin incidencia, latencia real 41 s")
    # null: se distingue de la ausencia en el diagnóstico; la incertidumbre es la misma
    j_n = _e2e_mot(an, _mot({T + 40: {"score": -0.70, "decision": "ALERT", "thr": None}}))
    cn = j_n["emisiones_observadas"]["registros"][0]["configuracion_emisora"]
    check(cn["umbral_registrado_estado"] == "null" and cn["umbral_registrado"] == "desconocido (threshold registrado como null)"
          and cn["estado"] == "desconocida" and cn["umbral_registrado"] != ce["umbral_registrado"],
          "null: diagnóstico distinto de la clave ausente, igual de desconocido")
    check(j_n["episodios"][EID]["emisiones_observadas"]["primera_alerta_IF_desplegado_confirmada_durante"] is None
          and all(j_n["episodios"][EID][c] == e_ok[c] for c in an.CONFIGS),
          "null: sin latencia confirmada; clasificaciones comparativas iguales")
    # no se aceptan registros sin otros campos imprescindibles
    for falta in ("logged_at", "window_end_utc", "decision", "entity_ip", "packet_count_10s"):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.log"
            p.write_text("\n".join(_sin_clave(sin_thr, T + 40, falta)), encoding="utf-8")
            regs, incs, _ = an.leer_motor(p)
        check(len(regs) == 14 and any(s.startswith("motor:5: faltan claves") and falta in s for s in incs),
              f"sin {falta}: el registro se descarta con incidencia (el requisito no se relaja)")


def test_conteos_cobertura_7_sin_cambios():
    """Comparación directa con el analizador de a6dc5ab si está disponible (CF_ANALIZADOR_PREVIO); siempre con el
    golden de 7 configuraciones."""
    import regresion_alfa as rg
    an = cargar("analizar")
    j = rg.correr(an)
    ref = rg.sin_procedencia(json.loads(rg.GOLDEN[7].read_text(encoding="utf-8")))
    act = rg.proyeccion(j, 7)
    check(not rg.diferencias(ref["tabla8"], act["tabla8"]), "Tabla 8 (7 configs) igual que en a6dc5ab")
    check(all(ref["episodios"][e][k] == act["episodios"][e][k] for e in ref["episodios"]
              for k in ("evaluable", "cobertura", "evidencia_destino")), "evaluabilidad y cobertura iguales")
    check(all(ref["episodios"][e][c]["categoria"] == act["episodios"][e][c]["categoria"]
              for e in ref["episodios"] for c in rg.CONFIGS[7]), "categorías por episodio y configuración iguales")
    check(ref["control_normal_fpr"] == act["control_normal_fpr"] and
          ref["metricas_por_ventana"] == act["metricas_por_ventana"], "control FPR y métricas por ventana iguales")
    prev = os.environ.get("CF_ANALIZADOR_PREVIO")
    if prev and Path(prev).is_file():
        jp = rg.correr(rg.cargar_analizador(Path(prev)))
        check(not rg.diferencias(rg.proyeccion(jp, 7), act), "comparación directa con el analizador previo: 0 dif.")


# --------------------------------------------------------------- 6. ventana_no_evaluada (#59)
# Fixtures de CÓDIGO (no resultados experimentales): eventos del motor corregido (producto 7b275b8) sin decisión.
OTRA = "10.10.20.21"   # perfil legítimo sintético (control)


def noev(logged, wend_ep, motivo="pcap_incompleto", ip=K, **extra):
    ciclo = logged - 1 if isinstance(logged, (int, float)) else wend_ep
    r = {"event": "ventana_no_evaluada", "logged_at": logged, "entity_ip": ip, "window_end_utc": iso(wend_ep),
         "motivo": motivo, "pendiente_desde": wend_ep + 2, "inicio_ciclo": ciclo,
         "marca_pcap": wend_ep - 5, "marca_eve": ciclo, "pcaps_ilegibles": 0, **extra}
    return json.dumps({k: v for k, v in r.items() if v is not ...})


def _sin(mot, *wends):
    """Quita las decisiones de la Kali con esos window_end (la ventana no tuvo decisión)."""
    return [x for x in mot if json.loads(x)["window_end_utc"] not in {iso(w) for w in wends}]


def _e2e_ne(an, mot, control=None, etiquetas=None):
    """Como _e2e_mot (episodio EID [T0, T0+90], destino completo, integridad apta) con --control y --etiquetas."""
    import contextlib, io
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "marcas.jsonl").write_text("\n".join(marca(EID, "inundacion_http", "10.10.30.10", T0, T0 + 90)),
                                        encoding="utf-8")
        (d / "motor.log").write_text("\n".join(mot), encoding="utf-8")
        (d / "cfg.json").write_text(json.dumps({"umbrales": {**UM, "desplegado_referencia": UDESP}, "origen": K,
                                                "modelo": {"detector": "if_limpio_2026_10"},
                                                "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}),
                                    encoding="utf-8")
        (d / "integ.json").write_text(json.dumps({"episodios": [{"episodio_id": EID, "apto": True}]}), encoding="utf-8")
        (d / "dest.csv").write_text(_csv_cubre(T0, "10.10.30.10"), encoding="utf-8")
        argv = ["x", "--marcas", str(d / "marcas.jsonl"), "--motor", str(d / "motor.log"), "--config",
                str(d / "cfg.json"), "--destinos", str(d / "dest.csv"), "--integridad", str(d / "integ.json"),
                "--salida", str(d / "out")]
        if control:
            argv += ["--control", f"{control[0]},{control[1]}"]
        if etiquetas:
            (d / "et.csv").write_text("entity_ip,window_end_utc,etiqueta\n" + "\n".join(
                f"{ip},{iso(w)},{y}" for (ip, w), y in etiquetas.items()) + "\n", encoding="utf-8")
            argv += ["--etiquetas", str(d / "et.csv")]
        old = sys.argv; sys.argv = argv
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                an.main()
        finally:
            sys.argv = old
        return (json.loads((d / "out" / "analisis.json").read_text(encoding="utf-8")),
                (d / "out" / "TABLA8.md").read_text(encoding="utf-8"))


def test_ventanas_no_evaluadas():
    import regresion_alfa as rg
    an = cargar("analizar")
    T = T0
    base = _mot({})
    j0, _ = _e2e_ne(an, base, control=(T, T + 200))
    # 0) sin eventos: claves nuevas neutras; el resto, igual (la regresión de goldens lo cubre aparte)
    jf = rg.correr(an)
    c0, m0 = jf["control_normal_fpr"], jf["metricas_por_ventana"]
    check(c0["ventanas_no_evaluadas"] == 0 and c0["cobertura_evaluada"] == 1.0
          and c0["ventanas_no_evaluadas_por_motivo"] == {} and m0["etiquetadas_no_evaluadas"] == 0
          and m0["cobertura_etiquetadas"] == 1.0 and jf["calidad_datos"]["ventanas_no_evaluadas"]["contadas"] == 0
          and jf["ventanas_no_evaluadas"]["contadas"] == 0 and jf["ventanas_no_evaluadas"]["registros"] == []
          and all(e["ventanas_no_evaluadas"] == {"n": 0, "ventanas_del_ataque": 0,
                                                 "ventanas_posteriores_que_solapan": 0, "detalle": [],
                                                 "efecto": "ninguno"} for e in jf["episodios"].values())
          and all("anclas_no_evaluadas" not in e["cobertura"] for e in jf["episodios"].values()),
          "sin eventos: 0 no evaluadas, cobertura 1,0 y cobertura/episodios sin claves nuevas")
    check(set(rg.CLAVES_NO_EVALUADAS).isdisjoint(rg.CLAVES_PROCEDENCIA)
          and not any(k in c0 for k in ("TN", "FN")), "exclusiones de #59 separadas de las de procedencia")
    check(j0["episodios"][EID]["evaluable"] is True and j0["tabla8"]["Inundación HTTP"]["evaluables"] == [EID],
          "base sintética: el episodio es evaluable sin eventos")

    # 1) evento ESCRITO tras el ataque (logged T+220 > fin T+90) cuya ventana (T-10, T+50] solapa el ataque;
    #    episodio sin detección y con cobertura insuficiente
    mot1 = _sin(base, T + 50) + [noev(T + 220, T + 50)]
    j1, md1 = _e2e_ne(an, mot1)
    jperd, _ = _e2e_ne(an, _sin(base, T + 50))               # misma ancla sin ningún registro (pérdida)
    e1 = j1["episodios"][EID]; v1 = e1["ventanas_no_evaluadas"]
    check(e1["evaluable"] is False and e1["cobertura"]["suficiente"] is False
          and e1["cobertura"]["anclas_no_evaluadas"] == 1 and e1["cobertura"]["anclas_sin_registro"] == 0
          and "1 registradas como ventana_no_evaluada (pcap_incompleto)" in e1["cobertura"]["motivo"],
          "ventana del ataque no evaluada: cobertura insuficiente con motivo distinto de la pérdida")
    check(v1["ventanas_del_ataque"] == 1 and v1["detalle"][0]["escrito"] == "tras_fin"
          and v1["detalle"][0]["escrito_tras_fin_s"] == 130.0
          and v1["detalle"][0]["relacion_ventana"] == "ventana_del_ataque"
          and v1["detalle"][0]["intervalo_ventana_utc"] == [iso(T - 10), iso(T + 50)],
          "se relaciona por el intervalo de la ventana, no por el instante de escritura (130 s tras el fin)")
    check(all(e1[c]["categoria"] == "no_evaluable" and e1[c]["senal_observada"] is False for c in an.CONFIGS)
          and all(v1["por_configuracion"][c]["estado"] == "ausencia_no_establecible"
                  and v1["por_configuracion"][c]["ausencia_establecible"] is False for c in an.CONFIGS)
          and "ningún α" in v1["por_configuracion"]["IF_0.01"]["motivo"]
          and "no se supone que no" in v1["por_configuracion"]["HEUR"]["motivo"],
          "sin detección y cobertura insuficiente: no evaluable, nunca 'sin_deteccion' ni ausencia confirmada")
    check(j1["tabla8"] == jperd["tabla8"] and j1["tabla8"]["Inundación HTTP"]["evaluables"] == []
          and e1["evaluable"] == jperd["episodios"][EID]["evaluable"]
          and "anclas_no_evaluadas" not in jperd["episodios"][EID]["cobertura"]
          and "(pérdida de datos)" in jperd["episodios"][EID]["cobertura"]["motivo"],
          "Tabla 8 y denominador iguales que con la misma ancla perdida: el evento no cambia la comparación")
    check("## Ventanas no evaluadas" in md1 and "| inundacion_http-r1 | 1 | 0 | no |" in md1,
          "TABLA8.md lista el episodio afectado")

    # 2) detección confirmada (IF ALERT T+40) + OTRA ventana del ataque no evaluada (T+70)
    mot2 = _sin(_mot({T + 40: {"score": -0.70, "decision": "ALERT"}}), T + 70) + [noev(T + 85, T + 70)]
    j2, md2 = _e2e_ne(an, mot2)
    e2 = j2["episodios"][EID]; pc2 = e2["ventanas_no_evaluadas"]["por_configuracion"]
    check(e2["evaluable"] is False and e2["IF_0.05"]["deteccion_confirmada"] is True
          and e2["IF_0.05"]["categoria"] == "no_evaluable" and pc2["IF_0.05"]["estado"] == "deteccion_confirmada_visible"
          and pc2["HIB_0.05"]["estado"] == "deteccion_confirmada_visible"
          and pc2["HEUR"]["estado"] == "ausencia_no_establecible"
          and e2["ventanas_no_evaluadas"]["detalle"][0]["escrito"] == "durante_actividad",
          "detección confirmada visible; HEUR (sin positivo) queda desconocido; el híbrido la prueba por el IF")
    dfu = j2["ventanas_no_evaluadas"]["detecciones_confirmadas_en_episodios_no_evaluables"]
    check(len(dfu) == 1 and dfu[0]["episodio_id"] == EID and "IF_0.05" in dfu[0]["configuraciones_con_deteccion_confirmada"]
          and "HEUR" not in dfu[0]["configuraciones_con_deteccion_confirmada"]
          and j2["tabla8"]["Inundación HTTP"]["IF_0.05"] == 0 and "Detección confirmada fuera de la comparación" in md2,
          "la detección se lista aparte y no entra en el numerador de la Tabla 8 (denominador común)")

    # 3) evento FUERA del periodo relevante (ventana T+400) y ventana posterior que solapa (T+120, fin=T+90)
    mot3 = _sin(base, T + 120) + [noev(T + 570, T + 400), noev(T + 290, T + 120)]
    j3, _ = _e2e_ne(an, mot3)
    e3 = j3["episodios"][EID]; v3 = e3["ventanas_no_evaluadas"]
    cob3, cob0 = e3["cobertura"], j0["episodios"][EID]["cobertura"]
    check(e3["evaluable"] is True and j3["tabla8"] == j0["tabla8"] and cob3["suficiente"] is True
          and cob3["anclas_ataque_observadas"] == cob0["anclas_ataque_observadas"] and "anclas_no_evaluadas" not in cob3
          and v3["n"] == 1 and v3["ventanas_posteriores_que_solapan"] == 1 and v3["ventanas_del_ataque"] == 0
          and all(v3["por_configuracion"][c]["estado"] == "posterior_incompleta" for c in an.CONFIGS)
          and "ninguno sobre la evaluabilidad" in v3["efecto_en_evaluabilidad"],
          "ventana que solapa solo el final: no excluye el episodio; deja incompleta la relación posterior")
    fuera = [r for r in j3["ventanas_no_evaluadas"]["registros"] if r["window_end_utc"] == iso(T + 400)][0]
    check(fuera["relacion_episodios"] == "fuera_de_episodio" and j3["ventanas_no_evaluadas"]["contadas"] == 2,
          "evento fuera del periodo: se cuenta como calidad, sin efecto sobre el episodio")

    # 4) control con ventanas no evaluadas (perfil legítimo): no son TN ni FP; denominador explícito
    mot4 = base + [rec(w + 1, w, -0.50, ip=OTRA) for w in range(T, T + 150, 10) if w not in (T + 60, T + 70, T + 80)]
    mot4 += [noev(T + 230, T + 60, "ventana_no_regenerada", ip=OTRA), noev(T + 240, T + 70, "otro_motivo", ip=OTRA),
             noev(T + 250, T + 80, None, ip=OTRA)]
    j4, md4 = _e2e_ne(an, mot4, control=(T, T + 200))
    c4, c0b = j4["control_normal_fpr"], j0["control_normal_fpr"]
    check(c4["ventanas"] == c4["denominador"] == 27 and c4["ventanas_no_evaluadas"] == 3
          and c4["cobertura_evaluada"] == round(27 / 30, 6)
          and c4["ventanas_no_evaluadas_por_motivo"] == {"desconocido (motivo ausente)": 1, "otro_motivo": 1,
                                                          "ventana_no_regenerada": 1},
          "control: 27 evaluadas + 3 no evaluadas; cobertura 0,9; motivos separados")
    check(all(c4[c]["falsas_alarmas"] == c0b[c]["falsas_alarmas"] and c4[c]["tasa"] == round(
        c4[c]["falsas_alarmas"] / 27, 6) for c in an.CONFIGS) and "no son TN" in c4["denominador_significado"],
          "las no evaluadas no son TN ni FP: tasa sobre las 27 evaluadas, rotulada")
    r4 = {r["motivo"]: r for r in j4["ventanas_no_evaluadas"]["registros"]}
    inc4 = j4["ventanas_no_evaluadas"]["incidencias"]
    check(r4["ventana_no_regenerada"]["motivo_estado"] == "reconocido"
          and r4["otro_motivo"]["motivo_estado"] == "no_reconocido"
          and r4["desconocido (motivo ausente)"]["motivo_estado"] == "ausente"
          and any("motivo no reconocido 'otro_motivo'" in s for s in inc4)
          and any("motivo ausente" in s for s in inc4)
          and all(r["relacion_episodios"].startswith("otra_entidad") for r in r4.values())
          and "Control: cobertura 0.9 (3 no evaluadas)" in md4,
          "motivos conocido, no reconocido y ausente: se conservan con diagnóstico explícito")
    check(not any(k in r for r in r4.values() for k in ("score", "decision", "etiqueta", "senal"))
          and all(set(r["disponibilidad"]) == set(an.CAMPOS_DISPONIBILIDAD) and r["respaldo"]["linea"] > 0
                  and len(r["respaldo"]["sha256"]) == 64 for r in r4.values()),
          "sin score/decisión/etiqueta inventados; disponibilidad y respaldo (línea + sha256) conservados")

    # 5) métricas por ventana: la no evaluada etiquetada no es FN
    j5, _ = _e2e_ne(an, _sin(_mot({T + 40: {"score": -0.70, "decision": "ALERT"}}), T + 50) + [noev(T + 220, T + 50)],
                    etiquetas={(K, T + 40): 1, (K, T + 50): 1, (K, T + 60): 0})
    m5 = j5["metricas_por_ventana"]["IF_0.05"]
    check(j5["metricas_por_ventana"]["denominador"] == 2 and j5["metricas_por_ventana"]["etiquetadas_no_evaluadas"] == 1
          and j5["metricas_por_ventana"]["cobertura_etiquetadas"] == round(2 / 3, 6)
          and m5["TP"] == 1 and m5["FN"] == 0 and m5["TN"] == 1 and m5["FP"] == 0,
          "métricas: la ventana positiva no evaluada no cuenta como FN; denominador 2 de 3 rotulado")

    # 6) duplicados y conflicto con una decisión de la misma clave
    mot6 = _sin(base, T + 50) + [noev(T + 220, T + 50), noev(T + 230, T + 50, "ventana_no_regenerada"),
                                 noev(T + 231, T + 60)]                    # T+60 SÍ tiene decisión
    j6, _ = _e2e_ne(an, mot6)
    b6 = j6["ventanas_no_evaluadas"]
    est = sorted(r["estado_en_analisis"] for r in b6["registros"])
    check(b6["contadas"] == 1 and len(b6["duplicados"]) == 1 and len(b6["duplicados"][0]["registros"]) == 2
          and b6["duplicados"][0]["motivos"] == ["pcap_incompleto", "ventana_no_regenerada"]
          and est == ["conflicto_con_decision", "contada", "duplicado_no_contado"],
          "duplicado: se cuenta una vez y se conservan ambos registros con sus motivos")
    check(len(b6["conflictos"]) == 1 and b6["conflictos"][0]["registro_decision"].startswith("motor:")
          and "prevalece la decisión" in b6["conflictos"][0]["regla"]
          and j6["episodios"][EID]["cobertura"]["anclas_no_evaluadas"] == 1
          and j6["episodios"][EID]["ventanas_no_evaluadas"]["n"] == 1
          and any(s.startswith("conflicto ") for s in b6["incidencias"]),
          "conflicto decisión/no evaluada: prevalece la decisión, el evento no se cuenta, queda registrado")
    check(j6["configuraciones"] == list(an.CONFIGS) == ["IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05",
                                                        "HIB_0.03", "HIB_0.01"]
          and list(j6["episodios"][EID]["ventanas_no_evaluadas"]["por_configuracion"]) == list(an.CONFIGS),
          "siete configuraciones en su orden")

    # 7) campos ausentes o inválidos con diagnóstico explícito
    malos = [noev(T + 220, T + 50, window_end_utc=...), noev("abc", T + 70), noev(T + 670, T + 500, marca_pcap="x")]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "m.log"
        p.write_text("\n".join(base + malos), encoding="utf-8")
        regs, inc_dec, _ = an.leer_motor(p)
        b7 = an.leer_no_evaluadas(p, regs, {"archivo": "m.log", "sha256": "0" * 64})
    check(len(regs) == 15 and not inc_dec, "las decisiones no cambian ni heredan incidencias de los eventos")
    check(len(b7["vigentes"]) == 1 and b7["vigentes"][0]["window_end_utc"] == iso(T + 500)
          and any(s.startswith("motor:16: ventana_no_evaluada: faltan claves ['window_end_utc']") for s in b7["incidencias"])
          and any(s.startswith("motor:17: ventana_no_evaluada: valor inválido") for s in b7["incidencias"])
          and b7["vigentes"][0]["diagnosticos"] == ["marca_pcap no numérico ('x')"]
          and b7["vigentes"][0]["marca_pcap_menos_window_end_s"] is None,
          "sin window_end o con logged_at inválido: no se cuenta, con incidencia motor:línea; campo de "
          "disponibilidad no numérico: se conserva con diagnóstico")


def test_no_evaluada_real_compatibilidad():
    """Evento REAL de la preparación (out_p38, candidato, 28-oct): solo compatibilidad de lectura. No se le asigna
    etiqueta, atribución ni efecto experimental."""
    an = cargar("analizar")
    src = AQUI.parent / "preparacion-2026-10-28" / "salidas" / "out_p38_sensor_noevaluada.txt"
    largo = Path("\\\\?\\" + str(src)) if os.name == "nt" else src   # ruta > 260 caracteres en Windows
    lineas = [x.strip() for x in largo.read_text(encoding="utf-8").splitlines()
              if x.strip().startswith("{") and '"ventana_no_evaluada"' in x]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "m.log"
        p.write_text("\n".join(lineas), encoding="utf-8")
        b = an.leer_no_evaluadas(p, [], {"archivo": str(src.name), "sha256": "-"})
    check(len(lineas) == 1 and len(b["vigentes"]) == 1 and not b["incidencias"], "out_p38: un evento, sin incidencias")
    e = b["vigentes"][0]
    check(e["entity_ip"] == "10.10.20.23" and e["window_end_utc"] == "2026-10-28T07:57:30+00:00"
          and e["motivo"] == "pcap_incompleto" and e["motivo_estado"] == "reconocido"
          and e["campos_disponibilidad_ausentes"] == [] and e["espera_desde_pendiente_s"] == 172.6
          and e["marca_pcap_menos_window_end_s"] == 163.3 and e["escrito_tras_window_end_s"] == 175.8,
          "out_p38: campos leídos tal cual (motivo registrado por el candidato; marca_pcap 163 s tras la ventana)")
    check(not any(k in e for k in ("score", "decision", "etiqueta", "atribucion")),
          "out_p38: sin etiqueta, atribución ni decisión inventadas")


def main():
    for fn in (test_validacion, test_generador_simulacion, test_generador_timeout_mata_hijos,
               test_analizador_basico, test_cobertura_una_ventana_insuficiente, test_score_nulo_con_heuristico,
               test_tabla8_evidencia_y_denominador, test_ventana_previa, test_emitido_vs_derivado,
               test_integridad_backing, test_integridad_informe_externo, test_integridad_descriptor_ilustrativo,
               test_integridad_gate_analizador, test_integridad_e2e_no_habilita_denominador,
               test_umbral_001_procedencia, test_comparacion_estricta, test_escala_anomalia,
               test_siete_configuraciones, test_no_regresion_005_003, test_anidamiento_por_alfa,
               test_procedencia_emisiones, test_umbral_registrado_ausente, test_conteos_cobertura_7_sin_cambios,
               test_ventanas_no_evaluadas, test_no_evaluada_real_compatibilidad):
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{ok['n']} comprobaciones pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
