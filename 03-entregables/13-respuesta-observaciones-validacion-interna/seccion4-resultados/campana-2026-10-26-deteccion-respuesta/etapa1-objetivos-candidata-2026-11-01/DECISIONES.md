# Matriz única de decisiones D1–D8

**Versión:** 2 (corrección de la Etapa 1), 1-nov-2026. Sustituye a las listas de decisiones de `2482a40`. **Todos los documentos de esta carpeta remiten a esta matriz.**

**Estados posibles:**

- **decidida**: la decidió el usuario.
- **recomendada**: hay propuesta concreta; debe confirmarse antes de la etapa indicada, pero no bloquea el trabajo offline.
- **pendiente esencial**: cambia el alcance o depende de una preferencia operativa del usuario.

Las cifras de la columna «Fundamento» proceden de `resultados/presupuesto-e2e.json` (simulación sobre registros de sombra, con restricciones **hipotéticas**) y de `resultados/TABLAS-E2E.md`.

| Id | Tema | Estado | Recomendación o decisión | Fundamento | Consecuencias | Se necesita en |
|---|---|---|---|---|---|---|
| **D1** | Respuesta para el DNS inusual | **pendiente esencial** (alcance) | **Punto de aplicación en DC1** (10.10.10.20): un agente mínimo consume el mismo feed firmado y aplica una **política de resolución de consultas del servidor DNS** que ignora o deniega las consultas **del origen señalado**, con caducidad. Si esa política no resulta adecuada, la alternativa es una regla del Firewall de Windows limitada a UDP/TCP 53 desde ese origen. | Hoy el único agente está en srv-dmz y el ataque va a DC1: un LIMIT al origen en srv-dmz no toca el DNS. Comparación en §D1. | Añade un agente en un controlador de dominio. Es un cambio de alcance y de infraestructura que se declara y se valida. Windows no ofrece un LIMIT por origen equivalente al de nft, así que la acción DNS pasa a ser una **denegación limitada al servicio DNS** y deja de ser un LIMIT. | Diseño: Etapa 2 (offline). Instalación: antes de la campaña B. |
| **D2** | Objetivo del escaneo breve | **decidida** (usuario) | «Detectar y aplicar una respuesta efectiva mientras el escaneo breve sigue activo.» No se sustituye por contención de la reincidencia ni se prolonga el ataque. | — | La Etapa 2 (captura y cadena) y la Etapa 3 (regla temprana de escaneo) son ambas necesarias (PRESUPUESTO-TEMPORAL §4). | Todas |
| **D3** | Acción del IF | **pendiente esencial** (preferencia operativa) | **El IF señala pero no restringe por sí solo** (política `if_senal`). La restricción la dan los heurísticos. El IF queda para la comparación en sombra, la priorización y la investigación. | El motor emite ALERT y el publicador desplegado lo convierte en LIMIT. En el control (33 min, restricciones hipotéticas) se restringe a 9 / 7 / 3 entidades con α = 0,05 / 0,03 / 0,01; con persistencia de 3 ventanas, a 3; con `if_senal`, a 1 (10.10.20.26, por `http_abuse`). En los 25 episodios, `if_senal` **no retrasa** la primera acción en ninguna familia, porque en las mismas ventanas había un heurístico (§D3). | Se pierde la respuesta automática ante anomalías que ningún heurístico cubra; queda como señal. El α del IF solo afecta a la comparación de detectores. | Etapa 3 (implementar), campaña B |
| **D4** | Repeticiones | **decidida** (usuario) | **25 episodios por campaña, 5 por escenario** (DNS, inundación HTTP, escaneo breve, escaneo sostenido, fuerza bruta). Sin aumento automático. | Con 5 por escenario se describen resultados e incertidumbre (OBJETIVOS §4), sin garantías poblacionales. | Se publican siempre planificados, ejecutados, admitidos y excluidos. Los fallos no se sustituyen. | Etapas 4 y 5 |
| **D5** | Independencia de episodios | **recomendada** | **Limpieza verificada del estado del origen de ensayo** entre episodios: copiar con hash el estado de escalada y los sets; retirar **solo** la entrada de 10.10.20.30 del estado de escalada del publicador y de los sets nft de cada punto de aplicación; comprobar que no quedan entradas antes de `t_inicio`. No se tocan las demás entidades ni sus evidencias. La reincidencia se evalúa en ensayos específicos aparte. | El origen ya estaba en nivel 3 antes del 3B. Con la política actual, 24/25 episodios habrían empezado con un BLOCK hipotético de 3600 s (simulación secuencial, bajo supuestos). | Si al inicio hay una restricción vigente, el episodio es un **fallo del experimento**. El procedimiento lo ejecuta Mark (sudo en srv-dmz y estado del sensor). | Etapa 2 (escribir y ensayar en seco), campaña B |
| **D6** | Presupuesto de falsas alarmas | **pendiente esencial** (preferencia operativa; hay propuesta) | P1: 0 BLOCK a legítimos. P2: ≤ 1 intervalo de restricción por entidad legítima y jornada de 8 h. P3: ≤ 1 % de tiempo restringido por entidad, **medido directamente** con renovaciones. P4: 0 fallos de transacciones legítimas atribuibles. P5: las señales se publican por componente, sin ser criterio por sí solas. Control normal nuevo de **≥ 2 h**. | PRESUPUESTO-FALSAS-ALARMAS §3. Las renovaciones alargan los intervalos: con la política actual hubo 734 renovaciones en 15 intervalos. | Con la política actual no se cumple con ningún α; con `if_senal` falla P3 por 10.10.20.26 (`http_abuse`, Etapa 3). | Congelación (antes de la Etapa 4) |
| **D7** | Instrumentación | **recomendada** | Registrar en la **rama candidata** t_pub, t_relay y t_apl (hora y código de retorno del commit nft, lote aplicado y lectura del set) y añadir `counter` a las reglas. **Preparar no es activar**: el agente sigue inactivo hasta que se autorice la campaña B. | t_apl y t_efecto hoy no se pueden medir. | Cambio de producto en la rama candidata, probado offline. Activar el agente es una decisión aparte. | Etapa 2 (código), campaña B (activación) |
| **D8** | Horizonte temporal | **recomendada** | Bucles: `t_inicio + 90 s`. nmap: `D_ref` = duración natural **mínima** de la familia en la campaña A de la **misma candidata**. En cualquier caso, `t_fin_eval = min(t_fin_ref, t_fin_observado)`. En la campaña B se registra por separado el corte provocado por la respuesta y se conserva la evidencia de intentos del generador (SPAN y salida). | Una referencia fija no puede convertir en oportuna una actuación posterior al final real: dns_inusual-r2 terminó a 89,08 s y su fin evaluado es el observado. La mínima es la referencia más exigente. | En el 3B: `D_ref` = 65,52 s (sostenido) y 17,59 s (breve). Para la candidata se recalcula con su campaña A. | Etapas 4 y 5 |

**Pendientes esenciales:** D1 (alcance: agente en DC1), D3 (política del IF) y D6 (cifras del presupuesto). **Ninguna impide** empezar el trabajo offline de la Etapa 2 (DISENO-VALIDACION §Etapa 2). El protocolo de evaluación **no está congelado**.

---

## D1 · Comparación de puntos de aplicación para el DNS

| Opción | Dónde actúa | Ventajas | Inconvenientes | Valoración |
|---|---|---|---|---|
| A1. Política de resolución de consultas en DC1 (agente en DC1) | Servicio DNS de DC1, solo frente al origen señalado | Actúa sobre el objetivo real sin cambiar el escenario. Afecta **solo al DNS**, no al resto del tráfico del origen hacia el DC. Es nativa y reversible. El efecto se mide con las respuestas DNS (desaparecen o pasan a REFUSED). | Agente nuevo en Windows, que debe verificar la firma ed25519 del feed. Toca un controlador de dominio. No es un LIMIT. | **Recomendada** |
| A2. Firewall de Windows en DC1, UDP/TCP 53 desde el origen | Pila de red de DC1 | Mismo objetivo real; sencilla | Mismo agente nuevo. Menos precisa que A1 si la regla se amplía. | Alternativa a A1 |
| B. pfSense (tabla de alias entre VLAN) | Cortafuegos | Cubre cualquier destino | Modifica el cortafuegos central del laboratorio: la norma vigente es no tocarlo. Si falla, el radio de impacto es toda la red. | No recomendada |
| C. Resolver Linux propio (p. ej. en srv-dmz) como destino del escenario | Host con el agente nft actual | Reutiliza el agente existente | **Cambia el escenario** (destino y topología). El ataque a DC1 deja de evaluarse y los clientes legítimos siguen usando DC1. | Solo si A1 y A2 se descartan, y declarada como cambio de escenario |
| D. Solo detección | — | Ninguna implantación | No cumple el objetivo del usuario, que incluye responder | **Descartada** como opción por defecto |

Que 10.10.10.20 esté en NUNCA_BLOQUEAR protege al resolvedor de ser restringido como **origen**, y no impide aplicar una medida **en** el resolvedor contra otro origen.

## D3 · Señal, corroboración y persistencia

| Política | Qué hace el IF | Rapidez en los 25 episodios del 3B | Control, 33 min: entidades con restricción hipotética · intervalos · entidades > 50 % | Lectura |
|---|---|---|---|---|
| actual (α desplegado ≈ 0,05) | ALERT → LIMIT | referencia | 9 · 15 · 5 | inaceptable para tráfico legítimo |
| actual, α = 0,03 / 0,01 | ídem | igual | 7 · 11 · 4 / 3 · 7 · 3 | α reduce el problema, pero no lo resuelve |
| persistencia k = 2, α desplegado / 0,01 | LIMIT si hay ALERT en 2 ventanas seguidas | igual (las acciones salen de los heurísticos) | 4 · 6 · 3 / 2 · 5 · 2 | los clientes 10.10.20.22, .24 y .26 son anómalos **de forma persistente**: la persistencia no los protege |
| persistencia k = 3, α desplegado / 0,01 | ídem, 3 ventanas (≥ 20 s más de espera) | igual | 3 · 5 · 3 / 2 · 5 · 1 | ídem |
| **if_senal** | solo señal | **igual**: en todas las familias la primera acción procede de un heurístico en la misma ventana | **1 · 1 · 0** (10.10.20.26, 21,9 % del control, `http_abuse`) | **recomendada** |
| corroboración (IF + heurístico en la misma ventana) | eleva la prioridad o el registro | igual que `if_senal` en acciones | igual que `if_senal` | compatible con `if_senal`: no añade restricciones |

**Advertencias:**

- La rapidez «igual» es la observada en **estos** 25 episodios. Un ataque que solo detecte el IF quedaría sin respuesta automática.
- En escaneo_sostenido-r3, sin el IF, la primera acción sería un BLOCK por `brute_force` (atribución errónea) y `port_scan` solo llega a los 74,3 s, después del fin. Corregir esa atribución es trabajo de la Etapa 3.
- La anomalía persistente de 10.10.20.22, .24 y .26 apunta a deriva del modelo o a perfiles legítimos no representados: se investiga offline en la Etapa 3.
