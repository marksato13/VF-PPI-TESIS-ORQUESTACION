#!/usr/bin/env bash
# PASO3B b01 — bastion: declara el control normal ANTES de empezarlo (en bastion y sensor) y arranca la vigilancia
# persistente (solo lectura del sensor cada 60 s; no toca la Kali ni srv-dmz).
set -u
ID=20261101T0721Z; B=$HOME/cf-3b-$ID
[ -e "$B" ] && { echo "PARAR: ya existe $B"; exit 2; }
mkdir -p "$B"
DESDE=2026-11-01T07:32:00Z; HASTA=2026-11-01T08:05:00Z
INI_ARCH=2026-11-01T07:04:56Z   # primer PCAP con OK en archivar.log (live-20261101070456.pcap)
D=$(cat <<EOF
{"declarado_en": "$(date -u +%FT%T.%3NZ)", "control_normal": {"desde": "$DESDE", "hasta": "$HASTA",
 "seleccion": "window_end_utc en [desde, hasta], ambos incluidos", "duracion_min": 33},
 "inicio_archivo": "$INI_ARCH", "inicio_archivo_mas_230": "2026-11-01T07:08:46Z",
 "requisito": "desde >= inicio_archivo + 230 s: cumple",
 "perfiles": "seis perfiles a factor 1,0 desde 2026-11-01T07:26:15Z (k01)",
 "preparacion_fuera_del_control": ["c00 bastion 07:21:23-07:21:28 (HTTP/HTTPS/DNS desde 10.10.10.30)",
   "c05 brute-lab 07:24:02-07:24:04 (desde 10.10.10.30)", "p10b relojes 07:21:29-07:21:43"],
 "accesos_prohibidos_durante_el_control": "sin SSH a Kali ni a srv-dmz; sin sondas; sin ataques"}
EOF
)
echo "$D" > $B/control-declarado.json
echo "$D" | ssh -n sensor1 "cat > ~/cf-3b-$ID/control-declarado.json" < <(echo "$D") 2>/dev/null || echo "$D" | ssh sensor1 "cat > ~/cf-3b-$ID/control-declarado.json"
ssh -n sensor1 "sha256sum ~/cf-3b-$ID/control-declarado.json"; sha256sum $B/control-declarado.json
cat > $B/vigilar.sh <<'EOS'
#!/usr/bin/env bash
# vigilancia: una linea por minuto (solo lectura del sensor)
while :; do
  ssh -n -o BatchMode=yes -o ConnectTimeout=8 sensor1 'B=$HOME/cf-3b-20261101T0721Z
  P=$(systemctl show -p MainPID --value ppi-motor)
  c=$(tail -n 6 $HOME/cyberflow/logs/_state/ciclos.jsonl | python3 -c "import sys,json,time
cs=[json.loads(l) for l in sys.stdin]; print(\"dur=%s pend=%s edad=%.0f\" % ([round(c[\"duracion_s\"],2) for c in cs],[c[\"ventanas_pendientes\"] for c in cs], time.time()-cs[-1][\"fin_ciclo\"]))")
  m=$(tail -1 $B/recursos/muestras.jsonl | python3 -c "import sys,json;m=json.loads(sys.stdin.read());print(\"rss=%.0fMB avail=%.0fMB load1=%s\" % (m[\"rss_kb\"]/1024,m[\"memavail_kb\"]/1024,m[\"load1\"]))")
  d=$(tail -n 400 /var/log/suricata/stats.log | grep capture.kernel_drops | tail -1 | awk "{print \$NF}")
  echo "$(date -u +%FT%TZ) motor=$(systemctl is-active ppi-motor) pid=$P NR=$(systemctl show -p NRestarts --value ppi-motor) enforce=$(tr "\0" " " < /proc/$P/cmdline | grep -c -- --enforce) cap=$(systemctl is-active ppi-motor-capture) sur=$(systemctl is-active suricata) drops=$d | $c | $m | arch: $(cat $B/archivo-pcap/ESTADO.txt | cut -c1-60) | disco=$(df -P / | awk "NR==2{print \$5}")"' >> $HOME/cf-3b-20261101T0721Z/vigilancia.log 2>&1
  sleep 60
done
EOS
setsid nohup bash $B/vigilar.sh > /dev/null 2>&1 < /dev/null &
echo $! > $B/vigilar.pid
sleep 5; echo "## b01 $(date -u +%FT%T.%3NZ) control declarado [$DESDE, $HASTA]; vigilancia PID $(cat $B/vigilar.pid)"
tail -1 $B/vigilancia.log
