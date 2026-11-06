# BLOQUE=estado_r2  (P0 r2, solo lectura) en bastión, Sensor1 o srv-dmz: sincronización del reloj y procesos con
# --aplicar/--enforce (P3). Lo demás (zona, chrony, recursos) es INFO. rc 0 si todas las lecturas críticas se hicieron.
set -u
B=estado_r2; E=0
req() { printf 'REQ %s %s %s\n' "$1" "$2" "${3:-}"; [ "$2" = ERROR ] && E=3; return 0; }
info() { printf 'INFO %s\n' "$*"; }
fin() { printf 'FIN_BLOQUE %s rc=%s\n' "$B" "$E"; exit "$E"; }
H=${1:-}; case "$H" in bastion|sensor1|srvdmz) ;; *) echo "uso: host"; E=2; fin;; esac
info "== $H $(hostname 2>&1) $(id -un 2>&1) epoch $(date -u +%s 2>&1) utc $(date -u +%FT%TZ 2>&1)"
t=$(timedatectl show -p Timezone -p NTP -p NTPSynchronized 2>&1); r=$?
printf '%s\n' "$t" | sed 's/^/INFO timedatectl /'
if [ $r != 0 ]; then req "X.sincronizado.$H" ERROR "timedatectl rc $r"
else
  case "$(sed -n 's/^NTPSynchronized=//p' <<<"$t")" in
    yes) req "X.sincronizado.$H" CUMPLE "NTPSynchronized=yes";;
    no)  req "X.sincronizado.$H" NO_CUMPLE "NTPSynchronized=no";;
    *)   req "X.sincronizado.$H" ERROR "timedatectl sin NTPSynchronized";;
  esac
fi
for s in chrony chronyd systemd-timesyncd ntp ntpsec; do printf 'INFO servicio %s=%s\n' "$s" "$(systemctl is-active "$s" 2>/dev/null)"; done
if command -v chronyc > /dev/null; then chronyc -n tracking 2>&1 | sed 's/^/INFO chronyc /'; info "rc_chronyc=${PIPESTATUS[0]}"; fi
timedatectl timesync-status 2>&1 | head -12 | sed 's/^/INFO timesync /'
a=$(ps -eo pid,args 2>&1); r=$?
if [ $r != 0 ] || [ -z "$a" ]; then req "P3.procesos.$H" ERROR "ps rc $r: no se pudo leer"
else
  n=$(grep -E -- '--(enforce|aplicar)( |$)' <<<"$a"); g=$?
  case $g in
    0) req "P3.procesos.$H" NO_CUMPLE "$(grep -c . <<<"$n") proceso(s): $(tr '\n' ';' <<<"$n" | cut -c1-300)";;
    1) req "P3.procesos.$H" CUMPLE "0 procesos con --aplicar/--enforce";;
    *) req "P3.procesos.$H" ERROR "grep rc $g";;
  esac
fi
df -h / /home 2>&1 | sed 's/^/INFO df /'; free -m 2>&1 | sed 's/^/INFO free /'; info "uptime $(uptime 2>&1)"
fin
