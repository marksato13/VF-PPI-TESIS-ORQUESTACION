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
SUDO = '''#!/bin/sh
shift
# sudoers de m4rk: NOPASSWD: /usr/bin/journalctl --no-pager *   (con --no-pager PRIMERO); cualquier otra forma de journalctl pide contraseña
case "$1" in
  journalctl) if [ "$2" != "--no-pager" ]; then echo "sudo: a password is required" >&2; exit 1; fi ;;
esac
[ -n "${SUDO_FALLA:-}" ] && { echo "sudo: a password is required" >&2; exit 1; }
exec "$@"
'''
JOURNALCTL = '''#!/bin/sh
u=""; prev=""
for a in "$@"; do [ "$prev" = "-u" ] && u="$a"; prev="$a"; done
case "$u" in
  ppi-motor-capture|ppi-via-rapida@ens37)
    [ -n "${JMODE_FALLA:-}" ] && exit 1
    [ -n "${JMODE_VACIO:-}" ] && exit 0
    [ -n "${JMODE_SINLECT:-}" ] && { echo "2026-11-09T01:00:00.000000+00:00 cyberflow-sensor systemd[1]: algo sin lecturas"; exit 0; }
    [ -n "${JNOSUDO_FALLA:-}" ] && [ "$(id -u)" = "$JUID" ] && [ -z "$VIA_SUDO" ] && exit 1
    ident=tcpdump; [ "$u" = "ppi-via-rapida@ens37" ] && ident=bash
    t=1794158040; while [ $t -le 1794194490 ]; do
      printf '%s cyberflow-sensor %s[1355]: tcpdump: 100 packets captured, 100 packets received by filter, 0 packets dropped by kernel\\n' "$(date -u -d @$t +%Y-%m-%dT%H:%M:%S.000000+00:00)" "$ident"
      t=$((t+3600)); done;;
  *) echo "2026-11-09T00:00:00 linea de journal";;
esac
'''


def instalar(lab, **env):
    stub = Path(lab.env["PATH"].split(":")[0])
    (stub / "sudo").write_text(SUDO); (stub / "journalctl").write_text(JOURNALCTL)
    for f in (stub / "sudo", stub / "journalctl"):
        f.chmod(0o755)
    lab.env.update({k: str(v) for k, v in env.items()})


def correr(lab, guion):
    return subprocess.run(["bash", str(guion), "4b"], env=lab.env, capture_output=True, text=True, timeout=120)


def reiniciar(lab):
    """s40 se vuelve a ejecutar sobre la misma carpeta: limpia lo que dejó la ejecución anterior."""
    for n in ("COPIAS-COMPLETAS.ok", "COPIAS-INCOMPLETAS.txt", "SHA256SUMS", "FUENTES-al-copiar.tsv"):
        (lab.c / n).unlink(missing_ok=True)


# --------------------------------------------------------------------------------------------- s40
def test_s40_v2_con_el_sudoers_real_reproduce_el_fallo_de_la_4b(lab):
    instalar(lab)
    r = correr(lab, S40_V2)
    assert r.returncode == 1 and "COPIAS INCOMPLETAS (2 fallos" in r.stdout, r.stdout
    assert (lab.b / "salud/tcpdump-anillo.log").stat().st_size == 0 and (lab.b / "salud/tcpdump-via.log").stat().st_size == 0


def test_s40_v3_extrae_ambos_logs_y_declara_completas(lab):
    instalar(lab)
    r = correr(lab, S40_V3)
    assert r.returncode == 0 and "## COPIAS COMPLETAS" in r.stdout, r.stdout + r.stderr
    for n, ident in (("tcpdump-anillo.log", "tcpdump["), ("tcpdump-via.log", "bash[")):
        t = (lab.b / "salud" / n).read_text()
        assert "packets captured" in t and ident in t
    assert (lab.c / "COPIAS-COMPLETAS.ok").exists() and (lab.c / "SHA256SUMS").stat().st_size > 0 and not (lab.c / "COPIAS-INCOMPLETAS.txt").exists()
    assert "lecturas SIGUSR1: anillo 10 / vía 10" in r.stdout or "lecturas SIGUSR1: anillo" in r.stdout


def test_s40_v3_si_el_journal_sin_sudo_falla_usa_sudo_con_la_forma_permitida(lab):
    """Primera orden (sin sudo) falla; la de respaldo `sudo -n journalctl --no-pager …` sí está permitida."""
    stub = Path(lab.env["PATH"].split(":")[0])
    instalar(lab)
    (stub / "journalctl").write_text(JOURNALCTL.replace('[ -n "${JNOSUDO_FALLA:-}" ] && [ "$(id -u)" = "$JUID" ] && [ -z "$VIA_SUDO" ] && exit 1',
                                                        '[ -z "${VIA_SUDO:-}" ] && exit 1'))
    (stub / "sudo").write_text(SUDO.replace('exec "$@"', 'VIA_SUDO=1 exec "$@"'))
    for f in (stub / "sudo", stub / "journalctl"):
        f.chmod(0o755)
    r = correr(lab, S40_V3)
    assert r.returncode == 0 and "## COPIAS COMPLETAS" in r.stdout, r.stdout


@pytest.mark.parametrize("modo,motivo", [("JMODE_FALLA", "journalctl rc≠0 en ambas formas"), ("JMODE_VACIO", "extracción vacía"), ("JMODE_SINLECT", "log sin lecturas SIGUSR1")])
def test_s40_v3_extraccion_fallida_vacia_o_sin_lecturas_impide_la_marca(lab, modo, motivo):
    instalar(lab, **{modo: "1"})
    r = correr(lab, S40_V3)
    assert r.returncode == 1 and "COPIAS INCOMPLETAS" in r.stdout, (motivo, r.stdout)
    assert not (lab.c / "COPIAS-COMPLETAS.ok").exists() and not (lab.c / "SHA256SUMS").exists()
    assert (lab.c / "COPIAS-INCOMPLETAS.txt").stat().st_size > 0


def test_s40_v3_solo_cambia_las_extracciones_de_tcpdump():
    a, b = S40_V2.read_text(encoding="utf-8").splitlines(), S40_V3.read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    quitadas = [l for l in cambios if l.startswith("-")]
    anadidas = [l for l in cambios if l.startswith("+")]
    # lo quitado: la cabecera de versión y las dos extracciones; nada más
    assert all(("s40 v2" in l) or ("tcpdump-anillo.log" in l) or ("tcpdump-via.log" in l) for l in quitadas), quitadas
    assert any("jtcp" in l for l in anadidas) and sum("journalctl" in l for l in anadidas) >= 2
    assert "sudo -n journalctl -u ppi-motor-capture" not in S40_V3.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------------- g01
def _orden_sensor(guion: Path) -> str:
    m = re.search(r'^OS="(.*)"$', guion.read_text(encoding="utf-8"), re.M)
    assert m, "no se encontró la orden del sensor (OS=) en g01"
    return m.group(1)


def test_g01_v2_solo_cambia_la_orden_del_sensor_y_los_comentarios():
    a, b = G01_V1.read_text(encoding="utf-8").splitlines(), G01_V2.read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    de_codigo = [l for l in cambios if not l[1:].lstrip().startswith("#")]
    assert len(de_codigo) == 2 and de_codigo[0].startswith("-OS=") and de_codigo[1].startswith("+OS="), de_codigo
    assert "--journalctl 'sudo -n journalctl --no-pager'" in de_codigo[1] and "--journalctl" not in de_codigo[0]


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
    env = dict(os.environ, PATH=f"{stub}:{os.environ['PATH']}", HOME=str(tmp_path))
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
