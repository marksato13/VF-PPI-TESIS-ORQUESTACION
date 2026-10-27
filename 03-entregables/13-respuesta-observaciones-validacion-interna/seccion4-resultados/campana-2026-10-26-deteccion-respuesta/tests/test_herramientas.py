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
    dok = {("inundacion_http-r1", iso(T + 40)): ["10.10.30.10"]}   # evidencia de destino (confirma atribución)
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


def _tabla8_e2e(an, tmp, destinos_csv, integ_apto=True):
    """Recorre main() hasta el fichero de la Tabla 8 y devuelve el dict tabla8. destinos_csv=None => sin --destinos."""
    T = 1793000000
    d = Path(tmp)
    (d / "marcas.jsonl").write_text("\n".join(
        marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90)), encoding="utf-8")
    mot = [rec(w + 1, w, -0.70 if w == T + 40 else -0.50, "ALERT" if w == T + 40 else "PERMIT")
           for w in range(T, T + 150, 10)]
    (d / "motor.log").write_text("\n".join(mot), encoding="utf-8")
    (d / "cfg.json").write_text(json.dumps({"umbrales": {"0.05": U05, "0.03": U03, "desplegado_referencia": -0.5693969936322356},
                                            "origen": K, "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}),
                                encoding="utf-8")
    (d / "integ.json").write_text(json.dumps({"episodios": [{"episodio_id": "inundacion_http-r1", "apto": integ_apto}]}),
                                  encoding="utf-8")
    argv = ["x", "--marcas", str(d / "marcas.jsonl"), "--motor", str(d / "motor.log"),
            "--config", str(d / "cfg.json"), "--integridad", str(d / "integ.json"), "--salida", str(d / "out")]
    if destinos_csv is not None:
        (d / "dest.csv").write_text(destinos_csv, encoding="utf-8")
        argv += ["--destinos", str(d / "dest.csv")]
    old = sys.argv
    sys.argv = argv
    try:
        an.main()
    finally:
        sys.argv = old
    return json.loads((d / "out" / "analisis.json").read_text(encoding="utf-8"))["tabla8"]["Inundación HTTP"]


def test_tabla8_excluye_no_confirmadas():
    an = cargar("analizar")
    T = 1793000000
    wk = iso(T + 40)
    casos = {
        "sin --destinos": (None, False),
        "mapa vacío": ("episodio_id,window_end_utc,destino\n", False),
        "clave ausente": (f"episodio_id,window_end_utc,destino\ninundacion_http-r1,{iso(T + 20)},10.10.30.10\n", False),
        "destino incorrecto": (f"episodio_id,window_end_utc,destino\ninundacion_http-r1,{wk},10.10.99.99\n", False),
        "destino correcto": (f"episodio_id,window_end_utc,destino\ninundacion_http-r1,{wk},10.10.30.10\n", True),
    }
    for nombre, (csvdata, debe_contar) in casos.items():
        with tempfile.TemporaryDirectory() as tmp:
            t8 = _tabla8_e2e(an, tmp, csvdata)
            cnt = t8["IF_0.05"]
            if debe_contar:
                check(cnt == 1 and "inundacion_http-r1" in t8["evaluables"],
                      f"Tabla 8 cuenta 1 con atribución confirmada ({nombre})")
            else:
                check(cnt == 0, f"Tabla 8 NO cuenta señal no confirmada ({nombre}) — contó {cnt}")


def test_integridad_gate():
    an = cargar("analizar")
    vi = cargar("verificar_integridad")
    # episodio con motor continuo pero PCAP incompleto / historia insuficiente / telemetría no verificable
    e = {"episodio_id": "inundacion_http-r1", "campana": "x",
         "pcap_presente": False,                         # PCAP incompleto/ausente
         "eve_presente": True, "decisiones_presentes": True, "caracteristicas_presentes": True,
         "cobertura_s": {"previa": 30, "posterior": 95}, # historia insuficiente (<120)
         "cobertura_durante_completa": True, "continuidad_sin_huecos": True, "faltantes": [],
         "captura": {"paquetes_descartados": 0}, "eve_eventos": 0,
         "salud": {"suricata_activo": True, "trafico_presente": True},  # EVE 0 con salud OK => fallo telemetría
         "relojes": {"sensor": 0.1, "tolerancia_s": 1}}
    rep = vi.evaluar_episodio(e)
    check(rep["apto"] is False, "integridad: PCAP ausente + historia corta => NO apto")
    check(rep["requisitos"]["historia_requerida_disponible"] is False, "historia <120 s => False")
    check(rep["requisitos"]["telemetria_eve_verificable"] is False, "EVE 0 con suricata activo y tráfico => fallo")
    # desconocido no es apto
    e2 = {"episodio_id": "y", "cobertura_s": {}, "eve_eventos": 5}
    rep2 = vi.evaluar_episodio(e2)
    check(rep2["apto"] is False and rep2["desconocidos"], "campos sin evidencia => 'desconocido' y NO apto")
    # un episodio con motor continuo pero integridad no apta NO se declara evaluable en el analizador
    T = 1793000000
    mot = [rec(w + 1, w, -0.70 if w == T + 40 else -0.50, "ALERT" if w == T + 40 else "PERMIT")
           for w in range(T, T + 150, 10)]
    c, _, _ = clasif(an, marca("inundacion_http-r1", "inundacion_http", "10.10.30.10", T, T + 90), mot,
                     "inundacion_http-r1", destinos={("inundacion_http-r1", iso(T + 40)): ["10.10.30.10"]},
                     integridad_apto=False)
    check(c["evaluable"] is False and c["IF_0.05"]["categoria"] == "no_evaluable",
          "motor continuo pero integridad no apta => no evaluable")


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
               test_tabla8_excluye_no_confirmadas, test_ventana_previa, test_emitido_vs_derivado,
               test_integridad_gate):
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{ok['n']} comprobaciones pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
