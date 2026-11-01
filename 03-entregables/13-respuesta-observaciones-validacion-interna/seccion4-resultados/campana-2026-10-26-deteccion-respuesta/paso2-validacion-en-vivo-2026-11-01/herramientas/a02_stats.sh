#!/usr/bin/env bash
tail -n 120 /var/log/suricata/stats.log | grep -E 'Date|capture|drop' | head -24
grep -c Date /var/log/suricata/stats.log
