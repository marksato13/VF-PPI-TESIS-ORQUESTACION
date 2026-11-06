set -u
# [SENSOR1 m4rk] Solo lectura: el motor_startup del arranque del 05-nov 23:59 quedó en el registro rotado (.1).
grep -F '"event": "motor_startup"' ~/cyberflow/logs/motor_decision.log.1 | tail -1 | python3 -c '
import json, sys
r = json.loads(sys.stdin.readline())
print("disparo:", r.get("disparo"), "| umbral del manifiesto presente:", "-0.5693969936322356" in json.dumps(r),
      "| detector:", r.get("detector_name"), "| horizonte:", r.get("horizonte"))
print("claves:", sorted(r)[:40])'
