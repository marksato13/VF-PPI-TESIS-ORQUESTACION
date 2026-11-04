D="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-recuperacion/deploy/etapa4/cierre"
for s in cierre4a_sensor1.sh cierre4a_bastion.sh revertir_cierre4a.sh cf-primer-pcap.sh; do
  bash -n "$D/$s"; echo "$s sintaxis rc=$?"
  grep -c $'\r' "$D/$s" | sed "s/^/$s CR=/"
done
T=$(mktemp -d)
printf 'af-packet:\n  - interface: ens37\n    cluster-id: 99\n    #ring-size: 2048\n  - interface: default\n' > "$T/y.yaml"
awk '{print} /^  - interface: ens37$/ && !h {print "    ring-size: 16384   # x"; h=1}' "$T/y.yaml" > "$T/c.yaml"
diff "$T/y.yaml" "$T/c.yaml"; echo "lineas_diff=$(diff "$T/y.yaml" "$T/c.yaml" | grep -c '^[<>]')"
