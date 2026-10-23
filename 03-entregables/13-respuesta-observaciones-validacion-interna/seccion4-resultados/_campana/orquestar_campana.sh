#!/bin/bash
# Campana instrumentada contra el MODELO LIMPIO (if_limpio_2026_10).
# SE EJECUTA EN LA KALI (10.10.20.30). Lanza los ataques y escribe marcas.jsonl
# con t0/t_fin por episodio (reloj de pared epoch + reloj MONOTONICO /proc/uptime).
# NO aplica bloqueos ni toca el sensor: solo genera trafico y registra marcas.
#
# Orden pensado para no chocar enforcement: DNS (LIMIT) y flood (LIMIT) primero;
# luego brute y scan (BLOCK) con espera de expiracion (5 min) entre repeticiones.
#
# Variables: N (reps por familia sin firma, def 3), NB (reps brute, def 1),
#            TARGET, RESOLVER, BRUTE_HOST, ESPERA_LIMIT, ESPERA_BLOCK.
set -u
OUT="${OUT:-/tmp/campana-limpio}"; mkdir -p "$OUT"
MARCAS="$OUT/marcas.jsonl"; : > "$MARCAS"
N="${N:-3}"; NB="${NB:-1}"
TARGET="${TARGET:-10.10.30.10}"
RESOLVER="${RESOLVER:-10.10.10.20}"
BRUTE_HOST="${BRUTE_HOST:-10.10.30.10:8081}"
ESPERA_LIMIT="${ESPERA_LIMIT:-90}"     # dejar acumular ventana 60s + publicar feed
ESPERA_BLOCK="${ESPERA_BLOCK:-330}"    # BLOCK de 1a ofensa dura 5 min: esperar expiracion

marca() { # id familia rep fase
  local wall mono; wall="$(date -u +%s.%N)"; mono="$(cut -d' ' -f1 /proc/uptime)"
  printf '{"id":"%s","familia":"%s","rep":%s,"fase":"%s","wall":%s,"mono":%s,"iso":"%s"}\n' \
    "$1" "$2" "$3" "$4" "$wall" "$mono" "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >> "$MARCAS"
}
snap_reloj() { # registra el reloj de la Kali para calcular desfase con sensor/host
  printf '{"id":"CLOCK-KALI","familia":"clock","rep":0,"fase":"%s","wall":%s,"mono":%s,"iso":"%s"}\n' \
    "$1" "$(date -u +%s.%N)" "$(cut -d' ' -f1 /proc/uptime)" "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >> "$MARCAS"
}

echo "== Campana limpio: N=$N NB=$NB TARGET=$TARGET =="; snap_reloj inicio_campana
echo "[pre] camino a la DMZ:"; nmap -Pn -p80,443 "$TARGET" | grep -E "80|443" || true

# 1) DNS alta entropia (DGA) -> dns_entropy -> LIMIT
for r in $(seq 1 "$N"); do
  ep="E-dns-$r"; echo "[$ep] DGA"; marca "$ep" dns "$r" inicio
  for i in $(seq 1 140); do
    x="$(head -c6 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    dig +short "${x}.francos-sac.com" @"$RESOLVER" >/dev/null 2>&1
  done
  marca "$ep" dns "$r" fin; sleep "$ESPERA_LIMIT"
done

# 2) Flood HTTP -> http_abuse -> LIMIT (y el modelo suele verlo)
for r in $(seq 1 "$N"); do
  ep="E-flood-$r"; echo "[$ep] flood"; marca "$ep" flood "$r" inicio
  seq 1 400 | xargs -P12 -I{} curl -s -o /dev/null "http://$TARGET/"
  marca "$ep" flood "$r" fin; sleep "$ESPERA_LIMIT"
done

# 3) Fuerza bruta -> brute_force -> BLOCK (control aparte, NB repeticiones)
for r in $(seq 1 "$NB"); do
  ep="E-brute-$r"; echo "[$ep] brute (requiere endpoint 401 en $BRUTE_HOST)"; marca "$ep" brute "$r" inicio
  for i in $(seq 1 80); do curl -s -o /dev/null -u "admin:mal$i" "http://$BRUTE_HOST/"; sleep 0.25; done
  marca "$ep" brute "$r" fin
  sleep 45; echo "[$ep] corte:"; nmap -Pn -p80,443 "$TARGET" -oG "$OUT/$ep-corte.gnmap" | grep -E "80|443" || true
  sleep "$ESPERA_BLOCK"
done

# 4) Escaneo de puertos -> port_scan -> BLOCK + corte real
for r in $(seq 1 "$N"); do
  ep="E-scan-$r"; echo "[$ep] scan"; marca "$ep" scan "$r" inicio
  nmap -sT -T4 --max-retries 1 -p 1-3000 --open "$TARGET" >/dev/null 2>&1
  marca "$ep" scan "$r" fin
  sleep 45; echo "[$ep] corte:"; nmap -Pn -p80,443 "$TARGET" -oG "$OUT/$ep-corte.gnmap" | grep -E "80|443" || true
  sleep "$ESPERA_BLOCK"; echo "[$ep] tras expiracion:"; nmap -Pn -p80,443 "$TARGET" | grep -E "80|443" || true
done

snap_reloj fin_campana
echo "== FIN. Marcas en $MARCAS =="; cat "$MARCAS"
