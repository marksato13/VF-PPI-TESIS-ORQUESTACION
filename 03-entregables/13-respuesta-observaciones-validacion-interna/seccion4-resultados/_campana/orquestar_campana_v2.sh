#!/bin/bash
# Campana v2 (corre en la KALI). Corrige los confounds de la corrida 2026-10-23:
#  - ESCANEO PRIMERO y con volumen (path abierto, antes de cualquier BLOCK), para que
#    llene ventanas y NO quede con trafico minimo como en la pasada de captura.
#  - N>=3 por familia sin firma; brute aparte; NIKTO como control (lo caza ET Open).
#  - Timeouts por herramienta para que el enforcement no alargue los episodios.
#  - Espera >1800 s tras familias que producen BLOCK (la escalera llega a 1800 s en la 2a).
# Captura: arrancar cf-capturar en el SENSOR antes (ver runbook). marcas.jsonl con t0/t_fin.
set -u
OUT="${OUT:-/tmp/campana-v2}"; mkdir -p "$OUT"; M="$OUT/marcas.jsonl"; : > "$M"
TARGET="${TARGET:-10.10.30.10}"; RES="${RES:-10.10.10.20}"; BRUTE="${BRUTE:-10.10.30.10:8081}"
N="${N:-3}"; NS="${NS:-3}"; NB="${NB:-1}"; NK="${NK:-1}"
ESPERA_LIMIT="${ESPERA_LIMIT:-90}"; ESPERA_BLOCK="${ESPERA_BLOCK:-1850}"
marca(){ printf '{"id":"%s","familia":"%s","rep":%s,"fase":"%s","wall":%s,"iso":"%s"}\n' "$1" "$2" "$3" "$4" "$(date -u +%s.%N)" "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >> "$M"; }
snap(){ printf '{"id":"CLOCK","familia":"clock","rep":0,"fase":"%s","wall":%s}\n' "$1" "$(date -u +%s.%N)" >> "$M"; }
corte(){ sleep 45; nmap -Pn -p80,443 "$TARGET" -oG "$OUT/$1-corte.gnmap" >/dev/null 2>&1; }
snap inicio
echo "[pre] camino:"; nmap -Pn -p80,443 "$TARGET" 2>/dev/null | grep -E "80/|443/" || true

# 1) ESCANEO primero (BLOCK). Volumen alto para llenar ventanas antes del corte.
for r in $(seq 1 "$NS"); do
  ep="E-scan-$r"; echo "[$ep] scan"; marca "$ep" scan "$r" inicio
  nmap -sT -T4 --min-rate 2000 --max-retries 1 -p 1-5000 --open "$TARGET" >/dev/null 2>&1
  marca "$ep" scan "$r" fin; corte "$ep"
  [ "$r" -lt "$NS" ] && { echo "esperando expiracion BLOCK ($ESPERA_BLOCK s)"; sleep "$ESPERA_BLOCK"; }
done
echo "esperando expiracion del ultimo BLOCK de escaneo ($ESPERA_BLOCK s)"; sleep "$ESPERA_BLOCK"

# 2) DNS alta entropia (LIMIT, no corta)
for r in $(seq 1 "$N"); do
  ep="E-dns-$r"; echo "[$ep] dga"; marca "$ep" dns "$r" inicio
  for i in $(seq 1 160); do x=$(head -c6 /dev/urandom|od -An -tx1|tr -d ' \n'); dig +short +time=1 +tries=1 "${x}.francos-sac.com" @"$RES" >/dev/null 2>&1; done
  marca "$ep" dns "$r" fin; sleep "$ESPERA_LIMIT"
done

# 3) Flood HTTP (LIMIT)
for r in $(seq 1 "$N"); do
  ep="E-flood-$r"; echo "[$ep] flood"; marca "$ep" flood "$r" inicio
  seq 1 400 | xargs -P12 -I{} curl -s --max-time 2 -o /dev/null "http://$TARGET/"
  marca "$ep" flood "$r" fin; sleep "$ESPERA_LIMIT"
done

# 4) Fuerza bruta (BLOCK) - requiere endpoint 401 en $BRUTE
for r in $(seq 1 "$NB"); do
  ep="E-brute-$r"; echo "[$ep] brute"; marca "$ep" brute "$r" inicio
  for i in $(seq 1 80); do curl -s --max-time 2 -o /dev/null -u "admin:mal$i" "http://$BRUTE/"; sleep 0.25; done
  marca "$ep" brute "$r" fin; corte "$ep"; sleep "$ESPERA_BLOCK"
done

# 5) NIKTO (control CON firma: lo detecta ET Open; CyberFlow por conducta)
for r in $(seq 1 "$NK"); do
  ep="E-nikto-$r"; echo "[$ep] nikto"; marca "$ep" nikto "$r" inicio
  timeout 180 nikto -host "http://$TARGET/" -maxtime 150 >/dev/null 2>&1 || true
  marca "$ep" nikto "$r" fin; sleep "$ESPERA_LIMIT"
done

snap fin
echo "== FIN =="; cat "$M"
