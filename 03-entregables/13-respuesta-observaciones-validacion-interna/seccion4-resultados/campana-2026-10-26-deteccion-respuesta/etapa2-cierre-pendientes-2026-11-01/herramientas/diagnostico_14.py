"""Diagnostico individual de las ventana_no_regenerada de un replay, independiente del motor.

Para cada (E, A) recalcula con las funciones congeladas (deduplicar_espejo, attribute_packets,
load_app_observations) sobre el PCAP ARCHIVADO del 3B y el segmento de EVE:
  - horizonte de alta (corte_incorporacion, del registro pendiente_cancelada del replay corregido)
  - horizonte propio [A-230, ...]
las observaciones de E en (A-60, A] (PCAP y EVE), los flujos de/hacia E en (A-60, A] con su
propietario e inicio en cada horizonte, y el estado que corresponde por la regla causal.
Uso (desde la raiz del repo del motor):
  python diagnostico_14.py archivo-pcap eve.json log_anterior log_corregido salida.json"""
import collections, datetime as dt, ipaddress, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "scripts/features")
import extract_multilayer_v3 as v3
v2 = v3.v2
pcap_dir, eve, log_ant, log_nuevo, salida = (Path(x) for x in sys.argv[1:6])
RED = ipaddress.ip_network("10.10.0.0/16")
EXC = {"10.10.60.11", "10.10.10.30", "10.10.60.2", "10.10.60.3", "10.10.60.10", "10.10.60.20", "10.10.60.21",
       "10.10.60.30", "10.10.60.40", "10.10.60.41", "10.10.60.50"}
H = 230
ts = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
iso = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S.%f")[:-3] if t else None


def leer(path, ev):
    return [r for r in map(json.loads, open(path, encoding="utf-8")) if r.get("event") == ev]


casos = leer(log_ant, "ventana_no_evaluada")
canc = {(r["entity_ip"], r["window_end_utc"]): r for r in leer(log_nuevo, "pendiente_cancelada")}
nuevas_ne = {(r["entity_ip"], r["window_end_utc"]): r for r in leer(log_nuevo, "ventana_no_evaluada")}
dec_nuevo = {(r["entity_ip"], r["window_end_utc"]) for r in leer(log_nuevo, "decision")}

# PCAP necesario (una sola lectura)
lo = min(ts(c["window_end_utc"]) for c in casos) - H - 120
hi = max(ts(c["window_end_utc"]) for c in casos) + 20
ctx = []
for f in sorted(pcap_dir.glob("live-*.pcap")):
    st = dt.datetime.strptime(f.stem[5:], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp()
    if st < lo - 60 or st > hi:
        continue
    for m, tr in v2.iter_pcap_frames(f):
        c = v3.parse_con_contexto(m, tr)
        if c is not None and c.packet.protocol not in (112, 240) and lo <= c.packet.timestamp <= hi:
            ctx.append(c)
ctx.sort(key=lambda c: c.packet.timestamp)
# EVE necesario
lineas = []
with open(eve, encoding="utf-8") as fh:
    for linea in fh:
        i = linea.find('"timestamp"')
        if i < 0:
            continue
        a = linea.find('"', i + 11); b = linea.find('"', a + 1)
        try:
            t = v2.parse_eve_timestamp(linea[a + 1:b])
        except ValueError:
            continue
        if lo <= t <= hi:
            lineas.append((t, linea.rstrip("\n")))


def obs_eve(ent, A):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        for t, l in lineas:
            if A - 61 <= t <= A + 1:
                tf.write(l + "\n")
    apps = v2.load_app_observations(Path(tf.name), RED)
    Path(tf.name).unlink()
    return sum(1 for o in apps if o.entity_ip == ent and A - 60 < o.timestamp <= A)


def horizonte(ent, A, corte):
    sel = [c for c in ctx if corte <= c.packet.timestamp <= A + 0.005]
    paq, _ = v3.deduplicar_espejo(sel)
    obs = v2.attribute_packets(paq, RED)
    e60 = [o for o in obs if o.entity_ip == ent and A - 60 < o.timestamp <= A]
    # paquetes de/hacia E en (A-60, A] y su propietario en este horizonte
    prop = collections.Counter(o.entity_ip for o in obs if A - 60 < o.timestamp <= A
                               and (o.peer_ip == ent) and o.entity_ip != ent)
    # flujos de/hacia E: primer paquete visible en el horizonte (quien lo envia fija el propietario)
    flujos = {}
    for p in paq:
        if ent not in (p.src_ip, p.dst_ip):
            continue
        k = v2.canonical_flow_key(p)
        flujos.setdefault(k, {"inicio": p.timestamp, "primer_emisor": p.src_ip, "n_en_ventana": 0})
        if A - 60 < p.timestamp <= A:
            flujos[k]["n_en_ventana"] += 1
    activos = [v for v in flujos.values() if v["n_en_ventana"]]
    return {"corte": iso(corte), "obs_pcap_E_60s": len(e60), "obs_pcap_E_30s": sum(o.timestamp > A - 30 for o in e60),
            "paquetes_de_E_atribuidos_a": dict(sorted(prop.items())),
            "flujos_activos": len(activos),
            "inicio_flujos_min": iso(min((v["inicio"] for v in activos), default=None)),
            "primer_emisor": sorted({v["primer_emisor"] for v in activos})}


filas = []
for c in casos:
    E, W = c["entity_ip"], c["window_end_utc"]
    A = ts(W)
    k = (E, W)
    cr = canc.get(k)
    corte_inc = cr["corte_incorporacion"] if cr else None
    propio = horizonte(E, A, A - H)
    alta = horizonte(E, A, corte_inc) if corte_inc is not None else None
    eve_n = obs_eve(E, A)
    registrable = propio["obs_pcap_E_60s"] > 0 or eve_n > 0
    propietarios = set(propio["paquetes_de_E_atribuidos_a"])
    filas.append({
        "entidad": E, "fin_ventana": W,
        "alta_pendiente_anterior": iso(c.get("pendiente_desde")), "expiro_anterior": iso(c.get("inicio_ciclo")),
        "motivo_anterior": c["motivo"],
        "alta_pendiente_corregido": iso(cr["pendiente_desde"]) if cr else None,
        "motivo_alta": "contenido de E en (A-60, A] segun la atribucion de la ultima ancla tratada",
        "horizonte_alta": alta, "horizonte_propio": propio, "obs_eve_E_60s": eve_n,
        "cambio_propietario": bool(alta and alta["obs_pcap_E_60s"] > 0 and propio["obs_pcap_E_60s"] == 0),
        "propietario_excluido": bool(propietarios and propietarios <= EXC),
        "estado_regla_causal": "requerida" if registrable else "no_registrable",
        "estado_corregido": ("cancelada" if k in canc else "decidida" if k in dec_nuevo
                             else ("no_evaluada:" + nuevas_ne[k]["motivo"]) if k in nuevas_ne else "sin_registro"),
        "coincide_motor": (cr is not None and cr["obs_pcap_propio"] == propio["obs_pcap_E_60s"]
                           and cr["obs_eve_propio"] == eve_n
                           and cr["paquetes_atribuidos_a"] == propio["paquetes_de_E_atribuidos_a"]) if cr else None,
    })
json.dump(filas, open(salida, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for f in filas:
    print(f["entidad"], f["fin_ventana"][11:19], "alta", f["alta_pendiente_anterior"],
          "| alta:", f["horizonte_alta"] and f["horizonte_alta"]["obs_pcap_E_60s"],
          "propio:", f["horizonte_propio"]["obs_pcap_E_60s"], "eve:", f["obs_eve_E_60s"],
          "| a:", f["horizonte_propio"]["paquetes_de_E_atribuidos_a"], "|", f["estado_regla_causal"],
          "->", f["estado_corregido"], "motor=", f["coincide_motor"])
