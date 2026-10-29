# Campaña A (detección, modo sombra) — ejecución del 2026-10-29

**Resultado principal.** Se ejecutaron los 25 episodios previstos y el control normal, sin fallos del generador, de la
captura ni del archivador. Con los criterios preregistrados, **ningún episodio es evaluable** (0/25). La causa es una
sola y está medida: durante la batería el motor espació sus ciclos más allá de la tolerancia de continuidad de 20 s
(huecos de hasta 43 s), y la cobertura exige registro continuo del motor. No se ha cambiado ningún criterio para
recuperar episodios. Por tanto la Tabla 8 queda sin recuentos de detección (n/a), y esta campaña **no aporta
evidencia comparativa de detección entre configuraciones ni entre α**. Sí aporta tasas de falsa alarma del control
normal sobre 2526 ventanas con cobertura completa.

Todas las horas son UTC (Perú = UTC−5).

## 1. Qué se ejecutó

| Fase | Intervalo | Estado |
|---|---|---|
| Control normal (sin ataques) | 08:01:00 – 08:35:00 | completo; declarado en `evidencia/otros-hosts/control-A.txt` |
| Batería de 25 episodios | 08:35:10 – 10:33:07 | `campana_fin: completa`; 25 inicios y 25 fines, todos `completo`, rc 0, stderr vacío |
| Espera de ventanas pendientes | 10:33:26 – 10:39:26 | 360 s |
| Parada del archivador | 10:39:35 – 10:39:54 | `FIN OK: vistos=816 archivados=816, sin fallos`; 0 FALLO, 0 PERDIDO |
| Medición de descartes de tcpdump | 10:56 – 10:58 | SIGUSR1 al PID 1393 (lo ejecutó Mark con sudo) |
| Recálculo de las 28 características | 10:42 – ~11:30 | 684 de 689 decisiones reproducidas exactas |

Comando del generador (Kali): `python3 -u /home/adminatacante/cf-campana-A/scripts/generar_campana.py --config
/home/adminatacante/cf-campana-A/escenarios/escenarios.json --salida-dir /home/adminatacante/cf-campana-A-corrida-20261029
--autorizado`. No se usó ninguna opción que omita escenarios. No hubo intentos fallidos que conservar: ningún
episodio terminó en estado distinto de `completo`.

**Configuración congelada.** Motor 7b275b8 (PID 2277062, sin `--enforce`, arrancado 2026-10-28 08:44:50, 0 reinicios).
Umbral desplegado −0,5693969936322356, sin cambios. Los 8 artefactos (motor, modelo IF, manifiesto/escalador,
heurísticos, esquema de 28 características, extractor, publicador del feed y archivador) tienen el mismo SHA-256 al
inicio y al final (`evidencia/estado-inicial/hashes.txt`, `evidencia/estado-final/hashes.txt`). Umbrales derivados α
0,05 / 0,03 / 0,01 = −0,5694578968203694 / −0,5898535710336618 / −0,6223889502095352. Procedencia **verificada** contra
`4.1-modelos/calibracion-alfa-2026-10-24` por igualdad exacta de float, con el orden respetado. `config-campana.json`
sha256 `1642ba31…`, idéntico al del repositorio.

## 2. Por qué no hay episodios evaluables

`scripts/huecos_ciclo_motor.py` → `tablas/huecos-ciclo-motor.csv`:

| Tramo | Huecos entre ciclos | p50 | p90 | p99 | máx | > 20 s |
|---|---|---|---|---|---|---|
| 07:00–08:00 (previo) | 293 | 9,6 s | 19,5 s | 19,9 s | 19,9 s | 0 |
| Control 08:01–08:35 | 152 | 10,2 s | 20,0 s | 22,0 s | 22,6 s | 13 |
| Batería 08:35–10:33 | 386 | 15,6 s | 23,6 s | 42,4 s | 43,0 s | 131 |
| 10:33–10:39 (posterior) | 22 | 18,6 s | 20,9 s | 23,0 s | 23,0 s | 6 |

- **Episodios rechazados por cobertura:** 22 de 25. El hueco máximo dentro del intervalo [inicio, fin+60] va de
  20,4 s a 41,2 s. En las cinco inundaciones HTTP es de 39,8 s a 41,2 s, es decir, un ciclo completo perdido. En
  todos los episodios se observaron las anclas de la Kali esperadas y la evidencia de destino cubre el episodio.
- **Episodios con cobertura «durante» suficiente pero integridad no apta:** dns_inusual-r5, dns_inusual-r2 y
  escaneo_breve-r3. Les falta cobertura previa (mínimo 120 s) o posterior (mínimo 90 s), por huecos del motor en el
  entorno del episodio.
- **Integridad (12 requisitos):** 8 están verificados en los 25 episodios: pcap, eve, decisiones, características,
  sin faltantes, captura sin errores, reinicios y relojes. Los fallos se concentran en los 4 requisitos de cobertura
  y continuidad, todos derivados del mismo hueco del motor:

  | Requisito | Episodios que lo cumplen |
  |---|---|
  | cobertura previa | 2/25 |
  | cobertura durante | 3/25 |
  | cobertura posterior | 5/25 |
  | continuidad | 3/25 |

No se ha determinado la causa del alargamiento de los ciclos. Por coincidir con la carga de la batería, el candidato
evidente es el coste de procesar más tráfico por ciclo, pero no se ha medido. Queda abierto como hallazgo operativo
del motor.

## 3. Tablas (sección 4.2)

Todas las tablas están en `tablas/`, generadas por `scripts/resumir_campana.py`; el resumen legible está en
`tablas/TABLAS-4.2.md`. Las siete configuraciones son clasificaciones comparativas derivadas sobre las mismas
ventanas, no siete detectores desplegados simultáneamente. Solo el IF con el umbral desplegado y los heurísticos
emiten en vivo.

### 3.1 Tabla 8 propuesta

| Escenario | Realizados | Evaluables | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 | HIB 0,03 | HIB 0,01 |
|---|---|---|---|---|---|---|---|---|---|
| Escaneo sostenido | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Inundación HTTP | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| DNS inusual | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Escaneo breve | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Fuerza bruta HTTP | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| **Total** | **25** | **0** | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

«n/a» significa que no hay población evaluable. No equivale a 0 detecciones ni a falsos negativos.

### 3.2 Complementaria: episodios no evaluables (descriptiva, fuera de la Tabla 8)

Lo que sigue describe qué clasificaron las configuraciones en episodios que **no superan** los criterios. No es una
tasa de detección, no se combina con la Tabla 8 y no se mezcla con las 84 ventanas de ataque de la evaluación
anterior. Detalle completo en `tablas/complementaria-tardias-no-evaluables.csv` y
`tablas/episodios-no-evaluables.csv`.

**Episodios no evaluables con detección confirmada durante la actividad:**

| Configuración | Episodios (de 25) | Escaneo sostenido | Inundación HTTP | DNS inusual | Escaneo breve | Fuerza bruta HTTP |
|---|---|---|---|---|---|---|
| IF 0,05 | 17 | 5 | 5 | 2 | 0 | 5 |
| IF 0,03 | 17 | 5 | 5 | 2 | 0 | 5 |
| IF 0,01 | 17 | 5 | 5 | 2 | 0 | 5 |
| HEUR | 20 | 5 | 5 | 5 | 0 | 5 |
| HIB 0,05 | 20 | 5 | 5 | 5 | 0 | 5 |
| HIB 0,03 | 20 | 5 | 5 | 5 | 0 | 5 |
| HIB 0,01 | 20 | 5 | 5 | 5 | 0 | 5 |

**Escaneo breve (~18 s de actividad):** en los 5 episodios solo hubo señales posteriores al fin del comando, entre
28,5 s y 58,4 s después del inicio. Ninguna configuración tiene una señal «durante», así que figuran como señal
tardía, no como detección. No se ha ampliado el intervalo de ataque.

### 3.3 Falsas alarmas del control normal

| Configuración | Falsas alarmas | Ventanas | Tasa |
|---|---|---|---|
| IF 0,05 | 355 | 2526 | 0,1405 |
| IF 0,03 | 231 | 2526 | 0,0914 |
| IF 0,01 | 85 | 2526 | 0,0337 |
| HEUR | 75 | 2526 | 0,0297 |
| HIB 0,05 | 423 | 2526 | 0,1675 |
| HIB 0,03 | 304 | 2526 | 0,1203 |
| HIB 0,01 | 160 | 2526 | 0,0633 |

- **Población:** window_end en [08:01:00, 08:35:00], ambos extremos incluidos.
- **Ventanas:** 2526 evaluadas y 0 ventanas no evaluadas en el intervalo. Hay 66 decisiones escritas después de
  08:35, pero sus ventanas pertenecen al control y por eso cuentan.
- **Cobertura:** 1,0 entre las ventanas registradas. No hay un inventario independiente de ventanas esperadas.
- **Huecos del motor en el control:** hubo 13 huecos de más de 20 s. Las ventanas que esos ciclos no llegaron a
  escribir no están en el denominador, y no se han convertido en TN.

**Exclusiones.** Las cadenas de exclusión del analizador llevan sufijo, por lo que la exclusión por IP desnuda
NUNCA_BLOQUEAR no filtra nada. Se informa por entidad en `tablas/control-por-entidad.csv`:

- Los 75 falsos positivos de HEUR salen todos de 10.10.10.20, el servidor DNS del laboratorio, que está en
  NUNCA_BLOQUEAR. Con el agente activo no habría bloqueo, pero la clasificación sí cuenta.
- En el IF, la mayor parte de los falsos positivos se concentra en 10.10.20.22 (167 con α 0,05) y 10.10.20.24 (114).

### 3.4 Compartidas y exclusivas IF / HEUR por α

**Población evaluable:** vacía para los tres α, a nivel de episodio y de ventana. La tabla queda sin valores; véase
`tablas/compartidas-exclusivas.csv`.

**Descriptivo sobre los 25 episodios no evaluables, detección durante la actividad.** Los resultados son iguales con
α 0,05, 0,03 y 0,01:

| Clasificación | Episodios |
|---|---|
| Ambas (IF y HEUR) | 17 |
| Solo IF | 0 |
| Solo HEUR | 3 (dns_inusual-r3, -r2, -r4) |
| Ninguna | 5 (los cinco escaneos breves) |

### 3.5 Tiempos (`tablas/tiempos.csv`)

Ningún episodio es evaluable, así que no hay latencias válidas para la Tabla 8. Como descripción, en los episodios no
evaluables:

- **Tiempo desde el inicio del generador hasta la primera decisión ALERT del IF desplegado:** entre 26,4 s y 46,0 s.
- **Disponibilidad del registro de las configuraciones derivadas:** misma escala. Es el `logged_at` de la decisión,
  no la latencia de emisión de esa configuración.

**Límites:**
- Con pasos de 10 s y ciclos de hasta 43 s, la resolución temporal es del orden del ciclo.
- Los tiempos están condicionados por los mismos huecos que invalidan la cobertura.

### 3.6 Comparación descriptiva de α

- **Detección:** no hay comparación posible porque no hay población evaluable. En los episodios no evaluables los
  tres α del IF clasifican exactamente los mismos episodios. HIB es igual para los tres α porque HEUR ya cubre esos
  episodios.
- **Falsas alarmas del control:** bajan de forma monótona con α. El IF pasa de 0,1405 (α 0,05) a 0,0914 (α 0,03) y
  a 0,0337 (α 0,01), y el híbrido de 0,1675 a 0,1203 y a 0,0633.

No se declara que α 0,01 gane. Esta campaña solo informa del lado de las falsas alarmas, y sin población de ataque
evaluable no puede sostener la elección de α. Si se usara para elegirlo, habría que declararlo explícitamente y
reconocer que la elección se apoyaría solo en las falsas alarmas.

No se calculan ROC-AUC ni AP: `metricas_por_ventana` no se generó, por falta de `--etiquetas`. En ningún caso se
atribuirían al híbrido las del IF.

## 4. Integridad de la captura y alcance de las mediciones

- **Archivador:** 816/816 ficheros PCAP, sin FALLO ni PERDIDO. El SHA-256 de cada fichero del periodo coincide con
  el registrado al archivarlo (`pcap-manifiesto.json` por episodio).
- **tcpdump** (PID 1393): `0 packets dropped by kernel`, contador acumulado del proceso desde 2026-10-21 19:09:39.
  Lectura a las 10:57:49: 114 571 707 paquetes capturados y 114 571 987 recibidos por el filtro; la diferencia son
  paquetes en búfer pendientes de escritura. Fuente: `evidencia/analisis-final/descartes-tcpdump*.{json,txt}`.
- **Suricata:** `kernel_drops` = 0 en las 1678 mediciones desde las 07:00, con alcance EVE.
- **Alcance de los descartes:** solo los del socket de captura del sensor. No se mide la pérdida aguas arriba (switch
  o SPAN). La continuidad de ficheros por sí sola no se ha usado como prueba de ausencia de pérdidas.
- **NIC rx_dropped:** 7 829 969, contador acumulado desde el arranque. Es tráfico promiscuo u otherhost, no pérdida
  de captura, y no se usa como medida.
- **Relojes** (p34, 10:39): sensor +3,2 ms, Kali −22,9 ms, srv-dmz +4,2 ms, clientes +2,3 ms. Todos con NTP y
  |desfase| ≤ 1 s.
- **Recálculo de características** desde los PCAP: 684 de 689 decisiones atribuidas a la Kali se reproducen exactas
  (pk10 y score). Las 5 que no coinciden están en el borde de un ciclo (`evidencia/analisis-final/caracteristicas.jsonl`):

  | Episodio | Ventana | Diferencia |
  |---|---|---|
  | dns_inusual-r3 | 08:47:50 | score no recalculable (pk10 0 frente a 20) |
  | fuerza_bruta_http-r5 | 09:27:10 | pk10 1921 frente a 7296 |
  | fuerza_bruta_http-r4 | 09:51:50 | pk10 5321 frente a 7104; el score sí coincide |
  | fuerza_bruta_http-r4 | 09:52:00 | score no recalculable (pk10 0 frente a 20) |
  | escaneo_breve-r4 | 10:04:30 | sin recálculo |

  Se conservan tal cual.

## 5. Actividad observada (registro de episodios)

`tablas/registro-episodios.csv`:

| Escenario | Actividad por episodio | Paquetes de la Kali hacia el destino (PCAP) |
|---|---|---|
| Escaneo sostenido | 65,7–66,2 s y unos 65 573 SYN | — |
| Inundación HTTP | 13 868–14 118 peticiones | ~97–99 k |
| DNS inusual | 207–209 consultas | igual al número de consultas |
| Escaneo breve | 17,6–18,0 s y 2010–2013 SYN | — |
| Fuerza bruta HTTP | 6031–6206 intentos | — |

En la fuerza bruta, los intentos coinciden uno a uno con los 401 que registra el servidor.

## 6. Estado final de equipos y procesos (11:35)

- **Sensor:**

  | Servicio | Estado | PID | Reinicios |
  |---|---|---|---|
  | ppi-motor | active, sin `--enforce` | 2277062 | 0 |
  | ppi-motor-capture | active | 1393 | 0 |
  | suricata | active | — | 0 |
  | ppi-publicar-feed.timer | active | — | — |

  Sin sesiones tmux de la campaña (archivador y recálculo terminados). 17 GB libres.
- **srv-dmz:** ppi-enforce-agent.service inactive y ppi-enforce-agent.timer inactive/disabled, es decir, **modo
  sombra conservado**. Sets nft `cyberflow_bloqueados` y `cyberflow_limitados` con 0 elementos.
- **Kali:** sin generador ni procesos de ataque.
- **Bastión:** bucles de vigilancia y de relojes detenidos.

No se reactivó el agente, no se ejecutó la campaña B ni el prompt 3, no se modificó el Word y no se reentrenó nada.

## 7. Qué quedó incompleto

- **Tabla 8 sin población evaluable.** No se puede repetir la batería con el motor actual y esperar otro resultado
  sin entender antes el alargamiento de ciclos. Corregirlo o reprogramar es una decisión de Mark.
- **Análisis de sensibilidad no preregistrado.** Consistiría, por ejemplo, en la tolerancia de continuidad igual al
  ciclo observado. No se ha hecho. Si se hace, debe presentarse aparte y etiquetado como tal, sin sustituir a la
  Tabla 8.
- **Exclusión NUNCA_BLOQUEAR del analizador:** no filtra IP desnudas. Se ha informado, no se ha corregido.
- **ROC-AUC y AP:** no calculados, por falta de etiquetas por ventana.

## 8. Evidencias

**En el repositorio** (`ejecucion-2026-10-29/`):
- `analisis/analisis.json` y `TABLA8.md`: salida de `analizar.py`, ejecutado en el laptop, que es donde se verifica
  la procedencia. Su campo `fuente.archivo` apunta a una copia temporal de trabajo; el log versionado es
  `evidencia/fuentes/motor_decision.log.gz`, con el mismo sha256 `2660a254…`.
- `tablas/`: todas las tablas anteriores.
- `evidencia/analisis-final/`: marcas, destinos, actividad, características recalculadas, respaldos por episodio,
  integridad, stats de Suricata, descartes de tcpdump y relojes.
- `evidencia/estado-inicial/` y `evidencia/estado-final/`: hashes, argv del motor, servicios, feed y anillo.
- `evidencia/otros-hosts/`: copias de Kali, srv-dmz y bastión, sin los .tar.
- `evidencia/archivo-pcap/archivar.log`: manifiesto de los 816 PCAP con su sha256.
- `MANIFIESTO-EJECUCION.sha256`: SHA-256 de todos los ficheros de esta carpeta.

**Solo en el sensor**, por volumen: `/home/m4rk/cf-campana-A-20261029/`

| Contenido | Tamaño | Integridad |
|---|---|---|
| PCAP (`archivo-pcap/`) | 1,2 GB | sha256 en `archivar.log` |
| `fuentes/eve.json` | 641 MB | sha256 `54e1882f…` en `fuentes/SHA256SUMS` |

**Scripts usados** (`scripts/`):

| Script | Papel |
|---|---|
| `analizar.py` | sin cambios, sha256 `5e96ef20…` |
| `extraer_evidencia_destino.py` | nuevo |
| `recalcular_caracteristicas.py` | nuevo |
| `generar_respaldos.py` | nuevo |
| `verificar_integridad.py` | sin cambios |
| `resumir_campana.py` | nuevo |
| `huecos_ciclo_motor.py` | nuevo |

`resumir_campana.py` escribe «n/a» en la Tabla 8 cuando no hay evaluables. Las tablas se regeneraron con esa versión.
La copia del sensor es la anterior, y solo difiere en ese punto.
