#!/usr/bin/env bash
# PREFLIGHT 11b — sensor: DETIENE solo el archivador de la prueba (PID guardado, comprobando su cmdline) y verifica
# codigo de salida, ESTADO.txt, log, inventario por marca de paquete, hashes de las copias y cobertura del intervalo.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
A=$HOME/bin/archivar_captura.sh; R=/var/lib/ppi-motor-capture
DST=$(cat "$HOME/cf-preflight-20261028/ULTIMA_PRUEBA"); P=$(cat "$DST.pid")
echo "## p11b  inicio=$(ts)  epoch=$(date +%s.%N)  DST=$DST  PID=$P"
cmd=$(tr '\0' ' ' < /proc/$P/cmdline 2>/dev/null)
case "$cmd" in *archivar_captura.sh*"$DST"*) echo "  PID $P es el archivador de la prueba: $cmd";;
  *) echo "  ABORTO: el PID $P no es el archivador de la prueba ($cmd); no se envia ninguna senal"; exit 2;; esac
act=$(ls -1t $R/live-*.pcap | head -1 | xargs basename); echo "  activo al parar: $act"
T_STOP=$(date +%s.%N); kill -TERM "$P"; echo "  [$(ts)] SIGTERM enviado solo a $P"
for i in $(seq 1 60); do [ -s "$DST.rc" ] && break; sleep 1; done
echo "  [$(ts)] codigo de salida del archivador: $(cat "$DST.rc" 2>/dev/null || echo 'NO TERMINO en 60 s')"
echo "  proceso vivo tras parar: $( [ -e /proc/$P ] && echo SI || echo NO )"
echo "  ESTADO.txt: $(cat "$DST/ESTADO.txt")"
echo "  lineas FALLO/PERDIDO en archivar.log: $(grep -cE 'FALLO|PERDIDO' "$DST/archivar.log")"
echo "  ultimas lineas del log:"; tail -n 4 "$DST/archivar.log" | sed 's/^/    /'
echo "## inventario por marca de paquete"
"$A" inventario "$DST" > "$DST.inventario.txt" 2>&1; echo "  rc inventario=$?"
head -3 "$DST.inventario.txt" | sed 's/^/    /'; echo "    ..."; tail -n 4 "$DST.inventario.txt" | sed 's/^/    /'
echo "## hashes: cada copia == su registro OK en el log; y == origen si sigue en el anillo (fichero cerrado intacto)"
ok=0; bad=0; ring_eq=0; ring_ne=0; gone=0
for f in "$DST"/live-*.pcap; do n=$(basename "$f"); h=$(sha256sum "$f" | cut -c1-64)
  grep -q "OK $n .* sha=$h" "$DST/archivar.log" && ok=$((ok+1)) || { bad=$((bad+1)); echo "    sin registro OK coincidente: $n"; }
  if [ -e "$R/$n" ]; then [ "$(sha256sum "$R/$n" | cut -c1-64)" = "$h" ] && ring_eq=$((ring_eq+1)) || { ring_ne=$((ring_ne+1)); echo "    DIFIERE del origen: $n"; }; else gone=$((gone+1)); fi
done
echo "  copias=$(ls -1 "$DST"/live-*.pcap | wc -l) con_registro_OK=$ok sin_registro=$bad | iguales_al_origen=$ring_eq distintas=$ring_ne ya_podadas_del_anillo=$gone"
echo "  ¿se copio el fichero activo al parar ($act) antes de cerrarse? $(grep -q "OK $act" "$DST/archivar.log" && echo "copiado en el barrido FINAL (tras CLOSE_AGE): $(grep "OK $act" "$DST/archivar.log" | cut -c1-20)" || echo 'NO copiado')"
echo "## cobertura del intervalo de la prueba"
python3 - "$DST.inventario.txt" "$(cat "$DST.salida" | head -1 | cut -c1-20)" "$T_STOP" <<'PY'
import sys,datetime
rows=[l.split() for l in open(sys.argv[1]) if l.startswith("live-")]
f=[(r[0],float(r[2]),float(r[3])) for r in rows if r[2]!="NA"]
t_ini=datetime.datetime.fromisoformat(sys.argv[2].replace("Z","+00:00")).timestamp(); t_stop=float(sys.argv[3])
print("  primer paquete archivado: %.3f (%s)"%(f[0][1],datetime.datetime.utcfromtimestamp(f[0][1]).isoformat()))
print("  ultimo paquete archivado: %.3f (%s)"%(f[-1][2],datetime.datetime.utcfromtimestamp(f[-1][2]).isoformat()))
print("  inicio archivador: %.3f | parada: %.3f"%(t_ini,t_stop))
print("  cubre [inicio, parada]: %s  (holgura antes %.1f s, despues %.1f s)"%(f[0][1]<=t_ini and f[-1][2]>=t_stop-1, t_ini-f[0][1], f[-1][2]-t_stop))
gaps=[(a[0],b[0],b[1]-a[2]) for a,b in zip(f,f[1:])]
print("  mayor separacion entre ficheros consecutivos: %.3f s (%s -> %s)"%max(((g[2],g[0],g[1]) for g in gaps)))
print("  segundos cubiertos: %.1f en %d ficheros"%(f[-1][2]-f[0][1],len(f)))
PY
echo "## volumen observado (para estimar capacidad)"
python3 - "$DST" <<'PY'
import os,sys,glob
fs=sorted(glob.glob(sys.argv[1]+"/live-*.pcap")); b=sum(os.path.getsize(x) for x in fs)
print("  bytes archivados=%d en %d ficheros de 15 s -> %.2f MB/min (%.0f MB/h)"%(b,len(fs),b/1e6/(len(fs)*15/60),b/1e6/(len(fs)*15/3600)))
PY
echo "  ens37 despues: $(awk '/ens37/{print "rx_bytes="$2" rx_packets="$3" rx_drop="$5}' /proc/net/dev)"
echo "## estado del proceso real de captura"; "$A" estado-motor 2>&1 | sed 's/^/  /'
echo "  disco: $(df -hP "$HOME" | awk 'NR==2{print $4" libres ("$5")"}') | tamano prueba: $(du -sh "$DST" | cut -f1)"
echo "## fin=$(ts)"
