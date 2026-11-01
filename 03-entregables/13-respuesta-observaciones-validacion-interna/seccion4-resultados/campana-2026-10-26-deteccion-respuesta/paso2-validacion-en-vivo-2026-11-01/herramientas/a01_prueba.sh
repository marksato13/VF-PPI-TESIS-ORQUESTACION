#!/usr/bin/env bash
set -u
B=$HOME/cf-paso2-20261101T0254Z; C=copias-prueba-0325
python3 $B/herramientas/analizar_p2.py --base $B --copias $C --t-normal 2026-11-01T03:20:00Z --t-fin 2026-11-01T05:00:00Z --salida $B/$C/resultados.json 2>&1 | tail -5
python3 - $B/$C/resultados.json <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for c, v in d["condiciones"].items():
    print(c, v["intervalo_ciclos"], v["ciclos"], v["ciclos_mas_9_5"], "pend", v["pendientes"])
    print("   retraso decidido", v["retraso_decidido_menos_wend"], "escrito-decidido", v["escrito_menos_decidido"])
    print("   ventanas", v["ventanas_por_window_end"], "orden_ok", v["orden_decidido_logged_escrito_ok"], "sin_ciclo", v["orden_sin_ciclo"])
    print("   recursos", v["recursos"])
    print("   suricata", v["suricata"], "http", v["http_kali_servidor"])
    print("   edad pcap", v["edad_marca_pcap"], "edad eve", v["edad_marca_eve"])
print(d["duplicados"])
print(d["alertas_no_kali_por_condicion"])
PY
