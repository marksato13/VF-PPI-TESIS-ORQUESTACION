# N1 · Regla de decisión PERMIT / LIMIT / BLOCK — verificada contra el código

**Observación N1 (Abner):** ¿en qué condiciones LIMIT y en cuáles BLOCK? ¿qué es LIMIT?
**Verificado (2026-10-23) contra:** `heuristicos.py` (2026-10-06.2), `publicar_feed.py`,
`escalada.py`, `agente_enforce.py` (producto-main `fa9e5b0`) y el modelo desplegado
`if_limpio_2026_10`. Corrige dos valores del `N1-tabla-decision-limit-block.md` previo (§4).

## 1. Las tres acciones (efecto REAL en el host)

| Acción | Efecto en nftables del host | Cuándo | Caducidad / reversión |
|---|---|---|---|
| **PERMIT** | nada | ventana dentro de lo normal | — |
| **LIMIT** | set `cyberflow_limitados`: `limit rate over 100/second drop` → **cae solo lo que excede 100 paq/s**; la conexión sigue | volumen **ambiguo** (puede ser uso legítimo): `http_abuse`, `dns_entropy`, o anomalía **solo-modelo** | **timeout de 300 s** (plano, no escala); se **re-publica** mientras persista, expira solo al cesar |
| **BLOCK** | set `cyberflow_bloqueados`: **`drop`** de todo el tráfico de la IP | ataque **inequívoco**: `port_scan`, `brute_force` | **escalera 300 → 1800 → 3600 s** por reincidencia (<24 h) + revisión humana en el 3º; **nunca ∞** |

**LIMIT ≠ BLOCK (lo que pide N1):** LIMIT **frena** (rate-limit a 100/s, reversible), no niega el
servicio; BLOCK **corta**. La distinción protege contra negar servicio por un falso positivo en
tráfico que podría ser legítimo. La caducidad la ejecuta el **`timeout` nativo de nftables** (se
retira sola aunque el agente muera); **salir del feed no retira la regla de inmediato**: expira por
su timeout.

**Combinación:** por IP se aplica la acción **más severa** de la ventana (PERMIT < LIMIT < BLOCK).
Un **LIMIT posterior no degrada un BLOCK** vivo (no hay downgrade automático).

## 2. De la señal a la acción (lo que hace el publicador)

`publicar_feed.py`: **anomalía del modelo** (`score < umbral`) → **LIMIT**; **heurístico** → la acción
de su regla (BLOCK/LIMIT); se queda con la más severa por IP. El motor **no degrada** el modelo:
escribe `decision` ALERT/PERMIT + `score` + `heuristico`; la traducción a LIMIT/BLOCK es del feed.

## 3. Reglas heurísticas (criterio razonado, versión 2026-10-06.2, configurable)

| Regla | Condición (código) | Acción |
|---|---|---|
| `port_scan` | `flow_attempt_count_30s ≥ 20` **y** `unique_dst_port_ratio_30s ≥ 0,45` **y** `syn_completion_ratio_10s ≤ 0,30` — **ó** ráfaga `flow_attempt_count_30s ≥ 200` **y** `syn_completion_ratio_10s ≤ 0,10` | **BLOCK** |
| `brute_force` | `http_request_count_60s ≥ 5` **y** `http_auth_failure_ratio_60s ≥ 0,80` | **BLOCK** |
| `http_abuse` | `http_request_count_60s ≥ 100` **y** `http_auth_failure_ratio_60s < 0,80` | **LIMIT** |
| `dns_entropy` | `dns_query_count_60s ≥ 20` **y** (`dns_nxdomain_ratio_60s ≥ 0,50` **ó** `unique_dns_name_ratio_60s ≥ 0,45`) | **LIMIT** |

Severidad entre heurísticos: BLOCK > LIMIT; a igualdad, gana el orden `brute_force` → `port_scan`
→ `http_abuse` → `dns_entropy` (de lo más específico a lo más genérico).

**Modelo (no supervisado):** las 28 variables entran juntas a un Isolation Forest; ventana anómala
si **`score_samples < −0,569397`** (= `decision_function < −0,069397`), umbral único (percentil
α = 0,05). No hay corte por variable. El modelo detecta lo sin regla; los heurísticos dan la acción
precisa en los patrones conocidos.

## 4. Correcciones al `N1-tabla-decision-limit-block.md` previo

1. **Umbral del modelo:** decía `−0,5689` (θ del modelo **contaminado** `if_recalibrado_2026_09`).
   El desplegado es **`if_limpio_2026_10`** → **`score_samples < −0,569397`**. Actualizar.
2. **Reversión de LIMIT:** "se levanta solo al bajar la actividad" es impreciso. Real: **timeout de
   300 s** (`escalada.TIMEOUT_LIMIT_S`) y efecto nft `limit rate over 100/second drop`. Se re-publica
   mientras persista la anomalía; expira 300 s después del último disparo.

(El resto del N1 previo es correcto: definiciones de LIMIT/BLOCK, combinación por severidad,
umbrales heurísticos, y que la acción se aplica en el host, no en el sensor.)
</content>
