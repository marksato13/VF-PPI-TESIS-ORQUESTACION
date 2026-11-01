#!/usr/bin/env bash
set -u
B=$HOME/cf-paso2-20261101T0254Z
setsid nohup bash $B/herramientas/s30_replay.sh 2026-11-01T03:19:50Z 2026-11-01T04:18:10Z > $B/replay.lanzador.out 2>&1 < /dev/null &
sleep 20; echo "replay: $(pgrep -fc replay_motor.py) proceso(s)"; tail -2 $B/replay/stderr.txt 2>/dev/null
python3 $B/herramientas/analizar_p2.py --base $B --copias copias --t-normal 2026-11-01T03:20:00Z --t-fin 2026-11-01T04:18:15Z --salida $B/copias/resultados-sin-inventario.json
python3 - $B/copias/resultados-sin-inventario.json <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(json.dumps(d["episodios"], indent=0, default=str))
for c, v in d["condiciones"].items():
    r = v["recursos"]
    print("%-15s ciclos %3d p50 %5.2f p95 %5.2f max %5.2f >9.5 %d >10 %d | pend p95 %s max %s 1/3 %.1f->%.1f | lag dec p50 %.1f p95 %.1f max %.1f | esc-dec max %.4f | orden_ok %d/%d | cpu p95 %.0f rss %.0f memmin %.0f swap %.0f pswpout %d | rxdrop %d sur %s" % (
        c, v["ciclos"]["n"], v["ciclos"]["p50"], v["ciclos"]["p95"], v["ciclos"]["max"], v["ciclos_mas_9_5"], v["ciclos_mas_10"],
        v["pendientes"]["p95"], v["pendientes"]["max"], v["pendientes"]["media_primer_tercio"], v["pendientes"]["media_ultimo_tercio"],
        v["retraso_decidido_menos_wend"]["p50"], v["retraso_decidido_menos_wend"]["p95"], v["retraso_decidido_menos_wend"]["max"],
        v["escrito_menos_decidido"]["max"] or 0, v["orden_decidido_logged_escrito_ok"], v["ventanas_por_window_end"]["decisiones"],
        r["cpu_motor_pct"]["p95"] or 0, r["rss_mb_max"], r["memavail_mb_min"], r["swap_usado_mb_max"], r["pswpout"], r["ens37_rx_drop"], v["suricata"]))
    if v["lista_mas_9_5"]: print("    >9.5:", v["lista_mas_9_5"])
    print("    ventanas", v["ventanas_por_window_end"], "| http", v["http_kali_servidor"], "| sin_dec_nuevas", v["ciclos_sin_decisiones_nuevas"], "| edad pcap max %.1f eve max %.1f" % (v["edad_marca_pcap"]["max"], v["edad_marca_eve"]["max"]))
print(d["duplicados"])
for k, e in d["deteccion"].items():
    print(k, "emitidas", e["emitidas"], "durante", e["emitidas_durante"], "ventanas_durante", e["ventanas_kali_durante"], "primera", e["primera_emision_durante"], "derivadas", e["derivadas_durante"])
print(json.dumps(d["alertas_no_kali_por_condicion"], indent=0))
PY
