echo "== syslog.3.gz 05-oct 20:2x-20:5x por programa"
zcat /var/log/syslog.3.gz | grep -E '2026-10-05T20:(2[0-9]|3[0-9]|4[0-9]|5[0-5])' | awk '{print $3}' | sed 's/\[.*//' | sort | uniq -c | sort -rn | head -20
echo "== lineas no CRON/sshd/systemd"
zcat /var/log/syslog.3.gz | grep -E '2026-10-05T20:(2[0-9]|3[0-9]|4[0-9]|5[0-5])' | grep -vE ' (CRON|sshd|systemd|systemd-logind)\[' | cut -c1-260 | head -40
echo "== CRON CMD 20:25-20:50"
zcat /var/log/syslog.3.gz | grep -E '2026-10-05T20:(2[5-9]|3[0-9]|4[0-9])' | grep 'CMD' | cut -c1-200 | head -40
echo "== auth.log sshd 10.10.10.30 20:25-20:50"
zcat /var/log/auth.log.3.gz | grep -E '2026-10-05T20:(2[5-9]|3[0-9]|4[0-9])' | grep -E 'Accepted|Disconnected|session (opened|closed)' | cut -c1-200 | head -80
