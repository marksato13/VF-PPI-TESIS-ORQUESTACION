"""Construye el paquete de cierre de la Campana B (B3 + B4) dentro del repositorio VF-PPI-TESIS-ORQUESTACION. Offline; no toca ningun host.
Lee: copias locales de la evidencia (C:\\Users\\markp\\cf-b3, cf-b4) y la carpeta de trabajo campana-B-protocolo-2026-11-10. Escribe en la carpeta del paquete (prefijo \\\\?\\ por las rutas largas).
Excluye: PCAP crudos (solo manifiestos con hash), credenciales, registros sensibles (accesos, journals, claves)."""
import csv, collections, datetime, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

REPO = r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio"
SEC = r"03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta"
SRC = Path("\\\\?\\" + REPO + "\\" + SEC + r"\campana-B-protocolo-2026-11-10")
PKG = Path("\\\\?\\" + REPO + "\\" + SEC + r"\campana-B-cierre-b3-b4-2026-11-12")
REL = (SEC + r"\campana-B-cierre-b3-b4-2026-11-12").replace("\\", "/")
W3, W4 = Path(r"C:\Users\markp\cf-b3"), Path(r"C:\Users\markp\cf-b4")
BASE_COMMIT = sys.argv[1] if len(sys.argv) > 1 else "?"


def sha(p, n=64):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:n]


def put(rel, texto=None, copia=None):
    d = PKG / rel
    d.parent.mkdir(parents=True, exist_ok=True)
    if texto is not None:
        with open(d, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    else:
        shutil.copyfile(copia, d)
    return d


# ---------------------------------------------------------------- datos
R3 = json.load(open(W3 / "resultado-b3.json", encoding="utf8"))["episodios"]
R4 = json.load(open(W4 / "resultado-b4.json", encoding="utf8"))["episodios"]
E1D = {x["episodio"]: x for x in json.load(open(W4 / "resultado-e1-por-destino-25.json", encoding="utf8"))}
marcas = [json.loads(l) for l in open(W4 / "kali" / "corrida" / "marcas.jsonl", encoding="utf8") if l.strip()]
ORDEN = [m for m in marcas if m["evento"] == "campana_inicio"][0]["tramo"]["orden_completo"]
ID_B3, ID_B4 = "4c-20261111T051928Z-2eb2f728a738", "4c-B4-20261111T135745Z-b0ec7e96836a"
FIL = {}
for tr, L, ide in (("B3", R3, ID_B3), ("B4", R4, ID_B4)):
    for r in L:
        FIL[r["episodio"]] = (tr, ide, r)


def clases(p):
    c = {}
    for l in open(p, encoding="utf8"):
        if not l.strip():
            continue
        x = json.loads(l)
        if isinstance(x.get("clases"), dict):
            for k, v in x["clases"].items():
                c[k] = v if isinstance(v, str) else v.get("clase")
    return c


CL = {}
CL.update(clases(W3 / "bastion" / "vigia" / "vigia.jsonl"))
CL.update(clases(W4 / "bastion" / "vigia" / "vigia.jsonl"))
REGLA = {"inundacion_http": ("http_abuse", "LIMIT"), "fuerza_bruta_http": ("brute_force", "BLOCK"), "dns_inusual": ("dns_entropy", "ninguna (DC1 sin punto de aplicacion)"),
         "escaneo_breve": ("port_scan", "BLOCK"), "escaneo_sostenido": ("port_scan", "BLOCK")}

# ---------------------------------------------------------------- hashes de analizadores y evidencia local
AN = {}
for nombre, ruta in (("analizar_b.py", SRC / "herramientas" / "analizar_b.py"), ("analizar_b_instrumentado.py", SRC / "instrumentacion" / "analizar_b_instrumentado.py"),
                     ("analizar_intentos.py", SRC / "instrumentacion" / "analizar_intentos.py"), ("lector_pcap.py", SRC / "revision-evidencia-b2" / "lector_pcap.py"),
                     ("analizar_b3.py", SRC / "corrida-2026-11-11" / "scripts-operativos" / "analizar_b3.py"), ("analizar_b4.py", SRC / "corrida-2026-11-11" / "scripts-operativos" / "analizar_b4.py"),
                     ("e1_por_destino.py", W4 / "e1_por_destino.py"), ("aplicar_e1_destino_25.py", W4 / "aplicar_e1_destino_25.py"), ("test_e1_por_destino.py", W4 / "test_e1_por_destino.py")):
    AN[nombre] = sha(ruta, 16)
EV = {
    "B3": {"marcas_generador": ("kali/corrida/marcas.jsonl (copia en bastion/corrida/marcas.jsonl)", sha(W3 / "bastion" / "corrida" / "marcas.jsonl")),
           "traza_agente_srvdmz": ("cf-b3-agente.jsonl (srv-dmz traza-B-20261111T060906Z.jsonl)", sha(W3 / "cf-b3-agente.jsonl")),
           "lecturas_set": ("cf-b3-set-lecturas.jsonl", sha(W3 / "cf-b3-set-lecturas.jsonl")),
           "traza_publicador": ("evid/traza.jsonl", sha(W3 / "evid" / "traza.jsonl"))},
    "B4": {"marcas_generador": ("kali/corrida/marcas.jsonl", sha(W4 / "kali" / "corrida" / "marcas.jsonl")),
           "traza_agente_srvdmz": ("agente-B4.jsonl (srv-dmz traza-B-20261111T171449Z.jsonl)", sha(W4 / "agente-B4.jsonl")),
           "lecturas_set": ("set-lecturas.jsonl", sha(W4 / "set-lecturas.jsonl")),
           "traza_publicador": ("evid/traza.jsonl", sha(W4 / "evid" / "traza.jsonl"))},
}
ANALIZADOR = {"B3": "analizar_b3.py@" + AN["analizar_b3.py"] + " + analizar_b.py@" + AN["analizar_b.py"] + " + analizar_b_instrumentado.py@" + AN["analizar_b_instrumentado.py"],
              "B4": "analizar_b4.py@" + AN["analizar_b4.py"] + " + analizar_b.py@" + AN["analizar_b.py"] + " + analizar_b_instrumentado.py@" + AN["analizar_b_instrumentado.py"]}
OBJ = SEC.replace("\\", "/") + "/etapa1-objetivos-candidata-2026-11-01/OBJETIVOS-Y-CRITERIOS.md"
BLOB_OBJ = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD:" + OBJ], capture_output=True, text=True).stdout.strip()
CRIT = {"E1": "OBJETIVOS-Y-CRITERIOS.md fila E1 (linea 93) @ blob " + BLOB_OBJ[:12], "E2": "OBJETIVOS-Y-CRITERIOS.md fila E2 (linea 94)", "E3": "criterios/CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md + OBJETIVOS fila E3 (linea 95)",
        "E4": "OBJETIVOS-Y-CRITERIOS.md fila E4 (linea 96)", "E5": "OBJETIVOS-Y-CRITERIOS.md fila E5 (linea 97)"}

# ---------------------------------------------------------------- motivos
def e3_motivo(r):
    f, e3 = r["familia"], r["E3"]
    if e3["resultado"] == "cumple":
        return "cumple: efecto sostenido 3 bloques de 1 s tras t_apl, 0 respuestas, SYN por bloque (SPAN), contador del host con id e IP; t_efecto +%.1f s del inicio" % e3["t_efecto_menos_t_inicio"]
    if e3["resultado"] == "no_aplica":
        return "no aplica: DC1 no tiene punto de aplicacion"
    if f == "inundacion_http":
        c = e3.get("continuidad") or {}
        return "indeterminado (I2): no se demuestra continuidad de intentos 5 bloques tras t_apl por SPAN ni por salida con hora (B0 SYN %s/s, B0 intentos %s/s; tras la regla el generador sincrono emite ~16,5 intentos/s < 0,5xB0); ver criterios/LIMITACION-GENERADOR-E3-INUNDACION.md" % (c.get("b0_syn"), c.get("b0_intentos_salida"))
    return ("indeterminado (I2 del analizador): en BLOCK la continuidad solo se acepta por SPAN 'al destino y puerto del episodio' y el analizador la midio en el puerto 18081 (rama BLOCK, tag '18'); "
            "un escaneo no tiene puerto unico, por lo que no se pudo verificar. NO demuestra que el generador dejara de intentar (ver reanalisis/ y CONSOLIDADO, evidencia complementaria)")


def e2_txt(r):
    e = r["E2"]
    if e["resultado"] == "no_aplica":
        return "no aplica: DC1 sin punto de aplicacion; el agente de srv-dmz ignora las entradas de DC1"
    return "%s %s a +%.2f s del inicio (margen %.1f s antes del fin), regla id %s" % (e["resultado"], e["confirmacion"], e["t_apl_menos_t_inicio"], e["margen_antes_del_fin_s"], e["id_regla"])


def e5_txt(r):
    e = r["E5"]
    if e["resultado"] == "no_aplica":
        return "no aplica: no hubo regla que retirar"
    return "%s por %s (retirada D5 +%.1f s tras el fin; %d lecturas del set)" % (e["resultado"], e["via"], e["retirada_d5_menos_fin_s"], e["lecturas_del_set"])


# ---------------------------------------------------------------- resultados por episodio
filas = []
for i, ep in enumerate(ORDEN, 1):
    tr, ide, r = FIL[ep]
    d = E1D[ep]
    reg, acc = REGLA[r["familia"]]
    iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"
    e1o = r["E1"]
    filas.append({
        "n": i, "tramo": tr, "corrida_id": ide, "episodio": ep, "familia": r["familia"], "regla_prevista": reg, "accion_prevista": acc,
        "estado_generador": r["estado_generador"], "clase_salud": CL.get(ep, "n/d"), "t_inicio_utc": iso(r["t_inicio"]), "t_fin_utc": iso(r["t_fin"]), "duracion_s": r["duracion_s"],
        "E1_formal_original": e1o["resultado"],
        "E1_original_motivo": e1o.get("motivo") or "senal %s a +%.2f s; paquetes en ventana: %s" % (e1o["señal_publicador"], e1o["t_det_menos_t_inicio"], e1o.get("paquetes_kali_en_ventana_evidencia_y_episodio")),
        "E1_reanalisis_por_destino": d["resultado_por_destino"], "E1_paquetes_por_destino": d["paquetes_por_destino"], "E1_paquetes_previos_al_inicio": d["paquetes_previos_al_inicio_en_ventana"],
        "E1_t_det_menos_t_inicio_s": e1o["t_det_menos_t_inicio"], "E1_destino": d["destino"], "E1_otras_reglas": ",".join(e1o.get("otras_reglas_en_ventana") or []),
        "E2_resultado": r["E2"]["resultado"], "E2_evidencia": e2_txt(r),
        "E3_formal": r["E3"]["resultado"], "E3_motivo": e3_motivo(r),
        "E4_resultado": r["E4"]["resultado"], "E4_evidencia": "%d transacciones de control en %d perfiles, %s" % (r["E4"]["n"], len(r["E4"]["perfiles"]), r["E4"]["motivo"]),
        "E5_resultado": r["E5"]["resultado"], "E5_evidencia": e5_txt(r),
        "criterio_E1": CRIT["E1"], "criterio_E3": CRIT["E3"], "analizador": ANALIZADOR[tr],
        "analizador_E1_reanalisis": "e1_por_destino.py@%s + aplicar_e1_destino_25.py@%s" % (AN["e1_por_destino.py"], AN["aplicar_e1_destino_25.py"]),
        "evidencia_marcas_sha256": EV[tr]["marcas_generador"][1], "evidencia_traza_agente_sha256": EV[tr]["traza_agente_srvdmz"][1], "evidencia_set_lecturas_sha256": EV[tr]["lecturas_set"][1],
        "evidencia_pcap": "manifiestos/pcap-%s.sha256 (PCAP crudos no incluidos)" % tr,
    })

cols = list(filas[0].keys())
(PKG / "resultados").mkdir(parents=True, exist_ok=True)
with open(PKG / "resultados" / "resultados-por-episodio.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(filas)
put("resultados/resultados-por-episodio.json", json.dumps({"campana": "B", "tramos": {"B3": {"corrida_id": ID_B3, "episodios": "1-6"}, "B4": {"corrida_id": ID_B4, "episodios": "7-25"}}, "planificados": 25, "ejecutados": 25, "episodios": filas}, indent=1, ensure_ascii=False) + "\n")
put("resultados/resultado-b3.json", copia=W3 / "resultado-b3.json")
put("resultados/resultado-b4.json", copia=W4 / "resultado-b4.json")
put("resultados/resultado-e1-por-destino-25.json", copia=W4 / "resultado-e1-por-destino-25.json")

# ---------------------------------------------------------------- consolidado
c = collections.Counter
t_e = {k: c() for k in ("E1o", "E1n", "E2", "E3", "E4", "E5")}
for x in filas:
    t_e["E1o"][x["E1_formal_original"]] += 1; t_e["E1n"][x["E1_reanalisis_por_destino"]] += 1
    t_e["E2"][x["E2_resultado"]] += 1; t_e["E3"][x["E3_formal"]] += 1; t_e["E4"][x["E4_resultado"]] += 1; t_e["E5"][x["E5_resultado"]] += 1
ok = lambda cc: cc["cumple"] + cc["verificado"]
fam = collections.defaultdict(lambda: {"B3": [], "B4": []})
for x in filas:
    fam[x["familia"]][x["tramo"]].append(x["episodio"].rsplit("-", 1)[1])
timeouts = [x for x in filas if x["estado_generador"] == "incompleto_timeout"]
L = []
L += ["# Consolidado de los 25 episodios de la Campana B (B3 + B4)", "",
      "Campana B = respuesta real con el agente `--aplicar` limitado a la Kali 10.10.20.30. Los 25 episodios previstos (5 por familia) se ejecutaron en **dos tramos de corridas separadas**: **B3** (episodios 1-6, corrida parcial `%s`, cancelada por decision de Mark tras el episodio 6) y **B4** (episodios 7-25, corrida nueva `%s`, completa). Cada episodio proviene de una de ellas; ninguno procede de B1 ni de B2 (ver `HISTORIAL-CAMPANA-B.md`)." % (ID_B3, ID_B4), "",
      "## Denominadores", "",
      "| Concepto | Valor |", "|---|---|",
      "| Episodios previstos | 25 (5 por familia: inundacion_http, fuerza_bruta_http, dns_inusual, escaneo_breve, escaneo_sostenido) |",
      "| Ejecutados | 25 = **B3: 6** (episodios 1-6) + **B4: 19** (episodios 7-25) |",
      "| Estado del generador | completo %d, `incompleto_timeout` %d (todos escaneos de B4); ninguno excluido del analisis |" % (sum(1 for x in filas if x["estado_generador"] == "completo"), len(timeouts)),
      "| Clase de salud de la captura | C0 en los 25 (B3 6/6, B4 19/19) |",
      "| E1, E4 | denominador 25 |",
      "| E2, E3, E5 | denominador **20** (los 5 episodios `dns_inusual` son `no aplica`: DC1 no tiene punto de aplicacion) |", "",
      "## Tabla de los 25 episodios", "",
      "Resultado **formal** (analisis original, sin modificar) en E2-E5. En E1 se muestra el formal original y, cuando difiere, el **reanalisis por destino** (ver `reanalisis/`).", "",
      "| N | Tramo | Episodio | Generador | Clase | E1 | E2 | E3 | E4 | E5 |", "|---|---|---|---|---|---|---|---|---|---|"]
sim = {"cumple": "cumple", "verificado": "verificado", "indeterminado": "indeterminado", "no_aplica": "no aplica"}
for x in filas:
    e1 = sim[x["E1_formal_original"]] if x["E1_formal_original"] == x["E1_reanalisis_por_destino"] else "%s -> **%s** (reanalisis)" % (sim[x["E1_formal_original"]], sim[x["E1_reanalisis_por_destino"]])
    L.append("| %d | %s | `%s` | %s | %s | %s | %s | %s | %s | %s |" % (x["n"], x["tramo"], x["episodio"], x["estado_generador"], x["clase_salud"], e1, sim[x["E2_resultado"]], sim[x["E3_formal"]], sim[x["E4_resultado"]], sim[x["E5_resultado"]]))
L += ["", "## Totales", "", "| Indicador | Denominador | cumple/verificado | indeterminado | no aplica | fallido |", "|---|---|---|---|---|---|"]
for k, nm, den in (("E1o", "E1 formal original", 25), ("E1n", "E1 reanalisis por destino", 25), ("E2", "E2", 20), ("E3", "E3 formal", 20), ("E4", "E4", 25), ("E5", "E5", 20)):
    cc = t_e[k]
    L.append("| %s | %d | %d | %d | %d | %d |" % (nm, den, ok(cc), cc["indeterminado"], cc["no_aplica"], cc["fallido"]))
L += ["", "Por tramo (E1 formal original / E3 formal): **B3** E1 6/6 verificado; E3 2 cumple (fuerza bruta), 2 indeterminado (inundacion), 2 no aplica (DNS). **B4** E1 9/19 verificado y 10 indeterminado (escaneos, por herramienta); E3 3 cumple, 13 indeterminado (3 inundacion + 10 escaneos), 3 no aplica.", "",
      "## Cobertura por familia y tramo", "", "| Familia | B3 | B4 | Total |", "|---|---|---|---|"]
for f in ("inundacion_http", "fuerza_bruta_http", "dns_inusual", "escaneo_breve", "escaneo_sostenido"):
    a, b = fam[f]["B3"], fam[f]["B4"]
    L.append("| %s | %d (%s) | %d (%s) | %d |" % (f, len(a), ", ".join(a) or "-", len(b), ", ".join(b) or "-", len(a) + len(b)))
L += ["", "## Los ocho `incompleto_timeout` (todos B4, conservados)", "",
      "El generador termino el proceso (`nmap`, codigo -15) al agotar el tope del episodio. No se reclasifican, no se excluyen y no se repiten en este cierre.", "",
      "| N | Episodio | Duracion (s) | Tope (s) | E2 | E3 | E5 |", "|---|---|---|---|---|---|---|"]
for x in timeouts:
    tope = 180 if "breve" in x["episodio"] else 900
    L.append("| %d | `%s` | %s | %d | %s | %s | %s |" % (x["n"], x["episodio"], x["duracion_s"], tope, x["E2_resultado"], x["E3_formal"], x["E5_evidencia"].split(" (")[0]))
L += ["", "Contraste (no formal): en la Campana A, sin restriccion, los mismos comandos terminaron en 4,6-5,0 s (breve) y 52,3-52,9 s (sostenido). Con BLOCK, breve tardo 138 s (2 completos) o mas de 182 s (3 cortados) y sostenido mas de 902 s (5 cortados). La causa interna en `nmap` no se observo.", "",
      "## Motivos de indeterminacion de E3 (15 episodios)", "", "| N | Episodio | Motivo |", "|---|---|---|"]
for x in filas:
    if x["E3_formal"] == "indeterminado":
        L.append("| %d | `%s` | %s |" % (x["n"], x["episodio"], x["E3_motivo"]))
L += ["", "## Motivos de `no aplica` (5, DNS)", "", "`dns_inusual-r1`, `-r3` (B3) y `-r4`, `-r2`, `-r5` (B4): DC1 (10.10.10.20) no tiene punto de aplicacion; E2, E3 y E5 no aplican. E1 y E4 si se evaluan.", "",
      "## Limitaciones abiertas", "",
      "- **Discrepancia entre el SPAN y los contadores de srv-dmz (abierta).** El contador del elemento en `bloqueados` cuenta entre el 5 y el 20 % de los paquetes Kali->srv-dmz que el SPAN ve en los escaneos (cota superior, tras tener en cuenta los reinicios del contador por cada renovacion de la regla) y alrededor de la mitad en fuerza bruta. No esta explicada; el ensayo del contador queda **fuera del alcance** de este cierre. Detalle en `balances/BALANCE-B4.md` (seccion SPAN frente a contadores).",
      "- La repeticion de los escaneos queda **fuera del alcance** de este cierre.",
      "- E3 de los 10 escaneos sigue indeterminado por el criterio fijado; la evidencia complementaria esta en `reanalisis/`.",
      "- E4 y E5 de B3 se calcularon con los datos de la corrida parcial; la puerta D5 de B3 devolvio `lista=false` tras el episodio 6 por un falso bloqueo ya diagnosticado y corregido antes de B4 (ver historial); no cambia ninguna celda.", ""]
put("CONSOLIDADO-25-EPISODIOS.md", "\n".join(L) + "\n")

# ---------------------------------------------------------------- copias
for n in ("CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md", "CRITERIO-E3-FINAL-PARA-APROBAR.md", "CRITERIO-E3-SPAN-O-SALIDA.md", "LIMITACION-GENERADOR-E3-INUNDACION.md"):
    put("criterios/" + n, copia=SRC / n)
put("balances/BALANCE-B3-PARCIAL.md", copia=SRC / "BALANCE-B3-PARCIAL.md")
b4 = open(SRC / "BALANCE-B4.md", "rb").read().decode("utf-8")
corte = b4.index("\n## Trazabilidad E1")
put("balances/BALANCE-B4.md", b4[:corte].rstrip("\n") + "\n")
anexo = b4[corte:]
for ruta, nombre in ((SRC / "herramientas" / "analizar_b.py", "analizar_b.py"), (SRC / "herramientas" / "mutar_analizar_b.py", "mutar_analizar_b.py"), (SRC / "tests" / "test_analizar_b.py", "test_analizar_b.py"),
                     (SRC / "instrumentacion" / "analizar_b_instrumentado.py", "analizar_b_instrumentado.py"), (SRC / "instrumentacion" / "analizar_intentos.py", "analizar_intentos.py"),
                     (SRC / "instrumentacion" / "test_instrumentacion.py", "test_instrumentacion.py"), (SRC / "revision-evidencia-b2" / "lector_pcap.py", "lector_pcap.py"),
                     (SRC / "corrida-2026-11-11" / "scripts-operativos" / "analizar_b3.py", "analizar_b3.py"), (SRC / "corrida-2026-11-11" / "scripts-operativos" / "analizar_b4.py", "analizar_b4.py")):
    put("analisis/" + nombre, copia=ruta)
for nombre in ("e1_por_destino.py", "test_e1_por_destino.py", "aplicar_e1_destino.py", "aplicar_e1_destino_25.py", "span_extract.py", "span_extract2.py", "cmp_contadores.py", "cmp2.py", "cmp3.py", "scan_rates.py", "consolidar.py"):
    put("analisis/" + nombre, copia=W4 / nombre)
put("analisis/construir_paquete.py", copia=Path(__file__))
put("analisis/textos_paquete.py", copia=Path(__file__).with_name("textos_paquete.py"))

# regresion E1 (15 episodios con puerto)
reg = ["| Episodio | Tramo | Conteo del lector historico | Conteo por puerto (nuevo lector) | Conteo por destino | Veredicto original = por destino |", "|---|---|---|---|---|---|"]
for ep in ORDEN:
    d = E1D[ep]
    if d["paquetes_control_mismo_puerto"] is None:
        continue
    reg.append("| `%s` | %s | %s | %s | %s | %s |" % (ep, d["tramo"], d["paquetes_original"], d["paquetes_control_mismo_puerto"], d["paquetes_por_destino"], "si" if d["resultado_original"] == d["resultado_por_destino"] else "NO"))
esc = ["| Episodio | Senal (s tras inicio) | Paquetes Kali->destino en ventana y episodio | Previos al inicio | Toca episodio anterior | Resultado original | Por destino |", "|---|---|---|---|---|---|---|"]
for ep in ORDEN:
    d = E1D[ep]
    if d["familia"].startswith("escaneo"):
        esc.append("| `%s` | %s (%s%s) | %d | %d | %s | %s | %s |" % (ep, d["t_det_menos_t_inicio"], d["regla_senal"], "; tambien " + ",".join(d["otras_reglas_en_ventana"]) if d["otras_reglas_en_ventana"] else "", d["paquetes_por_destino"], d["paquetes_previos_al_inicio_en_ventana"], d["toca_episodio_anterior"], d["resultado_original"], d["resultado_por_destino"]))
rean = ["# Reanalisis de E1 por destino (12-nov-2026) bajo el criterio vigente", "",
        "**Los balances originales (`../balances/`) no se modifican.** Este documento anade un reanalisis offline de E1 sobre las copias definitivas de la evidencia. No cambia E2-E5, no reclasifica E3 y conserva los ocho `incompleto_timeout`.", "",
        "## Criterio tal como esta escrito",
        "`" + CRIT["E1"] + "`: «senal atribuible (paquetes **del origen al destino del episodio** dentro de la ventana y de [inicio, fin]) de la regla prevista, con t_det + eps < t_fin_eval». Habla de destino, no de puerto.", "",
        "## Que cambia respecto del lector original",
        "El lector original (`analizar_b3.py`/`analizar_b4.py`) ademas filtraba por puerto (80, 18081, 53). Para los escaneos no habia puerto y devolvia `indeterminado: sin lector de paquetes para este servicio` (indeterminado de herramienta, no de datos). `e1_por_destino.py` cuenta todos los paquetes origen->destino (Kali -> 10.10.30.10; Kali -> 10.10.10.20 en DNS). Diferencia deliberada: sin paquetes en la ventana devuelve `indeterminado`; el lector historico devolvia el resultado de la senal.", "",
        "## Implementacion y pruebas",
        "- `analisis/e1_por_destino.py` (sha256 %s...), `analisis/test_e1_por_destino.py` (9 pruebas: 8 de comportamiento y una que exige eliminar 5 mutantes; todas pasan), `analisis/aplicar_e1_destino_25.py` -> `resultados/resultado-e1-por-destino-25.json`." % AN["e1_por_destino.py"],
        "- Extraccion del SPAN: `analisis/span_extract2.py` (PCAP B3: 514 ficheros; B4: 2.343; manifiestos con hash en `manifiestos/`).",
        "- Ejecucion registrada en `pruebas/PRUEBAS-EJECUTADAS.md`.", "",
        "## Regresion sobre los 15 episodios con puerto",
        "El veredicto original coincide con el de por destino en los 15. Los conteos del lector historico difieren algo de los nuevos: la ventana de evidencia se guardo redondeada a 0,1 s (diferencias de hasta ~0,9 %, consistente con ese redondeo) y, en DNS, el lector historico contaba ambos sentidos Kali<->DC1 (aproximadamente el doble). No se modifica ningun resultado formal.", ""] + reg + [
        "", "## Resultado en los 10 escaneos", "E1 = verificado en los 10: senal `port_scan` (prevista) dentro del episodio, paquetes de la Kali al destino en la ventana, 0 paquetes previos al inicio y ventana sin tocar el episodio anterior.", ""] + esc + [
        "", "## Resultado global", "E1 sobre los 25: formal original %d verificado / %d indeterminado; reanalisis por destino %d verificado / %d indeterminado." % (t_e["E1o"]["verificado"], t_e["E1o"]["indeterminado"], t_e["E1n"]["verificado"], t_e["E1n"]["indeterminado"]), "",
        "---", "", "# Anexo: texto anadido al BALANCE-B4 el 12-nov (sin cambios)", ""]
put("reanalisis/REANALISIS-E1-POR-DESTINO.md", "\n".join(rean) + anexo)

# ---------------------------------------------------------------- manifiestos
def manifiesto(dirp, nombre):
    ls = sorted(Path(dirp).glob("*.pcap"))
    txt = "".join("%s  %s\n" % (sha(p), p.name) for p in ls)
    put("manifiestos/" + nombre, txt)
    return len(ls)
n3 = manifiesto(W3 / "pcap", "pcap-B3.sha256")
n4 = manifiesto(W4 / "pcap", "pcap-B4.sha256")
loc = []
for tr, d in (("B3", W3), ("B4", W4)):
    pass
orig_rows = []
for tr in ("B3", "B4"):
    for k, (ruta, h) in EV[tr].items():
        orig_rows.append((tr, k, ruta, h))
ev_extra = [("B3", "clientes (transacciones por perfil)", W3 / "cf-b3-clientes"), ("B4", "clientes (transacciones por perfil)", W4 / "clientes"), ("B3", "intentos de la Kali (inundacion, con hora)", W3 / "cf-b3-kali" / "intentos"), ("B4", "intentos de la Kali (inundacion, con hora)", W4 / "kali" / "intentos"),
            ("B4", "salidas de nmap/curl del generador", W4 / "kali" / "corrida" / "salidas")]
txt = ""
for tr, nm, d in ev_extra:
    for p in sorted(Path(d).glob("*")):
        if p.is_file():
            txt += "%s  %s/%s/%s\n" % (sha(p), tr, nm.split(" ")[0], p.name)
put("manifiestos/evidencia-local-clientes-intentos-salidas.sha256", txt)
n_extra = txt.count("\n")

# ---------------------------------------------------------------- pruebas ejecutadas (se rellena tras correr pytest)
pr = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(SRC / "tests" / "test_analizar_b.py")[4:]], capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), cwd=r"C:\Users\markp")
pe = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(W4 / "test_e1_por_destino.py")], capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), cwd=r"C:\Users\markp")
ahora = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
put("pruebas/PRUEBAS-EJECUTADAS.md", "\n".join([
    "# Pruebas de los analizadores (ejecutadas al construir el paquete, %s)" % ahora, "",
    "| Prueba | Resultado | Notas |", "|---|---|---|",
    "| `analisis/test_analizar_b.py` (analizador de B, E1-E5) | `%s` | pytest, Python %s, sobre las fuentes del paquete (copia identica a la de la carpeta de trabajo) |" % ((pr.stdout.strip().splitlines() or ["?"])[-1], sys.version.split()[0]),
    "| `analisis/test_e1_por_destino.py` (E1 por destino) | `%s` | 8 pruebas de comportamiento + 1 de mutantes (5 mutantes, todos eliminados) |" % (pe.stdout.strip().splitlines() or ["?"])[-1], "",
    "## No re-ejecutado en este cierre", "`analisis/test_instrumentacion.py` (E3 `e3_v2`, instrumentacion de la inundacion, muestreador del set) requiere el banco Docker (`cyberflow-etapa3-banco:1`) con el producto de la etapa 3 montado; Docker Desktop estaba apagado al construir el paquete. Su ultima ejecucion registrada esta en los documentos de la carpeta de trabajo y en `criterios/CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md` (9 pruebas de la rama BLOCK, 4 mutaciones eliminadas); no se ha repetido ni se ha modificado desde entonces.", "",
    "## Salida literal", "```", pr.stdout.strip(), "```", "```", pe.stdout.strip(), "```", ""]))

# ---------------------------------------------------------------- historial, indice, readme
exec(open(Path(__file__).with_name("textos_paquete.py"), encoding="utf8").read())
put("HISTORIAL-CAMPANA-B.md", HISTORIAL)
put("README.md", README.replace("@BASE@", BASE_COMMIT).replace("@REL@", REL).replace("@N3@", str(n3)).replace("@N4@", str(n4)))
idx = [INDICE_CAB.replace("@BASE@", BASE_COMMIT), "", "## A. Originales y su referencia (NO incluidos en el paquete)", "",
       "| Tramo | Evidencia | Copia local de trabajo (no versionada) | sha256 |", "|---|---|---|---|"]
for tr, k, ruta, h in orig_rows:
    idx.append("| %s | %s | `%s` | `%s` |" % (tr, k, ruta, h))
idx += ["| B3 | resultado-b3.json (analisis) | `resultados/resultado-b3.json` | `%s` |" % sha(W3 / "resultado-b3.json"),
        "| B4 | resultado-b4.json (analisis) | `resultados/resultado-b4.json` | `%s` |" % sha(W4 / "resultado-b4.json"),
        "| B3 | PCAP crudos (%d) | `C:\\Users\\markp\\cf-b3\\pcap\\` | manifiesto `manifiestos/pcap-B3.sha256` |" % n3,
        "| B4 | PCAP crudos (%d) | `C:\\Users\\markp\\cf-b4\\pcap\\` (tar `pcap.tar` sha `%s`) | manifiesto `manifiestos/pcap-B4.sha256` |" % (n4, sha(W4 / "pcap.tar")),
        "| B3+B4 | clientes, intentos y salidas (%d ficheros) | `cf-b3-clientes`, `cf-b4\\clientes`, `kali\\intentos`, `kali\\corrida\\salidas` | `manifiestos/evidencia-local-clientes-intentos-salidas.sha256` |" % n_extra, "",
       INDICE_HOSTS, "", "## C. Referencias al criterio escrito", "",
       "| Indicador | Criterio | Version |", "|---|---|---|"]
for k, v in CRIT.items():
    idx.append("| %s | %s | `OBJETIVOS-Y-CRITERIOS.md` en `%s` (commit base `%s`, blob `%s`) |" % (k, v, OBJ, BASE_COMMIT[:7], BLOB_OBJ[:12]))
idx += ["", "## D. Version de los analizadores (sha256 de los 16 primeros caracteres; completo en `SHA256SUMS`)", "", "| Fichero | sha256 |", "|---|---|"]
for k, v in AN.items():
    idx.append("| `analisis/%s` | `%s` |" % (k, v))
idx += ["", "## E. Trazabilidad por episodio", "", "Cada fila de `resultados/resultados-por-episodio.csv` (y `.json`) lleva: tramo y `corrida_id`; criterio (`criterio_E1`, `criterio_E3`); analizador y version (`analizador`, `analizador_E1_reanalisis`); hashes de la evidencia de su tramo (`evidencia_marcas_sha256`, `evidencia_traza_agente_sha256`, `evidencia_set_lecturas_sha256`) y el manifiesto de PCAP; y, por indicador, el resultado con su evidencia o el motivo de indeterminacion o no aplicabilidad.", "",
        "## F. Exclusiones", "", "No se incluyen: PCAP crudos (3,x GB; solo manifiestos con hash), credenciales y claves SSH (los scripts solo citan nombres de ruta, ningun valor), registros de acceso a hosts (`accesos-kali.log`), journals, trazas del agente y salidas del generador en bruto (se referencian por hash). El historial cita rutas de los hosts del laboratorio, que son informacion de laboratorio aislado.", ""]
put("INDICE-EVIDENCIA.md", "\n".join(idx))

# ---------------------------------------------------------------- SHA256SUMS del paquete
lines = []
for p in sorted(PKG.rglob("*")):
    if p.is_file() and p.name != "SHA256SUMS":
        lines.append("%s  %s" % (sha(p), str(p)[len(str(PKG)) + 1:].replace("\\", "/")))
put("SHA256SUMS", "\n".join(lines) + "\n")
print("paquete:", PKG, "| ficheros:", len(lines), "| pytest B:", (pr.stdout.strip().splitlines() or ["?"])[-1], "| e1:", (pe.stdout.strip().splitlines() or ["?"])[-1])
