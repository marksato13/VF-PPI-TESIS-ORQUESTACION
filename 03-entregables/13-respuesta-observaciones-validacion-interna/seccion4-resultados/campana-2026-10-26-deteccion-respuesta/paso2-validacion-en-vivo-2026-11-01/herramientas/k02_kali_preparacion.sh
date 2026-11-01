#!/usr/bin/env bash
# PASO2 k02 — Kali: comprobaciones de PREPARACION (no evaluadas): HTTP, HTTPS y endpoints de autenticacion.
# Agente de usuario identificable. Las marcas se guardan en ~/cf-paso2-20261101T0254Z/preparacion.jsonl
set -u
UA="cf-preparacion-paso2-20261101T0254Z"; M=~/cf-paso2-20261101T0254Z/preparacion.jsonl
m(){ printf '{"t":%s,"utc":"%s","prueba":"%s","resultado":"%s"}\n' "$(date +%s.%N)" "$(date -u +%FT%T.%3NZ)" "$1" "$2" | tee -a "$M"; }
m inicio "-"
m "GET http://10.10.30.10/"            "$(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code} t=%{time_total}' http://10.10.30.10/)"
m "GET https://10.10.30.10/"           "$(curl -sk -o /dev/null -A "$UA" --max-time 5 -w '%{http_code} t=%{time_total}' https://10.10.30.10/)"
m "GET http://10.10.30.10/api/auth"    "$(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code} t=%{time_total}' http://10.10.30.10/api/auth)"
m "GET https://10.10.30.10/api/auth"   "$(curl -sk -o /dev/null -A "$UA" --max-time 5 -w '%{http_code} t=%{time_total}' https://10.10.30.10/api/auth)"
m "GET http://10.10.30.10:18081/auth"  "$(curl -s -o /dev/null -A "$UA" --max-time 5 -w '%{http_code} t=%{time_total}' http://10.10.30.10:18081/auth 2>&1)"
m fin "-"
