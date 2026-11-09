for d in 4c-cancelada-20261109T1058Z 4c-x3-cancelada-20261109T1350Z 4c-x3b-cancelada-20261109T1625Z; do
  echo "== $d"
  python3 - "$HOME/cf-e4/$d/vigia/vigia.jsonl" <<'PY'
import json, sys
rs = [json.loads(l) for l in open(sys.argv[1])]
f = [r for r in rs if r.get("evento") == "vigia_fin"]
if f:
    r = f[-1]; print("  campana_fin:", r.get("campana_fin"), "| clases:", ", ".join(f"{k.split('-')[0][:6]}-{k.split('-')[-1]}={v}" for k, v in r.get("clases", {}).items()))
    print("  causas:", (r.get("causas") or r.get("cancelacion") or "")[:200] if not isinstance(r.get("causas"), list) else r.get("causas")[:2])
else:
    print("  sin vigia_fin;", len(rs), "rondas")
PY
done
