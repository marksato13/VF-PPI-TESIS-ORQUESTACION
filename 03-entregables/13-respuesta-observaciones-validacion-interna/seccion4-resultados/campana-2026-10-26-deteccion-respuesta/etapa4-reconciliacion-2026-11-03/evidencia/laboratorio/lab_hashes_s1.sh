#!/bin/bash
# SOLO LECTURA: hash de blob git (sha1 de "blob <n>\0"+contenido) y sha256 de cada fichero.
set -u
cd ~/cyberflow || exit 1
blob() { local n; n=$(stat -c %s "$1"); { printf 'blob %s\0' "$n"; cat "$1"; } | sha1sum | cut -c1-40; }
echo "### codigo (git-blob sha256 tamano mtime ruta)"
find scripts/engine scripts/features scripts/enforce scripts/setup scripts/campaign scripts/etapa4 deploy configs/features configs/escenarios.json configs/cyberflow.toml configs/cyberflow.local.toml dashboard -type f \
  \( -name '*.py' -o -name '*.json' -o -name '*.toml' -o -name '*.sh' -o -name '*.service' -o -name '*.timer' -o -name '*.conf' \) \
  -not -name '*.bak*' 2>/dev/null | sort | while read -r f; do
  printf '%s %s %s %s %s\n' "$(blob "$f")" "$(sha256sum "$f" | cut -c1-16)" "$(stat -c %s "$f")" "$(stat -c %y "$f" | cut -c1-16)" "$f"
done
echo "### artefactos del modelo (sha256 completo)"
find artifacts/preliminar artifacts/model -maxdepth 3 -type f \( -name '*.joblib' -o -name '*.json' -o -name '*.pkl' \) 2>/dev/null | sort | while read -r f; do
  printf '%s %s %s %s\n' "$(sha256sum "$f" | cut -c1-64)" "$(stat -c %s "$f")" "$(stat -c %y "$f" | cut -c1-16)" "$f"
done
echo "### manifiesto desplegado (campos clave)"
python3 - <<'PY'
import json
m = json.load(open('artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json'))
def g(*k):
    d = m
    for x in k:
        d = d.get(x) if isinstance(d, dict) else None
    return d
for k in list(m.keys())[:40]:
    v = m[k]
    s = json.dumps(v, ensure_ascii=False)
    print(k, '=', s[:300])
PY
echo "### esquema multilayer-v2 (orden de columnas)"
python3 -c 'import json;d=json.load(open("configs/features/multilayer-v2.json"));c=d.get("features") or d.get("columns") or d.get("feature_order") or d; print(type(c).__name__, len(c) if hasattr(c,"__len__") else "");print(json.dumps(c if isinstance(c,list) else list(d.keys()), ensure_ascii=False)[:3000])'
echo "### python del venv y paquetes"
.venv/bin/python -c 'import sys,sklearn,numpy,joblib;print(sys.version.split()[0],"sklearn",sklearn.__version__,"numpy",numpy.__version__,"joblib",joblib.__version__)'
echo "### feed vigente"
python3 -c 'import json;d=json.load(open("/home/m4rk/feed/feed.json"));print({k:(v if k!="entradas" else len(v)) for k,v in d.items() if k not in ("liberaciones",)})'
ls -la ~/feed ~/feed/peticiones 2>/dev/null | head -20
echo "### respaldos y sombra"
ls -la ~/respaldos 2>/dev/null
ls -d ~/cyberflow-* ~/sombra* ~/cf-* ~/candidata* 2>/dev/null
systemctl list-units --all --no-legend '*sombra*' '*shadow*' '*via-rapida*' '*v2*' 2>/dev/null | awk '{print $1,$3,$4}'
