#!/usr/bin/env bash
python3 - <<'PY'
import json
from datetime import datetime
E = {"T1": (1793505059.753, 1793505149.044), "T2": (1793505416.135, 1793505506.063)}
rs = [json.loads(x) for x in open("/home/m4rk/cyberflow/logs/motor_decision.log") if '"10.10.20.30"' in x and '"decidido_en"' in x]
for k, (i, f) in E.items():
    print("==", k)
    for r in rs:
        w = datetime.fromisoformat(r["window_end_utc"]).timestamp()
        if i - 20 <= w <= f + 90:
            h = r.get("heuristico")
            print("  wend %+6.0f  decidido %+6.1f  lag %5.1f  %-6s score %.4f pc10 %s heur %s" % (w - i, r["decidido_en"] - i, r["decidido_en"] - w, r["decision"], r["score"] if r.get("score") is not None else float("nan"), r.get("packet_count_10s"), json.dumps(h)[:120] if h else None))
PY
