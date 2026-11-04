#!/usr/bin/env bash
# Banco de k20_canal_control_simulado.sh (reconciliación 2026-11-03). SOLO en un contenedor desechable.
# `ssh` simulado: ejecuta la orden «remota» en local (HOME aparte para la «Kali») y registra cada uso;
# `-O exit` cierra el «canal». Periodo acortado a 2 s (K20_PERIODO) y duración ~7 s: se esperan 4 rondas.
#   bash ensayo_k20.sh <k20>
set -u
K20=$(readlink -f "${1:?k20}"); T=$(mktemp -d /tmp/banco-k20.XXXX); export SSH_LOG=$T/ssh.log KALI_HOME=$T/kali
mkdir -p "$T/bin" "$KALI_HOME"; fallos=0
cat > "$T/bin/ssh" <<'EOF'
#!/usr/bin/env bash
cerrar=0
while [ $# -gt 0 ]; do case "$1" in -O) [ "$2" = exit ] && cerrar=1; shift 2;; -o|-i|-S|-p|-l|-F) shift 2;; -*) shift;; *) break;; esac; done
host=$1; shift
printf '%s host=%s cerrar=%s orden=%s\n' "$(date -u +%T)" "$host" "$cerrar" "$(printf '%s' "$*" | head -c 90)" >> "$SSH_LOG"
[ $cerrar = 1 ] && exit 0
HOME=$KALI_HOME exec bash -c "$*"
EOF
chmod +x "$T/bin/ssh"; export PATH="$T/bin:$PATH"
mkdir -p "$HOME/cf-e4/4b"
HASTA=$(date -u -d '+7 sec' +%FT%TZ)
K20_PERIODO=2 bash "$K20" 4b "$HASTA"; rc=$?
ok() { if eval "$2"; then echo "OK    $1"; else echo "FALLO $1"; fallos=$((fallos + 1)); fi; }
ok "rc 0" '[ "$rc" = 0 ]'
n=$(wc -l < "$HOME/cf-e4/4b/canal-simulado/canal.jsonl")
ok "3-5 rondas en ~7 s con periodo 2 s ($n)" '[ "$n" -ge 3 ] && [ "$n" -le 5 ]'
ok "todas con kali_rc 0" '! grep -v "\"kali_rc\": 0" "$HOME/cf-e4/4b/canal-simulado/canal.jsonl" | grep -q .'
ok "escribe SOLO permiso-simulado.json en la «Kali»" '[ "$(cd "$KALI_HOME" && find . -type f | sort | tr "\n" " ")" = "./cf-e4-canal-4b/permiso-simulado.json " ]'
ok "JSON válido con nonce simulado" 'python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d[\"nonce\"]==\"simulado-4b\"" "$KALI_HOME/cf-e4-canal-4b/permiso-simulado.json"'
ok "accesos-kali.log: apertura, rondas y cierre" 'grep -q "abrir canal de control SIMULADO" "$HOME/cf-e4/4b/accesos-kali.log" && grep -q "cerrado tras $n rondas" "$HOME/cf-e4/4b/accesos-kali.log"'
ok "canal cerrado con -O exit" 'grep -q "cerrar=1" "$SSH_LOG"'
ok "fase inválida para" '! bash "$K20" 5x "$HASTA" > /dev/null 2>&1'
sed 's/^/  /' "$HOME/cf-e4/4b/accesos-kali.log"
[ "$fallos" = 0 ] && echo "BANCO k20 OK" || { echo "BANCO k20 CON $fallos FALLOS"; exit 1; }
