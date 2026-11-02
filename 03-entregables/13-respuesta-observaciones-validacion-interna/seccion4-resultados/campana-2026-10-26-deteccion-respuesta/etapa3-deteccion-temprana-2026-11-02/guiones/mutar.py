"""Mutaciones mínimas: cada una debe hacer fallar al menos una prueba de la Etapa 3."""
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(sys.argv[1])
MUT = [
    ("scripts/engine/escaneo_temprano.py", "if n >= self.K and", "if n > self.K and"),
    ("scripts/engine/escaneo_temprano.py", "t - t0 < 0.005", "t - t0 < 0.0"),
    ("scripts/engine/escaneo_temprano.py", "t - par.ultimo_disparo >= self.refractario_s", "True"),
    ("scripts/engine/publicar_feed_v2.py", "ev_desde >= prev.get(\"evidencia_hasta\", float(\"inf\"))", "True"),
    # vistas de la Etapa 3
    ("scripts/engine/dns_heuristica.py", "abs(t - prev) < self.copia_s", "False"),
    ("scripts/engine/dns_heuristica.py", "reenvio = i > 0 and t - lst[i - 1] <= self.delta_s", "reenvio = False"),
    ("scripts/engine/http_heuristica.py", "en_cable = j < len(ts) and ts[j] <= t + self.tolerancia_s", "en_cable = True"),
    ("scripts/engine/heuristicos.py", "and up >= u.get(\"min_unique_dst_port_ratio_burst_30s\", 0.0))", ")"),
]
PRUEBAS = ["tests/test_escaneo_temprano.py", "tests/test_etapa3_publicador.py", "tests/test_etapa2_cadena.py",
           "tests/test_etapa3_dns.py", "tests/test_etapa3_http.py"]
res = 0
for f, a, b in MUT:
    p = RAIZ / f
    orig = p.read_bytes().decode("utf-8")
    assert orig.count(a) == 1, (f, a)
    shutil.copy(p, str(p) + ".bak")
    p.write_bytes(orig.replace(a, b).encode("utf-8"))
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", *PRUEBAS], cwd=RAIZ, capture_output=True, text=True)
        muerta = r.returncode != 0
        print(("MUERTA " if muerta else "VIVA   ") + f + " :: " + a + " -> " + b + " :: " + r.stdout.strip().splitlines()[-1])
        res |= (not muerta)
    finally:
        p.write_bytes(orig.encode("utf-8"))
        Path(str(p) + ".bak").unlink()
sys.exit(res)
