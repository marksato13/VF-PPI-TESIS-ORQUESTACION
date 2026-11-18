#!/usr/bin/env python3
"""Lector de solo lectura (banco #3): se ejecuta como un usuario SIN permiso de escritura sobre la auditoría. Reconstruye el id con
adaptador_banco_rot.diagnosticar_rot y, con --probar, intenta escribir/renombrar/borrar una generación para comprobar que el sistema lo niega.
Imprime un JSON. Uso: lector_solo_lectura.py <id> <origen> <work> <auditoria> [--probar]"""
import json
import os
import sys

sys.path.insert(0, "/banco")
import adaptador_banco_rot as abr  # noqa: E402
import auditoria_d5 as A  # noqa: E402


def intento(f):
    try:
        f()
        return "PERMITIDO"
    except OSError as ex:
        return ex.__class__.__name__


def main(id_, origen, work, aud, probar):
    out = {"uid": os.getuid(), "gid": os.getgid(), "grupos": sorted(os.getgroups())}
    try:
        os.listdir(os.path.dirname(aud))
        out["listado_directorio"] = "OK"
    except OSError as ex:
        out["listado_directorio"] = ex.__class__.__name__
    d = abr.diagnosticar_rot(os.path.join(work, "control.json"), id_, origen, os.path.join(work, "feed.json"), os.path.join(work, "estado.json"),
                             os.path.join(work, "traza.jsonl"), aud)
    out["diagnostico"] = {k: d.get(k) for k in ("categoria", "determinada", "secuencia_publicada", "trazabilidad", "publicacion", "motivo", "generaciones_del_id")}
    out["generaciones"] = [{"ruta": os.path.basename(g["ruta"]), "lineas": g["lineas"], "ilegibles": g["ilegibles"], "error": g["error"]} for g in d["auditoria"]["generaciones"]] if d["auditoria"] else []
    if probar:
        gens = [g for g in A.generaciones(aud) if os.path.isfile(g)]
        if gens:
            g = gens[0]
            out["probar_escritura"] = {"ruta": os.path.basename(g), "anexar": intento(lambda: open(g, "ab").close()),
                                       "renombrar": intento(lambda: os.rename(g, g + ".x")), "borrar": intento(lambda: os.unlink(g)),
                                       "crear_en_directorio": intento(lambda: open(os.path.join(os.path.dirname(aud), "intruso.txt"), "w").close())}
    return out


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], "--probar" in sys.argv), sort_keys=True))
