"""DB-3 (propuesta): un α solo es elegible si LOS SEIS perfiles están presentes y cada uno cumple de forma concluyente
con al menos 2 h de ventanas C0 decididas. Los límites propuestos (L1 = 1 aviso/entidad·hora, L2 = 10 %, 2 h) no se tocan."""
from __future__ import annotations

import inspect
import os
import re
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, os.environ.get("HERR", str(AQUI.parent / "scripts")))
import analisis_db3 as a3  # noqa: E402
import limites_db3 as db  # noqa: E402

PERFILES = [f"10.10.20.{n}" for n in range(21, 27)]
T0 = 1_800_000_000.0
H2 = 720            # 2 h de ventanas de 10 s


def ent(c0=H2, alertas=(), faltan=(), req=None):
    return {"alertas": list(alertas), "c0": c0, "faltan": list(faltan), "req": c0 + len(faltan) if req is None else req}


def seis(**cambios):
    d = {ip: ent() for ip in PERFILES}
    d.update(cambios)
    return d


def test_caso_base_seis_perfiles_dos_horas_es_elegible():
    v = a3.evaluar_alfa(seis())["veredicto_alfa"]
    assert v["alfa"] == "cumple" and v["elegible"] is True
    assert set(v["entidades"]) == set(PERFILES) and set(v["entidades"].values()) == {"cumple"}


@pytest.mark.parametrize("ausente", PERFILES)
def test_falta_un_perfil_no_es_elegible(ausente):
    d = seis(); del d[ausente]
    r = a3.evaluar_alfa(d)
    assert r["veredicto_alfa"]["elegible"] is False and r["veredicto_alfa"]["alfa"] == "no_concluyente"
    assert r["veredicto_alfa"]["entidades"][ausente] == "sin_ventanas"


def test_cinco_perfiles_buenos_mas_kali_y_dc1_no_completan_los_seis():
    d = {ip: ent() for ip in PERFILES[:5]}
    d["10.10.20.30"] = ent(); d["10.10.10.5"] = ent()
    r = a3.evaluar_alfa(d)
    assert r["veredicto_alfa"]["elegible"] is False


@pytest.mark.parametrize("perfil", PERFILES)
def test_un_perfil_con_menos_de_dos_horas_c0_no_es_elegible(perfil):
    r = a3.evaluar_alfa(seis(**{perfil: ent(c0=H2 - 1)}))        # 719 ventanas = 1,997 h
    e = r["seleccion"][perfil]
    assert e["horas_c0"] < 2.0 and e["decision"] == "no_concluyente" and "menos de 2.0 h" in e["motivo_extra"]
    assert r["veredicto_alfa"]["elegible"] is False and r["veredicto_alfa"]["alfa"] == "no_concluyente"


def test_justo_720_ventanas_c0_son_dos_horas_y_bastan():
    r = a3.evaluar_alfa(seis(**{PERFILES[0]: ent(c0=720)}))
    assert r["seleccion"][PERFILES[0]]["horas_c0"] == 2.0 and r["veredicto_alfa"]["elegible"] is True


def test_las_horas_c0_cuentan_ventanas_decididas_no_las_requeridas():
    """Mucha cobertura requerida pero pocas ventanas C0 decididas: no se llega a 2 h aunque las cotas sean favorables."""
    r = a3.evaluar_alfa(seis(**{PERFILES[2]: ent(c0=300, faltan=[T0 + 10 * i for i in range(0, 600, 20)], req=630)}))
    assert r["seleccion"][PERFILES[2]]["horas_c0"] < 2.0 and r["veredicto_alfa"]["elegible"] is False


def test_un_perfil_que_no_cumple_los_limites_descarta_el_alfa_aunque_haya_dos_horas():
    alertas = [T0 + 10 * i for i in range(100)]                  # 100/720 = 13,9 % > 10 % (L2)
    r = a3.evaluar_alfa(seis(**{PERFILES[3]: ent(alertas=alertas)}))
    assert r["seleccion"][PERFILES[3]]["decision"] == "no_cumple"
    assert r["veredicto_alfa"] == {"alfa": "no_cumple", "entidades": {**{ip: "cumple" for ip in PERFILES}, PERFILES[3]: "no_cumple"}, "elegible": False}


def test_limite_l1_un_aviso_por_hora_en_dos_horas():
    dos = [T0, T0 + 600]                                         # 2 avisos en 2 h = 1,0/h ≤ 1,0
    tres = dos + [T0 + 1200]                                     # 3 avisos en 2 h = 1,5/h > 1,0
    assert a3.evaluar_alfa(seis(**{PERFILES[0]: ent(alertas=dos)}))["veredicto_alfa"]["elegible"] is True
    r = a3.evaluar_alfa(seis(**{PERFILES[0]: ent(alertas=tres)}))
    assert r["seleccion"][PERFILES[0]]["L1_avisos_por_hora"]["decision"] == "no_cumple" and r["veredicto_alfa"]["elegible"] is False


def test_ventanas_faltantes_que_abren_las_cotas_dan_no_concluyente_no_cumple():
    faltan = [T0 + 10 * i for i in range(0, 200, 10)]            # 20 ventanas sin decisión C0 entre 720+20
    r = a3.evaluar_alfa(seis(**{PERFILES[1]: ent(c0=720, alertas=[T0 + 5000.0] * 1 + [T0 + 6000.0] * 1 + [T0 + 7000.0], faltan=faltan)}))
    e = r["seleccion"][PERFILES[1]]
    assert e["L1_avisos_por_hora"]["minimo"] < e["L1_avisos_por_hora"]["maximo"]
    assert e["decision"] in ("no_concluyente", "no_cumple") and r["veredicto_alfa"]["elegible"] is False


def test_kali_dc1_y_otros_no_bloquean_y_se_reportan_aparte():
    d = seis()
    d["10.10.20.30"] = ent(c0=10, alertas=[T0 + 10 * i for i in range(10)])    # Kali: todo ALERT, pocas horas
    d["10.10.10.5"] = ent(c0=5)
    r = a3.evaluar_alfa(d)
    assert r["veredicto_alfa"]["elegible"] is True
    assert set(r["seleccion"]) == set(PERFILES)
    assert set(r["reportadas_aparte"]) == {"10.10.20.30", "10.10.10.5"}
    assert not (set(r["reportadas_aparte"]) & set(PERFILES))


def test_los_33_minutos_del_3b_son_antecedente_no_dan_alfa_elegible():
    """33 min = 198 ventanas de 10 s: ni un α limpio puede ser elegible con ese control."""
    r = a3.evaluar_alfa({ip: ent(c0=198) for ip in PERFILES})
    assert all(e["horas_c0"] < 2.0 for e in r["seleccion"].values())
    assert r["veredicto_alfa"]["elegible"] is False and r["veredicto_alfa"]["alfa"] == "no_concluyente"


def test_el_minimo_es_un_parametro_pero_su_valor_por_defecto_es_dos_horas():
    r = a3.evaluar_alfa({ip: ent(c0=198) for ip in PERFILES}, min_c0_horas=0.5)
    assert r["veredicto_alfa"]["elegible"] is True                              # solo si alguien cambia el parámetro, a la vista
    p = inspect.signature(a3.evaluar_alfa).parameters
    assert (p["min_c0_horas"].default, p["l1"].default, p["l2"].default) == (2.0, 1.0, 0.10)
    fuente = Path(a3.__file__).read_text(encoding="utf-8")
    assert re.search(r'"--min-c0-horas", type=float, default=2\.0', fuente)
    assert re.search(r'"--l1", type=float, default=1\.0', fuente) and re.search(r'"--l2", type=float, default=0\.10', fuente)
    assert db.SEPARACION_AVISO_S == 60.0
    assert a3.PERFILES == tuple(PERFILES)


def test_la_eleccion_ignora_alfas_no_elegibles():
    ok = a3.evaluar_alfa(seis())["veredicto_alfa"]
    corto = a3.evaluar_alfa(seis(**{PERFILES[0]: ent(c0=H2 - 1)}))["veredicto_alfa"]
    r = db.elegir_alfa({"0.05": corto, "0.03": ok, "0.01": corto}, {"0.05": 99, "0.03": 1, "0.01": 99})
    assert r["resultado"] == "elegido" and r["alfa"] == "0.03"
    r2 = db.elegir_alfa({"0.05": corto, "0.03": corto, "0.01": corto}, {"0.05": 9, "0.03": 9, "0.01": 9})
    assert r2["resultado"] == "no_concluyente" and r2["alfa"] is None
