"""Construye la lista fija de PCAP (episodios elegibles + control de 30 min) con hash por fichero ANTES del replay."""
import csv, json, hashlib, os
from pathlib import Path

INV = Path(os.environ.get("CF43_DIR", "."))
OUT = Path(os.environ.get("CF43_DIR", "."))
B = Path(os.environ["CF43_ANALISIS_V2"])   # carpeta evidencia/analisis-v2 del repositorio
rows = list(csv.DictReader(open(INV / "episodios-campana-A-4c.csv", encoding="utf-8-sig")))
el = [r for r in rows if r["integridad_apta"] == "True" and r["poblacion_principal"] == "True"]
assert len(el) == 21
orden = {"dns_inusual": 0, "inundacion_http": 1, "fuerza_bruta_http": 2, "escaneo_sostenido": 3, "escaneo_breve": 4}
el.sort(key=lambda r: (orden[r["familia"]], int(r["repeticion"])))
lista = []
for r in el:
    m = json.load(open(B / "respaldos" / r["episodio_id"] / "pcap-manifiesto.json", encoding="utf8"))
    fs = sorted(m["ficheros"], key=lambda f: f["fichero"])
    assert all(f["sha256"] == f["sha256_archivador"] for f in fs)
    for i, f in enumerate(fs, 1):
        lista.append([r["episodio_id"], "episodio", i, f["fichero"], f["bytes"], f["sha256"]])
ctl = [l.split() for l in open(INV / "control-extracto-sensor1.txt", encoding="utf-8-sig") if l.startswith("F ")]
for i, f in enumerate(sorted(ctl, key=lambda x: x[1]), 1):
    lista.append(["control_30min", "control", i, f[1], int(f[2]), f[3]])
with open(OUT / "pcap-lista-fija.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n"); w.writerow(["slice_id", "tipo", "orden", "fichero", "bytes", "sha256"]); w.writerows(lista)
ep = [(r["episodio_id"], r["familia"], r["repeticion"], r["inicio_utc"], r["fin_utc"], r["destino"], r["servicio"]) for r in el]
with open(OUT / "episodios-elegibles.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n"); w.writerow(["episodio_id", "familia", "repeticion", "inicio_utc", "fin_utc", "destino", "servicio"]); w.writerows(ep)
print(len(lista), "filas;", len({x[0] for x in lista}), "slices;", len(ep), "episodios")
