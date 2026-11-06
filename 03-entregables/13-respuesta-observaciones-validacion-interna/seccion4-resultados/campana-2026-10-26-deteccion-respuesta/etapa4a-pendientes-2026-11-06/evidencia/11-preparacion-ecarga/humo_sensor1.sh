set -u
# [SENSOR1 m4rk] PRUEBA DE HUMO de la cadena de evaluación sobre los ~20 s de la prueba de mecanismo (sin generadores).
# NO es E-carga ni ninguna ventana: solo comprueba que las herramientas corren en el host con ficheros reales y que la
# entrada construida cumple el contrato del evaluador (rc distinto de 2). El resultado no tiene valor de medida.
X=$(ls -d ~/cf-e4/ecarga-v2-seco-*/sensor1-mecanismo | tail -1); E=~/cf-e4/ecarga-v2-evaluacion-e83f4be6
P=~/cf-e4/paquete-ae2900e
echo "carpeta de prueba: $X"
read D A < <(python3 -I -c 'import json,sys;t=[json.loads(l)["t"] for l in open(sys.argv[1]) if l.strip()];print(t[0]+1,t[-1]-1)' "$X/muestras.jsonl")
echo "periodo de prueba: $D – $A"
bash $E/sensor1_post.sh "$X" "$D" "$A"
echo "######## construir_entrada (solo fuentes de Sensor1; S de bastión y manuales sin dar -> null)"
python3 -I $E/construir_entrada.py --desde "$D" --hasta "$A" --clasificacion "$X/post/clasificacion/clasificacion.json" \
  --comparar "$X/post/comparar.json" --perfiles "$X/post/perfiles.json" --perfiles-rc "$(cat "$X/post/perfiles.rc")" \
  --pcap "$X/post/pcap_s.json" --salida-entrada "$X/post/entrada-PRUEBA.json" --salida-traza "$X/post/traza-PRUEBA.json"; echo "rc=$?"
python3 -I -c 'import json,sys;e=json.load(open(sys.argv[1]));print("K",e["K"]);print("S",e["S"]);print("clase",e["clasificacion"],"suricata",e["suricata"],"dpm",e["descartes_por_millon"])' "$X/post/entrada-PRUEBA.json"
echo "######## veredicto con el evaluador del paquete ae2900e"
python3 -I $P/deploy/etapa4/sensor1/evaluar_ecarga.py veredicto --entrada "$X/post/entrada-PRUEBA.json" > "$X/post/veredicto-PRUEBA.json"; echo "rc=$?"
python3 -I -c 'import json,sys;r=json.load(open(sys.argv[1]));print({k:r.get(k) for k in ("version","estabilidad_tecnica","habilita_condicion_3","K_sin_medida","incoherencias","error")})' "$X/post/veredicto-PRUEBA.json"
echo "######## generadores no intervienen; fin $(date -u +%FT%TZ)"
