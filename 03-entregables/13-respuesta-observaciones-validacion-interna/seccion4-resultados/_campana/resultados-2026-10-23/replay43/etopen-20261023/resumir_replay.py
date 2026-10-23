"""Resume EVE sin confundir alertas informativas con ataques confirmados."""
from collections import Counter
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
events = [json.loads(line) for line in (ROOT / "eve.json").read_text().splitlines() if line]
alerts = [event for event in events if event.get("event_type") == "alert"]
counts = Counter((e["alert"]["signature_id"], e["alert"]["signature"],
                  e.get("src_ip"), e.get("dest_ip")) for e in alerts)
summary = {
    "suricata": "7.0.3", "rules_loaded": 53013, "rules_failed": 0,
    "pcap_packets": 9470,
    "pcap_sha256": "9db1b269dcf19a4281130081ffb79582e9d29ea85cb01b4d87618d5f5a809070",
    "rules_sha256": "7b674459975dd56af2d03363b27df4ad6ff53e724e3c04ff65913701ddd5f4e9",
    "yaml_sha256": "d0ea918591040108586e43fb30e51c3583f6d61f6ed1acd8dff938150b303650",
    "home_net": "10.10.30.0/24",
    "event_counts": dict(Counter(e.get("event_type") for e in events)),
    "alerts_total": len(alerts),
    "signatures": [dict(sid=k[0], signature=k[1], src_ip=k[2], dest_ip=k[3], count=v)
                   for k, v in sorted(counts.items())],
    "files_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in ("eve.json", "suricata.log")},
    "interpretation": "54 alertas STREAM y una ET INFO por uso de curl; no afirmar cero alertas ni deteccion confirmada de flood.",
    "limitations": ["escaneo con trafico minimo", "control Nikto no incluido", "un PCAP archivado, no bateria N>=3"],
}
(ROOT / "resumen.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
