import json, sys
from pathlib import Path
p = Path(sys.argv[1]); c = json.loads(p.read_text(encoding="utf-8"))
assert c["version_config"]["version"] == "3b-2026-11-01.1"

c["version_config"] = {
    "version": "3b-2026-11-01.2",
    "anterior": "3b-2026-11-01.1 (commit e0ba9e0): conservaba en 'codigo' las referencias del motor de la primera A, la "
                "precondicion del agente ACTIVE+ENABLED y la restauracion del enforcement tras A",
    "deriva_de": "config-campana.json 2026-10-28.3 (sin modificarla)",
    "cambios": [
        "poblacion: excepciones_respuesta separadas de exclusiones_poblacion (scripts/poblacion.py); el DNS 10.10.10.20 queda EN la poblacion como excepcion de respuesta",
        "umbrales.fuente.archivo: ruta relativa ajustada a esta carpeta (los valores no cambian)",
        "protocolo_3b: cobertura (requeridas = rejilla del episodio; no evaluadas de la referencia siguen requeridas), puntualidad, deteccion durante el ataque, calidad de fuentes, cierre del archivo >= fin_ultimo + 180 s",
        "3b-2026-11-01.2: 'codigo' describe el motor INCREMENTAL instalado (24f8a80) con blobs y sha256 verificados contra el sensor; lo anterior pasa a codigo_historico_primera_A",
        "3b-2026-11-01.2: estado_operativo_3b sustituye la precondicion heredada del agente y la restauracion del enforcement (que pertenece a la preparacion de la campana B)"],
    "sin_cambios": "modelo, escalador, 28 caracteristicas, historia 230 s, umbral desplegado, umbrales 0,05/0,03/0,01, heuristicos, 7 configuraciones, 5 escenarios x 5 repeticiones"}

c["codigo_historico_primera_A"] = {
    "_nota": "HISTORICO: referencias vigentes en la primera campana A (motor 62a75a1/7b275b8, producto-main 53f919e). NO describen el motor del 3B; se conservan solo como trazabilidad.",
    **c.pop("codigo")}

sha = {"motor_decision.py": "6c274d9e3529e3fb6971ff38d8c6d586780b718b483ce4e2a5e3a1cfbf25692e",
       "motor_incremental.py": "a403307aa5f76d38d199aef2542350f57eaf5843fdb94b44ec0bd20eaa8ff168",
       "heuristicos.py": "10deb05d22fa0215e5f5f37bc6f05225cda31b806c67051a6584d878e25ed6a2",
       "extract_multilayer_v2.py": "7130edae65afefa2fd82a9314e20194adec684f4b2c3c35c2337880d8e636ccb",
       "extract_multilayer_v3.py": "5adbfbf4845554430a3e8b5a4c00eb1e45c2216cae73532da73d9d3f4898fa7f",
       "feed.py": "b4d36adb3f29b21693eb0cd964515aed42b3965910379616f1af27441793baba",
       "publicar_feed.py": "f7bc4c7d8e7ac0cd958f3936d55a5782285e59509919d82bf2998fbb70acc03d",
       "escalada.py": "7d80ab4a926457efb37f4c6c9778e53eda67a5840ca255ff4504f333ca638479",
       "multilayer-v2.json": "e032a1a28650d438ae707c93b3045801770b3a069b4395426077af3bbd2b0e33"}
c["codigo"] = {
    "_nota": "Motor INCREMENTAL realmente instalado en el Sensor1 (paso 2, 2026-11-01) y sus dependencias. Verificado en la preparacion 3A (2026-11-01 06:23Z, guion s11): blob git del fichero desplegado (git hash-object en el sensor) comparado con el blob del commit en el clon local del repo del producto. Re-verificar los sha256 antes de empezar el 3B.",
    "repo_producto": "github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos",
    "commit_motor": "24f8a80e376d89b78454fd16854d2239a1b7d278",
    "rama_motor": "candidato/motor-rendimiento-20261031",
    "commit_as_deployed": "f57ca00 (rama master / origin/as-deployed-sensor-20261006; snapshot del Sensor1 del 2026-10-29)",
    "ficheros_sensor": {
        "scripts/engine/motor_decision.py": {"origen": "24f8a80", "ultimo_commit": "9b4cf2b", "blob_git": "068c025dc867e753d59167b0e73d9df10db00c64", "sha256": sha["motor_decision.py"], "coincide_con_commit": True},
        "scripts/engine/motor_incremental.py": {"origen": "24f8a80", "ultimo_commit": "4552d83", "blob_git": "1197907c0d3f8e1c28001485bb43b1ed5fc12375", "sha256": sha["motor_incremental.py"], "coincide_con_commit": True},
        "scripts/engine/heuristicos.py": {"origen": "24f8a80", "ultimo_commit": "2d854a9", "blob_git": "ec0fe9e870c2f3c98c0cc9140011674df327f1f3", "sha256": sha["heuristicos.py"], "version_umbrales": "2026-10-06.2", "coincide_con_commit": True},
        "scripts/features/extract_multilayer_v2.py": {"origen": "24f8a80", "ultimo_commit": "2d854a9", "blob_git": "ec46849dc8454976b056622e334cc35b7cc95d26", "sha256": sha["extract_multilayer_v2.py"], "coincide_con_commit": True},
        "scripts/features/extract_multilayer_v3.py": {"origen": "24f8a80", "ultimo_commit": "a6d287a", "blob_git": "0739e4cda326c640facb5b6d1def1182a1d8b09c", "sha256": sha["extract_multilayer_v3.py"], "coincide_con_commit": True},
        "scripts/engine/feed.py": {"origen": "24f8a80", "ultimo_commit": "a6d287a", "blob_git": "fa30b818f03bf389554559312fc3e596314f3750", "sha256": sha["feed.py"], "coincide_con_commit": True},
        "configs/features/multilayer-v2.json": {"origen": "24f8a80 (contenido)", "blob_git_desplegado": "9560ce9e49f569e930dff07f12c3a85a1e7d0a82", "blob_git_commit": "20a89b8176b689cd3b31668c5c75a0fbdb4b39ca", "sha256": sha["multilayer-v2.json"], "coincide_con_commit": "contenido identico salvo fin de linea: el fichero desplegado tiene CRLF (37 lineas); normalizado a LF es byte a byte el blob 20a89b8 y el JSON es igual"},
        "scripts/engine/publicar_feed.py": {"origen": "f57ca00 (as-deployed; igual que el tag validacion-interna-2026-10-15, 6d92ff3), NO 24f8a80", "blob_git": "bf2b73f49fbbd48df8931540d2ff475403f12d15", "blob_en_24f8a80": "f73db5af8e2949f88ba2bbf23651af7ab3bf7d3a", "sha256": sha["publicar_feed.py"], "nota": "cadena de respuesta; el paso 2 solo instalo el motor y no la toco"},
        "scripts/engine/escalada.py": {"origen": "f57ca00 (as-deployed; igual que 6d92ff3), NO 24f8a80", "blob_git": "7bd55de8fbb261e521ebfbe40ad0a9bf04277dfb", "blob_en_24f8a80": "8f260bd0874b56809123f0f0ade9c234cb9b6014", "sha256": sha["escalada.py"]}},
    "modelo": {"artefacto": "artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib", "sha256": "df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60",
               "manifiesto": "artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json", "manifiesto_sha256": "b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7"},
    "srv_dmz_agente_enforce": {"fichero": "/home/adminsrvdmz/enforce/agente_enforce.py", "blob_git": "b769b01cac1cef9c3f1ee5f2ace4d16dc8aabec3", "origen": "tag validacion-interna-2026-10-15 (6d92ff3)", "sha256": "2985c1230a61933b308c84822b35217a1f6a6680a4a03b1bde07f4025778cb63", "estado": "timer y servicio inactive, timer disabled (sombra)"},
    "argv_motor": "evidencia/sensor/estado-inicial/argv-motor.txt (sin --enforce; --history-seconds 230 --step-seconds 10)"}

A = c["campanas"]["A_deteccion_4.2"]
c["campanas"]["historico_primera_A"] = {
    "_nota": "HISTORICO de la primera campana A (2026-10-28). NO aplica al 3B.",
    "precondicion_critica": A.pop("precondicion_critica")}
A["modo"] = "SOMBRA durante todo el 3B: el motor no lleva --enforce, el agente de srv-dmz esta parado y deshabilitado y no existe la tabla nft inet cyberflow; ninguna restriccion altera el trafico"
c["estado_operativo_3b"] = {
    "durante": "sombra: sin aplicacion de restricciones. El publicador del feed sigue escribiendo propuestas cada 10 s; nadie las aplica.",
    "verificar_antes_de_empezar": [
        "[SENSOR1] ppi-motor active, NRestarts registrado, sin --enforce en argv (/proc/<pid>/cmdline) ni en la unidad",
        "[SENSOR1] sha256 de 'codigo.ficheros_sensor' y del modelo iguales a esta config",
        "[srv-dmz] ppi-enforce-agent.timer y .service inactive; timer disabled",
        "[srv-dmz] 'sudo nft list tables' sin 'inet cyberflow'",
        "[SENSOR1] copia con sha256 de ~/feed/feed.json, feed.sig y estado.json"],
    "estado_de_escalada": "se conserva tal como este (la Kali llega con bloqueos=3 de propuestas en sombra); NO se restablece ni se edita. Se copia con hash al empezar y al terminar. No afecta a la deteccion: el motor no lee estado.json.",
    "al_terminar": "permanecer en sombra: no se ejecuta restaurar_enforcement.sh ni se arranca el agente. Repetir las verificaciones de 'verificar_antes_de_empezar' y copiar feed/estado con hash.",
    "activacion_de_la_respuesta": "pertenece a la PREPARACION de la campana B (estado inicial de la escalada, restauracion del enforcement y su verificacion), con autorizacion explicita. No forma parte del 3B."}

c["historia_y_registros"]["_nota_3b"] = ("despues_de_cada_episodio_s (90) rige ENTRE episodios. El CIERRE FINAL del archivo "
    "es distinto: protocolo_3b.cierre_archivo (>= fin del ultimo episodio + 180 s, prolongado hasta verificar)")
for k in ("evaluabilidad_episodio", "criterios_evaluacion"):
    c[k] = {"_nota": "HISTORICO (primera campana A, analizar.py). Para el 3B rigen protocolo_3b y analizar_3b.py.", **c[k]}
c["emision_vs_window_end"]["_nota_3b"] = ("En el 3B el motor es el incremental 24f8a80; la disponibilidad de una ventana "
    "es registro_escrito_en del ciclo (ciclos.jsonl), y logged_at solo si no se puede enlazar (protocolo_3b.disponibilidad)")

pb = c["protocolo_3b"]
pb["inventario"] = ("replay_motor.py con el motor instalado sobre el PCAP y el EVE archivados; rango window_end en "
                    "[inicio_archivo + 230, cierre_archivo - 120]; requeridas = claves con decision O ventana_no_evaluada "
                    "en la referencia (siguen requeridas aunque no se evaluaran)")
pb["ventanas_episodio"] = "rejilla de 10 s, window_end en (inicio, fin+60) abierto en ambos extremos; requeridas aunque falten en la referencia; sin exclusiones definidas"
pb["observacion_completa"] = ("rango del inventario contiene todas las ventanas requeridas + todas decididas en vivo + "
                              "calidad_fuentes 'completa' + integridad apta + destino por ventana")
pb["control"] = ("tramo cubierto = [desde, hasta] ∩ rango del inventario (poblacion = requeridas; cotas sobre ellas); "
                 "tramos fuera del inventario se informan aparte con cobertura no determinable. Requisito: desde >= "
                 "inicio_archivo + 230 s y hasta <= cierre_archivo - 120 s")
pb["cierre_archivo"] = {
    "minimo_s_tras_fin_ultimo_episodio": 180,
    "calculo": "la ultima ventana requerida tiene window_end < fin_ultimo + 60; el inventario solo es utilizable hasta "
               "cierre_archivo - 120; luego cierre_archivo >= fin_ultimo + 60 + 120 = fin_ultimo + 180",
    "marcas": {"fin_ultimo": "evento 'fin' del ultimo episodio en marcas.jsonl (reloj de pared, UTC)",
               "inicio_archivo": "inicio (nombre live-YYYYmmddHHMMSS.pcap) del primer PCAP con linea OK en archivar.log",
               "cierre_archivo": "inicio del ultimo PCAP con linea OK en archivar.log + 15 s"},
    "verificacion": "ver PROTOCOLO-CAMPANA-A-REPETIDA.md seccion 3 bis"}
p.write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print("ok")
