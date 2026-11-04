set -u
# [Sensor1 m4rk] Verificación de la fase A (solo lectura).
C=/home/m4rk/cf-e4/cierre4a; PY=/home/m4rk/cyberflow/.venv/bin/python
EV=$(ls -d $C/sudo-A-* 2>/dev/null | tail -n 1); echo "evidencia: $EV"
[ -n "$EV" ] && { tail -n 40 $EV/salida.txt; echo; cat $EV/t-restart-captura.txt; }
echo "== unidades"
for u in ppi-publicar-feed.timer ppi-publicar-feed.service ppi-publicar-feed-v2.service ppi-motor.service ppi-motor-capture.service ppi-dashboard.service ppi-via-rapida@ens37.service suricata.service; do
  printf '%s ' $u; systemctl show $u -p ActiveState -p UnitFileState -p MainPID -p ExecMainStartTimestamp --value | tr '\n' ' '; echo; done
systemctl list-timers --all --no-pager | grep -i publicar || echo "sin temporizador publicar en list-timers activos"
ps -eo pid,user,lstart,args | grep -E 'publicar_feed.py|acuse' | grep -v grep || echo "sin procesos v1"
stat -c '%n %y' /home/m4rk/feed/feed.json /home/m4rk/feed/acuses/srv-dmz.json
echo "== drop-ins"; systemctl cat ppi-motor-capture ppi-dashboard 2>/dev/null | grep -E '^# /|ExecStartPost|modo-panel'
tr '\0' ' ' < /proc/$(systemctl show -p MainPID --value ppi-dashboard)/cmdline | grep -o -- '--modo-panel v2 --cadena-v2-dir [^ ]* --modo-respuesta [^ ]*'
journalctl --no-pager -u ppi-dashboard --since "-15min" | grep -E 'modo|Preparar|incidencia' | tail -n 5
echo "== captura: primer fichero y rotaciones tras el reinicio"
T=$(cut -d. -f1 $EV/t-restart-captura.txt)
journalctl --no-pager -o short-iso-precise -u ppi-motor-capture --since @$T | head -n 12
find /var/lib/ppi-motor-capture -name 'live-*.pcap' -newermt @$((T-1)) -printf '%TY-%Tm-%Td %TT %u:%g %m %s %f\n' | sort | head -n 8
echo "no legibles por m4rk (todo el anillo):"; for f in /var/lib/ppi-motor-capture/live-*.pcap; do [ -r "$f" ] || echo "  $f"; done
echo "grupo tcpdump restante: $(find /var/lib/ppi-motor-capture -name 'live-*.pcap' -group tcpdump | wc -l)"
P=$(find /var/lib/ppi-motor-capture -name 'live-*.pcap' -newermt @$((T-1)) -printf '%T@ %p\n' | sort -n | head -n 1 | cut -d' ' -f2)
echo "primer fichero: $P"; ls -la --time-style=full-iso "$P"
$PY - "$P" <<'EOF'
import struct, sys
b = open(sys.argv[1], 'rb').read()
mag = b[:4].hex(); n = 0; off = 24
while off + 16 <= len(b):
    incl = struct.unpack('<I', b[off+8:off+12])[0]; off += 16 + incl; n += 1
print("magic", mag, "bytes", len(b), "paquetes", n, "completo", off == len(b))
EOF
echo "== motor: decisiones tras el reinicio"
L=/home/m4rk/cyberflow/logs/motor_decision.log
$PY - $L $T <<'EOF'
import json, sys, collections
T = float(sys.argv[2]); ile = collections.Counter(); motivos = set(); n = 0; ult = None
with open(sys.argv[1]) as fh:
    fh.seek(0, 2); fh.seek(max(0, fh.tell() - 30_000_000)); fh.readline()
    for l in fh:
        if '"event": "decision"' not in l: continue
        d = json.loads(l)
        if d.get("decidido_en", 0) < T: continue
        n += 1; ile[d.get("pcaps_ilegibles")] += 1; motivos.add(json.dumps(d.get("pcaps_ilegibles_motivo"))); ult = d
print("decisiones tras reinicio", n, "pcaps_ilegibles", dict(ile), "motivos", motivos)
if ult: print("ultima", ult.get("decision_id"), ult.get("decision"), "aplicar?", {k: ult.get(k) for k in ("modo", "enforce", "aplicar") if k in ult})
EOF
tail -n 400 /home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl | $PY -c '
import json,sys,time
T='$T'
c=[json.loads(l) for l in sys.stdin if l.strip()]
c=[x for x in c if x.get("inicio_ciclo",0)>=T]
d=[x["duracion_s"] for x in c]
print("ciclos tras reinicio", len(c), "dur max", max(d) if d else None, "p50", sorted(d)[len(d)//2] if d else None, "disparos", sorted(set(x.get("disparo") for x in c)))
if c: print("ultimo ciclo hace", round(time.time()-c[-1]["fin_ciclo"],1), "s")'
journalctl --no-pager -u ppi-motor --since @$T | grep -iE 'permission|error|traceback' | tail -n 5 || true
echo "== feed v2 y nft"
ls -la --time-style=full-iso /home/m4rk/feed-v2/ | grep -E 'traza|senales-if|feed.json'
sudo -n nft list ruleset 2>/dev/null | sha256sum
grep -c -- '--aplicar\|--enforce' /proc/*/cmdline 2>/dev/null | grep -v ':0$' || echo "ningún proceso con --aplicar/--enforce"
echo "== muestreadores"; for n in muestrear fino; do echo "$n vivo: $(kill -0 $(cat $C/salud/$n.pid) 2>/dev/null && echo si || echo NO)"; done
