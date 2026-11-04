set -u
# [srv-dmz adminsrvdmz] Estado final: agente v1 deshabilitado, v2 recibiendo, sin aplicaciones, ruleset de base. Solo lectura.
date -u +%FT%TZ
for u in ppi-enforce-agent.timer ppi-enforce-agent.service ppi-enforce-agent-v2-dmz.service; do
  printf '%s ' $u; systemctl show $u -p ActiveState -p UnitFileState -p MainPID -p NRestarts --value | tr '\n' ' '; echo; done
tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-enforce-agent-v2-dmz)/cmdline; echo
stat -c '%n %y' ~/enforce ~/enforce/acuse-historial.json
sudo -n nft list ruleset | sha256sum
sudo -n cat /var/lib/cyberflow/agente/traza.jsonl | python3 -c '
import json,sys,collections
D,H=1793773615,1793777215
r=[json.loads(l) for l in sys.stdin if l.strip()]
w=[x for x in r if D<=x.get("t",0)<=H]
print("lineas_total", len(r), "en_ventana", len(w), collections.Counter((x.get("evento"), x.get("estado")) for x in w).most_common(6))
ap=[x for x in r if x.get("evento") not in ("recepcion",) or x.get("aplicada")]
print("eventos distintos de recepcion (todo el fichero):", collections.Counter(x.get("evento") for x in ap).most_common(6))
sec=[x.get("secuencia") for x in w if x.get("secuencia") is not None]
print("secuencias en ventana", min(sec) if sec else None, "->", max(sec) if sec else None, "ultima", r[-1].get("secuencia"), r[-1].get("estado"))'
ps -eo args | grep -E -- '--aplicar|--enforce' | grep -v grep || echo "ningún proceso con --aplicar/--enforce"
