set -u
# [BASTIÓN gadmin] Solo lecturas: correlaciona cada rechazo firma_invalida del agente (srv-dmz) con la
# entrega del relé (bastión) que lo rodea. Relojes: ambos por NTP de internet.
W=$(mktemp -d)
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 \
  'sudo -n cat /var/lib/cyberflow/agente/traza.jsonl' > $W/agente.jsonl
tr -d '\000' < ~/relay-v2/traza.jsonl > $W/rele.jsonl
echo "NUL en traza del rele: $(tr -cd '\000' < ~/relay-v2/traza.jsonl | wc -c) bytes"
python3 - $W/agente.jsonl $W/rele.jsonl <<'EOF'
import json, sys, bisect
ag = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
re_ = []
for l in open(sys.argv[2]):
    try: re_.append(json.loads(l))
    except ValueError: pass
env = [(r["traido_en"], r["destinos"]["srv-dmz"].get("entregado_en"), r.get("secuencia")) for r in re_
       if r.get("evento") == "reenvio" and "srv-dmz" in r.get("destinos", {})]
env = [e for e in env if e[1]]
env.sort()
print("entregas del rele:", len(env), "desde", min(e[0] for e in env), "hasta", max(e[1] for e in env))
dur = sorted(e[1] - e[0] for e in env)
print("duracion traido->entregado (s): p50 %.3f p95 %.3f max %.3f" % (dur[len(dur)//2], dur[int(len(dur)*.95)], dur[-1]))
rec = [a for a in ag if a["evento"] == "recepcion"]
print("recepciones agente:", len(rec), " rechazos:", sum(1 for a in ag if a["evento"] == "rechazo"))
from collections import Counter
print("motivos rechazo:", Counter(a.get("motivo") for a in ag if a["evento"] == "rechazo"))
print("estados recepcion:", Counter(a.get("estado") for a in rec))
ini = [e[0] for e in env]
for a in ag:
    if a.get("motivo") != "firma_invalida": continue
    t = a["recibido_en"]
    i = bisect.bisect_right(ini, t) - 1
    e = env[i] if i >= 0 else None
    dentro = e is not None and e[0] <= t <= e[1] + 0.05
    sig = next((r for r in rec if r["recibido_en"] > t), None)
    print("rechazo %.3f | entrega seq %s traido %.3f entregado %.3f -> rechazo %s de la entrega (%.3f s antes de entregado) | siguiente aceptacion seq %s a +%.3f s" % (
        t, e[2], e[0], e[1], "DENTRO" if dentro else "FUERA", e[1] - t, sig and sig.get("secuencia"), (sig["recibido_en"] - t) if sig else -1))
# secuencias: huecos en lo aceptado por el agente
seqs = sorted({r["secuencia"] for r in rec if r.get("estado") in ("aceptado",)})
huecos = [(a, b) for a, b in zip(seqs, seqs[1:]) if b - a > 1]
print("secuencias aceptadas:", len(seqs), seqs[:1], seqs[-1:], "huecos:", len(huecos), huecos[:10])
seqr = sorted({e[2] for e in env if e[2] is not None})
print("secuencias entregadas por el rele:", len(seqr), "no vistas como aceptadas:", sorted(set(seqr) - set(seqs))[:20])
EOF
rm -rf $W
