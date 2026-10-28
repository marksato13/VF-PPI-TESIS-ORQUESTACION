#!/usr/bin/env bash
# PREP 32 — Kali: hashes de las copias, validar(exigir_herramientas=True) y SIMULACION sin --autorizado en /tmp
# (no lanza trafico: correr_episodio retorna "simulado" antes de Popen). Lista cada comando sin ejecutarlo.
set -u
cd ~/cf-campana-A || exit 2
echo "## p32  $(date -u +%FT%T.%3NZ)  host=$(hostname)  python=$(python3 --version 2>&1)"
sha256sum scripts/generar_campana.py scripts/esquema_campana.py escenarios/escenarios.json
cd scripts
python3 - <<'PY'
import json, shutil
import esquema_campana as esq
cfg = json.load(open("../escenarios/escenarios.json", encoding="utf-8"))
p = esq.validar(cfg, exigir_herramientas=True)
print("validar(exigir_herramientas=True):", "OK sin problemas" if not p else p)
print("claves de config:", sorted(k for k in cfg if k != "escenarios"))
for k in sorted(cfg):
    if k != "escenarios" and not isinstance(cfg[k], (dict, list)):
        print(f"  {k} = {cfg[k]}")
for k in ("tiempos_s", "alfa", "alfas", "alphas", "configuraciones"):
    if k in cfg:
        print(f"  {k} = {json.dumps(cfg[k], ensure_ascii=False)[:400]}")
print("escenarios:", len(cfg["escenarios"]), "habilitados:", sum(1 for s in cfg["escenarios"] if s.get("habilitado")))
for s in cfg["escenarios"]:
    cmd = esq.comando_de(cfg, s)
    print(f"  {s['id']:28s} hab={s.get('habilitado')!s:5s} dest={s['destino']} serv={s['servicio']} t={s['timeout_s']} "
          f"herr={cmd[0]} ({shutil.which(cmd[0]) or 'NO ENCONTRADA'})")
    print(f"      {' '.join(cmd)[:300]}")
PY
D=$(mktemp -d /tmp/cf-sim-XXXX)
echo "## simulacion sin --autorizado -> $D"
timeout 60 python3 generar_campana.py --config ../escenarios/escenarios.json --salida-dir "$D" --solo-habilitados; echo "rc=$?"
echo "  ficheros: $(ls $D)"; echo "  marcas: $(wc -l < $D/marcas.jsonl) lineas; salidas/: $(ls $D/salidas 2>/dev/null | wc -l) ficheros"
head -c 600 $D/marcas.jsonl; echo
rm -rf "$D"; echo "  $D borrado"
echo "## procesos de herramientas de ataque vivos: $(pgrep -fl 'nmap|hydra|curl|python3 generar' | grep -v pgrep | wc -l)"
echo "## fin $(date -u +%FT%T.%3NZ)"
