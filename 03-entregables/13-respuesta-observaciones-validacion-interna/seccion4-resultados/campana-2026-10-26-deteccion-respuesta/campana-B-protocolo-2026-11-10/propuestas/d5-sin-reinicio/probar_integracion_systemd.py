#!/usr/bin/env python3
"""Decisión E, solo banco: flujo completo de la COPIA integrada de d5_episodio.py (PuertaBanco) con el publicador derivado bajo una unidad systemd
temporal (User=nobody, Group=d5aud, UMask=0027; directorio 2750, ficheros 0640), retención `rotate 30` probada con `logrotate -f` real, datos
sintéticos (srv-dmz y agente simulados), SIN conexión al orquestador. Se ejecuta como root DENTRO del contenedor `cf-d5-integracion` (systemd PID 1).
Aprobado un caso solo si: unidad activa, mismo MainPID, NRestarts sin aumentar, journal nuevo sin parada ni arranque, publicación nueva DESPUÉS del
caso y las demás entidades (10.10.20.99 y 10.10.20.3) idénticas; más las condiciones propias del caso."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/banco")
import adaptador_banco as ab  # noqa: E402
import adaptador_banco_rot as abr  # noqa: E402
import hacer_d5_episodio_banco as hd  # noqa: E402
import probar_logrotate as pl  # noqa: E402
import probar_systemd as ps  # noqa: E402

EV, D5 = Path("/evidencia"), Path("/opt/d5")
K, OTRA, PREF = pl.K, pl.OTRA, pl.PREF
CHECKS = []


def chk(nombre, cond, detalle=""):
    CHECKS.append({"comprobacion": nombre, "ok": bool(cond), "detalle": detalle if not cond else ""})
    print(("OK   " if cond else "FALLA"), nombre, detalle if not cond else "", flush=True)
    return bool(cond)


class NftSimulado:
    def __init__(self):
        self.sets = {"bloqueados": {}, "limitados": {}}

    def __call__(self, peticion):
        op = peticion["operaciones"][0]
        if op["op"] == "listar":
            return {"ok": True, "estado": {"sets": {k: dict(v) for k, v in self.sets.items()}, "descartes_limite": {}}}
        if op["op"] == "retirar_origen":
            for v in self.sets.values():
                v.pop(op["ip"], None)
            return {"ok": True}
        return {"ok": False, "rechazo": "op_no_soportada"}


def cargar_banco():
    assert hd.main("/herramientas/d5_episodio.py", "/opt/d5/d5_episodio_banco.py") == 0
    spec = importlib.util.spec_from_file_location("d5_episodio_banco", "/opt/d5/d5_episodio_banco.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["d5_episodio_banco"] = m
    spec.loader.exec_module(m)
    return m


def arrancar_unidad(e, u):
    w = e.w
    args = ["--log", w / "motor.log", "--estado", w / "estado.json", "--clave-privada", w / "k.pem", "--salida-feed", w / "feed.json", "--salida-firma", w / "feed.sig",
            "--traza", w / "traza.jsonl", "--politica", "if_senal", "--seguir", "--sondeo-segundos", "0.05", "--refresco-segundos", "1.5",
            "--control-d5", e.ctl, "--d5-origen", K, "--d5-auditoria", e.aud]
    unit = ("[Unit]\nDescription=Integracion D5 banco (%s)\n[Service]\nType=simple\nUser=nobody\nGroup=d5aud\nUMask=0027\nWorkingDirectory=/opt/d5\n"
            "ExecStart=/usr/bin/python3 /opt/d5/publicar_feed_v2_d5.py %s\nRestart=always\nRestartSec=1\nStandardOutput=journal\nStandardError=journal\n" % (e.n, " ".join(str(a) for a in args)))
    Path("/run/systemd/system").mkdir(parents=True, exist_ok=True)
    Path("/run/systemd/system/%s.service" % u).write_text(unit)
    ps.sh("systemctl", "daemon-reload")
    ps.sh("systemctl", "start", u)
    return ps.espera(lambda: ps.show(u)["ActiveState"] == "active" and {x["ip"] for x in ps.feedj(w)["entradas"]} == {K, OTRA, PREF}, 20)


def caso(banco, nombre, falla_ack, tras_fallo):
    e = pl.Esc(nombre, rotate=30)
    u = "cf-d5-integ-" + nombre.lower()
    arrancada = arrancar_unidad(e, u)
    time.sleep(1.5)
    antes, jantes = ps.show(u), ps.journal(u)
    (e.ev / "antes.json").write_text(json.dumps(antes, indent=1, sort_keys=True))
    (e.ev / "journal-antes.txt").write_text(jantes)
    e0 = json.loads((e.w / "estado.json").read_text())
    if falla_ack:
        os.mkdir(str(e.ctl) + ".ack")
    llam, orig = [], ab.cli.solicitar_reset
    ab.cli.solicitar_reset = lambda *a, **k: (llam.append(1), orig(*a, **k))[1]
    traza = e.w / "agente-traza.jsonl"
    traza.write_text("")
    ad = abr.AdaptadorBancoRot(e.ctl, e.w / "feed.json", e.w / "estado.json", e.w / "traza.jsonl", e.aud, esperar_s=2.5 if falla_ack else 10.0)
    pu = banco.PuertaBanco(banco.RunnersBanco(ad, e.w / "feed.json", traza, NftSimulado()), registro=e.w / "puerta-banco.jsonl", espera_agente=2.0, espera_feed=8.0, sondeo=0.1)
    res = {}
    try:
        r1 = pu.preparar_episodio()
        res["primera"] = {"lista": r1["lista"], "bloqueada": r1["bloqueada"], "pasos": [p["paso"] for p in r1["historial"][0]["pasos"]]}
        extra = []
        if falla_ack:
            extra = [pu.preparar_episodio() for _ in range(2)] + [pu.una_vez()]
            res["llamadas_siguientes"] = [{"lista": x.get("lista"), "bloqueada": x.get("bloqueada")} for x in extra]
        if tras_fallo == "reanudar":
            os.rmdir(str(e.ctl) + ".ack")
            ad.esperar_s = 10.0
            pu.reanudar_manual("Mark (prueba de banco)", "acuse restablecido tras corregir el destino del acuse")
            r2 = pu.preparar_episodio()
            res["tras_reanudacion"] = {"lista": r2["lista"], "bloqueada": r2["bloqueada"]}
    finally:
        ab.cli.solicitar_reset = orig
    fin_feed = ps.feedj(e.w)
    n_traza = len(ab._jsonl(e.w / "traza.jsonl"))
    rc_lr = e.logrotate()                                            # retención de banco: `rotate 30`, logrotate real forzado
    nueva = ps.espera(lambda: ps.feedj(e.w)["secuencia"] > fin_feed["secuencia"] and len(ab._jsonl(e.w / "traza.jsonl")) > n_traza, 12)
    time.sleep(1.5)
    despues, jdesp = ps.show(u), ps.journal(u)
    (e.ev / "despues.json").write_text(json.dumps(despues, indent=1, sort_keys=True))
    (e.ev / "journal-despues.txt").write_text(jdesp)
    nuevas = jdesp[len(jantes):] if jdesp.startswith(jantes) else None
    e1 = json.loads((e.w / "estado.json").read_text())
    f1 = ps.feedj(e.w)
    otras_ok = all([v for k, v in e1["vigentes"].items() if k.startswith(ip + "|")] == [v for k, v in e0["vigentes"].items() if k.startswith(ip + "|")] and
                   [v for k, v in e1["escalada"].items() if k.startswith(ip + "@")] == [v for k, v in e0["escalada"].items() if k.startswith(ip + "@")] for ip in (OTRA, PREF)) \
        and {OTRA, PREF} <= {x["ip"] for x in f1["entradas"]}
    import auditoria_d5 as A
    ids = sorted({x["id"] for g in A.generaciones(e.aud) for x in A._leer_una(g)[1] if x.get("evento") == "consumido"})
    lector = {i: e.lector("d5lector", "d5aud", i)["diagnostico"] for i in ids}
    falta = (not arrancada or not jantes.strip() or not jdesp.strip() or nuevas is None)
    crit = {"unidad_activa": despues.get("ActiveState") == "active" and despues.get("SubState") == "running",
            "mismo_MainPID": antes.get("MainPID") == despues.get("MainPID") and antes.get("MainPID") not in (None, "0"),
            "NRestarts_no_aumenta": int(despues.get("NRestarts", -1)) <= int(antes.get("NRestarts", 99)),
            "journal_sin_parada_ni_arranque": nuevas is not None and not ps.PARADA.search(nuevas),
            "publicacion_nueva_tras_el_caso": nueva, "otras_entidades_conservadas": otras_ok, "logrotate_rc0": rc_lr == 0}
    servicio = "INDETERMINADO" if falta else ("PASA" if all(crit.values()) else "FALLA")
    reg = [x["evento"] for x in ab._jsonl(e.w / "puerta-banco.jsonl")]
    resumen = {"caso": nombre, "unidad": u, "servicio": servicio, "criterios": crit, "puerta": res, "solicitudes_reales": len(llam), "omitidas": pu.omitidas,
               "registro_de_la_puerta": reg, "lector_d5lector": {i: {k: v[k] for k in ("categoria", "publicacion", "secuencia_publicada")} for i, v in lector.items()},
               "observado": {"NRestarts": [antes.get("NRestarts"), despues.get("NRestarts")], "MainPID": [antes.get("MainPID"), despues.get("MainPID")]}}
    # --- condiciones propias del caso
    if nombre.startswith("I-A"):
        chk("%s: acuse válido -> la puerta deja continuar; 1 solicitud; sin reinicio" % nombre, res["primera"]["lista"] and not res["primera"]["bloqueada"] and len(llam) == 1 and servicio == "PASA", resumen)
        chk("%s: el lector (d5lector) reconstruye la solicitud: publicación confirmada" % nombre, len(lector) == 1 and all(v["publicacion"] == "confirmada" for v in lector.values()), lector)
    elif nombre.startswith("I-B"):
        chk("%s: acuse no escribible -> puerta fallida y BLOQUEADA; las 3 llamadas siguientes no solicitan; 1 solicitud real" % nombre,
            not res["primera"]["lista"] and res["primera"]["bloqueada"] and all(not x["lista"] and x["bloqueada"] for x in res["llamadas_siguientes"]) and len(llam) == 1 and pu.omitidas == 3, resumen)
        chk("%s: servicio continuo y limpieza confirmable por la auditoría (reportados por separado)" % nombre, servicio == "PASA" and all(v["publicacion"] == "confirmada" for v in lector.values()), resumen)
        chk("%s: evidencia del caso conservada" % nombre, any(f.name.startswith("control.json.evidencia-") for f in e.w.iterdir()), sorted(x.name for x in e.w.iterdir()))
    else:
        chk("%s: tras la reanudación manual registrada se emite UNA solicitud nueva y la puerta continúa" % nombre, res["tras_reanudacion"]["lista"] and len(llam) == 2 and "reanudacion_manual" in reg and servicio == "PASA", resumen)
    (e.ev / "resultado.json").write_text(json.dumps(resumen, indent=1, sort_keys=True, ensure_ascii=False, default=str))
    for x in e.w.iterdir():
        if x.is_file() and x.name != "k.pem":
            shutil.copy2(x, e.ev / x.name)
    e.guardar(None)
    ps.sh("systemctl", "stop", u)
    Path("/run/systemd/system/%s.service" % u).unlink()
    ps.sh("systemctl", "daemon-reload")
    return resumen


def main():
    EV.mkdir(exist_ok=True)
    hashes = ps.preparar_codigo()
    banco = cargar_banco()
    pl.preparar_entorno()
    hashes["d5_episodio_banco.py (derivado)"] = ps.sha("/opt/d5/d5_episodio_banco.py")
    hashes["d5_episodio.py (original, solo lectura)"] = ps.sha("/herramientas/d5_episodio.py")
    for n in ("hacer_d5_episodio_banco.py", "test_integracion_d5.py", "mutar_integracion_d5.py", "probar_integracion_systemd.py"):
        hashes[n] = ps.sha("/banco/" + n)
    (EV / "sha256-completos.json").write_text(json.dumps(hashes, indent=1, sort_keys=True))
    ent = [ps.sh("systemctl", "--version").stdout.splitlines()[0], "logrotate " + ps.sh("logrotate", "--version").stdout.splitlines()[0], "virt=" + ps.sh("systemd-detect-virt").stdout.strip(),
           ps.sh("uname", "-sr").stdout.strip(), "python=" + sys.version.split()[0], "red=" + repr(ps.sh("sh", "-c", "ls /sys/class/net").stdout.split())]
    (EV / "entorno.txt").write_text("\n".join(ent) + "\n")
    chk("versión: derivado del publicador idéntico al validado", hashes["publicar_feed_v2_d5.py"].startswith("58e2a0b2b0690892"))
    out = [caso(banco, "I-A-acuse-valido", False, None), caso(banco, "I-B-acuse-no-escribible-bloqueo", True, None), caso(banco, "I-C-reanudacion-manual", True, "reanudar")]
    (EV / "resumen.json").write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False, default=str))
    (EV / "comprobaciones.json").write_text(json.dumps(CHECKS, indent=1, ensure_ascii=False))
    mal = [c for c in CHECKS if not c["ok"]]
    print("\n%d comprobaciones, %d fallan" % (len(CHECKS), len(mal)))
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main())
