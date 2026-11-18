#!/usr/bin/env python3
"""Pendiente #3 con logrotate REAL (banco desechable, sin red, datos sintéticos, rutas temporales bajo /var/tmp/d5lr). Se ejecuta como root DENTRO
del contenedor. Publicador derivado (versión validada) como proceso del usuario `nobody` con umask 027; lector como `d5lector` (solo grupo
d5aud, sin permiso de escritura); `intruso` sin grupo. La rotación la hace `logrotate -f` por renombrado (nocopytruncate, compress, delaycompress).
Para colocar la rotación ENTRE `consumido` y `publicado` de forma determinista, un envoltorio de `openssl` (primero en PATH del publicador) espera
mientras exista un fichero-compuerta; el publicador firma entre ambas líneas de auditoría. No toca d5_episodio.py, el orquestador ni ningún host."""
import grp
import json
import os
import pwd
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, "/banco")
import adaptador_banco as ab  # noqa: E402
import adaptador_banco_rot as abr  # noqa: E402
import auditoria_d5 as A  # noqa: E402
import d5_control as cli  # noqa: E402
import probar_systemd as ps  # noqa: E402

EV, BASE, CONF, GATE = Path("/evidencia"), Path("/var/tmp/d5lr"), Path("/etc/d5lr"), Path("/var/tmp/d5lr/GATE")
K, OTRA, PREF = "10.10.20.30", "10.10.20.99", "10.10.20.3"
CHECKS = []

PLANTILLA = """{aud}/d5-auditoria.jsonl {{
    daily
    rotate {rotate}
    missingok
    notifempty
    compress
    delaycompress
    nocopytruncate
    create 0640 nobody d5aud
}}
"""


def chk(nombre, cond, detalle=""):
    CHECKS.append({"comprobacion": nombre, "ok": bool(cond), "detalle": detalle})
    print(("OK   " if cond else "FALLA"), nombre, detalle if not cond else "", flush=True)
    return bool(cond)


def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)


def espera(cond, s):
    fin = time.time() + s
    while time.time() < fin:
        try:
            if cond():
                return True
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(0.01)
    return False


def preparar_entorno():
    sh("groupadd", "d5aud")
    sh("useradd", "-M", "-N", "-g", "d5aud", "-s", "/usr/sbin/nologin", "d5lector")
    sh("useradd", "-M", "-N", "-g", "nogroup", "-s", "/usr/sbin/nologin", "intruso")
    Path("/opt/shim").mkdir(parents=True, exist_ok=True)
    Path("/opt/shim/openssl").write_text("#!/bin/sh\nwhile [ -e %s ]; do sleep 0.02; done\nexec /usr/bin/openssl \"$@\"\n" % GATE)
    os.chmod("/opt/shim/openssl", 0o755)
    CONF.mkdir(parents=True, exist_ok=True)
    BASE.mkdir(parents=True, exist_ok=True)
    os.chmod(BASE, 0o755)


class Esc:
    def __init__(self, nombre, rotate):
        self.n, self.ev = nombre, EV / nombre
        self.ev.mkdir(parents=True, exist_ok=True)
        self.raiz = BASE / nombre
        shutil.rmtree(self.raiz, ignore_errors=True)
        self.aud_dir, self.w = self.raiz / "aud", self.raiz / "work"
        for d in (self.raiz, self.aud_dir, self.w):
            d.mkdir(parents=True)
        os.chmod(self.raiz, 0o755)
        for d in (self.aud_dir, self.w):
            shutil.chown(d, "nobody", "d5aud")
            os.chmod(d, 0o2750)
        self.aud, self.ctl = self.aud_dir / "d5-auditoria.jsonl", self.w / "control.json"
        self.conf, self.state = CONF / (nombre + ".conf"), self.raiz / "logrotate.state"
        self.conf.write_text(PLANTILLA.format(aud=self.aud_dir, rotate=rotate))
        os.chmod(self.conf, 0o644)
        shutil.copy(self.conf, self.ev / "logrotate.conf")
        sh("openssl", "genpkey", "-algorithm", "ed25519", "-out", str(self.w / "k.pem"))
        shutil.chown(self.w / "k.pem", "nobody", "d5aud")
        os.chmod(self.w / "k.pem", 0o600)
        (self.w / "motor.log").write_text("".join(json.dumps(ps.decision(ip, r, a, n)) + "\n" for n, (ip, r, a) in enumerate(
            [(K, "brute_force", "BLOCK"), (OTRA, "http_abuse", "LIMIT"), (PREF, "http_abuse", "LIMIT")])))
        self.nrot, self.p, self.err = 0, None, None

    def arrancar(self):
        self.err = open(self.w / "stderr.txt", "w")
        w = self.w
        self.p = subprocess.Popen(["/usr/bin/python3", "/opt/d5/publicar_feed_v2_d5.py", "--log", str(w / "motor.log"), "--estado", str(w / "estado.json"),
                                   "--clave-privada", str(w / "k.pem"), "--salida-feed", str(w / "feed.json"), "--salida-firma", str(w / "feed.sig"),
                                   "--traza", str(w / "traza.jsonl"), "--politica", "if_senal", "--seguir", "--sondeo-segundos", "0.05",
                                   "--refresco-segundos", "600", "--control-d5", str(self.ctl), "--d5-origen", K, "--d5-auditoria", str(self.aud)],
                                  user="nobody", group="d5aud", umask=0o027, cwd="/opt/d5", stdout=subprocess.DEVNULL, stderr=self.err,
                                  env={"PATH": "/opt/shim:/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
        ok = espera(lambda: {e["ip"] for e in json.loads((w / "feed.json").read_text())["entradas"]} == {K, OTRA, PREF}, 15)
        chk("%s: publicador arrancado como nobody (feed inicial con 3 entidades)" % self.n, ok)
        self.pid, self.t0 = self.p.pid, open("/proc/%d/stat" % self.p.pid).read().rsplit(")", 1)[1].split()[19]

    def vivo(self):
        return self.p.poll() is None and open("/proc/%d/stat" % self.p.pid).read().rsplit(")", 1)[1].split()[19] == self.t0

    def logrotate(self):
        self.nrot += 1
        r = sh("logrotate", "-v", "-f", "-s", str(self.state), str(self.conf))
        (self.ev / ("logrotate-%02d.log" % self.nrot)).write_text("rc=%d\n--- stdout\n%s\n--- stderr\n%s\n" % (r.returncode, r.stdout, r.stderr))
        return r.returncode

    def eventos(self):
        return {os.path.basename(g): [x["evento"] + ":" + str(x.get("id")) for x in ab._jsonl(g)] if not g.endswith(".gz") else
                [x["evento"] + ":" + str(x.get("id")) for x in A._leer_una(g)[1]] for g in A.generaciones(self.aud)}

    def permisos(self):
        out = []
        for p in [str(self.aud_dir), str(self.w)] + A.generaciones(self.aud):
            st = os.stat(p)
            out.append({"ruta": p, "modo": oct(st.st_mode & 0o7777), "propietario": pwd.getpwuid(st.st_uid).pw_name, "grupo": grp.getgrgid(st.st_gid).gr_name})
        return out

    def lector(self, usuario, grupo, id_, probar=False):
        r = subprocess.run(["/usr/bin/python3", "-I", "/banco/lector_solo_lectura.py", id_, K, str(self.w), str(self.aud)] + (["--probar"] if probar else []),
                           capture_output=True, text=True, user=usuario, group=grupo, extra_groups=[], env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
        try:
            return json.loads(r.stdout)
        except ValueError:
            return {"error": r.stderr[-400:], "rc": r.returncode}

    def guardar(self, extra=None):
        d = self.ev / "auditoria"
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir()
        for g in A.generaciones(self.aud):
            if os.path.isfile(g):
                shutil.copy2(g, d)
        for f in ("stderr.txt", "traza.jsonl"):
            if (self.w / f).exists():
                shutil.copy2(self.w / f, self.ev / f)
        (self.ev / "permisos.json").write_text(json.dumps(self.permisos(), indent=1))
        (self.ev / "generaciones.json").write_text(json.dumps(self.eventos(), indent=1, sort_keys=True))
        if extra is not None:
            (self.ev / "resultado.json").write_text(json.dumps(extra, indent=1, sort_keys=True, ensure_ascii=False, default=str))

    def parar(self):
        if self.p and self.p.poll() is None:
            self.p.terminate()
            self.p.wait(5)
        if self.err:
            self.err.close()


def con_compuerta(e, accion_entre, id_="lr-1", falla_ack=False, adaptador=False):
    """Pide una limpieza con el publicador bloqueado al firmar; espera `consumido`; rota con logrotate real; libera; deja que cierre."""
    if falla_ack:
        os.mkdir(str(e.ctl) + ".ack")
    GATE.touch()
    res, llamadas = {}, []
    orig = ab.cli.solicitar_reset
    ab.cli.solicitar_reset = lambda *a, **k: (llamadas.append(1), orig(*a, **k))[1]
    try:
        if adaptador:
            ad = abr.AdaptadorBancoRot(e.ctl, e.w / "feed.json", e.w / "estado.json", e.w / "traza.jsonl", e.aud, esperar_s=12.0)
            t = threading.Thread(target=lambda: res.update(r=ad.limpiar(K)))
        else:
            t = threading.Thread(target=lambda: res.update(r=cli.solicitar_reset(e.ctl, K, esperar_s=20, id_=id_)))
        t.start()
        ok = espera(lambda: any(x.get("evento") == "consumido" for x in ab._jsonl(e.aud)), 10)
        chk("%s: `consumido` escrito mientras `publicado` aún no (compuerta)" % e.n, ok and not any(x.get("evento") == "publicado" for x in ab._jsonl(e.aud)))
        accion_entre()                                              # logrotate real entre consumido y publicado
        GATE.unlink()
        espera(lambda: any(x.get("evento") == "publicado" for g in A.generaciones(e.aud) for x in (A._leer_una(g)[1])), 10)
        t.join(30)
    finally:
        ab.cli.solicitar_reset = orig
        GATE.unlink(missing_ok=True)
    return res.get("r"), len(llamadas)


def s1():
    e = Esc("S1-determinista-entre-consumido-y-publicado", rotate=10)
    e.arrancar()
    r1, n = con_compuerta(e, lambda: chk("S1: logrotate real rotó (rc 0)", e.logrotate() == 0))
    ev1 = e.eventos()
    chk("S1: consumido quedó en .1 y publicado en el fichero actual (ficheros distintos)", ev1.get("d5-auditoria.jsonl.1") == ["consumido:lr-1"] and ev1.get("d5-auditoria.jsonl") == ["publicado:lr-1"], ev1)
    chk("S1: el publicador siguió escribiendo tras la rotación y el cliente recibió acuse", r1 and r1.get("ok") and e.vivo(), r1)
    p1 = {x["ruta"].split("/")[-1]: x for x in e.permisos()}
    chk("S1: el fichero actual creado por logrotate es 0640 nobody:d5aud y el publicador lo sigue usando", p1["d5-auditoria.jsonl"]["modo"] == "0o640" and p1["d5-auditoria.jsonl"]["propietario"] == "nobody" and p1["d5-auditoria.jsonl"]["grupo"] == "d5aud", p1)
    l1 = e.lector("d5lector", "d5aud", "lr-1", probar=True)
    d = l1["diagnostico"]
    chk("S1: el lector (d5lector, solo lectura) reconstruye id y secuencia con archivos distintos", d["categoria"] == "consumida_y_publicada" and d["publicacion"] == "confirmada" and d["secuencia_publicada"] == r1["secuencia"] and len(d["generaciones_del_id"]) == 2, l1)
    pe = l1["probar_escritura"]
    chk("S1: el lector no puede anexar, renombrar, borrar ni crear en el directorio", all(v == "PermissionError" for k, v in pe.items() if k != "ruta"), pe)
    # segunda rotación: consumido pasa a .2.gz
    chk("S1: segunda rotación real (rc 0)", e.logrotate() == 0)
    ev2 = e.eventos()
    chk("S1: tras la segunda rotación consumido está COMPRIMIDO (.2.gz) y publicado en .1", "d5-auditoria.jsonl.2.gz" in ev2 and ev2["d5-auditoria.jsonl.2.gz"] == ["consumido:lr-1"] and ev2.get("d5-auditoria.jsonl.1") == ["publicado:lr-1"], ev2)
    l2 = e.lector("d5lector", "d5aud", "lr-1")
    d2 = l2["diagnostico"]
    chk("S1: el lector reconstruye id y secuencia con una generación comprimida", d2["categoria"] == "consumida_y_publicada" and d2["secuencia_publicada"] == r1["secuencia"] and d2["publicacion"] == "confirmada" and "d5-auditoria.jsonl.2.gz" in d2["generaciones_del_id"], l2)
    pz = {x["ruta"].split("/")[-1]: x for x in e.permisos()}
    chk("S1: la generación comprimida conserva 0640 nobody:d5aud", pz["d5-auditoria.jsonl.2.gz"]["modo"] == "0o640" and pz["d5-auditoria.jsonl.2.gz"]["propietario"] == "nobody" and pz["d5-auditoria.jsonl.2.gz"]["grupo"] == "d5aud", pz)
    # el publicador sigue escribiendo tras DOS rotaciones
    r3 = cli.solicitar_reset(e.ctl, K, esperar_s=10, id_="lr-3")
    ev3 = e.eventos()
    chk("S1: tras dos rotaciones el publicador sigue escribiendo (nuevo id en el fichero actual) y sin reinicio", r3["ok"] and ev3.get("d5-auditoria.jsonl") == ["consumido:lr-3", "publicado:lr-3"] and e.vivo(), ev3)
    l3 = e.lector("d5lector", "d5aud", "lr-3")
    chk("S1: el lector reconstruye el id nuevo", l3["diagnostico"]["categoria"] == "consumida_y_publicada" and l3["diagnostico"]["secuencia_publicada"] == r3["secuencia"])
    li = e.lector("intruso", "nogroup", "lr-1")
    chk("S1: un usuario sin grupo (intruso) no accede: listado denegado y el id queda sin confirmar", li["listado_directorio"] == "PermissionError" and li["diagnostico"]["publicacion"] == "publicación sin confirmar", li)
    e.guardar({"acuse_lr1": r1, "acuse_lr3": r3, "lector_lr1_tras_rotacion1": l1, "lector_lr1_con_gz": l2, "lector_lr3": l3, "lector_intruso": li, "solicitudes_lr1": n})
    e.parar()


def s23():
    for nombre, perder in (("S2-generacion-perdida", True), ("S3-comprimida-acuse-no-escribible", False)):
        e = Esc(nombre, rotate=10)
        e.arrancar()
        # rotación 1 entre consumido y publicado; rotación 2 después de publicado (consumido -> .2.gz)
        res, llam = {}, []
        os.mkdir(str(e.ctl) + ".ack")
        GATE.touch()
        orig = ab.cli.solicitar_reset
        ab.cli.solicitar_reset = lambda *a, **k: (llam.append(1), orig(*a, **k))[1]
        try:
            ad = abr.AdaptadorBancoRot(e.ctl, e.w / "feed.json", e.w / "estado.json", e.w / "traza.jsonl", e.aud, esperar_s=12.0)
            t = threading.Thread(target=lambda: res.update(r=ad.limpiar(K)))
            t.start()
            espera(lambda: any(x.get("evento") == "consumido" for x in ab._jsonl(e.aud)), 10)
            e.logrotate()
            GATE.unlink()
            espera(lambda: any(x.get("evento") == "publicado" for g in A.generaciones(e.aud) for x in A._leer_una(g)[1]), 10)
            e.logrotate()
            if perder:
                for g in A.generaciones(e.aud):
                    if g.endswith(".2.gz"):
                        os.unlink(g)                                # se pierde la generación comprimida con `consumido`
            t.join(40)
        finally:
            ab.cli.solicitar_reset = orig
            GATE.unlink(missing_ok=True)
        r = res["r"]
        chk("%s: una sola solicitud, fallida, sin acuse, servicio vivo" % nombre, len(llam) == 1 and not r["ok"] and r["estado"] == "sin_acuse_procesada" and e.vivo(), r)
        chk("%s: ningún control pendiente (no se emitió otra solicitud)" % nombre, not e.ctl.exists())
        if perder:
            chk("S2: generación perdida -> «publicación sin confirmar», incierta, traza y evidencia conservadas", r["publicacion"] == "publicación sin confirmar" and r["incierto"] and r["categoria"] == "indeterminada" and r["secuencia"] is None, r)
        else:
            chk("S3: con la generación comprimida intacta se reconstruye aunque falle el acuse", r["categoria"] == "consumida_y_publicada" and r["publicacion"] == "confirmada" and r["determinada"] and r["secuencia"] > 0, r)
        chk("%s: evidencia y copia de la traza conservadas" % nombre, Path(r["evidencia"]).exists() and Path(r["traza_auditoria"]).is_dir() and os.listdir(r["traza_auditoria"]), r)
        for p in (r["evidencia"], r["traza_auditoria"]):
            if os.path.isdir(p):
                shutil.copytree(p, e.ev / "evidencia-del-adaptador" / os.path.basename(p), dirs_exist_ok=True)
            else:
                (e.ev / "evidencia-del-adaptador").mkdir(exist_ok=True)
                shutil.copy2(p, e.ev / "evidencia-del-adaptador")
        e.guardar({"operacion": {k: r.get(k) for k in ("ok", "estado", "rc", "categoria", "determinada", "incierto", "secuencia", "motivo", "trazabilidad", "publicacion")}, "solicitudes": len(llam)})
        e.parar()


def s4():
    e = Esc("S4-retencion-rotate-2", rotate=2)
    e.arrancar()
    sec = {}
    for i in range(1, 6):
        r = cli.solicitar_reset(e.ctl, K, esperar_s=10, id_="rt-%d" % i)
        sec["rt-%d" % i] = r["secuencia"]
        e.logrotate()
    lect = {i: e.lector("d5lector", "d5aud", i)["diagnostico"] for i in sec}
    chk("S4: con rotate 2 los ids más viejos quedan «publicación sin confirmar» (fuera de retención) y los recientes se confirman",
        lect["rt-1"]["publicacion"] == "publicación sin confirmar" and lect["rt-5"]["publicacion"] == "confirmada" and lect["rt-5"]["secuencia_publicada"] == sec["rt-5"],
        {k: v["publicacion"] for k, v in lect.items()})
    e.guardar({"secuencias": sec, "lector": lect})
    e.parar()


def s5():
    e = Esc("S5-estres-logrotate-continuo", rotate=300)
    e.arrancar()
    parar, rcs = threading.Event(), []
    t = threading.Thread(target=lambda: [rcs.append(e.logrotate()) for _ in iter(parar.is_set, True)])
    t.start()
    acuses = {}
    try:
        for i in range(20):
            r = cli.solicitar_reset(e.ctl, K, esperar_s=15, id_="st-%d" % i)
            acuses["st-%d" % i] = r["secuencia"] if r["ok"] else None
    finally:
        parar.set()
        t.join()
    chk("S5: las 20 solicitudes tuvieron acuse y el publicador no se reinició", all(v is not None for v in acuses.values()) and e.vivo(), acuses)
    chk("S5: logrotate real terminó siempre con rc 0 (%d rotaciones)" % len(rcs), set(rcs) == {0}, sorted(set(rcs)))
    bien, partidos, con_gz = 0, 0, 0
    fallos = []
    for i, s in acuses.items():
        d = e.lector("d5lector", "d5aud", i)["diagnostico"]
        if d["categoria"] == "consumida_y_publicada" and d["secuencia_publicada"] == s:
            bien += 1
            partidos += len(d["generaciones_del_id"]) > 1
            con_gz += any(g.endswith(".gz") for g in d["generaciones_del_id"])
        else:
            fallos.append((i, d))
    chk("S5: el lector (solo lectura) reconstruye 20/20 ids con su secuencia", bien == 20, fallos[:3])
    chk("S5: la prueba no es vacía (hubo ids repartidos en ficheros distintos)", partidos >= 1, {"repartidos": partidos, "con_gz": con_gz})
    e.guardar({"solicitudes": 20, "reconstruidas": bien, "ids_repartidos": partidos, "ids_con_generacion_comprimida": con_gz, "rotaciones_logrotate": len(rcs)})
    e.parar()


def main():
    EV.mkdir(exist_ok=True)
    hashes = ps.preparar_codigo()
    chk("versión probada: derivado idéntico al validado", hashes["publicar_feed_v2_d5.py"].startswith("58e2a0b2b0690892"))
    preparar_entorno()
    ent = [sh("logrotate", "--version").stdout.splitlines()[0], sh("dpkg", "-s", "logrotate").stdout.split("Version: ")[1].split("\n")[0], sh("uname", "-sr").stdout.strip(),
           sh("sh", "-c", ". /etc/os-release; echo $PRETTY_NAME").stdout.strip(), "python=" + sys.version.split()[0], "id lector: " + sh("id", "d5lector").stdout.strip(),
           "id publicador: " + sh("id", "nobody").stdout.strip(), "id intruso: " + sh("id", "intruso").stdout.strip(), "red=" + repr(sh("sh", "-c", "ls /sys/class/net").stdout.split())]
    (EV / "entorno.txt").write_text("\n".join(ent) + "\n")
    (EV / "sha256-completos.json").write_text(json.dumps(hashes, indent=1, sort_keys=True))
    for f in (s1, s23, s4, s5):
        try:
            f()
        except Exception as ex:                                     # un caso que revienta no oculta los demás
            chk("%s terminó sin excepción" % f.__name__, False, repr(ex))
    (EV / "comprobaciones.json").write_text(json.dumps(CHECKS, indent=1, ensure_ascii=False))
    mal = [c for c in CHECKS if not c["ok"]]
    print("\n%d comprobaciones, %d fallan" % (len(CHECKS), len(mal)))
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main())
