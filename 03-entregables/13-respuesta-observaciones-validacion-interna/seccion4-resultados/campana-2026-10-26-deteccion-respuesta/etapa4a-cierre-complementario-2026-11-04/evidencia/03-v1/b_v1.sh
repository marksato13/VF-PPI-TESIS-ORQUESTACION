set -u
echo "### bastión $(date -u +%FT%TZ)"
systemctl list-units --all --no-pager '*relay*' '*ppi*' '*cyberflow*' | cat
systemctl list-unit-files --no-pager '*relay*' '*ppi*' '*cyberflow*' | cat
systemctl list-timers --all --no-pager | grep -iE 'relay|ppi|cyberflow'
for u in $(systemctl list-unit-files --no-legend --no-pager '*relay*' '*ppi*' | awk '{print $1}'); do echo "===== $u"; systemctl cat $u 2>/dev/null | grep -vE '^\s*$'; systemctl show $u -p ActiveState -p UnitFileState -p TriggeredBy -p Triggers -p WantedBy -p ExecMainStartTimestamp 2>/dev/null; done
journalctl -u ppi-relay.service --since -2min --no-pager 2>&1 | tail -5
ls -la ~/cf-e4 | head; ls ~/respaldos-etapa4
