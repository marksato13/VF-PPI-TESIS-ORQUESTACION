#!/usr/bin/env bash
# PREFLIGHT 04 — sensor: hashes de codigo/modelo/config desplegados y copias de scripts de campana. Solo lectura.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
B=/home/m4rk/cyberflow
echo "## p04 sensor hashes  inicio=$(ts)"
echo "## codigo desplegado (sha256)"
for n in extract_multilayer_v2.py extract_multilayer_v3.py motor_decision.py heuristicos.py publicar_feed.py escalada.py feed.py agente_enforce.py acumular_v3.py; do
  find "$B/scripts" -maxdepth 3 -name "$n" -type f 2>/dev/null | while read -r f; do echo "  $(sha256sum "$f" | cut -c1-64)  $f  mtime=$(stat -c %y "$f" | cut -c1-19)"; done
done
echo "## heuristicos: VERSION_UMBRALES"; grep -rn "VERSION_UMBRALES *=" "$B/scripts" 2>/dev/null | head -3 | sed 's/^/  /'
echo "## modelo / manifiesto / esquema"
M=$B/artifacts/preliminar/limpio-2026-10
for f in "$M/if_limpio_2026_10_desplegable.joblib" "$M/manifest-if-limpio-2026-10.json" "$B/configs/features/multilayer-v2.json"; do echo "  $(sha256sum "$f" | cut -c1-64)  $f"; done
python3 - "$M/manifest-if-limpio-2026-10.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
def find(d,ks,p=""):
  if isinstance(d,dict):
    for k,v in d.items():
      q=p+"."+k
      if any(s in k.lower() for s in ks) and not isinstance(v,(dict,list)): print("   ",q.lstrip("."),"=",v)
      find(v,ks,q)
find(m,("threshold","umbral","detector","sha256","alpha","n_estimators"))
PY
echo "## toml (motor/umbral/calibrado)"; grep -nE '^\s*(detector|umbral|threshold|calibrado|modelo|manifiesto)\b' "$B/configs/cyberflow.local.toml" 2>/dev/null | sed 's/^/  /'
echo "## umbral registrado por el motor en vivo (ultimas 500 decisiones)"
tail -n 500 "$B/logs/motor_decision.log" | grep -o '"threshold": *[-0-9.e]*' | sort | uniq -c | sed 's/^/  /'
echo "## copias de scripts de CAMPANA presentes en el sensor"
for d in "$HOME/bin" "$HOME/cf-campana" "$HOME/cf-campana-archivo" "$HOME/cf-deploy" "$HOME/campana" "$HOME"; do
  [ -d "$d" ] || { echo "  $d: no existe"; continue; }
  find "$d" -maxdepth 2 -type f \( -name 'archivar_captura.sh' -o -name 'capturar.sh' -o -name 'estimar_espacio.sh' -o -name 'comprobar_relojes.sh' -o -name 'analizar.py' -o -name 'verificar_integridad.py' -o -name 'generar_campana.py' -o -name 'esquema_campana.py' -o -name 'escenarios.json' -o -name 'config-campana.json' -o -name 'modo_sombra.sh' -o -name 'restaurar_enforcement.sh' \) 2>/dev/null | while read -r f; do echo "  $(sha256sum "$f" | cut -c1-64)  $f  mtime=$(stat -c %y "$f" | cut -c1-19)"; done
done
echo "## directorios de archivo previos (no se tocan)"; ls -ld "$HOME"/cf-campana-archivo* "$HOME"/cf-preflight* 2>/dev/null | sed 's/^/  /' || true
[ -d "$HOME/cf-campana-archivo" ] && ls -la "$HOME/cf-campana-archivo" | sed 's/^/  /'
echo "## logrotate del motor"; grep -vE '^\s*#|^\s*$' /etc/logrotate.d/cyberflow 2>/dev/null | sed 's/^/  /'
echo "## python del venv"; "$B/.venv/bin/python" -c 'import sys,sklearn,numpy,joblib;print("  python",sys.version.split()[0],"sklearn",sklearn.__version__,"numpy",numpy.__version__,"joblib",joblib.__version__)' 2>&1
echo "## fin=$(ts)"
