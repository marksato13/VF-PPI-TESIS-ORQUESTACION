"""Pruebas de los guiones de reversión y activación de B con órdenes simuladas (sin tocar ningún sistema)."""
import os
import pathlib
import subprocess
import sys

import pytest

G = pathlib.Path(__file__).resolve().parent.parent / "guiones"

SUDO = '#!/bin/bash\nexec "$@"\n'
SYSTEMCTL = r'''#!/bin/bash
S="$STUB"; echo "systemctl $*" >> "$S/log"
act() { cat "$S/active" 2>/dev/null || echo active; }
exec_line() { if [ -e "$CF_DROPIN" ]; then echo "ExecStart={ argv[]=/usr/bin/python3 --aplicar --seguir }"; else echo "ExecStart={ argv[]=/usr/bin/python3 --seguir }"; fi; }
case "$1" in
  stop) [ -e "$S/falla_stop" ] && exit 1; echo inactive > "$S/active";;
  start|restart) echo active > "$S/active"; exec_line > "$S/execstart"
     [ -e "$S/aplica_al_arrancar" ] && echo '{"evento": "aplicacion"}' >> "$CF_TRAZA";;
  is-active) case "$2" in cf-b-fin.timer) [ -e "$S/timer" ] && echo active || { echo inactive; exit 3; };; *) act;; esac;;
  show) case "$*" in *NRestarts*) cat "$S/nrestarts" 2>/dev/null || echo 0;; *) [ -e "$S/execstart" ] && cat "$S/execstart" || exec_line;; esac;;
  daemon-reload) :;;
esac
exit 0
'''
NFT = '#!/bin/bash\ncase "$*" in "list tables") cat "$STUB/tablas";; "list ruleset") echo "# ruleset simulado";; esac\n'
HELPER = r'''#!/bin/bash
IN=$(cat); echo "helper $IN" >> "$STUB/log"
case "$IN" in
  *desinstalar*) [ -e "$STUB/helper_falla" ] && { echo '{"ok": false, "error_nft": "x"}'; exit 1; }
     [ -e "$STUB/helper_no_borra" ] || sed -i '/cyberflow_dmz/d' "$STUB/tablas"
     [ -e "$STUB/helper_borra_otra" ] && sed -i '/inet filter/d' "$STUB/tablas"
     echo '{"ok": true, "operaciones": 1, "perfil": "dmz"}';;
  *listar*) echo '{"ok": true, "estado": {}}';;
esac
'''
RUN = '#!/bin/bash\necho "systemd-run $*" >> "$STUB/log"\ntouch "$STUB/timer"\n'


@pytest.fixture
def ent(tmp_path):
    s = tmp_path / "stub"
    s.mkdir()
    for n, c in (("sudo", SUDO), ("systemctl", SYSTEMCTL), ("nft", NFT), ("helper", HELPER), ("systemd-run", RUN)):
        (s / n).write_text(c)
        (s / n).chmod(0o755)
    (s / "tablas").write_text("table inet filter\ntable inet cyberflow_dmz\n")
    traza = tmp_path / "traza.jsonl"
    traza.write_text('{"evento": "recepcion"}\n')
    (tmp_path / "estado.json").write_text("{}")
    (tmp_path / "disco").mkdir()
    env = dict(os.environ, STUB=str(s), CF_SUDO=str(s / "sudo"), CF_SYSTEMCTL=str(s / "systemctl"), CF_NFT=str(s / "nft"),
               CF_HELPER=str(s / "helper"), CF_SYSTEMD_RUN=str(s / "systemd-run"), CF_DROPIN=str(tmp_path / "aplicar.conf"),
               CF_DIR_RESPALDO=str(tmp_path / "resp"), CF_TRAZA=str(traza), CF_ESTADO=str(tmp_path / "estado.json"),
               CF_ESPERA_R5="0", CF_OPT=str(tmp_path / "opt"), CF_DIR_DISCO=str(tmp_path / "disco"), CF_MIN_LIBRE_KB="1", CF_SIN_PROPIETARIO="1")
    env.pop("CF_MODO", None)
    return type("E", (), {"env": env, "s": s, "t": tmp_path})


def corre(ent, guion, **extra):
    r = subprocess.run(["bash", str(G / guion)], env={**ent.env, **extra}, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


def log(ent):
    p = ent.s / "log"
    return p.read_text().splitlines() if p.exists() else []


MUTA = {"stop", "start", "restart", "daemon-reload", "helper", "systemd-run"}


def sin_cambios(ent):
    """Ninguna orden que modifique: solo is-active / show (lectura)."""
    return not [l for l in log(ent) if l.split()[0] in ("helper", "systemd-run") or
                (l.split()[0] == "systemctl" and l.split()[1] in MUTA)]


# ------------------------------------------------------------ reversión
def test_revertir_seco_no_cambia_nada(ent):
    (ent.t / "aplicar.conf").write_text("x")
    rc, out = corre(ent, "b_revertir_srvdmz.sh")
    assert rc == 0 and "modo=seco" in out and "SECO" in out
    assert sin_cambios(ent) and (ent.t / "aplicar.conf").exists()
    assert "cyberflow_dmz" in (ent.s / "tablas").read_text() and not (ent.t / "resp").exists()


def test_revertir_real_vuelve_a_sombra(ent):
    (ent.t / "aplicar.conf").write_text("x")
    rc, out = corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")
    assert rc == 0, out
    assert not (ent.t / "aplicar.conf").exists() and "cyberflow_dmz" not in (ent.s / "tablas").read_text()
    assert "inet filter" in (ent.s / "tablas").read_text()
    (resp,) = list((ent.t / "resp").iterdir())
    assert {"SHA256SUMS", "ruleset.txt", "tablas.txt", "listar.json", "dropin.conf", "traza.jsonl"} <= {p.name for p in resp.iterdir()}
    assert "--aplicar" not in (ent.s / "execstart").read_text() and (ent.s / "active").read_text().strip() == "active"
    orden = [l.split()[1] if l.startswith("systemctl") else "helper-" + ("des" if "desinstalar" in l else "lis") for l in log(ent)
             if l.startswith("systemctl") and any(m in l for m in ("stop", "start")) or l.startswith("helper")]
    assert orden.index("stop") < orden.index("helper-des") < orden.index("start")


def test_revertir_archiva_la_traza_de_B_sin_borrarla(ent):
    traza = ent.t / "traza.jsonl"
    traza.write_text('{"evento": "aplicacion", "aplicado_en": 1.0}\n{"evento": "recepcion"}\n')
    contenido = traza.read_text()
    rc, out = corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")
    assert rc == 0, out
    assert not traza.exists()                                              # la viva ya no cuenta como 'aplicacion' para el verificador
    (arch,) = list(ent.t.glob("traza-B-*.jsonl"))
    assert arch.read_text() == contenido and (ent.t / (arch.name + ".sha256")).exists()
    (resp,) = list((ent.t / "resp").iterdir())
    assert (resp / "ruleset.nft").exists() and (resp / "traza.jsonl").read_text() == contenido


def test_revertir_seco_no_archiva_la_traza(ent):
    (ent.t / "traza.jsonl").write_text("x\n")
    corre(ent, "b_revertir_srvdmz.sh")
    assert (ent.t / "traza.jsonl").exists() and not list(ent.t.glob("traza-B-*"))


def test_revertir_urgente_apaga_primero(ent):
    corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real", CF_URGENTE="1")
    ls = log(ent)
    assert ls.index("systemctl stop ppi-enforce-agent-v2-dmz") < next(i for i, l in enumerate(ls) if l.startswith("helper") and "listar" in l)


def test_revertir_helper_con_error_es_rc13(ent):
    (ent.s / "helper_falla").touch()
    rc, out = corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")
    assert rc == 13 and "FALLO R3" in out


def test_revertir_tabla_que_no_desaparece_es_rc14(ent):
    (ent.s / "helper_no_borra").touch()
    assert corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")[0] == 14


def test_revertir_detecta_que_cambio_otra_tabla_rc14(ent):
    (ent.s / "helper_borra_otra").touch()
    rc, out = corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")
    assert rc == 14 and "otras tablas" in out


def test_revertir_si_no_para_el_agente_sigue_y_da_rc11(ent):
    (ent.s / "falla_stop").touch()
    rc, out = corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")
    assert rc == 11 and any("desinstalar" in l for l in log(ent))  # continúa con el resto


def test_revertir_detecta_aplicaciones_nuevas_tras_volver_rc15(ent):
    (ent.s / "aplica_al_arrancar").touch()
    assert corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")[0] == 15


def test_revertir_modo_invalido_es_rc2(ent):
    assert corre(ent, "b_revertir_srvdmz.sh", CF_MODO="otro")[0] == 2


# ------------------------------------------------------------ activación
def preparar_sombra(ent):
    (ent.s / "tablas").write_text("table inet filter\n")
    (ent.s / "execstart").write_text("ExecStart={ argv[]=/usr/bin/python3 --seguir }")


def test_activar_seco_no_cambia_nada(ent):
    preparar_sombra(ent)
    rc, out = corre(ent, "b_activar_srvdmz.sh")
    assert rc == 0 and "SECO" in out and "--aplicar" in out
    assert sin_cambios(ent) and not (ent.t / "aplicar.conf").exists() and not (ent.t / "opt").exists()


def test_activar_real_y_revertir_ida_y_vuelta(ent):
    preparar_sombra(ent)
    rc, out = corre(ent, "b_activar_srvdmz.sh", CF_MODO="real", CF_HORAS="6")
    assert rc == 0, out
    assert "--aplicar" in (ent.t / "aplicar.conf").read_text() and "--aplicar" in (ent.s / "execstart").read_text()
    assert (ent.t / "opt" / "b_revertir_srvdmz.sh").exists() and (ent.t / "opt" / "SHA256SUMS").exists()
    assert (ent.t / "opt" / "pre-B" / "ruleset.nft").exists() and (ent.t / "opt" / "pre-B" / "SHA256SUMS").exists()
    assert any("--on-active=6h" in l and "--unit=cf-b-fin" in l and "CF_URGENTE=1" in l for l in log(ent))
    (ent.s / "tablas").write_text("table inet filter\ntable inet cyberflow_dmz\n")  # el agente creó la tabla
    rc, out = corre(ent, "b_revertir_srvdmz.sh", CF_MODO="real")
    assert rc == 0, out
    assert not (ent.t / "aplicar.conf").exists() and "--aplicar" not in (ent.s / "execstart").read_text()


# ------------------------------------------------------------ R6 y R7
def test_r6_control(ent):
    ok = ent.t / "curl_ok"
    ok.write_text('#!/bin/bash\necho -n 200\n')
    mal = ent.t / "curl_mal"
    mal.write_text('#!/bin/bash\necho -n 000; exit 28\n')
    for f in (ok, mal):
        f.chmod(0o755)
    assert corre(ent, "b_r6_control.sh", CF_CURL=str(ok), CF_N="2")[0] == 0
    rc, out = corre(ent, "b_r6_control.sh", CF_CURL=str(mal), CF_N="2")
    assert rc == 6 and "FALLO petición 1" in out


R7_SYSTEMCTL = r'''#!/bin/bash
S="$STUB"
case "$1 $2" in
  "cat "*) cat "$S/unit";;
  "is-active ppi-publicar-feed-v2.service") cat "$S/pub_activo" 2>/dev/null || echo active;;
  "is-active logrotate.timer") cat "$S/logrotate" 2>/dev/null || echo active;;
esac
'''


@pytest.fixture
def r7(ent):
    sc = ent.s / "systemctl_r7"
    sc.write_text(R7_SYSTEMCTL)
    sc.chmod(0o755)
    (ent.s / "unit").write_text("[Service]\nExecStart=/usr/bin/python3 publicar_feed_v2.py --politica if_senal --seguir\n")
    estado, feed = ent.t / "estado_pub.json", ent.t / "feed.json"
    estado.write_text('{"vigentes": {}, "escalada": {"10.10.20.99@srv-dmz": {"bloqueos": 1}}, "eventos": {}}')
    import time
    feed.write_text('{"expira": %f, "entradas": []}' % (time.time() + 60))
    ent.env.update(CF_SYSTEMCTL=str(sc), CF_ESTADO=str(estado), CF_FEED=str(feed), CF_ESPERA="0", CF_PY=sys.executable)
    ent.estado, ent.feed = estado, feed
    return ent


def test_r7_sensor_conforme(r7):
    rc, out = corre(r7, "b_r7_sensor.sh")
    assert rc == 0 and "R7 OK" in out


@pytest.mark.parametrize("rotura", ["aplicar", "politica", "estado_kali", "feed_con_kali", "feed_viejo", "logrotate", "parado"])
def test_r7_detecta_cada_incumplimiento(r7, rotura):
    import time
    if rotura == "aplicar":
        (r7.s / "unit").write_text("ExecStart=x --politica if_senal --aplicar\n")
    elif rotura == "politica":
        (r7.s / "unit").write_text("ExecStart=x --politica actual\n")
    elif rotura == "estado_kali":
        r7.estado.write_text('{"vigentes": {"10.10.20.30|srv-dmz|todo": {}}, "escalada": {}}')
    elif rotura == "feed_con_kali":
        r7.feed.write_text('{"expira": %f, "entradas": [{"ip": "10.10.20.30"}]}' % (time.time() + 60))
    elif rotura == "feed_viejo":
        r7.feed.write_text('{"expira": 1.0, "entradas": []}')
    elif rotura == "logrotate":
        (r7.s / "logrotate").write_text("inactive")
    else:
        (r7.s / "pub_activo").write_text("inactive")
    rc, out = corre(r7, "b_r7_sensor.sh")
    assert rc == 7 and "FALLO" in out


def test_r7_real_limpia_el_estado_de_la_kali_con_d5(r7):
    r7.estado.write_text('{"vigentes": {"10.10.20.30|srv-dmz|todo": {}}, "escalada": {"10.10.20.30@srv-dmz": {}}}')
    d5 = r7.t / "d5_falso.py"
    d5.write_text("import json,sys\np=sys.argv[sys.argv.index('--estado')+1]\ne=json.load(open(p))\n"
                  "e['vigentes']={};e['escalada']={}\njson.dump(e,open(p,'w'))\n")
    assert corre(r7, "b_r7_sensor.sh", CF_D5=str(d5))[0] == 7                         # en seco no limpia: informa
    rc, out = corre(r7, "b_r7_sensor.sh", CF_D5=str(d5), CF_MODO="real")
    assert rc == 0, out


@pytest.mark.parametrize("prep", ["tabla_previa", "nrestarts", "dropin_previo", "ya_aplicar", "agente_parado", "sin_disco"])
def test_activar_se_niega_si_no_esta_limpio(ent, prep):
    preparar_sombra(ent)
    extra = {}
    if prep == "tabla_previa":
        (ent.s / "tablas").write_text("table inet cyberflow_dmz\n")
    elif prep == "nrestarts":
        (ent.s / "nrestarts").write_text("1")
    elif prep == "dropin_previo":
        (ent.t / "aplicar.conf").write_text("x")
    elif prep == "ya_aplicar":
        (ent.s / "execstart").write_text("ExecStart={ --aplicar }")
    elif prep == "agente_parado":
        (ent.s / "active").write_text("inactive")
    else:
        extra["CF_MIN_LIBRE_KB"] = "999999999999"
    rc, out = corre(ent, "b_activar_srvdmz.sh", CF_MODO="real", **extra)
    assert rc == 20 and "FALLO A0" in out
    assert sin_cambios(ent) and not (ent.t / "opt").exists()
