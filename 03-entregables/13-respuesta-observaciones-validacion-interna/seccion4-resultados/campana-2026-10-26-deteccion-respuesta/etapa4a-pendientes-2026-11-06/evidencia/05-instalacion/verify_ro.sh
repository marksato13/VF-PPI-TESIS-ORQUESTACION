set -u
P=~/cf-e4/paquete-313f8f8
for f in $P/deploy/etapa4/unidades/bastion/ppi-relay-eventos.service $P/deploy/etapa4/unidades/srvdmz/ppi-enforce-agent-v2-dmz.service; do
  [ -f "$f" ] || continue
  systemd-analyze verify "$f" > /tmp/cf-verify.out 2>&1; rc=$?
  echo "verify $(basename $f) rc=$rc"; cat /tmp/cf-verify.out; rm -f /tmp/cf-verify.out
done
for u in ppi-relay-eventos.service ppi-enforce-agent-v2-dmz.service; do
  systemctl cat $u >/dev/null 2>&1 || continue
  systemd-analyze verify $u > /tmp/cf-verify.out 2>&1; echo "verify instalado $u rc=$?"; cat /tmp/cf-verify.out; rm -f /tmp/cf-verify.out
done
