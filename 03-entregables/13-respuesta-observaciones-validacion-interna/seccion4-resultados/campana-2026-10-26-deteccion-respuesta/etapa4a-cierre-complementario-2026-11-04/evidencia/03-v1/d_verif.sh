set -u
# [srv-dmz adminsrvdmz] Agente v1 deshabilitado, v2 recibiendo, sin aplicación (solo lectura).
for u in ppi-enforce-agent.timer ppi-enforce-agent.service ppi-enforce-agent-v2-dmz.service; do
  printf '%s ' $u; systemctl show $u -p ActiveState -p UnitFileState -p MainPID --value | tr '\n' ' '; echo; done
tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-enforce-agent-v2-dmz)/cmdline; echo
ls -la --time-style=full-iso ~/enforce/ 2>/dev/null | head -n 8
sudo -n nft list ruleset | sha256sum
journalctl --no-pager -u ppi-enforce-agent-v2-dmz --since "-3min" | tail -n 4
ps -eo args | grep -E -- '--aplicar|--enforce' | grep -v grep || echo "ningún proceso con --aplicar/--enforce"
