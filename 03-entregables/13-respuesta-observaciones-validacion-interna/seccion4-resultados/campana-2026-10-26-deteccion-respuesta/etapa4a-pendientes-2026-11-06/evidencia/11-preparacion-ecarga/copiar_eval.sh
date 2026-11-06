#!/usr/bin/env bash
# [LAPTOP Git Bash] Copia las herramientas de evaluación de E-carga v2 a ~/cf-e4/ecarga-v2-evaluacion-<tag de contenido>
# en Sensor1 y bastión. No sobrescribe. No instala nada en servicios.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
G="$AQUI/eval"; F=(construir_entrada.py derivar_bastion.py derivar_pcap.py sensor1_post.sh test_evaluacion.py)
( cd "$G" && for f in "${F[@]}"; do sha256sum "$f"; done | sed -E 's/^([0-9a-f]{64}) \*/\1  /' > SHA256SUMS )
TAG=$(sha256sum < "$G/SHA256SUMS" | cut -c1-8); D="ecarga-v2-evaluacion-$TAG"
echo "carpeta: $D"; cat "$G/SHA256SUMS"
W=$(mktemp -d); mkdir "$W/$D"; for f in "${F[@]}" SHA256SUMS; do cp "$G/$f" "$W/$D/"; done
tar -C "$W" -czf "$W/$D.tgz" "$D"
K="$HOME/.ssh/id_ed25519"; SO="-o BatchMode=yes -o ConnectTimeout=10"
scp -q $SO -i "$K" "$W/$D.tgz" gadmin@10.10.10.30:/tmp/
ssh $SO -i "$K" gadmin@10.10.10.30 "D=$D bash -s" <<'REMOTO'
set -u
instalar() { cat <<EOF
set -u; cd ~ && mkdir -p cf-e4 && cd cf-e4
if [ -e $D ]; then echo "\$(hostname): $D ya existe, no se sobrescribe"; rm -f /tmp/$D.tgz; exit 3; fi
tar -xzf /tmp/$D.tgz && rm -f /tmp/$D.tgz && cd $D && sha256sum -c --strict --quiet SHA256SUMS && chmod +x *.sh && echo "\$(hostname): $D verifica (\$(wc -l < SHA256SUMS) ficheros)"
EOF
}
O="-o BatchMode=yes -o ConnectTimeout=10 -i $HOME/.ssh/cyberflow-to-sensor"
scp -q $O /tmp/$D.tgz m4rk@10.10.60.11:/tmp/ && instalar | ssh $O m4rk@10.10.60.11 bash -s
instalar | bash -s
REMOTO
rm -r "$W"
echo "TAG=$TAG"
