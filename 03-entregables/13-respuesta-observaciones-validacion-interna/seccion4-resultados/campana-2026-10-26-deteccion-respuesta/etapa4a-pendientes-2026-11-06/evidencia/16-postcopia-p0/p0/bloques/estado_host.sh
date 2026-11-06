# Bloque P0 (solo lectura): reloj, sincronización, procesos con --aplicar/--enforce, recursos. rc 0 si todo se leyó.
H=${1:-?}; e=0
echo "== $H $(hostname) $(id -un)"
echo "epoch $(date -u +%s.%N) utc $(date -u +%FT%TZ)"
timedatectl show -p Timezone -p NTP -p NTPSynchronized -p LocalRTC 2>&1; r=$?; echo "rc_timedatectl=$r"; [ $r = 0 ] || e=3
for s in chrony chronyd systemd-timesyncd ntp ntpsec; do printf '%s=%s ' "$s" "$(systemctl is-active "$s" 2>/dev/null)"; done; echo
if command -v chronyc > /dev/null; then chronyc -n tracking 2>&1; echo "rc_chronyc=$?"; fi
timedatectl timesync-status 2>&1 | head -12; echo "rc_timesync_status=${PIPESTATUS[0]}"
echo "-- procesos con --aplicar/--enforce:"
a=$(ps -eo pid,args 2>&1); r=$?
if [ $r = 0 ] && [ -n "$a" ]; then n=$(grep -E -- '--(enforce|aplicar)( |$)' <<<"$a" | grep -v grep); echo "${n:-ninguno}"; [ -n "$n" ] && echo "CON_APLICAR=si" || echo "CON_APLICAR=no"
else echo "ps rc $r: no se pudo leer"; e=3; fi
df -h / /home 2>&1; free -m 2>&1; uptime
exit $e
