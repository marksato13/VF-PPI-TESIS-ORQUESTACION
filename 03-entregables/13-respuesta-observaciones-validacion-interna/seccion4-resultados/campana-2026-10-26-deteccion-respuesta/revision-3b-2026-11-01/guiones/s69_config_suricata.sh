set -u
grep -nE "^\s*(stats|interval|enabled)\b|^stats:" /etc/suricata/suricata.yaml | head -20
awk '/^stats:/{f=1} f&&NR<9999{print; n++} n>8{exit}' /etc/suricata/suricata.yaml
B=$HOME/cf-3b-20261101T0721Z; ls $B; ls $B/copias | head -40; du -sh $B/copias/eve-segmento.json
