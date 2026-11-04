"""Reanaliza el 3B revisado con analizar_3b original y con la versión de la reconciliación (solo lectura de la
evidencia; salidas en el scratchpad) y compara las emisiones oportunas por etiqueta."""
import gzip, hashlib, json, shutil, subprocess, sys
from pathlib import Path

C = Path(r"C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables"
         r"\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta")
E = C / "ejecucion-3b-2026-11-01" / "evidencia" / "sensor"
OUT = Path(sys.argv[1]); S = OUT / "S"; S.mkdir(parents=True, exist_ok=True)
for src, dst in ((E / "copias" / "motor_decision.log.gz", S / "motor_decision.log"),
                 (E / "replay" / "motor_decision.log.gz", S / "replay.log")):
    with gzip.open(src, "rb") as f, open(dst, "wb") as g:
        shutil.copyfileobj(f, g)
    print(dst.name, hashlib.sha256(dst.read_bytes()).hexdigest()[:8])
args = ["--marcas", E / "copias" / "marcas.jsonl", "--motor", S / "motor_decision.log",
        "--config", E / "herramientas" / "config-campana-3b.json", "--ciclos", E / "copias" / "ciclos.jsonl",
        "--inventario", S / "replay.log", "--inventario-rango", "2026-11-01T07:24:40Z,2026-11-01T10:05:30Z",
        "--destinos", E / "analisis" / "destinos-3b.csv",
        "--integridad", C / "revision-3b-2026-11-01" / "resultados" / "sensor" / "integridad-v2.json",
        "--calidad-fuentes", E / "analisis" / "calidad-fuentes.json",
        "--control", "2026-11-01T07:32:00Z,2026-11-01T08:05:00Z", "--etiqueta", "3B revisado, etiquetas separadas"]
res = {}
for nombre, script in (("original", C / "scripts" / "analizar_3b.py"),
                       ("reconciliacion", C / "etapa4-reconciliacion-2026-11-03" / "herramientas" / "analizar_3b.py")):
    sal = OUT / nombre
    env_path = str(C / "scripts")
    r = subprocess.run([sys.executable, "-c",
                        "import sys,runpy; sys.path.insert(0, sys.argv[1]); sys.argv = sys.argv[2:]; "
                        "runpy.run_path(sys.argv[0], run_name='__main__')",
                        env_path, str(script), *map(str, args), "--salida", str(sal)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        print(r.stderr[-2000:]); raise SystemExit(1)
    res[nombre] = json.loads((sal / "analisis-3b.json").read_text(encoding="utf-8"))
o, n = res["original"], res["reconciliacion"]
# 1) lo que el original publicaba no cambia
iguales = all(o["episodios"][e][cf] == n["episodios"][e][cf] for e in o["episodios"] for cf in
              ("IF_0.05", "IF_0.03", "IF_0.01", "HEUR", "HIB_0.05", "HIB_0.03", "HIB_0.01"))
ppal_igual = all(o["episodios"][e]["en_poblacion_principal"] == n["episodios"][e]["en_poblacion_principal"]
                 for e in o["episodios"])
op_igual = all(o["episodios"][e]["emisiones_reales"]["oportunas"] == n["episodios"][e]["emisiones_reales"]["oportunas"]
               for e in o["episodios"])
print("categorias 7 configuraciones iguales:", iguales, "| poblacion principal igual:", ppal_igual,
      "| recuento 'oportunas' (cualquiera) igual:", op_igual)
L = ["| Episodio | Principal | Oportunas (cualquiera) | Señal IF | Regla prevista | Otra regla | Reglas oportunas |",
     "|---|---|---|---|---|---|---|"]
fam = {}
for eid, c in sorted(n["episodios"].items()):
    er = c["emisiones_reales"]
    reglas = sorted({r for d in er.get("detalle", []) if d["oportuna"] for r in d["reglas"]})
    L.append(f"| {eid} | {'sí' if c['en_poblacion_principal'] else 'no'} | {er['oportunas']} | {er['oportunas_senal_if']}"
             f" | {er['oportunas_regla_prevista']} | {er['oportunas_regla_no_prevista']} | {', '.join(reglas) or '—'} |")
    if c["en_poblacion_principal"]:
        f = fam.setdefault(eid.rsplit("-r", 1)[0], {"principal": 0, "cualquiera": 0, "senal_if": 0,
                                                    "regla_prevista": 0, "solo_otra_regla": 0})
        f["principal"] += 1
        f["cualquiera"] += er["oportunas"] > 0
        f["senal_if"] += er["oportunas_senal_if"] > 0
        f["regla_prevista"] += er["oportunas_regla_prevista"] > 0
        f["solo_otra_regla"] += (er["oportunas"] > 0 and er["oportunas_senal_if"] == 0
                                 and er["oportunas_regla_prevista"] == 0)
L += ["", "| Familia (población principal) | Episodios | Con alguna emisión oportuna | Con señal IF oportuna | "
      "Con regla prevista oportuna | Solo otra regla |", "|---|---|---|---|---|---|"]
for k, f in sorted(fam.items()):
    L.append(f"| {k} | {f['principal']} | {f['cualquiera']} | {f['senal_if']} | {f['regla_prevista']} | {f['solo_otra_regla']} |")
tot = {k: sum(f[k] for f in fam.values()) for k in ("principal", "cualquiera", "senal_if", "regla_prevista", "solo_otra_regla")}
L.append(f"| **Total** | {tot['principal']} | {tot['cualquiera']} | {tot['senal_if']} | {tot['regla_prevista']} | {tot['solo_otra_regla']} |")
(OUT / "ETIQUETAS-3B-REVISADO.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[-(len(fam) + 4):]))
