#!/usr/bin/env bash
B=$HOME/cf-paso2-20261101T0254Z
echo "replay procesos: $(pgrep -fc replay_motor.py)  rc: $(cat $B/replay/rc.txt 2>/dev/null)"
tail -n1 $B/replay/ciclos-arnes.jsonl 2>/dev/null | python3 -c 'import sys,json,time;c=json.loads(sys.stdin.read());print("ultimo ciclo simulado:", time.strftime("%H:%M:%S",time.gmtime(c.get("t",c.get("ahora",0)))), {k:v for k,v in c.items() if k in ("t","ahora","duracion_s")})' 2>&1
wc -l $B/replay/ciclos-arnes.jsonl $B/replay/motor_decision.log 2>/dev/null
grep -iE "traceback|error" $B/replay/stderr.txt | head -3
ls -la --time-style=+%F_%T $HOME/cyberflow/scripts/engine/__pycache__/ | head -12
stat -c '%U:%G %a %n' $HOME/cyberflow/scripts/engine/__pycache__ $HOME/cyberflow/scripts/engine
systemctl show ppi-motor -p ProtectSystem,ReadWritePaths,User
free -m | sed -n 2p
