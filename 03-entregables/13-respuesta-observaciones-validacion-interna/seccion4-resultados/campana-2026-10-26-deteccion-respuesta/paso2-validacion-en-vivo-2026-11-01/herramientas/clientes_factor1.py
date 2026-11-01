#!/usr/bin/env python3
"""PASO2 (20261101T0254Z): ejecuta el generador legitimo SIN modificarlo, con el factor horario fijado en 1,0.

clientes_lab.py calcula factor = factor_horario(hora local, fin de semana) * --intensidad. Para la validacion
tecnica del motor se fija factor_horario = 1,0 (hora punta de dia laborable, la misma carga que la campana A
entre 08:00 y 13:00 UTC). Todo lo demas (perfiles, pesos, ritmos, rafagas x6 del perfil erratico, fallos
intencionados, --intensidad 1,0, origen, servidor, DNS) queda igual. No cambia relojes ni zona horaria.

Reversible: basta parar estos procesos (parar_factor1.sh); el fichero clientes_lab.py no se toca.
"""
import sys

sys.path.insert(0, "/home/adminclientes/laboratorio")
import clientes_lab  # noqa: E402

_original = clientes_lab.factor_horario


def factor_fijo(ahora, forzar_laborable=False):
    return 1.0


clientes_lab.factor_horario = factor_fijo
print("PASO2: factor_horario fijado en 1.0 (original devolveria %.3f ahora)"
      % _original(__import__("datetime").datetime.now()), file=sys.stderr, flush=True)
sys.argv = ["clientes_lab.py"] + sys.argv[1:]
raise SystemExit(clientes_lab.main())
