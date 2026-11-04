set -u
# [BASTIÓN gadmin] Recoge evidencia de la 4A (solo manifiestos de respaldos, nunca su contenido)
O=~/cf-e4/evidencia-4a-$(date -u +%Y%m%dT%H%M%SZ); mkdir -p $O/sensor1 $O/srvdmz $O/bastion
man() {  # imprime, por respaldo, la lista de ficheros, SHA256SUMS y RESPALDO.txt/ruleset.lectura/LEEME.txt
  for r in ~/respaldos-etapa4/*/; do
    echo "===== $r"; ls -la "$r" | sed 1d
    for f in SHA256SUMS RESPALDO.txt ruleset.lectura LEEME.txt; do [ -f "$r$f" ] && { echo "--- $f"; cat "$r$f"; }; done
    [ -f "$r/SHA256SUMS" ] && (cd "$r" && echo "--- verificación: $(sha256sum -c SHA256SUMS 2>&1 | grep -vc ': OK$') fallos")
  done
}
man > $O/bastion/respaldos-manifiestos.txt 2>&1
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "$(declare -f man); man; echo '===== volcado v1'; ls -l ~/respaldo-cyberflow-v1-*.nft 2>/dev/null; sha256sum ~/respaldo-cyberflow-v1-*.nft 2>/dev/null" > $O/sensor1/respaldos-manifiestos.txt 2>&1
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 "$(declare -f man); man; ls -d ~/respaldos-etapa4/../cf-e4/* 2>/dev/null; ls -la ~/srvdmz-evidencia-* ~/respaldos-etapa4/srvdmz-evidencia-* 2>/dev/null; ls -d ~/*evidencia* 2>/dev/null" > $O/srvdmz/respaldos-manifiestos.txt 2>&1
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd ~/cf-e4 && tar czf - 4a' > $O/sensor1/observacion-4a.tgz
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd ~/cf-e4/4a && sha256sum -c SHA256SUMS | grep -vc ": OK$"' > $O/sensor1/observacion-verificacion.txt
(cd $O && find . -type f | sort | xargs sha256sum > SHA256SUMS)
tar czf $O.tgz -C ~/cf-e4 $(basename $O) && echo "$O.tgz $(sha256sum < $O.tgz | cut -c1-64)"
for f in $O/*/respaldos-manifiestos.txt; do echo "== $f: $(grep -c '^=====' $f) respaldos; fallos: $(grep 'verificación' $f | tr '\n' ' ')"; done
cat $O/sensor1/observacion-verificacion.txt
