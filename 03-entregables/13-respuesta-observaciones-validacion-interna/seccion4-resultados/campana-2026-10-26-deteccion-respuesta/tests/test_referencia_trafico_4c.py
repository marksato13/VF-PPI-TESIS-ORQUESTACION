"""Pruebas de scripts/referencia_trafico_4c.py con datos sintéticos (no hay trafico-observado.json en el 3B)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import referencia_trafico_4c as rt  # noqa: E402

T0 = 1_800_000_000.0


def iso(t):
    return rt.iso(t)


def _analisis(tmp, eid, disp, senales=("IF_0.05", "HEUR"), cat="oportuna"):
    an = {"episodios": {eid: {
        "en_poblacion_principal": True,
        "IF_0.05": {"categoria": cat}, "HEUR": {"categoria": cat},
        "ventanas": [{"window_end_utc": iso(disp - 1.0), "disponible_utc": iso(disp), "atribucion": "atribuible",
                      "senales": list(senales)}],
        "emisiones_reales": {"emisiones": 1, "atribuibles": 1, "oportunas": 1}}}}
    p = tmp / "an.json"
    p.write_text(json.dumps(an), encoding="utf-8")
    return p


def _trafico(tmp, eid, ini, fin, pfin, paquetes=40, cubre=True):
    tr = {"episodios": [{"episodio": eid, "escenario": eid.rsplit("-r", 1)[0], "destino": "10.10.30.10",
                         "t_proc_inicio_utc": iso(T0), "t_proc_fin_utc": iso(pfin),
                         "t_trafico_inicio_utc": iso(ini) if ini else None, "t_trafico_fin_utc": iso(fin) if fin else None,
                         "paquetes_ataque": paquetes, "retraso_primer_paquete_s": (ini - T0) if ini else None,
                         "puertos_distintos_syn": 20, "captura_cubre_ventana": cubre, "observacion": None}]}
    p = tmp / "tr.json"
    p.write_text(json.dumps(tr), encoding="utf-8")
    return p


def _run(tmp, an, tr, *extra):
    out = tmp / "out.json"
    assert rt.main(["--analisis", str(an), "--trafico", str(tr), "--salida", str(out), *extra]) == 0
    return json.loads(out.read_text(encoding="utf-8"))["episodios"]


def test_escaneo_breve_oportuna_contra_rafaga_real(tmp_path):
    # generador termina en T0+10, el último SYN observado en T0+3: la señal disponible en T0+5 es solo_posterior
    eid = "escaneo_breve-r1"
    r = _run(tmp_path, _analisis(tmp_path, eid, T0 + 5.0), _trafico(tmp_path, eid, T0 + 0.5, T0 + 3.0, T0 + 10.0))[eid]
    c = r["configuraciones"]["IF_0.05"]
    assert c["categoria_3b"] == "oportuna"
    assert c["categoria_trafico"]["categoria"] == "solo_posterior"
    assert c["principal"] == "solo_posterior"
    assert r["referencia_principal"] == "tráfico"
    assert r["referencia_trafico"]["t_fin_eval"] == iso(T0 + 3.0)


def test_epsilon_y_fin_del_generador_acota(tmp_path):
    eid = "escaneo_breve-r2"
    # último SYN T0+12 después del fin del generador T0+10: fin_eval = T0+10; disponible T0+10,005 <= +ε
    r = _run(tmp_path, _analisis(tmp_path, eid, T0 + 10.005), _trafico(tmp_path, eid, T0 + 0.2, T0 + 12.0, T0 + 10.0))[eid]
    assert r["configuraciones"]["HEUR"]["principal"] == "oportuna"


def test_otro_escenario_conserva_categoria_3b(tmp_path):
    eid = "inundacion_http-r1"
    r = _run(tmp_path, _analisis(tmp_path, eid, T0 + 50.0), _trafico(tmp_path, eid, T0 + 1, T0 + 20, T0 + 60))[eid]
    c = r["configuraciones"]["IF_0.05"]
    assert c["categoria_trafico"]["categoria"] == "solo_posterior"
    assert c["principal"] == "oportuna"  # referencia principal = generador (v3)


def test_sin_trafico_no_inventa(tmp_path):
    eid = "escaneo_breve-r3"
    r = _run(tmp_path, _analisis(tmp_path, eid, T0 + 5.0), _trafico(tmp_path, eid, None, None, T0 + 10, paquetes=0))[eid]
    assert r["referencia_trafico"]["determinable"] is False
    assert r["configuraciones"]["IF_0.05"]["principal"] == "oportuna"


def test_via_rapida_y_propuesta_con_entrega(tmp_path):
    eid = "escaneo_breve-r4"
    sr = tmp_path / "sr.jsonl"
    sr.write_text(json.dumps({"event": "senal_rapida", "regla": "port_scan_temprano", "origen": "10.10.20.30",
                              "destino": "10.10.30.10", "t_evidencia": T0 + 1.0, "disponible_en": T0 + 1.2,
                              "emitido_en": T0 + 1.3}) + "\n", encoding="utf-8")
    tp = tmp_path / "tp.jsonl"
    tp.write_text(json.dumps({"evento": "publicacion", "publicado_en": T0 + 2.0, "secuencia": 7, "nuevos": [
        {"ip": "10.10.20.30", "regla": "port_scan_temprano", "tipo": "nueva", "accion": "BLOCK", "destino": "srv-dmz"}]})
        + "\n", encoding="utf-8")
    tl = tmp_path / "tl.jsonl"
    tl.write_text(json.dumps({"traido_en": T0 + 2.5, "destinos": {"srv-dmz": {"entregado_en": T0 + 2.9}}}) + "\n",
                  encoding="utf-8")
    r = _run(tmp_path, _analisis(tmp_path, eid, T0 + 5.0), _trafico(tmp_path, eid, T0 + 0.5, T0 + 3.0, T0 + 10.0),
             "--senales-rapidas", str(sr), "--traza-publicador", str(tp), "--traza-rele", str(tl))[eid]
    v = r["via_rapida"]
    assert v["senal"] and v["oportuna"] and v["referencia"] == "tráfico"
    p = r["respuesta_propuesta"]
    assert p["propuesta"] and p["accion"] == "BLOCK" and p["entrega_srv_dmz_utc"] == iso(T0 + 2.9)
    assert "NO aplicada" in p["nota"]
