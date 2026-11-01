#!/usr/bin/env python3
"""Diagnóstico de la demora de la PRIMERA emisión real por episodio (revisión 3B; solo lee registros).

Descompone disponibilidad - inicio del ataque en tramos medidos con lo que está registrado:
  A  acumulación   window_end de la ventana emisora - inicio del ataque  (cuánto ataque cabe antes de cerrar la
                   ventana que emite; depende de la rejilla de 10 s y de cuánta actividad necesita la señal)
  B  espera PCAP   cierre del fichero PCAP que contiene window_end - window_end. Un fichero live-*.pcap de 15 s se
                   considera cerrado cuando existe el siguiente (motor: files[:-1]); su inicio sale del NOMBRE del
                   siguiente fichero (resolución 1 s). tcpdump -G rota al llegar el primer paquete tras los 15 s.
  C  espera ciclo  inicio_ciclo del ciclo que decidió - cierre del PCAP (fase de la rejilla de 10 s del motor)
  D  proceso       registro_escrito_en del ciclo - inicio_ciclo (lectura, características, puntuación, escritura)
A + B + C + D = disponibilidad - inicio. No registrado (incertidumbre declarada): el instante exacto de rotación
de tcpdump (solo hay resolución de 1 s en el nombre y mtime no se archivó), y el instante en que el motor vio el
fichero (solo se sabe que fue en ese ciclo o antes).
Además: ventanas de 0 paquetes del origen decididas tarde y los ciclos > 10 s.
"""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent.parent / "scripts"))
import analizar as an  # noqa: E402


def t_nombre(n: str) -> float:
    return datetime.strptime(n[5:19], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analisis", required=True, type=Path, help="analisis-3b.json")
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--ciclos", required=True, type=Path)
    ap.add_argument("--archivador", required=True, type=Path, help="archivar.log (nombres de los PCAP)")
    ap.add_argument("--marcas", required=True, type=Path)
    ap.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args()

    an_ = json.load(open(a.analisis, encoding="utf-8"))
    eps, _ = an.leer_marcas(a.marcas)
    regs, _, _ = an.leer_motor(a.motor)
    vivo = {(r["entity_ip"], r["window_end_utc"]): r for r in regs}
    cic = sorted((c for c in map(json.loads, open(a.ciclos, encoding="utf-8")) if c.get("event") == "ciclo"),
                 key=lambda c: c["inicio_ciclo"])
    por_ini = {round(c["inicio_ciclo"], 6): c for c in cic}
    nombres = sorted(set(re.findall(r"OK (live-\d{14}\.pcap)", a.archivador.read_text(encoding="utf-8"))))
    tp = sorted(t_nombre(n) for n in nombres)
    origen = "10.10.20.30"

    def cierre_pcap(w):
        """Inicio del primer fichero que empieza DESPUÉS de w (el que contiene w queda cerrado entonces)."""
        return next((t for t in tp if t > w), None)

    filas = []
    for eid, c in an_["episodios"].items():
        ep = eps[eid]
        ini, fin = ep["inicio_ep"], ep["fin_ep"]
        er = c["emisiones_reales"]
        det = [d for d in er.get("detalle", []) if d.get("atribucion") == "atribuible"]
        f = {"episodio": eid, "en_poblacion_principal_revisada": c["en_poblacion_principal"],
             "inicio_utc": an.iso(ini), "duracion_ataque_s": round(fin - ini, 1)}
        if det:
            p = min(det, key=lambda d: (an.ep_iso(d["disponible_utc"]), d["window_end_utc"]))
            r = vivo[(origen, p["window_end_utc"])]
            w = r["_wend"]; ci = float(r["inicio_ciclo"]); cy = por_ini.get(round(ci, 6))
            esc = float(cy["registro_escrito_en"]) if cy else r["_logged"]
            cp = cierre_pcap(w)
            disp = an.ep_iso(p["disponible_utc"])
            f.update(primera_emision={"window_end_utc": p["window_end_utc"], "componente": p["componente_emisor"],
                                      "decision": p["decision"], "oportuna": p["oportuna"],
                                      "disponible_desde_inicio_s": round(disp - ini, 2),
                                      "fin_menos_inicio_s": round(fin - ini, 2)},
                     tramos_s={"A_acumulacion": round(w - ini, 2),
                               "B_espera_pcap": round(cp - w, 2) if cp else None,
                               "C_espera_ciclo": round(ci - cp, 2) if cp else None,
                               "D_proceso": round(esc - ci, 2)},
                     ciclo={"inicio_utc": an.iso(ci), "duracion_s": cy.get("duracion_s") if cy else None,
                            "marca_pcap_utc": an.iso(float(r["marca_pcap"]))},
                     suma_comprobada=bool(cp) and abs((w - ini) + (cp - w) + (ci - cp) + (esc - ci) - (disp - ini)) < 0.01)
        else:
            f["primera_emision"] = None
        # ventanas del episodio sin paquetes del origen decididas tarde
        tard = [v for v in c["ventanas"] if v.get("estado") == "decidida_tardia"]
        f["tardias"] = len(tard)
        f["tardias_sin_paquetes_del_origen"] = sum(1 for v in tard if (vivo.get((origen, v["window_end_utc"])) or {})
                                                   .get("_pk10", 1) == 0)
        if tard:
            f["tardias_disponibles_utc"] = sorted({v["disponible_utc"][11:19] for v in tard})
        filas.append(f)

    # siguiente actividad de la Kali tras cada episodio (para explicar las tardías sin paquetes)
    for f in filas:
        if f.get("tardias"):
            ep = eps[f["episodio"]]
            sig = min((r["_wend"] for r in regs if r["entity_ip"] == origen and r["_pk10"] > 0
                       and r["_wend"] > ep["fin_ep"] + 60), default=None)
            f["siguiente_ventana_kali_con_paquetes_utc"] = an.iso(sig) if sig else None

    largos = [{"inicio_utc": an.iso(c["inicio_ciclo"]), "duracion_s": c["duracion_s"],
               "etapas_s": c.get("etapas_s"), "pcaps_nuevos": c.get("pcaps_nuevos"),
               "paquetes_anillo": c.get("paquetes_anillo"), "filas_construidas": c.get("filas_construidas"),
               "lineas_eve_nuevas": c.get("lineas_eve_nuevas"), "decididas": c.get("decididas")}
              for c in cic if (c.get("duracion_s") or 0) > 10]
    dur = sorted(c["duracion_s"] for c in cic if an._numero(c.get("duracion_s")))
    lat = sorted(c["inicio_ciclo"] - b["inicio_ciclo"] for b, c in zip(cic, cic[1:]))
    out = {"episodios": filas, "ciclos_mas_de_10s": largos,
           "ciclos": {"n": len(cic), "duracion_p50": dur[len(dur) // 2], "duracion_p99": dur[int(.99 * (len(dur) - 1))],
                      "duracion_max": dur[-1], "latido_p50": lat[len(lat) // 2], "latido_max": lat[-1]},
           "pcap": {"ficheros": len(tp), "paso_p50": sorted(b - x for x, b in zip(tp, tp[1:]))[len(tp) // 2]}}
    a.salida.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"ciclos_mas_de_10s": len(largos), **out["ciclos"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
