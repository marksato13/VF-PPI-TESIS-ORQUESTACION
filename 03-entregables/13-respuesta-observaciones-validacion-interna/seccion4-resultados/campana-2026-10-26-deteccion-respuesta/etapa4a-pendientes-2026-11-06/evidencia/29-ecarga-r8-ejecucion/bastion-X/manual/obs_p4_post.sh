set -u
# [BASTIÓN gadmin] Solo lecturas. O1, O6, O7, O8, O9, O10 de la observación fija P4 (ventana 04:50:00Z–05:50:00Z)
# + correlación completa de los rechazos firma_invalida de toda la traza.
D=${1:-1793940600}; A=${2:-1793944200}
O=~/evidencia-etapa4/observacion-p4-20261106T0450Z
W=$(mktemp -d)
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'sudo -n cat /var/lib/cyberflow/agente/traza.jsonl' > $W/agente.jsonl
tr -d '\000' < ~/relay-v2/traza.jsonl > $W/rele.jsonl
cp $W/agente.jsonl $O/traza-agente-copia.jsonl; cp $W/rele.jsonl $O/traza-rele-copia-sin-nul.jsonl
echo "######## p4 post $(date -u +%FT%TZ) ventana $D-$A"
python3 - $W/agente.jsonl $W/rele.jsonl $O/muestras.txt $D $A <<'EOF'
import json, sys, re, bisect
from collections import Counter
D, A = float(sys.argv[4]), float(sys.argv[5])
ag = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
re_ = []
for l in open(sys.argv[2]):
    try: re_.append(json.loads(l))
    except ValueError: pass
ent = [r for r in re_ if r.get("evento") == "reenvio" and (r.get("destinos") or {}).get("srv-dmz", {}).get("entregado_en")]
# ---------- O7/O8 en la ventana
ev = [r for r in ent if D <= r["destinos"]["srv-dmz"]["entregado_en"] < A]
print("O7 entregas del relé en la ventana:", len(ev), "modos:", Counter(r.get("entrega", "pareja") for r in ev))
seq_e = [r["secuencia"] for r in sorted(ev, key=lambda r: r["destinos"]["srv-dmz"]["entregado_en"])]
print("   secuencias entregadas", seq_e[:1], "…", seq_e[-1:], "orden creciente:", all(b > a for a, b in zip(seq_e, seq_e[1:])),
      "huecos:", [(a, b) for a, b in zip(seq_e, seq_e[1:]) if b - a != 1][:10])
agw = [a for a in ag if D <= a.get("recibido_en", a.get("t", 0)) < A + 5]
rec = sorted((a for a in agw if a["evento"] == "recepcion"), key=lambda a: a["recibido_en"])
acep = [a["secuencia"] for a in rec if a.get("estado") == "aceptado"]
print("   agente: recepciones", len(rec), "estados", Counter(a.get("estado") for a in rec))
print("   aceptadas en orden:", all(b > a for a, b in zip(acep, acep[1:])))
falt = sorted(set(seq_e) - set(acep))
print("   entregadas NO aceptadas:", len(falt), falt[:20])
print("O8 rechazos en la ventana:", Counter(a.get("motivo") for a in agw if a["evento"] == "rechazo"))
print("O10 eventos aplicacion (toda la traza):", sum(1 for a in ag if a["evento"] == "aplicacion"),
      "en la ventana:", sum(1 for a in agw if a["evento"] == "aplicacion"))
# retraso publicador->agente en la ventana
ret = sorted(a["recibido_en"] - a["generado"] for a in rec if a.get("generado") and a.get("estado") == "aceptado")
if ret:
    print("   retraso generado->aceptado (s): p50 %.3f p95 %.3f max %.3f" % (ret[len(ret)//2], ret[int(len(ret)*.95)], ret[-1]))
# ---------- muestras (O1, O6, O9, O10, publicador)
bloques = open(sys.argv[3]).read().split("### ")[1:]
ts, pids, fseq, libre, panel, rs, dr, apl, fi, pi, en = [], {}, [], [], Counter(), set(), set(), set(), set(), set(), set()
for b in bloques:
    t = float(b.split("\n", 1)[0].split()[1])
    if not (D - 60 <= t <= A + 60): continue
    ts.append(t)
    for m in re.finditer(r"^[BSD] (\S+) pid=(\d+) nr=(\d+) (\w+)", b, re.M):
        pids.setdefault(m.group(1), set()).add((m.group(2), m.group(3), m.group(4)))
    m = re.search(r"feed_seq=(\d+)", b); fseq.append(int(m.group(1))) if m else None
    m = re.search(r"home_libre_kb=(\d+)", b); libre.append(int(m.group(1))) if m else None
    m = re.search(r"panel_https=(\d+)", b); panel[m.group(1) if m else "sin_dato"] += 1
    m = re.search(r"S ruleset=(\w+)", b); rs.add(m.group(1)) if m else None
    m = re.search(r"D aplicacion=(\d+) firma_invalida=(\d+) paquete_invalido=(\d+) ruleset=(\w+)", b)
    if m: apl.add(m.group(1)); fi.add(m.group(2)); pi.add(m.group(3)); dr.add(m.group(4))
    m = re.search(r"enforce_aplicar=(\d+)", b); en.add(m.group(1)) if m else None
iv = [b - a for a, b in zip(ts, ts[1:])]
print("muestras en ventana±60 s:", len(ts), "intervalo máximo %.0f s" % max(iv))
print("O1 pid/NRestarts/estado por servicio:")
for k, v in sorted(pids.items()): print("   ", k, sorted(v))
print("   publicador: secuencia", fseq[:1], "…", fseq[-1:], "sin retroceso:", all(b >= a for a, b in zip(fseq, fseq[1:])))
print("O6 /home libre mínimo (GB): %.2f" % (min(libre) / 1048576))
print("O9 panel desde el bastión:", dict(panel))
print("O10 ruleset Sensor1:", rs, " srv-dmz:", dr, " aplicacion:", apl, " procesos enforce/aplicar:", en)
print("O8 contadores acumulados firma_invalida:", fi, " paquete_invalido:", pi)
# ---------- correlación de TODOS los firma_invalida
env = sorted((r["traido_en"], r["destinos"]["srv-dmz"]["entregado_en"], r.get("secuencia"), r.get("entrega", "pareja")) for r in ent)
ini = [e[0] for e in env]
todas = sorted((a for a in ag if a["evento"] == "recepcion"), key=lambda a: a["recibido_en"])
print("correlación de rechazos (toda la traza):")
for a in ag:
    if a["evento"] != "rechazo": continue
    t = a.get("recibido_en", a["t"]); i = bisect.bisect_right(ini, t) - 1; e = env[i] if i >= 0 else None
    sig = next((r for r in todas if r["recibido_en"] > t), None)
    print("   %s %.3f | entrega seq %s modo %s traído %.3f entregado %.3f -> %s | siguiente recepción seq %s %s a +%.3f s" % (
        a.get("motivo"), t, e and e[2], e and e[3], e and e[0], e and e[1],
        "DENTRO" if e and e[0] <= t <= e[1] + 0.05 else "FUERA", sig and sig.get("secuencia"), sig and sig.get("estado"),
        (sig["recibido_en"] - t) if sig else -1))
EOF
rm -rf $W
echo "--- O10 srv-dmz después"
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'echo "tablas: [$(sudo -n nft list tables)]"; sudo -n nft list ruleset | sha256sum'
