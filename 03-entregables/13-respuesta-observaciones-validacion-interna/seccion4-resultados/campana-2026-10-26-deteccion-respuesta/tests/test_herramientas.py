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


# --------------------------------------------------------------- 3. analizador: fixtures con resultado conocido
def motor_linea(logged, ip, wend_ep, score, decision, heur=None, pk10=5):
    return json.dumps({"event": "decision", "logged_at": logged, "entity_ip": ip,
                       "window_end_utc": iso(wend_ep), "score": score, "threshold": U05,
                       "decision": decision, "packet_count_10s": pk10,
                       "history_coverage_s": 60, "detector_name": "if_limpio_2026_10", "heuristico": heur})


def test_analizador():
    an = cargar("analizar")
    T = 1793000000
    with tempfile.TemporaryDirectory() as d:
        # marcas: 4 episodios
        M = [
            {"evento": "inicio", "episodio_id": "inundacion_http-r1", "escenario": "inundacion_http",
             "repeticion": 1, "destino": "10.10.30.10", "reloj": {"pared_utc": iso(T)}},
            {"evento": "fin", "episodio_id": "inundacion_http-r1", "estado": "completo", "reloj": {"pared_utc": iso(T + 90)}},
            {"evento": "inicio", "episodio_id": "dns_inusual-r1", "escenario": "dns_inusual",
             "repeticion": 1, "destino": "10.10.10.20", "reloj": {"pared_utc": iso(T + 1000)}},
            {"evento": "fin", "episodio_id": "dns_inusual-r1", "estado": "completo", "reloj": {"pared_utc": iso(T + 1090)}},
            {"evento": "inicio", "episodio_id": "escaneo_breve-r1", "escenario": "escaneo_breve",
             "repeticion": 1, "destino": "10.10.30.10", "reloj": {"pared_utc": iso(T + 2000)}},
            {"evento": "fin", "episodio_id": "escaneo_breve-r1", "estado": "incompleto_timeout", "reloj": {"pared_utc": iso(T + 2090)}},
            {"evento": "inicio", "episodio_id": "inundacion_http-r2", "escenario": "inundacion_http",
             "repeticion": 2, "destino": "10.10.30.10", "reloj": {"pared_utc": iso(T + 3000)}},
            {"evento": "fin", "episodio_id": "inundacion_http-r2", "estado": "completo", "reloj": {"pared_utc": iso(T + 3090)}},
        ]
        (Path(d) / "marcas.jsonl").write_text("\n".join(json.dumps(x) for x in M), encoding="utf-8")

        K = "10.10.20.30"
        L = []
        # inundacion_http-r1: ventanas contiguas; una DURANTE con IF+HEUR y ALERT (emitido)
        for i, w in enumerate(range(T, T + 150, 10)):
            score = -0.70 if w == T + 40 else -0.50
            heur = {"heuristico": "http_abuse", "accion": "LIMIT"} if w == T + 40 else None
            dec = "ALERT" if w == T + 40 else "PERMIT"
            L.append(motor_linea(w + 1, K, w, score, dec, heur))
        # dns_inusual-r1: contiguas; DURANTE solo HEUR (dns_entropy, LIMIT) con decision PERMIT (derivado, no emitido)
        for w in range(T + 1000, T + 1150, 10):
            heur = {"heuristico": "dns_entropy", "accion": "LIMIT"} if w == T + 1030 else None
            L.append(motor_linea(w + 1, K, w, -0.50, "PERMIT", heur))
        # escaneo_breve-r1: SIN ventanas de la Kali en el intervalo -> no_evaluable
        # inundacion_http-r2: señal SOLO posterior (logged_at > fin)
        for w in range(T + 3000, T + 3150, 10):
            score = -0.70 if w == T + 3100 else -0.50     # T+3100 > fin(T+3090) -> posterior
            L.append(motor_linea(w + 1, K, w, score, "ALERT" if w == T + 3100 else "PERMIT"))
        # duplicado + discontinuidad artificiales (otra entidad, no afecta a la Kali)
        L.append(motor_linea(T + 41, K, T + 40, -0.70, "ALERT", {"heuristico": "http_abuse", "accion": "LIMIT"}))  # dup
        (Path(d) / "motor.log").write_text("\n".join(L), encoding="utf-8")

        cfg = {"umbrales": {"0.05": U05, "0.03": U03}, "origen": K,
               "combinacion_real": {"exclusiones": {"NUNCA_BLOQUEAR": []}}}
        (Path(d) / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")

        eps, inc_m = an.leer_marcas(Path(d) / "marcas.jsonl")
        regs, inc_r, dups = an.leer_motor(Path(d) / "motor.log")
        check(len(dups) == 1, f"detecta 1 ventana duplicada (hay {len(dups)})")

        c1 = an.clasificar(eps["inundacion_http-r1"], regs, K, U05, U03, None)
        check(c1["IF_0.05"]["categoria"] == "durante", "http-r1: IF durante")
        check(c1["IF_0.05"]["emitido_en_vivo"] is True, "http-r1: IF durante fue emitido en vivo (ALERT)")
        check(c1["IF_0.05"]["desde_inicio_generador_s"] == 41.0, "http-r1: logged_at 41 s tras inicio (no window_end)")

        cd = an.clasificar(eps["dns_inusual-r1"], regs, K, U05, U03, None)
        check(cd["HEUR"]["categoria"] == "durante", "dns-r1: HEUR durante")
        check(cd["HEUR"]["emitido_en_vivo"] is False, "dns-r1: HEUR LIMIT NO fue emitido como ALERT (derivado)")
        check(cd["IF_0.05"]["categoria"] == "sin_deteccion", "dns-r1: IF sin detección (cobertura continua)")

        ce = an.clasificar(eps["escaneo_breve-r1"], regs, K, U05, U03, None)
        check(ce["IF_0.05"]["categoria"] == "no_evaluable", "escaneo-r1: no_evaluable (sin cobertura / incompleto)")

        cp = an.clasificar(eps["inundacion_http-r2"], regs, K, U05, U03, None)
        check(cp["IF_0.05"]["categoria"] == "posterior", "http-r2: IF posterior")
        check(cp["IF_0.05"]["tras_fin_generador_s"] == 11.0, "http-r2: 11 s tras el fin")

        # IF_0.03 vs 0.05 sobre un score intermedio
        s_int = an.senales({"_pk10": 5, "_score": -0.58, "heuristico": None, "decision": "PERMIT"}, U05, U03)
        check(s_int["IF_0.05"] and not s_int["IF_0.03"], "score -0.58 dispara IF 0,05 pero no 0,03")

        # métricas por ventana: sin etiquetas no se fabrican
        m = an.metricas_por_ventana(regs, {}, U05, U03)
        check(m["calculadas"] is False, "sin etiquetas no se calculan métricas por ventana")
        et = {(K, iso(T + 40)): "1", (K, iso(T + 50)): "0"}
        m2 = an.metricas_por_ventana(regs, et, U05, U03)
        check(m2["calculadas"] and m2["IF_0.05"]["TP"] == 1 and m2["IF_0.05"]["FP"] == 0,
              "con etiquetas conocidas: TP=1, FP=0 para IF 0,05")

        # control FPR con denominador explícito (todas las ventanas de la Kali como 'normal' de prueba)
        f = an.fpr_control(regs, T, T + 3150, K, U05, U03, set())
        check(f["denominador"] == f["ventanas"] and f["IF_0.05"]["falsas_alarmas"] >= 1,
              "control FPR expone denominador y cuenta falsas alarmas")


def main():
    for fn in (test_validacion, test_generador_simulacion, test_generador_timeout_mata_hijos, test_analizador):
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{ok['n']} comprobaciones pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
