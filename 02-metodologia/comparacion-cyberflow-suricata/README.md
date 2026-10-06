# Comparacion CyberFlow vs Suricata

Carpeta de trabajo para el experimento solicitado por el asesor: comparar la
deteccion temprana de CyberFlow contra la deteccion basada en reglas de Suricata
bajo los mismos episodios de trafico controlado.

## Documentos

| Archivo | Contenido |
|---|---|
| `00-ESTADO-Y-DECISIONES.md` | Lo confirmado, lo realizado y las decisiones abiertas |
| `01-PLAN-P0.md` | Plan ejecutable del primer bloque, sin cambios destructivos |
| `02-ARQUITECTURA.md` | Topologia, interfaces y opciones de SPAN |
| `03-METRICAS-Y-EVIDENCIAS.md` | Metricas, formulas, timestamps y artefactos |
| `04-CHECKLIST-OPERACION.md` | Preflight, ejecucion, rollback y cierre |
| `05-VERIFICACION-SPAN-ESXI.md` | Evidencia de las capturas ESXi y comprobacion SSH del comparador |
| `06-PREPARACION-CAPTURA.md` | Captura sin IP aplicada; reinicio pendiente de verificar |
| `06-configurar-captura.sh` | Configuracion persistente de la interfaz de captura |
| `07-RECEPCION-Y-RELOJES.md` | Medicion RX/drops y bloqueo por desfase horario |
| `07-activar-promisc.sh` | Activacion persistente de promiscuo en el comparador; ejecutado |
| `08-probar-ntp.py` | Diagnostico NTP sin cambios en el reloj |
| `09-INSTALACION-SURICATA.md` | Bundle offline verificado, simulacion y procedimiento de instalacion |
| `10-simular-apt-offline.sh` | Simula solo desde la fuente local sin instalar |
| `11-instalar-suricata-offline.sh` | Instalo selectivamente Suricata; servicio detenido |
| `12-REGLAS-ET-OPEN.md` | Instantanea ET Open y decision metodologica del comparador |
| `13-preparar-prueba.py` | Ensambla YAML y reglas de prueba sin sudo |
| `14-aplicar-config-suricata.sh` | Aplico configuracion con respaldo y valido `-T`; ejecutado |
| `15-piloto-pasivo-suricata.sh` | Piloto pasivo de 75 s ejecutado y detenido |
| `16-PILOTO-PASIVO-20261002.md` | Resultado y limites del piloto sin ataques |
| `17-NTP-PROPUESTA.md` | Cambio minimo propuesto para relojes, aun no autorizado |
| `18-inspeccionar-pfsense.php` | Auditoria read-only de pfSense |
| `19-METODO-REPLAY-PCAP.md` | **Método recomendado:** replay offline del mismo PCAP a ambos detectores (resuelve relojes sin tocar pfSense) |
| `20-puntuar-por-ventana.py` | Scorer por ventana (da el tiempo de detección de CyberFlow vía `window_end_utc`) |
| `21-P0-06-ESCENARIOS-ATAQUE.md` | Familias de ataque con intensidad justificada (MITRE + estándar + línea base) |
| `22-correr-piloto.py` | Runner del piloto: PCAP → Suricata `-r` + CyberFlow offline → fila comparativa |
| `23-RESULTADO-PILOTO-E3-DNS.md` | **Resultado P0-09 (E3-dns-01):** tabla comparativa + causa del fallo DNS (doblado del espejo) |
| `24-LINEA-BASE.md` | **Línea base** (pps/bps/tamaño + rangos normales): justifica umbrales; valida FPR del fix DNS |
| `25-RESULTADOS-BATERIA.md` | Tabla comparativa E3+E4+E1 (N=1) + hallazgos de método (reloj, doblado del espejo) |
| `26-BATERIA-N3-RESULTADOS.md` | **Batería N=3 por familia** (automatizada): CyberFlow 3/3, Suricata 0/9, con intervalos |

## Alcance actual

El P0 compara deteccion. Las capturas confirman que Sensor1 y la VM comparadora
comparten el host ESXi `172.17.25.2` y el grupo `PG-CYBERFLOW-SPAN`. La ruta
prevista reutiliza el destino SPAN existente; no requiere otro puerto fisico ni
otra VLAN. El comparador recibe tramas sin `tcpdump` gracias a PROMISC persistente.

**Giro metodológico (2026-10-02):** la medición pasa a **replay offline de PCAP**
(nota `19`). El mismo PCAP se corre por Suricata (`-r`) y CyberFlow offline; el
tiempo sale del paquete → input idéntico, reproducible y **sin NTP/pfSense**. P0-05
deja de ser bloqueante. Tooling listo: `20-` (scorer) y `22-` (runner). Pendiente:
firmar P0-01, medir la línea base (`‹BASE_*›` de `21-`) y correr el primer piloto
(`22-`) con un PCAP real en Sensor1.

Fecha de apertura: 2026-10-01.
