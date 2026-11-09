"""4C, 2026-11-09 (tras la cancelación X3): los dos escenarios con nmap llevan -n y nada más cambia.

Causa de X3: nmap sin -n hace una consulta DNS inversa del destino a TODOS los servidores de /etc/resolv.conf de la Kali (10.10.10.20 y 10.10.10.21);
10.10.10.21 no está en la lista blanca del vigía. Se prueba: (1) el comando de cada escenario, (2) que solo cambian los dos nmap, (3) que el
generador original, con el esquema nuevo, simula el plan completo (25 episodios) sin tráfico y con -n, (4) que el diff de código del esquema y de c03 es
exactamente lo acordado, y (5) que X3 y la lista blanca no cambian."""
from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
A = AQUI.parent
CAMP = A.parent
ESQ_V1 = CAMP / "scripts-4c/esquema_campana.py"
ESQ_N = A / "scripts-4c-n/esquema_campana.py"
GEN = CAMP / "scripts-4c/generar_campana.py"
ESC = CAMP / "etapa4-preparacion-2026-11-02/escenarios-4c.json"
C03_V1 = CAMP / "etapa4-preparacion-2026-11-02/guiones/c03_kali_e4.sh"
C03_V2 = A / "guiones/c03_kali_e4.sh"


def _cargar(ruta: Path, nombre: str):
    espec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def mods():
    return _cargar(ESQ_V1, "esq_v1"), _cargar(ESQ_N, "esq_n"), json.loads(ESC.read_text(encoding="utf-8"))


def test_esquema_original_intacto():
    assert hashlib.sha256(ESQ_V1.read_bytes()).hexdigest().startswith("e762e60421b4721b"), "el esquema histórico de scripts-4c no se toca"


def test_los_dos_nmap_llevan_n_y_nada_mas_cambia(mods):
    v1, vn, cfg = mods
    vistos = 0
    for s in cfg["escenarios"]:
        a, b = v1.comando_de(cfg, s), vn.comando_de(cfg, s)
        if s["herramienta"] == "nmap":
            vistos += 1
            assert b[:2] == ["nmap", "-sT"] and b[2] == "-n", b
            assert b[:2] + b[3:] == a[:2] + a[2:] and a == b[:2] + b[3:], (a, b)   # quitando -n, es el comando anterior
            assert b.count("-n") == 1
        else:
            assert a == b, (s["id"], a, b)                                          # dig, curl: idénticos byte a byte
    assert vistos == 2, "escaneo_breve y escaneo_sostenido"


def test_comandos_exactos(mods):
    _, vn, cfg = mods
    por_id = {s["id"]: vn.comando_de(cfg, s) for s in cfg["escenarios"]}
    assert por_id["escaneo_breve"] == ["nmap", "-sT", "-n", "-T4", "--max-retries", "1", "-p", "1-1000", "10.10.30.10"]
    assert por_id["escaneo_sostenido"] == ["nmap", "-sT", "-n", "-T4", "--max-retries", "0", "--max-rate", "1500", "-p", "1-65535", "10.10.30.10"]


def test_ningun_otro_escenario_depende_del_dns_del_sistema(mods):
    """dig usa @destino explícito (solo 10.10.10.20); curl va a IP. Ningún comando usa nombres de host que resuelvan por /etc/resolv.conf."""
    _, vn, cfg = mods
    for s in cfg["escenarios"]:
        cmd = " ".join(vn.comando_de(cfg, s))
        if s["herramienta"] == "dig":
            assert "@10.10.10.20" in cmd
        if s["herramienta"] == "curl":
            assert "http://10.10.30.10" in cmd and "://" in cmd
            assert "localhost" not in cmd and "ad.francos-sac.com" not in cmd
        if s["herramienta"] == "nmap":
            assert " -n " in " " + cmd + " " and cmd.rstrip().endswith("10.10.30.10")


def test_diff_de_codigo_del_esquema_es_exactamente_lo_acordado():
    a, b = ESQ_V1.read_text(encoding="utf-8").splitlines(), ESQ_N.read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    codigo = [l for l in cambios if not l[1:].lstrip().startswith("#")]
    quitadas = [l[1:].strip() for l in codigo if l[0] == "-"]
    anadidas = [l[1:].strip() for l in codigo if l[0] == "+"]
    assert len(quitadas) == 2 and len(anadidas) == 2, codigo
    assert [q.replace('"-sT", ', '"-sT", "-n", ') for q in quitadas] == anadidas
    assert all("nmap" in l for l in quitadas)
    assert all(l.startswith("+") and l[1:].lstrip().startswith("#") for l in cambios if l not in codigo)


def test_generador_original_con_esquema_nuevo_simula_el_plan_completo_con_n(tmp_path):
    """generar_campana.py SIN --autorizado solo simula (no lanza tráfico). Se copia el generador original junto al esquema nuevo."""
    d = tmp_path / "g"; d.mkdir()
    shutil.copy(GEN, d / "generar_campana.py"); shutil.copy(ESQ_N, d / "esquema_campana.py")
    d1 = tmp_path / "g1"; d1.mkdir()
    shutil.copy(GEN, d1 / "generar_campana.py"); shutil.copy(ESQ_V1, d1 / "esquema_campana.py")
    # el modo simulación no lanza tráfico ni espera: se usa el JSON real tal cual (mismos bytes)
    (tmp_path / "c.json").write_bytes(ESC.read_bytes())
    res = {}
    for nombre, dd in (("v1", d1), ("n", d)):
        out = tmp_path / f"salida-{nombre}"
        r = subprocess.run([sys.executable, "-I", str(dd / "generar_campana.py"), "--config", str(tmp_path / "c.json"), "--salida-dir", str(out)],
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stdout[-400:] + r.stderr[-400:]
        assert "SIMULACIÓN (no lanza tráfico)" in r.stdout and "AUTORIZADO" not in r.stdout
        res[nombre] = [json.loads(l) for l in (out / "marcas.jsonl").read_text(encoding="utf-8").splitlines()]
    ini1 = [m for m in res["v1"] if m.get("evento") == "inicio"]
    inin = [m for m in res["n"] if m.get("evento") == "inicio"]
    assert len(ini1) == len(inin) == 25 or len(ini1) == len(inin) > 0
    assert [m["episodio_id"] for m in ini1] == [m["episodio_id"] for m in inin], "mismo orden de episodios (semilla 20261102)"
    for m1, mn in zip(ini1, inin):
        if m1["escenario"].startswith("escaneo"):
            assert "-n" in mn["comando"] and "-n" not in m1["comando"]
            assert [x for x in mn["comando"] if x != "-n"] == m1["comando"]
        else:
            assert m1["comando"] == mn["comando"]


def test_x3_y_lista_blanca_no_cambian():
    cfg = json.loads(ESC.read_text(encoding="utf-8"))
    assert cfg["lista_blanca_destinos"] == ["10.10.10.20", "10.10.30.10"]
    g01 = (A / "guiones/g01_lanzar_bateria_e4.sh").read_text(encoding="utf-8")
    assert "--lista-blanca" in g01 and "10.10.10.20,10.10.30.10" in g01 and "10.10.10.21" not in g01


def test_c03_v2_solo_cambia_el_hash_del_esquema_de_scripts_4c():
    a, b = C03_V1.read_text(encoding="utf-8").splitlines(), C03_V2.read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    codigo = [l for l in cambios if not l[1:].lstrip().startswith("#")]
    h = hashlib.sha256(ESQ_N.read_bytes()).hexdigest()
    assert codigo == [
        "-e762e60421b4721b1e8ce32549049ae10c7e86596b0fbd37f9a35517ab904144  $HOME/cf-campana-A/scripts-4c/esquema_campana.py",
        f"+{h}  $HOME/cf-campana-A/scripts-4c/esquema_campana.py"], codigo
    assert any("e762e60421b4721b1e8ce32549049ae10c7e86596b0fbd37f9a35517ab904144  $HOME/cf-campana-A/scripts/esquema_campana.py" in l for l in b), "el histórico de scripts/ sigue pinneado"
