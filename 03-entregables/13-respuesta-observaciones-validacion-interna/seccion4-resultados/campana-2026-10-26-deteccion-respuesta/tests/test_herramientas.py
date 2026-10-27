#!/usr/bin/env python3
"""Verificación SIN ataques de las herramientas de la campaña (no mide el desempeño de CyberFlow).

Usa fixtures con resultados conocidos. Ejecuta:  python3 tests/test_herramientas.py
Comprueba: validación de config (válida/ inválida, placeholders, destino fuera de lista), construcción de
comandos sin marcadores, simulación por defecto, timeout con muerte del grupo de procesos (hijos incluidos),
clasificación temporal por logged_at, separación emitido/derivado, duplicados/discontinuidades, control FPR y
métricas por ventana solo con etiquetas.
"""
from __future__ import annotations
import importlib.util, json, os, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SCRIPTS = AQUI.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import esquema_campana as esq  # noqa: E402


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, SCRIPTS / f"{nombre}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


U05, U03 = -0.5694578968203694, -0.5898535710336618
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


def rec(logged, wend_ep, score, decision="PERMIT", heur=None, pk10=5, det="if_limpio_2026_10", ip=K):
    return json.dumps({"event": "decision", "logged_at": logged, "entity_ip": ip, "window_end_utc": iso(wend_ep),
                       "score": score, "threshold": U05, "decision": decision, "packet_count_10s": pk10,
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
        return an.clasificar(eps[eid], regs, K, U05, U03, destinos, integridad_apto), regs, dups


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
    check(c["IF_0.05"]["base"].startswith("emitido_por_modelo"), "IF 0,05 por el modelo => emitido en vivo")
    check(c["IF_0.03"]["base"].startswith("derivado"), "IF 0,03 => derivado (umbral no desplegado)")
    # métricas por ventana solo con etiquetas; dedup evita doble conteo
    check(an.metricas_por_ventana(regs, {}, U05, U03)["calculadas"] is False, "sin etiquetas: no métricas")
    m2 = an.metricas_por_ventana(regs, {(K, iso(T + 40)): "1", (K, iso(T + 50)): "0"}, U05, U03)
    check(m2["IF_0.05"]["TP"] == 1 and m2["IF_0.05"]["FP"] == 0, "etiquetas conocidas: TP=1, FP=0")
    f = an.fpr_control(regs, T, T + 150, U05, U03, set())
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
        g = an.senales(fila[0], U05, U03)
        check(g["HEUR"] and not g["IF_0.05"], "score null: HEUR dispara, IF no")


def _tabla8_e2e(an, tmp, destinos_csv, con_senal=True):
    """Recorre main() hasta analisis.json/TABLA8.md. destinos_csv=None => sin --destinos. Devuelve (tabla8, episodio)."""
    T = 1793000000
    d = Path(tmp)
    (d / "marcas.jsonl").write_text("\n".join(
        marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90)), encoding="utf-8")
    mot = [rec(w + 1, w, (-0.70 if (con_senal and w == T + 40) else -0.50),
               ("ALERT" if (con_senal and w == T + 40) else "PERMIT")) for w in range(T, T + 150, 10)]
    (d / "motor.log").write_text("\n".join(mot), encoding="utf-8")
    (d / "cfg.json").write_text(json.dumps({"umbrales": {"0.05": U05, "0.03": U03, "desplegado_referencia": -0.5693969936322356},
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
        (Path(d) / "cfg.json").write_text(json.dumps({"umbrales": {"0.05": U05, "0.03": U03, "desplegado_referencia": -0.5693969936322356},
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
    an = cargar("analizar")
    # ALERT solo por IF (modelo): base emitido; HEUR no
    g = an.senales({"_score": -0.70, "_pk10": 5, "decision": "ALERT", "detector_name": "if_limpio_2026_10",
                    "heuristico": None}, U05, U03)
    check(g["IF_0.05"] and not g["HEUR"] and g["base"]["IF_0.05"].startswith("emitido_por_modelo"),
          "ALERT solo por IF: IF emitido, HEUR no")
    # señal solo heurística (PERMIT): registrada en vivo, no ALERT
    g = an.senales({"_score": -0.50, "_pk10": 5, "decision": "PERMIT", "detector_name": "if_limpio_2026_10",
                    "heuristico": {"heuristico": "http_abuse", "accion": "LIMIT"}}, U05, U03)
    check(g["HEUR"] and not g["IF_0.05"] and g["base"]["HEUR"] == "registrada_en_vivo",
          "heurístico LIMIT en PERMIT: registrada en vivo, no ALERT")
    # compartida
    g = an.senales({"_score": -0.70, "_pk10": 5, "decision": "ALERT", "detector_name": "if_limpio_2026_10",
                    "heuristico": {"heuristico": "http_abuse", "accion": "LIMIT"}}, U05, U03)
    check(g["IF_0.05"] and g["HEUR"] and g["HIB_0.05"], "señal compartida IF+HEUR")
    # alternativa no desplegada: IF_0.03 derivado; score intermedio dispara 0,05 y no 0,03
    g = an.senales({"_score": -0.58, "_pk10": 5, "decision": "PERMIT", "heuristico": None}, U05, U03)
    check(g["IF_0.05"] and not g["IF_0.03"] and g["base"]["IF_0.03"].startswith("derivado"),
          "IF 0,03 es derivado (umbral no desplegado); -0.58 no lo dispara")


def main():
    for fn in (test_validacion, test_generador_simulacion, test_generador_timeout_mata_hijos,
               test_analizador_basico, test_cobertura_una_ventana_insuficiente, test_score_nulo_con_heuristico,
               test_tabla8_evidencia_y_denominador, test_ventana_previa, test_emitido_vs_derivado,
               test_integridad_backing, test_integridad_informe_externo, test_integridad_descriptor_ilustrativo,
               test_integridad_gate_analizador, test_integridad_e2e_no_habilita_denominador):
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{ok['n']} comprobaciones pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
