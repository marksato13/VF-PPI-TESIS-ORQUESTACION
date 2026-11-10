#!/usr/bin/env python3
"""Construye guiones/s50_analisis_e4.sh (s50 v2 de la 4C) a partir del s50 de `etapa4-4c-paso3-eve-2026-11-08` (7477f4c5…).
Cada reemplazo debe aplicarse exactamente una vez; si no, el constructor falla. Los hashes de las dos herramientas nuevas se
calculan de los ficheros de `herramientas/`. Uso: python3 construir_s50_v2.py"""
import hashlib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
BASE = RAIZ.parent / "etapa4-4c-paso3-eve-2026-11-08" / "guiones" / "s50_analisis_e4.sh"
SHA_BASE = "7477f4c5ae651a4c08c1c1e8448ebf3e48cfb144341acb235f805dc756a935d5"
t = BASE.read_bytes().decode("utf-8")
assert "\r" not in t and hashlib.sha256(t.encode()).hexdigest() == SHA_BASE, "el s50 base no es el esperado (7477f4c5…)"
cfe = hashlib.sha256((RAIZ / "herramientas/calidad_fuentes_eve.py").read_bytes()).hexdigest()
dts = hashlib.sha256((RAIZ / "herramientas/descartes_tcpdump_sigusr1.py").read_bytes()).hexdigest()


def r(a: str, b: str) -> None:
    global t
    assert t.count(a) == 1, (t.count(a), a[:90])
    t = t.replace(a, b)


r("set -u -o pipefail\nFASE=",
  "# ENMIENDA 4C s50 v2 (2026-11-10, etapa4-4c-s50-v2-2026-11-10). La primera ejecución completa de la 4C (cuarta corrida) terminó con rc 0 pero con la\n"
  "# población principal vacía por dos defectos de las herramientas de análisis, no de los datos: (1) el paso 2 (calidad_fuentes.py) mide Suricata con\n"
  "# stats.log, que Suricata 7 escribe sin kernel_drops a cero -> «suricata: sin stats.log» en los 25 episodios; (2) el paso 5 (generar_respaldos.py) no\n"
  "# recibía las lecturas SIGUSR1 de tcpdump -> paquetes_descartados null -> integridad «ausente» en los 25. Cambios, y solo estos:\n"
  "#   - paso 2: calidad_fuentes_eve.py (reutiliza calidad_fuentes.calidad_episodio y sustituye la medida de Suricata por salud_captura.medida_suricata_eve sobre\n"
  "#     el segmento EVE; solo `cero_explicito` cuenta como cero descartes);\n"
  "#   - paso d (nuevo): descartes_tcpdump_sigusr1.py, JSON de descartes del proceso tcpdump desde las lecturas SIGUSR1 que s40 archivó en salud/tcpdump-anillo.log\n"
  "#     (una medición no demostrable da dropped_by_kernel null, nunca 0); el paso 5 lo recibe con --descartes-tcpdump y pasa a depender de 3, 4 y d;\n"
  "#   - ANALISIS_NOMBRE (por defecto «analisis»): carpeta de salida dentro de ~/cf-e4/<fase>/, para no tocar una v1 ya generada;\n"
  "#   - las dos herramientas nuevas viven en ~/cf-e4/herramientas-4c-v2 con hash fijado en este guion.\n"
  "# Las herramientas fijadas por hash (herramientas-e4.sha256) NO se modifican. El resto del guion es el de etapa4-4c-paso3-eve-2026-11-08.\n"
  "set -u -o pipefail\nFASE=")
r("C=$B/copias; A=$B/analisis; E4=$HOME/cyberflow-e4/ec78ca5\n",
  "C=$B/copias; A=$B/${ANALISIS_NOMBRE:-analisis}; E4=$HOME/cyberflow-e4/ec78ca5; HV=$HOME/cf-e4/herramientas-4c-v2\n"
  f"CFE_SHA={cfe}\nDTS_SHA={dts}\n"
  "case \"${ANALISIS_NOMBRE:-analisis}\" in *[!A-Za-z0-9._-]*|\"\"|.|..) echo \"PARAR: ANALISIS_NOMBRE no válido\"; exit 2;; esac\n")
r("[ -s \"$EVE\" ] || { echo \"PARAR: falta el segmento EVE",
  "[ \"$(sha256sum \"$HV/calidad_fuentes_eve.py\" 2>/dev/null | cut -c1-64)\" = \"$CFE_SHA\" ] || { echo \"PARAR: calidad_fuentes_eve.py ausente o con hash distinto\"; exit 2; }\n"
  "[ \"$(sha256sum \"$HV/descartes_tcpdump_sigusr1.py\" 2>/dev/null | cut -c1-64)\" = \"$DTS_SHA\" ] || { echo \"PARAR: descartes_tcpdump_sigusr1.py ausente o con hash distinto\"; exit 2; }\n"
  "[ -s \"$EVE\" ] || { echo \"PARAR: falta el segmento EVE")
r("sha256sum \"$H\"/*.py \"$H\"/*.json \"$SC\"", "sha256sum \"$H\"/*.py \"$H\"/*.json \"$HV\"/*.py \"$SC\"")
r("p_2() { python3 calidad_fuentes.py --marcas \"$M\" --stats \"$C/stats-inicio.log\" \"$C/stats-fin.log\" --archivador \"$C/archivar.log\" \\\n"
  "          --muestras \"$C/muestras.jsonl\" --duracion-pcap 5 --salida \"$A/calidad-fuentes.json\" > \"$A/calidad.stdout\" 2> \"$A/calidad.stderr\"; }\n",
  "p_2() { python3 \"$HV/calidad_fuentes_eve.py\" --herramientas \"$H\" --salud-captura \"$SC\" --eve \"$EVE\" --marcas \"$M\" --archivador \"$C/archivar.log\" \\\n"
  "          --muestras \"$C/muestras.jsonl\" --duracion-pcap 5 --salida \"$A/calidad-fuentes.json\" > \"$A/calidad.stdout\" 2> \"$A/calidad.stderr\"; }\n")
r("p_4() {",
  "p_d() { python3 \"$HV/descartes_tcpdump_sigusr1.py\" --salud-captura \"$SC\" --log \"$B/salud/tcpdump-anillo.log\" \\\n"
  "          --servicios-inicio \"$B/estado-inicial/servicios.txt\" --servicios-fin \"$C/servicios-fin.txt\" --salida \"$A/descartes-tcpdump.json\" \\\n"
  "          > \"$A/descartes.stdout\" 2> \"$A/descartes.stderr\"\n"
  "        cat \"$A/descartes.stdout\"; }\n"
  "p_4() {")
r("--servicios-fin \"$C/servicios-fin.txt\" --suricata-stats \"$A/suricata-stats.json\" \\\n",
  "--servicios-fin \"$C/servicios-fin.txt\" --suricata-stats \"$A/suricata-stats.json\" --descartes-tcpdump \"$A/descartes-tcpdump.json\" \\\n")
r("  REQ+=(1 2 3 4 5 6 7 8 9)\n", "  REQ+=(1 2 3 d 4 5 6 7 8 9)\n")
r("  paso 4 \"\"    \"caracteristicas.jsonl recalculo.stdout recalculo.stderr\" p_4\n  paso 5 \"3 4\" ",
  "  paso d \"\"    \"descartes-tcpdump.json descartes.stdout descartes.stderr\" p_d\n"
  "  paso 4 \"\"    \"caracteristicas.jsonl recalculo.stdout recalculo.stderr\" p_4\n  paso 5 \"3 4 d\" ")
out = AQUI / "s50_analisis_e4.sh"
out.write_bytes(t.encode("utf-8"))
print("s50 v2", hashlib.sha256(out.read_bytes()).hexdigest())
print("calidad_fuentes_eve.py", cfe)
print("descartes_tcpdump_sigusr1.py", dts)
