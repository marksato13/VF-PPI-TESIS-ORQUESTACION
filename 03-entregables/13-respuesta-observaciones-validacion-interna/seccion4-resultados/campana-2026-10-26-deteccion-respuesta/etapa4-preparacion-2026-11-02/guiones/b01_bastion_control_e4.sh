#!/usr/bin/env bash
# [BASTIÓN gadmin] ETAPA4 b01 — uso: b01_bastion_control_e4.sh <4b|4c> <DESDE_ISO> <HASTA_ISO> <INICIO_ARCHIVO_ISO>
# Declara el control normal ANTES de empezarlo (en el bastión y en el sensor) y arranca la vigilancia persistente
# (solo lectura del sensor cada 60 s; no toca la Kali ni srv-dmz). Igual que b01 del 3B salvo: rutas de la Etapa 4
# (_state-e4, feed-v2, salud), y las comprobaciones de los requisitos temporales se hacen aquí y no a mano.
# Resultado esperado: "control declarado [DESDE, HASTA]" y una primera línea de vigilancia.
# Parada: DESDE < INICIO_ARCHIVO + 230 s, DESDE en el pasado, duración menor que la del protocolo.
set -u
FASE=${1:?fase}; DESDE=${2:?desde}; HASTA=${3:?hasta}; INI=${4:?inicio_archivo}
case "$FASE" in 4b) MIN_S=7200;; 4c) MIN_S=1800;; *) echo "PARAR: fase $FASE"; exit 2;; esac
B=$HOME/cf-e4/$FASE
[ -e "$B/control-declarado.json" ] && { echo "PARAR: ya hay control declarado en $B"; exit 2; }
mkdir -p "$B"
d=$(date -d "$DESDE" +%s) || exit 2; h=$(date -d "$HASTA" +%s) || exit 2; i=$(date -d "$INI" +%s) || exit 2
[ "$d" -ge $(( i + 230 )) ] || { echo "PARAR: DESDE < inicio_archivo + 230 s"; exit 2; }
[ "$d" -gt "$(date +%s)" ] || { echo "PARAR: DESDE ya pasó: se declara ANTES de empezar"; exit 2; }
[ $(( h - d )) -ge "$MIN_S" ] || { echo "PARAR: duración $(( h - d )) s < $MIN_S s (protocolo $FASE)"; exit 2; }
J=$(python3 - "$FASE" "$DESDE" "$HASTA" "$INI" "$(( h - d ))" <<'PY'
import json, sys, time
f, de, ha, ini, dur = sys.argv[1:6]
print(json.dumps({"declarado_en": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "fase": f,
                  "control_normal": {"desde": de, "hasta": ha, "duracion_s": int(dur),
                                     "seleccion": "window_end_utc en [desde, hasta], ambos incluidos; clase de cada "
                                                  "ventana por [w - 60, w] (SALUD-CAPTURA.md §3)"},
                  "inicio_archivo": ini, "requisito": "desde >= inicio_archivo + 230 s: cumple",
                  "perfiles": "seis perfiles a factor 1,0 (k01_clientes_factor1_e4.sh); config en clientes ~/cf-e4/" + f,
                  "accesos_prohibidos_durante_el_control": "sin SSH a Kali ni a srv-dmz; sin sondas; sin ataques"},
                 ensure_ascii=False))
PY
)
echo "$J" > "$B/control-declarado.json"
echo "$J" | ssh -o BatchMode=yes sensor1 "cat > ~/cf-e4/$FASE/control-declarado.json"
ssh -n -o BatchMode=yes sensor1 "sha256sum ~/cf-e4/$FASE/control-declarado.json"; sha256sum "$B/control-declarado.json"
cat > "$B/vigilar.sh" <<EOS
#!/usr/bin/env bash
# vigilancia $FASE: una línea por minuto (solo lectura del sensor)
while :; do
  ssh -n -o BatchMode=yes -o ConnectTimeout=8 sensor1 'B=\$HOME/cf-e4/$FASE
  P=\$(systemctl show -p MainPID --value ppi-motor)
  c=\$(tail -n 6 \$HOME/cyberflow/logs/_state-e4/ciclos.jsonl | python3 -c "import sys,json,time
cs=[json.loads(l) for l in sys.stdin]; print(\"dur=%s pend=%s edad=%.0f\" % ([round(c[\"duracion_s\"],2) for c in cs],[c.get(\"ventanas_pendientes\") for c in cs], time.time()-cs[-1][\"fin_ciclo\"]))" 2>&1 | cut -c1-160)
  d=\$(tail -n 400 /var/log/suricata/stats.log | grep capture.kernel_drops | tail -1 | awk "{print \\\$NF}")
  t=\$(sudo -n journalctl -u ppi-motor-capture --since -2min -o cat --no-pager | grep "packets captured" | tail -1)
  echo "\$(date -u +%FT%TZ) motor=\$(systemctl is-active ppi-motor) NR=\$(systemctl show -p NRestarts --value ppi-motor) enforce=\$(tr "\0" " " < /proc/\$P/cmdline | grep -c -- --enforce) cap=\$(systemctl is-active ppi-motor-capture)/NR=\$(systemctl show -p NRestarts --value ppi-motor-capture) via=\$(systemctl is-active ppi-via-rapida@ens37) sur=\$(systemctl is-active suricata) drops_sur=\$d | tcpdump: \$t | \$c | arch: \$(cut -c1-60 \$B/archivo-pcap/ESTADO.txt) | disco=\$(df -P /home | awk "NR==2{print \\\$5}")"' >> $B/vigilancia.log 2>&1
  sleep 60
done
EOS
setsid nohup bash "$B/vigilar.sh" > /dev/null 2>&1 < /dev/null &
echo $! > "$B/vigilar.pid"
sleep 8; echo "## b01-e4 $(date -u +%FT%T.%3NZ) control declarado [$DESDE, $HASTA]; vigilancia PID $(cat "$B/vigilar.pid")"
tail -1 "$B/vigilancia.log"
