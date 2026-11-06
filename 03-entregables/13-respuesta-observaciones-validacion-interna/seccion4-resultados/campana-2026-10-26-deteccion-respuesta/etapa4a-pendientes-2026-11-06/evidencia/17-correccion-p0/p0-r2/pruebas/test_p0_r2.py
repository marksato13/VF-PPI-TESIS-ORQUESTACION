"""Banco AISLADO de P0 r2 (sin red: contenedor --network none; ssh es un doble). Nada de lo que corre aquí toca un host.

Rutas (variables de entorno, montadas en solo lectura por correr_banco.ps1):
  DIR_P16   ../16-postcopia-p0          manejador ANTIGUO (p0/p0_anticipado.sh) y la salida real de precheck del 06-nov
  PRODUCTO  árbol del producto en la rama con sensor1_muestreadores.sh 2026-11-06.3 (ficheros del paquete del banco)
Las pruebas «regresion» muestran el defecto con el manejador antiguo y su corrección con la r2.
"""
import base64
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
R2 = AQUI.parent
DRIVER = R2 / "p0_r2.sh"
BL = R2 / "bloques"
DOBLES = AQUI / "dobles"
P16 = Path(os.environ.get("DIR_P16", "/p16"))
PRODUCTO = Path(os.environ.get("PRODUCTO", "/r"))
V2_FIX = AQUI / "fixtures" / "sensor1_muestreadores-902991e.sh"
V2 = "25fb732ddc15bc83f1f1a79e6e9ccb7ca0cd867a2dfd48270a26dd9ba03c915b"
V3 = "4ed4385674e9f731c7d50f12b132d86a0a3625355df24ebaf4fa9fa0c8342b6e"
CLAVES = {"00-estado-bastion": "estado_r2:bastion", "00-estado-sensor1": "estado_r2:sensor1",
          "00-estado-srvdmz": "estado_r2:srvdmz", "01-verificar-bastion": "verificador_r2:bastion",
          "02-verificar-sensor1": "verificador_r2:sensor1", "03-verificar-srvdmz": "verificador_r2:srvdmz",
          "04-precheck-s11": "precheck_r2", "05-clientes": "clientes_r2", "06-sensor1": "sensor1_r2"}
SIN_CACHE_ENV = ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX")


def esperados():
    txt = DRIVER.read_text()
    e = {CLAVES[m.group(1)]: m.group(2).split() for m in re.finditer(r'^ESPERADOS\[(.+?)\]="(.*)"$', txt, re.M)}
    assert set(e) == set(CLAVES.values())
    return e


def bin_dobles(tmp, *nombres):
    b = tmp / "bin"
    b.mkdir(exist_ok=True)
    for n in nombres:
        shutil.copy(DOBLES / n, b / ("ssh" if n.startswith("ssh") else n))
        (b / ("ssh" if n.startswith("ssh") else n)).chmod(0o755)
    return b


# =============================================================================================== manejador
def correr(tmp, modo="anticipado", conf=None, driver=None, extra=(), todos_255=False):
    c = {"esperados": esperados()}
    c.update(conf or {})
    if todos_255:
        c["todos_ssh_255"] = True
    (tmp / "conf.json").write_text(json.dumps(c))
    b = bin_dobles(tmp, "ssh")
    (tmp / "home").mkdir(exist_ok=True)
    env = dict(os.environ, PATH=f"{b}:/usr/local/bin:/usr/bin:/bin", DOBLE_CONF=str(tmp / "conf.json"),
               DOBLE_LOG=str(tmp / "llamadas.log"), HOME=str(tmp / "home"), LANG="C.UTF-8")
    salida = tmp / "salida"
    if driver is None:
        a = ["bash", str(DRIVER), modo, str(salida), *extra]
    else:
        a = ["bash", str(driver), str(salida)]
    r = subprocess.run(a, env=env, capture_output=True, text=True, timeout=180)
    return r, salida


def resumen(s):
    return (s / "resumen.txt").read_text()


def llamadas(tmp):
    p = tmp / "llamadas.log"
    return p.read_text().splitlines() if p.exists() else []


def test_todos_correctos_anticipado(tmp_path):
    r, s = correr(tmp_path)
    t = resumen(s)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "BLOQUES 9/9 ejecutados sin errores" in t
    n = sum(len(v) for v in esperados().values()) - 1 + 1        # P5b es de momento; P5c lo añade el manejador
    assert f"PRECONDICIONES anticipables: {n}/{n} CUMPLE" in t
    assert "REQ momento NO_EVALUABLE P5b" in t and "REQ documental NO_EVALUABLE P8" in t and "REQ ejecucion NO_EVALUABLE P12" in t
    assert "RESULTADO_GLOBAL rc=0 modo=anticipado PRECONDICIONES ANTICIPABLES CONFORMES. NO sustituye al P0 inmediato" in t
    assert len(llamadas(tmp_path)) == 9
    for n in CLAVES:
        for ext in ("stdout", "stderr", "rc", "motivo"):
            assert (s / f"{n}.{ext}").exists(), f"{n}.{ext}"
        assert (s / f"{n}.rc").read_text().strip() == "0"


def test_inmediato_fuera_de_franja_no_es_conforme(tmp_path):
    r, s = correr(tmp_path, modo="inmediato")
    assert r.returncode == 5
    assert "P0 INMEDIATO NO CONFORME: P5b=NO_EVALUABLE" in resumen(s)


def test_inmediato_conforme(tmp_path):
    r, s = correr(tmp_path, modo="inmediato", conf={"sensor1_r2": {"reqs": {"P5b": "CUMPLE"}}})
    assert r.returncode == 0
    assert "RESULTADO_GLOBAL rc=0 modo=inmediato P0 INMEDIATO CONFORME" in resumen(s)


def test_regresion_nueve_ssh_fallidos(tmp_path):
    """Defecto A: con ssh rc 255 en los 9 bloques, el manejador antiguo termina con rc 0; la r2, con rc 4."""
    viejo = P16 / "p0" / "p0_anticipado.sh"
    assert viejo.is_file(), viejo
    (tmp_path / "v").mkdir()
    rv, sv = correr(tmp_path / "v", driver=viejo, todos_255=True)
    rcs = [(sv / f"{n}.rc").read_text().strip() for n in
           ("00-estado-bastion", "00-estado-sensor1", "00-estado-srvdmz", "01-verificar-bastion", "02-verificar-sensor1",
            "03-verificar-srvdmz", "04-precheck-s11", "05-clientes", "06-sensor1-comprobar")]
    assert rcs == ["255"] * 9
    assert rv.returncode == 0                       # <- el defecto
    (tmp_path / "n").mkdir()
    rn, sn = correr(tmp_path / "n", todos_255=True)
    t = resumen(sn)
    assert rn.returncode == 4
    assert "BLOQUES 0/9 ejecutados sin errores" in t
    assert t.count("motivo=SSH_FALLIDO rc 255") == 9
    assert "RESULTADO_GLOBAL rc=4 modo=anticipado NO VERIFICADO: 9 bloque(s) con error" in t
    assert "PRECONDICIONES anticipables: 1/" in t     # solo P5c, que no depende de ningún host
    assert len(llamadas(tmp_path / "n")) == 9          # no se detiene en el primer fallo


def test_regresion_un_ssh_fallido_el_antiguo_lo_oculta(tmp_path):
    (tmp_path / "v").mkdir()
    rv, sv = correr(tmp_path / "v", driver=P16 / "p0" / "p0_anticipado.sh", conf={"falla_llamada": 5})
    assert (sv / "02-verificar-sensor1.rc").read_text().strip() == "255"
    assert rv.returncode == 0                       # <- el defecto: un bloque sin ejecutar y rc 0
    (tmp_path / "n").mkdir()
    rn, sn = correr(tmp_path / "n", conf={"verificador_r2:sensor1": {"ssh_rc": 255}})
    assert rn.returncode == 4
    assert "BLOQUES 8/9" in resumen(sn)


def test_un_bloque_falla_y_el_resto_bien(tmp_path):
    r, s = correr(tmp_path, conf={"verificador_r2:sensor1": {"ssh_rc": 255}})
    t = resumen(s)
    assert r.returncode == 4
    assert "BLOQUES 8/9 ejecutados sin errores" in t
    assert "bloque con error: 02-verificar-sensor1 -> SSH_FALLIDO rc 255" in t
    assert "REQ anticipable SIN_VERIFICAR P1.sensor1" in t
    assert "Connection timed out" in (s / "02-verificar-sensor1.stderr").read_text()
    assert (s / "02-verificar-sensor1.rc").read_text().strip() == "255"


def test_error_seguido_de_operaciones_correctas(tmp_path):
    r, s = correr(tmp_path, conf={"estado_r2:bastion": {"ssh_rc": 255}})
    assert r.returncode == 4
    assert len(llamadas(tmp_path)) == 9
    t = resumen(s)
    assert "BLOQUES 8/9" in t and "estado=OK" in t and t.rstrip().splitlines()[-1].startswith("RESULTADO_GLOBAL rc=4")


def test_transporte_distinto(tmp_path):
    r, s = correr(tmp_path, conf={"precheck_r2": {"sha": "distinto"}})
    t = resumen(s)
    assert r.returncode == 4
    assert "04-precheck-s11 -> TRANSPORTE_DISTINTO" in t
    assert "REQ anticipable SIN_VERIFICAR P2.modelo" in t        # el bloque decía CUMPLE, pero no se le cree


@pytest.mark.parametrize("conf, motivo", [
    ({"modo": "vacio"}, "SIN_SALIDA"),
    ({"modo": "truncado"}, "INCOMPLETO sin FIN_BLOQUE"),
    ({"omitir": ["P11"]}, "FALTAN_REQ P11"),
    ({"lineas": ["REQ P9 CUMPLE otra vez"]}, "REQ_DUPLICADO P9"),
    ({"omitir": ["P7"], "lineas": ["REQ P7 BIEN mal formada"]}, "FALTAN_REQ P7"),
    ({"rc": 3, "fin_rc": 0}, "INCOHERENTE FIN_BLOQUE rc=0 y ssh rc=3"),
    ({"rc": 1, "fin_rc": 1}, "RC_NO_CERO rc 1"),
])
def test_resultado_ausente_incompleto_o_incoherente(tmp_path, conf, motivo):
    r, s = correr(tmp_path, conf={"sensor1_r2": conf})
    t = resumen(s)
    assert r.returncode == 4, t
    assert f"06-sensor1 -> {motivo}" in t, t


def test_error_de_lectura_en_el_host(tmp_path):
    r, s = correr(tmp_path, conf={"sensor1_r2": {"reqs": {"P13.inventario": "ERROR"}}})
    t = resumen(s)
    assert r.returncode == 4
    assert "06-sensor1 -> ERROR_EN_BLOQUE rc 3: P13.inventario" in t
    assert "REQ anticipable ERROR P13.inventario" in t


def test_bloque_con_cr_no_se_envia(tmp_path):
    copia = tmp_path / "copia"
    shutil.copytree(R2, copia, ignore=shutil.ignore_patterns("pruebas", "banco"))
    f = copia / "bloques" / "clientes_r2.sh"
    f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n", 1))
    c = {"esperados": esperados()}
    (tmp_path / "conf.json").write_text(json.dumps(c))
    b = bin_dobles(tmp_path, "ssh")
    env = dict(os.environ, PATH=f"{b}:/usr/local/bin:/usr/bin:/bin", DOBLE_CONF=str(tmp_path / "conf.json"),
               DOBLE_LOG=str(tmp_path / "llamadas.log"), HOME=str(tmp_path))
    r = subprocess.run(["bash", str(copia / "p0_r2.sh"), "anticipado", str(tmp_path / "s")], env=env, capture_output=True, text=True)
    assert r.returncode == 4
    assert "05-clientes -> CR_EN_BLOQUE" in (tmp_path / "s" / "resumen.txt").read_text()
    assert len(llamadas(tmp_path)) == 8


def test_precondicion_incumplida(tmp_path):
    r, s = correr(tmp_path, conf={"verificador_r2:bastion": {"reqs": {"P1.bastion": "NO_CUMPLE"}}})
    t = resumen(s)
    assert r.returncode == 5
    assert "BLOQUES 9/9 ejecutados sin errores" in t                # ejecutar sin errores ...
    assert "RESULTADO_GLOBAL rc=5 modo=anticipado PRECONDICIONES NO CONFORMES: P1.bastion=NO_CUMPLE" in t   # ... != conforme


def test_anticipable_no_evaluable_no_es_conforme(tmp_path):
    r, s = correr(tmp_path, conf={"sensor1_r2": {"reqs": {"P11": "NO_EVALUABLE"}}})
    assert r.returncode == 5
    assert "P11=NO_EVALUABLE" in resumen(s)


def test_error_manda_sobre_no_cumple(tmp_path):
    r, s = correr(tmp_path, conf={"verificador_r2:bastion": {"reqs": {"P1.bastion": "NO_CUMPLE"}},
                                  "clientes_r2": {"ssh_rc": 255}})
    t = resumen(s)
    assert r.returncode == 4
    assert "P1.bastion=NO_CUMPLE" in t and "05-clientes -> SSH_FALLIDO" in t


def test_salida_existente_y_uso(tmp_path):
    (tmp_path / "salida").mkdir()
    r, _ = correr(tmp_path)
    assert r.returncode == 2 and "ya existe" in r.stdout and llamadas(tmp_path) == []
    r2 = subprocess.run(["bash", str(DRIVER), "otro", str(tmp_path / "x")], capture_output=True, text=True)
    assert r2.returncode == 2 and not (tmp_path / "x").exists()
    r3 = subprocess.run(["bash", str(DRIVER), "anticipado", str(tmp_path / "y"), "--sumas", "abc"], capture_output=True, text=True)
    assert r3.returncode == 2 and not (tmp_path / "y").exists()


def test_paquete_corregido_por_argumento(tmp_path):
    r, s = correr(tmp_path, extra=("--paquete", "a1b2c3d", "--sumas", "0" * 64))
    assert r.returncode == 0
    assert "paquete=a1b2c3d sumas=" + "0" * 64 in resumen(s)


def test_guiones_sin_cr_y_con_bloque_declarado():
    for f in [DRIVER, *BL.glob("*.sh"), *DOBLES.iterdir()]:
        assert b"\r" not in f.read_bytes(), f
    for f in BL.glob("*_r2.sh"):
        t = f.read_text()
        assert re.search(r"^# BLOQUE=" + f.stem + r"\b", t, re.M) and t.rstrip().endswith("fin"), f
    assert hashlib.sha256((BL / "precheck.sh").read_bytes()).hexdigest() == \
        "b3127eddb28978c38295a425f8e672d7476d9ab4e5a779c656e19e3d65f980b8"


# =============================================================================================== bloques por dentro
def doble(b, nombre, cuerpo):
    p = b / nombre
    p.write_text("#!/usr/bin/env bash\n" + cuerpo + "\n")
    p.chmod(0o755)


def host(tmp, **kw):
    """Dobles mínimos de órdenes de host (lectura). timedatectl/ps configurables por kw."""
    b = bin_dobles(tmp, "ssh_bloques")
    tdc = kw.get("timedatectl", 'case "$*" in *--value*) echo Etc/UTC;; *timesync-status*) echo "Server: doble";;'
                                ' *) printf "Timezone=Etc/UTC\\nNTP=yes\\nNTPSynchronized=yes\\n";; esac')
    doble(b, "timedatectl", tdc)
    doble(b, "ps", kw.get("ps", 'echo "  PID ARGS"; echo "    1 /sbin/init"'))
    doble(b, "systemctl", kw.get("systemctl", r'''case "$1 $2" in
  "is-enabled ppi-relay-eventos") echo enabled;; "is-enabled ppi-relay-feed.timer") echo disabled;;
  "is-active ppi-relay-eventos") echo active;; is-active*) echo inactive; exit 3;;
  show*) case "$*" in *MainPID*ppi-relay-eventos) echo 1;; *NRestarts*ppi-relay-eventos) echo 0;; *) echo;; esac;;
  *) echo inactive;; esac'''))
    doble(b, "curl", "echo -n 401")
    doble(b, "sha256sum", 'case " $* " in *" /opt/"*|*" /etc/systemd/"*) for f in "$@"; do echo "0000000000000000000000000000000000000000000000000000000000000000  $f"; done;; '
                          '*) exec /usr/bin/sha256sum "$@";; esac')
    (tmp / "home").mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in SIN_CACHE_ENV}
    env.update(PATH=f"{b}:/usr/local/bin:/usr/bin:/bin", HOME=str(tmp / "home"), LANG="C.UTF-8",
               DOBLE_LOG=str(tmp / "ssh.log"))
    env.update(kw.get("env", {}))
    return env


def bloque(nombre, env, *args):
    """Ejecuta el bloque como en el host: bytes por stdin a «bash -s -- ARGS»."""
    r = subprocess.run(["bash", "-s", "--", *args], input=(BL / nombre).read_bytes(), env=env, capture_output=True,
                       timeout=180, cwd=env["HOME"])
    out = r.stdout.decode()
    reqs = dict(re.findall(r"^REQ (\S+) (\S+)", out, re.M))
    fin = re.findall(r"^FIN_BLOQUE (\S+) rc=(\d+)$", out, re.M)
    assert fin and out.rstrip().splitlines()[-1].startswith("FIN_BLOQUE"), out
    assert int(fin[-1][1]) == r.returncode, out
    return r.returncode, reqs, out


FICHEROS_PAQUETE = ["deploy/etapa4/sensor1/evaluar_ecarga.py", "deploy/etapa4/sensor1/obs_pcap.py",
                    "deploy/etapa4/sensor1/clasificar_periodo.py", "deploy/etapa4/sensor1/comparar_suricata.py",
                    "deploy/etapa4/sensor1/verificar_sensor1.sh", "deploy/etapa4/cierre/muestreo_fino.py",
                    "scripts/etapa4/salud_captura.py", "deploy/etapa4/ecarga/muestreo_s14.py",
                    "deploy/etapa4/ecarga/evaluar_s14.py"]


def paquete(tmp, guion=V2_FIX, nombre="banco", extra=None):
    """Paquete ESCRIBIBLE del banco en HOME/cf-e4/paquete-NOMBRE (ficheros del producto + el guion indicado)."""
    pkg = tmp / "home" / "cf-e4" / f"paquete-{nombre}"
    for rel in FICHEROS_PAQUETE:
        (pkg / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PRODUCTO / rel, pkg / rel)
    shutil.copy(guion, pkg / "deploy/etapa4/ecarga/sensor1_muestreadores.sh")
    rels = sorted(FICHEROS_PAQUETE + ["deploy/etapa4/ecarga/sensor1_muestreadores.sh"])
    (pkg / "SHA256SUMS").write_text("".join(f"{hashlib.sha256((pkg / r).read_bytes()).hexdigest()}  ./{r}\n" for r in rels))
    if extra:
        (pkg / extra).parent.mkdir(parents=True, exist_ok=True)
        (pkg / extra).write_bytes(b"\xcb\x0d\x0d\x0a" + b"\0" * 12)
    herr = tmp / "home" / "cyberflow-e4" / "herramientas-20261106"
    herr.mkdir(parents=True, exist_ok=True)
    shutil.copy(PRODUCTO / "scripts/etapa4/salud_captura.py", herr / "salud_captura.py")
    (herr / "SHA256SUMS").write_text(f"{hashlib.sha256((herr / 'salud_captura.py').read_bytes()).hexdigest()}  salud_captura.py\n")
    assert os.access(pkg / "deploy/etapa4/sensor1", os.W_OK)
    return pkg, hashlib.sha256((pkg / "SHA256SUMS").read_bytes()).hexdigest()


def inventario(raiz):
    inv = {}
    for d, ds, fs in os.walk(raiz):
        for n in ds + fs:
            p = Path(d) / n
            st = p.lstat()
            inv[str(p.relative_to(raiz))] = (stat.S_IFMT(st.st_mode), st.st_mode & 0o7777, st.st_size, st.st_mtime_ns,
                                             hashlib.sha256(p.read_bytes()).hexdigest() if stat.S_ISREG(st.st_mode) else None)
    return inv


def test_versiones_de_referencia():
    assert hashlib.sha256(V2_FIX.read_bytes()).hexdigest() == V2
    assert hashlib.sha256((PRODUCTO / "deploy/etapa4/ecarga/sensor1_muestreadores.sh").read_bytes()).hexdigest() == V3


def test_control_la_2_ejecutada_tal_cual_escribe_cache(tmp_path):
    """Control del banco: el paquete es escribible y la .2 de 902991e, ejecutada directamente, deja __pycache__."""
    pkg, _ = paquete(tmp_path)
    env = host(tmp_path)
    antes = inventario(pkg)
    subprocess.run(["bash", str(pkg / "deploy/etapa4/ecarga/sensor1_muestreadores.sh"), "comprobar",
                    str(tmp_path / "home/cf-e4/x"), "1794197760", "2026-11-09T04:16:00Z"], env=env, capture_output=True, timeout=120)
    nuevos = sorted(set(inventario(pkg)) - set(antes))
    assert any(n.endswith(".pyc") for n in nuevos), nuevos


@pytest.mark.parametrize("guion, modo", [(V2_FIX, "derivada"), (None, "publicado")])
def test_sensor1_mecanismo_sin_escritura(tmp_path, guion, modo):
    """La r2 ejecuta SIEMPRE los bytes de la .3 (publicados o derivados en memoria) y el paquete no cambia: 3 pasadas."""
    pkg, sumas = paquete(tmp_path, guion or PRODUCTO / "deploy/etapa4/ecarga/sensor1_muestreadores.sh")
    env = host(tmp_path)
    antes = inventario(pkg)
    for i in range(3):
        rc, reqs, out = bloque("sensor1_r2.sh", env, f"p0-banco-{i}", "banco", sumas, "0", "9999999999")
        assert reqs["X.mecanismo_sin_escritura"] == "CUMPLE", out
        assert (modo == "derivada") == ("derivada en memoria" in out)
        assert reqs["X.paquete_sin_cambios"] == "CUMPLE", out
        assert reqs["P13.sumas"] == reqs["P13.hashes"] == reqs["P13.inventario"] == "CUMPLE", out
        assert reqs["P5b"] == "CUMPLE" and reqs["P5a.sensor1"] == "CUMPLE"
        assert "| OK    evaluar_ecarga VERSION 2026-11-06.4" in out               # la consulta de versión se conserva
        assert reqs["P11"] == "NO_CUMPLE" and rc in (0, 3), out                    # el banco no tiene anillo ni journal
        assert inventario(pkg) == antes, f"pasada {i}"
        assert not (tmp_path / "home/cf-e4" / f"p0-banco-{i}").exists()


def test_sensor1_guion_desconocido_no_se_ejecuta(tmp_path):
    g = tmp_path / "otro.sh"
    g.write_bytes(V2_FIX.read_bytes().replace(b"RETENCION_MIN=900", b"RETENCION_MIN=901"))
    pkg, sumas = paquete(tmp_path, g)
    rc, reqs, out = bloque("sensor1_r2.sh", host(tmp_path), "p0-x", "banco", sumas, "0", "9999999999")
    assert rc == 3 and reqs["X.mecanismo_sin_escritura"] == "ERROR" and reqs["P11"] == "ERROR"
    assert "| OK    paquete" not in out and not (pkg / "deploy/etapa4/sensor1/__pycache__").exists()


def test_sensor1_pyc_anadido_es_no_cumple_no_error(tmp_path):
    """Lo que hay hoy en Sensor1: un .pyc fuera del manifiesto -> P13.inventario NO_CUMPLE (lo nombra); no es ERROR."""
    rel = "deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc"
    pkg, sumas = paquete(tmp_path, extra=rel)
    rc, reqs, out = bloque("sensor1_r2.sh", host(tmp_path), "p0-x", "banco", sumas, "0", "9999999999")
    assert reqs["P13.inventario"] == "NO_CUMPLE" and rel in out
    assert reqs["P13.hashes"] == "CUMPLE" and reqs["X.paquete_sin_cambios"] == "CUMPLE"
    assert (pkg / rel).read_bytes()[:4] == b"\xcb\x0d\x0d\x0a"                      # no se toca


@pytest.mark.parametrize("fi, ff, esperado", [("9999999990", "9999999999", "NO_EVALUABLE"), ("0", "1", "NO_CUMPLE"),
                                              ("0", "9999999999", "CUMPLE")])
def test_sensor1_franja(tmp_path, fi, ff, esperado):
    pkg, sumas = paquete(tmp_path)
    rc, reqs, out = bloque("sensor1_r2.sh", host(tmp_path), "p0-x", "banco", sumas, fi, ff)
    assert reqs["P5b"] == esperado


def test_sensor1_sin_paquete_todo_error(tmp_path):
    rc, reqs, out = bloque("sensor1_r2.sh", host(tmp_path), "p0-x", "banco", "0" * 64, "0", "1")
    assert rc == 3 and reqs["P13.sumas"] == "ERROR" and reqs["P11"] == "ERROR" and reqs["X.paquete_sin_cambios"] == "ERROR"


def test_estado_lecturas_y_fallos(tmp_path):
    rc, reqs, _ = bloque("estado_r2.sh", host(tmp_path), "sensor1")
    assert rc == 0 and reqs == {"X.sincronizado.sensor1": "CUMPLE", "P3.procesos.sensor1": "CUMPLE"}
    rc, reqs, _ = bloque("estado_r2.sh", host(tmp_path, timedatectl="exit 1"), "sensor1")
    assert rc == 3 and reqs["X.sincronizado.sensor1"] == "ERROR"
    rc, reqs, _ = bloque("estado_r2.sh", host(tmp_path, ps="exit 1"), "bastion")
    assert rc == 3 and reqs["P3.procesos.bastion"] == "ERROR"
    rc, reqs, out = bloque("estado_r2.sh", host(tmp_path, ps='echo "  PID ARGS"; echo "  77 python3 agente.py --aplicar"'), "srvdmz")
    assert rc == 0 and reqs["P3.procesos.srvdmz"] == "NO_CUMPLE" and "--aplicar" in out


def generadores(tmp):
    g = tmp / "home/cf-e4/paquete-902991e/deploy/etapa4/ecarga/generadores.sh"
    g.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(PRODUCTO / "deploy/etapa4/ecarga/generadores.sh", g)


def test_clientes_correcto_y_fallos(tmp_path):
    generadores(tmp_path)
    rc, reqs, _ = bloque("clientes_r2.sh", host(tmp_path))
    assert rc == 0 and set(reqs.values()) == {"CUMPLE"} and len(reqs) == 8
    rc, reqs, _ = bloque("clientes_r2.sh", host(tmp_path, env={"CLI_FALLA": "1"}))
    assert rc == 3 and reqs["P10"] == reqs["P4.parado"] == reqs["P4.generador"] == "ERROR"
    rc, reqs, _ = bloque("clientes_r2.sh", host(tmp_path, env={"CLI_RC": json.dumps({"configuracion": 4, "comprobar-parado": 5})}))
    assert rc == 3 and reqs["P10"] == "NO_CUMPLE" and reqs["P4.parado"] == "ERROR"
    rc, reqs, _ = bloque("clientes_r2.sh", host(tmp_path, env={"CLI_GEN": "f" * 64, "CLI_TZ": "America/Lima"}))
    assert rc == 0 and reqs["P4.generador"] == "NO_CUMPLE" and reqs["P5a.clientes"] == "NO_CUMPLE"
    rc, reqs, _ = bloque("clientes_r2.sh", host(tmp_path, env={"CLI_LECTURAS_RC": "3"}))
    assert rc == 3 and reqs["P4.generador"] == "ERROR"


def test_clientes_sin_generadores_sh(tmp_path):
    rc, reqs, _ = bloque("clientes_r2.sh", host(tmp_path))
    assert rc == 3 and reqs["X.generadores_sh"] == "ERROR" and reqs["P10"] == "ERROR"


def secciones(tmp):
    t = (P16 / "p0-anticipado-20261106T210504Z" / "04-precheck-s11.stdout").read_text().splitlines()
    i, j = t.index("## SENSOR1"), t.index("## BASTION")
    k = t.index("## SRV-DMZ")
    (tmp / "s1.txt").write_text("\n".join(t[i + 1:j]) + "\n")
    (tmp / "sd.txt").write_text("\n".join(t[k + 1:]) + "\n")
    return {"PRE_SENSOR1": str(tmp / "s1.txt"), "PRE_SRVDMZ": str(tmp / "sd.txt")}


def b64_precheck(texto=None):
    return base64.b64encode(texto if texto is not None else (BL / "precheck.sh").read_bytes()).decode()


def test_precheck_salida_real_del_06nov_cumple(tmp_path):
    rc, reqs, out = bloque("precheck_r2.sh", host(tmp_path, env=secciones(tmp_path)), b64_precheck(), "banco")
    assert rc == 0, out
    assert set(reqs) == set(esperados()["precheck_r2"]) and set(reqs.values()) == {"CUMPLE"}, reqs


def test_precheck_alterado_no_se_ejecuta(tmp_path):
    rc, reqs, out = bloque("precheck_r2.sh", host(tmp_path, env=secciones(tmp_path)),
                           b64_precheck((BL / "precheck.sh").read_bytes() + b"# otro\n"), "banco")
    assert rc == 3 and reqs == {"X.precheck_identico": "ERROR"}
    assert not (tmp_path / "ssh.log").exists()


def test_precheck_fallo_ssh_srvdmz(tmp_path):
    env = host(tmp_path, env={**secciones(tmp_path), "PRE_FALLA": "srvdmz"})
    rc, reqs, out = bloque("precheck_r2.sh", env, b64_precheck(), "banco")
    assert rc == 3 and reqs["P3.ruleset.srvdmz"] == reqs["P3.tablas.srvdmz"] == reqs["X.agente_v2"] == "ERROR"
    assert reqs["X.precheck_stderr"] == "ERROR" and reqs["P2.modelo"] == "CUMPLE"


def test_regresion_precheck_sudo_fallido_no_pasa_por_ruleset_vacio(tmp_path):
    """precheck.sh por sí solo daría tablas [] y el sha de la cadena vacía si sudo -n falla; la r2 lo marca ERROR."""
    env = host(tmp_path, env={**secciones(tmp_path), "PRE_SUDO": "1"})
    rc, reqs, out = bloque("precheck_r2.sh", env, b64_precheck(), "banco")
    assert rc == 3 and reqs["X.precheck_stderr"] == "ERROR" and "sudo: a password is required" in out


def test_precheck_hash_distinto_es_no_cumple(tmp_path):
    env = host(tmp_path, env={**secciones(tmp_path), "PRE_SURICATA": "1" * 64})
    rc, reqs, out = bloque("precheck_r2.sh", env, b64_precheck(), "banco")
    assert rc == 0 and reqs["P2.suricata"] == "NO_CUMPLE"


def verificadores(tmp, rc):
    base = tmp / "home/cf-e4/paquete-902991e/deploy/etapa4"
    for h, f in (("bastion", "verificar_bastion.sh"), ("sensor1", "verificar_sensor1.sh")):
        (base / h).mkdir(parents=True, exist_ok=True)
        (base / h / f).write_text(f"echo verificador doble; exit {rc}\n")


@pytest.mark.parametrize("rc, esperado, rc_bloque", [(0, "CUMPLE", 0), (1, "NO_CUMPLE", 0), (2, "ERROR", 3), (255, "ERROR", 3)])
def test_verificador(tmp_path, rc, esperado, rc_bloque):
    verificadores(tmp_path, rc)
    r, reqs, _ = bloque("verificador_r2.sh", host(tmp_path), "bastion")
    assert r == rc_bloque and reqs == {"P1.bastion": esperado}


def test_verificador_ausente_y_respaldo_ausente(tmp_path):
    r, reqs, _ = bloque("verificador_r2.sh", host(tmp_path), "sensor1")
    assert r == 3 and reqs == {"P1.sensor1": "ERROR"}
    r, reqs, _ = bloque("verificador_r2.sh", host(tmp_path), "srvdmz")
    assert r == 3 and reqs == {"P1.srvdmz": "ERROR"}
