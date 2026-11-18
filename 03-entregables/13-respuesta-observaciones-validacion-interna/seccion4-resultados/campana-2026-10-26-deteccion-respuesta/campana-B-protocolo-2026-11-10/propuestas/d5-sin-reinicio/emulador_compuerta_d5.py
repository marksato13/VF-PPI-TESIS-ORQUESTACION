#!/usr/bin/env python3
"""EMULADOR de cómo se invoca D5 de verdad: `compuerta_b.puerta` llama a `puerta_fn()` en cada turno del bucle y `puerta_fn` crea una `Puerta` NUEVA
(`d5.Puerta(runners).preparar_episodio(...)`); además cada orden remota (`sensor-limpiar`...) es un proceso nuevo por SSH y el proceso de la compuerta
puede reiniciarse. Aquí CADA invocación es un PROCESO NUEVO que construye todo desde cero (adaptador, runners, puerta) y sale.
Uso: emulador_compuerta_d5.py --modulo <d5_episodio_banco.py> --cfg <cfg.json> --dir <dir de la compuerta> preparar | reanudar --quien Q --motivo M
Imprime un JSON; rc 0 = ejecutado, rc 2 = reanudación rechazada."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, "/banco")
import adaptador_banco_rot as abr  # noqa: E402


class NftSimulado:
    def __call__(self, peticion):
        op = peticion["operaciones"][0]["op"]
        if op == "listar":
            return {"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": {}}, "descartes_limite": {}}}
        return {"ok": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--modulo", required=True)
    p.add_argument("--cfg", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("accion", choices=["preparar", "reanudar"])
    p.add_argument("--quien", default="")
    p.add_argument("--motivo", default="")
    a = p.parse_args()
    c = json.loads(Path(a.cfg).read_text())
    spec = importlib.util.spec_from_file_location("d5_episodio_banco", a.modulo)
    m = importlib.util.module_from_spec(spec)
    sys.modules["d5_episodio_banco"] = m
    spec.loader.exec_module(m)
    ad = abr.AdaptadorBancoRot(c["ctl"], c["feed"], c["estado"], c["traza"], c["auditoria"], esperar_s=c["esperar_s"])
    rn = m.RunnersBanco(ad, c["feed"], c["agente_traza"], NftSimulado())
    kw = dict(espera_agente=c["espera_agente"], espera_feed=c["espera_feed"], sondeo=0.1)
    if a.accion == "preparar":
        r = m.puerta_fn_banco(a.dir, rn, **kw)
        print(json.dumps({"lista": r["lista"], "bloqueada": r["bloqueada"], "pasos": [x["paso"] for x in r["historial"][0]["pasos"]]}))
        return 0
    pu = m.PuertaBanco(rn, registro=str(Path(a.dir) / "puerta-banco.jsonl"), estado_bloqueo=str(Path(a.dir) / "puerta-bloqueo.json"), **kw)
    try:
        pu.reanudar_manual(a.quien, a.motivo)
    except ValueError as ex:
        print(json.dumps({"reanudado": False, "error": str(ex)}))
        return 2
    print(json.dumps({"reanudado": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
