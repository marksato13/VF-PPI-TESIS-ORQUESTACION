#!/usr/bin/env bash
# [LAPTOP Git Bash -> BASTIÓN gadmin -> SENSOR1 m4rk] SOLO LECTURA de /proc y /sys, sin sudo: capacidad de Sensor1 y
# disponibilidad de las fuentes necesarias para definir S14. No toca servicios, no arranca nada, no escribe en Sensor1.
set -u
ssh -o BatchMode=yes -i "$HOME/.ssh/id_ed25519" gadmin@10.10.10.30 \
  'ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 bash -s' <<'R'
echo "fecha $(date -u +%FT%TZ) host $(hostname) kernel $(uname -r)"
echo "nproc $(nproc) cpus_en_stat $(grep -c '^cpu[0-9]' /proc/stat)"
grep -E '^(model name|cpu MHz)' /proc/cpuinfo | sort | uniq -c
grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree)' /proc/meminfo
echo "--- PSI"
for r in cpu io memory; do if [ -r /proc/pressure/$r ]; then echo "$r:"; sed 's/^/  /' /proc/pressure/$r; else echo "$r: NO DISPONIBLE ($(ls /proc/pressure 2>&1 | head -1))"; fi; done
grep -o 'psi=[0-9]' /proc/cmdline || echo "cmdline sin psi="
echo "--- discos"
lsblk -d -o NAME,ROTA,SIZE,TYPE,MODEL 2>&1
cat /sys/block/sda/queue/scheduler 2>&1; echo "nr_requests $(cat /sys/block/sda/queue/nr_requests 2>&1)"
df -k --output=target,source,size,avail / /home /var/log 2>&1
echo "--- NIC ens37: colas e IRQ"
ls /sys/class/net/ens37/queues/ 2>&1 | tr '\n' ' '; echo
grep -E 'ens37|vmxnet|eth' /proc/interrupts | cut -c1-160
for i in $(grep -E 'ens37' /proc/interrupts | cut -d: -f1); do echo "irq $i afinidad $(cat /proc/irq/$i/smp_affinity_list 2>&1)"; done
echo "rps: $(cat /sys/class/net/ens37/queues/rx-0/rps_cpus 2>&1)"
echo "--- softnet_stat (por CPU: procesados, dropped, time_squeeze)"
awk '{printf "cpu%d %d %d %d\n", NR-1, strtonum("0x"$1), strtonum("0x"$2), strtonum("0x"$3)}' /proc/net/softnet_stat
echo "--- /proc/stat por CPU (cabecera de columnas: user nice system idle iowait irq softirq steal)"
grep '^cpu' /proc/stat
echo "USER_HZ $(getconf CLK_TCK)"
echo "--- vmstat swap y fallos"
grep -E '^(pswpin|pswpout|pgmajfault|oom_kill) ' /proc/vmstat
echo "--- hilos de Suricata"
p=$(pgrep -o suricata); ls /proc/$p/task | while read t; do printf "%s " "$(cat /proc/$p/task/$t/comm)"; done; echo
echo "--- legible para m4rk sin sudo"
for f in /proc/pressure/cpu /proc/pressure/io /proc/pressure/memory /proc/vmstat /proc/diskstats /proc/net/softnet_stat; do [ -r $f ] && echo "OK $f" || echo "NO $f"; done
R
echo "rc=$?"
