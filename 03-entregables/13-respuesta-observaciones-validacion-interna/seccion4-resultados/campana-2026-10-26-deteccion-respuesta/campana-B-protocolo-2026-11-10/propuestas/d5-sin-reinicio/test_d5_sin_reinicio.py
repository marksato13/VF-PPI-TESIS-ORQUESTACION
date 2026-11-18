"""Prueba con DATOS SINTÉTICOS de la propuesta D5 sin reinicio: el publicador derivado limpia solo el origen del experimento,
conserva lo demás y la auditoría, republica un feed sin ese origen, reinicia la escalera y NO reinicia el proceso."""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import hacer_publicador_d5 as h  # noqa: E402

K, OTRA = "10.10.20.30", "10.10.20.99"
T0 = 1_000_000.0


def motor_dir():
    for c in (Path(os.environ.get("CF_PRODUCTO", "/nonexistent")), Path("/producto-etapa3"),
              *[p / "producto-etapa3" for p in AQUI.parents]):
        if (c / "scripts" / "engine" / "publicar_feed_v2.py").exists():
            return c / "scripts" / "engine"
    pytest.skip("el producto desplegado (producto-etapa3) no está disponible en el banco")


@pytest.fixture(scope="module")
def mod(tmp_path_factory):
    eng = motor_dir()
    orig = eng / "publicar_feed_v2.py"
    assert hashlib.sha256(orig.read_bytes()).hexdigest().startswith("5733f17d39bfa5fe")      # el desplegado en el Sensor1
    d = Path(tempfile.mkdtemp(prefix="d5prop_"))
    for f in eng.glob("*.py"):
        shutil.copy(f, d / f.name)
    assert h.main(str(orig), str(d / "publicar_feed_v2_d5.py")) == 0
    sys.path.insert(0, str(d))
    out = {}
    for nombre in ("publicar_feed_v2", "publicar_feed_v2_d5"):
        spec = importlib.util.spec_from_file_location(nombre, d / (nombre + ".py"))
        m = importlib.util.module_from_spec(spec)
        sys.modules[nombre] = m
        spec.loader.exec_module(m)
        out[nombre] = m
    return out


def decision(ip, regla, accion, n, logged):
    return {"event": "decision", "entity_ip": ip, "decision_id": "d%d|%s" % (n, ip), "window_end_utc": None, "logged_at": logged,
            "decidido_en": logged, "detector_name": "if_limpio_2026_10", "score": -0.1, "decision": "PERMIT",
            "heuristicos": [{"heuristico": regla, "accion": accion, "motivo": "sintético"}]}


def preparar(tmp):
    clave = tmp / "k.pem"
    subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", str(clave)], capture_output=True)
    if not clave.exists():
        pytest.skip("sin openssl")
    log = tmp / "motor.log"
    regs = [decision(K, "brute_force", "BLOCK", 1, T0 + 1), decision(OTRA, "http_abuse", "LIMIT", 2, T0 + 1)]
    log.write_text("".join(json.dumps(r) + "\n" for r in regs))
    return clave, log


def correr(m, tmp, clave, log, extra, hook, iteraciones=6):
    if hasattr(m, "_D5_IDS"):
        m._D5_IDS.clear()                                          # el módulo se reutiliza entre pruebas; en producción es un proceso nuevo
    t = [T0]

    def dormir(s):
        t[0] += 1
        hook(len([1 for _ in range(1)]) and t[0] - T0)
    args = ["--log", str(log), "--estado", str(tmp / "estado.json"), "--clave-privada", str(clave), "--salida-feed", str(tmp / "feed.json"),
            "--salida-firma", str(tmp / "feed.sig"), "--traza", str(tmp / "traza.jsonl"), "--politica", "if_senal", "--seguir",
            "--sondeo-segundos", "0", "--max-iteraciones", str(iteraciones)] + extra
    rc = m.main(args, reloj=lambda: t[0], dormir=dormir)
    return rc, t


def feed(tmp):
    return json.loads((tmp / "feed.json").read_text())


def estado(tmp):
    return json.loads((tmp / "estado.json").read_text())


def ctl(tmp, **kw):
    c = {"accion": "reset_origen", "origen": K, "id": "puerta-1"}
    c.update(kw)
    (tmp / "control.json").write_text(json.dumps(c))


def test_el_reset_limpia_solo_a_la_kali_conserva_lo_demas_y_no_reinicia(mod, tmp_path):
    clave, log = preparar(tmp_path)
    m = mod["publicar_feed_v2_d5"]
    pid = os.getpid()
    visto = {}

    def hook(s):
        if s == 2:
            e = estado(tmp_path)                                  # antes del reset: ambos orígenes presentes
            visto["antes"] = ({k.split("|")[0] for k in e["vigentes"]}, {k.split("@")[0] for k in e["escalada"]}, dict(e["eventos"]))
            ctl(tmp_path)
    rc, _ = correr(m, tmp_path, clave, log, ["--control-d5", str(tmp_path / "control.json"), "--d5-origen", K], hook)
    assert rc == 0 and os.getpid() == pid                         # misma llamada, mismo proceso: nada se mata ni se reinicia
    assert visto["antes"][0] == {K, OTRA} and visto["antes"][1] == {K, OTRA}
    e = estado(tmp_path)
    assert {k.split("|")[0] for k in e["vigentes"]} == {OTRA} and {k.split("@")[0] for k in e["escalada"]} == {OTRA}
    assert e["eventos"] and set(visto["antes"][2]) <= set(e["eventos"])    # los eventos (auditoría/dedupe) se conservan
    assert [x["ip"] for x in feed(tmp_path)["entradas"]] == [OTRA]        # el feed ya no propone nada sobre la Kali
    ack = json.loads((tmp_path / "control.json.ack").read_text())
    assert ack["ok"] and ack["id"] == "puerta-1" and len(ack["quitado"]["vigentes"]) == 1 and len(ack["quitado"]["escalada"]) == 1
    assert not (tmp_path / "control.json").exists()                       # control consumido
    pubs = [json.loads(l) for l in (tmp_path / "traza.jsonl").read_text().splitlines()]
    assert len(pubs) == 2 and len(pubs[0]["entradas"]) == 2 and len(pubs[1]["entradas"]) == 1   # publicación inicial y la inmediata tras el reset; nada se borra


def test_tras_el_reset_la_kali_vuelve_al_nivel_1_de_la_escalera(mod, tmp_path):
    clave, log = preparar(tmp_path)
    m = mod["publicar_feed_v2_d5"]

    def hook(s):
        if s == 2:
            ctl(tmp_path)
        if s == 4:                                                    # decisión NUEVA (otra ventana) sobre la Kali, tras el reset
            with open(log, "a") as fh:
                fh.write(json.dumps(decision(K, "brute_force", "BLOCK", 9, T0 + 4)) + "\n")
    correr(m, tmp_path, clave, log, ["--control-d5", str(tmp_path / "control.json"), "--d5-origen", K], hook, iteraciones=8)
    e = [x for x in feed(tmp_path)["entradas"] if x["ip"] == K]
    assert e and e[0]["nivel"] == 1 and e[0]["hasta"] - (T0 + 4) == 300      # BLOCK nivel 1 = 300 s (sin escalera heredada)


@pytest.mark.parametrize("control, error", [({"origen": OTRA}, "origen no permitido"), ({"accion": "borrar_todo"}, "control mal formado"),
                                              ({"id": 5}, "control mal formado")])
def test_controles_no_validos_se_rechazan_sin_tocar_el_estado(mod, tmp_path, control, error):
    clave, log = preparar(tmp_path)
    m = mod["publicar_feed_v2_d5"]

    def hook(s):
        if s == 2:
            ctl(tmp_path, **control)
    correr(m, tmp_path, clave, log, ["--control-d5", str(tmp_path / "control.json"), "--d5-origen", K], hook)
    ack = json.loads((tmp_path / "control.json.ack").read_text())
    assert not ack["ok"] and ack["error"] == error
    assert {k.split("|")[0] for k in estado(tmp_path)["vigentes"]} == {K, OTRA}


def test_control_ilegible_no_rompe_el_bucle(mod, tmp_path):
    clave, log = preparar(tmp_path)
    m = mod["publicar_feed_v2_d5"]

    def hook(s):
        if s == 2:
            (tmp_path / "control.json").write_text("{no es json")
    rc, _ = correr(m, tmp_path, clave, log, ["--control-d5", str(tmp_path / "control.json"), "--d5-origen", K], hook)
    assert rc == 0 and not json.loads((tmp_path / "control.json.ack").read_text())["ok"]
    assert {k.split("|")[0] for k in estado(tmp_path)["vigentes"]} == {K, OTRA}


def test_sin_las_opciones_es_identico_al_original_y_un_control_presente_se_ignora(mod, tmp_path):
    res = {}
    for nombre in ("publicar_feed_v2", "publicar_feed_v2_d5"):
        d = tmp_path / nombre
        d.mkdir()
        clave, log = preparar(d)
        (d / "control.json").write_text(json.dumps({"accion": "reset_origen", "origen": K, "id": "x"}))     # existe pero no se pasó --control-d5
        correr(mod[nombre], d, clave, log, [], lambda s: None)
        res[nombre] = (sorted((x["ip"], x["accion"], x["detector"], x["nivel"]) for x in feed(d)["entradas"]),
                       {k.split("|")[0] for k in estado(d)["vigentes"]})
        assert (d / "control.json").exists()
    assert res["publicar_feed_v2"] == res["publicar_feed_v2_d5"]


def test_el_cambio_al_codigo_es_pequeno(mod):
    import difflib
    eng = motor_dir()
    a = (eng / "publicar_feed_v2.py").read_text().splitlines()
    b = (Path(sys.modules["publicar_feed_v2_d5"].__file__)).read_text().splitlines()
    cambios = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    assert not [l for l in cambios if l[0] == "-"] or len([l for l in cambios if l[0] == "-"]) <= 1      # solo la línea de `toca`
    assert len(cambios) < 100                                                 # v3: + auditoría independiente del acuse (consumido/publicado/ack_fallido)
