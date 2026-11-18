"""α = 0,01 en el motor: manifiesto derivado, comprobación en sombra y el hecho de que una alerta del IF sola no restringe (código real)."""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

H = Path(__file__).resolve().parent.parent / "herramientas"
sys.path.insert(0, str(H))
import crear_manifiesto_alfa as cm  # noqa: E402
import verificar_umbral_motor as vm  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
NUEVO, ANTES = -0.6223889502095352, -0.5693969936322356


def manifiesto(thr=ANTES, alpha=0.05):
    return json.dumps({"tipo": "x", "detectors": {"if_limpio_2026_10": {"calibration": {
        "threshold": thr, "alpha": alpha, "comparison": "score < threshold", "n": 5}}},
        "evaluation": {"if_limpio_2026_10": {"threshold_used": thr}}}).encode()


def test_manifiesto_nuevo_cambia_solo_threshold_y_alpha():
    ob = manifiesto()
    nb = cm.crear(ob)
    o, n = json.loads(ob), json.loads(nb)
    c = n["detectors"]["if_limpio_2026_10"]["calibration"]
    assert c["threshold"] == NUEVO and c["alpha"] == 0.01 and c["comparison"] == "score < threshold" and c["n"] == 5
    assert c["_alfa_B"]["sha256_manifiesto_original"] == hashlib.sha256(ob).hexdigest()
    assert n["evaluation"] == o["evaluation"]                              # el registro de evaluación original no se reescribe
    del c["threshold"], c["alpha"], c["_alfa_B"]
    o["detectors"]["if_limpio_2026_10"]["calibration"].pop("threshold"), o["detectors"]["if_limpio_2026_10"]["calibration"].pop("alpha")
    assert n == o


def test_se_niega_si_el_original_no_es_el_esperado():
    with pytest.raises(ValueError):
        cm.crear(manifiesto(thr=-0.1))
    with pytest.raises(ValueError):
        cm.crear(manifiesto(alpha=0.03))
    with pytest.raises(ValueError):
        cm.crear(manifiesto().replace(b"score < threshold", b"score > threshold"))


def test_el_motor_real_carga_ese_umbral(tmp_path):
    spec = importlib.util.spec_from_file_location("motor", RAIZ.parent.parent.parent.parent.parent.parent.parent / "producto-etapa3" / "scripts" / "engine" / "motor_decision.py")
    ruta = Path(spec.origin)
    if not ruta.exists():
        pytest.skip("el motor del producto no está en el banco")
    src = ruta.read_text(encoding="utf-8")
    ns = {}
    # solo la función de carga, tal como está en el motor desplegado
    inicio = src.index("def load_threshold")
    exec("import json\nfrom pathlib import Path\n" + src[inicio:src.index("\n\n\n", inicio)], ns)
    (tmp_path / "m.json").write_bytes(cm.crear(manifiesto()))
    assert ns["load_threshold"](tmp_path / "m.json", "if_limpio_2026_10") == NUEVO


def decision(score, thr, t=100.0):
    return {"event": "decision", "score": score, "threshold": thr, "decision": "ALERT" if score < thr else "PERMIT",
            "decision_if": "ALERT" if score < thr else "PERMIT", "logged_at": t}


def regs(thr=NUEVO, n=30, extras=()):
    arr = [{"event": "motor_startup", "timestamp": 90.0, "threshold": thr, "manifest_path": "/m/nuevo.json"}]
    arr += [decision(-0.60 - 0.001 * i if i % 3 else -0.70, thr, 100.0 + i) for i in range(n)]
    return arr + list(extras)


def test_verificacion_conforme_y_cuanto_mueve_el_IF():
    r = vm.verificar(regs(), NUEVO, "/m/nuevo.json", 20, cmdline="x --manifest-path /m/nuevo.json --disparo eventos")
    assert r["ok"], r["fallos"]
    puntajes = [x["score"] for x in regs() if x["event"] == "decision"]
    assert r["alertas_con_umbral_nuevo"] == sum(s < NUEVO for s in puntajes) == 15
    assert r["alertas_que_habria_con_el_anterior"] == 30 > r["alertas_con_umbral_nuevo"]


@pytest.mark.parametrize("caso", ["sin_arranque", "umbral_viejo_en_arranque", "decision_con_umbral_viejo", "incoherente", "pocas", "otro_manifiesto", "enforce"])
def test_cada_incumplimiento_se_detecta(caso):
    r, man, cmd, n = regs(), "/m/nuevo.json", "x --manifest-path /m/nuevo.json", 20
    if caso == "sin_arranque":
        r = r[1:]
    elif caso == "umbral_viejo_en_arranque":
        r = regs(thr=ANTES)
    elif caso == "decision_con_umbral_viejo":
        r.append(decision(-0.9, ANTES, 200.0))
    elif caso == "incoherente":
        r.append({**decision(-0.60, NUEVO, 200.0), "decision_if": "ALERT"})       # -0,60 no es < -0,6224
    elif caso == "pocas":
        r = regs(n=5)
    elif caso == "otro_manifiesto":
        man = "/m/otro.json"
    else:
        cmd += " --enforce"
    res = vm.verificar(r, NUEVO, man, n, cmdline=cmd)
    assert not res["ok"] and res["fallos"]


def test_cli_lee_el_log_desde_el_reinicio(tmp_path):
    log = tmp_path / "motor.log"
    antes = [decision(-0.9, ANTES, 10.0), {"event": "motor_startup", "timestamp": 20.0, "threshold": ANTES, "manifest_path": "/m/viejo.json"}]
    log.write_text("".join(json.dumps(x) + "\n" for x in antes + regs()))
    assert vm.main(["--log", str(log), "--umbral", str(NUEVO), "--manifiesto", "/m/nuevo.json", "--desde", "80"]) == 0
    assert vm.main(["--log", str(log), "--umbral", str(NUEVO), "--desde", "5"]) == 0          # solo cuenta desde el ÚLTIMO arranque
    log.write_text("".join(json.dumps(x) + "\n" for x in regs() + antes))                      # el último arranque es el del umbral viejo
    assert vm.main(["--log", str(log), "--umbral", str(NUEVO), "--desde", "5"]) == 1
    assert vm.main(["--log", str(tmp_path / "no_existe"), "--umbral", "0", "--desde", "0"]) == 2


# ---- bajo if_senal, una alerta del IF por sí sola no activa LIMIT ni BLOCK (publicador desplegado, hash 5733f17d)
def publicador():
    ruta = RAIZ.parent.parent.parent.parent.parent.parent.parent / "producto-etapa3" / "scripts" / "engine" / "publicar_feed_v2.py"
    if not ruta.exists():
        pytest.skip("publicador del producto no disponible")
    assert hashlib.sha256(ruta.read_bytes()).hexdigest().startswith("5733f17d39bfa5fe")      # el desplegado en el Sensor1
    sys.path.insert(0, str(ruta.parent.parent.parent))
    spec = importlib.util.spec_from_file_location("pub", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def d_if(score, **kw):
    d = {"event": "decision", "entity_ip": "10.10.20.30", "decision_id": "d|%s" % score, "window_end_utc": "2026-11-10T10:00:00Z",
         "logged_at": 1000.0, "decidido_en": 1000.0, "detector_name": "if_limpio_2026_10", "score": score, "decision": "ALERT",
         "decision_if": "ALERT", "heuristico": None, "heuristicos": []}
    d.update(kw)
    return d


@pytest.mark.parametrize("score", [-0.6224, -0.70, -0.99, -5.0])
def test_alerta_del_IF_sola_no_restringe_con_if_senal(score):
    p = publicador()
    assert p.acciones_de(d_if(score), "if_senal") == []
    estado = {}
    nuevos = p.incorporar([d_if(score)], estado, p.NUNCA_BLOQUEAR_V2, "if_senal", 1000.0)
    assert nuevos == [] and estado.get("vigentes", {}) == {} and p.entradas_vigentes(estado, 1001.0) == []
    obj = p.publicar(estado, 1001.0, 60.0, *_claves(p, estado))
    assert obj["entradas"] == []


def _claves(p, estado):
    import tempfile
    d = Path(tempfile.mkdtemp())
    clave = d / "k.pem"
    os.system("openssl genpkey -algorithm ed25519 -out %s 2>/dev/null" % clave)
    if not clave.exists():
        pytest.skip("sin openssl")
    return clave, d / "feed.json", d / "feed.sig"


def test_el_contraste_la_politica_actual_si_restringe_y_los_heuristicos_si():
    p = publicador()
    assert [a["accion"] for a in p.acciones_de(d_if(-0.7), "actual")] == ["LIMIT"]        # lo que NO es B: sensibilidad de la prueba
    h = d_if(-0.7, heuristicos=[{"heuristico": "port_scan", "accion": "BLOCK", "motivo": "x"}])
    assert [a["accion"] for a in p.acciones_de(h, "if_senal")] == ["BLOCK"]               # las restricciones salen de los heurísticos
