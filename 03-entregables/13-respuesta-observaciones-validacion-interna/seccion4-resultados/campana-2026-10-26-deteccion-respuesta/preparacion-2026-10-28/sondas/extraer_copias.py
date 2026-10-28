"""Extrae de HEAD (bytes publicados por git, LF) las copias a desplegar y escribe copias/HASHES.txt."""
import hashlib, subprocess
from pathlib import Path
REPO = r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio"
C = "03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
OUT = Path(__file__).with_name("copias")
MAPA = {"srv/modo_sombra.sh": "scripts/modo_sombra.sh",
        "srv/restaurar_enforcement.sh": "scripts/restaurar_enforcement.sh",
        "kali/scripts/generar_campana.py": "scripts/generar_campana.py",
        "kali/scripts/esquema_campana.py": "scripts/esquema_campana.py",
        "kali/escenarios/escenarios.json": "escenarios/escenarios.json"}
head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], stdout=subprocess.PIPE, check=True).stdout.decode().strip()
filas = [f"# HEAD {head}"]
for dst, src in MAPA.items():
    b = subprocess.run(["git", "-C", REPO, "-c", "core.longpaths=true", "show", f"HEAD:{C}/{src}"],
                       stdout=subprocess.PIPE, check=True).stdout
    p = OUT / dst; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b)
    filas.append(f"{hashlib.sha256(b).hexdigest()}  {dst}  <- {src}")
(OUT / "HASHES.txt").write_text("\n".join(filas) + "\n", encoding="utf-8", newline="\n")
print("\n".join(filas))
