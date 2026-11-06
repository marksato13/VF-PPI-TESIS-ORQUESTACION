#!/usr/bin/env bash
# [LAPTOP Git Bash] Copia los guiones de preparación de E-carga v2 a una carpeta versionada por contenido
# ~/cf-e4/ecarga-v2-guiones-<8 primeros del sha256 de su SHA256SUMS> en bastión, Sensor1 y clientes. No sobrescribe.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
G="$AQUI/prep"
( cd "$G" && for f in generadores.sh guardia.py muestreo_bastion.sh sensor1_muestreadores.sh test_guardia.py; do sha256sum "$f"; done \
  | sed -E 's/^([0-9a-f]{64}) \*/\1  /' > SHA256SUMS )
TAG=$(sha256sum < "$G/SHA256SUMS" | cut -c1-8)
D="ecarga-v2-guiones-$TAG"
echo "carpeta: $D"; cat "$G/SHA256SUMS"
W=$(mktemp -d); mkdir "$W/$D"; cp "$G"/{generadores.sh,guardia.py,muestreo_bastion.sh,sensor1_muestreadores.sh,test_guardia.py,SHA256SUMS} "$W/$D/"
tar -C "$W" -czf "$W/$D.tgz" "$D"
K="$HOME/.ssh/id_ed25519"; SO="-o BatchMode=yes -o ConnectTimeout=10"
scp -q $SO -i "$K" "$W/$D.tgz" gadmin@10.10.10.30:/tmp/
ssh $SO -i "$K" gadmin@10.10.10.30 "D=$D bash -s" <<'REMOTO'
set -u
instalar() {  # se ejecuta en el host destino con la tgz en /tmp
  cat <<EOF
set -u; cd ~ && mkdir -p cf-e4 && cd cf-e4
if [ -e $D ]; then echo "\$(hostname): $D ya existe, no se sobrescribe"; rm -f /tmp/$D.tgz; exit 3; fi
tar -xzf /tmp/$D.tgz && rm -f /tmp/$D.tgz && cd $D && sha256sum -c --strict --quiet SHA256SUMS && chmod +x *.sh && echo "\$(hostname): $D verifica (\$(wc -l < SHA256SUMS) ficheros)"
EOF
}
for d in 'm4rk@10.10.60.11 cyberflow-to-sensor' 'adminclientes@10.10.20.20 cyberflow-to-clientes'; do
  set -- $d; O="-o BatchMode=yes -o ConnectTimeout=10 -i $HOME/.ssh/$2"
  scp -q $O /tmp/$D.tgz "$1:/tmp/" && instalar | ssh $O "$1" bash -s
done
instalar | bash -s
REMOTO
rm -r "$W"
echo "TAG=$TAG"
