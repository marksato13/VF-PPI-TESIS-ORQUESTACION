echo "#### AUTH"
zcat /var/log/auth.log.3.gz | grep -E '2026-10-05T(20:(1[5-9]|[2-5][0-9])|21:0)' | grep -E 'sshd\[[0-9]+\]: (Accepted|Disconnected)'
echo "#### RUNS"
nl -ba ~/cf-r42/runs.txt | sed -n '2600,2800p'
echo "#### PUBLICAR"
nl -ba ~/feed/publicar.log | sed -n '2600,2800p' | tr -d '\000'
echo "#### SHA"
sha256sum ~/feed/publicar.log /var/log/auth.log.3.gz /var/log/syslog.3.gz /var/log/syslog.4.gz
