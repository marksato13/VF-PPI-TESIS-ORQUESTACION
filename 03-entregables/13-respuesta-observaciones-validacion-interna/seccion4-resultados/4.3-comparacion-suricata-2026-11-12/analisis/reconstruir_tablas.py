#!/usr/bin/env python3
"""Reconstruye las tablas numericas de la Tabla 9 y del control SOLO a partir de los resultados publicados en ../resultados/ (sin PCAP ni extractos).
Uso: python reconstruir_tablas.py [carpeta_resultados]   (por omision ../resultados). Comprueba ademas las cifras de referencia y falla si no coinciden."""
import collections, csv, json, math, statistics as st, sys
from pathlib import Path

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "resultados"
E = list(csv.DictReader(open(D / "resultados-por-episodio.csv", encoding="utf-8")))
U = list(csv.DictReader(open(D / "control-unidades-entidad-ventana.csv", encoding="utf-8")))
FAMS = ["dns_inusual", "inundacion_http", "fuerza_bruta_http", "escaneo_sostenido", "escaneo_breve"]
f = lambda x: float(x) if x != "" else None


def cp(k, n, a=0.05):
    cdf = lambda x, p: sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))
    lo = 0.0 if k == 0 else None; hi = 1.0 if k == n else None
    if lo is None:
        a_, b_ = 0.0, 1.0
        for _ in range(60):
            m = (a_ + b_) / 2
            if 1 - cdf(k - 1, m) > a / 2: b_ = m
            else: a_ = m
        lo = (a_ + b_) / 2
    if hi is None:
        a_, b_ = 0.0, 1.0
        for _ in range(60):
            m = (a_ + b_) / 2
            if cdf(k, m) > a / 2: a_ = m
            else: b_ = m
        hi = (a_ + b_) / 2
    return round(100 * lo), round(100 * hi)


def med(v):
    v = [x for x in v if x is not None]
    return "—" if not v else "%s [%s–%s]" % tuple(("%.2f" % x).replace(".", ",") for x in (st.median(v), min(v), max(v)))


def cobertura():
    cols = [("CyberFlow `HIB_0.01`, tiempo de datos", lambda r: r["cf_HIB01_detecta_tiempo_datos"] == "si"),
            ("CyberFlow `HIB_0.01`, disponibilidad (`s50`)", lambda r: r["cf_HIB01_categoria_s50"] == "oportuna"),
            ("Suricata, regla fijada", lambda r: int(r["suri_P_validas_durante"]) > 0),
            ("Suricata, solo firmas ET Open", lambda r: int(r["suri_P_firmas_ET_durante"]) > 0)]
    out = {}
    L = ["| Familia | Elegibles | " + " | ".join(c for c, _ in cols) + " |", "|---|---|" + "---|" * len(cols)]
    for fam in FAMS + ["TOTAL"]:
        rs = E if fam == "TOTAL" else [r for r in E if r["familia"] == fam]; n = len(rs)
        cel = []
        for c, fn in cols:
            k = sum(1 for r in rs if fn(r)); out[(fam, c)] = (k, n)
            lo, hi = cp(k, n); cel.append("%d/%d (IC95 %d–%d %%)" % (k, n, lo, hi) if fam == "TOTAL" else "%d/%d" % (k, n))
        L.append("| %s | %d | %s |" % (("**Total**" if fam == "TOTAL" else fam), n, " | ".join(cel)))
    return "\n".join(L), out


def tiempos():
    L = ["| Familia | Episodios con alerta de ambos | CyberFlow: cierre de ventana (s) | CyberFlow: escritura de la señal (s) | Suricata: 1.ª alerta contada (s, tiempo del paquete) | Qué alerta contó |", "|---|---|---|---|---|---|"]
    qa = {"dns_inusual": "ninguna", "inundacion_http": "SID 2221010 (evento de decodificación)", "fuerza_bruta_http": "SID 2221010 (evento de decodificación)", "escaneo_sostenido": "SID 2010937 `ET SCAN … mySQL port 3306` (firma ET)", "escaneo_breve": "ninguna"}
    for fam in FAMS + ["TOTAL"]:
        rs = E if fam == "TOTAL" else [r for r in E if r["familia"] == fam]
        amb = [r for r in rs if r["suri_P_primera_s"] != ""]
        if fam == "TOTAL": amb = [r for r in E if r["suri_P_primera_s"] != ""]
        L.append("| %s | %d | %s | %s | %s | %s |" % (("**Comparables (ambos alertan)**" if fam == "TOTAL" else fam), len(amb), med([f(r["cf_HIB01_cierre_ventana_s"]) for r in (amb if fam == "TOTAL" else rs)]),
                  med([f(r["cf_HIB01_disponibilidad_s"]) for r in (amb if fam == "TOTAL" else rs)]), med([f(r["suri_P_primera_s"]) for r in amb]), "—" if fam == "TOTAL" else qa[fam]))
    return "\n".join(L)


def coincidencias():
    L = ["| Lectura | Criterio de CyberFlow | Regla de Suricata | Ambos | Solo CyberFlow | Solo Suricata | Ninguno |", "|---|---|---|---|---|---|---|"]
    for nom, cf, su, key in (("A (principal)", "tiempo de datos", "regla fijada", "coincidencia_datos_regla_fijada"), ("B", "disponibilidad (`s50`)", "regla fijada", "coincidencia_disponibilidad_regla_fijada"),
                             ("C", "tiempo de datos", "solo firmas ET Open", "coincidencia_datos_solo_ET"), ("D", "disponibilidad (`s50`)", "solo firmas ET Open", "coincidencia_disponibilidad_solo_ET")):
        c = collections.Counter(r[key] for r in E)
        L.append("| %s | %s | %s | %d | %d | %d | %d |" % (nom, cf, su, c["ambos"], c["solo_CyberFlow"], c["solo_Suricata"], c["ninguno"]))
    return "\n".join(L)


def control():
    n = len(U); wins = sorted({u["window_end_utc"] for u in U})
    L = ["| Detector | Unidades entidad–ventana marcadas (de %s) | Ventanas de 10 s con al menos una unidad marcada (de %d) |" % (format(n, ",").replace(",", "."), len(wins)), "|---|---|---|"]
    res = {}
    for nom, key in (("CyberFlow `HIB_0.01` (principal)", "cf_HIB01"), ("CyberFlow `IF_0.01`", "cf_IF01"), ("CyberFlow `HEUR`", "cf_HEUR"), ("CyberFlow `HIB_0.03` (sensibilidad)", "cf_HIB03"),
                     ("Suricata, HOME_NET principal", "suricata_principal_marcado"), ("Suricata, HOME_NET original (sensibilidad)", "suricata_s1_marcado")):
        m = [u for u in U if int(u[key])]; w = {u["window_end_utc"] for u in m}; res[key] = (len(m), len(w))
        L.append(("| %s | " % nom) + ("%d (%.2f %%) | %d (%.1f %%) |" % (len(m), 100 * len(m) / n, len(w), 100 * len(w) / len(wins))).replace(".", ","))
    return "\n".join(L), res


if __name__ == "__main__":
    cob, c = cobertura(); ctl, r = control()
    print("## Cobertura (Panel A)\n\n" + cob + "\n\n## Tiempos (Panel B)\n\n" + tiempos() + "\n\n## Coincidencias\n\n" + coincidencias() + "\n\n## Control\n\n" + ctl)
    esperado = {("TOTAL", "CyberFlow `HIB_0.01`, tiempo de datos"): (21, 21), ("TOTAL", "CyberFlow `HIB_0.01`, disponibilidad (`s50`)"): (20, 21), ("TOTAL", "Suricata, regla fijada"): (15, 21), ("TOTAL", "Suricata, solo firmas ET Open"): (5, 21)}
    esperado_ctl = {"cf_HIB01": (54, 54), "cf_IF01": (54, 54), "cf_HEUR": (0, 0), "cf_HIB03": (200, 140), "suricata_principal_marcado": (79, 67), "suricata_s1_marcado": (79, 67)}
    mal = [k for k, v in esperado.items() if c[k] != v] + [k for k, v in esperado_ctl.items() if r[k] != v]
    pares = {(u["entidad"], u["window_end_utc"]) for u in U}
    assert len(pares) == len(U) == 2218 and len({u["window_end_utc"] for u in U}) == 181
    assert all(int(u["suricata_principal_marcado"]) <= 1 for u in U)
    print("\nVERIFICACION:", "OK (cifras de referencia reproducidas; 2218 pares unicos, 181 ventanas)" if not mal else "FALLA " + str(mal))
    sys.exit(1 if mal else 0)
