# N1 — Tabla de decisión PERMIT / LIMIT / BLOCK (para metodología y presentación)

**Observación N1:** llevar la tabla de decisión LIMIT vs BLOCK (ya en el panel,
`#s-variables`) a la metodología y la presentación, y **definir qué es LIMIT**.
**Fuente:** panel vigente (sección «Umbrales y régimen de decisión») + `heuristicos.py`.

---

## 1. Las tres acciones (qué significa cada una)

| Acción | Qué hace en el host (nftables) | Cuándo | Reversión |
|---|---|---|---|
| **PERMIT** | Nada. El tráfico pasa normal. | Ventana dentro de lo normal aprendido. | — |
| **LIMIT** | **Limita la tasa, NO corta.** Degrada el caudal de esa IP (rate-limit), el servicio sigue accesible. | Volumen alto **ambiguo** que puede ser uso pesado legítimo (flood HTTP, DNS de alta entropía). | Se levanta solo al bajar la actividad. |
| **BLOCK** | **Corta.** Añade la IP a un set que la dropea en el host. | Patrón de ataque **inequívoco** (escaneo, fuerza bruta). | **Caduca sola** por timeout, con escalera por reincidencia **300 → 1800 → 3600 s**. No hay bloqueo permanente automático. |

> **La distinción clave (lo que pide N1):** **LIMIT** es una respuesta **graduada y
> reversible** para lo ambiguo (no se niega el servicio, solo se frena); **BLOCK** es un
> corte para lo que no deja dudas. Separar «frenar» de «cortar» evita negar servicio por un
> falso positivo en tráfico que podría ser legítimo.

**Regla de combinación:** cada IP recibe **la acción más severa** de todas las señales de
su ventana (PERMIT < LIMIT < BLOCK). Si coinciden el modelo (anomalía) y un heurístico
BLOCK, la acción es BLOCK.

---

## 2. Tabla de reglas (heurísticos deterministas → acción)

Son **criterio razonado, versionado (2026-10-06.2) y configurable**, no calibrados
estadísticamente como el umbral del modelo. Cubren los patrones donde el modelo mide flojo.

| Regla | Variables y umbral | Acción | Por qué ese valor |
|---|---|---|---|
| `port_scan` | intentos de flujo ≥20/30 s · puertos únicos ≥0,45 · SYN completados ≤0,30 — **ó** ráfaga ≥200/30 s con ≤10 % | **BLOCK** | El escaneo prueba muchos puertos y casi ninguno completa. FPR validado: +5 en 712 450 ventanas (0,012 %). |
| `brute_force` | ≥5 req HTTP/60 s **y** ≥80 % de fallo de auth (401/403) | **BLOCK** | Ráfaga de logins casi todos fallidos: señal inequívoca. El modelo mide flojo aquí. |
| `http_abuse` | ≥100 req HTTP/60 s sin patrón de fuerza bruta | **LIMIT** | Volumen alto **ambiguo** (puede ser uso pesado legítimo): se degrada la tasa, no se corta. |
| `dns_entropy` | ≥20 consultas DNS/60 s **y** (≥50 % NXDOMAIN **ó** ≥45 % nombres únicos) | **LIMIT** | El hueco donde el modelo sacó 0 % (DNS de alta entropía). FPR 0/527 sobre la línea base. |

**El modelo (no supervisado):** las 28 variables entran **juntas** a un Isolation Forest;
una ventana es anómala si su **score combinado < −0,5689** (umbral único, percentil
α = 0,05). **No hay corte por variable**. El modelo aporta la detección de lo que no tiene
regla; los heurísticos, la acción precisa (LIMIT/BLOCK) en los patrones conocidos.

---

## 3. Versión condensada para una diapositiva

> **Respuesta graduada por IP (la más severa de la ventana):**
> - **PERMIT** — normal, pasa.
> - **LIMIT** — *frena, no corta* (rate-limit). Para volumen ambiguo: `http_abuse` (≥100 req/60 s), `dns_entropy` (DNS alta entropía). Reversible al bajar la actividad.
> - **BLOCK** — *corta* (nftables en el host). Para ataque inequívoco: `port_scan`, `brute_force`. Caduca sola (escalera 300/1800/3600 s).
>
> El modelo (IsolationForest, no supervisado, θ = −0,5689) detecta lo anómalo; los
> heurísticos deciden la acción en los patrones conocidos.

---

## Notas para el artículo

- **LIMIT ≠ BLOCK**: definir explícitamente que LIMIT degrada la tasa y es reversible, y que
  BLOCK corta con caducidad por timeout. Es una decisión de diseño (minimizar negación de
  servicio ante ambigüedad), no un detalle de implementación.
- La respuesta se aplica **en el host protegido** (agente + nftables), no en el sensor
  (que solo observa por SPAN). Coherente con el alcance «observación en paralelo, acción
  en el host».
