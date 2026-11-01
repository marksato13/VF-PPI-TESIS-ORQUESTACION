#!/usr/bin/env bash
python3 - <<'PY'
import json, collections
from datetime import datetime
T0 = float(open("/home/m4rk/cf-paso2-20261101T0254Z/reinicio.t").read().split()[0])
rs = [json.loads(x) for x in open("/home/m4rk/cyberflow/logs/motor_decision.log") if '"decidido_en"' in x]
rs = [r for r in rs if r["decidido_en"] > T0 + 230]
for r in rs:
    r["_lag"] = r["decidido_en"] - datetime.fromisoformat(r["window_end_utc"]).timestamp()
lags = sorted(r["_lag"] for r in rs)
print("n", len(lags), "p50 %.1f p95 %.1f p99 %.1f max %.1f" % (lags[len(lags)//2], lags[int(.95*len(lags))], lags[int(.99*len(lags))], lags[-1]))
b = collections.Counter(min(int(l // 10) * 10, 250) for l in lags)
print("histograma (s):", sorted(b.items()))
big = [r for r in rs if r["_lag"] > 40]
print("lag>40:", len(big), collections.Counter(r["entity_ip"] for r in big))
for r in big[:12]:
    print("  ", r["entity_ip"], r["window_end_utc"][11:19], "lag %.0f" % r["_lag"], "pc10", r.get("packet_count_10s"), "pend_desde-wend %.0f" % (r["pendiente_desde"] - datetime.fromisoformat(r["window_end_utc"]).timestamp()) if r.get("pendiente_desde") else None, r["decision"], "cov", r.get("history_coverage_s"))
PY
