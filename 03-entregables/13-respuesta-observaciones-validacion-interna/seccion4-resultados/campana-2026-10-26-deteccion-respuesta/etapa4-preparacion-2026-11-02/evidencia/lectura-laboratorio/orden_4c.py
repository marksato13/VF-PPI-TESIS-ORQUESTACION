"""Crea escenarios-4c.json (copia de escenarios.json con semilla nueva) y publica el orden con generar_campana.plan_orden."""
import json, sys, hashlib
from pathlib import Path
camp = Path(sys.argv[1])           # carpeta campana-2026-10-26-deteccion-respuesta
dst = Path(sys.argv[2])            # carpeta etapa4-preparacion-2026-11-02
sys.path.insert(0, str(camp / "scripts"))
import generar_campana as g        # noqa: E402
import esquema_campana as esq      # noqa: E402
base = json.loads((camp / "escenarios" / "escenarios.json").read_text(encoding="utf-8"))
cfg = dict(base)
cfg["semilla"] = 20261102
cfg["_campana"] = "etapa4-campana-A-4c"
cfg["_nota_4c"] = ("Etapa 4, campaña A nueva (4C). Igual que escenarios/escenarios.json (escenarios, parámetros, "
                   "tiempos 60/120/90, origen y lista blanca) salvo la SEMILLA, fijada por regla antes de calcular el "
                   "orden: la fecha de la preparación, 20261102 (la 3B usó 20261026). El orden se publica en "
                   "ORDEN-4C.md antes de ejecutar; no se cambia la semilla a la vista del orden.")
problemas = esq.validar(cfg, exigir_herramientas=False)
assert not problemas, problemas
out = dst / "escenarios-4c.json"
# bytes UTF-8 con finales LF (el repositorio normaliza a LF: el hash publicado debe ser el de esos bytes)
out.write_bytes((json.dumps(cfg, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
plan = g.plan_orden(cfg)
orden = [f"{s['id']}-r{r}" for s, r in plan]
print(json.dumps({"semilla": cfg["semilla"], "sha256_config": hashlib.sha256(out.read_bytes()).hexdigest(),
                  "orden": orden}, ensure_ascii=False))
viejo = [f"{s['id']}-r{r}" for s, r in g.plan_orden(base)]
print("orden 3B (semilla 20261026):", viejo[:5], "...")
