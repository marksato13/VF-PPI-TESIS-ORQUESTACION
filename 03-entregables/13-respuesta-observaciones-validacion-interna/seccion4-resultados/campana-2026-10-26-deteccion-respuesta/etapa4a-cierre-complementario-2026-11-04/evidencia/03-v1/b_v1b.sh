set -u
ls -l ~/relay-feed.sh; sha256sum ~/relay-feed.sh; grep -vE '^\s*$' ~/relay-feed.sh | grep -viE 'BEGIN|PRIVATE' | head -60
ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'systemctl cat ppi-enforce-agent.service ppi-enforce-agent.timer | grep -vE "^\s*$"; systemctl show ppi-enforce-agent.timer ppi-enforce-agent.service -p ActiveState -p UnitFileState; ls -la ~/feed /home/adminsrvdmz/cyberflow-feed 2>&1 | head -20'
