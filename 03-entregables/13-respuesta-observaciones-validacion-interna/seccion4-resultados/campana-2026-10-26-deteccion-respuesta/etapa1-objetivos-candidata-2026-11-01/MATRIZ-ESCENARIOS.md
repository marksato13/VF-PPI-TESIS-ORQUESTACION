# Matriz por escenario

**Fuentes:** `escenarios/escenarios.json` y `FICHAS-ESCENARIOS.md` (configuración congelada de la campaña), `heuristicos.py` VERSION 2026-10-06.2 y los resultados del 3B en [resultados/TABLAS-E2E.md](resultados/TABLAS-E2E.md).

**Origen de todos los episodios:** Kali 10.10.20.30. Calentamiento 60 s, contexto previo 120 s y observación posterior 90 s.

**Reglas comunes:**

1. **No se usan como sustituto de la detección** la IP del generador, los horarios, los identificadores de episodio ni las marcas del generador. Esos datos sirven **solo** para atribuir una señal *a posteriori*, nunca para producirla ni para filtrar.
2. **El escaneo breve no se prolonga.** Su duración natural (≈ 18 s) es la característica que se evalúa.
3. En cada celda se separa lo **definido** de lo **provisional** y de lo **pendiente**, y se indica qué decisión (D1–D8, en [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) §7) lo desbloquea.
4. «Éxito», «fallo» e «indeterminado» se miden contra `t_fin_programado` (§2.2 de los objetivos).
5. Las exclusiones posibles son las de la §6. Un **fallo del experimento** no es un fallo del detector.

---

## 1. Escaneo sostenido (nmap -sT 1-65535 -T4, max-rate 1500, max-retries 0, a 10.10.30.10)

| Elemento | Contenido | Estado |
|---|---|---|
| Comportamiento y duración | Conexiones TCP a 65 535 puertos de srv-dmz. Termina de forma natural en 65,5–66,3 s (3B, n = 5). `t_fin_programado = t_inicio + 65,52 s` (D_ref, la mínima). | definido (D8 para D_ref) |
| Evidencia de atribución | SYN del origen al destino en el SPAN dentro de la ventana y de [inicio, fin] (`paquetes_en_intervalo_ataque > 0`), y la ventana solapa el episodio | definido (cadena v2) |
| Objetivo de detección | Heurístico `port_scan` → BLOCK. Rama de ráfaga ≥ 200 intentos/30 s con completitud SYN ≤ 0,1, o rama 20 flujos/30 s con ratio de puertos ≥ 0,45 y completitud ≤ 0,3. El IF → LIMIT es secundario. | definido |
| Respuesta prevista y condiciones | BLOCK del origen en srv-dmz (set `cyberflow_bloqueados`, timeout de la escalada). Requiere **agente activo** (D7) y estado de escalada vacío al inicio (D5). | pendiente D5/D7 |
| Evidencia de aplicación | Retorno del commit nft más `nft -j list set` con `expires` y marca de tiempo del agente. Hoy no se registra la hora del commit (Etapa 2). | pendiente (Etapa 2) |
| Evidencia de efecto | En el SPAN: los SYN del origen continúan y **desaparecen los SYN-ACK/RST** de 10.10.30.10 al origen. `t_efecto` = última respuesta del destino. Contadores nft si se añade `counter` (D7). | definido (método); contadores pendientes |
| Tráfico legítimo a preservar | Las transacciones de control a srv-dmz (HTTP 80 y 18081 de los clientes 10.10.20.21–26) y la gestión SSH desde el bastión 10.10.10.30, que está en NUNCA_BLOQUEAR | definido |
| Criterio | **Éxito:** t_apl y t_efecto < t_fin_programado − ε. **Fallo:** cualquiera de los dos ≥ t_fin, o no hay acción. **Indeterminado:** el intervalo de la marca cruza el fin. n y la cota según D4. | definido (n, D4) |
| Referencia 3B (estimación V0) | 5/5 t_apl estimado antes del fin. Mediana de la cota superior: 38,4 s; margen mínimo, 18,3 s. | estimado |

## 2. Escaneo breve (nmap -sT 1-1000 -T4 a 10.10.30.10)

| Elemento | Contenido | Estado |
|---|---|---|
| Comportamiento y duración | 1000 puertos. Termina en **17,6–18,0 s** (3B, n = 5). **No se prolonga.** `t_fin_programado = t_inicio + 17,59 s`. | definido (D8) |
| Evidencia de atribución | Igual que el escaneo sostenido | definido |
| Objetivo de detección | `port_scan` → BLOCK, **dentro de los ~17 s**. Con ventanas de 10 s, la señal debería salir de la **primera** ventana cerrada (window_end ≤ t_inicio + 10 s), con los pocos segundos de ataque que contiene. | **provisional (D2)** |
| Respuesta prevista y condiciones | BLOCK en srv-dmz, con las mismas condiciones D5/D7 | pendiente |
| Evidencia de aplicación y efecto | Igual que el sostenido | ídem |
| Tráfico legítimo a preservar | Igual que el sostenido | definido |
| Criterio | Igual que el sostenido. Hoy **se sabe de antemano que fallaría** (abajo). | provisional (D2) |
| Referencia 3B | **V0: 0/5 antes del fin** (t_apl sup. 28,2–50,6 s frente a 17,6–18,0). **V1** (cadena por eventos): 0/5. **V2** (decisión nada más cerrar la ventana, más la cadena por eventos): 1/5, y ese caso (r1) lo provoca una señal `brute_force` mal atribuida, no `port_scan`. En 2/5 la primera ventana con señal **cierra después** del fin. | estimado |

**Lectura.** En el escaneo breve, ninguna mejora de la cadena basta. La señal `port_scan` aparece en ventanas que contienen el ataque completo o que cierran después de él. Hace falta que el heurístico decida con evidencia parcial y antes del cierre de la ventana (Etapa 3) **y** una cadena por eventos (Etapa 2). Véase PRESUPUESTO-TEMPORAL §4.

## 3. Fuerza bruta HTTP (POST a 10.10.30.10:18081/auth, 90 s)

| Elemento | Contenido | Estado |
|---|---|---|
| Comportamiento y duración | Bucle de 90 s de intentos de autenticación con credenciales erróneas, con la credencial de control `control:control123 → 200` como verificación. `t_fin_programado = t_inicio + 90 s`. | definido |
| Evidencia de atribución | Peticiones HTTP del origen a :18081 en el EVE (`http`), con respuestas 401/403, dentro de la ventana y del episodio | definido. **Requiere EVE C0 o C1 explícito**: en C1 no se afirma la ausencia de señal L7. |
| Objetivo de detección | `brute_force` → BLOCK (≥ 5 req/60 s y ≥ 80 % de 401/403) | definido |
| Respuesta prevista y condiciones | BLOCK del origen en srv-dmz (D5/D7) | pendiente |
| Evidencia de aplicación | Igual que el sostenido | pendiente (Etapa 2) |
| Evidencia de efecto | Desaparecen las respuestas HTTP (401/200) de :18081 al origen en el SPAN/EVE; el servidor de laboratorio deja de registrar peticiones del origen | definido (método) |
| Tráfico legítimo a preservar | Inicios de sesión legítimos de los clientes en :18081 (perfil de control) | definido |
| Criterio | Igual que el sostenido | definido (n, D4) |
| Referencia 3B | V0: 5/5 antes del fin. t_apl sup. 28,5–35,5 s; margen ≥ 54,5 s. | estimado |

## 4. Inundación HTTP (curl, concurrencia 8, a 10.10.30.10:80, 90 s)

| Elemento | Contenido | Estado |
|---|---|---|
| Comportamiento y duración | 8 bucles de `curl --max-time 2` durante 90 s: 14 318 intentos en r1 (~160/s). `t_fin_programado = t_inicio + 90 s`. | definido |
| Evidencia de atribución | Peticiones HTTP del origen a :80 en EVE y SPAN dentro de la ventana y del episodio | definido |
| Objetivo de detección | `http_abuse` → LIMIT (≥ 100 req/60 s, fallos < 0,8) o anomalía del IF → LIMIT. **En el 3B**, la primera señal fue siempre el IF; `http_abuse` no la dio. Además, **`port_scan` → BLOCK** apareció hacia los 112–117 s, después del fin, en las 5 repeticiones: mezcla de abuso HTTP con escaneo (Etapa 3: «separación del abuso HTTP»). | **provisional (D3)** |
| Respuesta prevista y condiciones | LIMIT, `limit rate over 100/second drop`. Un LIMIT de 100 paquetes/s frente a ~160 peticiones/s (varios paquetes por petición) **puede o no** reducir el ataque: se desconoce. | provisional (D3) |
| Evidencia de aplicación | Igual que el sostenido | pendiente |
| Evidencia de efecto | Tasa de respuestas HTTP del destino al origen (SPAN/EVE) en bloques de 1 s: un efecto exige una reducción ≥ 50 % frente a los 10 s previos a t_apl. **El 50 % es provisional**; no existe una referencia previa que lo justifique y queda como decisión de Mark. | provisional |
| Tráfico legítimo a preservar | HTTP :80 de los clientes de control. Un LIMIT al origen no les afecta, pero un LIMIT por falsa alarma a ellos sí (véase el presupuesto de falsas alarmas). | definido |
| Criterio | Éxito si la restricción está aplicada **y** tiene efecto antes del fin | provisional |
| Referencia 3B | V0: 5/5 LIMIT antes del fin (t_apl sup. 32,3–45,5 s). **Población admitida: 1/5** (9 exclusiones del 3B: 4 de esta familia por kernel_drops de Suricata). | estimado |

## 5. DNS inusual (dig a 10.10.10.20, 2,3 consultas/s, 90 s, zona lab-ppi)

| Elemento | Contenido | Estado |
|---|---|---|
| Comportamiento y duración | Consultas con nombres aleatorios `*.lab-ppi`. El comodín responde y no hay nxdomain. `t_fin_programado = t_inicio + 90 s`. | definido |
| Evidencia de atribución | Consultas `dns` del origen a 10.10.10.20 en el EVE dentro de la ventana y del episodio | definido. C1 limita las afirmaciones L7. |
| Objetivo de detección | `dns_entropy` → LIMIT (≥ 20 consultas/60 s y ratio de nombres únicos ≥ 0,45) | definido |
| Respuesta prevista y condiciones | **No hay punto de aplicación.** El ataque va a DC1 (10.10.10.20) y el único agente está en srv-dmz (10.10.30.10). Un LIMIT al origen en srv-dmz **no toca** el tráfico DNS. El propio DNS está en NUNCA_BLOQUEAR, cosa correcta: esa lista protege al resolvedor de ser bloqueado, pero no es el origen del ataque. | **pendiente (D1)** |
| Evidencia de aplicación y efecto | No definible sin D1 | pendiente |
| Tráfico legítimo a preservar | Resolución DNS de todos los clientes (perfil de control) | definido |
| Criterio | Mientras D1 siga abierta: **solo Q1** (detección antes del fin, en sombra). La familia **no** entra en el criterio de respuesta. | definido como alcance reducido |
| Referencia 3B | t_det 17,2–25,9 s, 5/5 antes del fin (`dns_entropy` en 3/5 y el IF en 2/5). Pero `dns_entropy` también dispara 88 veces sobre el resolvedor 10.10.10.20 en el control (falsas alarmas; véase el presupuesto). | medido (t_det) |

---

## Resumen de viabilidad (con lo que hay hoy)

| Familia | Q1 detección antes del fin (3B, medido) | Q2 aplicación antes del fin (V0, estimado) | Q3 efecto | Bloqueante principal |
|---|---|---|---|---|
| Escaneo sostenido | 5/5 | 5/5 | no medible (sombra) | D5, D7 |
| Fuerza bruta HTTP | 5/5 | 5/5 | no medible | D5, D7, descartes de Suricata |
| Inundación HTTP | 5/5 (IF) | 5/5 (LIMIT) | **desconocido** (100 pps) | D3, descartes (1/5 admitidos) |
| Escaneo breve | **1/5** (r1, y por una señal `brute_force` mal atribuida); en 3/5 la ventana con señal cierra antes del fin, pero su registro llega después | **0/5** | — | arquitectura (Etapas 2 y 3), D2 |
| DNS inusual | 5/5 | sin punto de aplicación | — | D1 |

«Q1 detección» cuenta los episodios cuya primera señal atribuible con veredicto **estaba disponible** (t_det) antes del fin. En el escaneo breve, t_det llega 16–40 s después del inicio, frente a un fin a 17,6–18,0 s. Las cifras son del 3B, con 5 repeticiones y antes de las mejoras: **describen, no confirman** (cota inferior con 5/5: 0,55).
