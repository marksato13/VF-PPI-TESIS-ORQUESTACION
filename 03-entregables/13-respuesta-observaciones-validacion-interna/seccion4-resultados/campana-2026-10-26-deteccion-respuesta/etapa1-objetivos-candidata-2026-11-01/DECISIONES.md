# Matriz única de decisiones D1–D8

**Versión:** 3 (consolidación de la Etapa 1), 1-nov-2026, sobre `c1de49d`. Sustituye a la matriz de la versión 2. **Todos los documentos de esta carpeta remiten a esta matriz.**

**Las decisiones se separan en tres planos:**

- **Alcance o diseño:** lo que la candidata debe hacer. Puede estar *decidido* por el usuario, *adoptado* (camino aceptado por el usuario el 1-nov) o *recomendado*.
- **Compatibilidad técnica pendiente:** lo que hay que comprobar antes de congelar.
- **Autorización futura:** instalar, activar o desplegar. Siempre la da Mark y **ninguna está concedida**.

Las cifras proceden de `resultados/presupuesto-e2e.json` y `resultados/TABLAS-E2E.md`. Es una simulación sobre registros de sombra con restricciones **hipotéticas**, no son aplicaciones reales.

| Id | Tema | Alcance o diseño | Compatibilidad pendiente | Autorización futura | Fundamento |
|---|---|---|---|---|---|
| **D1** | Respuesta del escenario DNS | **Adoptado:** el destino sigue siendo DC1 (10.10.10.20) y la respuesta se aplica en DC1, limitada al DNS y al origen. **Mecanismo recomendado:** nftables en DC1 (tabla propia, UDP/TCP 53, set con `timeout`), con dos acciones: DNS-DENEGAR y DNS-LIMITAR por origen. | Ensayo del conjunto de reglas fuera de DC1; N de DNS-LIMITAR o asignación a DNS-DENEGAR; `alcance = "dns"` en el feed; 10.10.10.21 en NUNCA_BLOQUEAR; agente de DC1 en la rama candidata ([D1-VIABILIDAD-DC1.md](D1-VIABILIDAD-DC1.md) §6) | Instalar la cuenta, sudoers, llave y timer en DC1; destino nuevo del relé; activarlo en la campaña B | DC1 es **Samba 4.22.10 sobre Debian 13** con DNS interno. Las opciones Windows de la v2 no son aplicables. El DNS de Samba no tiene ACL por cliente; nft 1.1.3 está instalado con las reglas vacías (comprobado en solo lectura). |
| **D2** | Objetivo del escaneo breve | **Decidida:** detectar y actuar **durante** el escaneo breve, sin prolongarlo | Etapas 2 (captura y cadena) y 3 (regla temprana): ambas necesarias (PRESUPUESTO-TEMPORAL §4) | — | En el 3B, la regla prevista llegó tarde en 5/5 |
| **D3** | Papel del IF | **Adoptada `if_senal`:** el IF sigue puntuando y emitiendo ALERT; una alerta aislada del IF **no** produce LIMIT; las restricciones automáticas proceden de condiciones heurísticas explícitas y verificadas; la señal del IF queda para observación, priorización y análisis. **Se conservan α = 0,05, 0,03 y 0,01** para comparar la detección; el α definitivo **no se elige** aquí. | Implementarla en el publicador de la rama candidata (hoy ALERT del IF → LIMIT) con pruebas (Etapa 3) | Desplegar el publicador candidato (Mark) | §D3 |
| **D4** | Repeticiones | **Decidida:** 25 episodios por campaña, 5 por escenario | — | Ejecutar las campañas A y B | OBJETIVOS §4 |
| **D5** | Independencia de episodios | **Recomendada:** limpieza verificada **solo** del estado del origen de ensayo (10.10.20.30) en el estado de escalada del publicador y en los sets de **cada** punto de aplicación (srv-dmz y DC1). Antes se copian con hash, se comprueba que no queda nada antes de `t_inicio` y no se tocan otras entidades ni sus evidencias. La reincidencia se evalúa en pruebas separadas. | Procedimiento escrito y ensayado en seco sobre copias (Etapa 2) | Ejecutarlo con sudo en la campaña B (Mark) | El origen estaba en nivel 3 antes del 3B: 24/25 episodios habrían empezado con BLOCK hipotético |
| **D6** | Presupuesto de falsas respuestas | **Aceptados como objetivos operativos:** 0 BLOCK a entidades legítimas; 0 fallos de transacciones legítimas atribuibles a una restricción. **Propuesta técnica pendiente de confirmar antes de congelar:** para LIMIT, ≤ 1 intervalo por entidad legítima y jornada de 8 h, y ≤ 1 % del tiempo de observación restringido por entidad. Son límites independientes y **no** son umbrales científicos universales. | Confirmar los dos valores de LIMIT; control normal nuevo ≥ 2 h con medición de transacciones ([PRESUPUESTO-FALSAS-ALARMAS.md](PRESUPUESTO-FALSAS-ALARMAS.md) §3–§4) | Ejecutar el control (Mark) | Con `if_senal`: 1 entidad con restricción hipotética (10.10.20.26, 21,9 %, `http_abuse`) |
| **D7** | Instrumentación | **Recomendada:** t_pub, t_relay y t_apl (commit nft, código de retorno, relectura del set) y `counter` en las reglas, en la rama candidata, para srv-dmz **y** DC1. **Preparar no es activar.** | Pruebas unitarias del registro | Activar los agentes en la campaña B | Hoy t_apl y t_efecto no se pueden medir |
| **D8** | Horizonte temporal | **Recomendada:** se conservan `t_fin_ref` y `t_fin_observado`; `t_fin_eval = min(ref, observado)` para que una referencia artificial no convierta en oportuna una respuesta tardía. En la campaña B se distingue el **corte provocado por la respuesta** del **final natural** y se registran los **intentos del generador** después de t_apl (salida y SPAN). | — | — | dns_inusual-r2 terminó a 89,08 s; D_ref mínima de nmap: 65,52 s (sostenido) y 17,59 s (breve) |

**Antes de congelar faltan:**

- **D1:** comprobaciones técnicas concretas (el punto de aplicación ya está resuelto).
- **D6:** confirmar los dos valores de LIMIT.
- **D3:** implementarla y probarla en la rama candidata.
- Confirmar las recomendaciones D5, D7 y D8.

Ninguna de ellas bloquea el trabajo offline de la Etapa 2. El protocolo de evaluación **no está congelado**.

---

## D1 · Resumen

Detalle completo, con evidencia y referencias oficiales, en [D1-VIABILIDAD-DC1.md](D1-VIABILIDAD-DC1.md).

| Opción | Aplicable | Valoración |
|---|---|---|
| Política de resolución de consultas de Windows DNS | no (DC1 es Samba sobre Debian) | descartada por incompatibilidad |
| Regla del Firewall de Windows | no | descartada por incompatibilidad |
| **nftables en DC1, UDP/TCP 53 y el origen** | sí (inventario comprobado) | **recomendada** |
| Configuración del DNS interno de Samba | sin ACL de consultas por cliente | descartada |
| Pasar el DC a BIND9_DLZ | cambio de infraestructura | descartada |
| pfSense, resolver propio, solo detección | — | descartadas (norma o decisión del usuario) |

**Diferencia con srv-dmz:**

- En srv-dmz, BLOCK descarta **todo** el tráfico del origen y LIMIT usa un único cubo compartido de 100/s.
- En DC1, las dos acciones se limitan al **puerto 53** del origen, y DNS-LIMITAR es **por origen**.
- No se promete que un LIMIT sea eficaz contra el escenario DNS mientras N no esté fijado y probado.

Que 10.10.10.20 esté en NUNCA_BLOQUEAR impide restringirlo **como origen**. No impide aplicar una medida **en** él contra otro origen.

## D3 · Política `if_senal` consolidada

**Qué cambia respecto al publicador desplegado** (`publicar_feed.py` f7bc4c7d):

| | Desplegado | Candidata (`if_senal`) |
|---|---|---|
| ALERT del IF (score < umbral) | → **LIMIT** al origen («modelo:…») | → **solo señal**: se registra, se muestra y prioriza, pero no se escribe en el feed como restricción |
| Veredicto heurístico (`port_scan`, `brute_force`, `http_abuse`, `dns_entropy`) | → su acción (BLOCK/LIMIT) | igual |
| ALERT de heurístico *legacy* (`*_heuristic`) | → BLOCK | igual (debe revisarse en la Etapa 3: es una condición heurística, pero hay que verificarla) |
| α del IF | determina restricciones | solo determina **señales** |

**Tres resultados separados** (TABLAS-E2E §5, por episodio):

1. **Anomalía del IF:** primera ventana atribuible con ALERT del IF a cada α. El IF **no clasifica familias**: no se le exige producir `port_scan` para contar una anomalía atribuible.
2. **Identificación por el heurístico previsto** (MATRIZ-ESCENARIOS).
3. **Decisión y aplicación de la respuesta** (con `if_senal`, solo heurísticos), con su t_apl estimada bajo supuestos y, en la campaña B, la real.

Disponibles antes del fin en el 3B (simulación):

| Escenario | 1. IF (desplegado / 0,05 / 0,03 / 0,01) | 2. Heurístico previsto | 3. Respuesta de la regla prevista antes del fin* |
|---|---|---|---|
| DNS inusual | 2 / 2 / 2 / 2 | 5 | 5 (sin punto de aplicación hoy; con D1, DC1) |
| Escaneo breve | 1 / 1 / 1 / 0 | 0 | 0 |
| Escaneo sostenido | 5 / 5 / 5 / 5 | 4 | 4 |
| Fuerza bruta HTTP | 5 / 5 / 5 / 5 | 5 | 5 |
| Inundación HTTP | 5 / 5 / 5 / 5 | 5 | 5 |

\* aplicación estimada bajo supuestos (escenarios favorable y alto); no es una aplicación real.

**Consecuencias que se aceptan y declaran:**

- Un ataque señalado **solo** por el IF puede quedar sin respuesta automática. En el 3B no hubo ninguno (25/25 con una acción heurística). En escaneo_sostenido-r3 la acción vino de una regla equivocada (`brute_force`), y `port_scan` llegó tarde (Etapa 3).
- La reducción de entidades con restricción hipotética (de 9 a 1 en el control de 33 min) es una **simulación sobre datos de desarrollo**, no una validación independiente.
- `if_senal` **no** hace al híbrido superior a los heurísticos solos. Con esta política, las respuestas **son** las de los heurísticos; el valor del IF se mide en la campaña A como detector (resultado 1) y como apoyo a la priorización.
- En DNS r2–r4 el IF no alertó con ningún α: solo `dns_entropy` detectó.

**Comparación de políticas** (control de 33 min; entidades con restricción hipotética · intervalos · entidades > 50 %):

| Política | Resultado | Lectura |
|---|---|---|
| actual, α desplegado ≈ 0,05 | 9 · 15 · 5 | inaceptable para tráfico legítimo |
| actual, α 0,03 / 0,01 | 7 · 11 · 4 / 3 · 7 · 3 | α reduce el problema, no lo resuelve |
| persistencia k = 2 / k = 3 | 4 · 6 · 3 / 3 · 5 · 3 | 10.10.20.22, .24 y .26 son anómalos de forma persistente |
| **if_senal (adoptada)** | **1 · 1 · 0** | queda 10.10.20.26 por `http_abuse` (Etapa 3) |
