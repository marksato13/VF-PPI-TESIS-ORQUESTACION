"""Genera p06_kali.sh con esquema_campana.py y escenarios.json de HEAD embebidos (base64)."""
import base64, hashlib, subprocess
from pathlib import Path
REPO = r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio"
C = "03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta"
def show(p):
    return subprocess.run(["git", "-C", REPO, "-c", "core.longpaths=true", "show", f"HEAD:{C}/{p}"],
                          stdout=subprocess.PIPE, check=True).stdout
esq, escj = show("scripts/esquema_campana.py"), show("escenarios/escenarios.json")
h = {n: hashlib.sha256(b).hexdigest() for n, b in (("esquema_campana.py", esq), ("escenarios.json", escj))}
plantilla = Path(__file__).with_name("p06_kali.tpl.sh").read_text(encoding="utf-8")
out = (plantilla.replace("@@ESQ@@", base64.b64encode(esq).decode()).replace("@@ESC@@", base64.b64encode(escj).decode())
       .replace("@@H_ESQ@@", h["esquema_campana.py"]).replace("@@H_ESC@@", h["escenarios.json"]))
Path(__file__).with_name("p06_kali.sh").write_text(out, encoding="utf-8", newline="\n")
print(h)
