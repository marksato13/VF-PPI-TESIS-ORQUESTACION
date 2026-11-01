# Paso 3A — preparación final y congelación del protocolo de la campaña A repetida

**Fecha:** 2026-11-01, de 05:23 a 05:48 UTC.

**Alcance:** se prepara y se congela, sin ejecutar nada.

**Qué no se hizo:**

- ataques, control normal, los 25 episodios ni la campaña B;
- cambios en el Word, el modelo, el escalador, las características, la historia, los umbrales o los heurísticos;
- reactivar respuestas, recalibrar, cambiar relojes ni programar el inicio;
- tocar la primera campaña A.

## Conclusión

**3A pendiente.** Las correcciones pedidas sobre e0ba9e0 están hechas y probadas (sección 11). Queda un único
impedimento verificable: la comprobación global de logrotate (sección 3), que requiere el sudo con contraseña de Mark.
El guion v2 ya está en el sensor; falta su ejecución y su registro.

| # | Impedimento | Quién | Cómo se cierra |
|---|---|---|---|
| 1 | `sudo logrotate -d /etc/logrotate.conf`: no hay rc ni salida completa (a las 06:45Z no existe ningún `mark-04-logrotate-global-*.log` en el sensor) | Mark | Ejecutar `mark/04_logrotate_global.sh` v2 (sección 3). Se cierra **solo** si el registro dice `rc_logrotate=0` y `lineas_error=0` (código de salida 0). |

**Condiciones, que no son impedimentos y están en el protocolo:**

- `ppi-brute-lab` está activo pero **no habilitado** al arranque: se comprueba antes del primer episodio de fuerza bruta;
- el estado de escalada de la Kali (`bloqueos: 3`) solo afecta a las **propuestas** de respuesta en sombra, no a la detección.

## 1. Estado y directorio exclusivo

**Directorios exclusivos:**

- sensor: `/home/m4rk/cf-paso3a-20261101T0523Z/`;
- Kali: `/home/adminatacante/cf-paso3a-plan-sin-trafico-20261101T0523Z/`;
- repositorio: esta carpeta.

**Estado al empezar (05:24Z):**

| Elemento | Estado |
|---|---|
| `ppi-motor` | active, NRestarts = 0, PID 1289322 |
| `--enforce` | ausente en la unidad y en argv |
| argv del motor | idéntico al del paso 2 |
| Hashes de la implementación | coinciden con el paso 2 (`REFERENCIAS-Y-HASHES.md`) |
| Arranque | umbral −0.5693969936322356, historia 230 s, paso 10 s, procesamiento incremental, 0 trazas |
| Suricata | `HTTP_PORTS "[80,18081]"`; kernel_drops acumulados 3017 sobre 15,7 M paquetes |
| ens37 | rx_dropped 1 691 504 (significado no determinado; véase el paso 2) |
| srv-dmz | agente de enforcement inactive/disabled, sin tabla `inet cyberflow`, web HTTP/HTTPS activa, ufw inactivo |
| Kali | sin procesos de carga |
| Clientes | seis perfiles con la curva horaria normal, sin envoltorio vivo |

**Estado al terminar (05:47Z, `evidencia/salidas/out_s10_estado_final.txt`):**

| Elemento | Estado |
|---|---|
| Motor | mismo PID, NRestarts = 0, sin `--enforce`, mismos hashes, 0 trazas desde las 05:20Z; último ciclo hace 10 s (0,07 s, 1 pendiente) |
| srv-dmz | agente inactive/disabled; sin tabla nft; `ppi-brute-lab` active/**disabled**; web activa |
| Kali | sin carga ni generador |
| Clientes | target activo, 6 perfiles normales, sin envoltorio |
| DNS / web desde el bastión | `x.lab-ppi` → 10.10.30.10; HTTP 200; HTTPS 200; `/auth` sin credencial → 401 |

## 2. ppi-brute-lab (18081/auth)

**Estado previo y restauración:**

- estaba inactive/disabled desde el 29-oct 22:55;
- `app.py` (7e43aecb…) y la unidad (23e27a0b…) son idénticos a los versionados en `scripts/endpoint_brute/`;
- se arrancó con `sudo systemctl start ppi-brute-lab` a las 05:26:20Z (rc = 0);
- escucha en 0.0.0.0:18081;
- **no** se habilitó al arranque.

**Reversión:** `sudo systemctl stop ppi-brute-lab`.

**Prueba única desde la Kali (`b11`).** Sin bucles. Agente de usuario `cf-preparacion-paso3a-20261101T0523Z`. La
credencial de control se lee de la unidad y viaja por stdin, sin imprimirse ni guardarse.

| Hora UTC | Petición | Código | `brute.log` |
|---|---|---|---|
| 05:27:00.976 | sin credencial | 401 | user=- |
| 05:27:01.001 | credencial ficticia | 401 | user=fake |
| 05:27:01.028 | credencial de control | 200 | user=control |
| 05:27:01.045 | `/no-existe` | 404 | user=- |
| 05:27:01.081 | sin credencial | 401 | user=- |

El primer intento (`b10`) no llegó a enviar peticiones por un fallo al leer stdin. No dejó tráfico.

**Telemetría:**

- **Suricata:** 10 eventos `http`, cada petición dos veces (VLAN 20 y VLAN 30), con los estados correctos (`eve-http-preparacion.jsonl`).
- **Extracción:** `recalcular_caracteristicas.py`, sin cambios, reproduce los 3/3 scores.
  - La ventana 05:27:10 tiene `http_auth_failure_ratio_60s` = 0,6 y `http_error_ratio_60s` = 0,8.
  - `http_request_rate_60s` = 0,1667, el doble por la duplicación de VLAN en el extractor congelado. Es una observación y no se corrige.
  - Score −0.5928, por debajo del umbral desplegado: es una alerta de **preparación** y queda fuera de todo análisis.
- El SSH de administración bastión → Kali genera paquetes de la entidad Kali. Por eso el protocolo limita el SSH durante la campaña y el analizador exige actividad hacia el destino del episodio.

**HTTP/HTTPS y DNS `lab-ppi`:** se comprobaron desde el bastión al empezar y al terminar.

**Observación ajena al 3A:**

- la credencial de control del endpoint de laboratorio ya estaba escrita en claro en `scripts/endpoint_brute/` (unidad y valor por defecto de `app.py`), versionada desde antes;
- no se repite aquí ni se ha cambiado;
- conviene decidir si se sustituye por un marcador.

## 3. Respaldo de logrotate y validez global

**Respaldo — verificado.** Mark ejecutó el guion 03 (05:05:21Z). En `/var/backups/cyberflow-paso2-20261101T0254Z`
(root:root 700, ficheros 644), los hashes coinciden con los esperados (`REFERENCIAS-Y-HASHES.md`).
`/etc/logrotate.d/cyberflow` vigente: 183e7bc4…, sin los ficheros redundantes.

**Validez global — pendiente.**

- `sudo -n logrotate -d` da rc = 1 sin contraseña: no está en las reglas NOPASSWD del sensor.
- El guion `mark/04_logrotate_global.sh` es de solo lectura: `-d` es el modo depuración y no rota nada.
- **v1 (e0ba9e0) tenía un defecto:** terminaba con `tail`, así que su código de salida era el de `tail` y no el de
  logrotate. Se conserva como `mark/04_logrotate_global.v1.sh` (af99e727…) y no debe usarse.
- **v2 (sha256 5481d99b…, en el sensor desde las 06:28Z):**
  - guarda la salida completa en `mark/mark-04-logrotate-global-<UTC>.salida` y el registro en `…-<UTC>.log`, con marca de tiempo y sin sobrescribir ejecuciones anteriores;
  - el registro incluye el sha256 de `/etc/logrotate.conf` y de cada fichero de `/etc/logrotate.d/`, el rc real de `sudo logrotate -d` (`rc_logrotate`), las líneas `error:` y las `warning:`;
  - código de salida del guion, que `ssh` propaga: **0** = rc 0 y ninguna línea de error; **1** = rc ≠ 0 o hay errores; **2** = no se pudo ejecutar (sudo rechazado o logrotate ausente);
  - los warnings se informan, pero no cierran ni bloquean por sí solos;
  - probado en local con `sudo` y `logrotate` simulados: los cuatro casos (rc 0 limpio, rc 0 con `error:`, rc 1, sudo rechazado) dan 0/1/1/2.

`[BASTIÓN gadmin]` → lo ejecuta Mark (sudo con contraseña; `sudo -n logrotate` no está permitido sin ella):

```
ssh -t sensor1 'bash ~/cf-paso3a-20261101T0523Z/mark/04_logrotate_global.sh'; echo "rc_ssh=$?"
```

**Criterio de cierre:** `rc_ssh=0` y, en el registro, `## rc_logrotate=0`, `## lineas_error=0` y
`## RESULTADO: OK`. Cualquier otro resultado deja el 3A pendiente.

## 4. Excepciones de respuesta frente a exclusiones de población

**El problema.**

- `analizar.py` usaba `NUNCA_BLOQUEAR`, con cadenas anotadas como «10.10.10.20 (DNS/AD)», como conjunto de exclusión del control.
- Ninguna coincidía con `entity_ip`, así que **no se excluía a nadie**, en silencio.
- Además mezclaba dos conceptos distintos.

**La corrección.**

- **`scripts/poblacion.py`, nuevo:**
  - `excepciones_respuesta` (no restringir; la entidad sigue en la población y sus señales cuentan);
  - `exclusiones_poblacion` (fuera del denominador, cada una con justificación obligatoria);
  - las IP deben ser direcciones o CIDR estrictos; una entrada mal formada, anotada o sin justificación aborta;
  - declarar los dos formatos a la vez también aborta.
- **Formato anterior:** se convierte de forma explícita. Todo pasa a excepciones y las exclusiones quedan vacías, que es exactamente lo que se hacía de hecho: **los conteos no cambian**.
  - 222 comprobaciones de `test_herramientas.py` OK.
  - `regresion_alfa.py`: 0 diferencias.
  - Control de la primera A re-analizado: 2526 ventanas e idénticas falsas alarmas en las 7 configuraciones.
- **`config-campana-3b.json`:**
  - el DNS 10.10.10.20 es una **excepción de respuesta** y sigue en la población;
  - `exclusiones_poblacion` está vacía;
  - el motor ya excluye en origen (`--excluir`) el bastión, el sensor y la VLAN 60.
- **Lo que no cambia:** el publicador sigue con su lista. La lista anterior se conserva solo como documento.

## 5. Cobertura y puntualidad

Definidas en `analizar_3b.py` y en el protocolo (sección 5):

- inventario de ventanas esperadas, a partir de la repetición offline con el mismo motor, con bordes historia + 230 s y cierre − 120 s;
- disponibilidad = `registro_escrito_en` del ciclo;
- tardía si llega más de 60 s después de `window_end`;
- seis estados de ventana;
- un ciclo sin decisiones o un hueco > 20 s se informa, pero **no es pérdida**;
- el alcance del replay está declarado;
- población común para las 7 configuraciones;
- **sin umbral automático de cobertura**: el control se publica con su cobertura y con cotas;
- la falta de datos no es FN, ni TN, ni latencia 0.

**Re-análisis del paso 2** (`reanalisis-paso2/analisis/`, identificado como tal):

| Medida | Valor |
|---|---|
| Ventanas esperadas / decididas | 4058 / 4058 (0 ausentes, 0 solo en vivo) |
| A tiempo / tardías | 3942 / 116 (retraso p50 16,4 s, p95 32,7 s, máx. 240 s) |
| Ciclos | 389, de ellos 109 sin decisiones; varios huecos de ~20 s entre escrituras, todos sin pérdida contra el inventario |
| Control (03:23:50–03:50:50) | 2043 ventanas con cobertura total 1,0 |

## 6. Detección durante el ataque

**Requisitos de una señal que cuenta:**

- señal atribuible: destino del episodio y `paquetes_en_intervalo_ataque` > 0;
- actividad del ataque en los datos;
- disponibilidad ≤ fin para que sea `oportuna`.

**Categorías:**

- `oportuna`;
- `solo_posterior`;
- `ausencia_con_observacion_suficiente`;
- `no_evaluable`.

Las 7 configuraciones derivadas se publican aparte de las emisiones reales.

**Comprobación con el paso 2.** En los tres episodios:

- 15 ventanas esperadas;
- **10** con `window_end` en [inicio, fin + 10], de las que **6** estaban disponibles antes del fin;
- 6 emisiones oportunas;
- primera a los 28,66 / 34,45 / 37,21 s, igual que en el informe del paso 2.

Ningún episodio entra en la población principal:

- T1 tiene la integridad desconocida (el paso 2 no generó `integridad.json`);
- T2 y T3 tienen la fuente degradada (91 y 68 descartes de Suricata en [inicio − 60, fin + 60]).

Aun así, sus detecciones son visibles: la regla funciona como se pretende.

## 7. Calidad de fuentes

`scripts/calidad_fuentes.py`, nuevo, separa:

- el archivo (continuidad de los PCAP);
- el socket de tcpdump (no medible por intervalo: incertidumbre declarada);
- Suricata (`kernel_drops` > 0 → `degradada`);
- la interfaz ens37 (se informa sin clasificar).

**Criterio:** solo una fuente `completa` entra en la población principal. No se afirma ausencia de efecto por
coincidir con el replay.

## 8. Escenarios, configuraciones y plan sin tráfico

- **Escenarios:** 5 × 5. Hashes iguales en la Kali y en el repositorio.
- **Plan efectivo sin tráfico** (`plan-sin-trafico/`):
  - `generar_campana.py` **sin** `--autorizado`, en un directorio separado de la Kali;
  - rc = 0, 25 episodios simulados, el **mismo orden** que la primera A (semilla 20261026);
  - sin procesos de carga antes ni después;
  - marcas separadas de las de cualquier campaña.
- **Umbrales:** los tres verificados por igualdad exacta contra la calibración (sha256 26bfc6e6…), con la ruta relativa ajustada a esta carpeta. El desplegado es distinto y se mantiene.
- **Envoltorio de factor 1,0:**
  - hash 69d79937…, el mismo del paso 2;
  - comprobado sin arrancarlo: `clientes_lab.py` tiene la guarda `__main__` y llama a `factor_horario` como global del módulo;
  - el parche devuelve 1,0 (el original daba 0,036 a esa hora);
  - no hay ningún envoltorio vivo.
- **Escaneo breve:** dura ~18 s y no se prolonga. Se declara de antemano que sus detecciones serán probablemente solo posteriores.

## 9. Feed y escalada

**Copias con hash:** al empezar en `estado-inicial/` y a las 05:44:14Z en `escalada/`.

**Efecto sobre el 3B:**

- el motor **no** lee `estado.json`; solo `publicar_feed.py` (cada 10 s) y `escalada.py`;
- por tanto **afecta a la respuesta, no a la detección**;
- con el feed actual: 0 entradas.

**Estado de la Kali:** `bloqueos: 3`, último visto a las 05:29:30Z, por la alerta de preparación. Son **propuestas
en sombra**: el agente está desactivado y no hay tabla nft.

**Decaimiento:**

- 24 h desde `ultimo_visto`, que se renueva con cualquier propuesta;
- no se impone una espera de 24 h, porque no reiniciaría el contador si la Kali vuelve a aparecer.

**Campaña B:** su estado inicial se define en su preparación. Plan: copia con hash y, si procede, restablecimiento
documentado y autorizado. Nada se restablece en silencio.

## 10. Pruebas

`tests/test_analizar_3b.py`: **90 comprobaciones OK** tras la corrección (eran 57 en e0ba9e0; sección 11), con datos sintéticos. Cubren:

- detección:
  - señal oportuna y posterior;
  - ventana que solapa el final;
  - señal no atribuible: otro destino, sin actividad en el intervalo, actividad solo antes del inicio, formato «a»;
- estado de las ventanas:
  - ventana tardía, ausente y no evaluada;
  - ciclo sin decisiones y hueco > 20 s;
  - disponibilidad por ciclo;
- observación:
  - detección con observación parcial;
  - fuente degradada;
  - integridad desconocida;
  - sin calidad de fuentes;
- población y control:
  - excepciones y población: el DNS dentro; exclusión justificada; IP anotada, inválida o no estricta; dos formatos;
  - cotas del control y desglose por entidad;
- la separación entre las 7 configuraciones y las emisiones;
- una ejecución completa por la línea de comandos.

Además, `test_herramientas.py` (222 OK) y `regresion_alfa.py` (0 diferencias) siguen pasando.

**Re-análisis de la primera campaña A** (`reanalisis-campana-A-2026-10-29/`, marcado como re-análisis):

- 25/25 episodios `no_evaluable`;
- motivos: no hay inventario, no hay calidad de fuentes, los destinos son de formato «a» y la integridad no es apta;
- el control es idéntico al histórico;
- **la Tabla 8 publicada no se sustituye.**

## 11. Corrección del 3A sobre e0ba9e0 (2026-11-01, 06:00–06:50Z)

Sin ejecutar ataques, controles ni episodios; sin tocar el motor, el modelo, el escalador, las características, los
heurísticos, los escenarios ni sus parámetros; sin recalibrar. Se conservan los 3 α y las 7 configuraciones. Todo
sigue en sombra.

| # | Problema en e0ba9e0 | Corrección | Prueba | Resultado |
|---|---|---|---|---|
| 1 | `ventanas_esperadas_episodio()` tomaba las ventanas **del inventario** y solo comprobaba `fin + 60 ≤ hasta + 60`: un inventario truncado devolvía menos ventanas y el episodio salía con observación completa. Reproducido: un inventario cortado dejaba 10 de 15 ventanas y se aceptaba como completo. | Las ventanas del episodio son **todas** las anclas de la rejilla de 10 s en (inicio, fin + 60), abierto en ambos extremos, con independencia de lo que haya en el inventario. Se exige que el rango del inventario las contenga todas; si no, motivo «el inventario no cubre X/N ventanas requeridas» y salida `cobertura_inventario`. | `test_regresion_inventario_truncado`; `test_limites_temporales_rejilla` (hasta = T0+150 cubre y T0+149,9 no; desde = T0+10 cubre y T0+10,1 no; inicio y fin + 60 sobre la rejilla quedan fuera) | OK; con el analizador de e0ba9e0 estas pruebas fallan |
| 2 | Una ventana `ventana_no_evaluada` en la **referencia** se quitaba de las esperadas: si tampoco se evaluaba en vivo, desaparecía del denominador. Reproducido: 14 de 15 ventanas y observación completa. | Requeridas = claves con decisión **o** no evaluadas en la referencia. Por ventana se informa `estado_referencia` (decision / no_evaluada / sin_registro / sin_inventario) junto al estado en vivo (decidida / no evaluada / ausente). El resumen global da `requeridas`, `decididas_en_vivo`, `cobertura_total` y el desglose de las no evaluadas en la referencia; `solo_en_vivo` queda fuera del denominador. El **control** separa el tramo cubierto por el inventario (requeridas, cotas sobre ellas) de los tramos sin inventario (cobertura «no determinable») y dice si está parcialmente cubierto. | `test_regresion_no_evaluada_en_ambas_versiones` (también ausente en ambas; no evaluada en la referencia pero decidida en vivo = completa); `test_control_parcialmente_cubierto_y_no_evaluadas` | OK; fallan con e0ba9e0 |
| 3 | El cierre del archivo no estaba definido: sin mínimo tras el último episodio, sin marcas de los extremos y sin requisito para el inicio del control. | Protocolo, sección 3 bis, y `config → protocolo_3b.cierre_archivo`: cierre ≥ `fin_ultimo + 60 + 120 = fin_ultimo + 180 s`, prolongado hasta verificar cinco condiciones (PCAP `OK` que cubra, sin `FALLO`, EVE posterior, decisiones en vivo hasta `fin_ultimo + 60`, replay con rc = 0 que cubra). Marcas `inicio_archivo`, `fin_ultimo` y `cierre_archivo` con su fuente. Control: `desde ≥ inicio_archivo + 230`. Los 90 + 120 s entre episodios no son un cierre. | Aplicado a la evidencia del paso 2: inicio 02:44:54Z; control 03:23:50Z ≥ 02:48:44Z; fin último 04:04:22Z; cierre 04:18:31Z, 669 s por encima del mínimo; `archivar.log` sin fallos (374/374) | Cumple |
| 4 | `config-campana-3b.json` describía en `codigo` el motor por lotes de la primera A y mantenía la precondición de enforcement activo; el estado operativo del 3B era ambiguo. | Versión `3b-2026-11-01.2`: `codigo` = motor incremental `24f8a80` con blob y sha256 de cada fichero desplegado, y las dos excepciones as-deployed (`publicar_feed.py`, `escalada.py` de `f57ca00`/6d92ff3); lo anterior pasa a `codigo_historico_primera_A` y `campanas.historico_primera_A`, marcado HISTÓRICO. Nuevo `estado_operativo_3b`: sombra durante, verificación previa, escalada sin restablecer, se termina en sombra y la activación de la respuesta pertenece a la preparación del B. Protocolo, secciones 1, 3 y 8, unificado. | Guion s11 en el sensor (blobs desplegados) + s11b en local (comparación con 24f8a80, f57ca00 y 6d92ff3) | 6 ficheros iguales a 24f8a80; el esquema, igual salvo CRLF; publicador y escalada, de f57ca00 = 6d92ff3 |
| 5 | `mark/04` v1 devolvía el rc de `tail`, no el de logrotate, y sobrescribía su registro. | v2 (sección 3): rc real, registro con marca de tiempo, criterio rc = 0 y ninguna línea `error:`. | Prueba local con sudo y logrotate simulados (4 casos) | Guion OK; **ejecución pendiente de Mark** |
| 6 | — | Re-análisis del paso 2 y de la primera A con el analizador corregido, en carpetas nuevas (`reanalisis-paso2/analisis-corregido/`, `reanalisis-campana-A-2026-10-29/corregido/`), sin sobrescribir los anteriores. | 90 comprobaciones en `test_analizar_3b.py` (eran 57; dos aserciones anteriores se adaptaron a las claves renombradas, con la misma semántica); 222 en `test_herramientas.py`; `regresion_alfa.py` con 0 diferencias | OK |

**Re-análisis del paso 2 con el analizador corregido** (`reanalisis-paso2/analisis-corregido/`; mismas entradas que
`analisis/`: motor.log f344dfa0…, replay.log e43f2ce2…, rango 03:20:00–04:18:15Z, control 03:23:50–03:50:50Z):

| Medida | Antes (`analisis/`) | Ahora (`analisis-corregido/`) |
|---|---|---|
| **Cobertura:** ventanas por episodio | 15 «esperadas» (del inventario) | 15 **requeridas** (rejilla); el inventario cubre las 15 en los tres episodios |
| Inventario global | 4058 esperadas / 4058 decididas | 4058 requeridas / 4058 decididas; 0 no evaluadas en la referencia; 0 solo en vivo |
| Puntualidad | 3942 a tiempo / 116 tardías | igual |
| Control | 2043 ventanas, cobertura 1,0 | tramo cubierto = todo el control (2043 requeridas, 2043 decididas, cotas mín = máx); 0 tramos sin inventario; mismas falsas alarmas en las 7 configuraciones |
| **Calidad de fuentes** | T1 completa; T2 y T3 degradadas (91 y 68 descartes) | igual: **no** se convierten en completas |
| Integridad | desconocida en los tres | igual |
| Población principal | 0 de 3 | 0 de 3 (motivos: T1 integridad; T2 y T3 fuente e integridad) |
| **Oportunidad** | 7/7 configuraciones `oportuna` en los tres; 6 emisiones oportunas a 28,66 / 34,45 / 37,21 s | igual |

**Por qué no cambian los números.** En el paso 2 el inventario cubría de sobra los tres episodios (el último terminó a
las 04:04:22 y el inventario llega a 04:16:15) y no había ninguna ventana no evaluada en la referencia. Los dos
defectos solo se manifiestan con un inventario truncado o con no evaluadas en la referencia, que es justo lo que
cubren las pruebas nuevas. Las diferencias son de estructura: `ventanas_requeridas`, `cobertura_inventario` y
`estado_referencia` por ventana, y el control con `tramo_cubierto`, `tramos_sin_inventario` y
`historico_fpr_control`.

**Re-análisis de la primera A** (`reanalisis-campana-A-2026-10-29/corregido/`): igual población (25/25
`no_evaluable`) y misma tabla principal. Cambia la presentación: cada episodio lleva el motivo «sin inventario» y
el control 08:01–08:35 se presenta como **tramo sin inventario, cobertura no determinable** (2526 decididas en vivo,
mismas falsas alarmas), en vez de una cobertura 1,0 que solo se refería a las ventanas registradas.

**Analizador en el sensor:** `~/cf-paso3a-20261101T0523Z/herramientas3b/analizar_3b.py` = 27e67fd1… (compila con
python3); la versión de e0ba9e0 queda como `analizar_3b.e0ba9e0.py` (bdd44729…).

## Contenido de esta carpeta

| Ruta | Qué es |
|---|---|
| `PROTOCOLO-CAMPANA-A-REPETIDA.md` | Protocolo congelado |
| `config-campana-3b.json` | Configuración del 3B |
| `REFERENCIAS-Y-HASHES.md` | Commits y sha256 congelados |
| `plan-sin-trafico/` | Simulación del generador en la Kali |
| `reanalisis-paso2/` | Destinos 3b, calidad de fuentes y análisis 3B de la evidencia del paso 2 (`analisis/` con e0ba9e0; `analisis-corregido/` con la corrección) |
| `reanalisis-campana-A-2026-10-29/` | Re-análisis de la primera A (raíz con e0ba9e0; `corregido/` con la corrección) |
| `evidencia/sensor/` | Estado inicial, preparación de auth, escalada y guion `mark/04` |
| `evidencia/guiones/` | Guiones ejecutados (s01–s11, s11b, b10, b11, `04` v2 y `04.v1`, lanzadores; `correccion-3a/` con los scripts que aplicaron la corrección) |
| `evidencia/salidas/` | Sus salidas |
| `MANIFIESTO.sha256` | sha256 de todo lo anterior |

**Código en `../scripts/`:**

- nuevos: `analizar_3b.py`, `poblacion.py` y `calidad_fuentes.py`;
- modificados: `analizar.py` (población) y `extraer_evidencia_destino.py` (`--formato 3b`).

**Pruebas:** `../tests/test_analizar_3b.py`.
