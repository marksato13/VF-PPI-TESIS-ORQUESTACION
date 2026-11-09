"""Ajustes de la 4C (2026-11-09): g01 v2 (el vigía lee tcpdump con la forma que permite el sudoers) y s40 v3 (las dos extracciones de tcpdump).
El sudoers de m4rk en el Sensor1 solo permite `sudo -n journalctl --no-pager *`; los stubs lo reproducen. g01 se prueba con el vigia_4c.py REAL del
paquete del Sensor1 (VIGIA_DIR = copia de ~/cf-e4/paquete/scripts/etapa4; se omite si no está). Necesita bash/Linux."""
from __future__ import annotations

import difflib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
CAMP = AQUI.parents[1] if (AQUI.parents[1] / "etapa4-preparacion-2026-11-02").exists() else Path(os.environ.get("CAMPANA", AQUI.parents[1]))
G01_V1 = CAMP / "etapa4-preparacion-2026-11-02/guiones/g01_lanzar_bateria_e4.sh"
S40_V2 = CAMP / "etapa4-4b-enmienda-p1-2026-11-08/guiones/s40_cierre_e4.sh"
G01_V2 = AQUI.parent / "guiones/g01_lanzar_bateria_e4.sh"
S40_V3 = AQUI.parent / "guiones/s40_cierre_e4.sh"
VIGIA_DIR = Path(os.environ.get("VIGIA_DIR", "/vigia"))
pytestmark = pytest.mark.skipif(shutil.which("bash") is None or sys.platform == "win32", reason="requiere bash/Linux")
sys.path.insert(0, str(CAMP / "etapa4-4b-enmienda-p1-2026-11-08/tests"))
from test_s40_copias import lab  # noqa: E402,F401  (HOME falso de s40)


# --------------------------------------------------------------------------------------------- stubs con el sudoers REAL de m4rk
SUDO = """#!/bin/sh
shift
# sudoers de m4rk: NOPASSWD: /usr/bin/journalctl --no-pager *   (con --no-pager PRIMERO); cualquier otra forma de journalctl pide contraseña
case "$1" in
  journalctl) if [ "$2" != "--no-pager" ]; then echo "sudo: a password is required" >&2; exit 1; fi ;;
esac
VIA_SUDO=1 exec "$@"
"""
JOURNALCTL = """#!/usr/bin/env python3
import os, sys, time
a = sys.argv[1:]
u = a[a.index("-u") + 1] if "-u" in a else ""
if u not in ("ppi-motor-capture", "ppi-via-rapida@ens37"):
    print("2026-11-09T00:00:00 linea de journal"); sys.exit(0)
f = os.environ.get("JFALLA", "")
if f == "rc" or (f == "sin_sudo" and not os.environ.get("VIA_SUDO")): sys.exit(1)
if f == "vacio": sys.exit(0)
import datetime as dt
t_ini = float(os.environ["JT_INI"]); ahora = time.time()
pid = {"ppi-motor-capture": 1355, "ppi-via-rapida@ens37": 1389}[u]
ident = "tcpdump" if u == "ppi-motor-capture" else "bash"
desde, hasta = t_ini - 120, ahora
if f == "inicio_tarde" and u == "ppi-via-rapida@ens37": desde = t_ini + 900
if f == "fin_temprano" and u == "ppi-motor-capture": hasta = ahora - 900
if f == "pid_cruzado" and u == "ppi-via-rapida@ens37": pid = 1355          # lecturas del PID del anillo, pero con el formato de la vía: el log NO es idéntico al del anillo
n, t = 0, desde
while t <= hasta:
    n += 1
    iso = dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(timespec="microseconds")
    if f == "sin_lecturas":
        print(f"{iso} cyberflow-sensor systemd[1]: {u} algo sin lecturas")
    elif f == "truncadas" and n % 50 == 0:
        print(f"{iso} cyberflow-sensor {ident}[{pid}]: tcpdump: 100 packets captured")
    else:
        print(f"{iso} cyberflow-sensor {ident}[{pid}]: tcpdump: 100 packets captured, 100 packets received by filter, 0 packets dropped by kernel")
    t += 30
"""
SYSTEMCTL = """#!/bin/sh
case "$*" in *ControlGroup*) for a in "$@"; do u="$a"; done; echo "/system.slice/$u.service";; *--value*) echo 1;; *is-active*) echo active;; *) echo "Id=x";; esac
"""


@pytest.fixture
def lab4c(lab, tmp_path):
    """El HOME falso de s40 con el escenario real: archivo abierto hace 4 h, cgroups por unidad y el sudoers de m4rk."""
    import json
    t_ini = time.time() - 4 * 3600
    (lab.b / "eve/inicio.json").write_text(json.dumps({"t": t_ini, "inode": 1, "size": 0}))
    cg = tmp_path / "cgroup"
    for u, pids in (("ppi-motor-capture", [1355]), ("ppi-via-rapida@ens37", [1387, 1389, 1390])):
        d = cg / "system.slice" / f"{u}.service"; d.mkdir(parents=True)
        (d / "cgroup.procs").write_text("\n".join(map(str, pids)) + "\n")
    stub = Path(lab.env["PATH"].split(":")[0])
    for n, c in (("sudo", SUDO), ("journalctl", JOURNALCTL), ("systemctl", SYSTEMCTL)):
        (stub / n).write_text(c); (stub / n).chmod(0o755)
    lab.env.update(JT_INI=str(t_ini), CF_CGROUP_ROOT=str(cg))
    return lab


def correr(lab, guion, **env):
    e = dict(lab.env); e.update({k: str(v) for k, v in env.items()})
    return subprocess.run(["bash", str(guion), "4b"], env=e, capture_output=True, text=True, timeout=180)


def sin_marca(lab):
    return not (lab.c / "COPIAS-COMPLETAS.ok").exists() and not (lab.c / "SHA256SUMS").exists()


# --------------------------------------------------------------------------------------------- s40
def test_s40_v2_con_el_sudoers_real_reproduce_el_fallo_de_la_4b(lab4c):
    lab = lab4c
    r = correr(lab, S40_V2)
    assert r.returncode == 1 and "COPIAS INCOMPLETAS (2 fallos" in r.stdout, r.stdout
    assert (lab.b / "salud/tcpdump-anillo.log").stat().st_size == 0 and (lab.b / "salud/tcpdump-via.log").stat().st_size == 0


def test_s40_v3_extrae_ambos_logs_cubre_la_ventana_y_declara_completas(lab4c):
    lab = lab4c
    r = correr(lab, S40_V3)
    assert r.returncode == 0 and "## COPIAS COMPLETAS" in r.stdout, r.stdout + r.stderr
    a, v = (lab.b / "salud/tcpdump-anillo.log").read_text(), (lab.b / "salud/tcpdump-via.log").read_text()
    assert "tcpdump[1355]" in a and "bash[1389]" in v and a != v
    assert '"pids": [1355]' in r.stdout and '"pids": [1389]' in r.stdout and '"hueco_max_s": 30' in r.stdout, r.stdout
    assert (lab.c / "COPIAS-COMPLETAS.ok").exists() and (lab.c / "SHA256SUMS").stat().st_size > 0 and not (lab.c / "COPIAS-INCOMPLETAS.txt").exists()


def test_s40_v3_si_el_journal_sin_sudo_falla_usa_sudo_con_la_forma_permitida(lab4c):
    r = correr(lab4c, S40_V3, JFALLA="sin_sudo")
    assert r.returncode == 0 and "## COPIAS COMPLETAS" in r.stdout, r.stdout


@pytest.mark.parametrize("falla,motivo", [
    ("rc", "journalctl rc≠0 en ambas formas"), ("vacio", "extracción vacía"), ("sin_lecturas", "log sin lecturas SIGUSR1"),
    ("truncadas", "lecturas truncadas"), ("pid_cruzado", "la vía trae lecturas de otro proceso (el anillo)"),
    ("inicio_tarde", "la vía no cubre el inicio"), ("fin_temprano", "el anillo no cubre el final")])
def test_s40_v3_extraccion_fallida_vacia_incompleta_o_que_no_cubre_impide_la_marca(lab4c, falla, motivo):
    lab = lab4c
    r = correr(lab, S40_V3, JFALLA=falla)
    assert r.returncode == 1 and "COPIAS INCOMPLETAS" in r.stdout, (motivo, r.stdout)
    assert sin_marca(lab) and (lab.c / "COPIAS-INCOMPLETAS.txt").stat().st_size > 0
    if falla in ("pid_cruzado", "inicio_tarde", "fin_temprano", "truncadas", "sin_lecturas"):
        assert "MOTIVO:" in r.stdout or "FALLO" in r.stdout


def test_s40_v3_solo_cambia_las_extracciones_de_tcpdump():
    a, b = S40_V2.read_text(encoding="utf-8").splitlines(), S40_V3.read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    quitadas = [l for l in cambios if l.startswith("-")]
    # lo quitado: la cabecera de versión y las dos extracciones; nada más
    assert all(("s40 v2" in l) or ("tcpdump-anillo.log" in l) or ("tcpdump-via.log" in l) for l in quitadas), quitadas
    assert "sudo -n journalctl -u ppi-motor-capture" not in S40_V3.read_text(encoding="utf-8")
    cuerpo = S40_V3.read_text(encoding="utf-8")
    assert all(x in cuerpo for x in ("jtcp()", "pids_de()", "DESDE_REQ", "HASTA_REQ", "COPIAS-COMPLETAS.ok"))


# --------------------------------------------------------------------------------------------- g01
def _orden_sensor(guion: Path) -> str:
    m = re.search(r'^OS="(.*)"$', guion.read_text(encoding="utf-8"), re.M)
    assert m, "no se encontró la orden del sensor (OS=) en g01"
    return m.group(1)


def test_g01_solo_cambia_la_orden_del_sensor_la_comprobacion_del_generador_y_los_comentarios():
    a, b = G01_V1.read_text(encoding="utf-8").splitlines(), G01_V2.read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    de_codigo = [l for l in cambios if not l[1:].lstrip().startswith("#")]
    assert len(de_codigo) == 4, de_codigo
    quitadas, anadidas = [l[1:] for l in de_codigo if l[0] == "-"], [l[1:] for l in de_codigo if l[0] == "+"]
    os_q, os_a = [l for l in quitadas if l.startswith("OS=")], [l for l in anadidas if l.startswith("OS=")]
    assert len(os_q) == 1 and len(os_a) == 1 and "--journalctl 'sudo -n journalctl --no-pager'" in os_a[0] and "--journalctl" not in os_q[0]
    pg_q, pg_a = [l for l in quitadas if "pgrep" in l], [l for l in anadidas if "pgrep" in l]
    assert len(pg_q) == 1 and "pgrep -fc 'generar_campana.py --config'" in pg_q[0], pg_q
    assert len(pg_a) == 1 and "pgrep -fc '[g]enerar_campana.py --config'" in pg_a[0], pg_a


def _patron_pgrep(guion: Path) -> str:
    codigo = "\n".join(l for l in guion.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#"))
    m = re.search(r"pgrep -fc '([^']+)'", codigo)
    assert m, "no se encontró la comprobación del generador en g01"
    return m.group(1)


def _cuenta_en_bash_c(patron: str, con_generador: bool) -> int:
    """Lo que hace g01 en la Kali: `pgrep -fc PATRÓN` dentro de un `bash -c` (ssh ejecuta así el texto remoto), con o sin un generador real."""
    decoy = None
    if con_generador:
        decoy = subprocess.Popen(["bash", "-c", "exec -a 'python3 -u /x/generar_campana.py --config /x/escenarios-4c.json' sleep 30"])
        time.sleep(0.4)
    try:
        r = subprocess.run(["bash", "-c", f"echo $(pgrep -fc '{patron}')"], capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip() or "-1")
    finally:
        if decoy: decoy.kill()


def test_g01_v1_y_v2_se_cuentan_a_si_mismos_y_v3_no():
    if shutil.which("pgrep") is None:
        pytest.skip("falta pgrep")
    assert _cuenta_en_bash_c(_patron_pgrep(G01_V1), False) >= 1, "la comprobación original se autocoincide (el defecto del 9-nov)"
    assert _cuenta_en_bash_c(_patron_pgrep(G01_V2), False) == 0, "la corregida no se autocuenta"


def test_g01_corregido_sigue_detectando_un_generador_real():
    if shutil.which("pgrep") is None:
        pytest.skip("falta pgrep")
    assert _cuenta_en_bash_c(_patron_pgrep(G01_V2), True) >= 1


@pytest.fixture
def entorno_vigia(tmp_path):
    if not (VIGIA_DIR / "vigia_4c.py").exists():
        pytest.skip(f"falta VIGIA_DIR ({VIGIA_DIR})")
    stub = tmp_path / "stub"; stub.mkdir()
    (stub / "sudo").write_text(SUDO); (stub / "journalctl").write_text(JOURNALCTL)
    (stub / "systemctl").write_text('#!/bin/sh\ncase "$*" in *--value*) echo 1;; *is-active*) echo active;; *) echo "Id=x";; esac\n')
    for f in stub.iterdir():
        f.chmod(0o755)
    (tmp_path / "arch").mkdir(); (tmp_path / "salud").mkdir(); (tmp_path / "salud/muestras.jsonl").write_text("{}\n")
    (stub / "systemctl").write_text(SYSTEMCTL); (stub / "systemctl").chmod(0o755)
    env = dict(os.environ, PATH=f"{stub}:{os.environ['PATH']}", HOME=str(tmp_path), JT_INI=str(time.time() - 3600))
    return tmp_path, env


def _tcpdump_del_vigia(tmp, env, orden):
    orden = orden.replace("~/cf-e4/paquete/scripts/etapa4/vigia_4c.py", str(VIGIA_DIR / "vigia_4c.py")).replace("~/cf-e4/4c/archivo-pcap", str(tmp / "arch")) \
                 .replace("~/cf-e4/4c/salud/muestras.jsonl", str(tmp / "salud/muestras.jsonl"))
    # el vigía lanza esta orden por ssh: el shell remoto la interpreta; aquí lo hace bash -c
    r = subprocess.run(["bash", "-c", orden], env=env, capture_output=True, text=True, timeout=60)
    import json
    return json.loads(r.stdout)["tcpdump"]


def test_vigia_con_g01_v1_no_lee_tcpdump_y_con_g01_v2_si(entorno_vigia):
    tmp, env = entorno_vigia
    v1 = _tcpdump_del_vigia(tmp, env, _orden_sensor(G01_V1))
    assert v1["ok"] is False and "password is required" in v1["motivo"], v1
    v2 = _tcpdump_del_vigia(tmp, env, _orden_sensor(G01_V2))
    assert v2["ok"] is True and v2["lecturas"] and all(x["pid"] == 1355 and x["descartados_kernel"] == 0 for x in v2["lecturas"]), v2
