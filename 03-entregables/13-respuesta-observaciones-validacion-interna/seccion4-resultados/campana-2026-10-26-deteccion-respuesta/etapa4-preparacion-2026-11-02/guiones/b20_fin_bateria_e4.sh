#!/usr/bin/env bash
# [BASTIÓN gadmin] ETAPA4 b20 — uso: b20_fin_bateria_e4.sh. Fin de la batería 4C (en el 3B se hizo a mano, §6 de
# COMANDOS.md; aquí queda escrito). Solo lecturas y copias; sin sudo; no toca motor, servicios ni la Kali más allá
# de UNA sesión de lectura registrada en accesos-kali.log.
#  1) Kali: generador terminado (generador.rc) y sha256 de corrida/marcas.jsonl
#  2) copia de corrida/ al bastión (~/cf-e4/4c/corrida) y de marcas.jsonl al sensor (~/cf-e4/4c/copias/marcas.jsonl),
#     con el mismo sha256 en los tres sitios
#  3) fin_ultimo (evento 'fin' del último episodio) en epoch y ISO -> ~/cf-e4/4c/fin-ultimo.txt
#  4) relojes (p10b) añadidos a relojes-4c.log y copia al sensor (copias/relojes-4c.log)
#  5) traza del relé v2 (~/relay-v2/traza.jsonl) al sensor (copias/traza-rele.jsonl) SOLO si ya pasó fin_ultimo + 300 s;
#     si no, avisa y se repite este guion después (las copias 1-4 se rehacen idénticas).
# Resultado esperado: "generador rc=0" (o rc=3 = cancelada por el vigía, que también se cierra y se publica), tres
# sha256 iguales, "fin_ultimo=<epoch>", relojes sin "desfase|<=1 s: NO", "vigía terminado" y el canal cerrado.
# Parada: generador sin terminar o rc distinto de 0/3, marcas con sha256 distinto, ya existe la copia con otro sha256,
# vigía aún vivo.
set -u
B=$HOME/cf-e4/4c; K=/home/adminatacante/cf-e4-4c; C=/home/m4rk/cf-e4/4c/copias
[ -f "$B/control-declarado.json" ] || { echo "PARAR: no hay control 4c declarado en $B"; exit 2; }
# mismo canal de control que g01 (si sigue abierto se reutiliza; si no, se abre uno y queda anotado)
CTL="-o BatchMode=yes -o ControlMaster=auto -o ControlPath=$B/vigia/ctl-kali -o ControlPersist=60"
echo "## b20-e4 $(date -u +%FT%T.%3NZ)"
echo "## [ACCESO SSH A KALI $(date -u +%FT%T.%3NZ): lectura del fin del generador]" | tee -a "$B/accesos-kali.log"
R=$(ssh -n $CTL kali "cat $K/generador.rc 2>/dev/null; cat $K/terminado.txt 2>/dev/null; sha256sum $K/corrida/marcas.jsonl 2>/dev/null | cut -c1-64; pgrep -fc 'generar_campana.py --config'")
echo "## fin acceso Kali $(date -u +%FT%T.%3NZ)" | tee -a "$B/accesos-kali.log"
RC=$(sed -n 1p <<< "$R"); TERM_=$(sed -n 2p <<< "$R"); HK=$(sed -n 3p <<< "$R"); NG=$(sed -n 4p <<< "$R")
echo "  generador rc=$RC terminado=$TERM_ procesos=$NG marcas sha256=$HK"
case "$RC" in
  0) ;;
  3) echo "  AVISO: batería CANCELADA por el vigía (ver cancelacion en marcas.jsonl y vigia.jsonl); se cierra igual" ;;
  *) echo "PARAR: el generador no ha terminado con rc=0 ni rc=3"; exit 2 ;;
esac
[ "$NG" = 0 ] && [ -n "$HK" ] || { echo "PARAR: el generador sigue vivo o no hay marcas"; exit 2; }
VP=$(cat "$B/vigia/vigia.pid" 2>/dev/null)
if [ -n "$VP" ] && kill -0 "$VP" 2>/dev/null; then echo "PARAR: el vigía (PID $VP) sigue vivo"; exit 2; fi
echo "  vigía terminado: $(tail -1 "$B/vigia/vigia.jsonl" | cut -c1-200)"
if [ -e "$B/corrida/marcas.jsonl" ]; then
  [ "$(sha256sum "$B/corrida/marcas.jsonl" | cut -c1-64)" = "$HK" ] || { echo "PARAR: ya hay otra corrida copiada"; exit 2; }
else
  mkdir -p "$B/corrida"
  ssh -n $CTL kali "cd $K/corrida && tar cf - ." | tar xf - -C "$B/corrida"
  ssh -n $CTL kali "cat $K/comando.txt $K/lanzado.txt $K/terminado.txt $K/generador.rc $K/permiso.json" > "$B/generador-meta.txt"
fi
ssh -O exit -o ControlPath="$B/vigia/ctl-kali" kali 2>/dev/null && echo "  canal de control con la Kali cerrado $(date -u +%FT%T.%3NZ)" | tee -a "$B/accesos-kali.log"
HB=$(sha256sum "$B/corrida/marcas.jsonl" | cut -c1-64)
ssh -o BatchMode=yes sensor1 "mkdir -p $C && cat > $C/marcas.jsonl" < "$B/corrida/marcas.jsonl"
HS=$(ssh -n -o BatchMode=yes sensor1 "sha256sum $C/marcas.jsonl | cut -c1-64")
echo "  marcas: kali=$HK bastión=$HB sensor=$HS"
[ "$HK" = "$HB" ] && [ "$HB" = "$HS" ] || { echo "PARAR: sha256 de marcas distinto"; exit 2; }
F=$(python3 - "$B/corrida/marcas.jsonl" <<'PY'
import json, sys
from datetime import datetime
fins = []
for l in open(sys.argv[1], encoding="utf-8"):
    try:
        r = json.loads(l)
    except ValueError:
        continue
    if r.get("evento") == "fin":
        t = r["reloj"]["pared_utc"]  # mismo campo que analizar.leer_marcas
        fins.append(datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp())
print("%.6f" % max(fins) if fins else "")
PY
)
[ -n "$F" ] || { echo "PARAR: sin eventos 'fin' en marcas.jsonl"; exit 2; }
echo "fin_ultimo=$F $(date -u -d "@${F%.*}" +%FT%TZ)" | tee "$B/fin-ultimo.txt"
echo "## relojes (p10b)"; bash "$HOME/cf-e4/p10b_relojes.sh" | tee -a "$B/relojes-4c.log"
grep -q '|desfase|<=1 s: NO' "$B/relojes-4c.log" && echo "  AVISO: desfase de reloj > 1 s en alguna lectura (se publica; afecta a la comparación entre hosts)"
ssh -o BatchMode=yes sensor1 "cat > $C/relojes-4c.log" < "$B/relojes-4c.log"
AHORA=$(date +%s)
if [ "$AHORA" -ge $(( ${F%.*} + 300 )) ]; then
  ssh -o BatchMode=yes sensor1 "cat > $C/traza-rele.jsonl" < "$HOME/relay-v2/traza.jsonl"
  echo "  traza del relé al sensor: $(wc -l < "$HOME/relay-v2/traza.jsonl") líneas, sha256 $(sha256sum "$HOME/relay-v2/traza.jsonl" | cut -c1-64)"
else
  echo "  AVISO: aún no han pasado 300 s desde fin_ultimo: la traza del relé NO se copia; repetir b20 después de $(date -u -d "@$(( ${F%.*} + 300 ))" +%T)Z"
fi
echo "## fin $(date -u +%FT%T.%3NZ)"
