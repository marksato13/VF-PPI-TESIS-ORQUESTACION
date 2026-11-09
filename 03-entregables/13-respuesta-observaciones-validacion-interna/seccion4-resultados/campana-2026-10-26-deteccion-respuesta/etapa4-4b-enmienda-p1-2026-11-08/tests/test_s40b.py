"""s40b: completa un s40 v2 que falló SOLO en las dos extracciones de journal de tcpdump (sudo -n journalctl ... -o short-iso-precise).
El escenario previo es REAL: se ejecuta el guion s40 v2 con un sudo falso que rechaza esa forma, y sobre el resultado se ejecuta s40b.
Necesita bash y Linux (se omite en Windows)."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from test_s40_copias import lab  # noqa: E402,F401  (fixture del HOME falso de s40)

S40 = AQUI.parent / "guiones" / "s40_cierre_e4.sh"
S40B = AQUI.parent / "guiones" / "s40b_completar_copias_e4.sh"
pytestmark = pytest.mark.skipif(shutil.which("bash") is None or sys.platform == "win32", reason="requiere bash/Linux")
UN_ANILLO, UN_VIA = "ppi-motor-capture", "ppi-via-rapida@ens37"
PIDS = {UN_ANILLO: [1355], UN_VIA: [1387, 1389]}      # la vía: servicio 1387 y tcpdump hijo 1389


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(timespec="microseconds")


def journal(unidad, t0, t1, pid, paso=30.0, cortar=None, truncar_cada=0):
    """Salida de `journalctl -o short-iso-precise` en el FORMATO REAL del Sensor1: una línea por lectura SIGUSR1; el identificador es
    tcpdump[PID] en el anillo y bash[PID] en la vía rápida."""
    ident = "bash" if "via" in unidad else "tcpdump"
    out, t, k = [], t0, 0
    while t <= t1:
        if cortar is None or not (cortar[0] <= t <= cortar[1]):
            k += 1
            cola = ", 100 packets received by filter, 0 packets dropped by kernel" if not (truncar_cada and k % truncar_cada == 0) else ""
            out.append(f"{iso(t)} cyberflow-sensor {ident}[{pid}]: tcpdump: 100 packets captured{cola}")
        t += paso
    return "\n".join(out) + "\n"


@pytest.fixture
def fallido(lab, tmp_path):
    """Un HOME donde s40 v2 REALMENTE terminó con COPIAS INCOMPLETAS por las dos extracciones con sudo."""
    now = time.time()
    t_ini = now - 4 * 3600
    (lab.b / "eve/inicio.json").write_text(json.dumps({"t": t_ini, "inode": 1, "size": 0}))
    stub = Path(lab.env["PATH"].split(":")[0])
    jd = tmp_path / "journal"; jd.mkdir()
    cg = tmp_path / "cgroup"
    for u, pids in PIDS.items():
        d = cg / "system.slice" / f"{u}.service"; d.mkdir(parents=True)
        (d / "cgroup.procs").write_text("\n".join(map(str, pids)) + "\n")
    (stub / "sudo").write_text('#!/bin/sh\nshift\ncase "$*" in *short-iso-precise*) echo "sudo: a password is required" >&2; exit 1;; esac\nexec "$@"\n')
    (stub / "journalctl").write_text(
        '#!/bin/sh\nu=""; prev=""\nfor a in "$@"; do [ "$prev" = "-u" ] && u="$a"; prev="$a"; done\n'
        'case "$*" in *short-iso-precise*) f="$JDIR/$u.txt"; [ -f "$JDIR/$u.rc" ] && rc=$(cat "$JDIR/$u.rc") || rc=0; [ -f "$f" ] && cat "$f"; exit $rc;;\n'
        '*) echo "2026-11-08T00:00:00 linea de journal";; esac\n')
    (stub / "systemctl").write_text(
        '#!/bin/sh\ncase "$*" in *ControlGroup*) for a in "$@"; do u="$a"; done; echo "/system.slice/$u.service";;\n'
        '*--value*) echo 1;; *is-active*) echo active;; *) echo "Id=x";; esac\n')
    for f in stub.iterdir():
        f.chmod(0o755)
    lab.env.update(JDIR=str(jd), CF_CGROUP_ROOT=str(cg))
    lab.jd, lab.t_ini, lab.cg = jd, t_ini, cg
    r = subprocess.run(["bash", str(S40), "4b"], env=lab.env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 1 and "COPIAS INCOMPLETAS (2 fallos" in r.stdout, r.stdout + r.stderr
    lab.cierre_t = float((lab.b / "cierre.t").read_text())
    lab.salud = lab.b / "salud"
    assert (lab.salud / "tcpdump-anillo.log").stat().st_size == 0 and (lab.salud / "tcpdump-via.log").stat().st_size == 0

    def preparar(anillo=None, via=None, rc_anillo=0, rc_via=0):
        """Deja listo lo que daría el journal sin sudo (ventana completa por defecto)."""
        a = anillo if anillo is not None else journal(UN_ANILLO, t_ini - 120, lab.cierre_t + 40, 1355)
        v = via if via is not None else journal(UN_VIA, t_ini - 120, lab.cierre_t + 40, 1389)
        (jd / f"{UN_ANILLO}.txt").write_text(a); (jd / f"{UN_VIA}.txt").write_text(v)
        (jd / f"{UN_ANILLO}.rc").write_text(str(rc_anillo)); (jd / f"{UN_VIA}.rc").write_text(str(rc_via))
    lab.preparar = preparar
    lab.s40b = lambda: subprocess.run(["bash", str(S40B), "4b"], env=lab.env, capture_output=True, text=True, timeout=120)
    return lab


def sin_marca(lab):
    return not (lab.c / "COPIAS-COMPLETAS.ok").exists() and not (lab.c / "SHA256SUMS").exists()


def test_recupera_los_dos_logs_y_declara_completas(fallido):
    lab = fallido
    lab.preparar()
    antes_cierre = (lab.b / "cierre.t").read_bytes(); antes_inc = (lab.c / "COPIAS-INCOMPLETAS.txt").read_bytes()
    antes_motor = (lab.c / "motor_decision.log").read_bytes(); antes_fuentes = (lab.c / "FUENTES-al-copiar.tsv").read_bytes()
    r = lab.s40b()
    assert r.returncode == 0 and "## COPIAS COMPLETAS (recuperadas por s40b)" in r.stdout, r.stdout + r.stderr
    assert (lab.c / "COPIAS-COMPLETAS.ok").read_text().startswith("ok s40b")
    # los dos logs quedan con contenido y con la ventana pedida
    for n in ("tcpdump-anillo.log", "tcpdump-via.log"):
        assert (lab.salud / n).stat().st_size > 1000
    assert b"tcpdump[1355]" in (lab.salud / "tcpdump-anillo.log").read_bytes() and b"bash[1389]" in (lab.salud / "tcpdump-via.log").read_bytes()
    # hashes APARTE: verifican y no están en copias/SHA256SUMS
    v = subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS-tcpdump"], cwd=lab.salud, capture_output=True, text=True)
    assert v.returncode == 0, v.stdout + v.stderr
    sumas = (lab.c / "SHA256SUMS").read_text()
    assert "tcpdump-anillo.log" not in sumas and "tcpdump-via.log" not in sumas
    assert subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS"], cwd=lab.c, capture_output=True).returncode == 0
    # lo ya tomado queda intacto y la evidencia del fallo se conserva
    assert (lab.b / "cierre.t").read_bytes() == antes_cierre and (lab.c / "motor_decision.log").read_bytes() == antes_motor
    assert (lab.c / "FUENTES-al-copiar.tsv").read_bytes() == antes_fuentes and (lab.c / "COPIAS-INCOMPLETAS.txt").read_bytes() == antes_inc
    assert (lab.c / "s40-fallido/COPIAS-INCOMPLETAS.txt").read_bytes() == antes_inc and (lab.c / "s40-fallido/estado-antes.txt").exists()
    assert (lab.c / "s40b-ejecutado.txt").exists() and (lab.c / "COPIAS-RECUPERADAS-s40b.txt").exists()
    assert not list(lab.salud.glob("*.s40b-tmp*"))


def _no_completa(lab, r, motivo=None):
    assert r.returncode == 1, r.stdout + r.stderr
    assert sin_marca(lab), "no debe haber COPIAS-COMPLETAS.ok ni SHA256SUMS"
    assert (lab.salud / "tcpdump-anillo.log").stat().st_size == 0 and (lab.salud / "tcpdump-via.log").stat().st_size == 0, "los logs quedan como estaban"
    assert not list(lab.salud.glob("*.s40b-tmp*")) and not (lab.salud / "SHA256SUMS-tcpdump").exists()
    assert "s40b NO COMPLETÓ" in r.stdout
    if motivo:
        assert motivo in r.stdout, r.stdout


def test_extraccion_vacia_impide_la_marca(fallido):
    fallido.preparar(anillo="")
    _no_completa(fallido, fallido.s40b(), "la extracción de ppi-motor-capture está vacía")


def test_extraccion_vacia_de_la_via_impide_la_marca(fallido):
    fallido.preparar(via="")
    _no_completa(fallido, fallido.s40b(), "la extracción de ppi-via-rapida@ens37 está vacía")


@pytest.mark.parametrize("cual", ["anillo", "via"])
def test_journalctl_con_rc_distinto_de_cero_impide_la_marca(fallido, cual):
    fallido.preparar(**({"rc_anillo": 1} if cual == "anillo" else {"rc_via": 1}))
    _no_completa(fallido, fallido.s40b(), "terminó con rc=1")


def test_la_via_con_lecturas_de_otra_unidad_se_rechaza(fallido):
    lab = fallido
    # la «vía» trae las lecturas del anillo (PID 1355): no pertenecen a su unidad
    lab.preparar(via=journal(UN_VIA, lab.t_ini - 120, lab.cierre_t + 40, 1355))
    _no_completa(lab, lab.s40b(), "que no pertenecen a la unidad")


def test_dos_logs_identicos_se_rechazan(fallido):
    lab = fallido
    mismo = journal(UN_ANILLO, lab.t_ini - 120, lab.cierre_t + 40, 1355)
    lab.preparar(anillo=mismo, via=mismo)
    _no_completa(lab, lab.s40b())


def test_no_cubre_el_inicio_se_rechaza(fallido):
    lab = fallido
    lab.preparar(anillo=journal(UN_ANILLO, lab.t_ini + 600, lab.cierre_t + 40, 1355))
    _no_completa(lab, lab.s40b(), "es posterior al inicio requerido")


def test_no_cubre_el_final_se_rechaza(fallido):
    lab = fallido
    lab.preparar(via=journal(UN_VIA, lab.t_ini - 120, lab.cierre_t - 900, 1389))
    _no_completa(lab, lab.s40b(), "es anterior al fin requerido")


def test_lecturas_truncadas_se_rechazan(fallido):
    lab = fallido
    a = journal(UN_ANILLO, lab.t_ini - 120, lab.cierre_t + 40, 1355)
    lab.preparar(anillo=journal(UN_ANILLO, lab.t_ini - 120, lab.cierre_t + 40, 1355, truncar_cada=50))
    _no_completa(lab, lab.s40b(), "lecturas truncadas")


def test_un_hueco_se_informa_pero_no_impide_la_marca(fallido):
    """Un hueco en medio es un asunto de calidad de los datos (lo clasifica s50 como C3), no de que la extracción esté incompleta."""
    lab = fallido
    lab.preparar(anillo=journal(UN_ANILLO, lab.t_ini - 120, lab.cierre_t + 40, 1355, cortar=(lab.t_ini + 3600, lab.t_ini + 3900)))
    r = lab.s40b()
    assert r.returncode == 0 and '"hueco_max_s": 3' in r.stdout, r.stdout     # 330 s de hueco: se informa, no bloquea


def test_copia_ya_tomada_alterada_se_rechaza(fallido):
    lab = fallido
    lab.preparar()
    (lab.c / "motor_decision.log").write_bytes(b"x" * 10)
    _no_completa(lab, lab.s40b(), "no cubre los")


def test_otro_fallo_distinto_de_las_dos_extracciones_no_se_resuelve_con_s40b(fallido):
    lab = fallido
    lab.preparar()
    with open(lab.c / "COPIAS-INCOMPLETAS.txt", "a") as fh:
        fh.write("cp -p /home/x/motor_decision.log copia\n")
    r = lab.s40b()
    assert r.returncode == 2 and "OTROS fallos" in r.stdout and sin_marca(lab)
    assert not (lab.c / "s40b-ejecutado.txt").exists(), "no se llegó a ejecutar nada"


def test_sin_s40_fallido_no_hace_nada(fallido):
    lab = fallido
    lab.preparar()
    os.remove(lab.c / "COPIAS-INCOMPLETAS.txt")
    r = lab.s40b()
    assert r.returncode == 2 and "no hay un s40 fallido" in r.stdout and sin_marca(lab)


def test_se_ejecuta_una_sola_vez(fallido):
    lab = fallido
    lab.preparar(anillo="")                                  # primer intento: falla
    assert lab.s40b().returncode == 1
    lab.preparar()                                           # aunque ahora los datos sean buenos, NO se vuelve a ejecutar solo
    r = lab.s40b()
    assert r.returncode == 2 and "ya se ejecutó una vez" in r.stdout and sin_marca(lab)


def test_si_ya_estan_completas_no_hace_nada(fallido):
    lab = fallido
    lab.preparar()
    assert lab.s40b().returncode == 0
    r = lab.s40b()
    assert r.returncode == 2 and "ya están declaradas completas" in r.stdout


def test_logs_con_contenido_previo_no_se_pisan(fallido):
    lab = fallido
    lab.preparar()
    (lab.salud / "tcpdump-anillo.log").write_text("ya habia algo\n")
    r = lab.s40b()
    assert r.returncode == 2 and "ya tienen contenido" in r.stdout and sin_marca(lab)
    assert (lab.salud / "tcpdump-anillo.log").read_text() == "ya habia algo\n"
