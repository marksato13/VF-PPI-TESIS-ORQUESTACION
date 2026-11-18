#!/usr/bin/env bash
# [CLIENTES adminclientes] k01 con REGISTRO POR TRANSACCIÓN (E4) — copia de k01_clientes_factor1_e4.sh (etapa4-preparacion-2026-11-02) para la nueva corrida de la Campaña B.
# Cambios, y solo estos: (1) el envoltorio es clientes_factor1_tx.py (d86c7edc…, ~/cf-b/instrumentacion; mismo factor 1,0 y mismos argumentos; solo añade un registro con hora por acción en
# <fase>/transacciones-<perfil>.tsv); (2) la cuenta de procesos vivos busca `clientes_factor1` (el nombre `_tx` no coincidía con `clientes_factor1.py`); (3) exige que ya no haya ningún
# clientes_lab.py (las unidades paradas) para que NO haya perfiles duplicados. No modifica clientes_lab.py. Uso: k01_clientes_factor1_tx_e4.sh 4c
set -u
FASE=${1:?uso: k01_clientes_factor1_tx_e4.sh 4c}
case "$FASE" in 4c) ;; *) echo "PARAR: fase $FASE"; exit 2;; esac
B=$HOME/cf-e4/$FASE; W=$HOME/cf-b/instrumentacion/clientes_factor1_tx.py; G=$HOME/laboratorio/clientes_lab.py
echo "## k01-tx-e4 $FASE $(date -u +%FT%T.%3NZ)"
[ -e "$B/pids" ] && { echo "PARAR: ya hay $B/pids"; exit 2; }
[ -e "$B/perfiles" ] && { echo "PARAR: ya existe $B/perfiles (evidencia de otra corrida sin apartar)"; exit 2; }
mkdir -p "$B"
[ "$(sha256sum "$W" | cut -c1-64)" = d86c7edc9f10e353fca11aee506bd13bf1b6c3a587e8baf55d7d9d73d8d6c307 ] || { echo "PARAR: hash del envoltorio tx"; exit 2; }
[ "$(sha256sum "$G" | cut -c1-8)" = ae5134a7 ] || { echo "PARAR: clientes_lab.py no es ae5134a7…"; exit 2; }
cat > "$B/clientes_parar_factor1.sh" <<'EOS'
#!/usr/bin/env bash
set -u
B=$(cd "$(dirname "$0")" && pwd)
echo "## parar factor1 $(date -u +%FT%T.%3NZ)"
while read -r u p; do kill -TERM -- -"$p" 2>/dev/null; echo "  $u pgid=$p TERM"; done < "$B/pids"
sleep 3
while read -r u p; do pgrep -g "$p" >/dev/null && { kill -KILL -- -"$p"; echo "  $u KILL"; }; done < "$B/pids"
echo "  quedan: $(pgrep -fc 'clientes_factor1')"; mv "$B/pids" "$B/pids.parado-$(date -u +%H%M%S)"
for f in "$B"/perfiles/*.out; do echo "  $(basename "$f"): $(tail -1 "$f")"; done
for f in "$B"/transacciones-*.tsv; do echo "  $(basename "$f"): $(grep -vc '^#' "$f") transacciones"; done
EOS
cat > "$B/clientes_restaurar.sh" <<'EOS'
#!/usr/bin/env bash
set -u
B=$(cd "$(dirname "$0")" && pwd)
bash "$B/clientes_parar_factor1.sh"
echo "  generador sin cambios: $(sha256sum "$HOME/laboratorio/clientes_lab.py" | cut -c1-64)"
sudo -n systemctl start cyberflow-lab.target; echo "  [$(date -u +%FT%T.%3NZ)] start cyberflow-lab.target rc=$?"
sleep 15
echo "  target: $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
for s in ofimatica navegacion descargas aplicacion ligero erratico; do echo "  cyberflow-lab-$s $(systemctl is-active cyberflow-lab-$s) NR=$(systemctl show -p NRestarts --value cyberflow-lab-$s)"; done
echo "  envoltorios vivos: $(pgrep -fc 'clientes_factor1')  clientes_lab.py (uno por perfil esperado): $(pgrep -fc '[c]lientes_lab.py --perfil')"
EOS
for u in ofimatica navegacion descargas aplicacion ligero erratico; do
  systemctl show -p ExecStart --value "cyberflow-lab-$u.service" | grep -oE 'argv\[\]=[^;]*' | head -1 | sed 's/^argv\[\]=//' > "$B/argv-$u.txt"
done
{ echo "target $(systemctl is-active cyberflow-lab.target)/$(systemctl is-enabled cyberflow-lab.target)"
  date -u +"inicio_factor1_utc %FT%T.%3NZ"; timedatectl show -p Timezone; echo "envoltorio: clientes_factor1_tx.py con --registro por perfil"; } > "$B/config-efectiva.txt"
sha256sum "$W" "$G" "$HOME/laboratorio/clientes_config.py" >> "$B/config-efectiva.txt" 2>&1
sudo -n systemctl stop cyberflow-lab.target; echo "  [$(date -u +%FT%T.%3NZ)] stop cyberflow-lab.target rc=$?"
sleep 3
ACT=$(for s in ofimatica navegacion descargas aplicacion ligero erratico; do systemctl is-active cyberflow-lab-$s; done | grep -c '^active')
echo "  unidades activas tras parar: $ACT"
for i in $(seq 20); do [ "$(pgrep -fc '[c]lientes_lab.py --perfil')" = 0 ] && break; sleep 1; done   # los procesos tardan unos segundos en salir tras parar el target
[ "$(pgrep -fc '[c]lientes_lab.py --perfil')" = 0 ] || { echo "PARAR: quedan procesos clientes_lab.py tras parar el target (perfiles duplicados): $(pgrep -f '[c]lientes_lab.py --perfil' | tr '\n' ' ')"; exit 3; }
mkdir -p "$B/perfiles"
for u in ofimatica navegacion descargas aplicacion ligero erratico; do
  A=$(cat "$B/argv-$u.txt")
  ARGS=$(echo "$A" | sed 's#^/usr/bin/python3 /home/adminclientes/laboratorio/clientes_lab.py ##')
  echo "  $u: unidad -> $A" | tee -a "$B/config-efectiva.txt"
  echo "$ARGS" | grep -q -- "--perfil $u " || { echo "PARAR: argumentos inesperados para $u"; exit 3; }
  # shellcheck disable=SC2086  # ARGS se parte en palabras a propósito (argumentos de la unidad)
  setsid nohup bash -c 'W="$1"; LOG="$2"; REG="$3"; shift 3; cd /home/adminclientes/laboratorio
    while :; do python3 -u "$W" --registro "$REG" "$@" >> "$LOG.out" 2>> "$LOG.err"; echo "$(date -u +%FT%T) salida rc=$?" >> "$LOG.err"; sleep 5; done' \
    _ "$W" "$B/perfiles/$u" "$B/transacciones-$u.tsv" $ARGS > /dev/null 2>&1 < /dev/null &
  echo "$u $!" >> "$B/pids"
done
sleep 8
while read -r u p; do echo "  $u pgid=$p vivo=$(kill -0 "$p" 2>/dev/null && echo si || echo NO) hijos=$(pgrep -g "$p" -c)"; done < "$B/pids"
sleep 30; echo "## conexiones por origen (ss)"; ss -tn 2>/dev/null | awk 'NR>1{print $4}' | grep -oE '10\.10\.20\.2[0-9]' | sort | uniq -c | sed 's/^/  /'
echo "## perfiles: un clientes_lab/_tx por perfil (sin duplicados)"
for u in ofimatica navegacion descargas aplicacion ligero erratico; do echo "  $u: procesos python=$(pgrep -fc "clientes_factor1_tx.py --registro $B/transacciones-$u.tsv .*--perfil $u ")"; done
echo "  total envoltorios=$(pgrep -fc '[c]lientes_factor1_tx.py --registro')"
for f in "$B"/perfiles/*.out; do echo "  $(basename "$f"): $(wc -l < "$f") lineas; $(tail -1 "$f" | cut -c1-140)"; done
for f in "$B"/transacciones-*.tsv; do echo "  $(basename "$f"): $(grep -vc '^#' "$f") transacciones"; done
echo "## fin $(date -u +%FT%T.%3NZ)"
