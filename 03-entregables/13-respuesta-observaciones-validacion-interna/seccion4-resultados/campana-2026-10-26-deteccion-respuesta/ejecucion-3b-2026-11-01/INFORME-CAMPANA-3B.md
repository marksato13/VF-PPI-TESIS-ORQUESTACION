# Campaña A repetida (paso 3B, modo sombra) — ejecución del 2026-11-01

ID de ejecución `20261101T0721Z`. Protocolo congelado en 1b35bf6
(`preparacion-3a-2026-11-01/PROTOCOLO-CAMPANA-A-REPETIDA.md`), configuración `config-campana-3b.json` sha256
`cbf72fbb…`. Todas las horas son UTC (Perú = UTC−5).

## Resultado principal

- **Ejecución y archivo.** Se ejecutaron los 25 episodios y el control normal (33 min), sin fallos del generador,
  del archivador ni de la captura. El archivo PCAP tiene 844/844 ficheros sin fallos y tcpdump registró
  **0 descartes de kernel**.
- **Repetición offline (inventario).** Cubre toda la ejecución: **12 667 ventanas requeridas, 0 ausentes,
  0 no evaluadas y cobertura 1,0**. De ellas, 655 son tardías (> 60 s).
- **Detecciones visibles.** Las emisiones reales del motor (ALERT del IF desplegado y heurísticos) fueron
  **oportunas en 21 de 25 episodios**. Las cuatro excepciones son escaneos breves de unos 18 s, cuya señal llega
  después del fin.
- **Población principal: 1 de 25.** Solo `escaneo_breve-r3` tiene observación completa. Los otros 24 quedan fuera
  por **integridad no apta** (los 24) y, en 9 de ellos, también por **fuente degradada** (descartes de Suricata).
- **Causa dominante de la falta de integridad.** Es el requisito de continuidad del registro del motor:
  hueco ≤ 20 s (`TOL_CONTINUIDAD_S = 2 × paso`). El motor incremental escribe sus decisiones cada ≈ 10 s, pero a
  veces junta dos ventanas en una escritura. Así deja huecos de 20,0 a 23,5 s, que se repiten **en todos los
  tramos**, incluido el previo sin carga (208 huecos > 20 s entre las 03:14 y las 07:32). No es pérdida de datos:
  el inventario no encuentra ninguna ventana ausente. Aun así, el criterio está congelado y **no lo he cambiado**.
  Ver la sección 5.
- **Consecuencia.** La Tabla 8 principal solo tiene recuentos en Escaneo breve (n = 1), y el resto queda en n/a.
  Las detecciones de los 24 episodios fuera de la población se publican con el prefijo «fuera:».
- **Control normal.** Las tasas de falsa alarma tienen cobertura total (2644 / 2644 ventanas requeridas), así que
  sus cotas coinciden: IF α 0,05 = 14,9 %, α 0,03 = 9,6 %, α 0,01 = 3,1 %; HEUR = 3,5 %.
- **α.** Con una población principal de un episodio, **esta campaña no sustenta formalmente la elección de α**.
  Fuera de la población, la detección oportuna casi no cambia entre α y la falsa alarma cae a la quinta parte
  (sección 7). No se elige α en este informe.

## 1. Qué se ejecutó

| Fase | Intervalo (UTC) | Estado | Evidencia |
|---|---|---|---|
| Comprobaciones previas (c00–c05) | 07:21:23 – 07:24:04 | sin discrepancias | `guiones/salidas/out_c0*.txt` |
| Archivador PCAP (s10) | 07:24:32 → 10:36:33 | `FIN OK: vistos=844 archivados=844, sin fallos` | `evidencia/sensor/copias/archivar.log` |
| Clientes a factor 1,0 (k01) | desde 07:26:15 | seis perfiles; 10.10.20.21–26 con ventanas | `guiones/salidas/out_k01_clientes_factor1.txt` |
| Control normal declarado | 07:32:00 – 08:05:00 (33 min) | declarado a las 07:28:02 | `evidencia/sensor/control-declarado.json` |
| Batería de 25 episodios | 08:08:39 – 10:02:05,818 | `campana_fin: completa`; 25 inicios y 25 fines, todos `completo`, rc 0, stderr vacío | `evidencia/kali/` |
| Comprobación de cierre (s20) | 10:05:58 | condiciones 1–4 se cumplen | `guiones/salidas/out_s20_verificar_cierre.txt` |
| Repetición offline (s30) | 10:06:16 – 10:34:50 | rc = 0; 13 187 decisiones; condición 5 cumplida | `evidencia/sensor/replay/` |
| Cierre del archivo (s40) | 10:36:00 – 10:36:39 | archivador rc 0; servicios con NR = 0; 11 hashes OK; sin `--enforce` | `evidencia/sensor/s40.out` |
| Restauración de clientes y del endpoint | 10:36:55 – 10:37:46 | target activo; `ppi-brute-lab` parado (inactive/disabled) | `evidencia/clientes/restaurar.out`, `evidencia/bastion/srv-final.txt` |
| Descartes de tcpdump (Mark, sudo) | 10:51:44 | SIGUSR1 al PID 1375: 0 *dropped by kernel* | `evidencia/sensor/copias/descartes-tcpdump*.{json,txt}` |
| Análisis (s50) | 10:37:46 – 11:25:45 | 7 pasos, todos con rc 0 | `guiones/salidas/out_s50_analisis.txt` |

**Generador (Kali).**

- Comando: `python3 -u /home/adminatacante/cf-campana-A/scripts/generar_campana.py --config
  /home/adminatacante/cf-campana-A/escenarios/escenarios.json --salida-dir
  /home/adminatacante/cf-3b-20261101T0721Z/corrida --autorizado`.
- Los hashes de `generar_campana.py`, `esquema_campana.py` y `escenarios.json` coinciden con los esperados.
- Orden aleatorio del generador; los 25 episodios aparecen en `tablas/episodios-configuraciones.csv`. No se omitió
  ningún escenario y no hubo intentos fallidos que conservar.

**Marcas del archivo** (sección 3 bis del protocolo):

| Marca | Valor | Fuente |
|---|---|---|
| `inicio_archivo` | 07:04:56Z | `live-20261101070456.pcap`, primer `OK` de `archivar.log` (el barrido inicial recogió los PCAP aún presentes en el directorio de captura) |
| `inicio_archivo + 230` | 07:08:46Z | el control empieza a las 07:32:00, así que se cumple |
| `fin_ultimo` | 10:02:05,818Z | `fin` de `escaneo_sostenido-r1` en `marcas.jsonl` |
| `fin_ultimo + 180` | 10:05:05,8Z | |
| `cierre_archivo` | 10:35:53 + 15 s = 10:36:08Z | último `OK` (`live-20261101103553.pcap`); margen de 1862 s sobre el mínimo |

**Rango del inventario (declarado).** La repetición se lanzó con `--desde 07:24:40Z --hasta 10:05:30Z`, porque el
segmento EVE archivado empieza en el byte 220 192 406 (07:24:32, cuando arrancó el archivador). Por eso
`analizar_3b.py` recibió `--inventario-rango "07:24:40Z,10:05:30Z"` en vez de `inicio_archivo,cierre_archivo`, y el
rango efectivo del inventario es **[07:28:30, 10:03:30]**. Es más estricto que el del protocolo
([07:08:46, 10:34:08]), porque la repetición no tiene EVE antes de 07:24:32 ni decisiones después de 10:05:20. Aun
así contiene el control completo y todas las ventanas requeridas de los 25 episodios (`cobertura_inventario.cubre =
true` en los 25; la última requerida es la de 10:03:00). Ningún umbral ni duración cambia por ello.

## 2. Configuración y entorno (sin cambios)

**Motor.**

- Motor 24f8a80 instalado: `ppi-motor` PID 1289322, activo desde 03:14:01, NR = 0, **sin `--enforce`** en argv ni
  en la unidad; argv idéntico al del 3A.
- 11 artefactos (motor, incremental, heurísticos, extractores v2/v3, feed, esquema de 28 características,
  publicador, escalada, modelo IF y manifiesto) con el mismo sha256 al inicio (c01) y al final (s40).
- Umbral desplegado −0,5693969936322356.

**Umbrales α.** Son −0,5694578968203694 / −0,5898535710336618 / −0,6223889502095352 (0,05 / 0,03 / 0,01).

- En el sensor, `analizar_3b.py` marcó su procedencia como `no_verificada` porque allí no está el fichero de
  calibración.
- La comprobé en local contra `4.1-modelos/calibracion-alfa-2026-10-24/umbrales-alfa-precision-completa.json`
  (sha256 `26bfc6e6…`): los tres son iguales como float a `validacion_sin_kali_65553`, y el desplegado es el α 0,05
  de `validacion_original_65633`. Columna `umbral_igual_a_calibracion_sin_kali` de `tablas/comparacion-alfa.csv`.

**Respuesta en sombra.**

- `ppi-agent.timer` inactive/disabled; `nft list tables` sin `inet cyberflow` (rc 0) al inicio, en g01 y al final.
- `estado.json` se copió con hash al inicio (`8902fddd…`) y al final (`600f0c65…`) **sin tocarlo**.
- Las excepciones de procedencia (`publicar_feed` y la escalada de f57ca00) se conservan.

**Población.** `exclusiones_poblacion` está vacía. El DNS 10.10.10.20 queda **dentro** de la población: es una
excepción de respuesta. `poblacion.formato = nuevo`.

**Relojes.** Se midieron tres veces (07:21, 08:05 y 10:05), con |desfase| ≤ 3,3 ms en todos los hosts
(`evidencia/bastion/relojes-3b.log`, `guiones/salidas/out_p10b_relojes.txt`).

**Salud del sensor durante la batería.**

- Motor siempre activo y con NR = 0.
- Ciclos: p50 1,65 s, p95 5,06 s, máximo 10,6 s.
- Memoria disponible: mínimo 4,75 GB en el control y 3,84 GB en la batería (3,43 GB tras ella, durante la
  repetición offline), sin presión de memoria (`psi_mem_some10` = 0).
- Suricata: `kernel_drops` 3017 → 6249 (+3232), concentrados en las inundaciones (sección 6).

## 3. Intervenciones y desviaciones (todas registradas)

1. **Muestreador de recursos.** El primer intento falló: una edición con `sed` dejó la variable `R` sin definir
   («R: unbound variable»). Se corrigió y relanzó con s11 (PID 1615401) antes del control. No afecta al motor ni a
   la captura.
2. **Comprobaciones del endpoint de fuerza bruta** desde el bastión (10.10.10.30, que no es la Kali):
   - **07:24:02, completa:** sin credencial 401, ficticia 401, una de control 200, ruta inexistente 404;
   - **08:05:23, mínima:** 401;
   - **08:49:02, mínima, antes del episodio 10:** 401.

   La credencial de control se leyó a una variable y no se imprimió ni se guardó. Las tres comprobaciones caen
   fuera del control y de los episodios.
3. **Accesos SSH a la Kali.** Fueron cuatro, ninguno durante el control ni durante un episodio:
   - 08:05:38,930: lanzar el generador;
   - 10:05:30,887: comprobar el fin y copiar las marcas;
   - 10:05:44: la copia;
   - 10:37:16: el estado final.

   Están en `evidencia/bastion/accesos-kali.log` y en `evidencia/bastion/g01.out`. La vigilancia del bastión
   durante el control (`vigilancia.log`) no registró accesos a la Kali ni a srv-dmz.
4. **Rango del inventario** limitado por el inicio del EVE archivado (sección 1). Es más estricto que el del
   protocolo.
5. **Salida de s20.** No se guardó en el sensor. Se transcribió del registro de la sesión
   (`guiones/salidas/out_s20_verificar_cierre.txt`); sus condiciones 3 y 4 leen ficheros en vivo y no se pueden
   repetir.
6. **Descartes de tcpdump.** Los midió Mark con sudo (la captura corre como el usuario `tcpdump`). La señal SIGUSR1
   no para ni reinicia la captura: después, PID 1375 y NR = 0. s50 la incorporó porque el fichero ya existía cuando
   generó los respaldos.

No se cambió ningún umbral, regla, duración, criterio ni lista de población.

## 4. Detección por episodio

Las 7 configuraciones son clasificaciones **derivadas** sobre las mismas ventanas, no siete detectores en vivo.
Categorías del protocolo (sección 6): `oportuna` (señal atribuible disponible ≤ fin), `solo_posterior`,
`ausencia_con_observacion_suficiente` y `no_evaluable`.

Tablas completas:

- `tablas/episodios-configuraciones.csv`: una fila por episodio con las 7 categorías, la población, los motivos,
  la calidad de la fuente, los requisitos de integridad no verificados y las ventanas a tiempo o tardías;
- `tablas/senales-por-configuracion.csv`: número de señales y primera disponibilidad;
- `evidencia/sensor/analisis/analisis-3b/TABLA-3B.md`: la tabla original del analizador.

| Escenario (n = 5 c/u) | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 / 0,03 / 0,01 | Emisiones reales oportunas |
|---|---|---|---|---|---|---|
| Escaneo sostenido | 5 op. | 5 op. | 5 op. | 5 op. | 5 op. | 5/5 (1.ª a 22,0–39,6 s) |
| Inundación HTTP | 5 op. | 5 op. | 5 op. | 5 op. | 5 op. | 5/5 (24,2–29,3 s) |
| Fuerza bruta HTTP | 5 op. | 5 op. | 5 op. | 5 op. | 5 op. | 5/5 (18,4–25,1 s) |
| DNS inusual | 2 op., 3 n/e | 2 op., 3 n/e | 2 op., 3 n/e | 5 op. | 5 op. | 5/5 (17,2–25,9 s) |
| Escaneo breve (≈ 18 s) | 1 op., 4 post. | 1 op., 4 post. | 0 op., 2 post., 2 n/e, 1 aus. | 1 op., 4 post. | 1 op., 4 post. | 1/5 (16,4 s) |

(op. = oportuna; post. = solo_posterior; n/e = no_evaluable; aus. = ausencia con observación suficiente)

Estos recuentos incluyen los 24 episodios **fuera** de la población principal. Una detección observada vale aunque
la observación sea incompleta; lo que no se puede afirmar con observación incompleta es una ausencia.

**Escaneos breves.** Duran 17,6–18,0 s. La primera ventana que los contiene se cierra en `inicio + 10…20 s` y se
decide en el ciclo siguiente, así que la primera señal llega a los 26–41 s del inicio, después del fin. Solo en
`escaneo_breve-r1` hay señal antes del fin (16,4 s).

**DNS con IF.**

- IF da señal oportuna en dns_inusual-r1 y r5. En r2, r3 y r4 no da señal atribuible, y como la observación es
  incompleta el resultado es `no_evaluable`, no ausencia.
- El heurístico `dns_entropy` da señal oportuna en los 5. Fue el primer emisor real en 4 de los 5; en dns_inusual-r1
  lo fue el IF.

**Población principal: `escaneo_breve-r3`.** Fuente completa, integridad apta, inventario cubierto y destino para
cada ventana decidida.

- `solo_posterior` en 6 configuraciones (primera señal a 30,7 s con HEUR/HIB y a 40,9 s con IF 0,05/0,03, cuando el
  episodio duró 17,6 s).
- `ausencia_con_observacion_suficiente` con IF 0,01.
- Las emisiones reales fueron 4 atribuibles, 0 oportunas.

**Tabla 8 propuesta.** `tablas/tabla8-propuesta.csv`, también en `tablas/TABLAS-3B.md`.

| Escenario | Realizados | Población principal | IF 0,05 | IF 0,03 | IF 0,01 | HEUR | HIB 0,05 | HIB 0,03 | HIB 0,01 |
|---|---|---|---|---|---|---|---|---|---|
| Escaneo sostenido | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Inundación HTTP | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| DNS inusual | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Escaneo breve | 5 | 1 | 0/1 (1 post.) | 0/1 (1 post.) | 0/1 (aus.) | 0/1 (1 post.) | 0/1 (1 post.) | 0/1 (1 post.) | 0/1 (1 post.) |
| Fuerza bruta HTTP | 5 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

La versión CSV incluye en cada celda el recuento «fuera:» (op./post./n-e) de los episodios excluidos.

## 5. Por qué 24 de 25 episodios no tienen integridad apta

`verificar_integridad.py` exige 12 requisitos «verificado» (`tablas/integridad-requisitos.csv`). Siete se
verifican en los 25 episodios:

- PCAP, EVE, decisiones y características (hash real coincidente);
- sin faltantes (secuencia PCAP sin huecos);
- reinicios (ninguno);
- relojes.

El requisito de captura se verifica en 16: los descartes de tcpdump están medidos (0) en los 25, pero en 9 hay
descartes de Suricata.

Episodios que **no** cumplen cada uno de los otros requisitos:

| Requisito | Episodios que no lo cumplen | Causa medida |
|---|---|---|
| cobertura durante | 22 | `analizar.cobertura()`: motor no continuo en [inicio, fin+60] (hueco del registro de 20,01–21,78 s); todas las anclas de la Kali están observadas en los 25 |
| continuidad | 22 | la misma: hueco del registro > 20 s |
| cobertura previa (≥ 120 s) | 21 | segundos continuos (huecos ≤ 20 s) antes del inicio: se cortan en el primer hueco de 20,x s |
| cobertura posterior (≥ 90 s) | 10 | ídem tras fin+60 |
| captura sin errores relevantes | 9 | Suricata `kernel_drops` > 0 en [inicio−120, fin+90] |

**Diagnóstico de los huecos** (`tablas/ciclos-y-huecos-por-tramo.csv`, con todos los instantes de escritura de
decisiones de `motor_decision.log`):

| Tramo | Ciclo p50 / p95 | Hueco entre escrituras p50 / p95 / máx | Huecos > 20 s |
|---|---|---|---|
| Previo, sin campaña (03:14–07:32) | 0,28 / 2,23 s | 10,0 / 20,1 / 23,5 s | 208 |
| Control normal | 1,17 / 1,87 s | 10,2 / 20,4 / 20,8 s | 21 |
| Batería | 1,65 / 5,06 s | 10,6 / 20,4 / 21,8 s | 79 |
| Cierre | 1,16 / 1,91 s | 10,3 / 20,3 / 21,0 s | 24 |

El motor incremental decide cada ventana de 10 s cuando se cierra. Cuando un cierre cae justo después de un ciclo,
esa ventana y la siguiente se escriben juntas y el hueco entre escrituras es de ≈ 20 s más el jitter. Por eso el p95
ronda 20,1–20,4 s **en todos los tramos**, incluido el previo sin tráfico de campaña.

El inventario confirma que en esos huecos no se pierde ninguna decisión: 0 ausentes en 12 667. El analizador ya lo
advierte: «un hueco > 20 s entre escrituras NO prueba pérdida».

La tolerancia de 20 s procede del motor por lotes de la primera A, cuyo ciclo era la unidad de escritura. Con el
motor incremental queda en el límite de su cadencia normal. El paso 2 y la preparación 3A no lo detectaron porque
su reanálisis no disponía de respaldos de integridad (resultado «integridad desconocida»).

**No he modificado la tolerancia, el criterio ni la población.** Si se quiere evaluar la población con un criterio
de continuidad adaptado al motor incremental (por ejemplo, contra el inventario en vez de contra el hueco de
escritura), es una decisión de protocolo que corresponde a Mark y que tendría que declararse antes de reanalizar.
Los datos para hacerlo están completos y publicados.

## 6. Calidad de fuentes y descartes de Suricata (por separado)

`tablas/calidad-fuentes-suricata.csv`:

- **Archivo PCAP:** continuo y con ambos extremos cubiertos en los 25 episodios. 844 ficheros (1 274 860 299 bytes),
  0 FALLO, 0 PERDIDO.
- **tcpdump:** 0 descartes de kernel en el contador acumulado del proceso. Fueron 26 236 100 paquetes capturados
  desde el 2026-10-30 19:55:21; la medición se tomó a las 10:51:44, después de toda la campaña. No cubre pérdidas
  aguas arriba (switch o SPAN).
- **Suricata** (`capture.kernel_drops`, ±60 s, `calidad_fuentes.py`): 9 episodios **degradados**.

  | Episodio | Descartes (±60 s) | Paquetes (±60 s) |
  |---|---|---|
  | inundacion_http-r3 | 1146 | 497 276 |
  | inundacion_http-r4 | 182 | 482 648 |
  | inundacion_http-r2 | 111 | 500 407 |
  | dns_inusual-r5 | 100 | 120 988 |
  | fuerza_bruta_http-r2 | 97 | 280 189 |
  | fuerza_bruta_http-r3 | 61 | 310 514 |
  | escaneo_breve-r4 | 58 | 83 944 |
  | dns_inusual-r3 | 28 | 110 979 |

  - Hay una discrepancia de ventana en `inundacion_http-r1`: tiene fuente `completa` con ±60 s, pero +11 descartes
    con el periodo de integridad [−120, +90]. Se publican las dos cifras.
  - Fuera de los episodios, el contador pasó de 3017 a 6249 en toda la ejecución.
- **Interfaz ens37:** `rx_dropped` de 1987 a 3060 por episodio. Se publica sin clasificar porque su significado en
  este laboratorio no está determinado.

Una fuente degradada no anula una señal observada (los 9 tienen detecciones visibles), pero impide concluir una
ausencia. Tampoco afirmo que no tuviera efecto porque el motor en vivo coincida con la repetición.

## 7. Control normal (07:32:00 – 08:05:00, dentro del inventario)

**Cobertura y población.**

- Tramo cubierto: **2644 ventanas requeridas, 2644 decididas en vivo, 0 sin decisión y cobertura 1,0**, así que las
  cotas mínima y máxima coinciden con la tasa.
- No hay ventanas no evaluadas ni tramos sin inventario.
- 22 entidades. El DNS 10.10.10.20 está **dentro** de la población.

`tablas/control-falsas-alarmas.csv`:

| Configuración | Falsas alarmas | Decididas | Tasa | Cotas [mín, máx] |
|---|---|---|---|---|
| IF α 0,05 | 395 | 2644 | 14,94 % | [14,94 %, 14,94 %] |
| IF α 0,03 | 254 | 2644 | 9,61 % | [9,61 %, 9,61 %] |
| IF α 0,01 | 83 | 2644 | 3,14 % | [3,14 %, 3,14 %] |
| HEUR | 92 | 2644 | 3,48 % | [3,48 %, 3,48 %] |
| HIB 0,05 | 466 | 2644 | 17,62 % | [17,62 %, 17,62 %] |
| HIB 0,03 | 336 | 2644 | 12,71 % | [12,71 %, 12,71 %] |
| HIB 0,01 | 171 | 2644 | 6,47 % | [6,47 %, 6,47 %] |

**Desglose por entidad** (`tablas/control-por-entidad.csv`).

- Las falsas alarmas del IF se concentran en dos clientes:
  - **10.10.20.22:** 171 / 128 / 50 de 199 ventanas con α 0,05 / 0,03 / 0,01;
  - **10.10.20.24:** 124 / 74 / 9.
- Les siguen 10.10.20.26 (46 / 36 / 23), 10.10.10.20 (DNS: 26 / 10 / 1) y 10.10.20.21 (17 / 4 / 0).
- HEUR: 88 de sus 92 falsas alarmas son del DNS 10.10.10.20 y 4 de 10.10.20.26.
- La Kali tuvo una sola ventana en el control (07:43:20, 2 paquetes, PERMIT).

`tablas/control-informativo-sin-dns.csv` da las tasas sin el DNS **solo como información** (HEUR 0,16 %). No
sustituye a la tabla del protocolo.

**Separación de fuentes.** Este control usa el motor 24f8a80, el tráfico de esta ejecución y el inventario de esta
ejecución. **No se mezcla** con las 84 ventanas de la sección 4.1 ni con el control de la primera A.

## 8. Emisiones reales con latencia

`tablas/emisiones-reales.csv` (por episodio) y `tablas/emisiones-reales-detalle.csv` (cada emisión, con
`window_end`, componente, disponibilidad, `logged_at` y si es oportuna).

- **Qué son.** Las emisiones son las decisiones ALERT del IF desplegado y los heurísticos registrados en vivo.
- **Cómo se miden.** La latencia es la disponibilidad (`registro_escrito_en` del ciclo) menos el inicio del episodio.
- **Resultado.**
  - 21 de 25 episodios tienen al menos una emisión oportuna;
  - la latencia de la primera va de 16,4 s a 39,6 s (mediana 23,9 s);
  - el primer emisor fue el IF desplegado en 17 episodios y `heuristico:dns_entropy` en 4;
  - todas las emisiones fueron atribuibles; ningún episodio tiene emisiones hacia otro destino.
- **Las 4 sin emisión oportuna** son escaneos breves (r2, r3, r4 y r5). Su primera emisión llega entre 26,2 y 39,5 s
  después del inicio (las siguientes, hasta 240 s), cuando el episodio ya terminó.
- **Puntualidad global** (inventario): 12 012 ventanas a tiempo y 655 tardías (> 60 s). El retraso de
  disponibilidad tiene p50 16,0 s, p95 65,7 s y máximo 238,7 s.

## 9. Comparación de los tres α (mismo tráfico)

`tablas/comparacion-alfa.csv`:

| α | Umbral | Población principal (n = 1) | Oportuna, los 25 | solo_posterior | no_evaluable | 1.ª señal oportuna, mediana | Falsa alarma (control, cobertura 1,0) |
|---|---|---|---|---|---|---|---|
| IF 0,05 | −0,56946 | solo_posterior | 18/25 | 4 | 3 | 24,0 s | 14,94 % (395/2644) |
| IF 0,03 | −0,58985 | solo_posterior | 18/25 | 4 | 3 | 24,6 s | 9,61 % (254/2644) |
| IF 0,01 | −0,62239 | ausencia con obs. suficiente | 17/25 | 2 | 5 | 24,9 s | 3,14 % (83/2644) |
| HIB 0,05 | | solo_posterior | 21/25 | 4 | 0 | 23,9 s | 17,62 % |
| HIB 0,03 | | solo_posterior | 21/25 | 4 | 0 | 23,9 s | 12,71 % |
| HIB 0,01 | | solo_posterior | 21/25 | 4 | 0 | 23,9 s | 6,47 % |

**Qué sustentan los datos.**

- **Formalmente, nada.** La población principal tiene un episodio, así que la Tabla 8 no permite comparar α con los
  criterios preregistrados. Esta campaña **no** basta para elegir α definitivamente, y no lo elijo.
- **Descriptivamente** (24 episodios fuera de la población, cuyas detecciones son observaciones reales):
  - pasar de α 0,05 a 0,01 deja la detección oportuna del IF casi igual (18 → 17 de 25). La única pérdida es
    `escaneo_breve-r1`, que pasa a solo_posterior;
  - la falsa alarma del control cae de 14,9 % a 3,1 % (÷ 4,8);
  - en el híbrido, la detección oportuna no cambia (21/25 con los tres α) y la falsa alarma cae de 17,6 % a 6,5 %.
- **Lectura.** Si se confirma con una población evaluable, estos datos favorecen α 0,01. La preferencia del usuario
  por 0,01 no ha intervenido en este análisis.
- **Límites.**
  - Los α no se distinguen en los escenarios largos (todos detectan).
  - La diferencia en detección se juega solo en los escaneos breves. Los tres α fallan en puntualidad en 4 de los
    5, porque la señal llega después del fin.
  - El control es un solo intervalo de 33 min. Sus falsas alarmas dependen sobre todo de dos clientes (sección 7).

## 10. Feed y escalada

- **Feed inicial** (c01): `feed.json` bb9080a0…, `feed.sig` cbfbdc9d…, `estado.json` 8902fddd….
- **Feed final** (s40): `feed.json` 8038c925…, `feed.sig` b0617035…, `estado.json` 600f0c65….
- **Estado del publicador.** El publicador siguió en sombra y actualizó `estado.json` con propuestas, sin aplicar
  ninguna (agente desactivado, sin tabla nft). No se restableció el estado de escalada.
- **Copias.** Están en `evidencia/sensor/estado-inicial/` y `evidencia/sensor/copias/`.

## 11. Estado final

- **Sensor:** ppi-motor, ppi-motor-capture, suricata y ppi-dashboard activos con NR = 0. El motor sigue en sombra.
- **srv-dmz:** `ppi-brute-lab` parado y no habilitado, como antes de la preparación. Sombra intacta. HTTP y HTTPS
  responden 200.
- **Clientes:** `cyberflow-lab.target` restaurado. Los seis perfiles a factor 1,0 terminaron sin acciones fallidas.
- **Kali:** sin carga.
- **Evidencia voluminosa:** queda en el sensor y no se sube a Git (sección 12).

## 12. Evidencia y reproducibilidad

- `COMANDOS.md`: todos los comandos, con la máquina y la cuenta, en orden.
- `MANIFIESTO.sha256`: sha256 de todos los ficheros de esta carpeta, verificado con `sha256sum -c`.
- `evidencia/sensor/SHA256-ORIGINALES-COMPRIMIDOS.txt`: sha256 de los originales de los cuatro registros que se
  suben comprimidos (`.gz`).
- `evidencia/sensor/voluminosos-sha256.txt`: **rutas absolutas en el sensor, bytes y sha256** de los 844 PCAP, del
  segmento EVE (600 954 324 bytes, `b7bf61a2…`) y de `stats-inicio.log`. La lista misma tiene sha256 `6ceab84a…`.
  Los PCAP también tienen su manifiesto por episodio en `evidencia/sensor/analisis/respaldos/*/pcap-manifiesto.json`,
  que coincide con el sha256 registrado por el archivador.
- **Datos reutilizables:**
  - `evidencia/sensor/copias/` (marcas, ciclos, `motor_decision.log.gz`, archivar.log, muestras, feed, journals,
    servicios);
  - `evidencia/sensor/replay/` (inventario);
  - `evidencia/sensor/analisis/` (destinos, calidad, características recalculadas, respaldos, integridad y
    analisis-3b.json);
  - `tablas/`.
- **Herramientas:** `evidencia/sensor/herramientas/` (con los sha256 de `REFERENCIAS-Y-HASHES.md`;
  `evidencia/sensor/analisis/sha256-herramientas.txt`) y `herramientas-informe/resumir_3b.py`, que genera
  `tablas/` sin recalcular nada.
- **Recálculo de las 28 características:** 693 de 702 decisiones de la Kali reproducidas exactas
  (`evidencia/sensor/analisis/recalculo.stdout`).
