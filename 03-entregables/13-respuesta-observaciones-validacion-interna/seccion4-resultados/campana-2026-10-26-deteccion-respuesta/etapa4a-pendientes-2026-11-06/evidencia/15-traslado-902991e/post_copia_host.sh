set -u
# Comprobación POST-COPIA de solo lectura (§6 de TRASLADO-PAQUETE-902991e-r2.md). No escribe nada.
echo "### $(hostname) $(whoami) $(date -u +%FT%TZ)"
cd ~/cf-e4 || { echo "SIN ~/cf-e4"; exit 1; }
grep -x 'SUMAS=8480f0e02952216d0a371f13201657e81e27ccc53fef2d5917d5dc74a68df30c' paquete-902991e.VERIFICADO.txt > /dev/null && echo "marca-OK" || echo "MARCA-FALLO"
(cd paquete-902991e && echo "SHA256SUMS interno $(sha256sum < SHA256SUMS | cut -c1-64)" && sha256sum -c --strict --quiet SHA256SUMS && echo hashes-OK)
diff <(sed -E 's/^[0-9a-f]{64}  //' paquete-902991e/SHA256SUMS | LC_ALL=C sort) \
     <(cd paquete-902991e && find . ! -type d ! -path ./SHA256SUMS | LC_ALL=C sort) > /dev/null && echo "inventario-exacto $(wc -l < paquete-902991e/SHA256SUMS)" || echo "INVENTARIO-DISTINTO"
echo "evaluador $(sha256sum < paquete-902991e/deploy/etapa4/sensor1/evaluar_ecarga.py | cut -c1-64)"
echo "ecarga/SHA256SUMS $(sha256sum < paquete-902991e/deploy/etapa4/ecarga/SHA256SUMS | cut -c1-64)"
(cd paquete-902991e/deploy/etapa4/ecarga && sha256sum -c --strict --quiet SHA256SUMS && echo ecarga-OK)
grep -x 'VERSION = "evaluar_s14 2026-11-06.2"' paquete-902991e/deploy/etapa4/ecarga/evaluar_s14.py
grep -x 'VERSION = "construir_entrada 2026-11-06.3"' paquete-902991e/deploy/etapa4/ecarga/construir_entrada.py
echo "aviso: $(head -1 paquete-a12deae.NO-USAR.txt)"; grep -c 902991e paquete-a12deae.NO-USAR.txt
echo "parciales: $(ls -d .paquete-902991e.parcial.* 2>/dev/null | wc -l)"
echo "registro: $(tail -1 traslado-902991e.20261106T194952Z-10146.*.log)"
echo "paquete-a12deae: $(find paquete-a12deae -type f | wc -l) ficheros; $( [ -f paquete-a12deae/deploy/etapa4/ecarga/SHA256SUMS ] && (cd paquete-a12deae/deploy/etapa4/ecarga && sha256sum -c --strict --quiet SHA256SUMS && echo 'ecarga a12deae intacta (9ff24889?)' ; sha256sum < SHA256SUMS | cut -c1-8))"
echo "contenido ~/cf-e4:"; ls -1A
