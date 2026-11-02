"""Prueba offline de guiones/d01_dns_dia_e4.sh (el bloque Python del guion, tal cual) con un directorio de Suricata
sintético: eve.json + eve.json.1.gz (día repartido en dos ficheros por la rotación), eventos fuera del día, un hueco
de 400 s, stats.log con un reinicio de contador. Uso: python -I probar_d01_dns.py <guion> <dir_temporal>"""
import gzip, json, re, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

guion, tmp = Path(sys.argv[1]), Path(sys.argv[2])
code = re.search(r"<<'PY'\n(.*?)\nPY\n", guion.read_text(encoding="utf-8"), re.S).group(1)
s, o = tmp / "suricata", tmp / "salida"
s.mkdir(parents=True); o.mkdir()
tz = timezone(timedelta(hours=-5))
d0 = datetime(2026, 11, 3, tzinfo=tz)


def ev(t, tipo):
    return json.dumps({"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.%f") + "-0500", "event_type": tipo,
                       "src_ip": "10.10.20.21", "dest_ip": "10.10.10.20"}) + "\n"


a = [ev(d0 - timedelta(seconds=30), "dns")]  # día anterior: fuera
a += [ev(d0 + timedelta(seconds=10 * i), "dns" if i % 3 == 0 else "flow") for i in range(0, 100)]
b = [ev(d0 + timedelta(seconds=990 + 400 + 10 * i), "dns" if i % 2 == 0 else "flow") for i in range(0, 50)]
b += [ev(d0 + timedelta(days=1, seconds=5), "dns")]  # día siguiente: fuera
with gzip.open(s / "eve.json.1.gz", "wt") as g:
    g.writelines(a)
(s / "eve.json").write_text("".join(b) + '{"sin_timestamp": 1}\n', encoding="utf-8")


def st(t, p, d):
    u = t.astimezone(timezone.utc)
    return (f"Date: {u.month}/{u.day}/{u.year} -- {u:%H:%M:%S} (uptime: 0d)\n"
            f"capture.kernel_packets | Total | {p}\ncapture.kernel_drops | Total | {d}\n")


(s / "stats.log").write_text(st(d0 + timedelta(hours=1), 1000, 1) + st(d0 + timedelta(hours=2), 3000, 3)
                             + st(d0 + timedelta(hours=3), 500, 0) + st(d0 + timedelta(hours=4), 1500, 2),
                             encoding="utf-8")
r = subprocess.run([sys.executable, "-I", "-", "2026-11-03", str(s), str(o)], input=code, capture_output=True, text=True)
print(r.stdout.strip(), r.stderr.strip())
c = json.loads((o / "continuidad-2026-11-03.json").read_text())
n_dns = sum(1 for _ in gzip.open(o / "eve-dns-2026-11-03.json.gz", "rt"))
esperado_dns = sum(1 for i in range(100) if i % 3 == 0) + sum(1 for i in range(50) if i % 2 == 0)
assert c["dns"] == n_dns == esperado_dns, (c["dns"], n_dns, esperado_dns)
assert c["eventos"] == 150, c["eventos"]
assert c["hueco_max_s"] == 400.0 and len(c["huecos_mayores_300s"]) == 1, c
assert c["reinicios_contador"] == 1 and c["kernel_packets"] == 3000 and c["kernel_drops"] == 4, c
print("OK", json.dumps({k: c[k] for k in ("dns", "eventos", "hueco_max_s", "kernel_packets", "kernel_drops",
                                          "reinicios_contador", "drops_pct")}))
