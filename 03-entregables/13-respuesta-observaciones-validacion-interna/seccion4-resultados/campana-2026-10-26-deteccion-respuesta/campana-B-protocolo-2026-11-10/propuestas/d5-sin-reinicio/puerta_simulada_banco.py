#!/usr/bin/env python3
"""PROPUESTA DE BANCO (simulador): función de puerta D5 SIMULADA que usa el adaptador aislado. Se entrega a `compuerta_b.paso_puerta` /
`compuerta_b.bucle` (el mismo contrato que usa el arnés de integración: devuelve {"lista": bool, "intentos": int}). NO es d5_episodio.py, no se
instala y no toca el orquestador: `compuerta_b` solo se importa en banco, de solo lectura, para verificar el cableado.

Reglas:
 - Acuse válido (`ok`)            -> {"lista": True}: la compuerta libera y el episodio simulado puede continuar.
 - Acuse ausente, incierto o rechazado -> {"lista": False}: el caso queda FALLIDO, se conserva su traza (la del adaptador) y se REGISTRA.
 - HALLAZGO del banco: `compuerta_b.bucle` vuelve a llamar a la función tras cada `fallida`. Una función ingenua repetiría la solicitud (con id
   nuevo) en cada turno. Por eso, tras un fallo la función queda BLOQUEADA y responde {"lista": False, "intentos": 0} SIN emitir otra
   solicitud, hasta que una persona llame a `reanudar_manual`."""
import json
import time


class PuertaSimulada:
    def __init__(self, adaptador, origen, registro=None, ahora=time.time):
        self.ad, self.origen, self.registro, self.ahora = adaptador, origen, registro, ahora
        self.bloqueada = None                                         # resultado del caso fallido que bloquea nuevas solicitudes
        self.solicitudes = 0                                          # solicitudes REALES emitidas
        self.omitidas = 0                                             # turnos de la compuerta sin solicitud por estar bloqueada

    def _log(self, reg):
        if self.registro is not None:
            with open(self.registro, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(reg, t=self.ahora()), sort_keys=True, default=str) + "\n")

    def __call__(self):
        if self.bloqueada is not None:
            self.omitidas += 1
            self._log({"evento": "omitida_por_caso_fallido", "id_fallido": self.bloqueada.get("id")})
            return {"lista": False, "intentos": 0}
        self.solicitudes += 1
        r = self.ad.limpiar(self.origen)
        self._log({"evento": "solicitud", "ok": r["ok"], "estado": r.get("estado"), "categoria": r.get("categoria"), "id": r.get("id"),
                   "publicacion": r.get("publicacion"), "evidencia": r.get("evidencia")})
        if r["ok"]:
            return {"lista": True, "intentos": 1}
        self.bloqueada = r
        return {"lista": False, "intentos": 1}

    def reanudar_manual(self, quien):
        """Única vía para volver a solicitar tras un fallo: decisión manual, registrada con quién la tomó."""
        self._log({"evento": "reanudacion_manual", "por": quien, "id_fallido": (self.bloqueada or {}).get("id")})
        self.bloqueada = None
