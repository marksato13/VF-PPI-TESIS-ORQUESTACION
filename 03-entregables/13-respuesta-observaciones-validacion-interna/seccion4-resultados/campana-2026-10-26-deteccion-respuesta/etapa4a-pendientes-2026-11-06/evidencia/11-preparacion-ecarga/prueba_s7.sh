#!/usr/bin/env bash
# [LAPTOP Git Bash -> BASTIÓN gadmin] Prueba EN SECO del procedimiento de S7 (y del cruce O1/O6/O8–O10): se deriva
# obs_p4_post.sh del 06-nov cambiando SOLO su carpeta fija (O=) por la carpeta seco del bastión, y se ejecuta sobre las
# 3 muestras de la prueba de muestreo. Solo lecturas (traza del agente con sudo -n cat, ya permitido). Sin valor de medida.
set -u
DOC="$1"
SECO=$(ssh -n -o BatchMode=yes -i "$HOME/.ssh/id_ed25519" gadmin@10.10.10.30 'ls -d ~/cf-e4/ecarga-v2-seco-*/bastion | tail -1')
echo "carpeta seco: $SECO"
read D A < <(ssh -n -o BatchMode=yes -i "$HOME/.ssh/id_ed25519" gadmin@10.10.10.30 "grep '^### ' $SECO/muestras.txt | awk '{print \$3}' | sed -n '1p;\$p' | tr '\n' ' '")
echo "periodo de prueba: $D – $A"
echo "sha256 obs_p4_post.sh original (06-nov): $(sha256sum < "$DOC" | cut -c1-64)"
sed -E "s#^O=.*#O=$SECO#" "$DOC" > /tmp/obs_p4_post_ecarga.sh
diff "$DOC" /tmp/obs_p4_post_ecarga.sh
echo "sha256 derivado: $(sha256sum < /tmp/obs_p4_post_ecarga.sh | cut -c1-64)"
ssh -o BatchMode=yes -i "$HOME/.ssh/id_ed25519" gadmin@10.10.10.30 "bash -s $D $A" < /tmp/obs_p4_post_ecarga.sh 2>&1 | grep -v '^   firma_invalida\|^   paquete_invalido' | head -40
echo "rc=${PIPESTATUS[0]}"
