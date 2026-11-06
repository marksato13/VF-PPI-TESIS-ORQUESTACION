"""Banco aislado de los guiones de traslado del paquete 902991e (revisión r2 frente a la versión anterior).

Sin red y sin laboratorio: ssh y scp son dobles (pruebas/dobles) que simulan bastión, Sensor1 y srv-dmz como
directorios $SIM/<host>. systemctl, sudo, nft, reboot, shutdown, install, chmod, chown, iptables y useradd son dobles
que registran la llamada y fallan: el traslado no debe usarlos.

TRASLADO_VERSION=r2 (por defecto) usa los guiones de esta carpeta; TRASLADO_VERSION=anterior usa los de
evidencia/13-correccion-s14 (DIR_ANTERIOR). PRODUCTO_BUNDLE es un `git bundle` de la rama del producto (contiene 902991e).

Las pruebas `test_regresion_*` son las que la versión anterior no supera porque OCULTA el fallo (rc 0 o éxito falso).
En cada caso de fallo la primera aserción es «sin éxito falso»; las siguientes fijan el código y la evidencia de la r2.
"""
import hashlib
import itertools
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
VERSION = os.environ.get("TRASLADO_VERSION", "r2")
DIR_R2 = Path(os.environ.get("DIR_R2", AQUI.parent))
DIR_ANT = Path(os.environ.get("DIR_ANTERIOR", "/anterior"))
BUNDLE = os.environ.get("PRODUCTO_BUNDLE", "/b/producto.bundle")
C = "902991e"
ESPERADO = "53e9f7bd578123f6499289ebbb92d8d6c71a6e56b7c1c35a59463b98aad5c23f"
ECARGA = "e001352c2e6485d99e71b1e62ff68a4051bebdfc2bbb4fbd927000517d463b80"
HOSTS = {"bastion": "gadmin@10.10.10.30", "sensor1": "m4rk@10.10.60.11", "srvdmz": "adminsrvdmz@10.10.30.10"}
PROHIBIDAS = ["systemctl", "sudo", "nft", "reboot", "shutdown", "install", "chmod", "chown", "iptables", "useradd"]
PATRON_PROHIBIDO = re.compile(r"systemctl|sudo|\bnft\b|generadores\.sh|muestreo_|sensor1_post|evaluar_ecarga\.py\s+\w|"
                              r"evaluar_s14\.py\s|construir_entrada\.py\s|clientes_lab|cyberflow-lab|--aplicar|--enforce")
_n = itertools.count(1)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sh(cmd, **kw):
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, **kw)


# --------------------------------------------------------------------------------------------------- preparación
@pytest.fixture(scope="session")
def base(tmp_path_factory):
    b = tmp_path_factory.mktemp("base")
    dob = b / "dobles"
    dob.mkdir()
    for f in (AQUI / "dobles").iterdir():
        shutil.copy(f, dob / f.name)
    for n in PROHIBIDAS:
        shutil.copy(AQUI / "dobles" / "prohibido", dob / n)
    for f in dob.iterdir():
        os.chmod(f, 0o755)
    home = b / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home))
    for cmd in (["git", "clone", "-q", "--bare", BUNDLE, str(b / "origin.git")],
                ["git", "clone", "-q", str(b / "origin.git"), str(b / "repo")]):
        p = subprocess.run(cmd, env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
    # Paquete de referencia construido con la r2 (--solo-construir): solo construye y verifica, no copia nada.
    sim0 = b / "sim0"
    (sim0 / "log").mkdir(parents=True)
    env = dict(os.environ, HOME=str(home), CF_REPO=str(b / "repo"), SIM=str(sim0), PATH=f"{dob}:{os.environ['PATH']}")
    p = subprocess.run(["bash", str(DIR_R2 / "paquete_902991e.sh"), "--solo-construir", str(b / "construido")],
                       env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert p.returncode == 0, p.stdout + p.stderr
    v = dict(re.findall(r"^(TGZ|SUMAS|FICHEROS)=(\S+)$", p.stdout, re.M))
    return {"dobles": dob, "repo": b / "repo", "home": home, "arbol": b / "construido" / f"paquete-{C}",
            "tgz": b / "construido" / f"paquete-{C}.tgz", "TGZ": v["TGZ"], "SUMAS": v["SUMAS"],
            "ficheros": int(v["FICHEROS"]), "salida": p.stdout}


class Lab:
    def __init__(self, base, sim, tmp):
        self.base, self.sim, self.tmp = base, sim, tmp
        self.env = dict(os.environ, PATH=f"{base['dobles']}:{os.environ['PATH']}", SIM=str(sim),
                        HOME=str(sim / "portatil" / "home"), CF_REPO=str(base["repo"]))
        self.huella = {}

    def cf(self, h):
        return self.sim / h / "home" / "cf-e4"

    def dest(self, h):
        return self.cf(h) / f"paquete-{C}"

    def marca(self, h):
        return self.cf(h) / f"paquete-{C}.VERIFICADO.txt"

    def aviso(self, h):
        return self.cf(h) / "paquete-a12deae.NO-USAR.txt"

    def tmp_de(self, h):
        return Path("/tmp") if h == "bastion" else self.sim / h / "tmp"

    def sellar(self):
        """Huella de todo lo que hay en ~/cf-e4 de los tres hosts: debe seguir igual al terminar (sin sobrescribir)."""
        self.huella = {}
        for h in HOSTS:
            for p in self.cf(h).rglob("*"):
                if p.is_file() and not p.is_symlink():
                    self.huella[str(p)] = sha(p)

    def restos_tmp(self):
        return sorted(str(p) for h in HOSTS for p in self.tmp_de(h).glob("cf-e4-*"))

    def parciales(self, h):
        return sorted(self.cf(h).glob(f".paquete-{C}.parcial.*"))

    def ordenes(self):
        f = self.sim / "log" / "ordenes.log"
        return f.read_text() if f.exists() else ""


@pytest.fixture
def lab(base, tmp_path):
    for p in Path("/tmp").glob("cf-e4-*"):
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    sim = tmp_path / "sim"
    (sim / "log").mkdir(parents=True)
    (sim / "portatil" / "home" / ".ssh").mkdir(parents=True)
    for h in HOSTS:
        (sim / h / "home").mkdir(parents=True)
        if h == "bastion":
            (sim / h / "tmp").symlink_to("/tmp")
        else:
            (sim / h / "tmp").mkdir()
        cf = sim / h / "home" / "cf-e4"                       # paquetes y evidencia ANTERIORES, que no se tocan
        (cf / "paquete-a12deae" / "deploy").mkdir(parents=True)
        (cf / "paquete-a12deae" / "deploy" / "x.py").write_text(f"anterior {h}\n")
        (cf / "paquete-a12deae" / "SHA256SUMS").write_text("anterior\n")
        (cf / "paquete-a12deae.tgz").write_bytes(f"tgz anterior {h}".encode())
        (cf / "paquete-ae2900e").mkdir()
        (cf / "paquete-ae2900e" / "README").write_text("paquete ae2900e\n")
        (cf / "4a").mkdir()
        (cf / "4a" / "evidencia.log").write_text(f"evidencia 4A de {h}\n")
    lb = Lab(base, sim, tmp_path)
    lb.sellar()
    yield lb
    # Comprobaciones comunes a TODAS las pruebas
    prohibido = sim / "log" / "PROHIBIDO.log"
    assert not prohibido.exists(), "ORDEN PROHIBIDA: " + prohibido.read_text()
    malas = [l for l in lb.ordenes().splitlines() if PATRON_PROHIBIDO.search(l)]
    assert not malas, f"órdenes que arrancarían o tocarían algo: {malas}"
    cambiados = [p for p, hs in lb.huella.items() if not Path(p).is_file() or sha(p) != hs]
    assert not cambiados, f"ficheros anteriores modificados o eliminados: {cambiados}"


def principal(lab, version=VERSION, **fallos):
    env = dict(lab.env, **fallos)
    if version == "r2":
        guion = DIR_R2 / "paquete_902991e.sh"
    else:  # la versión anterior tiene la ruta del portátil fija: solo se sustituye esa línea por CF_REPO
        d = lab.tmp / "anterior"
        d.mkdir(exist_ok=True)
        shutil.copy(DIR_ANT / "op_host_902991e.sh", d / "op_host_902991e.sh")
        txt = (DIR_ANT / "paquete_902991e.sh").read_text()
        txt, k = re.subn(r'^R=".*"$', 'R="$CF_REPO"', txt, flags=re.M)
        assert k == 1
        (d / "paquete_902991e.sh").write_text(txt)
        guion = d / "paquete_902991e.sh"
    p = subprocess.run(["bash", str(guion)], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                       cwd=lab.tmp, timeout=600)
    out = p.stdout + p.stderr
    (lab.sim / "log" / f"principal-{next(_n)}.txt").write_text(out)
    return p.returncode, out


def en_host(lab, h, tgz, tgz_sha=None, sumas=None, version=VERSION, run=None, **fallos):
    """Ejecuta op_host en un host simulado a través del doble de ssh, como lo haría el reparto."""
    run = run or f"20261107T{next(_n):06d}Z-1"
    if version == "r2":
        nombre = f"cf-e4-stage-{C}.{run}.tgz"
        cmd = f"N={h} RUN={run} TGZ={tgz_sha or lab.base['TGZ']} SUMAS={sumas or lab.base['SUMAS']} bash -s"
        guion = DIR_R2 / "op_host_902991e.sh"
    else:
        nombre = f"cf-e4-stage-{C}.tgz"
        cmd = f"C={C} ESPERADO={ESPERADO} ECARGA={ECARGA} N={h} bash -s"
        guion = DIR_ANT / "op_host_902991e.sh"
    shutil.copy(tgz, lab.tmp_de(h) / nombre)
    with open(guion, "rb") as f:
        p = subprocess.run([str(lab.base["dobles"] / "ssh"), "-o", "BatchMode=yes", HOSTS[h], cmd], stdin=f,
                           env=dict(lab.env, **fallos), capture_output=True, timeout=300)
    out = p.stdout.decode(errors="replace") + p.stderr.decode(errors="replace")
    return p.returncode, out, run


def variante(lab, cambio, regenerar=False):
    """Copia del paquete de referencia con un cambio; regenerar=True rehace SHA256SUMS (alteración «coherente»)."""
    d = lab.tmp / f"var{next(_n)}"
    shutil.copytree(lab.base["arbol"], d / f"paquete-{C}", symlinks=True)
    cambio(d / f"paquete-{C}")
    if regenerar:
        r = sh(f"cd '{d}/paquete-{C}' && find . -type f ! -path ./SHA256SUMS -print0 | LC_ALL=C sort -z "
               f"| xargs -0 sha256sum > ../S && mv ../S SHA256SUMS")
        assert r.returncode == 0, r.stderr
    r = sh(f"set -o pipefail; tar -C '{d}' -cf - paquete-{C} | gzip -n > '{d}/p.tgz'")
    assert r.returncode == 0, r.stderr
    return d / "p.tgz", sha(d / "p.tgz"), sha(d / f"paquete-{C}" / "SHA256SUMS")


def estado_final(out, h):
    m = re.findall(rf"^{h}: ESTADO_FINAL=(\w+) rc=(\d+)$", out, re.M)
    return (m[-1][0], int(m[-1][1])) if m else (None, None)


def sin_paquete(lab, h):
    assert not lab.dest(h).exists(), f"{h}: quedó paquete-{C} con un paquete inválido"
    assert not lab.marca(h).exists(), f"{h}: quedó la marca VERIFICADO"
    assert not lab.aviso(h).exists(), f"{h}: aviso de sustitución creado sin paquete verificado"


def verificado(lab, h):
    assert lab.dest(h).is_dir() and lab.marca(h).is_file(), f"{h}: falta paquete o marca"
    assert f"SUMAS={lab.base['SUMAS']}" in lab.marca(h).read_text()
    r = sh(f"cd '{lab.dest(h)}' && sha256sum -c --strict --quiet SHA256SUMS")
    assert r.returncode == 0, r.stdout + r.stderr
    assert lab.aviso(h).is_file() and f"paquete-{C}" in lab.aviso(h).read_text()
    assert not lab.parciales(h)


def registro(lab, h):
    logs = sorted(lab.cf(h).glob(f"traslado-{C}.*.{h}.log"))
    assert logs, f"{h}: sin registro del traslado en el host"
    return logs


# ------------------------------------------------------------------------------------------- op_host en un host
ALTERACIONES = [
    # (id, cambio, regenerar SHA256SUMS, rc r2, estado r2)
    ("fichero-alterado-checksum-incorrecto",
     lambda d: (d / "deploy/etapa4/ecarga/generadores.sh").open("ab").write(b"# alterado\n"), False, 6, "INVENTARIO_INVALIDO"),
    ("fichero-esperado-ausente", lambda d: (d / "README.md").unlink(), False, 6, "INVENTARIO_INVALIDO"),
    ("fichero-inesperado", lambda d: (d / "deploy/etapa4/ecarga/extra.sh").write_text("echo intruso\n"), False, 6,
     "INVENTARIO_INVALIDO"),
    ("evaluador-distinto", lambda d: (d / "deploy/etapa4/sensor1/evaluar_ecarga.py").open("a").write("# otro\n"), True, 7,
     "EVALUADOR_DISTINTO"),
    ("version-incorrecta", lambda d: (d / "deploy/etapa4/ecarga/construir_entrada.py").write_text(
        (d / "deploy/etapa4/ecarga/construir_entrada.py").read_text().replace(
            'VERSION = "construir_entrada 2026-11-06.3"', 'VERSION = "construir_entrada 2026-11-06.2"')), True, 9,
     "VERSION_INCORRECTA"),
    ("manifiesto-ecarga-distinto", lambda d: (d / "deploy/etapa4/ecarga/SHA256SUMS").open("a").write("\n"), True, 8,
     "MANIFIESTO_ECARGA_DISTINTO"),
]


@pytest.mark.parametrize("caso,cambio,regenerar,rc_r2,est_r2", ALTERACIONES, ids=[a[0] for a in ALTERACIONES])
def test_regresion_host_paquete_invalido(lab, caso, cambio, regenerar, rc_r2, est_r2):
    tgz, t, s = variante(lab, cambio, regenerar)
    rc, out, run = en_host(lab, "sensor1", tgz, t, s)
    assert rc != 0, f"ÉXITO FALSO: op_host rc=0 con un paquete inválido ({caso})\n{out}"
    assert (rc, estado_final(out, "sensor1")) == (rc_r2, (est_r2, rc_r2)), out
    sin_paquete(lab, "sensor1")
    assert not lab.parciales("sensor1") and not lab.restos_tmp(), (lab.parciales("sensor1"), lab.restos_tmp())
    assert f"ESTADO_FINAL={est_r2} rc={rc_r2}" in registro(lab, "sensor1")[0].read_text()


@pytest.mark.parametrize("h", list(HOSTS))
def test_host_copia_correcta(lab, h):
    rc, out, run = en_host(lab, h, lab.base["tgz"])
    assert (rc, estado_final(out, h)) == (0, ("VERIFICADO", 0)), out
    verificado(lab, h)
    assert f"{lab.base['ficheros']} ficheros" in out and not lab.restos_tmp()
    assert "ESTADO_FINAL=VERIFICADO rc=0" in registro(lab, h)[0].read_text()


def test_host_tgz_truncado(lab):
    tr = lab.tmp / "truncado.tgz"
    datos = lab.base["tgz"].read_bytes()
    tr.write_bytes(datos[: len(datos) // 2])
    rc, out, _ = en_host(lab, "srvdmz", tr)                    # TGZ = el del paquete completo
    assert rc != 0, f"ÉXITO FALSO\n{out}"
    assert (rc, estado_final(out, "srvdmz")) == (4, ("TGZ_DISTINTO", 4)), out
    sin_paquete(lab, "srvdmz")


def test_host_extraccion_fallida(lab):
    malo = lab.tmp / "malo.tgz"
    malo.write_bytes(b"\x1f\x8b\x08\x00" + b"no es un gzip valido" * 50)
    rc, out, _ = en_host(lab, "sensor1", malo, sha(malo))      # el hash coincide: falla la extracción
    assert rc != 0, f"ÉXITO FALSO\n{out}"
    assert (rc, estado_final(out, "sensor1")) == (5, ("EXTRACCION", 5)), out
    sin_paquete(lab, "sensor1")
    assert not lab.parciales("sensor1")


def test_host_destino_ya_existente(lab):
    lab.dest("sensor1").mkdir(parents=True)
    (lab.dest("sensor1") / "centinela").write_text("no tocar\n")
    lab.sellar()
    rc, out, _ = en_host(lab, "sensor1", lab.base["tgz"])
    assert rc != 0, f"ÉXITO FALSO\n{out}"
    assert (rc, estado_final(out, "sensor1")) == (3, ("DESTINO_EXISTE", 3)), out
    assert (lab.dest("sensor1") / "centinela").read_text() == "no tocar\n"
    assert not lab.marca("sensor1").exists() and not lab.aviso("sensor1").exists()


def test_host_marca_de_otro_paquete(lab):
    lab.dest("bastion").mkdir(parents=True)
    lab.marca("bastion").write_text("SUMAS=" + "0" * 64 + "\n")
    lab.sellar()
    rc, out, _ = en_host(lab, "bastion", lab.base["tgz"])
    assert rc != 0, f"ÉXITO FALSO\n{out}"
    assert (rc, estado_final(out, "bastion")) == (3, ("DESTINO_EXISTE", 3)), out


def test_regresion_host_fallo_al_crear_el_aviso(lab):
    lab.aviso("sensor1").mkdir()                               # el aviso no se puede escribir
    rc, out, _ = en_host(lab, "sensor1", lab.base["tgz"])
    assert rc != 0, f"ÉXITO FALSO: el aviso no se creó y op_host terminó con rc 0\n{out}"
    assert (rc, estado_final(out, "sensor1")) == (11, ("AVISO_FALLIDO", 11)), out
    assert lab.dest("sensor1").is_dir() and lab.marca("sensor1").is_file()   # verificado antes del aviso
    assert lab.aviso("sensor1").is_dir() and not any(lab.aviso("sensor1").iterdir())


def test_regresion_host_fallo_de_limpieza_tras_un_error(lab):
    tgz, t, s = variante(lab, ALTERACIONES[0][1])
    rc, out, _ = en_host(lab, "sensor1", tgz, t, s, DOBLE_FALLA_RM=".parcial.")
    assert rc != 0, f"ÉXITO FALSO\n{out}"
    assert (rc, estado_final(out, "sensor1")) == (6, ("INVENTARIO_INVALIDO", 6)), out   # el error ORIGINAL
    assert re.search(r"^sensor1: limpieza-staging rc=1 NO-ELIMINADO", out, re.M), out
    sin_paquete(lab, "sensor1")                                # el resto oculto .parcial no es utilizable
    assert lab.parciales("sensor1")


def test_host_reintento_con_paquete_ya_verificado(lab):
    rc, out, _ = en_host(lab, "srvdmz", lab.base["tgz"])
    assert rc == 0, out
    lab.sellar()                                               # el segundo intento no debe cambiar nada
    rc, out, _ = en_host(lab, "srvdmz", lab.base["tgz"])
    assert (rc, estado_final(out, "srvdmz")) == (0, ("YA_VERIFICADO", 0)), out
    assert len(registro(lab, "srvdmz")) == 2                   # la evidencia de los dos intentos se conserva


def test_host_paquete_existente_alterado_despues(lab):
    rc, out, _ = en_host(lab, "sensor1", lab.base["tgz"])
    assert rc == 0, out
    with open(lab.dest("sensor1") / "README.md", "a") as f:
        f.write("alterado después de verificar\n")
    lab.sellar()
    rc, out, _ = en_host(lab, "sensor1", lab.base["tgz"])
    assert rc != 0, f"ÉXITO FALSO: un paquete alterado tras la marca se da por bueno\n{out}"
    assert (rc, estado_final(out, "sensor1")) == (6, ("INVENTARIO_INVALIDO_EN_PAQUETE_EXISTENTE", 6)), out


# ------------------------------------------------------------------------------------ guion principal (3 hosts)
def test_traslado_correcto_en_los_tres_hosts(lab):
    rc, out = principal(lab)
    assert rc == 0, out
    assert "TRASLADO COMPLETO: bastion, sensor1 y srvdmz verificados (3/3)" in out
    for h in HOSTS:
        verificado(lab, h)
        assert re.search(rf"^RESULTADO {h} rc=0 estado=VERIFICADO$", out, re.M), out
        registro(lab, h)
    assert not lab.restos_tmp(), lab.restos_tmp()


def test_regresion_manifiesto_interno_sin_autorreferencia(lab):
    """El SHA256SUMS interno no puede listarse a sí mismo: si se escribe dentro del árbol mientras `find` lo recorre,
    queda una entrada ./SHA256SUMS con el hash de un fichero a medio escribir y `sha256sum -c` falla siempre."""
    rc, out = principal(lab)
    sumas = lab.dest("sensor1") / "SHA256SUMS"
    listado = sumas.read_text().splitlines() if sumas.is_file() else []
    propio = [l for l in listado if l.endswith("  ./SHA256SUMS")]
    r = sh(f"cd '{lab.dest('sensor1')}' && sha256sum -c --strict --quiet SHA256SUMS")
    assert not (rc == 0 and (propio or r.returncode != 0)), \
        f"ÉXITO FALSO: rc 0 con un manifiesto interno que no verifica ({len(listado)} entradas, propio={propio})\n{out}"
    assert rc == 0 and not propio and r.returncode == 0, out
    assert len(listado) == lab.base["ficheros"] == 480


@pytest.mark.parametrize("h,rc_r2", [("bastion", 4), ("sensor1", 6), ("srvdmz", 6)])
def test_regresion_fallo_de_scp_en_cada_destino(lab, h, rc_r2):
    rc, out = principal(lab, DOBLE_FALLA_SCP=h)
    assert rc != 0 and "TRASLADO COMPLETO" not in out, f"ÉXITO FALSO con scp a {h} fallido\n{out}"
    assert rc == rc_r2, out
    sin_paquete(lab, h)
    if h == "bastion":
        for o in HOSTS:
            sin_paquete(lab, o)
        assert "NINGÚN host preparado" in out
    else:
        assert re.search(rf"^RESULTADO {h} rc=30 estado=SCP_FALLIDO$", out, re.M), out
        assert f"NO preparado en:" in out and h in out.split("NO preparado en:")[-1].splitlines()[0]
        for o in set(HOSTS) - {h}:
            verificado(lab, o)
    assert not lab.restos_tmp(), lab.restos_tmp()


@pytest.mark.parametrize("h,rc_r2", [("bastion", 5), ("sensor1", 6)])
def test_regresion_fallo_de_ssh(lab, h, rc_r2):
    rc, out = principal(lab, DOBLE_FALLA_SSH=h)
    assert rc != 0 and "TRASLADO COMPLETO" not in out, f"ÉXITO FALSO con ssh a {h} fallido\n{out}"
    assert rc == rc_r2, out
    sin_paquete(lab, h)
    if h == "sensor1":
        assert re.search(r"^RESULTADO sensor1 rc=255 estado=SSH_FALLIDO$", out, re.M), out
        verificado(lab, "bastion")
        verificado(lab, "srvdmz")
    else:
        assert "estado de los hosts DESCONOCIDO" in out


def test_regresion_tgz_truncado_en_la_transferencia(lab):
    rc, out = principal(lab, DOBLE_TRUNCA_SCP="sensor1")
    assert rc != 0 and "TRASLADO COMPLETO" not in out, f"ÉXITO FALSO con un tgz truncado\n{out}"
    assert rc == 6 and re.search(r"^RESULTADO sensor1 rc=4 estado=TGZ_DISTINTO$", out, re.M), out
    sin_paquete(lab, "sensor1")
    assert not lab.parciales("sensor1") and not lab.restos_tmp()


def test_regresion_destino_existente_en_un_host(lab):
    lab.dest("srvdmz").mkdir(parents=True)
    (lab.dest("srvdmz") / "centinela").write_text("copia previa\n")
    lab.sellar()
    rc, out = principal(lab)
    assert rc != 0 and "TRASLADO COMPLETO" not in out, f"ÉXITO FALSO con el destino ya existente\n{out}"
    assert rc == 6 and re.search(r"^RESULTADO srvdmz rc=3 estado=DESTINO_EXISTE$", out, re.M), out
    assert not lab.aviso("srvdmz").exists()


def test_regresion_un_host_correcto_y_otro_fallido(lab):
    rc, out = principal(lab, DOBLE_FALLA_SSH="srvdmz")
    assert rc != 0 and "TRASLADO COMPLETO" not in out, f"ÉXITO FALSO con srvdmz sin verificar\n{out}"
    assert rc == 6, out
    assert "TRASLADO INCOMPLETO: 2/3 verificados; NO preparado en: srvdmz" in out
    verificado(lab, "bastion")
    verificado(lab, "sensor1")
    sin_paquete(lab, "srvdmz")
    # la evidencia identifica host, operación, código y estado
    assert re.search(r"portatil host-srvdmz rc=255 SSH_FALLIDO: paquete NO preparado en srvdmz", out), out
    assert re.search(r"portatil host-sensor1 rc=0 VERIFICADO", out), out


def test_regresion_fallo_de_limpieza_en_el_portatil_tras_un_error(lab):
    rc, out = principal(lab, DOBLE_FALLA_SCP="sensor1", DOBLE_FALLA_RM="cf-e4-portatil")
    assert rc != 0 and "TRASLADO COMPLETO" not in out, f"ÉXITO FALSO\n{out}"
    assert rc == 6, out                                      # el error original, no el de limpieza
    assert re.search(r"portatil limpieza-local rc=1 NO-ELIMINADO", out), out
    assert re.search(r"portatil RESULTADO_GLOBAL rc=6 TRASLADO INCOMPLETO", out), out


def test_referencia_git_inaccesible(lab):
    sin = lab.tmp / "repo-sin-origen"
    r = sh(f"git clone -q '{lab.base['repo']}' '{sin}' && git -C '{sin}' remote set-url origin /no/existe",
           env=dict(lab.env, HOME=str(lab.base["home"])))
    assert r.returncode == 0, r.stderr
    rc, out = principal(lab, CF_REPO=str(sin))
    assert rc != 0, f"ÉXITO FALSO sin poder confirmar la referencia\n{out}"
    assert rc == 2 and "git fetch falla" in out, out
    assert "scp " not in lab.ordenes() and "ssh " not in lab.ordenes(), lab.ordenes()


# ------------------------------------------------------------------------------- recuperación de una copia parcial
def test_recuperacion_reintento_tras_copia_parcial(lab):
    rc, out = principal(lab, DOBLE_FALLA_SCP="srvdmz")
    assert rc != 0, f"ÉXITO FALSO en el primer intento\n{out}"
    lab.sellar()            # bastión y Sensor1 ya verificados: el reintento no los puede modificar
    rc, out = principal(lab)
    assert rc == 0 and "TRASLADO COMPLETO" in out, out
    assert re.search(r"^RESULTADO bastion rc=0 estado=YA_VERIFICADO$", out, re.M), out
    assert re.search(r"^RESULTADO sensor1 rc=0 estado=YA_VERIFICADO$", out, re.M), out
    assert re.search(r"^RESULTADO srvdmz rc=0 estado=VERIFICADO$", out, re.M), out
    for h in HOSTS:
        verificado(lab, h)
    assert len(registro(lab, "bastion")) == 2 and len(registro(lab, "srvdmz")) == 1


def test_recuperacion_destino_sin_marca(lab):
    shutil.copytree(lab.base["arbol"], lab.dest("sensor1"))   # p. ej. copia interrumpida tras el renombrado
    lab.sellar()
    rc, out = principal(lab)
    assert rc != 0, f"ÉXITO FALSO: un paquete sin marca se aceptó\n{out}"
    assert rc == 6 and re.search(r"^RESULTADO sensor1 rc=3 estado=DESTINO_EXISTE$", out, re.M), out
    retirado = lab.cf("sensor1") / f"paquete-{C}.RETIRADO-20261107T000000Z"
    lab.dest("sensor1").rename(retirado)                       # procedimiento: apartar sin borrar
    lab.sellar()
    rc, out = principal(lab)
    assert rc == 0 and "TRASLADO COMPLETO" in out, out
    assert re.search(r"^RESULTADO sensor1 rc=0 estado=VERIFICADO$", out, re.M), out
    assert retirado.is_dir()


def test_recuperacion_con_restos_de_un_intento_interrumpido(lab):
    resto = lab.cf("srvdmz") / f".paquete-{C}.parcial.20261107T000000Z-1"
    resto.mkdir(parents=True)
    (resto / "a_medias").write_text("extracción interrumpida\n")
    lab.sellar()
    rc, out = principal(lab)
    assert rc == 0 and "TRASLADO COMPLETO" in out, out
    assert re.search(r"^srvdmz: restos-previos rc=0 1 directorio", out, re.M), out
    assert (resto / "a_medias").is_file()


# ------------------------------------------------------------------------------------------------------- estático
def test_los_guiones_no_contienen_ordenes_prohibidas():
    d = DIR_R2 if VERSION == "r2" else DIR_ANT
    for f in ("paquete_902991e.sh", "op_host_902991e.sh", "reparto_bastion_902991e.sh"):
        p = d / f
        if not p.exists():
            continue
        codigo = "\n".join(l for l in p.read_text().splitlines() if not l.lstrip().startswith("#"))
        assert not re.search(r"\b(systemctl|sudo|nft|reboot|shutdown|chmod|chown|install|iptables)\b", codigo), f
        assert not re.search(r"generadores\.sh|muestreo_|sensor1_post|--aplicar|--enforce", codigo), f
