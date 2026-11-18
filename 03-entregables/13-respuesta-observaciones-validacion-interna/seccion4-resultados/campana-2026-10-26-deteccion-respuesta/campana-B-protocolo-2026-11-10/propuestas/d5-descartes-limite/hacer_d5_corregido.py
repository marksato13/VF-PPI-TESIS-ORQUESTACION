#!/usr/bin/env python3
"""Genera `d5_episodio_corregido.py` a partir de `herramientas\\d5_episodio.py` (85c71124…, el de B2/B3; NO se modifica) con la corrección de D5 que distingue los sets
de APLICACIÓN (`bloqueados`, `limitados`) del contador de instrumentación `descartes_limite`. Cada sustitución se exige exacta (una sola ocurrencia).
Solo banco: no se despliega. Uso: hacer_d5_corregido.py"""
import hashlib
import io
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ORIG = AQUI.parent.parent / "herramientas" / "d5_episodio.py"
DEST = AQUI / "d5_episodio_corregido.py"

VIEJO = '''def srv_nft(origen, helper=_helper):
    r = helper({"perfil": "dmz", "operaciones": [{"op": "listar"}]})
    if not r.get("ok"):
        return {"ok": False, "rc": 2, "motivo": "listar falló: %s" % (r.get("rechazo") or r.get("error_nft"))}
    sets = (r.get("estado") or {}).get("sets") or {}
    desc = (r.get("estado") or {}).get("descartes_limite") or {}
    donde = [s for s, el in sets.items() if el and origen in el] + (["descartes_limite"] if origen in desc else [])
    tabla = any(el is not None for el in sets.values())
    return {"ok": True, "rc": 0, "tabla": tabla, "presente": bool(donde), "donde": donde}
'''
NUEVO = '''SETS_APLICACION = ("bloqueados", "limitados")   # los únicos sets sobre los que las reglas de la cadena hacen match (y descartan)
RESIDUAL = "descartes_limite"                  # contador dinámico de INSTRUMENTACIÓN (paquetes descartados por exceder la tasa): nunca descarta nada


def srv_nft(origen, helper=_helper):
    """Estado del origen en nftables. `presente`/`donde` cuentan SOLO los sets de aplicación: una restricción activa los bloquea. El contador `descartes_limite`
    es evidencia, no restricción (en el 11-nov-2026 su resto de la inundación bloqueó la puerta sin que ninguna regla pudiera actuar): se informa aparte en `residual`
    y NUNCA se borra. Fallo cerrado: si el estado no se puede verificar (helper, formato, sets de aplicación ausentes o ilegibles) devuelve `ok` False."""
    r = helper({"perfil": "dmz", "operaciones": [{"op": "listar"}]})
    if not r.get("ok"):
        return {"ok": False, "rc": 2, "motivo": "listar falló: %s" % (r.get("rechazo") or r.get("error_nft"))}
    est = r.get("estado")
    if not isinstance(est, dict):
        return {"ok": False, "rc": 2, "motivo": "estado ilegible"}
    sets = est.get("sets")
    if not isinstance(sets, dict) or any(not isinstance(sets.get(s), dict) for s in SETS_APLICACION):
        return {"ok": False, "rc": 2, "motivo": "sets de aplicación ausentes o ilegibles"}
    desc = est.get(RESIDUAL)
    if desc is not None and not isinstance(desc, dict):
        return {"ok": False, "rc": 2, "motivo": "%s ilegible" % RESIDUAL}
    donde = [s for s, el in sets.items() if s != RESIDUAL and el and origen in el]
    residual = {RESIDUAL: desc[origen]} if desc and origen in desc else {}
    return {"ok": True, "rc": 0, "tabla": True, "presente": bool(donde), "donde": donde, "residual": residual}
'''
V2 = '''        return {"lista": not motivos, "motivos": motivos, "pasos": pasos}
'''
N2 = '''        residual = {}
        for p in pasos:
            if p.get("residual"):
                residual = p["residual"]
        return {"lista": not motivos, "motivos": motivos, "pasos": pasos, "residual_conservado": residual}
'''


def main():
    t = ORIG.read_text(encoding="utf-8").replace("\r\n", "\n")
    for a, b in ((VIEJO, NUEVO), (V2, N2)):
        assert t.count(a) == 1, a[:60]
        t = t.replace(a, b)
    io.open(DEST, "w", encoding="utf-8", newline="\n").write(t)
    print("origen", hashlib.sha256(ORIG.read_bytes()).hexdigest()[:16], "-> corregido", hashlib.sha256(DEST.read_bytes()).hexdigest()[:16])


if __name__ == "__main__":
    main()
