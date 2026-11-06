"""O6 (recursos de Sensor1) a partir de muestras.txt del bastión, solo la ventana 04:50:00Z–05:50:00Z."""
import re
import sys

D, A = 1793940600, 1793944200
carga, mem, libre, n = [], [], [], 0
for b in open(sys.argv[1], encoding="utf-8").read().split("### ")[1:]:
    t = float(b.split("\n", 1)[0].split()[1])
    if not D <= t <= A:
        continue
    n += 1
    m = re.search(r"home_libre_kb=(\d+) carga=([\d.]+) ([\d.]+) ([\d.]+) memdisp_kb=(\d+)", b)
    if m:
        libre.append(int(m.group(1)))
        carga.append(float(m.group(2)))
        mem.append(int(m.group(5)))
print(f"muestras en la ventana: {n}; con recursos: {len(carga)}")
print(f"carga 1 min: máx {max(carga):.2f}, mediana {sorted(carga)[len(carga)//2]:.2f}")
print(f"MemAvailable: mín {min(mem)/1048576:.2f} GB; /home libre: mín {min(libre)/1048576:.2f} GB")
