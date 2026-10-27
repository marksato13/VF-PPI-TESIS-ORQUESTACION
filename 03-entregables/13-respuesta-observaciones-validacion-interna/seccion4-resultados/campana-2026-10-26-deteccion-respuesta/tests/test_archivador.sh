#!/usr/bin/env bash
# Pruebas del archivador con ficheros LOCALES inocuos (no toca el sensor ni la red).
# Casos: copia correcta, permiso denegado, error de copia, copia incompleta y PERDIDA.
# Los fallos deben ser VISIBLES (codigo != 0 y ESTADO.txt != OK) y NO terminar anunciando exito.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../scripts/archivar_captura.sh"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
okc=0; badc=0
pass(){ echo "OK  $1"; okc=$((okc+1)); }
bad(){ echo "FALLO  $1"; badc=$((badc+1)); }

# cp falsos
mkdir -p "$WORK/bin"
cat > "$WORK/bin/cp_denegado" <<'SH'
#!/usr/bin/env bash
echo "cp: no se puede crear '$2': Permission denied" >&2; exit 1
SH
cat > "$WORK/bin/cp_error" <<'SH'
#!/usr/bin/env bash
echo "cp: error generico de E/S" >&2; exit 1
SH
cat > "$WORK/bin/cp_incompleto" <<'SH'
#!/usr/bin/env bash
# "copia" truncada: exit 0 pero contenido distinto (simula copia incompleta)
head -c 1 "$1" > "$2" 2>/dev/null; exit 0
SH
chmod +x "$WORK/bin/"*

# anillo de prueba: 2 objetivos cerrados + 1 activo (el mas reciente, se excluye)
mk_ring(){ local R="$1"; rm -rf "$R"; mkdir -p "$R"
  printf 'AAAA-contenido-1' > "$R/live-20000101000000.pcap"
  printf 'BBBB-contenido-2' > "$R/live-20000101000015.pcap"
  sleep 1; printf 'ZZZZ-activo'   > "$R/live-29991231235959.pcap"   # mtime mas nuevo => activo, excluido
}

run(){ # $1=caso_cp ; ejecuta un barrido ; exporta RC y EST
  local R="$WORK/ring" D="$WORK/dst_$RANDOM"; mk_ring "$R"
  RC=0; CP="$1" RING="$R" MIN_KB=1 CLOSE_AGE=0 bash "$SCRIPT" barrido "$D" >/dev/null 2>&1 || RC=$?
  EST="$(cat "$D/ESTADO.txt" 2>/dev/null)"; LOG="$(cat "$D/archivar.log" 2>/dev/null)"; DOUT="$D"
}

echo "== caso 1: copia correcta =="
run "cp"
if [ "$RC" -eq 0 ] && echo "$EST" | grep -q '^OK'; then
  # ambos objetivos presentes y con sha correcto
  if [ -f "$DOUT/live-20000101000000.pcap" ] && [ -f "$DOUT/live-20000101000015.pcap" ] \
     && [ "$(sha256sum "$DOUT/live-20000101000000.pcap"|awk '{print $1}')" = "$(printf 'AAAA-contenido-1'|sha256sum|awk '{print $1}')" ]; then
    pass "copia correcta (RC=0, ESTADO OK, contenido identico)"
  else bad "copia correcta: faltan ficheros o sha no coincide"; fi
else bad "copia correcta: RC=$RC ESTADO='$EST'"; fi

echo "== caso 2: permiso denegado =="
run "$WORK/bin/cp_denegado"
if [ "$RC" -ne 0 ] && ! echo "$EST" | grep -q '^OK' && echo "$LOG" | grep -qi 'Permission denied'; then
  [ -f "$DOUT/live-20000101000000.pcap" ] && bad "permiso denegado: NO deberia existir la copia" \
    || pass "permiso denegado VISIBLE (RC=$RC, ESTADO!=OK, motivo en log, sin copia)"
else bad "permiso denegado: deberia fallar visiblemente (RC=$RC ESTADO='$EST')"; fi

echo "== caso 3: error de copia =="
run "$WORK/bin/cp_error"
if [ "$RC" -ne 0 ] && ! echo "$EST" | grep -q '^OK' && echo "$LOG" | grep -q 'FALLO'; then
  pass "error de copia VISIBLE (RC=$RC, ESTADO!=OK, FALLO en log)"
else bad "error de copia: deberia fallar visiblemente (RC=$RC ESTADO='$EST')"; fi

echo "== caso 4: copia incompleta =="
run "$WORK/bin/cp_incompleto"
if [ "$RC" -ne 0 ] && ! echo "$EST" | grep -q '^OK' && echo "$LOG" | grep -qi 'INCOMPLETA'; then
  # no debe quedar una copia "final" truncada
  if [ -f "$DOUT/live-20000101000000.pcap" ]; then bad "copia incompleta: quedo una copia final truncada"; else
    pass "copia incompleta DETECTADA por integridad (RC=$RC, ESTADO!=OK, sin copia final)"; fi
else bad "copia incompleta: deberia detectarse por sha (RC=$RC ESTADO='$EST')"; fi

echo "== caso 5: perdida (visto, no archivado, desaparece del anillo) =="
R="$WORK/ring5"; D="$WORK/dst5"; rm -rf "$R" "$D"; mkdir -p "$R"
printf 'C1' > "$R/live-20010101000000.pcap"; sleep 1; printf 'ZZ' > "$R/live-29991231235959.pcap"
RC=0; CP="$WORK/bin/cp_error" RING="$R" MIN_KB=1 CLOSE_AGE=0 bash "$SCRIPT" barrido "$D" >/dev/null 2>&1 || RC=$?   # falla -> visto, no archivado
rm -f "$R/live-20010101000000.pcap"                                                                                 # se poda del anillo
RC2=0; CP="cp" RING="$R" MIN_KB=1 CLOSE_AGE=0 bash "$SCRIPT" barrido "$D" >/dev/null 2>&1 || RC2=$?
EST2="$(cat "$D/ESTADO.txt" 2>/dev/null)"; LOG2="$(cat "$D/archivar.log" 2>/dev/null)"
if [ "$RC2" -eq 4 ] && echo "$EST2" | grep -q '^FALLO' && echo "$LOG2" | grep -q 'PERDIDO'; then
  pass "perdida DETECTADA (RC=4, ESTADO FALLO, PERDIDO en log; no se salto en silencio)"
else bad "perdida: deberia marcarse PERDIDO/FALLO (RC2=$RC2 ESTADO='$EST2')"; fi

# ---- modo CONTINUO detenido por SIGTERM: el codigo de salida de fin() debe reflejar el cierre ----
RC_C=0; EST_C=""; LOG_C=""; D_C=""
run_cont(){ # $1=cp  $2=hook-antes-de-parar (opcional, se ejecuta tras 1 barrido)
  local R="$WORK/ringc"; D_C="$WORK/dstc_$RANDOM"; mk_ring "$R"
  CP="$1" RING="$R" MIN_KB=1 CLOSE_AGE=0 INT_DEFAULT=1 bash "$SCRIPT" archivar "$D_C" >/dev/null 2>&1 &
  local pid=$!
  sleep 2                                  # deja que haga >=1 barrido (marca 'visto')
  [ -n "${2:-}" ] && eval "$2"
  kill -TERM "$pid" 2>/dev/null
  wait "$pid"; RC_C=$?
  EST_C="$(cat "$D_C/ESTADO.txt" 2>/dev/null)"; LOG_C="$(cat "$D_C/archivar.log" 2>/dev/null)"
}

echo "== caso 6: continuo SIGTERM, cierre correcto =="
run_cont "cp"
if [ "$RC_C" -eq 0 ] && echo "$EST_C" | grep -q '^OK' \
   && [ -f "$D_C/live-20000101000000.pcap" ] && [ -f "$D_C/live-20000101000015.pcap" ]; then
  pass "cierre correcto (RC=0, ESTADO OK, objetivos archivados)"
else bad "cierre correcto: RC=$RC_C ESTADO='$EST_C'"; fi

echo "== caso 7: continuo SIGTERM, copia pendiente =="
run_cont "$WORK/bin/cp_error"
if [ "$RC_C" -eq 5 ] && echo "$EST_C" | grep -q '^PENDIENTE' && echo "$LOG_C" | grep -q 'FALLO' \
   && [ ! -f "$D_C/live-20000101000000.pcap" ]; then
  pass "copia pendiente al cerrar (RC=5, ESTADO PENDIENTE, sin copia) -> NO sale 0"
else bad "copia pendiente: deberia salir !=0 con PENDIENTE (RC=$RC_C ESTADO='$EST_C')"; fi

echo "== caso 8: continuo SIGTERM, archivo perdido =="
run_cont "$WORK/bin/cp_error" 'rm -f "$WORK/ringc/live-2000"*'
if [ "$RC_C" -eq 4 ] && echo "$EST_C" | grep -q '^FALLO' && echo "$LOG_C" | grep -q 'PERDIDO'; then
  pass "archivo perdido al cerrar (RC=4, ESTADO FALLO, PERDIDO en log)"
else bad "archivo perdido: deberia salir 4 con FALLO (RC=$RC_C ESTADO='$EST_C')"; fi

echo "----- archivador: $okc ok, $badc fallos"
[ "$badc" -eq 0 ]
