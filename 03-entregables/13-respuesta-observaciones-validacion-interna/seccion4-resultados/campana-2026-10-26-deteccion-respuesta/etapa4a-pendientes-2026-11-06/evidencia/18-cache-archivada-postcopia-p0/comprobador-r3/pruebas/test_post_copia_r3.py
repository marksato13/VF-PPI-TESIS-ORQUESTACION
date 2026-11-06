"""Banco aislado del comprobador post-copia r3 (copia del banco r2 con los guiones r3 + pruebas de locale) (sin red: ssh es un doble y cada host es un directorio).

El paquete de prueba es el REAL de 902991e: se extrae del bundle del producto con `git archive` y su SHA256SUMS se
escribe como lo hace paquete_902991e.sh r2; la prueba exige que dé SUMAS 8480f0e0… (480 ficheros).
Al terminar cada prueba se exige además:
  - que no cambió ningún byte, modo ni fichero de los hosts simulados (solo lectura);
  - que no se llamó a ninguna orden prohibida en los hosts (rm, mv, cp, chmod, systemctl, sudo, ...).
Variables: DIR_R3 (carpeta del comprobador r3), DIR_R2 (r2, regresiones), I18N (fuentes de locales), DIR_R1 (carpeta de la r1), PRODUCTO_BUNDLE.
"""
import hashlib
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

R3 = Path(os.environ.get("DIR_R3", "/c"))
R2 = Path(os.environ.get("DIR_R2", "/r2"))   # comprobador r2 (anterior; solo regresiones)
R1 = Path(os.environ.get("DIR_R1", "/r1"))
BUNDLE = os.environ.get("PRODUCTO_BUNDLE", "/b/producto.bundle")
CFULL = "902991ec077c9495a99e1075cb26af35ae980507"
SUMAS = "8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c"
HOSTS = ("bastion", "sensor1", "srvdmz")
PROHIBIDAS = ("rm", "mv", "cp", "chmod", "chown", "mkdir", "touch", "ln", "tee", "systemctl", "sudo", "nft",
              "iptables", "reboot", "shutdown", "install", "dd", "truncate")
ES_ROOT = os.geteuid() == 0


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


@pytest.fixture(scope="session")
def base(tmp_path_factory):
    d = tmp_path_factory.mktemp("base")
    git = d / "repo.git"
    assert sh(["git", "clone", "-q", "--bare", BUNDLE, str(git)]).returncode == 0
    pkg = d / "paquete-902991e"
    pkg.mkdir()
    a = subprocess.run(["git", "-C", str(git), "-c", "core.autocrlf=false", "archive", CFULL], capture_output=True)
    assert a.returncode == 0
    assert subprocess.run(["tar", "-x", "-C", str(pkg)], input=a.stdout).returncode == 0
    r = sh(["bash", "-c", "set -o pipefail; cd \"$1\" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > \"$2\"",
            "_", str(pkg), str(d / "sumas")])
    assert r.returncode == 0, r.stderr
    shutil.move(str(d / "sumas"), str(pkg / "SHA256SUMS"))
    assert hashlib.sha256((pkg / "SHA256SUMS").read_bytes()).hexdigest() == SUMAS
    assert len((pkg / "SHA256SUMS").read_text().splitlines()) == 480
    # dobles: ssh en PATH del portátil; órdenes prohibidas solo en los hosts
    dob = d / "dobles"
    dob.mkdir()
    shutil.copy(R3 / "pruebas" / "dobles" / "ssh", dob / "ssh")
    rem = d / "remoto"
    rem.mkdir()
    for p in PROHIBIDAS:
        shutil.copy(R3 / "pruebas" / "dobles" / "prohibido", rem / p)
    for f in list(dob.iterdir()) + list(rem.iterdir()):
        f.chmod(0o755)
    return {"pkg": pkg, "dobles": dob, "remoto": rem}


def instantanea(sim):
    out = {}
    for h in HOSTS:
        raiz = sim / h / "home"
        for p in sorted(raiz.rglob("*")):
            st = p.lstat()
            dato = hashlib.sha256(p.read_bytes()).hexdigest() if stat.S_ISREG(st.st_mode) and os.access(p, os.R_OK) else ""
            out[str(p.relative_to(sim))] = (stat.S_IFMT(st.st_mode), stat.S_IMODE(st.st_mode), st.st_size, dato)
    return out


class Lab:
    def __init__(self, sim, base):
        self.sim, self.base = sim, base
        for h in HOSTS:
            cf = sim / h / "home" / "cf-e4"
            cf.mkdir(parents=True)
            shutil.copytree(base["pkg"], cf / "paquete-902991e", symlinks=True)
            (cf / "paquete-902991e.VERIFICADO.txt").write_text(
                f"paquete-902991e verificado en {h} (2026-11-06T19:50:10Z)\nRUN=20261106T194952Z-10146\nTGZ=bda6\n"
                f"SUMAS={SUMAS}\nevaluar_ecarga=53e9\necarga_SHA256SUMS=e001\n")
            a = cf / "paquete-a12deae" / "deploy" / "etapa4" / "ecarga"
            a.mkdir(parents=True)
            (a / "x.py").write_text("x = 1\n")
            (a / "SHA256SUMS").write_text(hashlib.sha256(b"x = 1\n").hexdigest() + "  x.py\n")
            (cf / "paquete-a12deae.NO-USAR.txt").write_text(
                "paquete-a12deae SUSTITUIDO por ~/cf-e4/paquete-902991e (verificado; RUN=20261106T194952Z-10146; "
                "PROTOCOLO-CARGA-v2 r4).\n")
            (cf / f"traslado-902991e.20261106T194952Z-10146.{h}.log").write_text(f"x {h}: ESTADO_FINAL=VERIFICADO rc=0\n")
        (sim / "portatil").mkdir()

    def cf(self, h):
        return self.sim / h / "home" / "cf-e4"

    def p(self, h):
        return self.cf(h) / "paquete-902991e"

    def correr(self, guion_dir=None, salida=None, entorno=None, guion="comprobar_post_copia_r3.sh"):
        guion_dir = guion_dir or R3
        salida = salida or (self.sim / "salida")
        env = dict(os.environ, SIM=str(self.sim), HOME=str(self.sim / "portatil"),
                   PATH=f"{self.base['dobles']}:{os.environ['PATH']}", DOBLES_REMOTO=str(self.base["remoto"]))
        env.update(entorno or {})
        antes = instantanea(self.sim)
        r = sh(["bash", str(guion_dir / guion), str(salida)], env=env, cwd=str(self.sim / "portatil"))
        assert instantanea(self.sim) == antes, "el comprobador modificó un host"
        r.salida = salida
        return r

    def ordenes(self):
        f = self.sim / "log" / "ordenes.log"
        return f.read_text() if f.exists() else ""


@pytest.fixture
def lab(tmp_path, base):
    lb = Lab(tmp_path / "sim", base)
    yield lb
    prohibido = lb.sim / "log" / "PROHIBIDO.log"
    assert not prohibido.exists(), prohibido.read_text()


def host(r, h):
    s = r.salida
    return {"rc": int((s / f"{h}.rc").read_text()), "out": (s / f"{h}.stdout").read_text(),
            "err": (s / f"{h}.stderr").read_text(),
            "linea": [l for l in (s / "resumen.txt").read_text().splitlines() if l.startswith(f"HOST {h} ")][0]}


def check(r, h, nombre):
    for l in host(r, h)["out"].splitlines():
        if l.startswith(f"CHECK {nombre} "):
            return l.split()[2]
    return None


def global_(r):
    return [l for l in r.stdout.splitlines() if l.startswith("RESULTADO_GLOBAL")][-1]


# ---------------------------------------------------------------- entrada correcta
def test_entrada_correcta_tres_hosts(lab):
    r = lab.correr()
    assert r.returncode == 0, r.stdout + r.stderr
    assert global_(r).startswith("RESULTADO_GLOBAL rc=0 CONFORME 3/3")
    local = hashlib.sha256((R3 / "post_copia_host_r3.sh").read_bytes()).hexdigest()
    for h in HOSTS:
        d = host(r, h)
        assert d["rc"] == 0 and "estado=CONFORME" in d["linea"] and "ok=12/12" in d["linea"]
        assert f"recibido={local}" in d["linea"]
        assert d["out"].splitlines()[-1] == f"RESULTADO {h} rc=0 estado=CONFORME ok=12/12"
        assert "\r" not in d["out"] and "command not found" not in d["err"]


# ---------------------------------------------------------------- CR en la entrada
def _copia_con(tmp_path, transformar):
    d = tmp_path / "variante"
    d.mkdir()
    shutil.copy(R3 / "comprobar_post_copia_r3.sh", d)
    datos = (R3 / "post_copia_host_r3.sh").read_bytes()
    (d / "post_copia_host_r3.sh").write_bytes(transformar(datos))
    return d


@pytest.mark.parametrize("caso,transformar", [
    ("crlf", lambda b: b.replace(b"\n", b"\r\n")),
    ("cr-residual-final", lambda b: b + b"\r"),
    ("cr-residual-interno", lambda b: b.replace(b"terminar\n", b"terminar\r\n", 1)),
])
def test_guion_con_cr_no_se_envia(lab, tmp_path, caso, transformar):
    d = _copia_con(tmp_path, transformar)
    r = lab.correr(guion_dir=d)
    assert r.returncode == 2 and "RESULTADO_GLOBAL rc=2 PRECONDICION" in r.stdout
    assert "CR" in r.stderr
    assert lab.ordenes() == "", "no debe abrirse ninguna conexión"
    assert not r.salida.exists()


def test_transporte_que_anade_cr_se_detecta(lab):
    r = lab.correr(entorno={"DOBLE_CR_FINAL": "sensor1"})
    assert r.returncode == 4
    assert "estado=TRANSPORTE_DISTINTO" in host(r, "sensor1")["linea"]
    for h in ("bastion", "srvdmz"):
        assert "estado=CONFORME" in host(r, h)["linea"]
    assert "sin conformidad en: sensor1" in global_(r)


def test_regresion_r1_con_el_transporte_de_powershell(lab):
    """La r1 recibida con el \\r\\n final que añade PowerShell: error en la línea 19 y rc 127, como en la evidencia."""
    r1 = (R1 / "post_copia_host.sh").read_bytes()
    assert b"\r" not in r1
    env = dict(os.environ, HOME=str(lab.cf("bastion").parent))
    r = subprocess.run(["bash", "-s"], input=r1 + b"\r\n", capture_output=True, env=env, cwd=str(lab.cf("bastion").parent))
    assert b"line 19: $'\\r': command not found" in r.stderr
    assert r.returncode == 127


def test_r3_ignora_basura_tras_el_resultado(lab):
    """La r2 termina con exit explícito: aunque llegara un \\r\\n final, no se ejecuta ni cambia el rc."""
    g = (R3 / "post_copia_host_r3.sh").read_bytes()
    env = dict(os.environ, HOME=str(lab.cf("bastion").parent), N="bastion")
    r = subprocess.run(["bash", "-s"], input=g + b"\r\n", capture_output=True, env=env, cwd=str(lab.cf("bastion").parent))
    assert r.returncode == 0 and b"command not found" not in r.stderr


# ---------------------------------------------------------------- SSH y lectura
def test_fallo_ssh_al_bastion(lab):
    r = lab.correr(entorno={"DOBLE_FALLA_SSH": "bastion"})
    assert r.returncode == 4
    for h in HOSTS:
        d = host(r, h)
        assert d["rc"] == 255 and "estado=SSH_FALLIDO" in d["linea"] and "Connection timed out" in d["err"]


def test_fallo_ssh_a_srvdmz(lab):
    r = lab.correr(entorno={"DOBLE_FALLA_SSH": "srvdmz"})
    assert r.returncode == 4
    assert "estado=SSH_FALLIDO" in host(r, "srvdmz")["linea"]
    assert "estado=CONFORME" in host(r, "bastion")["linea"] and "estado=CONFORME" in host(r, "sensor1")["linea"]


def test_fallo_de_lectura_fichero_convertido_en_directorio(lab):
    f = lab.p("bastion") / "deploy/etapa4/sensor1/evaluar_ecarga.py"
    f.unlink()
    f.mkdir()
    r = lab.correr()
    d = host(r, "bastion")
    assert r.returncode == 4 and d["rc"] == 3 and "estado=ERROR_LECTURA" in d["linea"]
    assert check(r, "bastion", "evaluador") == "ERROR"


@pytest.mark.skipif(ES_ROOT, reason="root lee sin permisos; se cubre con la prueba del directorio")
def test_fallo_de_lectura_sin_permiso(lab):
    f = lab.p("srvdmz") / "SHA256SUMS"
    f.chmod(0)
    try:
        r = lab.correr()
        d = host(r, "srvdmz")
        assert r.returncode == 4 and d["rc"] == 3 and "estado=ERROR_LECTURA" in d["linea"]
        assert check(r, "srvdmz", "sumas-interno") == "ERROR"
        assert check(r, "srvdmz", "hashes") == "ERROR" and check(r, "srvdmz", "inventario") == "ERROR"
    finally:
        f.chmod(0o644)


# ---------------------------------------------------------------- contenido
def test_hash_incorrecto(lab):
    f = lab.p("sensor1") / "deploy/etapa4/ecarga/construir_entrada.py"
    f.write_bytes(f.read_bytes() + b"#\n")
    r = lab.correr()
    d = host(r, "sensor1")
    assert r.returncode == 4 and d["rc"] == 1 and "estado=NO_CONFORME" in d["linea"]
    assert check(r, "sensor1", "hashes") == "FALLO" and check(r, "sensor1", "ecarga-verifica") == "FALLO"


def test_fichero_ausente(lab):
    rel = (lab.p("srvdmz") / "SHA256SUMS").read_text().splitlines()[9].split("  ", 1)[1]
    (lab.p("srvdmz") / rel).unlink()
    r = lab.correr()
    assert r.returncode == 4 and host(r, "srvdmz")["rc"] == 1
    assert check(r, "srvdmz", "inventario") == "FALLO" and check(r, "srvdmz", "hashes") == "FALLO"
    assert rel in host(r, "srvdmz")["out"]


def test_fichero_inesperado(lab):
    (lab.p("bastion") / "deploy" / "intruso.py").write_text("x\n")
    r = lab.correr()
    assert r.returncode == 4 and host(r, "bastion")["rc"] == 1
    assert check(r, "bastion", "hashes") == "OK" and check(r, "bastion", "inventario") == "FALLO"
    assert "intruso.py" in host(r, "bastion")["out"]


def test_marca_ausente(lab):
    (lab.cf("sensor1") / "paquete-902991e.VERIFICADO.txt").unlink()
    r = lab.correr()
    assert r.returncode == 4 and check(r, "sensor1", "marca") == "FALLO"


@pytest.mark.parametrize("contenido", [
    "SUMAS=" + "0" * 64 + "\n",
    f"SUMAS={SUMAS}\nSUMAS={'1' * 64}\n",
    f"SUMAS={SUMAS} \n",
    "sin linea de sumas\n",
])
def test_marca_distinta(lab, contenido):
    (lab.cf("srvdmz") / "paquete-902991e.VERIFICADO.txt").write_text(contenido)
    r = lab.correr()
    assert r.returncode == 4 and check(r, "srvdmz", "marca") == "FALLO"
    assert "estado=CONFORME" in host(r, "bastion")["linea"]


def test_version_incorrecta(lab):
    f = lab.p("bastion") / "deploy/etapa4/ecarga/evaluar_s14.py"
    f.write_text(f.read_text().replace('VERSION = "evaluar_s14 2026-11-06.2"', 'VERSION = "evaluar_s14 2026-11-06.1"'))
    r = lab.correr()
    assert r.returncode == 4 and check(r, "bastion", "version-evaluar_s14") == "FALLO"


def test_aviso_ausente_o_sin_nombrar_el_paquete(lab):
    (lab.cf("bastion") / "paquete-a12deae.NO-USAR.txt").unlink()
    (lab.cf("sensor1") / "paquete-a12deae.NO-USAR.txt").write_text("otro aviso\n")
    r = lab.correr()
    assert check(r, "bastion", "aviso") == "FALLO" and check(r, "sensor1", "aviso") == "FALLO"
    assert r.returncode == 4


def test_resto_parcial(lab):
    (lab.cf("srvdmz") / ".paquete-902991e.parcial.20261106T000000Z-1").mkdir()
    r = lab.correr()
    assert r.returncode == 4 and check(r, "srvdmz", "sin-parciales") == "FALLO"


def test_un_host_correcto_y_otro_fallido(lab):
    (lab.p("sensor1") / "SHA256SUMS").write_text("")
    r = lab.correr()
    assert r.returncode == 4
    assert "estado=CONFORME" in host(r, "bastion")["linea"] and "estado=CONFORME" in host(r, "srvdmz")["linea"]
    assert "estado=NO_CONFORME" in host(r, "sensor1")["linea"] or "estado=ERROR_LECTURA" in host(r, "sensor1")["linea"]
    assert "NO_CONFORME 2/3; sin conformidad en: sensor1" in global_(r)


def test_regresion_r1_oculta_el_fallo(lab):
    """Con la marca distinta y transporte limpio, la r1 termina con rc 0 (su última orden es ls); la r2 con rc 1."""
    (lab.cf("bastion") / "paquete-902991e.VERIFICADO.txt").write_text("SUMAS=" + "0" * 64 + "\n")
    env = dict(os.environ, HOME=str(lab.cf("bastion").parent))
    r1 = subprocess.run(["bash", "-s"], input=(R1 / "post_copia_host.sh").read_bytes(), capture_output=True, env=env,
                        cwd=str(lab.cf("bastion").parent))
    assert b"MARCA-FALLO" in r1.stdout and r1.returncode == 0
    r2 = subprocess.run(["bash", "-s"], input=(R3 / "post_copia_host_r3.sh").read_bytes(), capture_output=True,
                        env=dict(env, N="bastion"), cwd=str(lab.cf("bastion").parent))
    assert r2.returncode == 1 and b"estado=NO_CONFORME" in r2.stdout


# ---------------------------------------------------------------- evidencia
def test_salida_existente_no_se_sobrescribe(lab):
    s = lab.sim / "salida"
    s.mkdir()
    (s / "previo.txt").write_text("evidencia anterior\n")
    r = lab.correr(salida=s)
    assert r.returncode == 2 and lab.ordenes() == ""
    assert (s / "previo.txt").read_text() == "evidencia anterior\n" and sorted(p.name for p in s.iterdir()) == ["previo.txt"]


def test_se_conservan_stdout_stderr_y_rc_por_host(lab):
    r = lab.correr(entorno={"DOBLE_FALLA_SSH": "sensor1"})
    for h in HOSTS:
        for ext in ("stdout", "stderr", "rc"):
            assert (r.salida / f"{h}.{ext}").exists()
    assert (r.salida / "sensor1.rc").read_text().strip() == "255"
    assert "Connection timed out" in (r.salida / "sensor1.stderr").read_text()


def test_guiones_sin_cr_y_sin_ordenes_de_escritura_en_el_host():
    g = (R3 / "post_copia_host_r3.sh").read_text()
    assert "\r" not in g and "\r" not in (R3 / "comprobar_post_copia_r3.sh").read_text()
    codigo = "\n".join(l.split("#")[0] for l in g.splitlines())
    for p in ("rm ", "mv ", "cp ", "chmod", "systemctl", "sudo", "mkdir", "touch", " > \"$", ">> "):
        assert p not in codigo, p


# ================================================================ r3: locales y comm (nuevo en r3)
# Los locales es_PE.UTF-8 y en_US.UTF-8 no vienen en la imagen del banco: se compilan con localedef desde las
# fuentes de glibc montadas en $I18N (sin root: LOCPATH apunta a un directorio temporal). Si no se pueden compilar
# o no cambian la colación, la prueba FALLA (no se salta): una prueba de locale sin locale sería vacía.
import gzip  # noqa: E402

I18N = Path(os.environ.get("I18N", "/i18n"))
PYC = "./deploy/etapa4/sensor1/__pycache__/evaluar_ecarga.cpython-312.pyc"


@pytest.fixture(scope="session")
def locales(tmp_path_factory):
    d = tmp_path_factory.mktemp("locales")
    assert (I18N / "locales" / "es_PE").is_file(), f"faltan las fuentes de locales en {I18N}"
    cm = d / "UTF-8"
    cm.write_bytes(gzip.decompress((I18N / "charmaps" / "UTF-8.gz").read_bytes()))
    loc = d / "loc"
    loc.mkdir()
    env = dict(os.environ, I18NPATH=str(I18N))
    for nombre in ("es_PE", "en_US"):
        r = sh(["localedef", "-i", nombre, "-f", str(cm), str(loc / f"{nombre}.UTF-8")], env=env)
        assert r.returncode in (0, 1), r.stderr        # 1 = avisos de localedef; el locale se crea igual
        assert (loc / f"{nombre}.UTF-8" / "LC_COLLATE").is_file(), r.stderr
    # el locale compilado debe cambiar la colación respecto de C (si no, la prueba sería vacía)
    entrada = "B\na\n_z\n"
    c = sh(["sort"], input=entrada, env=dict(os.environ, LC_ALL="C")).stdout
    for nombre in ("es_PE", "en_US"):
        r = sh(["sort"], input=entrada, env=dict(os.environ, LC_ALL=f"{nombre}.UTF-8", LOCPATH=str(loc)))
        assert r.returncode == 0 and r.stderr == "" and r.stdout != c, (nombre, r.stdout, r.stderr)
    return str(loc)


LIMPIO = {"LC_ALL": "", "LANG": "", "LC_COLLATE": "", "LANGUAGE": ""}
ENTORNOS = {
    "sin-locale": {},
    "LC_ALL=C": {"LC_ALL": "C"},
    "LC_ALL=POSIX": {"LC_ALL": "POSIX"},
    "LC_ALL=C.UTF-8": {"LC_ALL": "C.UTF-8"},
    "LANG=es_PE.UTF-8": {"LANG": "es_PE.UTF-8"},
    "LC_ALL=es_PE.UTF-8": {"LC_ALL": "es_PE.UTF-8"},
    "LC_COLLATE=es_PE+LANG=en_US": {"LC_COLLATE": "es_PE.UTF-8", "LANG": "en_US.UTF-8"},
    "LC_ALL=en_US.UTF-8": {"LC_ALL": "en_US.UTF-8"},
}


def entorno(locales, nombre, **extra):
    e = dict(LIMPIO, LOCPATH=locales)
    e.update(ENTORNOS[nombre])
    e.update(extra)
    return e


def detalle(r, h, nombre):
    for l in host(r, h)["out"].splitlines():
        if l.startswith(f"CHECK {nombre} "):
            return l
    return ""


@pytest.mark.parametrize("loc", list(ENTORNOS))
def test_r3_locale_inventarios_iguales(lab, locales, loc):
    r = lab.correr(entorno=entorno(locales, loc))
    assert r.returncode == 0 and global_(r).startswith("RESULTADO_GLOBAL rc=0 CONFORME 3/3"), r.stdout + r.stderr
    for h in HOSTS:
        assert detalle(r, h, "inventario") == "CHECK inventario OK 480 ficheros, ninguno ausente, ninguno inesperado"
        assert "sorted order" not in host(r, h)["err"] and "locale" not in host(r, h)["err"].lower()


@pytest.mark.parametrize("loc", list(ENTORNOS))
def test_r3_locale_fichero_anadido(lab, locales, loc):
    """El caso real de Sensor1: un .pyc fuera del manifiesto. Se nombra exactamente, con el recuento 1."""
    f = lab.p("sensor1") / PYC
    f.parent.mkdir()
    f.write_bytes(b"\x00pyc")
    r = lab.correr(entorno=entorno(locales, loc))
    d = host(r, "sensor1")
    assert r.returncode == 4 and d["rc"] == 1 and "estado=NO_CONFORME" in d["linea"]
    assert check(r, "sensor1", "hashes") == "OK"
    assert detalle(r, "sensor1", "inventario") == (
        f"CHECK inventario FALLO manifiesto 480, presentes 481 (se exigen 480); ausentes (0): ninguno; inesperados (1): {PYC} ")
    assert "sorted order" not in d["err"]
    for h in ("bastion", "srvdmz"):
        assert "estado=CONFORME" in host(r, h)["linea"]


@pytest.mark.parametrize("loc", list(ENTORNOS))
def test_r3_locale_fichero_ausente(lab, locales, loc):
    rel = (lab.p("srvdmz") / "SHA256SUMS").read_text().splitlines()[9].split("  ", 1)[1]
    (lab.p("srvdmz") / rel).unlink()
    r = lab.correr(entorno=entorno(locales, loc))
    assert r.returncode == 4 and host(r, "srvdmz")["rc"] == 1
    assert check(r, "srvdmz", "hashes") == "FALLO"
    assert detalle(r, "srvdmz", "inventario") == (
        f"CHECK inventario FALLO manifiesto 480, presentes 479 (se exigen 480); ausentes (1): {rel} ; inesperados (0): ninguno")
    assert "sorted order" not in host(r, "srvdmz")["err"]


@pytest.mark.parametrize("loc", list(ENTORNOS))
def test_r3_locale_error_de_lectura(lab, locales, loc):
    f = lab.p("bastion") / "deploy/etapa4/sensor1/evaluar_ecarga.py"
    f.unlink()
    f.mkdir()
    r = lab.correr(entorno=entorno(locales, loc))
    d = host(r, "bastion")
    assert r.returncode == 4 and d["rc"] == 3 and "estado=ERROR_LECTURA" in d["linea"]
    assert check(r, "bastion", "evaluador") == "ERROR"
    assert "CONFORME 3/3" not in global_(r)


def test_regresion_r2_con_es_pe_reproduce_el_aviso_de_sensor1(lab, locales):
    """La r2 (conservada) con LC_ALL=es_PE.UTF-8 y el .pyc: comm avisa «not in sorted order» (como en Sensor1).
    Su veredicto sigue siendo FALLO (no un OK falso). La r3, en el mismo estado, nombra exactamente el .pyc sin aviso."""
    f = lab.p("sensor1") / PYC
    f.parent.mkdir()
    f.write_bytes(b"\x00pyc")
    e = entorno(locales, "LC_ALL=es_PE.UTF-8")
    r2 = lab.correr(guion_dir=R2, guion="comprobar_post_copia_r2.sh", salida=lab.sim / "salida-r2", entorno=e)
    assert "not in sorted order" in host(r2, "sensor1")["err"]
    assert host(r2, "sensor1")["rc"] == 1 and check(r2, "sensor1", "inventario") == "FALLO" and r2.returncode == 4
    r3 = lab.correr(salida=lab.sim / "salida-r3", entorno=e)
    assert "sorted order" not in host(r3, "sensor1")["err"]
    assert f"inesperados (1): {PYC} " in detalle(r3, "sensor1", "inventario")


def _remoto_con(tmp_path, base, **dobles):
    d = tmp_path / "remoto-extra"
    shutil.copytree(base["remoto"], d)
    for n, txt in dobles.items():
        (d / n).write_text(txt)
        (d / n).chmod(0o755)
    return str(d)


COMM_FALLA = "#!/usr/bin/env bash\necho 'comm: fallo simulado (doble del banco)' >&2\nexit 1\n"


def test_comm_que_falla_r3_da_error_y_r2_daba_conformidad_falsa(lab, tmp_path, base):
    """Regresión: la r2 ignora el rc de comm; con comm fallando, listas vacías y 480/480 -> CONFORME falso.
    La r3 comprueba el rc: inventario ERROR, host ERROR_LECTURA (rc 3) y global rc 4."""
    rem = _remoto_con(tmp_path, base, comm=COMM_FALLA)
    r2 = lab.correr(guion_dir=R2, guion="comprobar_post_copia_r2.sh", salida=lab.sim / "salida-r2",
                    entorno={"DOBLES_REMOTO": rem})
    assert r2.returncode == 0 and "CONFORME 3/3" in global_(r2)      # defecto de la r2, demostrado
    assert check(r2, "sensor1", "inventario") == "OK"
    r3 = lab.correr(salida=lab.sim / "salida-r3", entorno={"DOBLES_REMOTO": rem})
    assert r3.returncode == 4 and global_(r3).startswith("RESULTADO_GLOBAL rc=4 NO_CONFORME 0/3")
    for h in HOSTS:
        d = host(r3, h)
        assert d["rc"] == 3 and "estado=ERROR_LECTURA" in d["linea"]
        assert detalle(r3, h, "inventario").startswith("CHECK inventario ERROR comm rc 1/1")


def test_entrada_desordenada_r3_da_error(lab, tmp_path, base):
    """Si sort entregara una lista desordenada, comm --check-order lo detecta: ERROR, nunca OK."""
    rem = _remoto_con(tmp_path, base, sort="#!/usr/bin/env bash\ncommand -p sort \"$@\" | command -p tac\n")
    r = lab.correr(entorno={"DOBLES_REMOTO": rem})
    assert r.returncode == 4
    for h in HOSTS:
        d = host(r, h)
        assert d["rc"] == 3 and detalle(r, h, "inventario").startswith("CHECK inventario ERROR comm rc ")
        assert "order" in detalle(r, h, "inventario")


def test_r3_fija_lc_all_c_y_check_order():
    g = (R3 / "post_copia_host_r3.sh").read_text()
    codigo = [l.split("#")[0] for l in g.splitlines()]
    assert "export LC_ALL=C" in codigo
    comms = [l for l in codigo if "comm -" in l]           # invocaciones de comm (no los mensajes «comm rc»)
    assert len(comms) == 2 and all("LC_ALL=C comm --check-order" in l for l in comms)
    sorts = [l for l in codigo if "sort" in l]
    assert len(sorts) == 2 and all("LC_ALL=C sort" in l for l in sorts)
    assert (R2 / "post_copia_host_r2.sh").is_file(), "la r2 debe conservarse"
