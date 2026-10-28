#!/usr/bin/env bash
# PREFLIGHT 10 — relojes medidos desde el BASTION (referencia chrony). Por host: una sesion SSH persistente y 7
# muestras; desfase = t_remoto - (t0+t1)/2, incertidumbre = (t1-t0)/2. Se informa la muestra de menor RTT y la
# mediana. DNS 10.10.10.20 (sin llave): consulta SNTP al puerto 123. Tolerancia de la preparacion: |desfase| <= 1 s.
set -u
ts(){ date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
echo "## p10 relojes  inicio=$(ts)  referencia=bastion $(hostname)"
chronyc tracking 2>&1 | grep -E 'Reference|System time|Last offset|RMS offset|Root dispersion' | sed 's/^/  /'
medir(){ # $1=nombre $2=llave $3=usuario@host
  local n="$1" k="$2" u="$3"
  coproc R { ssh -o BatchMode=yes -o ConnectTimeout=8 -i "$k" "$u" 'while IFS= read -r _; do date +%s.%N; done' 2>/dev/null; }
  local i t0 t1 r out=""
  echo x >&"${R[1]}"; IFS= read -r -t 10 r <&"${R[0]}" || { echo "  $n: SIN RESPUESTA (no se puede medir)"; kill "$R_PID" 2>/dev/null; return; }
  for i in 1 2 3 4 5 6 7; do
    t0=$(date +%s.%N); echo x >&"${R[1]}"; IFS= read -r -t 5 r <&"${R[0]}"; t1=$(date +%s.%N)
    out="$out$(awk -v a="$t0" -v b="$t1" -v r="$r" 'BEGIN{printf "%.6f %.6f %.6f\n", r-(a+b)/2, (b-a)/2, b-a}')"$'\n'
    sleep 0.2
  done
  exec {R[1]}>&- 2>/dev/null; kill "$R_PID" 2>/dev/null; wait "$R_PID" 2>/dev/null
  echo "$out" | awk -v n="$n" 'NF==3{k++; o[k]=$1; inc[k]=$2; rtt[k]=$3; printf "  %-8s m%d desfase=%+.4f s  inc=+-%.4f s  rtt=%.4f s\n", n, k, $1, $2, $3}
    END{best=1; for(i=2;i<=k;i++) if(rtt[i]<rtt[best]) best=i; n2=asort(o,s); med=(n2%2)?s[(n2+1)/2]:(s[n2/2]+s[n2/2+1])/2;
        printf "  %-8s RESUMEN mejor(m%d)=%+.4f s inc=+-%.4f s | mediana=%+.4f s | |desfase|<=1 s: %s\n", n, best, o[best], inc[best], med, ((o[best]<1&&o[best]>-1)?"SI":"NO")}'
}
t=$(ts); echo "## [$t] sensor 10.10.60.11";    medir sensor   ~/.ssh/cyberflow-to-sensor   m4rk@10.10.60.11
t=$(ts); echo "## [$t] kali 10.10.20.30";      medir kali     ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30
t=$(ts); echo "## [$t] srv-dmz 10.10.30.10";   medir srv-dmz  ~/.ssh/cyberflow-to-srv      adminsrvdmz@10.10.30.10
t=$(ts); echo "## [$t] clientes 10.10.20.20";  medir clientes ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20
t=$(ts); echo "## [$t] DNS/DC 10.10.10.20 (SNTP, sin llave SSH)"
python3 - <<'PY'
import socket,struct,time
def q(h):
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(3)
    pkt=b'\x23'+47*b'\0'; t0=time.time(); s.sendto(pkt,(h,123)); d,_=s.recvfrom(64); t3=time.time()
    st=d[1]; rx=struct.unpack("!II",d[32:40]); tx=struct.unpack("!II",d[40:48])
    f=lambda x:x[0]-2208988800+x[1]/2**32; t1,t2=f(rx),f(tx)
    return ((t1-t0)+(t2-t3))/2,(t3-t0)/2,st
for i in range(5):
    try: o,inc,st=q("10.10.10.20"); print("  dns      m%d desfase=%+.4f s  inc=+-%.4f s  estrato=%d"%(i+1,o,inc,st))
    except Exception as e: print("  dns      m%d SIN RESPUESTA SNTP (%s)"%(i+1,e))
    time.sleep(0.3)
PY
echo "## fin=$(ts)"
