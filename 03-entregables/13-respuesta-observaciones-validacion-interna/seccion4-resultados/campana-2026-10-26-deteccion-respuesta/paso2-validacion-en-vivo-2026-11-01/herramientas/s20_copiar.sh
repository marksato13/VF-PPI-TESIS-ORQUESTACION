#!/usr/bin/env bash
# PASO2 s20 — sensor: copia (solo lectura de las fuentes) el estado actual a ~/cf-paso2-ID/<DESTINO>/ para analizar.
# Uso: s20_copiar.sh <copias|copias-prueba-HHMM>
set -u
ID=20261101T0254Z; B=$HOME/cf-paso2-$ID; D=$B/${1:?destino}
mkdir -p "$D"
cp -p $HOME/cyberflow/logs/_state/ciclos.jsonl "$D/ciclos.jsonl"
cp -p $HOME/cyberflow/logs/motor_decision.log "$D/motor_decision.log"
cp -p $HOME/cyberflow/logs/motor_decision.log.1 "$D/motor_decision.log.1"
cp -p $B/recursos/muestras.jsonl "$D/muestras.jsonl"
cp -p $B/eve/stats-inicio.log "$D/stats-inicio.log"; cp -p /var/log/suricata/stats.log "$D/stats-fin.log"
I=$(head -1 $B/eve/inicio.json | python3 -c 'import json,sys;d=json.loads(sys.stdin.read());print(d["inode"],d["size"])')
set -- $I
if [ "$(stat -c %i /var/log/suricata/eve.json)" = "$1" ]; then tail -c +$(( $2 + 1 )) /var/log/suricata/eve.json > "$D/eve-segmento.json"; echo "  eve segmento desde byte $2: $(stat -c %s "$D/eve-segmento.json") bytes"
else echo "  AVISO: eve.json cambio de inodo (rotacion); segmento no extraido"; fi
cp -p $B/archivo-pcap/ESTADO.txt "$D/archivador-ESTADO.txt"
[ -f "$B/marcas-episodios.jsonl" ] && cp -p "$B/marcas-episodios.jsonl" "$D/marcas-episodios.jsonl" || : > "$D/marcas-episodios.jsonl"
( cd "$D" && sha256sum * > SHA256SUMS ) ; wc -l "$D"/*.jsonl "$D"/motor_decision.log | sed 's/^/  /'
