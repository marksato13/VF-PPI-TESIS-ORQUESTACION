"""s40 v2: solo declara «copias completas» si todas las operaciones de copia tuvieron éxito. Banco con HOME falso y sudo/journalctl/systemctl
de mentira; se ejecuta el guion REAL con bash. Necesita bash y /proc (se omite en Windows)."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
S40 = AQUI.parent / "guiones" / "s40_cierre_e4.sh"
HERR = Path(os.environ.get("CF_SCRIPT", AQUI.parent / "herramientas" / "cf_4b_rotacion.py"))
pytestmark = pytest.mark.skipif(shutil.which("bash") is None or sys.platform == "win32", reason="requiere bash/Linux")


@pytest.fixture
def lab(tmp_path):
    h = tmp_path / "home"; b = h / "cf-e4/4b"; stub = tmp_path / "stub"; stub.mkdir()
    for d in ("replay", "archivo-pcap", "recursos", "salud", "eve", "estado-inicial", "copias"):
        (b / d).mkdir(parents=True)
    for d in ("cyberflow/logs/_state-e4", "feed-v2", "feed", "cyberflow-e4/ec78ca5"):
        (h / d).mkdir(parents=True)
    (b / "replay/rc.txt").write_text("rc=0\n"); (b / "archivo-pcap.rc").write_text("0\n")
    (b / "archivo-pcap/ESTADO.txt").write_text("OK vistos=1\n"); (b / "archivo-pcap/archivar.log").write_text("2026 OK live-1.pcap\n")
    (b / "archivo-pcap/live-1.pcap").write_bytes(b"p")
    (b / "recursos/muestras.jsonl").write_text("{}\n"); (b / "salud/muestras.jsonl").write_text("{}\n")
    (b / "eve/inicio.json").write_text(json.dumps({"t": 1_800_000_000})); (b / "eve/motor-inicio.txt").write_text("123\n")
    (b / "eve/stats-inicio.log").write_text("s\n"); (b / "estado-inicial/servicios.txt").write_text("MainPID=1\nNRestarts=0\n")
    wr = lambda p, n: p.write_text((f"{p.name} linea\n") * n)
    wr(h / "cyberflow/logs/motor_decision.log", 50); wr(h / "cyberflow/logs/_state-e4/ciclos.jsonl", 20)
    for n in ("traza", "senales-rapidas", "senales-if", "via-rapida-resumen"):
        wr(h / f"feed-v2/{n}.jsonl", 10)
    for n in ("feed.json", "feed.sig", "estado.json"):
        (h / "feed-v2" / n).write_text("{}\n"); (h / "feed" / n).write_text("{}\n")
    stats = tmp_path / "stats.log"; stats.write_text("stats\n" * 30)
    procs = [subprocess.Popen(["sleep", "300"]) for _ in range(3)]
    (b / "archivo-pcap.pid").write_text(f"{procs[0].pid}\n"); (b / "recursos/muestreo.pid").write_text(f"{procs[1].pid}\n"); (b / "salud/muestrear.pid").write_text(f"{procs[2].pid}\n")
    (stub / "sudo").write_text('#!/bin/sh\nshift\nexec "$@"\n')
    (stub / "journalctl").write_text('#!/bin/sh\necho "2026-11-08T00:00:00 linea de journal"\n')
    (stub / "systemctl").write_text('#!/bin/sh\ncase "$*" in *--value*) echo 1;; *is-active*) echo active;; *) echo "Id=x";; esac\n')
    for f in stub.iterdir():
        f.chmod(0o755)
    env = dict(os.environ, HOME=str(h), PATH=f"{stub}:{os.environ['PATH']}", CF_STATS_LOG=str(stats))
    class L: pass
    l = L(); l.h, l.b, l.c, l.env, l.stats = h, b, b / "copias", env, stats
    l.run = lambda: subprocess.run(["bash", str(S40), "4b"], env=env, capture_output=True, text=True, timeout=120)
    yield l
    for p in procs:
        p.kill()


def test_s40_v2_todo_bien_declara_copias_completas(lab):
    r = lab.run()
    assert r.returncode == 0 and "## COPIAS COMPLETAS" in r.stdout, r.stdout + r.stderr
    assert (lab.c / "COPIAS-COMPLETAS.ok").read_text().startswith("ok") and (lab.c / "SHA256SUMS").stat().st_size > 0
    assert not (lab.c / "COPIAS-INCOMPLETAS.txt").exists()
    spec = importlib.util.spec_from_file_location("cf_rot3", HERR); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    f = m.leer_fuentes(str(lab.c / "FUENTES-al-copiar.tsv"))
    assert f["motor_decision.log"] == (lab.h / "cyberflow/logs/motor_decision.log").stat().st_size
    assert set(f) == {"ciclos.jsonl", "motor_decision.log", "stats-fin.log", "feed-v2/traza.jsonl", "feed-v2/senales-rapidas.jsonl",
                      "feed-v2/senales-if.jsonl", "feed-v2/via-rapida-resumen.jsonl"}
    v = subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS"], cwd=lab.c, capture_output=True, text=True)
    assert v.returncode == 0, v.stdout + v.stderr


@pytest.mark.parametrize("fallo", ["fuente_motor_ausente", "feed_v2_traza_ausente", "destino_no_escribible", "stats_ausente"])
def test_s40_v2_un_cp_fallido_impide_declarar_completas_y_no_genera_manifiesto(lab, fallo):
    if fallo == "fuente_motor_ausente":
        os.remove(lab.h / "cyberflow/logs/motor_decision.log")
    elif fallo == "feed_v2_traza_ausente":
        os.remove(lab.h / "feed-v2/traza.jsonl")
    elif fallo == "stats_ausente":
        os.remove(lab.stats)
    elif fallo == "destino_no_escribible":
        (lab.c / "archivar.log").mkdir()                       # cp -p fuente destino-que-es-directorio copia dentro, así que se bloquea con un dir no vacío
        (lab.c / "archivar.log" / "x").write_text("x")
        os.chmod(lab.c / "archivar.log", 0o500)
        (lab.c / "ciclos.jsonl").mkdir(); os.chmod(lab.c / "ciclos.jsonl", 0o500)
    r = lab.run()
    if fallo == "destino_no_escribible":
        os.chmod(lab.c / "archivar.log", 0o700); os.chmod(lab.c / "ciclos.jsonl", 0o700)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "COPIAS INCOMPLETAS" in r.stdout and "FALLO COPIA" in r.stdout
    assert not (lab.c / "COPIAS-COMPLETAS.ok").exists() and not (lab.c / "SHA256SUMS").exists()
    assert (lab.c / "COPIAS-INCOMPLETAS.txt").stat().st_size > 0


def test_s40_v2_copia_que_no_cubre_la_fuente_al_empezar_se_detecta(lab):
    """cp que deja un fichero más corto que la fuente (disco lleno): sustituimos cp por uno que trunca la copia de motor_decision.log."""
    stub = Path(lab.env["PATH"].split(":")[0])
    (stub / "cp").write_text('#!/bin/sh\n/bin/cp "$@"; rc=$?\nfor a in "$@"; do last="$a"; done\ncase "$last" in */motor_decision.log) truncate -s 100 "$last";; esac\nexit $rc\n')
    (stub / "cp").chmod(0o755)
    r = lab.run()
    assert r.returncode == 1 and "motor_decision.log no cubre" in r.stdout, r.stdout
    assert not (lab.c / "COPIAS-COMPLETAS.ok").exists() and not (lab.c / "SHA256SUMS").exists()


def test_s40_v2_ejecutado_dos_veces_no_hereda_marcas_viejas(lab):
    assert lab.run().returncode == 0
    os.remove(lab.h / "feed-v2/traza.jsonl")
    r = lab.run()
    assert r.returncode == 1 and not (lab.c / "COPIAS-COMPLETAS.ok").exists() and not (lab.c / "SHA256SUMS").exists()
