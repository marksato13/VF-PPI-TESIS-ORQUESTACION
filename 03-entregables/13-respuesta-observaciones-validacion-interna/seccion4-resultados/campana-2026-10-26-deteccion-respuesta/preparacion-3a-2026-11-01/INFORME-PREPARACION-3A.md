# Paso 3A — preparación final y congelación del protocolo de la campaña A repetida

**Fecha:** 2026-11-01, de 05:23 a 05:48 UTC.

**Alcance:** se prepara y se congela, sin ejecutar nada.

**Qué no se hizo:**

- ataques, control normal, los 25 episodios ni la campaña B;
- cambios en el Word, el modelo, el escalador, las características, la historia, los umbrales o los heurísticos;
- reactivar respuestas, recalibrar, cambiar relojes ni programar el inicio;
- tocar la primera campaña A.

## Conclusión

**El 3B puede ejecutarse en cuanto se cierre un único impedimento:** la comprobación global de logrotate (punto 3).
Requiere el sudo con contraseña de Mark. El guion ya está en el sensor; lo que falta es su ejecución y su resultado.

| # | Impedimento | Quién | Cómo se cierra |
|---|---|---|---|
| 1 | `sudo logrotate -d /etc/logrotate.conf`: falta el rc y la salida completa | Mark | Ejecutar `mark/04_logrotate_global.sh` (sección 3). Si rc = 0 y no hay líneas de error, queda cerrado. |

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
- Guarda el rc, la salida completa y las líneas de error en `~/cf-paso3a-20261101T0523Z/mark/mark-04-logrotate-global.log`.

`[BASTIÓN gadmin]` → lo ejecuta Mark (sudo con contraseña):

```
ssh -t sensor1 'bash ~/cf-paso3a-20261101T0523Z/mark/04_logrotate_global.sh'
```

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

`tests/test_analizar_3b.py`: **57 comprobaciones OK**, con datos sintéticos. Cubren:

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

## Contenido de esta carpeta

| Ruta | Qué es |
|---|---|
| `PROTOCOLO-CAMPANA-A-REPETIDA.md` | Protocolo congelado |
| `config-campana-3b.json` | Configuración del 3B |
| `REFERENCIAS-Y-HASHES.md` | Commits y sha256 congelados |
| `plan-sin-trafico/` | Simulación del generador en la Kali |
| `reanalisis-paso2/` | Destinos 3b, calidad de fuentes y análisis 3B de la evidencia del paso 2 |
| `reanalisis-campana-A-2026-10-29/` | Re-análisis de la primera A |
| `evidencia/sensor/` | Estado inicial, preparación de auth, escalada y guion `mark/04` |
| `evidencia/guiones/` | Guiones ejecutados (s01–s10, b10, b11, 04, lanzadores) |
| `evidencia/salidas/` | Sus salidas |
| `MANIFIESTO.sha256` | sha256 de todo lo anterior |

**Código en `../scripts/`:**

- nuevos: `analizar_3b.py`, `poblacion.py` y `calidad_fuentes.py`;
- modificados: `analizar.py` (población) y `extraer_evidencia_destino.py` (`--formato 3b`).

**Pruebas:** `../tests/test_analizar_3b.py`.
