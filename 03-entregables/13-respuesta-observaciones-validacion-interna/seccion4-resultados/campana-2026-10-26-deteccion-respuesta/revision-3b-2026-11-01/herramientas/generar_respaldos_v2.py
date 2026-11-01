#!/usr/bin/env python3
"""generar_respaldos v2 — REVISIÓN POSTERIOR A CONOCER LOS RESULTADOS del paso 3B (ver ../CRITERIOS-REVISION.md).

Cambia SOLO el respaldo de cobertura/continuidad. Captura, reinicios, relojes y manifiesto PCAP se generan con el
mismo código que generar_respaldos.py (se importa; no se modifica).

Defecto que corrige: la v1 medía la continuidad con los instantes de escritura (logged_at) de TODAS las decisiones
con tolerancia 20 s (analizar.TOL_CONTINUIDAD_S) y llamaba a analizar.cobertura(), que exige lo mismo. El motor
incremental no escribe en un ciclo sin ventanas listas (marca_pcap < window_end hasta la siguiente rotación PCAP de
15 s), así que un hueco de escritura de 20,2 s con todas las ventanas presentes se contaba como pérdida.
La v2 NO sube la tolerancia: deja de usar la cadencia de escritura (pasa a informativa) y mide, por intervalo
(previa [ini-120, ini], durante [ini, fin+60], posterior [fin, fin+90]) y por separado:
  pcap           secuencia de live-*.pcap que cubre el intervalo, hueco entre inicios <= 16 s (15 s + 1)
  eve            pulso de eventos 'stats' del EVE (stats.interval = 8 s) sin hueco >= 16 s
  procesamiento  todas las ventanas requeridas por el inventario (todas las entidades) con window_end en el
                 intervalo decididas en vivo, ninguna ausente ni no evaluada, con marca_pcap y marca_eve >= window_end;
                 fuera del rango del inventario -> no verificado
  anclas_kali    (solo durante) todas las anclas de la Kali en (ini, fin+60) decididas en vivo
continuidad = pcap + eve + procesamiento sobre todo [ini-120, fin+90].
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
for p in (AQUI, AQUI.parent.parent / "scripts"):          # en el sensor, todo en el mismo directorio
    sys.path.insert(0, str(p))
import analizar as an  # noqa: E402
import analizar_3b as a3  # noqa: E402
import generar_respaldos as gr  # noqa: E402

VERSION = "v2-revision-posterior-2026-11-01"
PCAP_S = 15.0
PCAP_TOL_S = PCAP_S + 1.0
EVE_STATS_S = 8.0
EVE_MAX_HUECO_S = 2 * EVE_STATS_S
ANTES, DESPUES, HOR = gr.ANTES, gr.DESPUES, an.HORIZONTE_S


# ------------------------------------------------------------------ componentes (funciones puras, probadas)
def comp_pcap(tp: list, a: float, b: float, perdidos=()) -> dict:
    """tp: inicios (epoch) de los ficheros live-*.pcap. Cubre [a, b] si hay un fichero que empieza <= a, el último
    llega a b (inicio + 15 >= b) y ningún hueco entre inicios consecutivos supera 16 s."""
    tp = sorted(tp)
    sel = [t for t in tp if a - PCAP_S < t <= b]
    if not sel:
        return {"ok": False, "motivo": "sin ficheros PCAP en el intervalo", "ficheros": 0}
    huecos = [round(y - x, 1) for x, y in zip(sel, sel[1:]) if y - x > PCAP_TOL_S]
    cubre_ini, cubre_fin = sel[0] <= a, sel[-1] + PCAP_S >= b
    ok = cubre_ini and cubre_fin and not huecos and not perdidos
    mot = "ok" if ok else "; ".join(m for m, c in (
        ("no cubre el inicio", not cubre_ini), ("no cubre el fin", not cubre_fin),
        (f"huecos {huecos}", bool(huecos)), (f"perdidos {list(perdidos)}", bool(perdidos))) if c)
    return {"ok": ok, "motivo": mot, "ficheros": len(sel), "primero_utc": an.iso(sel[0]),
            "ultimo_utc": an.iso(sel[-1]), "hueco_max_s": round(max((y - x for x, y in zip(sel, sel[1:])),
                                                                     default=0.0), 1)}


def comp_eve(ts: list, a: float, b: float) -> dict:
    """ts: instantes de los eventos 'stats' del EVE. Cubre [a, b] si hay uno <= a, otro >= b y entre ellos ningún
    hueco >= 16 s. Prueba que Suricata siguió escribiendo; NO prueba ausencia de descartes (eso es captura)."""
    ts = sorted(ts)
    antes = [t for t in ts if t <= a]
    despues = [t for t in ts if t >= b]
    if not antes or not despues:
        return {"ok": False, "motivo": "el pulso stats no cubre " + ("el inicio" if not antes else "el fin"),
                "eventos": sum(1 for t in ts if a <= t <= b)}
    seq = [antes[-1]] + [t for t in ts if a < t < b] + [despues[0]]
    hmax = max((y - x for x, y in zip(seq, seq[1:])), default=0.0)
    ok = hmax < EVE_MAX_HUECO_S
    return {"ok": ok, "motivo": "ok" if ok else f"hueco del pulso stats {hmax:.1f} s >= {EVE_MAX_HUECO_S:.0f} s",
            "eventos": len(seq), "hueco_max_s": round(hmax, 1)}


def comp_procesamiento(a: float, b: float, inv, vivo: dict, ne_vivo: dict) -> dict:
    """Ventanas requeridas por el inventario (todas las entidades) con window_end en [a, b]."""
    if inv is None:
        return {"ok": False, "motivo": "sin inventario: no se puede saber si faltan ventanas"}
    if a < inv["desde"] or b > inv["hasta"]:
        return {"ok": False, "motivo": f"el intervalo [{an.iso(a)}, {an.iso(b)}] sale del inventario "
                                       f"[{an.iso(inv['desde'])}, {an.iso(inv['hasta'])}]: no verificado",
                "fuera_del_inventario": True}
    req = a3.requeridas_inventario(inv, desde=a, hasta=b)
    aus, ne, sin_marca, dec = [], [], [], 0
    for k in sorted(req, key=lambda k: (k[1], k[0])):
        r = vivo.get(k)
        if r is None:
            (ne if k in ne_vivo else aus).append(f"{k[0]}|{k[1]}")
            continue
        dec += 1
        w = r["_wend"]
        mp, me = r.get("marca_pcap"), r.get("marca_eve")
        if not (an._numero(mp) and an._numero(me) and mp >= w and me >= w):
            sin_marca.append(f"{k[0]}|{k[1]}")
    ok = bool(req) and not aus and not ne and not sin_marca
    mot = "ok" if ok else "; ".join(m for m, c in (
        ("ninguna ventana requerida", not req), (f"{len(aus)} ausentes", bool(aus)),
        (f"{len(ne)} no evaluadas", bool(ne)), (f"{len(sin_marca)} sin marcas >= window_end", bool(sin_marca))) if c)
    return {"ok": ok, "motivo": mot, "requeridas": len(req), "decididas": dec, "ausentes": aus[:20],
            "no_evaluadas": ne[:20], "sin_marcas": sin_marca[:20],
            "n_ausentes": len(aus), "n_no_evaluadas": len(ne), "n_sin_marcas": len(sin_marca)}


def comp_anclas_kali(ep: dict, origen: str, inv, vivo: dict, ne_vivo: dict) -> dict:
    claves, cob = a3.ventanas_esperadas_episodio(ep, origen, inv, vivo, ne_vivo)
    falt = [k for k in claves if k not in vivo]
    ok = bool(claves) and not falt and cob.get("cubre", False)
    return {"ok": ok, "motivo": "ok" if ok else (f"{len(falt)}/{len(claves)} anclas sin decisión" if falt else
                                                 "el inventario no cubre las anclas"),
            "anclas": len(claves), "sin_decision": [f"{k[0]}|{k[1]}" for k in falt][:20]}


def intervalo(nombre, a, b, tp, ts_eve, inv, vivo, ne_vivo, perdidos=(), extra=None) -> dict:
    c = {"rango_utc": [an.iso(a), an.iso(b)], "duracion_s": round(b - a, 1),
         "pcap": comp_pcap(tp, a, b, perdidos), "eve": comp_eve(ts_eve, a, b),
         "procesamiento": comp_procesamiento(a, b, inv, vivo, ne_vivo)}
    if extra is not None:
        c["anclas_kali"] = extra
    c["verificado"] = all(c[k]["ok"] for k in ("pcap", "eve", "procesamiento") + (("anclas_kali",) if extra else ()))
    return c


def hueco_escritura(tlog: list, a: float, b: float):
    d = sorted(t for t in tlog if a <= t <= b)
    return round(max((y - x for x, y in zip(d, d[1:])), default=0.0), 2) if d else None


def cobertura_v2(base, ep, origen, tp, ts_eve, inv, vivo, ne_vivo, tlog, perdidos=(), huecos_pcap=()) -> dict:
    ini, fin = ep["inicio_ep"], ep["fin_ep"]
    prev = intervalo("previa", ini - ANTES, ini, tp, ts_eve, inv, vivo, ne_vivo, perdidos)
    dur = intervalo("durante", ini, fin + HOR, tp, ts_eve, inv, vivo, ne_vivo, perdidos,
                    extra=comp_anclas_kali(ep, origen, inv, vivo, ne_vivo))
    post = intervalo("posterior", fin, fin + DESPUES, tp, ts_eve, inv, vivo, ne_vivo, perdidos)
    cont = intervalo("continuidad", ini - ANTES, fin + DESPUES, tp, ts_eve, inv, vivo, ne_vivo, perdidos)
    return {**base, "fuente": "PCAP archivados + pulso stats del EVE + decisiones en vivo frente al inventario",
            "version_criterio": VERSION,
            "intervalos": {"previa": prev, "durante": dur, "posterior": post},
            "continuidad": cont,
            # campos de la v1, derivados de los componentes (el verificador v2 NO los usa sin desglose)
            "previa_s": ANTES if prev["verificado"] else 0.0,
            "posterior_s": DESPUES if post["verificado"] else 0.0,
            "durante_completa": dur["verificado"], "continuidad_sin_huecos": cont["verificado"],
            "faltantes": list(huecos_pcap) + list(perdidos),
            "informativo": {"hueco_escritura_max_s": hueco_escritura(tlog, ini - ANTES, fin + DESPUES),
                            "nota": "cadencia de escritura del registro: NO clasifica (ciclo sin ventanas listas "
                                    "no escribe); la pérdida solo se establece contra el inventario"}}


def leer_stats_eve(path: Path) -> list:
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            if '"event_type":"stats"' not in ln:
                continue
            try:
                out.append(an.ep_iso(json.loads(ln)["timestamp"]))
            except (ValueError, KeyError, TypeError):
                continue
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("marcas", "motor", "eve", "caracteristicas", "pcap-dir", "relojes", "servicios-inicio",
              "servicios-fin", "inventario", "salida-dir"):
        ap.add_argument("--" + k, required=True, type=Path)
    ap.add_argument("--inventario-rango", required=True)
    ap.add_argument("--historia", type=float, default=230.0)
    ap.add_argument("--descartes-tcpdump", type=Path)
    ap.add_argument("--suricata-stats", type=Path)
    ap.add_argument("--campana", required=True)
    ap.add_argument("--origen", default="10.10.20.30")
    a = ap.parse_args()
    if a.salida_dir.exists():
        raise SystemExit(f"PARAR: existe {a.salida_dir}")

    # 1) v1 sin cambios (captura, reinicios, relojes, pcap-manifiesto, descriptor) en un directorio aparte
    v1 = a.salida_dir / "_v1"
    argv = [sys.argv[0], "--marcas", a.marcas, "--motor", a.motor, "--eve", a.eve, "--caracteristicas",
            a.caracteristicas, "--pcap-dir", a.pcap_dir, "--relojes", a.relojes, "--servicios-inicio",
            a.servicios_inicio, "--servicios-fin", a.servicios_fin, "--campana", a.campana, "--salida-dir", v1]
    if a.descartes_tcpdump:
        argv += ["--descartes-tcpdump", a.descartes_tcpdump]
    if a.suricata_stats:
        argv += ["--suricata-stats", a.suricata_stats]
    sys.argv = [str(x) for x in argv]
    gr.main()

    # 2) cobertura v2
    eps, _ = an.leer_marcas(a.marcas)
    regs, _, _ = an.leer_motor(a.motor)
    ref = {"archivo": str(a.motor), "sha256": gr.sha256(a.motor)}
    ne = an.leer_no_evaluadas(a.motor, regs, ref)["vigentes"]
    vivo = {(r["entity_ip"], r["window_end_utc"]): r for r in regs}
    ne_vivo = {e["_clave"]: e for e in ne}
    tlog = [r["_logged"] for r in regs]
    rango = tuple(map(an.como_epoch, a.inventario_rango.split(",")))
    inv = a3.leer_inventario(a.inventario, rango, a.historia)
    pcaps = sorted(a.pcap_dir.glob("live-*.pcap"), key=lambda p: p.name)
    tp = [gr.t_pcap(p) for p in pcaps]
    archlog = (a.pcap_dir / "archivar.log").read_text(encoding="utf-8", errors="replace").splitlines()
    ts_eve = leer_stats_eve(a.eve)

    desc = json.loads((v1 / "descriptor-integridad.json").read_text(encoding="utf-8"))
    desc["_nota"] = f"generado por generar_respaldos_v2.py ({VERSION}); captura/reinicios/relojes/pcap = v1"
    desc["inventario"] = {"fuente": str(a.inventario), "sha256": inv["sha256"],
                          "rango_utc": [an.iso(inv["desde"]), an.iso(inv["hasta"])]}
    for e in desc["episodios"]:
        eid = e["episodio_id"]
        ep = eps[eid]
        d = a.salida_dir / eid
        d.mkdir(parents=True, exist_ok=True)
        for k in ("captura", "reinicios", "relojes"):
            src = v1 / eid / f"{k}.json"
            (d / f"{k}.json").write_bytes(src.read_bytes())
            e["respaldos"][k]["ruta"] = str(d / f"{k}.json")
        if ep["fin_ep"] is None:
            continue
        man = json.loads((v1 / eid / "pcap-manifiesto.json").read_text(encoding="utf-8"))
        (d / "pcap-manifiesto.json").write_bytes((v1 / eid / "pcap-manifiesto.json").read_bytes())
        e["rutas"]["pcap"] = str(d / "pcap-manifiesto.json")
        nombres = {m["fichero"] for m in man["ficheros"]}
        perdidos = [ln for ln in archlog if "PERDIDO" in ln and any(n in ln for n in nombres)]
        base = {"campana": a.campana, "episodio": eid, "periodo": man["periodo"], "origen": "sensor (automatico)"}
        cob = cobertura_v2(base, ep, a.origen, tp, ts_eve, inv, vivo, ne_vivo, tlog, perdidos)
        v1cob = json.loads((v1 / eid / "cobertura.json").read_text(encoding="utf-8"))
        cob["faltantes"] = v1cob["faltantes"]                  # mismo cálculo que v1 (huecos PCAP + PERDIDO)
        cob["v1"] = {k: v1cob.get(k) for k in ("previa_s", "posterior_s", "durante_completa",
                                               "continuidad_sin_huecos")}
        cob["v1"]["hueco_motor_max_s"] = (v1cob.get("detalle") or {}).get("hueco_motor_max_s")
        (d / "cobertura.json").write_text(json.dumps(cob, ensure_ascii=False, indent=1), encoding="utf-8")
        e["respaldos"]["cobertura"]["ruta"] = str(d / "cobertura.json")
    (a.salida_dir / "descriptor-integridad.json").write_text(json.dumps(desc, ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
    print(f"{len(desc['episodios'])} episodios (v2) -> {a.salida_dir / 'descriptor-integridad.json'}; "
          f"stats EVE={len(ts_eve)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
