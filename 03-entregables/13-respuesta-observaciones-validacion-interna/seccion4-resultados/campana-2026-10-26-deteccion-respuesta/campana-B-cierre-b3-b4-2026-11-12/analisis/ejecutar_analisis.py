"""Ejecuta un script de analisis/ SIN modificarlo, sustituyendo las rutas fijas del equipo del autor por las del equipo actual.

Los scripts de analisis/ llevan fijas dos carpetas del equipo del autor: C:\\Users\\<usuario>\\cf-b3 (evidencia de B3) y C:\\Users\\<usuario>\\cf-b4 (evidencia de B4).
Este lanzador lee el script tal cual esta en el repositorio (su hash en SHA256SUMS sigue valiendo), cambia esas dos carpetas en memoria (para cualquier usuario) y lo ejecuta.

Uso (desde esta carpeta, Windows):
    python -X utf8 ejecutar_analisis.py --b3 D:\\evidencia\\cf-b3 --b4 D:\\evidencia\\cf-b4 SCRIPT.py [argumentos]

Los scripts asumen rutas de Windows (separador \\). El directorio de este lanzador va primero en sys.path, de modo que los modulos
(analizar_b, analizar_b_instrumentado, analizar_intentos, lector_pcap, e1_por_destino) se importan de aqui. No usar `python -I`
(aisla sys.path y no importaria los modulos locales)."""
import argparse
import os
import re
import sys

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--b3", required=True, help="carpeta con la evidencia de B3 (sustituye a C:\\Users\\<usuario>\\cf-b3)")
ap.add_argument("--b4", required=True, help="carpeta con la evidencia de B4 (sustituye a C:\\Users\\<usuario>\\cf-b4)")
ap.add_argument("script", help="nombre de un script de esta carpeta, p. ej. aplicar_e1_destino_25.py")
ap.add_argument("args", nargs="*", help="argumentos para el script")
a = ap.parse_args()
aqui = os.path.dirname(os.path.abspath(__file__))
ruta = os.path.join(aqui, os.path.basename(a.script))
src = open(ruta, encoding="utf-8").read()
for nombre, nuevo in (("cf-b3", a.b3), ("cf-b4", a.b4)):
    nuevo = nuevo.rstrip("\\/")
    # forma con barras dobles (docstrings) y forma simple (cadenas raw); cualquier usuario de Windows
    src = re.sub(r"C:\\\\Users\\\\[^\\\\\"'\n]+\\\\" + nombre, lambda m: nuevo.replace("\\", "\\\\"), src)
    src = re.sub(r"C:\\Users\\[^\\\"'\n]+\\" + nombre, lambda m: nuevo, src)
sys.path.insert(0, aqui)
sys.argv = [ruta] + a.args
exec(compile(src, ruta, "exec"), {"__name__": "__main__", "__file__": ruta})
