import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas"))
import compuerta_b as c  # noqa: E402
import d5_episodio as d5  # noqa: E402

K, OTRA = "10.10.20.30", "10.10.20.99"


def permiso(estado="continuar"):
    return json.dumps({"nonce": "n", "estado": estado, "causas": [], "secuencia": 1})


class FakeSsh:
    """Sustituye al ssh a la Kali: guarda el permiso instalado y devuelve epoch + marcas nuevas."""
    def __init__(self):
        self.instalado, self.marcas = None, []

    def __call__(self, orden, input=None, **kw):
        self.instalado = json.loads(input)
        salida = "1794300000.1\n" + "".join(json.dumps(m) + "\n" for m in self.marcas)
        self.marcas = []
        return subprocess.CompletedProcess(orden, 0, stdout=salida, stderr="")


def ronda(d, ssh, estado="continuar"):
    c.filtrar(str(d), ["ssh", "kali"], permiso(estado), run=ssh)
    return ssh.instalado["estado"]


def test_puerta_pendiente_convierte_continuar_en_pausa_y_explica(tmp_path):
    ssh = FakeSsh()
    assert ronda(tmp_path, ssh) == "pausa"
    assert any("D5" in x for x in ssh.instalado["causas"]) and ssh.instalado["nonce"] == "n"


def test_no_convierte_cancelar_ni_pausa_en_continuar(tmp_path):
    ssh = FakeSsh()
    assert ronda(tmp_path, ssh, "cancelar") == "cancelar" and ronda(tmp_path, ssh, "pausa") == "pausa"
    with c.Estado(str(tmp_path)) as st:
        st["pendiente"] = False
    assert ronda(tmp_path, ssh, "cancelar") == "cancelar" and ronda(tmp_path, ssh, "pausa") == "pausa"


def test_puerta_libre_deja_pasar_continuar(tmp_path):
    with c.Estado(str(tmp_path)) as st:
        st["pendiente"] = False
    assert ronda(tmp_path, FakeSsh()) == "continuar"


def test_inicio_de_episodio_cierra_la_puerta_y_fin_marca_termino(tmp_path):
    with c.Estado(str(tmp_path)) as st:
        st["pendiente"] = False
    ssh = FakeSsh()
    ssh.marcas = [{"evento": "inicio", "episodio_id": "e1"}]
    assert ronda(tmp_path, ssh) == "continuar"          # este permiso se emitió antes de ver la marca
    with c.Estado(str(tmp_path)) as st:
        assert st["pendiente"] and st["en_episodio"] and st["episodio"] == "e1" and st["n_inicios"] == 1
    assert ronda(tmp_path, ssh) == "pausa"              # desde ahora y durante todo el episodio, pausa
    ssh.marcas = [{"evento": "fin", "episodio_id": "e1"}]
    ronda(tmp_path, ssh)
    with c.Estado(str(tmp_path)) as st:
        assert not st["en_episodio"] and st["pendiente"] and st["fin_en"] is not None
    assert len(open(tmp_path / "marcas-vistas.jsonl").read().splitlines()) == 2


def test_otras_marcas_y_ssh_fallido_no_cambian_el_estado(tmp_path):
    ssh = FakeSsh()
    ssh.marcas = [{"evento": "pausa"}, {"evento": "contexto"}]
    ronda(tmp_path, ssh)
    with c.Estado(str(tmp_path)) as st:
        assert st["n_inicios"] == 0 and not st["en_episodio"]

    def malo(orden, input=None, **kw):
        return subprocess.CompletedProcess(orden, 255, stdout="x\n" + json.dumps({"evento": "inicio"}) + "\n", stderr="e")
    rc, _o, _e = c.filtrar(str(tmp_path), ["ssh"], permiso(), run=malo)
    assert rc == 255
    with c.Estado(str(tmp_path)) as st:
        assert st["n_inicios"] == 0


def test_por_episodio_el_permiso_nombra_al_siguiente_episodio(tmp_path):
    ssh = FakeSsh()
    ssh.marcas = [{"evento": "campana_inicio", "orden": ["a-r1", "b-r1", "c-r1"]}]
    with c.Estado(str(tmp_path)) as st:
        st["pendiente"] = False
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, por_episodio=True)
    assert ssh.instalado["estado"] == "pausa" and "orden" in " ".join(ssh.instalado["causas"])   # aún no conocía el orden
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, por_episodio=True)
    assert ssh.instalado["estado"] == "continuar" and ssh.instalado["episodio"] == "a-r1"
    ssh.marcas = [{"evento": "inicio", "episodio_id": "a-r1"}]
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, por_episodio=True)
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, por_episodio=True)
    assert ssh.instalado["estado"] == "pausa" and "episodio" not in ssh.instalado
    ssh.marcas = [{"evento": "fin", "episodio_id": "a-r1"}]
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, por_episodio=True)
    assert c.paso_puerta(str(tmp_path), lambda: {"lista": True}, dormir=lambda s: None) == "liberada"
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, por_episodio=True)
    assert ssh.instalado["estado"] == "continuar" and ssh.instalado["episodio"] == "b-r1"      # no a-r1: ya se lanzó


def test_por_episodio_sin_episodios_restantes_pausa(tmp_path):
    ssh = FakeSsh()
    with c.Estado(str(tmp_path)) as st:
        st.update(pendiente=False, orden=["a"], n_inicios=1)
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, por_episodio=True)
    assert ssh.instalado["estado"] == "pausa"


def test_el_filtro_sella_el_instante_de_decision(tmp_path):
    ssh = FakeSsh()
    c.filtrar(str(tmp_path), ["ssh"], permiso(), run=ssh, ahora=lambda: 77.0)
    assert ssh.instalado["compuerta_b"]["decidido_en"] == 77.0


def test_cli_como_ssh_kali_del_vigia(tmp_path):
    """Tal como lo invoca el vigía: shlex.split(--ssh-kali) + [orden]; el permiso por stdin; la salida se reenvía."""
    falso = tmp_path / "ssh_falso.py"
    falso.write_text("import sys\nsys.stdout.write('123.4\\n{\"evento\": \"inicio\", \"episodio_id\": \"e9\"}\\n')\n"
                     "open(sys.argv[0] + '.recibido', 'w').write(sys.stdin.read() + '|' + ' '.join(sys.argv[1:]))\n")
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "..", "herramientas", "compuerta_b.py"), "filtro",
           "--dir", str(tmp_path / "g"), "--", sys.executable, str(falso), "kali", "umask 077; tail -n +{N} x"]
    r = subprocess.run(cmd, input=permiso(), capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.splitlines()[0] == "123.4"
    recibido = open(str(falso) + ".recibido").read()
    assert '"estado": "pausa"' in recibido and recibido.endswith("|kali umask 077; tail -n +{N} x")
    with c.Estado(str(tmp_path / "g")) as st:
        assert st["en_episodio"] and st["episodio"] == "e9"


# ------------------------------------------------------------------ proceso de puerta
def test_no_corre_la_puerta_en_episodio_ni_sin_pendiente(tmp_path):
    llamadas = []
    fn = lambda: llamadas.append(1) or {"lista": True}
    with c.Estado(str(tmp_path)) as st:
        st["en_episodio"] = True
    assert c.paso_puerta(str(tmp_path), fn) == "nada"
    with c.Estado(str(tmp_path)) as st:
        st.update(en_episodio=False, pendiente=False)
    assert c.paso_puerta(str(tmp_path), fn) == "nada" and not llamadas


def test_puerta_lista_libera_y_el_siguiente_permiso_es_continuar(tmp_path):
    ssh = FakeSsh()
    assert ronda(tmp_path, ssh) == "pausa"
    assert c.paso_puerta(str(tmp_path), lambda: {"lista": True}) == "liberada"
    assert ronda(tmp_path, ssh) == "continuar"


def test_puerta_fallida_mantiene_la_pausa(tmp_path):
    ssh = FakeSsh()
    assert c.paso_puerta(str(tmp_path), lambda: {"lista": False}) == "fallida"
    assert ronda(tmp_path, ssh) == "pausa"


def test_si_empieza_otro_episodio_mientras_corre_la_puerta_no_se_libera(tmp_path):
    def fn():
        with c.Estado(str(tmp_path)) as st:
            st.update(en_episodio=True, n_inicios=st["n_inicios"] + 1)
        return {"lista": True}
    assert c.paso_puerta(str(tmp_path), fn) == "interrumpida"
    with c.Estado(str(tmp_path)) as st:
        assert st["pendiente"]


def test_espera_tras_el_fin_antes_de_la_puerta(tmp_path):
    t = {"v": 1000.0}
    dormidos = []
    with c.Estado(str(tmp_path)) as st:
        st["fin_en"] = 1000.0
    c.paso_puerta(str(tmp_path), lambda: {"lista": True}, ahora=lambda: t["v"], dormir=dormidos.append, espera_fin=15.0)
    assert dormidos == [15.0]


def test_ciclo_completo_dos_episodios(tmp_path):
    """Permiso en pausa hasta la puerta; en episodio, pausa; tras el fin, puerta; el segundo episodio solo con puerta nueva."""
    ssh, vistos = FakeSsh(), []
    vistos.append(ronda(tmp_path, ssh))                      # antes del episodio 1: pausa (puerta inicial)
    assert c.paso_puerta(str(tmp_path), lambda: {"lista": True}, dormir=lambda s: None) == "liberada"
    vistos.append(ronda(tmp_path, ssh))                      # continuar
    ssh.marcas = [{"evento": "inicio", "episodio_id": "e1"}]
    ronda(tmp_path, ssh)
    vistos.append(ronda(tmp_path, ssh))                      # episodio en curso: pausa
    assert c.paso_puerta(str(tmp_path), lambda: {"lista": True}) == "nada"
    ssh.marcas = [{"evento": "fin", "episodio_id": "e1"}]
    vistos.append(ronda(tmp_path, ssh))                      # terminó: pausa hasta la puerta
    assert c.paso_puerta(str(tmp_path), lambda: {"lista": False}, dormir=lambda s: None) == "fallida"
    vistos.append(ronda(tmp_path, ssh))                      # puerta fallida: el episodio 2 espera
    assert c.paso_puerta(str(tmp_path), lambda: {"lista": True}, dormir=lambda s: None) == "liberada"
    vistos.append(ronda(tmp_path, ssh))
    assert vistos == ["pausa", "continuar", "pausa", "pausa", "pausa", "continuar"]


# ------------------------------------------------------------------ srv-estado (X2 -> P1)
def helper_con(sets):
    return lambda p: {"ok": True, "estado": {"sets": sets, "descartes_limite": {}}}


def test_srv_estado_solo_la_kali_o_nada_es_rc0():
    assert d5.srv_estado(K, helper_con({"bloqueados": {K: {"id": "a"}}, "limitados": {}}), ahora=lambda: 5.0)["rc"] == 0
    assert d5.srv_estado(K, helper_con({"bloqueados": {}, "limitados": {}}))["rc"] == 0
    assert d5.srv_estado(K, helper_con({"bloqueados": None, "limitados": None}))["rc"] == 0   # sin tabla


def test_srv_estado_otra_ip_es_rc1_p1():
    r = d5.srv_estado(K, helper_con({"bloqueados": {K: {}}, "limitados": {OTRA: {"id": "x"}}}))
    assert r["rc"] == 1 and r["ajenas"] == [OTRA] and "P1" in r["resumen"]


def test_srv_estado_lectura_fallida_es_rc2():
    r = d5.srv_estado(K, lambda p: {"ok": False, "rechazo": "x"})
    assert r["rc"] == 2 and not r["ok"]


def test_srv_estado_cli_imprime_epoch_primero(monkeypatch, capsys):
    monkeypatch.setattr(d5, "_helper", lambda p, **k: {"ok": True, "estado": {"sets": {"bloqueados": {OTRA: {}}}}})
    monkeypatch.setattr(d5, "srv_estado", lambda o, helper=None, ahora=None: {"ok": True, "rc": 1, "t": 12.5, "resumen": "P1 x"})
    assert d5.main(["srv-estado"]) == 1
    assert capsys.readouterr().out.splitlines() == ["12.500000", "P1 x"]
