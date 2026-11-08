"""Banco de cf_4b_rotacion.py (PROPUESTA) con systemd FALSO: orden de armado, reversión, detección de rotación por varias vías,
cierre exitoso y reanudación (normal, por tope absoluto y sin reanudar). El comportamiento real de systemd no se prueba aquí
(véase tests/prueba_systemd_real.sh y evidencia-pendiente/systemd-real-prueba.txt)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
SCRIPT = Path(os.environ.get("CF_SCRIPT", AQUI.parent / "herramientas" / "cf_4b_rotacion.py"))
FALSO = AQUI / "falso_systemd.py"


def test_timer_parado_informa_lasttrigger_vacio_y_no_es_un_disparo():
    """Hallazgo del ensayo en systemd real (255): un timer PARADO informa LastTriggerUSec vacío. Eso NO es «disparó mientras
    se paraba» (con el comparador anterior, armar revertía siempre). Un valor distinto en ambos lados sí es un disparo."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cf_rot", SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    t = "logrotate.timer"
    assert m.sistema_igual(t, {"LastTriggerUSec": "Sun 2026-11-08 00:00:00 UTC"}, {"LastTriggerUSec": ""})
    assert m.sistema_igual(t, {"LastTriggerUSec": ""}, {"LastTriggerUSec": "Sun 2026-11-08 00:00:00 UTC"})
    assert m.sistema_igual(t, {"LastTriggerUSec": "a"}, {"LastTriggerUSec": "a"})
    assert not m.sistema_igual(t, {"LastTriggerUSec": "a"}, {"LastTriggerUSec": "b"})
    assert not m.sistema_igual("logrotate.service", {"InvocationID": "x"}, {"InvocationID": "y"})


@pytest.fixture
def ent(tmp_path):
    home, estado, suri, fake = tmp_path / "home", tmp_path / "estado", tmp_path / "suricata", tmp_path / "fake"
    for d in (home / "cyberflow/logs/_state-e4", home / "feed-v2", home / "cf-e4/4b", suri, fake):
        d.mkdir(parents=True, exist_ok=True)
    wr = lambda p, n: p.write_bytes((f"{p.name} linea\n" * n).encode())
    wr(suri / "eve.json", 4000); wr(suri / "stats.log", 800)
    wr(home / "cyberflow/logs/motor_decision.log", 3000); wr(home / "cyberflow/logs/_state-e4/ciclos.jsonl", 500)
    for n in ("via-rapida-resumen", "traza", "senales-if"):
        wr(home / f"feed-v2/{n}.jsonl", 1500)
    (home / "feed-v2/senales-rapidas.jsonl").write_bytes(b"")
    (suri / "eve.json.1.gz").write_bytes(b"viejo")                                     # ya existía, rotado de antes
    for n, w in (("sw-systemctl", "systemctl"), ("sw-run", "systemd-run")):
        (tmp_path / n).write_text(f'#!/bin/sh\nexec {sys.executable} {FALSO} {w} "$@"\n'); (tmp_path / n).chmod(0o755)
    (tmp_path / "sw-self").write_text(f'#!/bin/sh\nexec {sys.executable} {SCRIPT} "$@"\n'); (tmp_path / "sw-self").chmod(0o755)
    (fake / "activo").mkdir(); (fake / "props").mkdir()
    (fake / "activo/logrotate.timer").write_text("active")
    for k, v in (("logrotate.service.InvocationID", "inv-0"), ("logrotate.service.ExecMainStartTimestampMonotonic", "111"),
                 ("logrotate.service.ActiveEnterTimestampMonotonic", "112"), ("logrotate.timer.LastTriggerUSec", "t-0"),
                 ("logrotate.timer.LastTriggerUSecMonotonic", "m-0")):
        (fake / "props" / k).write_text(v)
    env = dict(os.environ, CF_HOME=str(home), CF_ESTADO=str(estado), CF_SURICATA=str(suri), CF_PRUEBA="1",
               CF_SYSTEMCTL=str(tmp_path / "sw-systemctl"), CF_SYSTEMD_RUN=str(tmp_path / "sw-run"), CF_SELF=str(tmp_path / "sw-self"),
               FAKE_DIR=str(fake), FAKE_FALLA="")
    class E:
        pass
    e = E(); e.home, e.estado, e.suri, e.fake, e.env = home, estado, suri, fake, env
    e.motor, e.eve = home / "cyberflow/logs/motor_decision.log", suri / "eve.json"
    e.calls = lambda: (fake / "llamadas.log").read_text().splitlines() if (fake / "llamadas.log").exists() else []
    e.timer = lambda: (fake / "activo/logrotate.timer").read_text().strip()
    e.log = lambda: (estado / "log.txt").read_text() if (estado / "log.txt").exists() else ""
    def correr(*args, falla="", timeout=60):
        env2 = dict(env, FAKE_FALLA=falla)
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=env2, capture_output=True, text=True, timeout=timeout)
    e.run = correr
    e.tope = lambda: int(time.time()) + 20 * 3600
    return e


def armado(ent):
    r = ent.run("armar", "--tope", str(ent.tope()))
    assert r.returncode == 0, r.stdout + r.stderr
    return r


def cierre_completo(ent):
    """Árbol de una corrida cerrada bien: lo que dejan s30 y s40."""
    B = ent.home / "cf-e4/4b"; C = B / "copias"; (C / "feed-v2").mkdir(parents=True, exist_ok=True)
    (B / "replay").mkdir(exist_ok=True); (B / "replay/rc.txt").write_text("rc=0\n"); (B / "cierre.t").write_text("1.0\n")
    (B / "archivo-pcap.rc").write_text("0\n")
    # La corrida escribió en las fuentes (registros de la 4B) y s40 las copió enteras: copia == fuente al empezar s40.
    fuentes = {"motor_decision.log": ent.motor, "ciclos.jsonl": ent.home / "cyberflow/logs/_state-e4/ciclos.jsonl", "stats-fin.log": ent.suri / "stats.log",
               "feed-v2/via-rapida-resumen.jsonl": ent.home / "feed-v2/via-rapida-resumen.jsonl", "feed-v2/traza.jsonl": ent.home / "feed-v2/traza.jsonl",
               "feed-v2/senales-if.jsonl": ent.home / "feed-v2/senales-if.jsonl", "feed-v2/senales-rapidas.jsonl": ent.home / "feed-v2/senales-rapidas.jsonl"}
    for n, ruta in fuentes.items():
        if n != "feed-v2/senales-rapidas.jsonl":                       # esta puede no crecer en toda la corrida
            with open(ruta, "ab") as fh:
                fh.write(b"registro de la 4B\n")
        (C / n).write_bytes(ruta.read_bytes())
    for n, c in (("eve-segmento.json", b"e\n"), ("muestras.jsonl", b"m\n"), ("archivar.log", b"2026 OK live-x.pcap\n"), ("archivador-ESTADO.txt", b"OK vistos=1\n"),
                 ("servicios-fin.txt", b"x\n"), ("sha256-feed-final.txt", b"h\n"), ("feed-v2/feed.json", b"{}\n")):
        (C / n).write_bytes(c)
    (C / "FUENTES-al-copiar.tsv").write_text("".join(f"{n}\t{(C / n).stat().st_size}\n" for n in fuentes))
    reescribir_sumas(C)
    (C / "COPIAS-COMPLETAS.ok").write_text("ok 2026\n")
    return B, C


def reescribir_sumas(C):
    """Como s40: el manifiesto se genera con lo que haya quedado, también de una copia truncada."""
    (C / "SHA256SUMS").write_text("".join(f"{hashlib.sha256((C / n).read_bytes()).hexdigest()}  ./{n}\n" for n in sorted(
        str(p.relative_to(C)) for p in C.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS", "COPIAS-COMPLETAS.ok"))))


# ------------------------------------------------------------------------------------------------ armar
def test_armar_arma_y_verifica_antes_de_parar(ent):
    r = armado(ent)
    c = ent.calls()
    i = lambda s: next(n for n, l in enumerate(c) if s in l)
    assert i("systemd-run --unit=cf-4b-tope") < i("systemd-run --unit=cf-4b-vigia") < i("is-active cf-4b-tope.timer") < i("stop logrotate.timer")
    assert i("is-active cf-4b-vigia.service") < i("stop logrotate.timer")
    assert ent.timer() == "inactive"
    assert "recuperación ARMADA y verificada" in ent.log() and "logrotate.timer PARADO" in ent.log()
    base = json.loads((ent.estado / "base.json").read_text())
    assert base["ficheros"][str(ent.eve)]["tam"] > 0 and len(base["hermanos"]) == 1


@pytest.mark.parametrize("falla", ["run-tope", "run-vigia", "elapse-distinto", "vigia-cae"])
def test_si_no_se_arma_no_se_para_el_timer(ent, falla):
    r = ent.run("armar", "--tope", str(ent.tope()), falla=falla)
    assert r.returncode == 3, r.stdout + r.stderr
    assert not any("stop logrotate.timer" in l for l in ent.calls()), "no debe parar el timer sin recuperación armada"
    assert ent.timer() == "active"
    assert "ARMAR FALLÓ" in ent.log()


def test_si_no_para_revierte(ent):
    r = ent.run("armar", "--tope", str(ent.tope()), falla="stop-no-para")
    assert r.returncode == 3 and ent.timer() == "active"
    assert any(l.endswith("start logrotate.timer") for l in ent.calls())


def test_si_el_timer_dispara_durante_el_stop_revierte(ent):
    r = ent.run("armar", "--tope", str(ent.tope()), falla="timer-dispara")
    assert r.returncode == 3 and ent.timer() == "active"


def test_tope_es_un_instante_absoluto(ent):
    t = int(time.time()) + 20 * 3600
    armado_r = ent.run("armar", "--tope", str(t)); assert armado_r.returncode == 0
    esperado = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t))
    assert any(f"--on-calendar={esperado}" in l for l in ent.calls()), "el tope va como fecha y hora absolutas"
    assert not any("--on-active" in l for l in ent.calls()), "nunca un plazo relativo al momento de aplicar"


def test_armar_exige_timer_activo_y_tope_futuro(ent, tmp_path):
    (ent.fake / "activo/logrotate.timer").write_text("inactive")
    assert ent.run("armar", "--tope", str(ent.tope())).returncode == 2
    (ent.fake / "activo/logrotate.timer").write_text("active")
    env = dict(ent.env); env.pop("CF_PRUEBA")
    r = subprocess.run([sys.executable, str(SCRIPT), "armar", "--tope", "1"], env=env, capture_output=True, text=True)
    assert r.returncode == 2                      # sin CF_PRUEBA: necesita root


# ------------------------------------------------------------------------------------------------ comprobar (más que el inodo)
def test_comprobar_sin_rotacion_con_crecimiento(ent):
    armado(ent)
    for p in (ent.eve, ent.motor, ent.home / "feed-v2/via-rapida-resumen.jsonl", ent.suri / "stats.log"):
        with open(p, "ab") as fh:
            fh.write(b"mas datos\n" * 50)
    r = ent.run("comprobar")
    assert r.returncode == 0, r.stdout
    assert "RESULTADO_COMPROBAR OK" in r.stdout


@pytest.mark.parametrize("caso", ["copytruncate", "reescrito_mayor", "renombrado", "hermano_nuevo", "servicio", "timer", "desaparece", "hermano_modificado"])
def test_comprobar_detecta_la_rotacion(ent, caso):
    armado(ent)
    if caso == "copytruncate":
        ent.eve.write_bytes(b"")                                           # mismo inodo, tamaño 0
    elif caso == "reescrito_mayor":
        ent.eve.write_bytes(b"x" * (ent.eve.stat().st_size + 1000))        # mismo inodo y MAYOR tamaño: solo lo delata el prefijo
    elif caso == "renombrado":
        os.rename(ent.motor, str(ent.motor) + ".1"); ent.motor.write_bytes(b"nuevo\n")
    elif caso == "hermano_nuevo":
        (ent.suri / "eve.json.1").write_bytes(b"rotado")
    elif caso == "hermano_modificado":
        (ent.suri / "eve.json.1.gz").write_bytes(b"viejo-pero-distinto")
    elif caso == "servicio":
        (ent.fake / "props/logrotate.service.InvocationID").write_text("inv-1")
    elif caso == "timer":
        (ent.fake / "props/logrotate.timer.LastTriggerUSec").write_text("t-1")
    elif caso == "desaparece":
        os.remove(ent.home / "feed-v2/traza.jsonl")
    r = ent.run("comprobar")
    assert r.returncode == 1 and "FALLO" in r.stdout, r.stdout


def test_mismo_inodo_y_mayor_tamano_no_basta_para_aprobar(ent):
    """El caso que un comprobador de inodo + tamaño daría por bueno."""
    armado(ent)
    antes = ent.eve.stat()
    ent.eve.write_bytes(b"y" * (antes.st_size + 5))
    despues = ent.eve.stat()
    assert despues.st_ino == antes.st_ino and despues.st_size >= antes.st_size
    assert ent.run("comprobar").returncode == 1


# ------------------------------------------------------------------------------------------------ cierre
def test_cierre_ok(ent):
    armado(ent); cierre_completo(ent)
    r = ent.run("cierre"); assert r.returncode == 0, r.stdout


@pytest.mark.parametrize("fallo", ["truncada", "sin_salto_final", "otro_fichero", "vacia", "cp_fallido_enospc"])
def test_copia_fallida_no_reanuda_aunque_el_manifiesto_verifique(ent, fallo):
    """s40 genera SHA256SUMS con lo que haya quedado, también de una copia truncada: el manifiesto consistente NO prueba la copia."""
    armado(ent); B, C = cierre_completo(ent)
    objetivo = C / "feed-v2/via-rapida-resumen.jsonl" if fallo == "sin_salto_final" else C / "motor_decision.log"
    datos = objetivo.read_bytes()
    if fallo == "truncada": objetivo.write_bytes(datos[: len(datos) // 2])
    elif fallo == "sin_salto_final": objetivo.write_bytes(datos.rstrip(b"\n"))
    elif fallo == "otro_fichero": objetivo.write_bytes(b"Z" * len(datos))                    # mismo tamaño, otro contenido
    elif fallo == "vacia": objetivo.write_bytes(b"")
    elif fallo == "cp_fallido_enospc": objetivo.write_bytes(datos[: len(datos) - 7])           # cp cortado por disco lleno, a mitad de línea
    # el manifiesto se regenera DESPUÉS del fallo, como hace s40: verifica y está completo
    (C / "SHA256SUMS").write_text("".join(f"{hashlib.sha256((C / n).read_bytes()).hexdigest()}  ./{n}\n" for n in sorted(
        str(q.relative_to(C)) for q in C.rglob("*") if q.is_file() and q.name != "SHA256SUMS")))
    r = ent.run("cierre")
    assert "copias/SHA256SUMS: " in r.stdout and "OK    copias/SHA256SUMS" in r.stdout, "el manifiesto SÍ verifica"
    assert r.returncode == 1 and "FALLO copia fiel" in r.stdout, r.stdout
    t0 = time.time()
    ent.run("vigilar", "--tope", str(int(t0) + 3), "--intervalo", "0.3", timeout=30)
    assert "REANUDADO_NORMAL" not in ent.log() and "REANUDADO_POR_TOPE" in ent.log()


@pytest.mark.parametrize("rotura", ["sin_replay", "replay_fallo", "sin_cierre_t", "archivador_rc", "estado_no_ok", "fallo_arch", "hash", "sin_sumas",
                                    "falta_imprescindible", "motor_menor", "sin_eve"])
def test_cierre_exige_todo(ent, rotura):
    armado(ent); B, C = cierre_completo(ent)
    def resumar():
        (C / "SHA256SUMS").write_text("".join(f"{hashlib.sha256((C / n).read_bytes()).hexdigest()}  ./{n}\n" for n in sorted(
            str(p.relative_to(C)) for p in C.rglob("*") if p.is_file() and p.name != "SHA256SUMS")))
    if rotura == "sin_replay": os.remove(B / "replay/rc.txt")
    elif rotura == "replay_fallo": (B / "replay/rc.txt").write_text("rc=1\n")
    elif rotura == "sin_cierre_t": os.remove(B / "cierre.t")
    elif rotura == "archivador_rc": (B / "archivo-pcap.rc").write_text("1\n")
    elif rotura == "estado_no_ok": (C / "archivador-ESTADO.txt").write_text("PARADO\n"); resumar()
    elif rotura == "fallo_arch": (C / "archivar.log").write_text("x FALLO live-y.pcap\n"); resumar()
    elif rotura == "hash": (C / "motor_decision.log").write_bytes(b"alterado")                    # SHA256SUMS ya no verifica
    elif rotura == "sin_sumas": os.remove(C / "SHA256SUMS")
    elif rotura == "falta_imprescindible": os.remove(C / "feed-v2/traza.jsonl"); resumar()
    elif rotura == "motor_menor": (C / "motor_decision.log").write_bytes(b"corto\n"); resumar()
    elif rotura == "sin_eve": (C / "eve-segmento.json").write_bytes(b""); resumar()
    r = ent.run("cierre")
    assert r.returncode == 1 and "FALLO" in r.stdout, r.stdout


# ------------------------------------------------------------------------------------------------ vigilar / reanudar
def test_reanudacion_normal_solo_con_cierre_y_sin_rotacion(ent):
    armado(ent); cierre_completo(ent)
    r = ent.run("vigilar", "--tope", str(int(time.time()) + 600), "--intervalo", "0.2", timeout=20)
    assert r.returncode == 0 and ent.timer() == "active"
    assert "REANUDADO_NORMAL" in ent.log() and "TOPE" not in ent.log().split("REANUDADO_NORMAL")[0].upper().replace("TOPE ", "")
    assert sum(l.endswith("start logrotate.timer") for l in ent.calls()) == 1


def test_sin_cierre_no_reanuda_hasta_el_tope_absoluto(ent):
    armado(ent)                                                                 # no hay copias ni replay
    t0 = time.time()
    r = ent.run("vigilar", "--tope", str(int(t0) + 3), "--intervalo", "0.3", timeout=30)
    assert r.returncode == 0 and ent.timer() == "active"
    assert time.time() - t0 >= 2.0, "no debe reanudar antes del tope"
    assert "REANUDADO_POR_TOPE_SIN_CIERRE_VERIFICADO" in ent.log() and "REANUDADO_NORMAL" not in ent.log()


def test_con_rotacion_detectada_no_hay_reanudacion_normal(ent):
    armado(ent); cierre_completo(ent)
    ent.eve.write_bytes(b"")                                                    # alguien rotó por su cuenta
    t0 = time.time()
    r = ent.run("vigilar", "--tope", str(int(t0) + 3), "--intervalo", "0.3", timeout=30)
    assert r.returncode == 0
    lg = ent.log()
    assert "ROTACION_DETECTADA" in lg and "REANUDADO_NORMAL" not in lg and "REANUDADO_POR_TOPE_SIN_CIERRE_VERIFICADO" in lg


def test_copias_alteradas_no_reanuda_normal(ent):
    armado(ent); B, C = cierre_completo(ent)
    (C / "stats-fin.log").write_bytes(b"alterado")
    t0 = time.time()
    ent.run("vigilar", "--tope", str(int(t0) + 3), "--intervalo", "0.3", timeout=30)
    assert "REANUDADO_NORMAL" not in ent.log() and "REANUDADO_POR_TOPE" in ent.log()


def test_si_otro_reanuda_el_vigia_termina_sin_tocar(ent):
    armado(ent)
    (ent.fake / "activo/logrotate.timer").write_text("active")                  # Mark lo arrancó a mano
    r = ent.run("vigilar", "--tope", str(int(time.time()) + 600), "--intervalo", "0.2", timeout=20)
    assert r.returncode == 0 and "reanudado por otro medio" in ent.log()
    assert not any(l.endswith("start logrotate.timer") for l in ent.calls())


def test_reanudar_tope_es_idempotente(ent):
    armado(ent)
    assert ent.run("reanudar-tope").returncode == 0 and ent.timer() == "active"
    n = sum(l.endswith("start logrotate.timer") for l in ent.calls())
    assert ent.run("reanudar-tope").returncode == 0
    assert sum(l.endswith("start logrotate.timer") for l in ent.calls()) == n, "con el timer activo no vuelve a arrancarlo"


def test_el_vigia_armado_antes_de_parar_no_confunde_timer_activo_con_reanudacion(ent):
    """El vigía arranca ANTES de parar el timer: con el timer aún activo y sin parado.json no debe salir ni actuar."""
    armado(ent)
    os.remove(ent.estado / "parado.json")                                       # situación previa a la parada
    (ent.fake / "activo/logrotate.timer").write_text("active")
    t0 = time.time()
    r = ent.run("vigilar", "--tope", str(int(t0) + 3), "--intervalo", "0.3", timeout=30)
    assert r.returncode == 0 and time.time() - t0 >= 2.0, "no sale antes del tope"
    assert "reanudado por otro medio" not in ent.log() and not any(l.endswith("start logrotate.timer") for l in ent.calls())


def test_armar_borra_una_marca_de_parada_antigua(ent):
    ent.estado.mkdir(parents=True, exist_ok=True)
    (ent.estado / "parado.json").write_text("{}")
    r = ent.run("armar", "--tope", str(ent.tope()), falla="run-tope")
    assert r.returncode == 3 and not (ent.estado / "parado.json").exists()


def test_desarmar_a_mano(ent):
    armado(ent)
    assert ent.run("desarmar").returncode == 0 and ent.timer() == "active"
    c = ent.calls()
    assert any("stop cf-4b-vigia.service" in l for l in c) and any("stop cf-4b-tope.timer" in l for l in c)
    ini = max(n for n, l in enumerate(c) if l.endswith("start logrotate.timer"))
    desde = c[ini:]
    assert next(n for n, l in enumerate(desde) if "is-active logrotate.timer" in l) < next(n for n, l in enumerate(desde) if "stop cf-4b-vigia.service" in l), \
        "se comprueba que el timer está activo ANTES de retirar la recuperación"


def test_desarmar_si_el_timer_no_arranca_no_retira_la_recuperacion(ent):
    """Si `systemctl start logrotate.timer` falla, desarmar NO devuelve 0 ni cancela el vigía y el tope: son lo único que queda para reanudar."""
    armado(ent)
    n0 = len(ent.calls())
    r = ent.run("desarmar", falla="start-falla")
    assert r.returncode == 1 and "DESARMAR FALLÓ" in r.stderr, r.stdout + r.stderr
    assert ent.timer() == "inactive"
    nuevas = ent.calls()[n0:]
    assert not any(l.startswith("systemctl stop cf-4b") for l in nuevas), nuevas
    assert sum(l.endswith("start logrotate.timer") for l in nuevas) == 3, "reintenta antes de rendirse"
    assert "DESARMAR FALLÓ" in ent.log() and "SIGUEN armados" in ent.log()
    assert (ent.estado / "parado.json").exists(), "el vigía debe seguir actuando"
    # cuando el arranque vuelve a funcionar, el desarme sí completa y retira la recuperación
    r2 = ent.run("desarmar")
    assert r2.returncode == 0 and ent.timer() == "active"
    assert any("stop cf-4b-vigia.service" in l for l in ent.calls()[n0:]) and not (ent.estado / "parado.json").exists()


def test_armar_revertido_con_start_fallido_deja_la_recuperacion_y_sale_con_error(ent):
    r = ent.run("armar", "--tope", str(ent.tope()), falla="timer-dispara,start-falla")
    assert r.returncode == 3
    assert ent.timer() == "inactive"
    assert not any(l.startswith("systemctl stop cf-4b") for l in ent.calls()), "no se retira el tope ni el vigía si el timer no volvió"
    assert "ARMAR FALLÓ" in ent.log() and "DESARMAR FALLÓ" in ent.log()


@pytest.mark.parametrize("caso", ["identica_a_la_base", "parcial_en_linea_valida", "fuentes_anotadas_como_base", "sin_marca_completa", "sin_fuentes"])
def test_copia_que_no_cubre_la_corrida_no_cierra_aunque_el_manifiesto_verifique(ent, caso):
    """Una copia de motor_decision.log idéntica a la línea base (o cortada en una línea válida) con SHA256SUMS correcto y la fuente ya con
    registros de la 4B NO es un cierre: el timer no se reanuda por el camino normal."""
    armado(ent); B, C = cierre_completo(ent)
    base = json.loads((ent.estado / "base.json").read_text())["ficheros"][str(ent.motor)]
    original = ent.motor.read_bytes()[: base["tam"]]
    motor_copia = C / "motor_decision.log"
    tsv = C / "FUENTES-al-copiar.tsv"
    def anotar(nombre, tam):
        lin = [l for l in tsv.read_text().splitlines() if not l.startswith(nombre + "\t")]
        tsv.write_text("\n".join(lin + [f"{nombre}\t{tam}"]) + "\n")
    if caso == "identica_a_la_base":
        motor_copia.write_bytes(original)
    elif caso == "parcial_en_linea_valida":
        with open(ent.motor, "ab") as fh:
            fh.write(b"registro 2 de la 4B\nregistro 3 de la 4B\n")            # la fuente siguió creciendo antes de que s40 la leyera
        anotar("motor_decision.log", ent.motor.stat().st_size)
        assert motor_copia.read_bytes().endswith(b"\n") and len(motor_copia.read_bytes()) > base["tam"]
    elif caso == "fuentes_anotadas_como_base":
        motor_copia.write_bytes(original); anotar("motor_decision.log", base["tam"])
    elif caso == "sin_marca_completa":
        os.remove(C / "COPIAS-COMPLETAS.ok")
    elif caso == "sin_fuentes":
        os.remove(tsv)
    reescribir_sumas(C)
    r = ent.run("cierre")
    assert "OK    copias/SHA256SUMS" in r.stdout, "el manifiesto es correcto: " + r.stdout
    assert r.returncode == 1 and "FALLO" in r.stdout, r.stdout
    if caso in ("identica_a_la_base", "parcial_en_linea_valida", "fuentes_anotadas_como_base"):
        assert "FALLO copia fiel de motor_decision.log" in r.stdout and "NO cubre la corrida" in r.stdout, r.stdout
    t0 = time.time()
    ent.run("vigilar", "--tope", str(int(t0) + 3), "--intervalo", "0.3", timeout=30)
    assert "REANUDADO_NORMAL" not in ent.log() and "REANUDADO_POR_TOPE" in ent.log()


def test_cierre_acepta_copia_que_cubre_la_corrida(ent):
    armado(ent); cierre_completo(ent)
    r = ent.run("cierre")
    assert r.returncode == 0 and "RESULTADO_CIERRE OK" in r.stdout, r.stdout


def test_formato_de_fuentes_al_copiar_lo_lee_el_cierre(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("cf_rot2", SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    p = tmp_path / "f.tsv"; p.write_text("motor_decision.log\t123\nfeed-v2/traza.jsonl\t0\n")
    assert m.leer_fuentes(str(p)) == {"motor_decision.log": 123, "feed-v2/traza.jsonl": 0}
    p.write_text("motor_decision.log\tmucho\n"); assert m.leer_fuentes(str(p)) == {}
    assert m.leer_fuentes(str(tmp_path / "no-existe")) == {}
