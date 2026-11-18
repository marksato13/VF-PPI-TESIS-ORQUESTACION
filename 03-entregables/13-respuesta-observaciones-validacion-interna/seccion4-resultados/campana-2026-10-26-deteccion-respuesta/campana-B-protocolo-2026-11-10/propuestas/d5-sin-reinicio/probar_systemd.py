#!/usr/bin/env python3
"""Pendiente #1 (banco con systemd real, desechable, sin red; datos sintéticos). Se ejecuta DENTRO del contenedor `cf-d5-systemd`
(systemd como PID 1). Cada caso corre el publicador derivado (versión validada) bajo una unidad temporal en /run/systemd/system,
con Restart=always (un reinicio subiría NRestarts) y registra, antes y después: estado de la unidad, NRestarts, MainPID y journal.
Aprobado SOLO si: unidad activa, mismo MainPID, NRestarts no aumenta, el journal NUEVO no muestra parada ni arranque y hay una
publicación nueva DESPUÉS del caso. Si falta evidencia -> INDETERMINADO. No toca d5_episodio.py, el orquestador ni ningún host."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/banco")
import adaptador_banco as ab  # noqa: E402
import hacer_publicador_d5 as h  # noqa: E402

EV, ENG, D5, BASE = Path("/evidencia"), Path("/producto-etapa3/scripts/engine"), Path("/opt/d5"), Path("/var/tmp/d5case")
K, OTRA, PREF = "10.10.20.30", "10.10.20.99", "10.10.20.3"
PARADA = re.compile(r"Started |Starting |Stopped |Stopping |Main process exited|Scheduled restart|Deactivated|Failed with result|Stop job", re.I)


def sh(*a, check=False):
    return subprocess.run(a, capture_output=True, text=True, check=check)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def show(u):
    r = sh("systemctl", "show", u, "-p", "ActiveState,SubState,NRestarts,MainPID,InvocationID,ActiveEnterTimestamp,ExecMainStartTimestamp,Result")
    d = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
    return d


def journal(u):
    return sh("journalctl", "-u", u + ".service", "--no-pager", "-o", "short-iso-precise").stdout


def decision(ip, regla, accion, n):
    return {"event": "decision", "entity_ip": ip, "decision_id": "d%s|%s" % (n, ip), "window_end_utc": None, "logged_at": time.time(),
            "decidido_en": time.time(), "detector_name": "if_limpio_2026_10", "score": -0.1, "decision": "PERMIT",
            "heuristicos": [{"heuristico": regla, "accion": accion, "motivo": "sintético"}]}


def jl(p):
    return ab._jsonl(p)


def feedj(w):
    try:
        return json.loads((w / "feed.json").read_text())
    except (OSError, ValueError):
        return {"entradas": [], "secuencia": 0, "generado": 0}


def espera(cond, s):
    fin = time.time() + s
    while time.time() < fin:
        try:
            if cond():
                return True
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(0.1)
    return False


def preparar_codigo():
    if D5.exists():
        shutil.rmtree(D5)
    D5.mkdir(parents=True)
    for f in ENG.glob("*.py"):
        shutil.copy(f, D5 / f.name)
    orig = ENG / "publicar_feed_v2.py"
    assert sha(orig).startswith("5733f17d39bfa5fe")
    assert h.main(str(orig), str(D5 / "publicar_feed_v2_d5.py")) == 0
    shutil.copy(D5 / "publicar_feed_v2_d5.py", EV / "publicar_feed_v2_d5.py.generado")
    return {"publicar_feed_v2.py": sha(orig), "publicar_feed_v2_d5.py": sha(D5 / "publicar_feed_v2_d5.py"),
            **{n: sha("/banco/" + n) for n in ("adaptador_banco.py", "d5_control.py", "hacer_publicador_d5.py", "mutar_d5_sin_reinicio.py",
                                               "test_adaptador_extremo_a_extremo.py", "test_d5_sin_reinicio.py", "test_flujo_completo.py")}}


def caso(nombre, falla_ack, falla_audit, sin_audit_en_unidad, adaptador_con_audit):
    u, w, ev = "cf-d5-banco-" + nombre.lower(), BASE / nombre, EV / nombre
    if w.exists():
        shutil.rmtree(w)
    w.mkdir(parents=True)
    ev.mkdir(parents=True, exist_ok=True)
    sh("openssl", "genpkey", "-algorithm", "ed25519", "-out", str(w / "k.pem"), check=True)
    (w / "motor.log").write_text("".join(json.dumps(decision(ip, r, a, n)) + "\n" for n, (ip, r, a) in enumerate(
        [(K, "brute_force", "BLOCK"), (OTRA, "http_abuse", "LIMIT"), (PREF, "http_abuse", "LIMIT")])))
    aud = w / "d5-auditoria.jsonl"
    if falla_ack:
        os.mkdir(str(w / "control.json.ack"))                       # el acuse no se puede escribir
    if falla_audit:
        os.mkdir(str(aud))                                          # la auditoría no se puede escribir
    shutil.chown(w, "nobody", "nogroup")
    shutil.chown(w / "k.pem", "nobody", "nogroup")
    args = ["--log", w / "motor.log", "--estado", w / "estado.json", "--clave-privada", w / "k.pem", "--salida-feed", w / "feed.json",
            "--salida-firma", w / "feed.sig", "--traza", w / "traza.jsonl", "--politica", "if_senal", "--seguir", "--sondeo-segundos", "0.05",
            "--refresco-segundos", "1.5", "--control-d5", w / "control.json", "--d5-origen", K]
    if not sin_audit_en_unidad:
        args += ["--d5-auditoria", aud]
    unit = ("[Unit]\nDescription=Banco D5 temporal (%s)\n[Service]\nType=simple\nUser=nobody\nWorkingDirectory=/opt/d5\nExecStart=/usr/bin/python3 /opt/d5/publicar_feed_v2_d5.py %s\n"
            "Restart=always\nRestartSec=1\nStandardOutput=journal\nStandardError=journal\n" % (nombre, " ".join(str(a) for a in args)))
    Path("/run/systemd/system").mkdir(parents=True, exist_ok=True)
    Path("/run/systemd/system/%s.service" % u).write_text(unit)
    sh("systemctl", "daemon-reload")
    sh("systemctl", "start", u)
    arrancada = espera(lambda: show(u)["ActiveState"] == "active" and {e["ip"] for e in feedj(w)["entradas"]} == {K, OTRA, PREF}, 20)
    time.sleep(1.5)
    antes, jantes = show(u), journal(u)
    (ev / "antes.json").write_text(json.dumps(antes, indent=1, sort_keys=True))
    (ev / "journal-antes.txt").write_text(jantes)
    e0 = json.loads((w / "estado.json").read_text()) if (w / "estado.json").exists() else {}
    # --- el caso ---
    llamadas = []
    orig = ab.cli.solicitar_reset
    ab.cli.solicitar_reset = lambda *a, **k: (llamadas.append(1), orig(*a, **k))[1]
    ad = ab.AdaptadorBanco(w / "control.json", w / "feed.json", w / "estado.json", w / "traza.jsonl", aud if adaptador_con_audit else None, esperar_s=3.0)
    try:
        r = ad.limpiar(K)
    finally:
        ab.cli.solicitar_reset = orig
    fin_caso = feedj(w)
    n_traza = len(jl(w / "traza.jsonl"))
    nueva = espera(lambda: feedj(w)["secuencia"] > fin_caso["secuencia"] and len(jl(w / "traza.jsonl")) > n_traza, 12)
    time.sleep(1.5)
    despues, jdesp = show(u), journal(u)
    (ev / "despues.json").write_text(json.dumps(despues, indent=1, sort_keys=True))
    (ev / "journal-despues.txt").write_text(jdesp)
    nuevas = jdesp[len(jantes):] if jdesp.startswith(jantes) else None
    f1 = feedj(w)
    e1 = json.loads((w / "estado.json").read_text()) if (w / "estado.json").exists() else {}
    sin_k = K not in {e["ip"] for e in f1["entradas"]} and not [k for k in e1.get("vigentes", {}) if k.split("|")[0] == K]
    otras_ok = {OTRA, PREF} <= {e["ip"] for e in f1["entradas"]}
    stderr = [l for l in (nuevas or "").splitlines() if "d5:" in l]
    evidencia = {x.name for x in w.iterdir()}
    for x in w.iterdir():                                           # copia de la evidencia del caso (clave privada sintética excluida)
        if x.name != "k.pem" and x.is_file():
            shutil.copy(x, ev / x.name)
    # --- criterios del servicio ---
    falta = (not arrancada or not jantes.strip() or not jdesp.strip() or nuevas is None or "MainPID" not in antes or "MainPID" not in despues)
    crit = {"unidad_activa": despues.get("ActiveState") == "active" and despues.get("SubState") == "running",
            "mismo_MainPID": antes.get("MainPID") == despues.get("MainPID") and antes.get("MainPID") not in (None, "0"),
            "NRestarts_no_aumenta": int(despues.get("NRestarts", -1)) <= int(antes.get("NRestarts", 99)) and despues.get("NRestarts") is not None,
            "journal_sin_parada_ni_arranque": nuevas is not None and not PARADA.search(nuevas),
            "publicacion_nueva_tras_el_caso": nueva,
            "una_sola_solicitud": len(llamadas) == 1}
    servicio = "INDETERMINADO" if falta else ("PASA" if all(crit.values()) else "FALLA")
    # --- limpieza ---
    kal_en_audit = [x for x in jl(aud) if x.get("evento") == "consumido"] if aud.is_file() else []
    if r["ok"]:
        limpieza = "confirmada" if sin_k else "NO confirmada"
        via = "acuse + feed + estado" + (" + auditoría" if kal_en_audit else " (sin auditoría)")
    elif r.get("categoria") == "consumida_y_publicada":
        limpieza, via = ("confirmada" if sin_k else "NO confirmada"), "auditoría del publicador (consumido+publicado) + feed + estado, sin acuse"
    else:
        limpieza, via = "indeterminada", "el adaptador no pudo determinarlo (categoría %s); feed/estado se guardan pero no deciden" % r.get("categoria")
    res = {"caso": nombre, "unidad": u, "servicio": servicio, "criterios": crit, "limpieza": limpieza, "limpieza_via": via,
           "operacion": {k: r.get(k) for k in ("ok", "estado", "rc", "categoria", "determinada", "incierto", "secuencia", "evidencia")},
           "observado": {"K_fuera_del_feed_y_estado": sin_k, "otras_entidades_en_feed": otras_ok, "lineas_d5_en_journal": stderr,
                         "NRestarts": [antes.get("NRestarts"), despues.get("NRestarts")], "MainPID": [antes.get("MainPID"), despues.get("MainPID")],
                         "secuencia_feed": [fin_caso["secuencia"], f1["secuencia"]], "ficheros_del_caso": sorted(evidencia)},
           "rutas": {"evidencia": "evidencia-systemd/%s/" % nombre}}
    (ev / "resultado.json").write_text(json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False))
    sh("systemctl", "stop", u)
    Path("/run/systemd/system/%s.service" % u).unlink()
    sh("systemctl", "daemon-reload")
    return res


def main():
    EV.mkdir(exist_ok=True)
    hashes = preparar_codigo()
    ent = "\n".join([sh("systemctl", "--version").stdout.splitlines()[0], "virt=" + sh("systemd-detect-virt").stdout.strip(), sh("uname", "-sr").stdout.strip(),
                     sh("sh", "-c", ". /etc/os-release; echo $PRETTY_NAME").stdout.strip(), "python=" + sys.version.split()[0],
                     "estado_sistema=" + sh("systemctl", "is-system-running").stdout.strip(), "fallidas=" + sh("systemctl", "--failed", "--no-legend").stdout.strip(),
                     "red=" + sh("sh", "-c", "ls /sys/class/net").stdout.split().__repr__()])
    (EV / "entorno.txt").write_text(ent + "\n")
    (EV / "sha256-completos.json").write_text(json.dumps(hashes, indent=1, sort_keys=True))
    out = [caso("A", False, False, False, True),                    # limpieza con acuse
           caso("B", True, False, False, True),                     # limpieza con fallo de escritura del acuse
           caso("C", False, True, False, True),                     # fallo de escritura de la auditoría
           caso("D", True, False, True, False)]                     # acuse perdido y sin auditoría: indeterminada
    (EV / "resumen.json").write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False))
    for o in out:
        print(o["caso"], o["servicio"], "limpieza=" + o["limpieza"], o["observado"]["NRestarts"], o["observado"]["MainPID"], o["criterios"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
