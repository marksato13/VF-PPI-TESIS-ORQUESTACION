import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas"))
import orquestar_b as o  # noqa: E402
import test_d5 as t  # noqa: E402


def plan(n=3, cmd=("true",)):
    return {"origen": t.K, "episodios": [{"id": "e%d" % i, "comando": list(cmd)} for i in range(n)]}


def leer(p):
    return [json.loads(l) for l in open(p).read().splitlines()]


def test_completa_escribe_marcas_y_rc0(tmp_path):
    m = t.Mundo(tmp_path / "m") if (tmp_path / "m").mkdir() is None else None
    fase = tmp_path / "4c"
    rc, hechos = o.orquestar(plan(), t.Runners(m), str(fase), True, str(tmp_path / "puertas.jsonl"),
                             ahora=lambda: m.t, dormir=m.tick)
    assert rc == 0 and hechos == ["e0", "e1", "e2"]
    assert (fase / "replay" / "rc.txt").read_text().startswith("rc=0 ")
    ev = [(x["evento"], x["episodio_id"]) for x in leer(fase / "marcas-B.jsonl")]
    assert ev == [(e, "e%d" % i) for i in range(3) for e in ("puerta", "inicio", "fin")]
    assert len(leer(tmp_path / "puertas.jsonl")) == 3


def test_puerta_que_no_pasa_detiene_la_campana_sin_iniciar(tmp_path):
    (tmp_path / "m").mkdir()
    m = t.Mundo(tmp_path / "m", ignora_limpieza=True)
    marca = tmp_path / "ejecutado"
    fase = tmp_path / "4c"
    rc, hechos = o.orquestar(plan(2, ("touch", str(marca))), t.Runners(m), str(fase), True, str(tmp_path / "p.jsonl"),
                             ahora=lambda: m.t, dormir=m.tick, puerta_kw={"espera_feed": 3})
    assert rc == 3 and hechos == [] and not marca.exists()
    assert (fase / "replay" / "rc.txt").read_text().startswith("rc=3 ")
    assert not any(x["evento"] == "inicio" for x in leer(fase / "marcas-B.jsonl"))


def test_comando_fallido_detiene_con_rc4(tmp_path):
    (tmp_path / "m").mkdir()
    m = t.Mundo(tmp_path / "m")
    rc, hechos = o.orquestar(plan(3, ("false",)), t.Runners(m), str(tmp_path / "4c"), True, str(tmp_path / "p.jsonl"),
                             ahora=lambda: m.t, dormir=m.tick)
    assert rc == 4 and hechos == [] and (tmp_path / "4c" / "replay" / "rc.txt").read_text().startswith("rc=4 ")


def test_seco_no_ejecuta_ni_escribe(tmp_path, capsys):
    marca = tmp_path / "x"
    rc, hechos = o.orquestar(plan(2, ("touch", str(marca))), None, str(tmp_path / "4c"), False, "a")
    assert rc == 0 and len(hechos) == 2 and not marca.exists() and not (tmp_path / "4c").exists()
    assert "SECO" in capsys.readouterr().out


def test_main_real_exige_ssh(tmp_path):
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan(1)))
    assert o.main(["--plan", str(p), "--real"]) == 2
    assert o.main(["--plan", str(p), "--fase-dir", str(tmp_path / "f")]) == 0


def test_ssh_runners_arma_la_orden_y_lee_el_ultimo_json():
    vistos = []

    def run(orden, **kw):
        vistos.append(orden)
        return subprocess.CompletedProcess(orden, 0, stdout='ruido\n{"ok": true, "rc": 0, "x": 1}\n', stderr="")
    r = o.SshRunners("ssh -n s", "ssh -n v", run=run)
    assert r.sensor("limpiar", origen="1.2.3.4") == {"ok": True, "rc": 0, "x": 1}
    r.srv("agente", origen="1.2.3.4", desde=5.5)
    assert vistos[0][:2] == ["ssh", "-n"] and "sensor-limpiar --real --origen 1.2.3.4" in vistos[0][-1]
    assert "srv-agente --origen 1.2.3.4 --desde 5.5" in vistos[1][-1] and vistos[1][2] == "v"
    sin = o.SshRunners("ssh s", "ssh v", run=lambda *a, **k: subprocess.CompletedProcess(a, 255, stdout="", stderr="e"))
    assert sin.srv("nft", origen="x")["ok"] is False
