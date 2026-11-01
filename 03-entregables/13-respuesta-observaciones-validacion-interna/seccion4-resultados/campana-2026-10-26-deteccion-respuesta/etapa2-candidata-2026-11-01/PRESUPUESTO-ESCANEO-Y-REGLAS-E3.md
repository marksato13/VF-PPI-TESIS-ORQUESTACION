# Presupuesto del escaneo breve, requisitos de reglas y siete configuraciones (Etapa 2, puntos 6, 8 y 9)

**Origen de los datos.** Se reprodujo el tramo 08:40–09:05 del 3B (1-nov) con el motor candidato. Las entradas son las del archivo, no se tocó el laboratorio:

- PCAP archivado;
- `eve-segmento.json`;
- `marcas.jsonl`.

Salidas: `resultados/comparacion-replays-tramo.json`. Herramientas: `herramientas/` (copia de la rama candidata).

**Lo que no se ha hecho.** Todo lo de este documento son mediciones sobre datos archivados y requisitos. **No se ha implementado ninguna regla temprana nueva, ni cambiado umbrales, ni excluido a DC1 de `dns_entropy`.** Esas son decisiones para la Etapa 3.

**Naturaleza de cada dato** (misma convención que `PROTOTIPO-ROTACION-Y-DISPARO.md`):

- **MEDIDO sobre datos archivados:** los SYN por segundo del PCAP (§1), las tasas DNS del EVE (§3), las consultas que DC1 reenvía (§3) y las características y reglas de los replays (§4), que son deterministas para unos datos dados.
- **SIMULADO:** los tiempos de decisión de los replays (reloj simulado con la CPU del portátil), la cadena del banco sin ssh (§1) y las renovaciones del publicador (§4.1).
- **PENDIENTE:** todo lo que exige el Sensor1, el ssh o el 3B completo.

## 1. Presupuesto temporal del escaneo breve (`escaneo_breve-r5`)

**Qué hizo la Kali** (`marcas.jsonl`): `nmap -sT -T4 --max-retries 1 -p 1-1000 10.10.30.10`, de 08:47:26,93 a 08:47:44,92 (18,0 s).

**Qué hay en el cable.** SYN del origen 10.10.20.30 al destino 10.10.30.10 por segundo, contados en el PCAP archivado (`herramientas/rafaga_escaneo.py`). El espejo SPAN duplica: hay unos 2 SYN por puerto.

| Segundo (UTC) | SYN | Puertos distintos | Acumulado |
|---|---|---|---|
| 08:47:27 | 2 | 1 | 2 |
| 08:47:28–39 | 0 | 0 | 2 |
| 08:47:40 | 13 | 12 | 15 |
| 08:47:41 | 207 | 104 | 222 |
| 08:47:42 | 492 | 272 | 714 |
| 08:47:43 | 760 | 432 | 1474 |
| 08:47:44 | 542 | 297 | 2016 |
| 08:47:45 en adelante | 0 | 0 | 2016 |

**El escaneo efectivo dura unos 5 s (08:47:40,0–08:47:44,9), no 18 s.** Los primeros 13 s son la fase previa de nmap: hay un contacto a las 08:47:27 y luego silencio. La duración que importa para el presupuesto es la de la ráfaga, unos 4,9 s.

**Dónde cae en las anclas de 10 s:**

- la ventana que termina a las 08:47:40 no contiene la ráfaga;
- la que termina a las 08:47:50 la contiene entera, y es la primera que dispara `port_scan`;
- el IF solo la marca a α = 0,05 y 0,03 (score −0,613); a α = 0,01 no la marca.

| Replay | Ventana | Decisión tras el fin de ventana | Decisión desde el inicio del episodio | Respecto al fin del escaneo (08:47:44,92) |
|---|---|---|---|---|
| r2: rotación de 15 s, periódico (como hoy) | 08:47:50 | 22,4 s | 45,46 s | +27,5 s |
| r4: rotación de 5 s, por eventos | 08:47:50 | 3,4 s | 26,44 s | +8,5 s |

**Cota inferior con las anclas de 10 s (que se conservan).** El escaneo no puede detectarse antes de que termine:

- la primera ventana que lo contiene acaba a las 08:47:50, 5,1 s después del último SYN;
- aunque la disponibilidad de los datos y el ciclo fueran 0 s, la decisión llegaría después del fin.

El replay r4 se queda a 3,4 s de esa cota: la decisión sale a las 08:47:53,4.

**Cota inferior con una regla temprana sobre PCAP de 5 s** (no implementada; requisito R-E1):

- el fichero que contiene 08:47:40–45 se cierra con el primer paquete posterior a 08:47:45;
- en el replay r4, la espera media entre el cierre y el inicio del ciclo es de 0,69 s (`espera_marca_pcap_s`), y el ciclo dura 1,6 s de mediana;
- una regla que evaluara ese fichero aislado decidiría hacia las 08:47:47,3;
- sumando la cadena medida en el banco (decisión → confirmación nft, p50 1,43 s; `ensayo-cadena-eventos.json`), queda hacia las 08:47:48,7: **unos 3,8 s después del fin del escaneo**;
- en el laboratorio hay que añadir el ssh del relé, que no se ha medido.

**Conclusión del presupuesto.** Con capturas por ficheros (ni siquiera con 5 s) no se puede **cortar este escaneo breve mientras dura**: la ráfaga entera cabe en un fichero de 5 s. Lo alcanzable es:

| Objetivo | Estado |
|---|---|
| Detectarlo (ventana 08:47:50) | Ya se cumple: 5/5 en HEUR |
| Decidir unos 8,5 s después del fin con rotación de 5 s y disparo por eventos | Medido (r4) |
| Restringir antes de la siguiente acción del mismo origen | Requiere la cadena por eventos instalada; el presupuesto es la suma de los tramos medidos en `PROTOTIPO-ROTACION-Y-DISPARO.md` (sección 4) |
| Cortar durante el escaneo | **No alcanzable** con este diseño. Exigiría inspección en línea (por ejemplo, Suricata IPS o un contador nft con `meter`/`limit` en el propio srv-dmz), lo que cambia la arquitectura. No se propone en esta etapa. |

## 2. Requisitos de la regla temprana (R-E1, para la Etapa 3)

| # | Requisito | Base medida |
|---|---|---|
| R-E1.1 | Opera sobre el **último fichero cerrado** (nunca uno abierto) y no sobre ventanas: es una regla aparte de las 28 características, que no cambian. | `test_etapa2_disparo.py` (fichero abierto que no dispara) |
| R-E1.2 | Umbral por origen y destino: SYN sin completar a ≥ *P* puertos distintos en el fichero. En el tramo, el máximo legítimo de `syn_rate_10s` es 1,7/s (10.10.20.26), frente a 1611/s del escaneo; en la ráfaga hay 104–432 puertos distintos por segundo. Un *P* del orden de 50 por fichero de 5 s deja un margen de más de 25× sobre lo legítimo observado, **solo en este tramo**. Hay que validarlo sobre el 3B entero antes de fijarlo. | `comparacion-replays-tramo.json` y caracteristicas r2 |
| R-E1.3 | El espejo duplica los SYN: se cuentan **puertos distintos**, no SYN. | Tabla de la sección 1 |
| R-E1.4 | La acción de la regla temprana es la del port_scan actual: BLOCK en srv-dmz, con el mismo `evento_id` y la misma escalera. No se cambia LIMIT por BLOCK en ningún otro caso. | D3 |
| R-E1.5 | Excepciones: NUNCA_BLOQUEAR y los escáneres autorizados (lista explícita; hoy ninguno en el laboratorio). | — |

## 3. Atribución DNS (R-E2) y tráfico legítimo confundible

**Falsa alarma de DC1.** `dns_entropy` dispara sobre **10.10.10.20 (DC1)** en prácticamente todas las ventanas del tramo, haya o no episodio DNS. Son 24 ventanas fuera de episodios en 25 min (desglose en `siete_configuraciones.HEUR.alarmas_fuera_por_entidad_y_regla`).

Causa observada en el EVE del segmento: DC1 **reenvía** consultas a su reenviador 10.10.10.1 (pfSense):

- 2981 consultas;
- 5784 registros con nombres `*.francos-sac.com`;
- 2912 respuestas NXDOMAIN.

Es decir, el resolvedor hereda la entropía de los nombres que le piden sus clientes. DC1 está en NUNCA_BLOQUEAR (publicador, agente y helper), así que **no se restringiría nunca**. Aun así, es una alarma falsa a nivel de detección, y el IF también lo puntúa cerca del umbral (−0,52 a −0,62).

| # | Requisito |
|---|---|
| R-E2.1 | `dns_entropy` se atribuye al **cliente que pregunta al DC** (destino 10.10.10.20/21, puerto 53), no al DC que reenvía. Las consultas cuyo origen es un DC y cuyo destino es su reenviador no cuentan para la regla. |
| R-E2.2 | DC1 y DC2 siguen **evaluándose** (IF y demás reglas), como pide el encargo para DC2. Solo se excluye su papel de reenviador en `dns_entropy`. |
| R-E2.3 | Hay que medir antes y después sobre el 3B entero: las alarmas `10.10.10.20|dns_entropy` deben bajar a 0 sin perder `dns_inusual` (hoy 5/5). |

**Tasa DNS por origen y valor de N** (`resultados/tasa-dns-por-origen.json`, EVE completo del segmento, de 07:05 a 09:46 aproximadamente):

| Origen | Contexto | Máx. en 1 s | Media máx. en 10 s |
|---|---|---|---|
| 10.10.20.30 | En `dns_inusual` (5 episodios) | 3 | 2,4 (media por episodio 2,29–2,32/s) |
| Clientes legítimos (10.10.20.21–26, 10.10.40.10, 10.10.50.51/52, 10.10.60.x) | Fuera de episodios | **9** (ráfagas puntuales) | **0,9** |

**El N candidato del helper (5/s, ráfaga 10) NO separa.** El escenario va a 2,3 consultas/s, por debajo de 5/s, así que el LIMIT de DNS no lo recortaría. Lo reconozco tal cual.

**Un N que sí separaría por tasa sostenida:** 1,5/s, que en nft es `90/minute`, con ráfaga de 10 paquetes.

- Los legítimos tienen picos de hasta 9 en 1 s (caben en la ráfaga) y no pasan de 0,9/s sostenido en 10 s.
- El escenario sostiene 2,3/s.
- El margen es pequeño: 1,5/s frente a 0,9/s legítimo (×1,7) y frente a 2,3/s del escenario (×1,5).
- Aun así, el LIMIT solo recorta el escenario en torno a un 35 %. **No lo detiene.**

**Decisión pendiente (D-N, de Mark):**

- (a) aceptar que el LIMIT de DNS es una mitigación débil y dejar N en 5/s, que no molesta a nadie y no actúa sobre el escenario;
- (b) bajar a 90/minute con ráfaga 10, que exige repetir el caso C1 del ensayo netns con ese valor;
- (c) tratar `dns_entropy` como señal y no como restricción.

El helper actual sigue con 5/s. **No se ha cambiado.**

## 4. Separación HTTP/escaneo y confusión entre reglas (R-E3)

Reglas que disparan sobre el origen de ensayo en cada episodio (r2; ventanas con fin en (inicio − 10 s, fin + 180 s]):

| Episodio | Regla prevista | Otras reglas que disparan | Ventanas sin score (sin tráfico propio de 10 s) que aún disparan | Última alarma tras el fin |
|---|---|---|---|---|
| escaneo_sostenido-r5 | port_scan (8) | **http_abuse (12)** | port_scan 2, http_abuse 10 | http_abuse +103 s |
| escaneo_breve-r5 | port_scan (3) | — | port_scan 2 | +25 s |
| fuerza_bruta_http-r3 | brute_force (22) | **port_scan (1)** | brute_force 12, port_scan 1 | brute_force **+126 s** |
| fuerza_bruta_http-r5 | brute_force (20) | **port_scan (2)** | brute_force 10, port_scan 2 | +106 s |
| dns_inusual-r5 | dns_entropy (11) | **http_abuse (5)** | 1 y 1 | +16 s |

**Lectura:**

- **Escaneo → http_abuse.** El escaneo sostenido genera registros HTTP suficientes para `http_abuse` (≥ 100 peticiones en 60 s con pocos fallos de autenticación).
  - En la respuesta no cambia nada, porque port_scan (BLOCK) domina sobre http_abuse (LIMIT) en srv-dmz.
  - Pero la clase atribuida es errónea, y la alarma de http_abuse se alarga hasta 103 s después del fin.
- **Fuerza bruta → port_scan.** Con muchas conexiones cortas, la rama «ráfaga» de port_scan (≥ 200 intentos en 30 s con completitud ≤ 0,1) dispara en 1–2 ventanas. Las dos son BLOCK en srv-dmz, así que la acción no cambia.
- **Colas.** Las reglas de 60 s siguen disparando en ventanas **sin tráfico propio** (score `None`) hasta 126 s después del fin. La causa de que la cola pase de 60 s no está demostrada; puede deberse a registros EVE tardíos (http y flow se escriben al cerrar la transacción o el flujo). Su efecto sobre las restricciones se mide en la sección 4.1.
- **Tráfico legítimo confundible observado** (máximos de los clientes legítimos en el tramo, frente al origen de ensayo):
  - `http_request_rate_60s`: 1,95 frente a 133,5 /s;
  - `http_auth_failure_ratio_60s`: 0,20 (10.10.20.21) frente a 1,0;
  - `syn_rate_10s`: 1,7 frente a 1611;
  - `dns_query_rate_60s`: 0,6 frente a 4,57.

  En este tramo hay **dos confusiones reales con tráfico legítimo**:

  - DC1 en DNS (sección 3): 24 ventanas fuera de episodios más 54 **dentro** de los intervalos de episodio;
  - **10.10.20.26** (cliente legítimo) dispara `http_abuse` (104 y 117 peticiones HTTP en 60 s) en las ventanas 08:51:50 y 08:52:00, durante la fuerza bruta r3. Con el candidato, eso **crearía un LIMIT en srv-dmz contra un cliente legítimo** (simulación de la sección 4.1: `otras_ips_con_eventos = ["10.10.20.26"]`). DC1, en cambio, está en NUNCA y no se restringe.

  El resto separa con márgenes amplios, **solo en este tramo y con este tráfico sintético**.

| # | Requisito |
|---|---|
| R-E3.1 | Una ventana sin score (sin tráfico propio en sus 10 s) **no crea una entrada nueva** en el feed. Solo puede mantener la que ya existe. Se implementa en `incorporar` del publicador v2 con prueba unitaria. Hay que medir sobre el 3B que no se pierde ninguna detección. |
| R-E3.2 | http_abuse no se evalúa en una ventana donde port_scan dispara para el mismo origen (o se etiqueta como «secundaria»). Así se separa HTTP de escaneo sin cambiar las acciones. |
| R-E3.3 | Se mantiene `heuristicos` con **todas** las reglas en el registro (instrumentación), aunque la entrada del feed use la principal. |
| R-E3.4 | `http_abuse` (umbral 100 peticiones en 60 s) alcanza a un cliente legítimo (10.10.20.26: 104–117). Antes de que pueda restringir hay que revisar el umbral sobre el 3B entero o dejarlo como señal. |

### 4.1 Renovaciones sin tráfico — SIMULADO con el código real del publicador

`herramientas/simular_renovaciones.py` pasa las decisiones del replay, en orden de `logged_at`, por `incorporar` **del publicador v2 candidato** (política `if_senal`). Lo hace con dos variantes:

- **A**, el candidato tal cual;
- **B**, que solo admite ventanas con score: es lo que pide R-E3.1.

Estado de escalera vacío al inicio del tramo. Resultados en `resultados/renovaciones-sin-trafico-r2-e15-periodico.json` y `resultados/renovaciones-sin-trafico-r4-e5-eventos.json`; r4 da cifras iguales a ±20 s.

| Episodio (r2) | Eventos A → B | Última ventana que crea entrada, tras el fin (A → B) | `hasta` de la restricción tras el fin (A → B) | Nivel de escalera |
|---|---|---|---|---|
| escaneo_sostenido-r4 (cola del tramo) | 7 → 7 | +9 → +9 s | +347 → +347 s | 1 |
| escaneo_sostenido-r5 | **20 → 8** | **+103 → +3 s** | +1846 → +1817 s | 2 |
| escaneo_breve-r5 | 3 → 1 | +25 → +5 s | +3818 → +3627 s | 3 |
| fuerza_bruta_http-r3 | **35 → 10** | **+126 → +6 s** | +3819 → +3629 s | 3 |
| fuerza_bruta_http-r5 | **32 → 10** | +106 → +6 s | +3819 → +3629 s | 3 |
| dns_inusual-r5 | 16 → 14 | +16 → +6 s | +328 → +328 s (dc1 y srv-dmz) | 3 en srv-dmz |
| **Total del tramo** | **115 → 52** | | | |

**Lectura (lo que hace hoy el candidato, sin R-E3.1):**

- **El 55 % de las entradas (63 de 115) las crean ventanas sin tráfico propio del origen**, hasta 126 s después de que acabe el ataque.
- Cada una es un `evento_id` nuevo y legítimo para el contrato: no es renovación por reprocesar, que está probado que no ocurre. Pero **prorroga la restricción con datos viejos**: unos 190 s más en los episodios de nivel 3 (+3819 frente a +3629 s) y unos 30 s en el escaneo sostenido.
- **Las colas también suben la escalera.** El escaneo breve llega a nivel 3 por eventos de los episodios anteriores, así que su BLOCK dura aproximadamente 1 h. La escalera hace lo que debe con un reincidente, pero en la variante A parte de esos peldaños los han puesto ventanas sin tráfico.
- **La variante B no pierde ninguna detección:** los 5 episodios siguen generando entrada. Solo elimina la cola.
- **R-E3.1 no está implementado.** Es una decisión de la Etapa 3: la simulación muestra el efecto, pero no lo cambia.

## 5. Siete configuraciones y tres α (punto 8, `if_senal`)

Tramo de 25 min con 5 episodios. Detección: alguna ventana del origen de ensayo con fin en (inicio − 10, fin + 120] que cumple la configuración. HEUR solo cuenta la regla prevista. Alarmas fuera: ventanas de cualquier entidad que cumplen la configuración fuera de (inicio − 10, fin + 120] de **todos** los episodios del 3B.

**Corrección de la métrica.** La cuenta «fuera» no ve las alarmas sobre **otras entidades durante** los episodios. Por eso se añade la columna «otras IPs en episodios» (`alarmas_otras_entidades_en_episodios`): ventanas de entidades distintas del origen de ensayo, dentro de los intervalos de episodio, que cumplen la configuración. Son falsas alarmas igualmente.

| Config | Detectados | t. escaneo breve (r2 → r4) | Alarmas fuera, r2 / r4 | Otras IPs en episodios | **Falsas alarmas totales, r2** |
|---|---|---|---|---|---|
| IF α = 0,05 | 5/5 | 45,5 → 26,4 s | 71 / 74 | 208 | **279** |
| IF α = 0,03 | 5/5 | 45,5 → 26,4 s | 51 / 52 | 141 | **192** |
| IF α = 0,01 | **4/5** (falla el escaneo breve) | — | 14 / 14 | 47 | **61** |
| HEUR | 5/5 | 45,5 → 26,4 s | 25 / 25 | 56 | **81**: DC1 `dns_entropy` (24 + 54), 10.10.20.26 `http_abuse` (2), cola de `brute_force` del origen (1) |
| HÍB α = 0,05 | 5/5 | 45,5 → 26,4 s | 91 / 94 | 248 | **339** |
| HÍB α = 0,03 | 5/5 | 45,5 → 26,4 s | 74 / 75 | 190 | **264** |
| HÍB α = 0,01 | 5/5 | 45,5 → 26,4 s | 39 / 39 | 101 | **140** |

r4 coincide con r2 en detecciones y en «otras IPs en episodios»; en «fuera» difiere en hasta +3, por los cambios de clase α de la rotación. r7 (reinicio) da HEUR 21 fuera, porque pierde 4 ventanas de `dns_entropy` de DC1 tras el reinicio. Cifras exactas y entidades por replay: `resultados/comparacion-replays-tramo.json` → `configuraciones.<replay>.siete_configuraciones`.

**Lectura (sin elegir α, que es decisión de Mark):**

- **`if_senal` se sostiene.** Cualquier α que detecte el escaneo breve con el IF (0,05 o 0,03) produce entre 192 y 279 falsas alarmas sobre otras entidades en 25 min. Si esas alarmas restringieran, cortarían a usuarios.
  - Con `if_senal`, el IF queda como señal registrada (`senales-if.jsonl` del publicador v2), y la restricción la deciden las reglas.
- **HEUR** detecta 5 de 5 con 81 falsas alarmas: 78 de DC1, 2 de 10.10.20.26 y 1 de cola.
  - Si se aplica R-E2 (DC1 deja de contar como origen de `dns_entropy`), quedarían 3.
  - Con R-E3.1 (sin colas) y R-E3.4 (umbral de `http_abuse`), quedarían 0 **en este tramo**.
  - Ninguno de esos cambios está implementado.
- **HÍB** no añade detecciones a HEUR en este tramo y sí añade alarmas.
- **Límite:** son 5 episodios en 25 min de un solo día. Las proporciones no se pueden extrapolar sin repetirlo sobre el 3B completo (25 episodios), que queda pendiente.

## 6. Limpieza en seco del origen de ensayo (punto 9)

`scripts/enforce/limpiar_origen.py` y la operación `retirar_origen` del helper:

- respaldo previo del estado del publicador;
- retirada de 10.10.20.30 del estado del publicador, incluida la escalera;
- retirada de los sets `bloqueados` y `limitados` de los perfiles dmz y dns;
- comprobación posterior (`presente: false`).

Rechaza las IPs de NUNCA_BLOQUEAR. Ensayado solo en el banco, con 3 pruebas:

- `test_limpieza_en_seco_no_toca_original`;
- `test_limpieza_rechaza_infraestructura`;
- `test_limpieza_con_helper_real`.

**No se ha ejecutado contra el laboratorio.**
