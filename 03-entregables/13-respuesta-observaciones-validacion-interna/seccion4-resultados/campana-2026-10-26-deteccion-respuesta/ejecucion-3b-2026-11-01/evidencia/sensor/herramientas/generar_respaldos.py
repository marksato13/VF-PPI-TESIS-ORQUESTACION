#!/usr/bin/env python3
"""Genera los RESPALDOS por episodio y el descriptor de verificar_integridad.py a partir de evidencias reales
(corre en el sensor, donde están los PCAP archivados; solo lectura de las fuentes).

Cada respaldo es un JSON que identifica campaña, episodio y periodo, y contiene los VALORES medidos de los que se
deriva el requisito. Nada se declara con un booleano sin medición:
  cobertura   previa_s / posterior_s = continuidad medida (mínimo entre el registro del motor, huecos <= 20 s, y la
              secuencia de PCAP archivados, ficheros de 15 s sin huecos); durante_completa = analizar.cobertura()
              (motor continuo en [inicio, fin+60] y todas las anclas de la Kali); faltantes = huecos de la secuencia de
              PCAP y ficheros PERDIDOS del archivador en el periodo; continuidad_sin_huecos.
  captura     errores del archivador en el periodo y cambios del servicio de captura; paquetes_descartados SOLO si se
              aporta una medición del proceso tcpdump (--descartes-tcpdump); si no, null (no medido) y el requisito
              no queda verificado. kernel_drops de Suricata (EVE) se informa aparte, con su alcance.
  reinicios   ActiveEnterTimestamp/NRestarts de ppi-motor, ppi-motor-capture y suricata al inicio y al final.
  relojes     mediciones p34 (sesión persistente frente al bastión) más cercanas al episodio, y chrony del bastión.
Ficheros: pcap = manifiesto por episodio (nombre y sha256 de cada PCAP del periodo, recalculado y contrastado con el
sha256 que registró el archivador); eve, decisiones y caracteristicas = copias de la campaña.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analizar as an  # noqa: E402

TOL = an.TOL_CONTINUIDAD_S
PCAP_S = 15
ANTES, DESPUES = 120.0, 90.0
BUSQUEDA_S = 900.0
RE_P34 = re.compile(r"^\s*\[(\S+)\]\s+(\S+)\s+mejor desfase=([+-][\d.]+) s inc=\+-([\d.]+) s")
RE_P34_INI = re.compile(r"inicio=(\S+)")
RE_CHRONY = re.compile(r"System time\s*:\s*([\d.]+) seconds (slow|fast)")
RE_DISP = re.compile(r"Root dispersion\s*:\s*([\d.]+)")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def t_pcap(p: Path) -> float:
    return datetime.strptime(p.name[5:19], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()


def continuidad(ts: list[float], centro_ini: float, centro_fin: float, paso: float):
    """Segundos continuos (huecos <= paso) antes de centro_ini y después de centro_fin, y hueco máximo dentro."""
    ts = sorted(ts)
    if not ts or ts[0] > centro_ini + paso or ts[-1] < centro_fin - paso:
        return 0.0, 0.0, None
    dentro = [t for t in ts if centro_ini - paso <= t <= centro_fin + paso]
    hueco = max((b - a for a, b in zip(dentro, dentro[1:])), default=0.0)
    i = max(k for k, t in enumerate(ts) if t <= centro_ini + paso)
    a = i
    while a > 0 and ts[a] - ts[a - 1] <= paso and centro_ini - ts[a - 1] <= BUSQUEDA_S:
        a -= 1
    j = min(k for k, t in enumerate(ts) if t >= centro_fin - paso)
    b = j
    while b < len(ts) - 1 and ts[b + 1] - ts[b] <= paso and ts[b + 1] - centro_fin <= BUSQUEDA_S:
        b += 1
    return max(0.0, centro_ini - ts[a]), max(0.0, ts[b] - centro_fin), hueco


def leer_p34(path: Path):
    meds, ini, bastion = [], None, []
    blo = None
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = RE_P34_INI.search(ln)
        if "p10b relojes" in ln and m:
            blo = an.ep_iso(m.group(1)); continue
        m = RE_CHRONY.search(ln)
        if m and blo is not None:
            v = float(m.group(1)) * (-1 if m.group(2) == "slow" else 1)
            bastion.append({"host": "bastion", "referencia": "NTP (chrony del bastión)", "momento": blo,
                            "desfase_s": v, "incertidumbre_s": None}); continue
        m = RE_DISP.search(ln)
        if m and bastion and bastion[-1]["momento"] == blo and bastion[-1]["incertidumbre_s"] is None:
            bastion[-1]["incertidumbre_s"] = float(m.group(1)); continue
        m = RE_P34.match(ln)
        if m:
            meds.append({"host": m.group(2), "referencia": "bastion (p34, sesión SSH persistente, 9 muestras)",
                         "momento": an.ep_iso(m.group(1)), "desfase_s": float(m.group(3)),
                         "incertidumbre_s": float(m.group(4))})
    return meds + [b for b in bastion if b["incertidumbre_s"] is not None]


def servicios(path: Path) -> dict:
    out, cur = {}, None
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("Id="):
            cur = ln[3:]; out[cur] = {}
        elif "=" in ln and cur:
            k, v = ln.split("=", 1); out[cur][k] = v
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marcas", required=True, type=Path)
    ap.add_argument("--motor", required=True, type=Path)
    ap.add_argument("--eve", required=True, type=Path)
    ap.add_argument("--caracteristicas", required=True, type=Path)
    ap.add_argument("--pcap-dir", required=True, type=Path)
    ap.add_argument("--relojes", required=True, type=Path, help="salida acumulada de p34_relojes.sh")
    ap.add_argument("--servicios-inicio", required=True, type=Path)
    ap.add_argument("--servicios-fin", required=True, type=Path)
    ap.add_argument("--descartes-tcpdump", type=Path, help="JSON con la medición del proceso tcpdump, si existe")
    ap.add_argument("--suricata-stats", type=Path, help="JSON de capture.kernel_drops de Suricata por instante")
    ap.add_argument("--campana", default="deteccion-respuesta-2026-10-26")
    ap.add_argument("--salida-dir", required=True, type=Path)
    a = ap.parse_args()

    eps, _ = an.leer_marcas(a.marcas)
    regs, _, _ = an.leer_motor(a.motor)
    ref = {"archivo": str(a.motor), "sha256": sha256(a.motor)}
    ne = an.leer_no_evaluadas(a.motor, regs, ref)["vigentes"]
    origen = "10.10.20.30"
    kali = [r for r in regs if r["entity_ip"] == origen]
    ne_kali = [e for e in ne if e.get("entity_ip") == origen]
    tlog = sorted(r["_logged"] for r in regs)

    pcaps = sorted(a.pcap_dir.glob("live-*.pcap"), key=lambda p: p.name)
    tp = [t_pcap(p) for p in pcaps]
    archlog = (a.pcap_dir / "archivar.log").read_text(encoding="utf-8", errors="replace").splitlines()
    sha_arch = {}
    for ln in archlog:
        m = re.search(r" OK (live-\d{14}\.pcap) \(\d+ bytes\) sha=([0-9a-f]{64})", ln)
        if m:
            sha_arch[m.group(1)] = m.group(2)
    fallos = [ln for ln in archlog if " FALLO " in ln]

    relojes = leer_p34(a.relojes)
    s_ini, s_fin = servicios(a.servicios_inicio), servicios(a.servicios_fin)
    desc = json.loads(a.descartes_tcpdump.read_text(encoding="utf-8")) if a.descartes_tcpdump else None
    sstats = json.loads(a.suricata_stats.read_text(encoding="utf-8")) if a.suricata_stats else []

    rutas_comunes = {"eve": str(a.eve), "decisiones": str(a.motor), "caracteristicas": str(a.caracteristicas)}
    hashes_comunes = {k: sha256(Path(v)) for k, v in rutas_comunes.items()}
    a.salida_dir.mkdir(parents=True, exist_ok=True)
    descriptor = {"_nota": "generado por generar_respaldos.py con evidencias de la campaña A", "episodios": []}

    for eid, ep in sorted(eps.items(), key=lambda kv: kv[1]["inicio_ep"]):
        ini, fin = ep["inicio_ep"], ep["fin_ep"]
        d = a.salida_dir / eid
        d.mkdir(exist_ok=True)
        e_desc = {"episodio_id": eid, "campana": a.campana, "intervalo": {"inicio": ini, "fin": fin}}
        if fin is None:
            descriptor["episodios"].append({**e_desc, "intervalo": {"inicio": ini, "fin": ini}}); continue
        per = {"inicio": ini - ANTES, "fin": fin + DESPUES}
        base = {"campana": a.campana, "episodio": eid, "periodo": per, "origen": "sensor (automatico)"}

        # PCAP del periodo (con el fichero que contiene el borde inicial)
        sel = [(p, t) for p, t in zip(pcaps, tp) if per["inicio"] - PCAP_S < t <= per["fin"]]
        man, distintos = [], []
        for p, t in sel:
            h = sha256(p)
            man.append({"fichero": p.name, "bytes": p.stat().st_size, "sha256": h,
                        "sha256_archivador": sha_arch.get(p.name)})
            if sha_arch.get(p.name) != h:
                distintos.append(p.name)
        mp = d / "pcap-manifiesto.json"
        mp.write_text(json.dumps({**base, "fuente": "pcap", "ficheros": man}, indent=1), encoding="utf-8")

        huecos = [f"{sel[k][0].name}->{sel[k + 1][0].name} ({sel[k + 1][1] - sel[k][1]:.0f} s)"
                  for k in range(len(sel) - 1) if sel[k + 1][1] - sel[k][1] > PCAP_S + 1]
        perdidos = [ln for ln in archlog if "PERDIDO" in ln and any(n["fichero"] in ln for n in man)]
        m_prev, m_post, m_hueco = continuidad(tlog, ini, fin + an.HORIZONTE_S, TOL)
        p_prev, p_post, _ = continuidad(tp, ini, fin, PCAP_S + 1)
        cov = an.cobertura(ep, regs, kali, ne_kali)
        cobertura = {**base, "fuente": "motor_decision.log + secuencia de PCAP archivados",
                     "previa_s": round(min(m_prev, p_prev), 1), "posterior_s": round(min(m_post + an.HORIZONTE_S, p_post), 1),
                     "detalle": {"motor_previa_s": round(m_prev, 1), "motor_posterior_desde_fin_mas_60_s": round(m_post, 1),
                                 "pcap_previa_s": round(p_prev, 1), "pcap_posterior_s": round(p_post, 1),
                                 "hueco_motor_max_s": m_hueco, "analizar_cobertura": cov},
                     "durante_completa": bool(cov.get("suficiente")),
                     "faltantes": huecos + perdidos,
                     "continuidad_sin_huecos": not huecos and not perdidos and m_hueco is not None and m_hueco <= TOL}
        (d / "cobertura.json").write_text(json.dumps(cobertura, ensure_ascii=False, indent=1), encoding="utf-8")

        errores = [{"desc": f"archivador: {ln}", "afecta_fuentes": True} for ln in fallos
                   if per["inicio"] <= an.ep_iso(ln.split()[0]) <= per["fin"]]
        errores += [{"desc": f"sha256 de {n} distinto del registrado por el archivador", "afecta_fuentes": True}
                    for n in distintos]
        cap_i, cap_f = s_ini.get("ppi-motor-capture.service", {}), s_fin.get("ppi-motor-capture.service", {})
        if cap_i.get("MainPID") != cap_f.get("MainPID"):
            errores.append({"desc": "ppi-motor-capture cambió de PID durante la campaña", "afecta_fuentes": True})
        sur = [x for x in sstats if per["inicio"] <= x["momento"] <= per["fin"]]
        sur_delta = (sur[-1]["kernel_drops"] - sur[0]["kernel_drops"]) if len(sur) >= 2 else None
        if sur_delta:
            errores.append({"desc": f"Suricata kernel_drops +{sur_delta} en el periodo (afecta a EVE)",
                            "afecta_fuentes": True})
        descartados, alcance = None, "no medido: tcpdump corre con -G sin estadísticas en vivo"
        if desc and desc.get("dropped_by_kernel") is not None and desc.get("proceso_desde", 1e18) <= per["inicio"] \
                and desc.get("momento", 0) >= per["fin"]:
            if desc["dropped_by_kernel"] == 0:
                descartados, alcance = 0, "medido: contador acumulado del proceso tcpdump = 0 al final"
            else:
                alcance = (f"medido {desc['dropped_by_kernel']} acumulados en todo el proceso; no atribuible al "
                           "periodo del episodio")
        captura = {**base, "fuente": "archivar.log + estado del servicio de captura + mediciones de descarte",
                   "errores": errores, "paquetes_descartados": descartados, "alcance_descartes": alcance,
                   "suricata_kernel_drops_delta_periodo": sur_delta,
                   "suricata_mediciones_en_periodo": len(sur)}
        (d / "captura.json").write_text(json.dumps(captura, ensure_ascii=False, indent=1), encoding="utf-8")

        rein = {}
        for u, nom in (("ppi-motor.service", "motor"), ("ppi-motor-capture.service", "captura"),
                       ("suricata.service", "suricata")):
            i, f = s_ini.get(u, {}), s_fin.get(u, {})
            rein[nom] = [] if (i and f and i.get("ActiveEnterTimestamp") == f.get("ActiveEnterTimestamp")
                               and i.get("NRestarts") == f.get("NRestarts")) else \
                [{"inicio": i, "fin": f, "recuperado": False, "nota": "cambio de estado o sin datos"}]
        (d / "reinicios.json").write_text(json.dumps({**base, "fuente": "systemctl show al inicio y al final",
                                                      "reinicios": rein}, ensure_ascii=False, indent=1), encoding="utf-8")

        centro = (ini + fin) / 2
        meds = []
        for h in ("sensor", "kali", "srv-dmz", "bastion"):
            c = [m for m in relojes if m["host"] == h]
            if c:
                meds.append(min(c, key=lambda m: abs(m["momento"] - centro)))
        (d / "relojes.json").write_text(json.dumps({**base, "fuente": "p34_relojes.sh", "tolerancia_s": 1.0,
                                                    "requeridos": ["sensor", "kali", "srv-dmz", "bastion"],
                                                    "mediciones": meds}, ensure_ascii=False, indent=1), encoding="utf-8")

        descriptor["episodios"].append({
            **e_desc,
            "rutas": {"pcap": str(mp), **rutas_comunes},
            "hashes_esperados": {"pcap": sha256(mp), **hashes_comunes},
            "respaldos": {k: {"ruta": str(d / f"{k}.json")} for k in ("cobertura", "captura", "reinicios", "relojes")}})
    (a.salida_dir / "descriptor-integridad.json").write_text(json.dumps(descriptor, ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
    print(f"{len(descriptor['episodios'])} episodios -> {a.salida_dir / 'descriptor-integridad.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
