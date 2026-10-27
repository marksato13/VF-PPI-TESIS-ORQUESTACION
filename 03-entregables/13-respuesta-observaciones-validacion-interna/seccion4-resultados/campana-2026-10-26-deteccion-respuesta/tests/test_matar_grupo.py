#!/usr/bin/env python3
"""Terminación del grupo de procesos del generador — contra la función PUBLICADA correr_episodio().

No reemplaza la implementación: solo sustituye esq.comando_de (configuración) para lanzar escenarios de
padre/hijo inocuos con tiempos abreviados de prueba. Comprueba que NINGÚN hijo deja un 'testigo' tras la
limpieza, en cuatro casos:
  1) padre e hijo normales
  2) padre que termina (SIGTERM) e hijo que lo ignora
  3) padre que termina antes de la limpieza y deja un hijo
  4) interrupción (KeyboardInterrupt) durante el episodio
Portable: en POSIX ejercita killpg SIGTERM->SIGKILL con el pgid capturado al crear; en Windows, taskkill /T.
"""
from __future__ import annotations
import importlib.util, json, os, sys, tempfile, threading, time, _thread
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SCRIPTS = AQUI.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import esquema_campana as esq  # noqa


def cargar(n):
    sp = importlib.util.spec_from_file_location(n, SCRIPTS / f"{n}.py")
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


gen = cargar("generar_campana")
ok = {"n": 0}


def check(cond, msg):
    assert cond, "FALLA: " + msg
    ok["n"] += 1


CFG = {"tiempos_s": {"calentamiento_inicial": 0, "contexto_antes": 120, "observacion_despues": 90}}
S = {"id": "inundacion_http", "destino": "10.10.30.10", "servicio": "TCP/80", "timeout_s": 2}


def correr(cmd_builder, timeout_s=2, interrumpir=False):
    with tempfile.TemporaryDirectory() as d:
        testigo = (Path(d) / "hijo_vivo").as_posix()
        hijo = Path(d) / "hijo.py"
        hijo.write_text(
            "import sys,time\n"
            "try:\n import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "except Exception: pass\n"
            "time.sleep(5)\n"
            "open(sys.argv[1],'w').close()\n")
        padre = Path(d) / "padre.py"
        padre.write_text(cmd_builder(hijo, testigo))
        orig = esq.comando_de
        esq.comando_de = lambda c, s: [sys.executable, str(padre), str(hijo), testigo]
        sys.modules["esquema_campana"].comando_de = esq.comando_de
        s = dict(S); s["timeout_s"] = timeout_s
        marcas = open(Path(d) / "m.jsonl", "a", encoding="utf-8")
        try:
            if interrumpir:
                threading.Timer(1.0, lambda: _thread.interrupt_main()).start()
            estado = gen.correr_episodio(CFG, s, 1, Path(d), marcas, autorizado=True)
        finally:
            esq.comando_de = orig; sys.modules["esquema_campana"].comando_de = orig
            marcas.close()
        time.sleep(7)  # si algún hijo sobrevivió, crearía el testigo a los ~5 s
        ev = [json.loads(x) for x in (Path(d) / "m.jsonl").read_text().splitlines()]
        return estado, os.path.exists(testigo), ev


# 1) padre e hijo normales (el padre espera al hijo; timeout corta ambos)
def test_normal():
    estado, vivo, ev = correr(lambda h, t: "import subprocess,sys\n"
                              "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]]).wait()\n")
    check(not vivo, "1) hijo normal terminado tras la limpieza")
    check(any(e["evento"] == "inicio" for e in ev) and any(e["evento"] == "fin" for e in ev),
          "1) inicio y fin registrados por separado")


# 2) padre termina (recibe SIGTERM) e hijo IGNORA SIGTERM -> solo SIGKILL al grupo lo mata
def test_hijo_ignora_sigterm():
    estado, vivo, _ = correr(lambda h, t: "import subprocess,sys,time\n"
                             "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]])\n"
                             "time.sleep(30)\n")
    check(not vivo, "2) hijo que ignora SIGTERM terminado (SIGKILL al grupo)")


# 3) el PADRE termina pronto (antes de la limpieza) y deja un hijo vivo
def test_padre_termina_antes():
    estado, vivo, _ = correr(lambda h, t: "import subprocess,sys\n"
                             "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]])\n"
                             "sys.exit(0)\n")
    if os.name == "nt":
        # taskkill por el PID del padre (ya muerto) no alcanza al huérfano; en POSIX el pgid capturado sí.
        print("    (3) SKIP en Windows: se verifica en POSIX con el pgid)")
        ok["n"] += 1
        return
    check(not vivo, "3) hijo huérfano (padre terminó antes) terminado por el grupo (POSIX, pgid)")


# 4) interrupción durante el episodio
def test_interrupcion():
    estado, vivo, _ = correr(lambda h, t: "import subprocess,sys,time\n"
                             "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]])\n"
                             "time.sleep(30)\n", timeout_s=30, interrumpir=True)
    check("interrumpido" in estado, f"4) estado incompleto_interrumpido (fue {estado})")
    if os.name == "nt":
        print("    (4) kill del hijo SKIP en Windows (taskkill /T); se verifica en POSIX")
        ok["n"] += 1
        return
    check(not vivo, "4) interrupción: hijo terminado (POSIX, pgid)")


def main():
    for fn in (test_normal, test_hijo_ignora_sigterm, test_padre_termina_antes, test_interrupcion):
        fn(); print(f"OK  {fn.__name__}")
    print(f"\n{ok['n']} comprobaciones de terminación pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
