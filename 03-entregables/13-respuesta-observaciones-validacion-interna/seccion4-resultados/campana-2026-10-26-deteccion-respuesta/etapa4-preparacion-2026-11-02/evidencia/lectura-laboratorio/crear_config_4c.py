"""Crea config-campana-4c.json a partir de config-campana-3b.json SIN cambiar umbrales, población, modelo, 28
características, historia, configuraciones ni criterios. Solo actualiza lo que describe la ejecución: campaña,
versión, escenarios (escenarios-4c.json, semilla 20261102), código instalado (ec78ca5 por drop-in, con los sha256
del paquete) y estado operativo de la Etapa 4. Escribe UTF-8 con LF.

Uso: python crear_config_4c.py <carpeta campana-2026-10-26-deteccion-respuesta>
"""
import hashlib
import json
import sys
from pathlib import Path

camp = Path(sys.argv[1])
prep = camp / "etapa4-preparacion-2026-11-02"
base = json.loads((camp / "preparacion-3a-2026-11-01" / "config-campana-3b.json").read_text(encoding="utf-8"))
esc = prep / "escenarios-4c.json"
sums = {}
for ln in (prep / "evidencia" / "paquete" / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    h, f = ln.split(maxsplit=1)
    sums[f.lstrip("*").removeprefix("./")] = h
cfg = dict(base)
cfg["campana"] = "deteccion-respuesta-2026-10-26 / Etapa 4, campana A nueva (4C) y control normal (4B)"
cfg["registrado"] = "2026-11-02, en la preparacion de la Etapa 4, antes de instalar y antes de ejecutar ningun episodio."
cfg["version_config"] = {
    "version": "4c-2026-11-02.1", "anterior": "3b-2026-11-01.2", "deriva_de": "preparacion-3a-2026-11-01/config-campana-3b.json (sin modificarla)",
    "cambios": ["escenarios: escenarios-4c.json (semilla 20261102; resto identico a escenarios/escenarios.json)",
                "codigo: candidato ec78ca5 instalado por drop-in en /home/m4rk/cyberflow-e4/ec78ca5 (--disparo eventos, _state-e4); el de 24f8a80 pasa a codigo_3b",
                "estado_operativo_etapa4 sustituye a estado_operativo_3b (sombra con agente v2 sin --aplicar y rele v2 a srv-dmz)",
                "protocolo_3b.documento apunta a los protocolos de la Etapa 4; cierre >= fin_ultimo + 300 s; anillo de 5 s"],
    "sin_cambios": base["version_config"]["sin_cambios"]}
cfg["escenarios"] = dict(base["escenarios"], definicion="etapa4-preparacion-2026-11-02/escenarios-4c.json (copia de escenarios/escenarios.json con semilla nueva)",
                         semilla=20261102, sha256_lf=hashlib.sha256(esc.read_bytes()).hexdigest(),
                         orden_publicado="etapa4-preparacion-2026-11-02/ORDEN-4C.md")
cfg["protocolo_3b"] = dict(base["protocolo_3b"], documento="etapa4-preparacion-2026-11-02/PROTOCOLO-4C-CAMPANA-A.md y PROTOCOLO-4B-CONTROL.md",
                           cierre_archivo=dict(base["protocolo_3b"].get("cierre_archivo") or {}, minimo_s_tras_fin_ultimo_episodio=300,
                                               nota_etapa4="300 s: 180 s del 3B + 120 s de margen (el ultimo episodio es escaneo_sostenido)"),
                           rotacion_pcap_s=5, calidad_fuentes="calidad_fuentes.py --duracion-pcap 5",
                           salud="SALUD-CAPTURA.md (C0-C3 por periodo con salud_captura.py)")
cfg["codigo_3b"] = base["codigo"]
fich = {f: {"sha256": sums[f], "origen": "ec78ca5"} for f in sorted(sums)
        if f.startswith(("scripts/engine/", "scripts/features/", "configs/features/")) and not f.startswith("scripts/etapa4/")}
cfg["codigo"] = {"_nota": "Candidato de la Etapa 4 instalado en sombra (4A). Sha256 del paquete (evidencia/paquete/SHA256SUMS); re-verificar con sha256sum -c en el Sensor1 antes de empezar.",
                 "repo_producto": base["codigo"]["repo_producto"], "commit_motor": "ec78ca56a3a8f4bb17fda967a7f0abe0e9a2c742",
                 "rama_motor": "candidato/etapa3-20261102", "herramientas": "acc6588 (scripts/etapa4, deploy/etapa4)",
                 "ruta_sensor": "/home/m4rk/cyberflow-e4/ec78ca5", "argumentos": "deploy/etapa4/unidades/sensor1/ppi-motor.service.d/etapa4.conf",
                 "modelo_manifiesto_esquema": "los de ~/cyberflow (sin cambios: modelo df547da0..., manifiesto b3ad6805..., esquema e032a1a2...)",
                 "cadena_v1_sin_cambios": "publicar_feed.py y escalada.py as-deployed f57ca00",
                 "ficheros_paquete": fich}
cfg.pop("estado_operativo_3b", None)
cfg["estado_operativo_etapa4"] = {
    "durante": "sombra: motor sin --enforce; publicador v2 propone; rele v2 entrega a srv-dmz; agente v2 dmz SIN --aplicar; agente v1 disabled/inactive; DC1 sin CyberFlow; LIMIT DNS sin aplicar",
    "verificar_antes_de_empezar": ["verificar_sensor1.sh", "verificar_bastion.sh", "CON_SUDO=1 verificar_srvdmz.sh <respaldo>", "SALUD-CAPTURA.md §4.1 (I1-I8)"],
    "al_terminar": "permanecer en sombra; repetir las verificaciones; copiar feed v1/v2 y estado con hash",
    "activacion_de_la_respuesta": "pertenece a la preparacion de la campana B, con autorizacion explicita. No forma parte de la Etapa 4."}
out = prep / "config-campana-4c.json"
out.write_bytes((json.dumps(cfg, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
print(out, hashlib.sha256(out.read_bytes()).hexdigest(), len(fich), "ficheros de codigo")
