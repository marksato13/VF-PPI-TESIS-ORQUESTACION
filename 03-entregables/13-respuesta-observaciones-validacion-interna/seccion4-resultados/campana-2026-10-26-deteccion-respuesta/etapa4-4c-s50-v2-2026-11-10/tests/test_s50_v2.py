"""4C, s50 v2 (2026-11-10): Suricata medido por EVE en el paso 2 (D1) y descartes de tcpdump desde las lecturas SIGUSR1 de s40 (D2).

Se prueban con las herramientas REALES (calidad_fuentes.py, analizar.py y salud_captura 2026-11-06.1, comprobadas contra los hashes
fijados) y datos sintéticos de diseño conocido; las pruebas comprueban CÓDIGO, no son medidas. Eje común: una medición que falta
NUNCA se interpreta como cero descartes. Necesita bash/Linux (el recorrido de s50) y los montajes /camp y /p1 (o CAMPANA y P1_DIR)."""
from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CAMP = RAIZ.parent
HERR_V2 = RAIZ / "herramientas"
SCRIPTS = CAMP / "scripts"                                   # calidad_fuentes.py, analizar.py (fijados por hash)
PINNED = CAMP / "etapa4-4b-enmienda-p1-2026-11-08/herramientas/herramientas-e4.sha256"
S50_BASE = CAMP / "etapa4-4c-paso3-eve-2026-11-08/guiones/s50_analisis_e4.sh"
S50_V2 = RAIZ / "guiones/s50_analisis_e4.sh"
P1 = Path(os.environ.get("P1_DIR", "/p1"))
SC = P1 / "salud_captura.py"
SC_SHA = "274b4d613357be60e362f13ce007f07b6bb8055e0e0029316f7bafaa845344d2"
sys.path.insert(0, str(CAMP / "etapa4-4b-enmienda-p1-2026-11-08/tests"))
os.environ.setdefault("HERR", "/nada"); os.environ.setdefault("D3B", "/nada")
import datos_sinteticos as ds       # noqa: E402
import generar_entorno_4b as g      # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("bash") is None or sys.platform == "win32", reason="requiere bash/Linux")


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def _prerrequisitos():
    if not SC.exists() or sha(SC) != SC_SHA:
        pytest.skip(f"falta salud_captura 2026-11-06.1 con hash {SC_SHA[:16]} en {P1}")
    pin ={n: h for h, n in (l.split("  ", 1) for l in PINNED.read_text().splitlines() if "  " in l)}
    for n in ("calidad_fuentes.py", "analizar.py", "generar_respaldos.py", "verificar_integridad.py"):
        assert sha(SCRIPTS / n) == pin[n], f"{n} del repositorio no coincide con el hash fijado"


# ------------------------------------------------------------------------------------------------ datos
EPISODIOS = {"e1-r1": (g.utc(7, 30), g.utc(7, 33)), "e2-r1": (g.utc(7, 44, 10), g.utc(7, 46, 30)), "e3-r1": (g.utc(7, 52, 30), g.utc(7, 53, 20))}


def marcas_texto() -> str:
    out = []
    for eid, (a, b) in EPISODIOS.items():
        base = {"episodio_id": eid, "escenario": "inundacion_http", "repeticion": 1, "destino": "10.10.30.10"}
        out.append(json.dumps({**base, "evento": "inicio", "reloj": {"pared_utc": ds.iso(a)}}))
        out.append(json.dumps({**base, "evento": "fin", "estado": "completo", "reloj": {"pared_utc": ds.iso(b)}}))
    return "\n".join(out) + "\n"


def archivar_log(t0: float, t1: float) -> str:
    out, t = [], t0
    while t <= t1:
        nombre = dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("live-%Y%m%d%H%M%S.pcap")
        out.append(f"{ds.iso(t)} OK {nombre} (100 bytes) sha=0")
        t += 5.0
    return "\n".join(out) + "\n"


def correr_calidad(tmp: Path, eve: bytes | None, **kw):
    eve_p = tmp / "eve.json"
    if eve is not None:
        eve_p.write_bytes(eve)
    (tmp / "marcas.jsonl").write_text(marcas_texto())
    (tmp / "archivar.log").write_text(archivar_log(g.utc(7, 15), g.utc(8, 20)))
    (tmp / "muestras.jsonl").write_text("")
    r = subprocess.run([sys.executable, "-I", str(HERR_V2 / "calidad_fuentes_eve.py"), "--herramientas", str(SCRIPTS), "--salud-captura", str(SC),
                        "--eve", str(eve_p), "--marcas", str(tmp / "marcas.jsonl"), "--archivador", str(tmp / "archivar.log"),
                        "--muestras", str(tmp / "muestras.jsonl"), "--duracion-pcap", "5", "--ahora", str(g.utc(9, 0)),
                        "--salida", str(tmp / "calidad.json")], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
    return json.loads((tmp / "calidad.json").read_text())


def eve_base(**kw) -> bytes:
    return ds.eve_stats(g.INI - 60, g.FIN + 60, arranque=g.INI - 86400, **kw)


# ------------------------------------------------------------------------------------------------ D1: calidad con EVE
def test_d1_eve_sano_todos_completa(tmp_path):
    j = correr_calidad(tmp_path, eve_base())
    for e in EPISODIOS:
        s = j["episodios"][e]["suricata"]
        assert j["episodios"][e]["estado"] == "completa" and s["medido"] is True and s["kernel_drops"] == 0 and s["estado"] == "cero_explicito"
    assert j["fuentes"]["suricata"] == "eve_stats" and j["fuentes"]["muestras_eve"] > 300


def test_d1_rafaga_de_descartes_degrada_solo_ese_episodio(tmp_path):
    j = correr_calidad(tmp_path, eve_base(rafagas=[(g.utc(7, 45, 0), 23)]))["episodios"]
    assert (j["e1-r1"]["estado"], j["e2-r1"]["estado"], j["e3-r1"]["estado"]) == ("completa", "degradada", "completa")
    assert j["e2-r1"]["suricata"]["kernel_drops"] == 23


def test_d1_hueco_de_eve_deja_insuficiente_no_completa(tmp_path):
    j = correr_calidad(tmp_path, eve_base(huecos=[(g.utc(7, 52, 10), g.utc(7, 53, 50))]))["episodios"]
    assert j["e3-r1"]["estado"] == "insuficiente" and j["e3-r1"]["suricata"]["medido"] is False
    assert j["e3-r1"]["suricata"]["estado"] == "cobertura_insuficiente"
    assert j["e1-r1"]["estado"] == "completa" and j["e2-r1"]["estado"] == "completa"


def test_d1_eve_sin_eventos_stats_no_es_cero(tmp_path):
    vacio = b"".join(l + b"\n" for l in eve_base().splitlines() if b'"event_type":"stats"' not in l)
    j = correr_calidad(tmp_path, vacio)["episodios"]
    for e in EPISODIOS:
        assert j[e]["estado"] == "insuficiente" and j[e]["suricata"]["medido"] is False and j[e]["suricata"]["estado"] == "ausente"
        assert "kernel_drops" not in j[e]["suricata"]


def test_d1_stats_sin_kernel_drops_no_es_cero(tmp_path):
    j = correr_calidad(tmp_path, eve_base(sin_drops=[(g.utc(7, 58, 0), g.utc(7, 58, 40)), (g.utc(7, 29, 0), g.utc(7, 34, 0))]))["episodios"]
    assert j["e1-r1"]["estado"] == "insuficiente" and j["e1-r1"]["suricata"]["estado"] == "ausente"
    assert j["e2-r1"]["estado"] == "completa"      # su tramo sí trae kernel_drops: el defecto de un tramo no contagia a otro


def test_d1_reinicio_de_suricata_dentro_del_episodio(tmp_path):
    j = correr_calidad(tmp_path, eve_base(reinicios=[g.utc(7, 45, 30)]))["episodios"]
    assert j["e2-r1"]["estado"] == "insuficiente" and j["e2-r1"]["suricata"]["estado"] == "cobertura_insuficiente"
    assert j["e1-r1"]["estado"] == "completa" and j["e3-r1"]["estado"] == "completa"


def test_d1_linea_stats_corrupta_o_eve_ausente_deja_todo_sin_medir(tmp_path):
    j = correr_calidad(tmp_path, eve_base(basura_en=g.INI - 60 + 8 * round((g.utc(7, 40) - (g.INI - 60)) / 8)))["episodios"]
    assert all(j[e]["estado"] == "insuficiente" and j[e]["suricata"]["estado"] == "error_lectura" for e in EPISODIOS)
    d2 = tmp_path / "sin_eve"; d2.mkdir()
    j2 = correr_calidad(d2, None)["episodios"]
    assert all(j2[e]["estado"] == "insuficiente" and j2[e]["suricata"]["estado"] == "error_lectura" for e in EPISODIOS)


def test_d1_el_defecto_original_se_reproduce_con_stats_log_sin_kernel_drops(tmp_path):
    (tmp_path / "marcas.jsonl").write_text(marcas_texto())
    (tmp_path / "archivar.log").write_text(archivar_log(g.utc(7, 15), g.utc(8, 20)))
    bloque = "Date: 11/1/2026 -- 08:16:00 (uptime: 1d, 08h 16m 00s)\n" + "-" * 84 + "\ncapture.kernel_packets | Total | 41020424\n"
    (tmp_path / "stats.log").write_text(bloque)
    r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "calidad_fuentes.py"), "--marcas", str(tmp_path / "marcas.jsonl"), "--stats", str(tmp_path / "stats.log"),
                        "--archivador", str(tmp_path / "archivar.log"), "--duracion-pcap", "5", "--salida", str(tmp_path / "o.json")], capture_output=True, text=True)
    assert r.returncode == 0
    j = json.loads((tmp_path / "o.json").read_text())["episodios"]
    assert all(j[e]["estado"] == "insuficiente" and "sin stats.log" in " ".join(j[e]["motivos"]) for e in EPISODIOS)


def test_d1_mapear_medida_incoherente_no_es_cero():
    sys.path.insert(0, str(HERR_V2))
    import calidad_fuentes_eve as c
    iso = lambda t: str(t)
    base = {"paquetes": 10, "acotado_por": [1.0, 2.0], "motivos": [], "muestras": 3}
    assert c.mapear_medida({**base, "estado": "cero_explicito", "descartes": 0}, iso)["medido"] is True
    assert c.mapear_medida({**base, "estado": "cero_explicito", "descartes": None}, iso)["medido"] is False
    assert c.mapear_medida({**base, "estado": "cero_explicito", "descartes": 5}, iso)["medido"] is False
    assert c.mapear_medida({**base, "estado": "descartes", "descartes": 0}, iso)["medido"] is False
    assert c.mapear_medida({**base, "estado": "descartes", "descartes": 7}, iso)["kernel_drops"] == 7
    assert c.mapear_medida({"estado": "cero_explicito", "descartes": 0, "paquetes": None, "acotado_por": [1, 2]}, iso)["medido"] is False
    for est in ("ausente", "desactualizada", "error_lectura", "cobertura_insuficiente"):
        m = c.mapear_medida({**base, "estado": est, "descartes": 0}, iso)
        assert m["medido"] is False and "kernel_drops" not in m


# ------------------------------------------------------------------------------------------------ D2: descartes de tcpdump
EPOCH_ARRANQUE = dt.datetime(2026, 11, 1, 3, 0, 0, tzinfo=dt.timezone.utc).timestamp()


def servicios_txt(pid=777, enter="Sun 2026-11-01 03:00:00 UTC", nr=0, con_unidad=True, id_="ppi-motor-capture.service") -> str:
    bloques = ["MainPID=100\nNRestarts=0\nId=ppi-motor.service\nActiveState=active\nActiveEnterTimestamp=Sun 2026-11-01 03:00:00 UTC\n"]
    if con_unidad:
        bloques.append(f"MainPID={pid}\nNRestarts={nr}\nId={id_}\nActiveState=active\nActiveEnterTimestamp={enter}\n")
    return "\n".join(bloques)


def correr_descartes(tmp: Path, log: str | None, ini: str | None = None, fin: str | None = None):
    if log is not None:
        (tmp / "tcpdump.log").write_text(log)
    (tmp / "ini.txt").write_text(ini if ini is not None else servicios_txt())
    (tmp / "fin.txt").write_text(fin if fin is not None else servicios_txt())
    r = subprocess.run([sys.executable, "-I", str(HERR_V2 / "descartes_tcpdump_sigusr1.py"), "--salud-captura", str(SC), "--log", str(tmp / "tcpdump.log"),
                        "--servicios-inicio", str(tmp / "ini.txt"), "--servicios-fin", str(tmp / "fin.txt"), "--salida", str(tmp / "d.json")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads((tmp / "d.json").read_text()), r.stdout


def log_ok(descartes=0, pid=777, t0=None, t1=None):
    return ds.tcpdump_log(t0 or g.INI - 60, t1 or g.FIN + 60, pid=pid, descartes=descartes)


def test_d2_lecturas_sanas_demuestran_cero_del_proceso(tmp_path):
    d, out = correr_descartes(tmp_path, log_ok())
    assert d["dropped_by_kernel"] == 0 and d["pid"] == 777 and d["proceso_desde"] == EPOCH_ARRANQUE
    assert d["momento"] >= g.FIN and d["lecturas"] > 100 and d["motivos_no_medido"] == [] and "0 acumulados" in out
    assert any("mismo MainPID" in v for v in d["validaciones"])


def test_d2_descartes_positivos_se_informan_no_se_ocultan(tmp_path):
    d, _ = correr_descartes(tmp_path, log_ok(descartes=12))
    assert d["dropped_by_kernel"] == 12 and d["maximo_dropped"] == 12


@pytest.mark.parametrize("caso", ["log_vacio", "log_ausente", "sin_lecturas", "dos_pids", "pid_distinto_del_servicio", "servicio_reiniciado",
                                  "linea_malformada", "contador_decrece", "hora_no_utc", "unidad_ausente", "nrestarts_distinto", "sin_servicios"])
def test_d2_medicion_no_demostrable_es_null_nunca_cero(tmp_path, caso):
    log, ini, fin = log_ok(), None, None
    if caso == "log_vacio":
        log = ""
    elif caso == "log_ausente":
        log = None
    elif caso == "sin_lecturas":
        log = "2026-11-01T07:20:00.000000+0000 sensor1 systemd[1]: ppi-motor-capture.service: Sent signal SIGUSR1\n"
    elif caso == "dos_pids":
        log = log_ok(t0=g.INI - 60, t1=g.utc(7, 40), pid=777) + log_ok(t0=g.utc(7, 40, 30), t1=g.FIN + 60, pid=778)
    elif caso == "pid_distinto_del_servicio":
        log = log_ok(pid=999)
    elif caso == "servicio_reiniciado":
        fin = servicios_txt(enter="Sun 2026-11-01 07:40:00 UTC")
    elif caso == "linea_malformada":
        log = log_ok() + "2026-11-01T08:17:30.000000+0000 sensor1 tcpdump[777]: 99999 packets captured, 99999 packets received by filter\n"
    elif caso == "contador_decrece":
        log = log_ok() + "2026-11-01T08:18:30.000000+0000 sensor1 tcpdump[777]: 5 packets captured, 5 packets received by filter, 0 packets dropped by kernel\n"
    elif caso == "hora_no_utc":
        ini = fin = servicios_txt(enter="Sun 2026-11-01 03:00:00 PET")
    elif caso == "unidad_ausente":
        ini = servicios_txt(con_unidad=False)
    elif caso == "nrestarts_distinto":
        fin = servicios_txt(nr=1)
    elif caso == "sin_servicios":
        ini = fin = ""
    d, out = correr_descartes(tmp_path, log, ini, fin)
    assert d["dropped_by_kernel"] is None, (caso, d)
    assert d["motivos_no_medido"] and "NO MEDIDO" in out and "0 acumulados" not in out


def test_d2_el_json_de_salida_tiene_el_formato_que_consume_generar_respaldos(tmp_path):
    d, _ = correr_descartes(tmp_path, log_ok())
    for k in ("pid", "proceso_desde", "momento", "packets_captured", "packets_received_by_filter", "dropped_by_kernel", "alcance"):
        assert k in d
    fuente = (SCRIPTS / "generar_respaldos.py").read_text(encoding="utf-8")
    assert 'desc.get("dropped_by_kernel") is not None' in fuente and 'desc.get("proceso_desde", 1e18) <= per["inicio"]' in fuente
    assert 'desc.get("momento", 0) >= per["fin"]' in fuente and "paquetes_descartados\": descartados" in fuente
    # contrato: con null el consumidor deja descartados = None (rama sin medición), con 0 verificado deja 0
    assert 'descartados, alcance = None, "no medido' in fuente


# ------------------------------------------------------------------------------------------------ s50 v2: texto y recorrido
def test_s50_v2_sintaxis_y_hashes_de_las_herramientas_nuevas():
    assert subprocess.run(["bash", "-n", str(S50_V2)], capture_output=True).returncode == 0
    t = S50_V2.read_text(encoding="utf-8")
    assert f"CFE_SHA={sha(HERR_V2 / 'calidad_fuentes_eve.py')}" in t and f"DTS_SHA={sha(HERR_V2 / 'descartes_tcpdump_sigusr1.py')}" in t
    assert sha(S50_BASE) == "7477f4c5ae651a4c08c1c1e8448ebf3e48cfb144341acb235f805dc756a935d5"


def test_s50_v2_solo_cambia_lo_acordado_frente_al_s50_de_la_4c():
    a, b = S50_BASE.read_text(encoding="utf-8").splitlines(), S50_V2.read_text(encoding="utf-8").splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    codigo = [l for l in cambios if not l[1:].lstrip().startswith("#")]
    quitadas = [l[1:] for l in codigo if l[0] == "-"]
    esperadas = ["B=$HOME/cf-e4/$FASE; H=", "sha256sum \"$H\"/*.py", "p_2() { python3 calidad_fuentes.py",
                 "          --servicios-fin \"$C/servicios-fin.txt\" --suricata-stats", "  REQ+=(1 2 3 4 5 6 7 8 9)", "  paso 5 \"3 4\" "]
    assert len(quitadas) == len(esperadas), quitadas
    for q, e in zip(quitadas, esperadas):
        assert q.startswith(e) or e in q, (q, e)
    anadidas = "\n".join(l[1:] for l in codigo if l[0] == "+")
    for pieza in ("ANALISIS_NOMBRE", "calidad_fuentes_eve.py", "descartes_tcpdump_sigusr1.py", "--descartes-tcpdump \"$A/descartes-tcpdump.json\"",
                  "REQ+=(1 2 3 d 4 5 6 7 8 9)", "paso 5 \"3 4 d\"", "paso d \"\""):
        assert pieza in anadidas, pieza
    assert "capture.kernel_drops" not in "".join(l for l in b if not l.lstrip().startswith("#") and "stats.log" in l and "p_3" in l)


def armar_home(tmp: Path, escenario: str = "eventos", servicios_fin: str | None = None, descartes_log: str | None = None) -> Path:
    h = tmp / "home"
    for d in ("cyberflow/.venv/bin", "cf-e4/herramientas", "cf-e4/herramientas-4c-v2", "cyberflow-e4/ec78ca5/scripts/etapa4", "cyberflow-e4/herramientas-20261106",
              "cf-e4/4c/salud", "cf-e4/4c/copias/feed-v2", "cf-e4/4c/replay", "cf-e4/4c/eve", "cf-e4/4c/estado-inicial", "cf-e4/4c/archivo-pcap"):
        (h / d).mkdir(parents=True, exist_ok=True)
    (h / "cyberflow/.venv/bin/python").symlink_to(Path(sys.executable))
    H, B = h / "cf-e4/herramientas", h / "cf-e4/4c"
    for n in ("analizar.py", "calidad_fuentes.py", "poblacion.py"):
        shutil.copy2(SCRIPTS / n, H / n)
    falsa = ("import json, os, sys\nn = os.path.basename(sys.argv[0]); a = sys.argv[1:]\nv = lambda k: a[a.index(k) + 1] if k in a else None\n"
             "if n == 'analizar_3b.py':\n    os.makedirs(v('--salida'), exist_ok=True); open(os.path.join(v('--salida'), 'analisis-3b.json'), 'w').write('{}\\n')\n"
             "else:\n    for k in ('--salida', '--salida-csv', '--salida-json'):\n        if v(k): open(v(k), 'w').write('{}\\n')\n"
             "    if v('--salida-dir'):\n        os.makedirs(v('--salida-dir'), exist_ok=True); open(os.path.join(v('--salida-dir'), 'descriptor-integridad.json'), 'w').write('{}\\n')\n"
             "        json.dump(sys.argv, open(os.path.join(v('--salida-dir'), 'argv.json'), 'w'))\nprint(n, 'ok')\n")
    for n in ("control_4b.py", "extraer_evidencia_destino.py", "recalcular_caracteristicas.py", "generar_respaldos.py", "verificar_integridad.py",
              "analizar_3b.py", "referencia_trafico_4c.py"):
        (H / n).write_text(falsa)
    (H / "config-campana-4c.json").write_text("{}\n"); (H / "escenarios-4c.json").write_text("{}\n")
    (H / "herramientas-e4.sha256").write_text("".join(f"{sha(p)}  {p.name}\n" for p in sorted(H.glob("*.py")) + sorted(H.glob("*.json"))))
    for n in ("calidad_fuentes_eve.py", "descartes_tcpdump_sigusr1.py"):
        shutil.copy2(HERR_V2 / n, h / "cf-e4/herramientas-4c-v2" / n)
    e4 = h / "cyberflow-e4/ec78ca5"
    (e4 / "scripts/etapa4/trafico_observado.py").write_text("import sys\na = sys.argv[1:]\nopen(a[a.index('--salida') + 1], 'w').write('{}\\n')\n")
    (e4 / "SHA256SUMS").write_text(f"{sha(e4 / 'scripts/etapa4/trafico_observado.py')}  scripts/etapa4/trafico_observado.py\n")
    p1 = h / "cyberflow-e4/herramientas-20261106"
    shutil.copy2(SC, p1 / "salud_captura.py"); (p1 / "SHA256SUMS").write_text(f"{sha(p1 / 'salud_captura.py')}  salud_captura.py\n")
    ev = dict(g.EVENTOS) if escenario == "eventos" else {}
    c = B / "copias"
    (B / "salud/muestras.jsonl").write_text(g.muestras(g.INI, g.FIN))
    (B / "salud/tcpdump-anillo.log").write_text(descartes_log if descartes_log is not None else ds.tcpdump_log(g.INI - 60, g.FIN + 60, pid=777))
    (B / "salud/tcpdump-via.log").write_text(ds.tcpdump_log(g.INI - 60, g.FIN + 60, pid=888))
    (c / "eve-segmento.json").write_bytes(ds.eve_stats(g.INI - 60, g.FIN + 60, arranque=g.INI - 86400, **ev))
    (c / "marcas.jsonl").write_text(marcas_texto()); (c / "motor_decision.log").write_text(""); (c / "ciclos.jsonl").write_text("")
    (c / "archivar.log").write_text(archivar_log(g.utc(7, 15), g.utc(8, 20))); (c / "muestras.jsonl").write_text("")
    (c / "relojes-4c.log").write_text(""); (c / "feed-v2/senales-rapidas.jsonl").write_text(""); (c / "feed-v2/traza.jsonl").write_text("")
    (c / "servicios-fin.txt").write_text(servicios_fin if servicios_fin is not None else servicios_txt())
    (B / "estado-inicial/servicios.txt").write_text(servicios_txt()); (B / "estado-inicial/arranque-motor.t").write_text("1\n")
    (B / "eve/inicio.json").write_text(json.dumps({"t": g.INI, "inode": 1, "size": 0}))
    return h


def s50(h: Path, nombre: str | None = None, script: Path = S50_V2):
    env = dict(os.environ, HOME=str(h))
    if nombre:
        env["ANALISIS_NOMBRE"] = nombre
    return subprocess.run(["bash", str(script), "4c", "2026-11-01T07:24:40Z", "2026-11-01T10:05:30Z", "2026-11-01T07:29:00Z", "2026-11-01T08:05:00Z"],
                          capture_output=True, text=True, env=env, timeout=300)


def estado(h: Path, paso: str, carpeta="analisis") -> str:
    ee = [l.split("\t") for l in (h / f"cf-e4/4c/{carpeta}/ESTADO-PASOS.tsv").read_text().splitlines()[1:]]
    return [e[1] for e in ee if e[0] == paso][-1]


def test_s50_v2_recorrido_completo_cableado_de_d1_y_d2(tmp_path):
    h = armar_home(tmp_path)
    r = s50(h)
    A = h / "cf-e4/4c/analisis"
    assert r.returncode == 0 and (A / "SHA256SUMS").read_text().startswith("# COMPLETO"), r.stdout[-800:] + r.stderr[-400:]
    assert all(estado(h, p) == "ok" for p in ("a1", "a2", "a3", "b", "1", "2", "3", "d", "4", "5", "6", "7", "8", "c", "9"))
    cal = json.loads((A / "calidad-fuentes.json").read_text())
    assert cal["fuentes"]["suricata"] == "eve_stats"
    assert [cal["episodios"][e]["estado"] for e in EPISODIOS] == ["completa", "degradada", "insuficiente"]
    d = json.loads((A / "descartes-tcpdump.json").read_text())
    assert d["dropped_by_kernel"] == 0 and d["pid"] == 777
    argv = json.loads((A / "respaldos/argv.json").read_text())
    assert argv[argv.index("--descartes-tcpdump") + 1] == str(A / "descartes-tcpdump.json")
    ee = [l.split("\t") for l in (A / "ESTADO-PASOS.tsv").read_text().splitlines()[1:]]
    orden = [e[0] for e in ee]
    assert orden.index("d") < orden.index("5") and [e for e in ee if e[0] == "5"][0][5] == "3 4 d"


def test_s50_v2_servicio_reiniciado_deja_descartes_null_y_el_paso_5_lo_recibe(tmp_path):
    h = armar_home(tmp_path, servicios_fin=servicios_txt(enter="Sun 2026-11-01 07:40:00 UTC"))
    r = s50(h)
    A = h / "cf-e4/4c/analisis"
    assert r.returncode == 0, r.stdout[-600:]
    d = json.loads((A / "descartes-tcpdump.json").read_text())
    assert d["dropped_by_kernel"] is None and "NO MEDIDO" in r.stdout
    assert "--descartes-tcpdump" in json.loads((A / "respaldos/argv.json").read_text())


def test_s50_v2_carpeta_nueva_no_toca_la_v1(tmp_path):
    h = armar_home(tmp_path)
    v1 = h / "cf-e4/4c/analisis"; v1.mkdir()
    (v1 / "caracteristicas.jsonl").write_text("resultado v1\n"); (v1 / "SHA256SUMS").write_text("# COMPLETO v1\n")
    antes = {p.name: sha(p) for p in v1.iterdir()}
    r = s50(h, nombre="analisis-v2")
    assert r.returncode == 0, r.stdout[-600:]
    assert {p.name: sha(p) for p in v1.iterdir()} == antes and (h / "cf-e4/4c/analisis-v2/SHA256SUMS").read_text().startswith("# COMPLETO")
    # sin ANALISIS_NOMBRE y con la v1 presente, el guion se niega (no sobrescribe)
    r2 = s50(h)
    assert r2.returncode == 2 and "PARAR: existe" in r2.stdout
    # nombre no válido
    assert s50(h, nombre="../x").returncode == 2


def test_s50_v2_herramienta_nueva_alterada_para_antes_de_empezar(tmp_path):
    h = armar_home(tmp_path)
    f = h / "cf-e4/herramientas-4c-v2/descartes_tcpdump_sigusr1.py"
    f.write_text(f.read_text() + "\n# alterado\n")
    r = s50(h)
    assert r.returncode == 2 and "descartes_tcpdump_sigusr1.py ausente o con hash distinto" in r.stdout
    assert not (h / "cf-e4/4c/analisis/ESTADO-PASOS.tsv").exists()
