set -u
systemctl cat ppi-dashboard | grep -vE '^\s*$'
ls -la /etc/systemd/system/ppi-dashboard.service.d/ /etc/systemd/system/ppi-motor-capture.service.d/ 2>&1
ls -la ~/cf-e4/ ~/cf-e4/4a 2>&1 | head -40
cat /etc/logrotate.d/cyberflow-etapa4 2>&1
sudo -n -l 2>&1 | grep -vE '^\s*$' | head -30
