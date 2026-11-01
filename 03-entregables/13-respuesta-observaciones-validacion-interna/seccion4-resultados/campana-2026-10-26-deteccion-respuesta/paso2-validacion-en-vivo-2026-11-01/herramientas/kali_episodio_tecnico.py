#!/usr/bin/env python3
"""PASO2 (20261101T0254Z): UN episodio tecnico de inundacion HTTP para validar el motor en vivo.

NO es la campana A. Reutiliza sin modificarlos el constructor aprobado (esquema_campana.comando_de) y el
ejecutor aprobado (generar_campana.correr_episodio) de ~/cf-campana-A/scripts, con el escenario inundacion_http
de ~/cf-campana-A/escenarios/escenarios.json (sha 67798012...). Comprueba los hashes antes de lanzar nada.
La configuracion tecnica efectiva se guarda APARTE (config-tecnica.json); escenarios.json no se toca.

Uso: python3 episodio_tecnico.py --rep T1 --salida-dir ~/cf-paso2-20261101T0254Z/episodios [--autorizado]
"""
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

H = Path.home() / "cf-campana-A"
APROBADOS = {
    H / "scripts/generar_campana.py": "c586d813472d5853ae43fe512b5a53d22654699ace10894e43f57b3ddc4b171b",
    H / "scripts/esquema_campana.py": "e762e60421b4721b1e8ce32549049ae10c7e86596b0fbd37f9a35517ab904144",
    H / "escenarios/escenarios.json": "67798012cbd306e9c06ebccf5ec293c7d9db12951d93119f739c3f86a83c64ec",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rep", required=True)
    ap.add_argument("--salida-dir", required=True)
    ap.add_argument("--autorizado", action="store_true")
    a = ap.parse_args()
    for p, h in APROBADOS.items():
        real = hashlib.sha256(p.read_bytes()).hexdigest()
        if real != h:
            print(f"ABORTO: {p} sha {real} != aprobado {h}", file=sys.stderr)
            return 2
    sys.path.insert(0, str(H / "scripts"))
    import esquema_campana as esq
    import generar_campana as gen
    cfg = json.loads((H / "escenarios/escenarios.json").read_text(encoding="utf-8"))
    s = next(x for x in cfg["escenarios"] if x["id"] == "inundacion_http")
    probl = [p for p in esq.validar(cfg, exigir_herramientas=True) if "inundacion" in p]
    if probl or not s.get("habilitado"):
        print("ABORTO: escenario no valido:", probl, file=sys.stderr)
        return 2
    cfg_t = {k: v for k, v in cfg.items() if k != "escenarios"}
    cfg_t.update({"escenarios": [s], "repeticiones": 3,
                  "_campana": "paso2-tecnico-motor-20261101T0254Z (prueba de ingenieria; NO es la campana A)",
                  "_origen_config": {str(p): h for p, h in APROBADOS.items()},
                  "_comando_constructor_aprobado": esq.comando_de(cfg, s)})
    sd = Path(a.salida_dir).expanduser()
    sd.mkdir(parents=True, exist_ok=True)
    ct = sd / "config-tecnica.json"
    if not ct.exists():
        ct.write_text(json.dumps(cfg_t, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(sd / "marcas.jsonl", "a", encoding="utf-8") as marcas:
        gen.jsonl(marcas, {"evento": "episodio_tecnico_lanzado", "rep": a.rep, "autorizado": a.autorizado,
                           "reloj": gen.reloj()})
        estado = gen.correr_episodio(cfg_t, s, a.rep, sd, marcas, a.autorizado)
    print(json.dumps({"rep": a.rep, "estado": estado, "fin_utc": datetime.now(timezone.utc).isoformat()}))
    return 0 if estado in ("completo", "simulado") else 1


if __name__ == "__main__":
    raise SystemExit(main())
