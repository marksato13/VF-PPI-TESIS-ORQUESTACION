#!/usr/bin/env bash
# Copia las salidas de la Etapa 3 a la carpeta de documentacion (gzip -n -9 para lo grande).
set -eu
S="C:/Users/markp/AppData/Local/Temp/claude/C--Users-markp-Desktop-PY-MEGATRON-PY---PERSONAL-TESIS/51c74eee-a71d-4dd3-9ea4-b614ec3c2579/scratchpad"
DOC="C:/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa3-deteccion-temprana-2026-11-02"
R="$DOC/resultados"; E="$S/e3"; X="$S/e3res"
mkdir -p "$R/via-rapida/humo" "$R/dns" "$R/http" "$R/contrato" "$R/comparaciones" "$R/rendimiento" "$R/replays/e3-b1ee393-e5-eventos" "$DOC/guiones"
cp "$E"/anatomia-breves.json "$E"/anatomia-sostenidos.json "$E"/anatomia-escaneos.json "$E"/rejilla-temprana.json \
   "$E"/margen-legitimo.json "$E"/rapido-3b-k8.jsonl "$E"/rapido-3b-k8-resumen.jsonl "$R/via-rapida/"
cp "$E/banco/humo/ensayo-via-rapida.jsonl" "$R/via-rapida/humo/"
cp "$X/via-rapida-episodios-e3-b1ee393-e5-eventos.json" "$R/via-rapida/via-rapida-episodios-e3.json"
cp "$X/rapida-sobre-opt.json" "$R/via-rapida/via-rapida-episodios-sobre-6b6ef82.json"
cp "$E"/atribucion-dns-3b.json "$E"/dns-dist-3b.json "$E"/politica-limit-dns-3b.json "$E"/dns-heuristica-3b.json "$R/dns/"
cp "$E"/matriz-reglas-ref.json "$E"/http-kali-3b.json "$E"/http-kali-cable-3b.json "$E"/http-cli26-3b.json "$E"/picos-http-3b.json "$R/http/"
cp "$E/doc-res/http/rasgos-port-scan.txt" "$R/http/"
cp "$X/matriz-reglas-e3-b1ee393-e5-eventos.json" "$R/http/matriz-reglas-e3.json"
cp "$E"/flow-duration-entrenamiento.json "$E"/sensibilidad-flow-duration.json "$E"/flujos-excluidos-8.json "$R/contrato/"
rm -rf "$R/analisis-3b-e3"; cp -r "$X/analisis-3b-e3-b1ee393-e5-eventos" "$R/analisis-3b-e3"
cp "$X/analisis-3b-e3-b1ee393-e5-eventos.stdout" "$R/analisis-3b-e3.stdout"
cp "$X/analisis-3b-e3-b1ee393-e5-eventos.stderr" "$R/analisis-3b-e3.stderr"
cp "$X/comparaciones/25-ref-vs-opt-vs-e3.json" "$R/comparaciones/"
cp "$X/comparaciones/sec-opt-6b6ef82-vs-e3-b1ee393-e5-eventos.json" "$R/comparaciones/sec-opt-6b6ef82-vs-e3.json"
cp "$X/rendimiento/e3-b1ee393-e5-eventos.json" "$R/rendimiento/"
L="$S/replay/e3-b1ee393-e5-eventos"; RR="$R/replays/e3-b1ee393-e5-eventos"
for f in motor_decision.log caracteristicas.jsonl ciclos-arnes.jsonl stderr.txt; do gzip -n -9 -c "$L/$f" > "$RR/$f.gz"; done
gzip -n -9 -c "$L/_state/ciclos.jsonl" > "$RR/ciclos.jsonl.gz"
cp "$E/correr_completo_e3.sh" "$E/analizar_e3.sh" "$E/ensamblar_e3.sh" "$DOC/guiones/"
if [ -s "$E/banco/bateria/ensayo-via-rapida.jsonl" ]; then
  mkdir -p "$R/via-rapida/bateria"; cp "$E/banco/bateria/ensayo-via-rapida.jsonl" "$E/banco/bateria/stdout.txt" "$E/banco/bateria/stderr.txt" "$R/via-rapida/bateria/"
  [ -f "$E/banco/bateria/resumen.json" ] && cp "$E/banco/bateria/resumen.json" "$R/via-rapida/bateria/"
  [ -f "$E/banco/bateria/TABLA.md" ] && cp "$E/banco/bateria/TABLA.md" "$R/via-rapida/bateria/"
fi
if [ -s "$E/banco/limit-dns/ensayo-limit-dns.jsonl" ]; then
  mkdir -p "$R/dns/limit-dns"
  cp "$E/banco/limit-dns/ensayo-limit-dns.jsonl" "$E/banco/limit-dns/resumen-limit-dns.json" \
     "$E/banco/limit-dns/stdout.txt" "$E/banco/limit-dns/stderr.txt" "$R/dns/limit-dns/"
  cp "$E"/banco/seg-dns/*.pcap.json "$R/dns/limit-dns/"
fi
if [ -s "$E/suite/pytest-completo.txt" ]; then
  mkdir -p "$R/pruebas"; cp "$E/suite/pytest-completo.txt" "$R/pruebas/pytest-completo-docker.txt"
fi
du -sh "$R"
# los dos JSON de anatomía grandes van comprimidos
for f in anatomia-escaneos anatomia-sostenidos; do gzip -n -9 -f "$R/via-rapida/$f.json"; done
