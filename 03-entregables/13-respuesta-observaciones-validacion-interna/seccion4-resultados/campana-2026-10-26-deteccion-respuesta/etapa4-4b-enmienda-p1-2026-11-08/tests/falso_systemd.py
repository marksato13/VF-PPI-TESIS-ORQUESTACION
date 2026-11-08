#!/usr/bin/env python3
"""systemctl y systemd-run FALSOS para el banco de cf_4b_rotacion.py (sin systemd). Estado en $FAKE_DIR.

  falso_systemd.py systemctl  <args>      is-active U | show U -pP... | start U | stop U...
  falso_systemd.py systemd-run <args>     crea la unidad transitoria (timer o servicio)
Fallos inducidos con $FAKE_FALLA (separados por comas): run-tope, run-vigia, elapse-distinto, vigia-cae, stop-no-para, timer-dispara, start-falla (systemctl start logrotate.timer falla).
"""
import datetime as dt
import os
import sys
from pathlib import Path

D = Path(os.environ["FAKE_DIR"])
(D / "activo").mkdir(parents=True, exist_ok=True)
(D / "props").mkdir(parents=True, exist_ok=True)
FALLA = set(filter(None, os.environ.get("FAKE_FALLA", "").split(",")))


def llamada(txt):
    with open(D / "llamadas.log", "a") as fh:
        fh.write(f"{txt}\n")


def estado(u):
    p = D / "activo" / u
    return p.read_text().strip() if p.exists() else "inactive"


def poner(u, v):
    (D / "activo" / u).write_text(v)


def prop(u, k):
    p = D / "props" / f"{u}.{k}"
    return p.read_text().strip() if p.exists() else ""


def systemctl(a):
    cmd = a[0]
    llamada("systemctl " + " ".join(a))
    if cmd == "is-active":
        print(estado(a[1])); return 0 if estado(a[1]) == "active" else 3
    if cmd == "show":
        u = a[1]
        ps = [x[2:] for x in a[2:] if x.startswith("-p")]
        for k in ps:
            print(f"{k}={prop(u, k)}")
        return 0
    if cmd == "start":
        if a[1] == "logrotate.timer" and "start-falla" in FALLA:
            print("Failed to start logrotate.timer: Unit is masked / sin permiso"); return 1
        poner(a[1], "active"); return 0
    if cmd == "stop":
        for u in a[1:]:
            if u == "logrotate.timer" and "stop-no-para" in FALLA:
                continue
            poner(u, "inactive")
            if u == "logrotate.timer" and "timer-dispara" in FALLA:
                (D / "props" / "logrotate.timer.LastTriggerUSec").write_text("disparo-durante-el-stop")
        return 0
    return 1


def systemd_run(a):
    llamada("systemd-run " + " ".join(a))
    unit = next(x.split("=", 1)[1] for x in a if x.startswith("--unit="))
    cal = next((x.split("=", 1)[1] for x in a if x.startswith("--on-calendar=")), None)
    if cal:
        if "run-tope" in FALLA:
            print("Failed to start transient timer unit"); return 1
        poner(unit + ".timer", "active")
        when = dt.datetime.strptime(cal, "%Y-%m-%d %H:%M:%S UTC")
        if "elapse-distinto" in FALLA:
            when += dt.timedelta(hours=1)
        (D / "props" / f"{unit}.timer.NextElapseUSecRealtime").write_text(when.strftime("%a %Y-%m-%d %H:%M:%S UTC"))
    else:
        if "run-vigia" in FALLA:
            print("Failed to start transient service unit"); return 1
        poner(unit + ".service", "inactive" if "vigia-cae" in FALLA else "active")
    return 0


if __name__ == "__main__":
    modo, args = sys.argv[1], sys.argv[2:]
    sys.exit(systemctl(args) if modo == "systemctl" else systemd_run(args))
