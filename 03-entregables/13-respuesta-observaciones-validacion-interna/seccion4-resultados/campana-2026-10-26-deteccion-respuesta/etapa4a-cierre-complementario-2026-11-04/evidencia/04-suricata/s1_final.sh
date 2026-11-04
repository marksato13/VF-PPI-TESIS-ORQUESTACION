set -u
# [Sensor1 m4rk] Análisis de la ventana fija del ensayo del anillo (06:26:55–07:26:55 UTC). Solo lectura.
C=/home/m4rk/cf-e4/cierre4a; H=$C/herr; PY=/home/m4rk/cyberflow/.venv/bin/python
O=$C/ensayo; mkdir -p $O
T0=$(date -ud 2026-11-04T06:16:55Z +%s); D=$((T0+600)); HH=$((T0+4200))
echo "ventana $D $HH ($(date -ud @$D +%T)–$(date -ud @$HH +%T)); ahora $(date -u +%T)" | tee $O/ventana.txt
[ $(date +%s) -lt $HH ] && { echo "PARADA: la ventana aún no ha terminado"; exit 1; }
cp $C/salud/muestras.jsonl $O/muestras-copia.jsonl; cp $C/salud/fino.jsonl $O/fino-copia.jsonl
echo "== Suricata: proceso, reinicios y errores"
systemctl show suricata -p ActiveState -p MainPID -p ExecMainStartTimestamp -p NRestarts | tee $O/suricata-estado.txt
awk -v t="2026-11-04 06:16:5" '{ if (index($0, "2026-11-04 06:16:5") || f) {f=1; print} }' /var/log/suricata/suricata.log \
   | grep -iE 'error|warn|unable|alloc|mmap|ring|af-packet|Engine' | grep -v 'no rules were loaded' | tee $O/suricata-log-ensayo.txt
echo "== Suricata: ventana del ensayo (eve stats) y calentamiento"
$PY -I $H/comparar_suricata.py --stats-eve /var/log/suricata/eve.json --eve /var/log/suricata/eve.json --desde $D --hasta $HH --etiqueta "ensayo ring-size 16384" > $O/ensayo-suricata.json
$PY -I $H/comparar_suricata.py --stats-eve /var/log/suricata/eve.json --eve /var/log/suricata/eve.json --desde $T0 --hasta $D --etiqueta "calentamiento" > $O/calentamiento-suricata.json
$PY -I $H/comparar_suricata.py --stats-eve /var/log/suricata/eve.json --eve /var/log/suricata/eve.json \
   --desde $(date -ud 2026-11-04T02:19:45Z +%s) --hasta $(date -ud 2026-11-04T03:19:51Z +%s) --etiqueta "4A (eve)" > $O/base-4a-suricata-eve-flujos.json
$PY -c '
import json,sys
for f in sys.argv[1:]:
    d=json.load(open(f)); q=d["paquetes_por_intervalo"]
    print("%-24s %s bloques=%d interv=%d hueco_max=%s reinicios=%d cobertura_s=%s paq=%d desc=%d por_M=%s episodios=%s rafagas=%d p50/p95/max=%s/%s/%s pps_max=%s flujos=%d grandes=%d pk_grandes=%d" % (
      d["etiqueta"], d["fuente_contadores"], d["bloques_stats"], d["intervalos_validos"], d["hueco_max_entre_bloques_s"], d["reinicios_suricata_en_ventana"], d["cobertura_stats_s"],
      d["paquetes"], d["descartes"], d["descartes_por_millon"], [(x["t_utc"],x["paquetes"],x["descartes"]) for x in d["intervalos_con_descartes"]],
      d["rafagas_ge_umbral"], q["p50"], q["p95"], q["max"], d["pps_max_intervalo"], d["flujos_eve"], d["flujos_grandes"], d["paquetes_en_flujos_grandes"]))
    print("   srv-dmz por cliente:", {k:(v["flujos"],v["paquetes"]) for k,v in list(d["volumen_srv_dmz_por_cliente"].items())[:6]})
' $O/base-4a-suricata-eve-flujos.json $O/calentamiento-suricata.json $O/ensayo-suricata.json | tee $O/resumen-suricata.txt
echo "== recursos (muestreo fino 1 s)"
$PY -I $H/analizar_fino.py --fino $O/fino-copia.jsonl --desde $D --hasta $HH > $O/fino-ensayo.json; cat $O/fino-ensayo.json
$PY -I $H/analizar_fino.py --fino $O/fino-copia.jsonl --desde $T0 --hasta $D > $O/fino-calentamiento.json
$PY -I $H/analizar_fino.py --fino $O/fino-copia.jsonl --desde $(date -ud 2026-11-04T06:05:00Z +%s) --hasta $(date -ud 2026-11-04T06:12:40Z +%s) > $O/fino-previo-anillo-viejo.json
$PY -c 'import json,sys
for f in sys.argv[1:]:
    d=json.load(open(f)); print(f.split("/")[-1], "cpu_hilo", d["suricata_cpu_hilo_mas_cargado_pct"], "softirq", d["host_softirq_pct"], "iowait", d["host_iowait_pct"], "disco", d["disco_ms_en_es_por_s"], "mem_min", d["mem_disponible_min_kb"], "rss_max", d["suricata_rss_max_kb"], "softnet", d["softnet_incrementos"], "nic", d["nic_incrementos"], "eve_parada", d["eve_parada_max_s"])' \
  $O/fino-previo-anillo-viejo.json $O/fino-calentamiento.json $O/fino-ensayo.json | tee $O/resumen-fino.txt
echo "== calidad de captura en la ventana (clasificar_periodo, criterios congelados)"
$PY -I $H/clasificar_periodo.py --salud-captura /home/m4rk/cyberflow-e4/ec78ca5/scripts/etapa4/salud_captura.py \
   --muestras $O/muestras-copia.jsonl --salida $O/clasificacion --desde $D --hasta $HH > $O/clasificar.out 2>&1; echo "rc_clasificar=$?" | tee -a $O/clasificar.out
tail -n 30 $O/clasificar.out
[ -f $O/clasificacion/clasificacion.json ] && $PY -c 'import json; d=json.load(open("'$O'/clasificacion/clasificacion.json")); print(json.dumps({k:v for k,v in d.items() if k!="capturas"}, ensure_ascii=False)[:1500]); [print(k, v.get("clase"), v.get("motivos_c3") or v.get("motivos"), v.get("continuidad")) for k,v in d.get("capturas",{}).items()]'
echo "== motor y vía rápida en la ventana"
$PY - $D $HH <<'EOF' | tee $O/motor-ventana.txt
import json, sys, collections
D, H = float(sys.argv[1]), float(sys.argv[2])
c = []
for l in open("/home/m4rk/cyberflow/logs/_state-e4/ciclos.jsonl"):
    try: x = json.loads(l)
    except ValueError: continue
    if D <= x.get("inicio_ciclo", 0) <= H: c.append(x)
dur = sorted(x["duracion_s"] for x in c); ini = [x["inicio_ciclo"] for x in c]
print("ciclos", len(c), "dur p50/p95/max", dur[len(dur)//2] if dur else None, dur[int(.95*(len(dur)-1))] if dur else None, dur[-1] if dur else None,
      "hueco_max_entre_ciclos_s", round(max((b-a for a, b in zip(ini, ini[1:])), default=0), 2), "disparos", collections.Counter(x.get("disparo") for x in c))
n = 0; ile = collections.Counter(); hc = collections.Counter(); dec = collections.Counter(); ifd = collections.Counter()
with open("/home/m4rk/cyberflow/logs/motor_decision.log") as fh:
    fh.seek(0, 2); fh.seek(max(0, fh.tell() - 120_000_000)); fh.readline()
    for l in fh:
        if '"event": "decision"' not in l: continue
        x = json.loads(l)
        if not (D <= x.get("decidido_en", 0) <= H): continue
        n += 1; ile[x.get("pcaps_ilegibles")] += 1; hc[x.get("historial_completo")] += 1; dec[x.get("decision")] += 1; ifd[x.get("decision_if")] += 1
print("decisiones", n, "decision", dict(dec), "decision_if", dict(ifd), "pcaps_ilegibles", dict(ile), "historial_completo", dict(hc))
EOF
echo "== v1 sigue parada, sin aplicación, ruleset"
for u in ppi-publicar-feed.timer ppi-publicar-feed.service ppi-publicar-feed-v2.service ppi-motor.service ppi-motor-capture.service ppi-dashboard.service ppi-via-rapida@ens37.service; do
  printf '%s ' $u; systemctl show $u -p ActiveState -p UnitFileState -p MainPID -p NRestarts --value | tr '\n' ' '; echo; done | tee $O/unidades-fin.txt
stat -c '%n %y' /home/m4rk/feed/feed.json /home/m4rk/feed/acuses/srv-dmz.json | tee -a $O/unidades-fin.txt
ps -eo pid,args | grep -E -- '--aplicar|--enforce|publicar_feed.py ' | grep -v grep || echo "ningún proceso v1 ni con --aplicar/--enforce"
sudo -n nft list ruleset | sha256sum | tee $O/nft-fin.sha256
ls -la --time-style=full-iso /home/m4rk/feed-v2/ | grep -E 'traza|senales-if|feed.json'
( cd $O && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
echo "evidencia en $O"
