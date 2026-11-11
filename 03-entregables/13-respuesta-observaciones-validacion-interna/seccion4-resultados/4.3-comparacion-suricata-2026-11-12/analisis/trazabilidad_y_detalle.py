"""Trazabilidad por rebanada (hash, paquetes, reglas, rc) y detalle de firmas. Lee los extractos del comparador."""
import csv, collections, json, os, re
from pathlib import Path
R = Path(os.environ.get("CF43_DIR", ".")); E = R / "extractos"
slices = [l.strip() for l in open(R / "lista-slices.txt") if l.strip()]
rows = []
for s in slices:
    log = (E / (s + ".log")).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"SLICE_SHA256 (\w+) bytes (\d+) paquetes (\d+)", log)
    row = {"slice": s, "estado": (E / (s + ".estado")).read_text().strip(), "hash_ficheros": "HASH_OK" if "HASH_OK" in log else "FALLA", "slice_sha256": m.group(1), "bytes": m.group(2), "paquetes_tcpdump": m.group(3)}
    for c in ("principal", "s1"):
        d = E / c / s
        h = (d / "hashes.txt").read_text()
        sl = (d / "suricata.log").read_text(errors="replace")
        row[c + "_rc"] = (d / "rc.txt").read_text().strip()
        row[c + "_reglas"] = (re.search(r"(\d+) rules successfully loaded, (\d+) rules failed", sl).group(0))
        row[c + "_paquetes_suricata"] = re.search(r"read 1 file, (\d+) packets", sl).group(1)
        row[c + "_eve_sha256"] = re.search(r"EVE_SHA256 %s (\w+)" % c, h).group(1)
        row[c + "_eve_gz_sha256"] = re.search(r"EVE_GZ_SHA256 %s (\w+)" % c, h).group(1)
        row[c + "_alertas_totales"] = json.load(open(d / "resumen-eve.json"))["alertas"]
    rows.append(row)
with open(R / "trazabilidad-rebanadas.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "rebanadas; hash OK:", sum(r["hash_ficheros"] == "HASH_OK" for r in rows), "; rc 0 principal/s1:", sum(r["principal_rc"] == "rc=0" for r in rows), sum(r["s1_rc"] == "rc=0" for r in rows),
      "; reglas:", {r["principal_reglas"] for r in rows} | {r["s1_reglas"] for r in rows})
dif = [(r["slice"], r["paquetes_tcpdump"], r["principal_paquetes_suricata"]) for r in rows if r["paquetes_tcpdump"] != r["principal_paquetes_suricata"]]
print("rebanadas con tcpdump != Suricata paquetes:", len(dif), dif[:3])
# detalle de firmas validas por familia (regla fijada)
fam = collections.defaultdict(collections.Counter)
for s in slices:
    if s == "control_30min": continue
    f = s.rsplit("-", 1)[0]
    for l in open(E / "principal" / s / "alertas.jsonl", encoding="utf-8"):
        a = json.loads(l); fi = a["firma"]
        if fi.startswith("SURICATA STREAM ") or fi.startswith("ET INFO "): continue
        if {a["src_ip"], a["dest_ip"]} != {"10.10.20.30", "10.10.10.20" if f == "dns_inusual" else "10.10.30.10"}: continue
        fam[f][(a["sid"], fi[:70], a["categoria"])] += 1
for f, c in fam.items():
    print(f, c.most_common(8))
# alertas excluidas por familia (principal): ET INFO y STREAM sobre el par Kali-destino
ex = collections.defaultdict(collections.Counter)
for s in slices:
    if s == "control_30min": continue
    f = s.rsplit("-", 1)[0]
    for l in open(E / "principal" / s / "alertas.jsonl", encoding="utf-8"):
        a = json.loads(l); fi = a["firma"]
        if {a["src_ip"], a["dest_ip"]} != {"10.10.20.30", "10.10.10.20" if f == "dns_inusual" else "10.10.30.10"}: continue
        if fi.startswith("SURICATA STREAM "): ex[f]["STREAM"] += 1
        elif fi.startswith("ET INFO "): ex[f]["ET INFO: " + fi[:60]] += 1
for f, c in ex.items(): print("EXCLUIDAS", f, dict(c))
