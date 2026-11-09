import hashlib, subprocess
from pathlib import Path
C = Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta")
F = C / "etapa4-4c-ajustes-2026-11-09/scripts-4c-n/esquema_campana.py"
orig = F.read_bytes(); h0 = hashlib.sha256(orig).hexdigest()
t = orig.decode("utf-8")
muts = {
 "M1 se quita -n del sostenido": t.replace('return ["nmap", "-sT", "-n", p["timing"], "--max-retries", str(p["max_retries"]),\n', 'return ["nmap", "-sT", p["timing"], "--max-retries", str(p["max_retries"]),\n'),
 "M2 el dig deja de usar @destino": t.replace("dig +time=1 +tries=1 @{dst} ", "dig +time=1 +tries=1 "),
 "M3 -n duplicado en el breve": t.replace('["nmap", "-sT", "-n", p["timing"], "--max-retries", str(p["max_retries"]), "-p"', '["nmap", "-sT", "-n", "-n", p["timing"], "--max-retries", str(p["max_retries"]), "-p"'),
}
try:
    for n, m in muts.items():
        assert m != t, n
        F.write_bytes(m.encode("utf-8"))
        r = subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", "65534:65534", "--tmpfs", "/tmp:exec,mode=1777", "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
                            "-v", f"{C}:/camp:ro", "-w", "/camp/etapa4-4c-ajustes-2026-11-09", "cyberflow-etapa3-banco:1", "python3", "-I", "-m", "pytest", "-p", "no:cacheprovider", "-q", "tests/test_nmap_sin_dns.py"],
                           capture_output=True, text=True)
        ult = [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l][-1:]
        print(f"{n}: rc={r.returncode} (debe ser 1) {ult}")
finally:
    F.write_bytes(orig)
print("restaurado:", hashlib.sha256(F.read_bytes()).hexdigest() == h0, h0[:16])
