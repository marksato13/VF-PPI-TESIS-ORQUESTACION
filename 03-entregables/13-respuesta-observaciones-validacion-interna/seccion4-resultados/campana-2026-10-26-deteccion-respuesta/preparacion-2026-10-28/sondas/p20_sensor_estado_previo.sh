#!/usr/bin/env bash
# PREP 20 — sensor: estado ACTUAL antes de tocar nada (no se asume igual al preflight). Guarda versiones, hashes,
# argumentos de servicios, feed/estado.json (escalada residual) en ~/cf-prep-20261028/estado-previo-<ts>/. Solo lectura
# del sistema; escribe unicamente en esa carpeta nueva.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
D=$HOME/cf-prep-20261028/estado-previo-$(date -u +%H%M%S); mkdir -p "$D"
echo "## p20  inicio=$(ts)  destino=$D"
for u in ppi-motor ppi-motor-capture ppi-publicar-feed suricata cyberflow-acumular cyberflow-limpieza; do
  systemctl cat $u.service > "$D/unidad-$u.service.txt" 2>&1
  systemctl show $u.service -p MainPID,NRestarts,ActiveState,SubState,UnitFileState,ActiveEnterTimestamp > "$D/show-$u.txt" 2>&1
  echo "  $u: $(tr '\n' ' ' < "$D/show-$u.txt")"
done
P=$(systemctl show -p MainPID --value ppi-motor); tr '\0' ' ' < /proc/$P/cmdline > "$D/argv-motor.txt"; echo >> "$D/argv-motor.txt"
P2=$(systemctl show -p MainPID --value ppi-motor-capture); tr '\0' ' ' < /proc/$P2/cmdline > "$D/argv-captura.txt"; echo >> "$D/argv-captura.txt"
echo "  argv motor: $(cat "$D/argv-motor.txt")"
echo "  argv captura: $(cat "$D/argv-captura.txt")"
echo "  --enforce en unidad del motor: '$(systemctl cat ppi-motor.service | grep -o -- '--enforce' || true)' | en argv real: '$(grep -o -- '--enforce' "$D/argv-motor.txt" || true)'"
echo "## hashes de implementacion"
( cd $HOME/cyberflow && sha256sum scripts/engine/*.py configs/features/*.json configs/cyberflow.local.toml \
   artifacts/preliminar/limpio-2026-10/*.joblib artifacts/preliminar/limpio-2026-10/*.json 2>/dev/null ) | tee "$D/sha256-implementacion.txt" | grep -E 'motor_decision|extract|heuristicos|publicar_feed|joblib|manifest' | sed 's/^/  /'
( cd $HOME/cyberflow && git log -1 --format='  git sensor: %H %ad %s' --date=iso 2>/dev/null; git status --short 2>/dev/null | head -20 | sed 's/^/    /' ) | tee "$D/git-sensor.txt"
echo "## feed y escalada (copias desde el sensor)"
cp -p $HOME/feed/feed.json $HOME/feed/feed.sig $HOME/feed/estado.json "$D/" && echo "  copiados feed.json feed.sig estado.json"
sha256sum "$D"/feed.json "$D"/feed.sig "$D"/estado.json | sed "s#$D/##;s/^/  /"
python3 - "$D/feed.json" "$D/estado.json" <<'PY'
import json,sys,time
f=json.load(open(sys.argv[1])); e=json.load(open(sys.argv[2]))
print("  feed: generado=%s (hace %.0f s) umbrales=%s entradas=%d %s"%(f.get("generado"),time.time()-float(f.get("generado",0)),f.get("umbrales"),len(f.get("entradas",[])),f.get("entradas")))
print("  escalada (estado.json):", {k:v.get("bloqueos") for k,v in e.items()})
PY
echo "## nftables del sensor (consulta real)"
o=$(sudo -n nft list ruleset 2>&1); rc=$?; echo "$o" > "$D/nft-sensor.txt"; echo "  rc=$rc tablas: $(echo "$o" | grep -E '^table' | tr '\n' ' ')"
echo "## motor: ¿puede aplicar restricciones directamente?"
grep -nE "add_argument\(.--enforce|nft |subprocess|iptables" $HOME/cyberflow/scripts/engine/motor_decision.py | head -12 | sed 's/^/  /'
echo "## fin=$(ts)"
