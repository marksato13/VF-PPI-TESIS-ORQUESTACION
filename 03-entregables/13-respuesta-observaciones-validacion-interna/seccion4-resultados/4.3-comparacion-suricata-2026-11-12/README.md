# Sección 4.3 — CyberFlow frente a Suricata (paquete de evidencia)

Paquete de evidencia de la comparación **descriptiva** entre CyberFlow híbrido con α = 0,01 (`HIB_0.01`) y Suricata 7.0.3 con ET Open, sobre las capturas existentes de la **cuarta corrida de la Campaña A** (9-nov-2026, modo sombra). No contiene tráfico nuevo: el replay de Suricata se ejecutó offline el 11-nov-2026 con el protocolo fijado de antemano. Rama `seccion-4-3-suricata`, base `f8cef33a470b983cdb93115b6c63543572fd1472` (`main`). La redacción del artículo es aparte.

- **Tabla 9 final:** [`TABLA-9.md`](TABLA-9.md)
- **Resultados por episodio:** [`resultados/resultados-por-episodio.csv`](resultados/resultados-por-episodio.csv) (diccionario de campos en [`resultados/DICCIONARIO-CAMPOS.md`](resultados/DICCIONARIO-CAMPOS.md))
- **Control legítimo:** [`resultados/resultados-control.json`](resultados/resultados-control.json) y [`resultados/control-unidades-entidad-ventana.csv`](resultados/control-unidades-entidad-ventana.csv)

## 1. Resultado en una tabla (detalle y notas en `TABLA-9.md`)

| Lectura | Criterio | Resultado (21 elegibles) |
|---|---|---|
| CyberFlow `HIB_0.01`, tiempo de datos | primera ventana de 10 s con señal atribuible que cierra ≤ `t_fin` | **21/21** |
| CyberFlow `HIB_0.01`, disponibilidad (`s50`) | señal escrita antes de `t_fin` | **20/21** (`escaneo_breve-r4`: señal escrita a +7,75 s; fin a +4,68 s) |
| Suricata, regla fijada | ≥ 1 alerta válida durante el episodio (sin `SURICATA STREAM *` ni `ET INFO *`) | **15/21** (10 por el evento de decodificación SID 2221010, 5 por firmas ET Open) |
| Suricata, solo firmas ET Open | además se descartan los eventos con prefijo `SURICATA` (lectura complementaria; descrita antes del replay) | **5/21** (los cinco escaneos sostenidos, SID 2010937 y otras cuatro firmas `ET SCAN`) |
| Control legítimo de 30 min | unidades entidad–ventana marcadas (de 2.218) | `HIB_0.01` **54 (2,43 %)**; Suricata **79 (3,56 %)**; `HIB_0.03` (sensibilidad) 200 (9,02 %) |

**Qué no permite concluir.** La rejilla de 10 s de CyberFlow impide ordenar a los dos sistemas por tiempo (las diferencias observadas son < 10 s); DNS y escaneo breve no tienen alerta válida de Suricata y no son comparables en tiempo; el control se reporta como *proporción de unidades marcadas* (no hay etiquetas por unidad que permitan llamarla tasa de falsos positivos).

## 2. Alcance y criterios

- **Población:** 21 de los 25 episodios de la Campaña A: 5 DNS, 5 inundación, 5 fuerza bruta, 5 escaneo sostenido y 1 escaneo breve (`r4`). Criterio de elegibilidad (fijado antes de comparar): los 12 requisitos de integridad «verificado» + fuente completa (clase C0). **Excluidos:** `escaneo_breve-r1`, `-r2`, `-r3`, `-r5`; único requisito ausente, `cobertura_durante` (0 anclas esperadas en un barrido de ~5 s). No se sustituyeron ni entran en recuentos. Respaldo: `integridad.json` → `episodios[<id>].resumen.ausente`, y `analisis-3b.json` → `episodios.<id>.en_poblacion_principal` (en `campana-2026-10-26-deteccion-respuesta/etapa4-4c-s50-v2-2026-11-10/evidencia/analisis-v2/`, ya versionado en `main`). Lista: `protocolo/episodios-elegibles.csv`.
- **Control legítimo:** 21:23:00–21:53:00 Z del 9-nov, 6 perfiles de clientes a factor 1,0, sin ataques ni sondas (`control-declarado.json`). Población de CyberFlow: **2.218 pares únicos entidad–ventana, 19 entidades, 181 ventanas de 10 s** (`manifiestos/control-extracto-sensor1.txt`, filas `R`, tomadas de `motor_decision.log`). **Los 79 pares marcados por Suricata pertenecen todos a ese conjunto (0 fuera)**, con ambos `HOME_NET` (`resultados/control-unidades-entidad-ventana.csv`, columnas `suricata_*_marcado`). Cada alerta se asignó al iniciador de su flujo (`flow_id` → `src_ip` del evento `flow`) y a la ventana de 10 s que la contiene; se deduplicó por par (184 alertas → 79 pares). No se contaron 129 alertas del bastión (fuera de la población de CyberFlow) ni 12 fuera del intervalo; se excluyeron 1.177 `ET INFO` y 310 `SURICATA STREAM`.
- **Regla de alerta válida (fijada antes del replay):** `protocolo/PROTOCOLO-REPLAY-4.3.md` §2. Tipo `alert`; excluidas `SURICATA STREAM *` y `ET INFO *`; tiempo del paquete en [`t_inicio`, `t_fin` + 60 s]; par Kali–destino en cualquier sentido; puerto del servicio generado (cualquier TCP en escaneos). Detección = ≥ 1 alerta durante el episodio.
- **SID 2221010** (`SURICATA HTTP unable to match response to request`): evento de decodificación, no firma de amenaza. Conteos **filtrados** por el intervalo anterior: inundación 4.149 (3.171 durante + 978 posteriores), fuerza bruta 877 (655 + 222) (`resultados/resultados-por-episodio.csv`, columnas `suri_P_2221010_*`; `resultados/alertas-validas-episodios.csv`). Su relación con la duplicación del espejo es una **hipótesis** no verificada.
- **Corrección de α:** el protocolo se fijó con α = 0,03 tomado de un manuscrito desactualizado; la decisión vigente (10-nov-2026) es **α = 0,01, umbral −0,6223889502095352** (como en la Campaña B). Se registró el 11-nov-2026 en `protocolo/CORRECCION-ALFA-2026-11-11.md` sin editar el protocolo: `HIB_0.01` es principal, `IF_0.01` y `HEUR` son componentes y `HIB_0.03` es sensibilidad. La nota declara que no se había visto ningún resultado comparativo cuando llegó el cambio.

## 3. Configuraciones y hashes

| Elemento | Valor |
|---|---|
| CyberFlow | modelo `if_limpio_2026_10` (joblib sha256 `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60`); manifiesto `b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7`; heurísticos `VERSION_UMBRALES 2026-11-02.1` (`5d30ffe6a8156c07954f39752e175becb7bfa0fd21a6119e1e6537b2a1217f68`); motor `ec78ca5` |
| Umbrales IF (`score_samples <`) | α = 0,01: −0,6223889502095352 (principal) · α = 0,03: −0,5898535710336618 (sensibilidad) |
| Suricata | 7.0.3 RELEASE, comparador (`suricata-comparator`), sin sudo y sin arrancar el servicio |
| Reglas ET Open | `suricata.rules` sha256 `7b674459975dd56af2d03363b27df4ad6ff53e724e3c04ff65913701ddd5f4e9` (53.012 `alert` + 1 `drop` = 53.013 cargadas, 0 fallidas); instantánea del 2-oct-2026; tarball `et-open-20261002.tar.gz` `3facf0eaed30caf56d2eba43d96ccd2b79dcc851c8d6be4c822e67b4120a7355` |
| `HOME_NET` principal | `[10.10.10.0/24,10.10.30.0/24]` (incluye DC1 10.10.10.20 y la DMZ); `suricata.yaml` copia con **una línea** cambiada, sha256 `8dc620e3bbd73a904a5a5444e07224c53a4f1d64d479db1a7c1ae67b3fc78346` |
| `HOME_NET` original (sensibilidad) | `[10.10.30.0/24]`; `suricata.yaml` sha256 `d0ea918591040108586e43fb30e51c3583f6d61f6ed1acd8dff938150b303650` |
| Protocolo | `protocolo/PROTOCOLO-REPLAY-4.3.md` sha256 `829853b179e9bc7e132c5fd9b1789d772fea8a8e3385fbe1df150e69c291a42d` (sin editar); `FIJADO.txt` registra la hora de fijado (2026-11-11T20:31:18Z) y los hashes |
| Marcas del generador | `marcas.jsonl` sha256 `5fd72ab9da47eb7fddc498debec1f4affcdb127e3636c339663d362d3e3fe1c1` |
| Decisiones del motor | `motor_decision.log` sha256 `733d7a0cab66ef1a6358c80cc2285a6d0da8693722c11a018c5dfb49bb9267cd` |
| PCAP | 1.634 hashes por fichero en `protocolo/pcap-lista-fija.csv` (22 rebanadas: 21 episodios + control); hash de cada rebanada unida y de cada `eve.json` en `manifiestos/trazabilidad-rebanadas.csv` |

Más referencias a los originales (rutas en los hosts y hashes): `manifiestos/REFERENCIAS-ORIGINALES.md`.

## 4. Contenido

| Ruta | Contenido |
|---|---|
| `TABLA-9.md` | Tabla 9 (cobertura y tiempos), detalle por episodio, escaneos sostenidos, notas y control |
| `resultados/` | `resultados-por-episodio.csv` (21 filas, con criterio y campos de respaldo), `alertas-validas-episodios.csv` (alertas que cuentan, ambas configuraciones), `control-unidades-entidad-ventana.csv` (2.218 filas), `resultados-control.json`, `resultados-por-episodio-detalle.json` y `RESULTADOS-TABLAS-analizar_replay.md` (salidas originales del análisis), `DICCIONARIO-CAMPOS.md` |
| `protocolo/` | Protocolo original, corrección de α, `FIJADO.txt`, lista de episodios y de PCAP con hashes, inventario de la Campaña A, creación del YAML principal |
| `manifiestos/` | Trazabilidad por rebanada, `control-extracto-sensor1.txt`, referencias a originales, resumen del respaldo local |
| `analisis/` | `reconstruir_tablas.py` (a partir de lo publicado), `analizar_replay.py`, `trazabilidad_y_detalle.py`, `preparar_lista.py` (con rutas por variable de entorno) |

## 5. Cómo reconstruir las tablas

**Nivel 1 — solo con lo publicado (sin PCAP ni extractos).** Requiere Python 3.10 o posterior (biblioteca estándar):

```
python analisis/reconstruir_tablas.py resultados
```

Imprime los Paneles A y B, las coincidencias (lecturas A–D) y el control, desde `resultados-por-episodio.csv` y `control-unidades-entidad-ventana.csv`, y **falla** si no reproduce 21/21, 20/21, 15/21, 5/21, 54/79/200 unidades y los 2.218 pares únicos en 181 ventanas.

**Nivel 2 — rehacer el análisis desde las alertas extraídas.** `analisis/analizar_replay.py` y `trazabilidad_y_detalle.py` leen una carpeta de trabajo (variable `CF43_DIR`, por omisión la actual) con: `episodios-elegibles.csv` y `lista-slices.txt` (los 21 `episodio_id` y `control_30min`, uno por línea), `control-extracto-sensor1.txt` y `episodios-campana-A-4c.csv` (publicados), `extractos/{principal,s1}/<rebanada>/{alertas.jsonl,hashes.txt,rc.txt,suricata.log,resumen-eve.json}` y `extractos/<rebanada>.{estado,log}` (**no publicados**: 165 MB, mayoría `SURICATA STREAM`), y `analisis-3b.json` (variable `CF43_ANALISIS3B`; versionado en `main`). Se probó el 11-nov-2026 con una copia de trabajo: `resultados-por-episodio-detalle.json`, `resultados-control.json`, `RESULTADOS-TABLAS-analizar_replay.md`, `trazabilidad-rebanadas.csv`, `pcap-lista-fija.csv` y `episodios-elegibles.csv` salieron **idénticos byte a byte** a los publicados. `preparar_lista.py` requiere además `CF43_ANALISIS_V2` (carpeta `evidencia/analisis-v2` del repositorio, con los manifiestos de PCAP). Aviso: `trazabilidad_y_detalle.py` imprime conteos de SID 2221010 **sin filtro de intervalo** (5.839 y 1.472); no deben citarse, los valores correctos son los de la sección 2.

**Nivel 3 — reproducción completa (replay).** Requiere, además: los 1.583 PCAP originales del Sensor1 (`~/cf-e4/4c-A-completa-20261110T0951Z/archivo-pcap/`, verificables contra `protocolo/pcap-lista-fija.csv`), `motor_decision.log`, `marcas.jsonl`, `ciclos.jsonl` y `SHA256SUMS` de esa corrida (`.../copias/`), los `eve.json.gz` completos de cada ejecución (comparador, `~/cf-4.3/out/<config>/<rebanada>/`, con sus hashes en `manifiestos/trazabilidad-rebanadas.csv`), las reglas ET Open y los dos YAML con los hashes de la sección 3, y Suricata 7.0.3. Comando por rebanada: `suricata -r <rebanada.pcap> -c <yaml> -S <suricata.rules> -l <salida> -k none --runmode single --set unix-command.enabled=no`; la rebanada une, sin reordenar, los ficheros de su lista en orden de nombre. **Estos registros no se publican** (PCAP, EVE completos y registros internos); están en el equipo de trabajo del autor con copia de respaldo y verificación de hashes (`manifiestos/RESPALDO-LOCAL.md`), y los originales siguen en el Sensor1 y en el comparador.

## 6. Qué se verificó antes de publicar
- Cifras de Tabla 9 recalculadas contra los registros originales (`analisis-3b.json`, `marcas.jsonl`, `ciclos.jsonl`, `motor_decision.log` y las alertas extraídas): 21/21, 20/21, 15/21, 5/21; 7,75 s de `escaneo_breve-r4`; primer SID válido y marcas de los cinco escaneos sostenidos; 79 de 79 pares dentro del conjunto de 2.218; conteos filtrados del SID 2221010.
- 22/22 rebanadas con hashes de ficheros verificados antes de unirlas, 53.013 reglas cargadas y 0 fallidas, rc 0 con ambos `HOME_NET`.
- Reproducción de los scripts publicados (nivel 2) y de `reconstruir_tablas.py` (nivel 1), y revisión de credenciales y rutas personales (sección 9).

## 7. Límites y pendientes
- Comparación descriptiva: una corrida, 21 episodios, modo sombra, sin significancia estadística. La Campaña A también aportó a la elección de α = 0,01.
- Suricata procesó los PCAP **crudos** (con la duplicación del espejo); no se evaluó la sensibilidad con PCAP deduplicado. Los tiempos de Suricata son del paquete en un replay offline.
- La causa del SID 2221010 y la diferencia del 0,03–0,23 % entre los paquetes leídos por Suricata y los de `tcpdump` **no están explicadas**.
- Las firmas ET SCAN de los escaneos sostenidos son por puerto; su instante depende de cuándo `nmap` probó el puerto, y no se puede verificar el instante del primer paquete real frente a la marca de inicio del generador.
- Escaneo breve: n = 1 elegible y 4 excluidos por integridad. ET Open es una instantánea del 2-oct-2026.
- El análisis interno preliminar `RESULTADOS-4.3.md` **no se publica**: contenía conteos del SID 2221010 sin filtro de intervalo (5.839 y 1.472), sustituidos por los valores de este paquete.
- Pendiente fuera de este paquete: actualizar en el manuscrito las referencias al α seleccionado (§3.3.5 y las demás listadas en `protocolo/CORRECCION-ALFA-2026-11-11.md`).

## 8. Antecedente separado: Nikto (fuera de la Tabla 9 y de sus totales)
Episodio de control con firma del 6-oct-2026 (N = 1; modelo anterior `if_recalibrado_2026_09`): según las notas `02-metodologia/comparacion-cyberflow-suricata/27-EPISODIO-NIKTO.md` y `28-RESULTADO-NIKTO.md` (ya en `main`), Suricata con ET Open dio 590 alertas de 34 firmas con la primera a 3,4 s y CyberFlow 12,0 s. **Solo se conservan esas notas**: no se localizó el PCAP ni el EVE (la nota 27 planifica `-maxtime 120s` y la 28 registra `75s`). Tampoco entran la batería N=3 del 5-oct ni la pasada del 23-oct, que son antecedentes con otros PCAP.

## 9. Privacidad
No se publican PCAP, `eve.json` completos, `motor_decision.log` ni credenciales. Los archivos publicados contienen direcciones IP privadas del laboratorio, puertos, firmas, puntuaciones del modelo y marcas de tiempo. Los documentos de `protocolo/` se conservan **byte a byte** (para no alterar sus hashes) y pueden citar rutas de trabajo del equipo del autor (línea 71) y el nombre de la cuenta de servicio del comparador (línea 40: un nombre de usuario, no una credencial); los scripts de `analisis/` no llevan rutas personales (usan variables de entorno).
