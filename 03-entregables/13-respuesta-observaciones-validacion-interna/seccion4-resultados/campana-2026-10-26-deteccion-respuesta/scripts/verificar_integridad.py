#!/usr/bin/env python3
"""Verificador de integridad de fuentes por campaña/episodio (lo consulta analizar.py antes de declarar evaluable).

La continuidad de motor_decision.log NO demuestra que PCAP, EVE e historia previa estén completos. Este verificador
produce, por episodio, un informe con:
  - ficheros y hashes de PCAP, EVE, decisiones y características/puntuaciones
  - cobertura previa / durante / posterior
  - continuidad, rotaciones y ficheros faltantes
  - estado y reinicios de captura, Suricata y motor
  - errores y pérdidas de captura conocidos
  - disponibilidad de la historia que exige el procesamiento (>=120 s)
  - estado de sincronización y correspondencia temporal entre fuentes
Cada requisito es True / False / "desconocido". Un requisito 'desconocido' NO se cuenta como correcto:
  apto = (todos los requisitos True) y (sin desconocidos).

Entrada: un DESCRIPTOR JSON (lista de episodios con rutas/estadísticas/salud). Donde haya rutas reales, calcula el
hash; donde falte evidencia, marca 'desconocido'. No ejecuta la campaña ni toca los hosts.

    python3 verificar_integridad.py --descriptor desc.json --salida integridad.json
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

REQUISITOS = ("pcap_presente", "eve_presente", "decisiones_presentes", "caracteristicas_presentes",
              "cobertura_previa_suficiente", "cobertura_durante_completa", "cobertura_posterior_suficiente",
              "continuidad_sin_huecos", "sin_ficheros_faltantes", "captura_sin_perdidas",
              "historia_requerida_disponible", "relojes_sincronizados", "telemetria_eve_verificable")
HISTORIA_MIN_S = 120
POST_MIN_S = 90


def sha256(p: Path):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def _tri(v):
    """Normaliza a True / False / 'desconocido'."""
    return v if v in (True, False) else "desconocido"


def evaluar_episodio(e: dict) -> dict:
    """e: descriptor de un episodio. Devuelve requisitos tri-estado + apto + desconocidos."""
    req = {}
    # ficheros: hash real si la ruta existe; si no, el hash declarado en el descriptor; si no, None
    arch = {}
    for campo in ("pcap", "eve", "decisiones", "caracteristicas"):
        ruta = e.get("rutas", {}).get(campo)
        h = sha256(Path(ruta)) if ruta and Path(ruta).exists() else e.get("hashes", {}).get(campo)
        arch[campo] = {"ruta": ruta, "sha256": h}
    # 'presente' = True si hay hash (real o declarado); si el descriptor no dice nada -> desconocido
    req["pcap_presente"] = _tri(True if arch["pcap"]["sha256"] else e.get("pcap_presente"))
    req["eve_presente"] = _tri(True if arch["eve"]["sha256"] else e.get("eve_presente"))
    req["decisiones_presentes"] = _tri(True if arch["decisiones"]["sha256"] else e.get("decisiones_presentes"))
    req["caracteristicas_presentes"] = _tri(True if arch["caracteristicas"]["sha256"]
                                            else e.get("caracteristicas_presentes"))
    cov = e.get("cobertura_s", {})
    req["cobertura_previa_suficiente"] = _tri(cov["previa"] >= HISTORIA_MIN_S if "previa" in cov else None)
    req["cobertura_durante_completa"] = _tri(e.get("cobertura_durante_completa"))
    req["cobertura_posterior_suficiente"] = _tri(cov["posterior"] >= POST_MIN_S if "posterior" in cov else None)
    req["continuidad_sin_huecos"] = _tri(e.get("continuidad_sin_huecos"))
    req["sin_ficheros_faltantes"] = _tri((len(e["faltantes"]) == 0) if "faltantes" in e else None)
    perd = e.get("captura", {}).get("paquetes_descartados")
    req["captura_sin_perdidas"] = _tri(perd == 0 if perd is not None else None)
    req["historia_requerida_disponible"] = _tri(cov["previa"] >= HISTORIA_MIN_S if "previa" in cov else None)
    off = e.get("relojes", {})
    req["relojes_sincronizados"] = _tri(all(abs(v) <= off.get("tolerancia_s", 1) for k, v in off.items()
                                            if k != "tolerancia_s") if off else None)
    # EVE: ausencia de eventos NO es pérdida salvo que la salud lo contradiga
    salud = e.get("salud", {})
    if e.get("eve_eventos", None) == 0:
        # inactividad válida vs fallo de telemetría: solo verificable con salud + cobertura
        if salud.get("suricata_activo") and salud.get("trafico_presente"):
            req["telemetria_eve_verificable"] = False      # debería haber eventos y no hay -> fallo
        else:
            req["telemetria_eve_verificable"] = _tri(None)  # desconocido: no se puede afirmar pérdida ni validez
    else:
        req["telemetria_eve_verificable"] = _tri(e.get("telemetria_eve_verificable"))

    reinicios = {k: e.get("reinicios", {}).get(k) for k in ("captura", "suricata", "motor")}
    desconocidos = [k for k, v in req.items() if v == "desconocido"]
    apto = all(req[k] is True for k in REQUISITOS)
    return {"episodio_id": e["episodio_id"], "campana": e.get("campana"), "archivos": arch,
            "requisitos": req, "reinicios": reinicios, "errores_captura": e.get("errores_captura", []),
            "desconocidos": desconocidos, "apto": apto,
            "criterio": "apto sólo si todos los requisitos son True y no hay 'desconocido' (desconocido != correcto)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--descriptor", required=True)
    ap.add_argument("--salida", default="integridad.json")
    a = ap.parse_args()
    desc = json.load(open(a.descriptor, encoding="utf-8"))
    eps = [evaluar_episodio(e) for e in desc.get("episodios", [])]
    rep = {"generado_por": "verificar_integridad.py",
           "nota": "La continuidad del motor NO implica PCAP/EVE/historia completos. 'desconocido' no es 'apto'.",
           "episodios": eps,
           "resumen": {"aptos": [e["episodio_id"] for e in eps if e["apto"]],
                       "no_aptos": [e["episodio_id"] for e in eps if not e["apto"]]}}
    Path(a.salida).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep["resumen"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
