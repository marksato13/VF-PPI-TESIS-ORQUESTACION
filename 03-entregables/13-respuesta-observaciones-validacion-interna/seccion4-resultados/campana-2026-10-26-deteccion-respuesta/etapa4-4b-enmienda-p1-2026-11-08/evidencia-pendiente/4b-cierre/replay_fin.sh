#!/usr/bin/env bash
cd "$HOME" || exit 2
ssh -o BatchMode=yes -o ConnectTimeout=15 -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 'ssh -o BatchMode=yes -o ConnectTimeout=15 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "bash -s"' <<'EOS' 2>&1
O=$HOME/cf-e4/4b/replay; B=$HOME/cf-e4/4b
echo "rc.txt: $(cat $O/rc.txt) | inicio: $(cat $O/inicio.txt) | fin: $(cat $O/fin.txt)"
echo "procesos replay: $(pgrep -fc replay_motor.py)"
echo "stderr (últimas 6):"; tail -6 $O/stderr.txt | cut -c1-200
echo "--- time -v:"; grep -E "Elapsed|Maximum resident|Exit status|Command exited" $O/stderr.txt | head
echo "--- salida:"; ls -la $O | head -20
echo "--- s40 NO iniciado?: cierre.t=$([ -e $B/cierre.t ] && echo EXISTE || echo no_existe) COPIAS-COMPLETAS.ok=$([ -e $B/copias/COPIAS-COMPLETAS.ok ] && echo EXISTE || echo no_existe) SHA256SUMS=$([ -e $B/copias/SHA256SUMS ] && echo EXISTE || echo no_existe) archivo-pcap.rc=$([ -e $B/archivo-pcap.rc ] && echo EXISTE || echo no_existe)"
echo "ventanas inventario: $(wc -l < $O/motor_decision.log)"
tail -1 $O/motor_decision.log | python3 -c "import sys,json;j=json.loads(sys.stdin.read());print('última decisión:',j.get('window_end') or j.get('decision_id'))" 2>&1
echo "servicios: motor=$(systemctl is-active ppi-motor) cap=$(systemctl is-active ppi-motor-capture) via=$(systemctl is-active ppi-via-rapida@ens37) suricata=$(systemctl is-active suricata)"
echo "archivador: $(cat $B/archivo-pcap/ESTADO.txt | cut -c1-90)"
echo "aplazamiento: logrotate.timer=$(systemctl is-active logrotate.timer) tope=$(systemctl is-active cf-4b-tope.timer) vigía=$(systemctl is-active cf-4b-vigia.service)"
EOS
