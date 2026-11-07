#!/usr/bin/env python3
"""[banco sin red] Comprobación en seco de la variante r5. Sin hosts. PRODUCTO=/r pytest banco_variante.py
Cubre: la curva con y sin la opción, el aplicar/revertir con un systemctl simulado, el comprobador estricto, que
generadores.sh acepta el argv de la variante y que rechaza otro distinto."""
import datetime
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
R = Path(os.environ.get("PRODUCTO", "/r"))
sys.path.insert(0, str(R / "tests"))
os.environ.setdefault("ECARGA_DIRS", str(R / "deploy" / "etapa4" / "ecarga"))
from test_etapa4_ecarga_prep import Lab                                                         # noqa: E402

PERFILES = [("ofimatica", "10.10.20.21"), ("navegacion", "10.10.20.22"), ("descargas", "10.10.20.23"),
            ("aplicacion", "10.10.20.24"), ("ligero", "10.10.20.25"), ("erratico", "10.10.20.26")]
GEN = "/home/adminclientes/laboratorio/clientes_lab.py"
CONF = "10-forzar-laborable-r5.conf"
FAKE_SC = r"""#!/bin/bash
# systemctl simulado: lee las unidades y los drop-ins de $CF_RAIZ como haría systemd
echo "$*" >> "$CF_RAIZ/llamadas.log"
case "$1" in
  daemon-reload) [ ! -e "$CF_RAIZ/falla_reload" ]; exit $? ;;
  is-active) cat "$CF_RAIZ/activo-$2" 2>/dev/null || echo inactive; exit 0 ;;
  show) p=$3; u=$5; n=${u#cyberflow-lab-}; n=${n%.service}; d="$CF_RAIZ/etc/systemd/system/$u.d"
    case $p in
      DropInPaths) ls "$d"/*.conf 2>/dev/null | tr '\n' ' ' | sed 's/ $//'; echo ;;
      MainPID) cat "$CF_RAIZ/pid-$n" 2>/dev/null || echo 0 ;;
      ExecStart)
        if ls "$d"/*.conf > /dev/null 2>&1; then a=$(sed -n 's/^ExecStart=\(.\+\)$/\1/p' "$d"/*.conf)
        else a=$(cat "$CF_RAIZ/base-$n"); fi
        echo "{ path=/usr/bin/python3 ; argv[]=$a ; ignore_errors=no ; start_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }" ;;
    esac ;;
esac
"""


def cargar_curva():
    f = R / "scripts" / "laboratorio" / "clientes_lab.py"
    assert hashlib.sha256(f.read_bytes()).hexdigest().startswith("ae5134a778e6")
    e = importlib.util.spec_from_file_location("clientes_lab_banco", f)
    m = importlib.util.module_from_spec(e)
    sys.modules["clientes_lab_banco"] = m
    e.loader.exec_module(m)
    return m.factor_horario


def test_curva_domingo_forzado_igual_al_lunes():
    f = cargar_curva()
    dom = [datetime.datetime(2026, 11, 8, 3, m) for m in range(0, 60)] + [datetime.datetime(2026, 11, 8, 4, m) for m in range(0, 18)]
    lun = [d + datetime.timedelta(days=1) for d in dom]
    assert {f(d, True) for d in dom} == {0.12}
    assert {f(d) for d in lun} == {0.12}
    assert {round(f(d), 6) for d in dom} == {0.036}


@pytest.fixture
def h(tmp_path):
    r = tmp_path / "raiz"
    (r / "etc/systemd/system").mkdir(parents=True)
    for n, ip in PERFILES:
        (r / f"base-{n}").write_text(f"/usr/bin/python3 {GEN} --perfil {n} --origen {ip} --servidor 10.10.30.10 --dns 10.10.10.20")
    sc = tmp_path / "systemctl"
    sc.write_text(FAKE_SC)
    sc.chmod(sc.stat().st_mode | stat.S_IEXEC)
    g = tmp_path / "gen.py"
    g.write_text("# generador\n")
    env = dict(os.environ, CF_RAIZ=str(r), CF_SYSTEMCTL=str(sc), CF_GEN=str(g), CF_HASH=hashlib.sha256(g.read_bytes()).hexdigest(),
               CF_PROC=str(tmp_path / "proc"))

    class H:
        raiz, entorno, tmp = r, env, tmp_path

        def forzar(self, o):
            return subprocess.run(["bash", str(AQUI / "forzar_laborable.sh"), o], env=env, capture_output=True, text=True)

        def comp(self, m):
            return subprocess.run(["bash", str(AQUI / "comprobar_forzar_host.sh"), m], env=env, capture_output=True, text=True)
    return H()


def test_estado_inicial_es_sin_y_no_con(h):
    assert h.comp("sin").returncode == 0
    assert h.comp("con").returncode == 1


def test_aplicar_comprobar_y_revertir_deja_el_estado_inicial(h):
    r = h.forzar("aplicar")
    assert r.returncode == 0, r.stdout
    assert h.comp("con").returncode == 0
    assert h.comp("sin").returncode == 1
    assert "daemon-reload" in (h.raiz / "llamadas.log").read_text()
    r = h.forzar("revertir")
    assert r.returncode == 0, r.stdout
    assert h.comp("sin").returncode == 0
    assert not list((h.raiz / "etc/systemd/system").iterdir())


def test_con_el_target_activo_no_cambia_nada(h):
    (h.raiz / "activo-cyberflow-lab.target").write_text("active\n")
    assert h.forzar("aplicar").returncode == 1
    assert not list((h.raiz / "etc/systemd/system").iterdir())
    assert "daemon-reload" not in (h.raiz / "llamadas.log").read_text()


def test_con_una_unidad_activa_no_cambia_nada(h):
    (h.raiz / "activo-cyberflow-lab-ligero.service").write_text("active\n")
    assert h.forzar("revertir").returncode == 1


def test_hash_distinto_no_cambia_nada(h):
    h.entorno["CF_HASH"] = "0" * 64
    assert h.forzar("aplicar").returncode == 1
    assert not list((h.raiz / "etc/systemd/system").iterdir())
    assert h.comp("sin").returncode == 1


def test_no_pisa_un_dropin_ajeno(h):
    d = h.raiz / "etc/systemd/system/cyberflow-lab-ligero.service.d"
    d.mkdir()
    (d / "otro.conf").write_text("[Service]\n")
    assert h.forzar("aplicar").returncode == 1
    assert not (d / CONF).exists()


def test_revertir_conserva_ficheros_ajenos(h):
    assert h.forzar("aplicar").returncode == 0
    d = h.raiz / "etc/systemd/system/cyberflow-lab-ligero.service.d"
    (d / "otro.conf").write_text("[Service]\n")
    assert h.forzar("revertir").returncode == 1
    assert (d / "otro.conf").exists()


def test_un_solo_perfil_sin_forzar_no_cumple(h):
    assert h.forzar("aplicar").returncode == 0
    (h.raiz / "etc/systemd/system/cyberflow-lab-erratico.service.d" / CONF).unlink()
    (h.raiz / "etc/systemd/system/cyberflow-lab-erratico.service.d").rmdir()
    r = h.comp("con")
    assert r.returncode == 1 and "erratico" in r.stdout


def test_opcion_de_mas_no_cumple(h):
    assert h.forzar("aplicar").returncode == 0
    f = h.raiz / "etc/systemd/system/cyberflow-lab-ligero.service.d" / CONF
    f.write_text(f.read_text().replace("--forzar-laborable", "--forzar-laborable --intensidad 2"))
    assert h.comp("con").returncode == 1


def test_fallo_de_lectura_nunca_aprueba(h):
    h.entorno["CF_SYSTEMCTL"] = "/bin/false"
    assert h.comp("con").returncode == 3
    assert h.comp("sin").returncode == 3


def test_vivo_exige_el_argv_de_cada_proceso(h):
    assert h.forzar("aplicar").returncode == 0
    for i, (n, ip) in enumerate(PERFILES):
        pid = 100 + i
        (h.raiz / f"pid-{n}").write_text(f"{pid}\n")
        d = h.tmp / "proc" / str(pid)
        d.mkdir(parents=True)
        (d / "cmdline").write_bytes(b"\0".join(x.encode() for x in ["/usr/bin/python3", GEN, "--perfil", n, "--origen", ip, "--servidor",
                                                                    "10.10.30.10", "--dns", "10.10.10.20", "--forzar-laborable"]) + b"\0")
    assert h.comp("vivo").returncode == 0
    d = h.tmp / "proc" / "105" / "cmdline"
    d.write_bytes(d.read_bytes().replace(b"--forzar-laborable\0", b""))
    r = h.comp("vivo")
    assert r.returncode == 1 and "erratico" in r.stdout


def lab_con_variante(tmp):
    lab = Lab(tmp)
    for p, ip in PERFILES:
        exe = (f"{{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 {lab.gen} --perfil {p} --origen {ip} "
               "--servidor 10.10.30.10 --dns 10.10.10.20 --forzar-laborable ; ignore_errors=no ; start_time=[n/a] ; pid=0 }")
        lab.unidad(f"cyberflow-lab-{p}.service", ExecStart=exe)
    return lab


def test_generadores_acepta_la_variante(tmp_path):
    lab = lab_con_variante(tmp_path)
    r = subprocess.run(["bash", str(lab.pkg / "generadores.sh"), "configuracion"], env=lab.env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.count("OK cyberflow-lab-") == 6


def test_generadores_rechaza_otro_origen(tmp_path):
    lab = lab_con_variante(tmp_path)
    u = "cyberflow-lab-ligero.service"
    lab.unidad(u, ExecStart=lab.leer(u)["ExecStart"].replace("10.10.20.25", "10.10.20.99"))
    r = subprocess.run(["bash", str(lab.pkg / "generadores.sh"), "configuracion"], env=lab.env, capture_output=True, text=True)
    assert r.returncode == 4, r.stdout + r.stderr
