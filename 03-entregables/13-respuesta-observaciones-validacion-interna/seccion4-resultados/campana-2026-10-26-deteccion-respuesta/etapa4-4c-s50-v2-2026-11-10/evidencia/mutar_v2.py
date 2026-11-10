import hashlib, subprocess
from pathlib import Path
C = Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta")
R = C / "etapa4-4c-s50-v2-2026-11-10"
P1 = r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-recuperacion\scripts\etapa4"
CFE, DTS, S50 = R / "herramientas/calidad_fuentes_eve.py", R / "herramientas/descartes_tcpdump_sigusr1.py", R / "guiones/s50_analisis_e4.sh"
orig = {p: p.read_bytes() for p in (CFE, DTS, S50)}
h0 = {p: hashlib.sha256(b).hexdigest() for p, b in orig.items()}
MUT = [
 ("M1 calidad: cualquier estado de EVE se toma como cero medido", CFE, "    else:\n        ok = False\n", "    else:\n        ok = True; desc = 0; paq = paq or 0; acot = acot or [0, 0]\n"),
 ("M2 calidad: cero_explicito sin exigir cifras coherentes", CFE, 'est == "cero_explicito" and coherente and desc == 0', 'est == "cero_explicito"'),
 ("M3 descartes: medición no demostrable escribe 0 en vez de null", DTS, '    if motivos:\n        r["dropped_by_kernel"] = None', '    if motivos:\n        r["dropped_by_kernel"] = 0'),
 ("M4 descartes: se acepta más de un PID", DTS, "if len(pids) != 1:", "if False:"),
 ("M5 descartes: no se compara el arranque del servicio", DTS, 'if ini.get("ActiveEnterTimestamp") != fin.get("ActiveEnterTimestamp") or ini.get("NRestarts") != fin.get("NRestarts"):', "if False:"),
 ("M6 s50: el paso 5 no recibe --descartes-tcpdump", S50, ' --descartes-tcpdump "$A/descartes-tcpdump.json"', ""),
 ("M7 s50: el paso 5 ya no depende del paso d", S50, 'paso 5 "3 4 d"', 'paso 5 "3 4"'),
 ("M8 s50: el paso 2 vuelve a calidad_fuentes.py original", S50, 'p_2() { python3 "$HV/calidad_fuentes_eve.py" --herramientas "$H" --salud-captura "$SC" --eve "$EVE" --marcas', 'p_2() { python3 calidad_fuentes.py --stats "$C/stats-inicio.log" "$C/stats-fin.log" --marcas'),
]
def pruebas():
    r = subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", "65534:65534", "--tmpfs", "/tmp:exec,mode=1777", "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
                        "-e", "P1_DIR=/p1", "-v", f"{C}:/camp:ro", "-v", f"{P1}:/p1:ro", "-w", "/camp/etapa4-4c-s50-v2-2026-11-10", "cyberflow-etapa3-banco:1",
                        "python3", "-I", "-m", "pytest", "-p", "no:cacheprovider", "-q", "tests/test_s50_v2.py"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    res = [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l][-1:]
    return r.returncode, res
try:
    for n, f, a, b in MUT:
        t = orig[f].decode("utf-8")
        assert t.count(a) == 1, (n, t.count(a))
        f.write_bytes(t.replace(a, b).encode("utf-8"))
        rc, res = pruebas()
        print(f"{n}: rc={rc} {'DETECTADA' if rc != 0 else 'NO DETECTADA'} {res}")
        f.write_bytes(orig[f])
finally:
    for p, b in orig.items(): p.write_bytes(b)
print("restaurados:", all(hashlib.sha256(p.read_bytes()).hexdigest() == h0[p] for p in orig))
rc, res = pruebas(); print("sin mutar:", rc, res)
