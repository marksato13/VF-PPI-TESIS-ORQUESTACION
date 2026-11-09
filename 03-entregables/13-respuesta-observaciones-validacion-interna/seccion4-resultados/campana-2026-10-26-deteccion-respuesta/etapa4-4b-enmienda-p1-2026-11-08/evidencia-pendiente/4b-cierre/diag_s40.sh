#!/usr/bin/env bash
cd "$HOME" || exit 2
ssh -o BatchMode=yes -o ConnectTimeout=15 -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 'ssh -o BatchMode=yes -o ConnectTimeout=15 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "bash -s"' <<'EOS' 2>&1
B=$HOME/cf-e4/4b; C=$B/copias
echo "== COPIAS-INCOMPLETAS.txt:"; cat $C/COPIAS-INCOMPLETAS.txt | cut -c1-230
echo "== marcas: COPIAS-COMPLETAS.ok=$([ -e $C/COPIAS-COMPLETAS.ok ] && echo EXISTE || echo no) SHA256SUMS=$([ -e $C/SHA256SUMS ] && echo EXISTE || echo no) FUENTES=$(wc -l < $C/FUENTES-al-copiar.tsv 2>/dev/null) lineas cierre.t=$(cat $B/cierre.t)"
echo "== tamaños de los dos registros de tcpdump (los que fallaron):"; ls -l $B/salud/tcpdump-anillo.log $B/salud/tcpdump-via.log 2>&1 | cut -c1-120
echo "== ¿el journal los puede dar SIN sudo (solo conteo, sin escribir)?"
INI="2026-11-08 17:13:48"
echo "anillo: $(journalctl -u ppi-motor-capture --since "$INI UTC" -o short-iso-precise --no-pager 2>/dev/null | grep -c "packets captured") lecturas SIGUSR1; primera: $(journalctl -u ppi-motor-capture --since "$INI UTC" -o short-iso-precise --no-pager 2>/dev/null | grep "packets captured" | head -1 | cut -c1-70)"
echo "vía:    $(journalctl -u ppi-via-rapida@ens37 --since "$INI UTC" -o short-iso-precise --no-pager 2>/dev/null | grep -c "packets captured") lecturas SIGUSR1"
echo "journal desde: $(journalctl --no-pager -o short-iso -n 1 --reverse 2>/dev/null | head -1 | cut -c1-30) | más antiguo: $(journalctl --no-pager -o short-iso 2>/dev/null | head -2 | tail -1 | cut -c1-30)"
echo "== sudoers NOPASSWD (formas permitidas de journalctl):"; sudo -n -l 2>&1 | grep -i journalctl | cut -c1-220 | head -6
echo "== aplazamiento: timer=$(systemctl is-active logrotate.timer) tope=$(systemctl is-active cf-4b-tope.timer) vigía=$(systemctl is-active cf-4b-vigia.service)"; tail -3 /var/lib/cf-4b-rotacion/log.txt | cut -c1-200
echo "== cierre (herramienta):"; /usr/local/sbin/cf-4b-rotacion cierre 2>&1 | grep -E "FALLO|RESULTADO" | cut -c1-200
echo "== disco: $(df -h /home | tail -1)"
EOS
