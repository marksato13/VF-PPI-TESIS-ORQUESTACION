#!/usr/bin/env python3
"""Integración con SYSTEMD REAL del D5 corregido (variante del lanzador): reutiliza el arnés `probar_integracion_systemd.py` (sin modificarlo) sustituyendo el
nftables simulado por uno con el contrato real del helper (contador `descartes_limite` con la Kali + la Kali en `limitados`), para que cada caso (acuse válido, acuse no
escribible -> bloqueo, reanudación manual) corra con el residual presente. Criterios del arnés: unidad activa, mismo MainPID, NRestarts sin aumentar, journal sin parada ni
arranque, publicación nueva tras el caso, demás entidades conservadas. Añade: en I-A el contador queda registrado y NO se borra, y el publicador no se reinició.
Se ejecuta como root DENTRO del contenedor con systemd (`cf-d5-integracion`): /banco = propuestas\\d5-sin-reinicio, /herramientas = herramientas con el d5 CORREGIDO como
d5_episodio.py, /camp = esta carpeta de campaña (solo lectura), /evidencia escribible."""
import sys

sys.path.insert(0, "/banco")
sys.path.insert(0, "/camp/propuestas/d5-descartes-limite")
import probar_integracion_systemd as P  # noqa: E402

RES = {"10.10.20.30": {"bytes": 5546, "expira_s": 3248, "id": None, "paquetes": 74}}
ESTADO = {"descartes_finales": []}


class NftResidual(P.NftSimulado):
    def __init__(self):
        super().__init__()
        self.sets["limitados"] = {P.K: {"id": "lim"}}          # la Kali con regla activa (episodio con LIMIT)
        self.descartes = {i: dict(v) for i, v in RES.items()}
        ESTADO["nft"] = self

    def __call__(self, peticion):
        op = peticion["operaciones"][0]
        if op["op"] == "listar":
            return {"ok": True, "estado": {"sets": {k: dict(v) for k, v in self.sets.items()}, "descartes_limite": {i: dict(v) for i, v in self.descartes.items()}, "reglas": []}}
        return super().__call__(peticion)


P.NftSimulado = NftResidual
_cargar = P.cargar_banco


def cargar_banco_corregido():
    m = _cargar()
    P.chk("el derivado del lanzador contiene la corrección (SETS_APLICACION, residual)", "SETS_APLICACION" in open("/opt/d5/d5_episodio_banco.py").read() and "residual_conservado" in open("/opt/d5/d5_episodio_banco.py").read())
    orig = m.PuertaBanco.preparar_episodio

    def preparar(self, *a, **k):
        r = orig(self, *a, **k)
        h = r["historial"][0]
        nft = ESTADO.get("nft")
        if r["lista"] and h.get("residual_conservado"):
            P.chk("residual registrado en la puerta (resultado y paso nft_despues)", h["residual_conservado"] == {"descartes_limite": RES["10.10.20.30"]} and
                  any(p.get("residual") for p in h["pasos"] if p["paso"] == "nft_despues"))
            P.chk("el contador residual NO se borró del nftables simulado", nft is not None and nft.descartes == RES)
        return r
    m.PuertaBanco.preparar_episodio = preparar
    return m


P.cargar_banco = cargar_banco_corregido

if __name__ == "__main__":
    sys.exit(P.main())
