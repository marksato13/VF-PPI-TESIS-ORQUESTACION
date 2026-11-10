set -u
B=~/cf-e4/4c; C=$B/copias; H=~/cf-e4/herramientas; HV=~/cf-e4/herramientas-4c-v2; V1=$B/analisis
SC=~/cyberflow-e4/herramientas-20261106/salud_captura.py
T=/tmp/v2chk-$(date -u +%H%M%S); mkdir -p $T; cd $H
echo "## prueba real v2 $(date -u +%T)Z -> $T"
echo "== D1 calidad por EVE (25 episodios)"
python3 $HV/calidad_fuentes_eve.py --herramientas $H --salud-captura $SC --eve $C/eve-segmento.json --marcas $C/marcas.jsonl --archivador $C/archivar.log --muestras $C/muestras.jsonl --duracion-pcap 5 --salida $T/calidad.json > $T/calidad.out 2>&1; echo "rc=$?"
python3 - <<PY
import json, collections
j = json.load(open("$T/calidad.json"))
c = collections.Counter(v["estado"] for v in j["episodios"].values())
s = collections.Counter(v["suricata"].get("estado") for v in j["episodios"].values())
print("estados de calidad:", dict(c), "| suricata:", dict(s), "| drops:", sorted({v["suricata"].get("kernel_drops") for v in j["episodios"].values()}), "| muestras EVE:", j["fuentes"]["muestras_eve"])
malos = {k: v["motivos"] for k, v in j["episodios"].items() if v["estado"] != "completa"}
print("no completos:", malos)
PY
echo "== D2 descartes tcpdump desde SIGUSR1 de s40"
python3 $HV/descartes_tcpdump_sigusr1.py --salud-captura $SC --log $B/salud/tcpdump-anillo.log --servicios-inicio $B/estado-inicial/servicios.txt --servicios-fin $C/servicios-fin.txt --salida $T/descartes.json; echo "rc=$?"
python3 -c "
import json; d=json.load(open('$T/descartes.json')); print({k:d[k] for k in ('pid','proceso_desde','momento','dropped_by_kernel','lecturas','hueco_max_s','maximo_dropped')}); print(d['validaciones'])"
# variante "no medido": servicios-fin con otro ActiveEnterTimestamp (como si el servicio se hubiera reiniciado)
sed 's/^ActiveEnterTimestamp=Mon 2026-11-09 19:28:12 UTC$/ActiveEnterTimestamp=Mon 2026-11-09 23:00:00 UTC/' $C/servicios-fin.txt > $T/servicios-fin-alterado.txt
python3 $HV/descartes_tcpdump_sigusr1.py --salud-captura $SC --log $B/salud/tcpdump-anillo.log --servicios-inicio $B/estado-inicial/servicios.txt --servicios-fin $T/servicios-fin-alterado.txt --salida $T/descartes-null.json
echo "== paso 5 real (generar_respaldos) con 3 variantes; sin tocar la v1"
p5() { # $1=nombre $2=extra
  python3 generar_respaldos.py --marcas $C/marcas.jsonl --motor $C/motor_decision.log --eve $C/eve-segmento.json --caracteristicas $V1/caracteristicas.jsonl --pcap-dir $B/archivo-pcap --relojes $C/relojes-4c.log --servicios-inicio $B/estado-inicial/servicios.txt --servicios-fin $C/servicios-fin.txt --suricata-stats $V1/suricata-stats.json $2 --campana etapa4-campana-A-4c --salida-dir $T/resp-$1 > $T/resp-$1.out 2>&1; echo "  $1: generar_respaldos rc=$?"
  python3 verificar_integridad.py --descriptor $T/resp-$1/descriptor-integridad.json --salida $T/integ-$1.json > $T/integ-$1.out 2>&1; echo "  $1: verificar_integridad rc=$?"
}
p5 valido "--descartes-tcpdump $T/descartes.json"
p5 nulo "--descartes-tcpdump $T/descartes-null.json"
p5 sin ""
python3 - <<PY
import json, collections
for n in ("valido", "nulo", "sin"):
    caps = [json.load(open(f"$T/resp-{n}/{e}/captura.json")) for e in sorted(__import__("os").listdir(f"$T/resp-{n}")) if __import__("os").path.isdir(f"$T/resp-{n}/{e}")]
    pd = collections.Counter(repr(c["paquetes_descartados"]) for c in caps)
    j = json.load(open(f"$T/integ-{n}.json"))
    cap = collections.Counter(e["requisitos"]["captura_sin_errores_relevantes"]["estado"] for e in j["episodios"])
    print(f"{n:7} episodios={len(caps)} paquetes_descartados={dict(pd)} | captura_sin_errores_relevantes={dict(cap)} | aptos={len(j['resumen']['aptos'])}")
    if n == "valido":
        dur = [(e["episodio_id"], e["requisitos"]["cobertura_durante"]["estado"]) for e in j["episodios"] if e["requisitos"]["cobertura_durante"]["estado"] != "verificado"]
        otros = collections.Counter(k for e in j["episodios"] for k, v in e["requisitos"].items() if v["estado"] != "verificado")
        print("   requisitos no verificados con la medición válida:", dict(otros)); print("   cobertura_durante no verificada:", dur)
        print("   no aptos:", [(e["episodio_id"]) for e in j["episodios"] if not e["apto"]])
PY
echo "== la v1 sigue intacta"; (cd $V1 && sha256sum -c --quiet SHA256SUMS 2>&1 | head -3; echo "sha256sum -c SHA256SUMS de la v1: rc=$?")
echo "## fin prueba real $(date -u +%T)Z; temporales en $T (se pueden borrar)"
