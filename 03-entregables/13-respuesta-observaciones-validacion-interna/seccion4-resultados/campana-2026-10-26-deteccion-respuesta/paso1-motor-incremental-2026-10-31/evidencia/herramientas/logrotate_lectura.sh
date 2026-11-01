#!/bin/bash
# Solo lectura, sin sudo: que configuraciones de logrotate mencionan los registros del motor y que dice el modo -d.
ls -la /etc/logrotate.d/
grep -n "include\|tabooext\|taboopat" /etc/logrotate.conf
grep -ln "cyberflow/logs" /etc/logrotate.d/* 2>/dev/null
/usr/sbin/logrotate -d /etc/logrotate.conf > /tmp/lr-global.txt 2>&1; echo "rc=$?"
wc -l /tmp/lr-global.txt
grep -n -i -E "duplicate|error" /tmp/lr-global.txt | grep -v "state file" | head -20
grep -n -E "reading config file|motor_decision" /tmp/lr-global.txt | head -40
rm -f /tmp/lr-global.txt
grep -n "cyberflow" /etc/logrotate.d/suricata.orig-cyberflow | head
ls -la /home/m4rk/cyberflow/logs/ | head -5
