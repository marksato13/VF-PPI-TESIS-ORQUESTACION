# 4.4 · A — Reconciliación del despliegue (qué ejecuta de verdad la versión actual)

**Revisión:** 2026-10-23 · **Modelo:** `if_limpio_2026_10` · Verificado por lectura del
proceso `ppi-motor`, los units de systemd y el código en `producto-main` (`fa9e5b0`). Sin tocar
el sistema. Resuelve las contradicciones entre documentos de fechas distintas (regla del encargo).

## 1. Modelo y umbral activos (verificado en el proceso vivo)

- Detector `if_limpio_2026_10`; artefacto desplegado
  `/home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib`.
- Umbral: **`score_samples < −0,569397`** (= `decision_function < −0,069397`). En el log del motor
  aparece `threshold: −0,5693969936322356`.
- `--step-seconds 10 --history-seconds 230`; `--entity-network 10.10.0.0/16`;
  `--excluir 10.10.60.11/32,10.10.10.30/32`; `--excluir-protocolos 112,240`.

## 2. Decisión del motor (lo que de verdad escribe el log)

`motor_decision.py` escribe `decision` ∈ **{ALERT, PERMIT}** (no LIMIT/BLOCK):
- `score < threshold` (con paquetes L3/L4) → `ALERT` (`motor_decision.py:566-567`).
- Ventana sin paquetes → `PERMIT`, salvo que un heurístico dispare, en cuyo caso se **escala a
  ALERT** (`:574-592`).
- Cada línea lleva además `heuristico` (dict o `null`), `score`, `threshold`, `window_end_utc`,
  `logged_at`. **El modelo NO se degrada**: `decision`/`score`/`threshold` quedan intactos; la
  traducción a LIMIT/BLOCK la hace el publicador.

## 3. Versión de heurísticos (y una discrepancia real del unit)

- Código vigente: `heuristicos.py` **`VERSION_UMBRALES = 2026-10-06.2`** (`fa9e5b0`): `brute_force`→
  BLOCK, `port_scan`→BLOCK (con rama OR de ráfaga ≥200/30s y ≤10 % completadas), `http_abuse`→LIMIT,
  `dns_entropy`→LIMIT. Umbrales de unicidad a 0,45 por el espejo SPAN.
- **Discrepancia (menor, documentada):** el unit `ppi-publicar-feed.service` pasa `--umbrales
  2026-10-06.1` (obsoleto). El código **lo ignora** y etiqueta el feed con la versión del propio
  código (`2026-10-06.2`), avisando por stderr (`publicar_feed.py:110-123`). ⇒ el feed se publica
  **bien etiquetado `.2`**; el argumento viejo solo genera un AVISO. (Acción opcional: corregir el
  arg del unit para que no avise; no cambia el comportamiento.)

## 4. Publicador del feed (sensor)

`publicar_feed.py` (timer `ppi-publicar-feed.timer`, **cada 10 s**, verificado): lee los últimos
`--ventana-segundos 120` del `motor_decision.log`, agrega por IP el veredicto **más severo**, aplica
la escalera de caducidad y firma el feed (ed25519):
- **Modelo** `ALERT` (detector no `*_heuristic`) → **LIMIT** (anomalía: degradar).
- **Heurístico** → la acción de su regla (BLOCK/LIMIT); `*_heuristic` legacy → BLOCK.
  (`publicar_feed.py:42-65`). Una anomalía **solo-modelo sí** produce un LIMIT en el feed.
- Nunca-bloquear (se omiten siempre): bastión `10.10.10.30`, sensor `10.10.60.11`, gateways
  `10.10.{20,30,40,60}.1`, DNS/AD `10.10.10.20`.
- Escribe `feed.json` + `feed.sig` + estado de escalera (`/home/m4rk/feed/…`).

## 5. Relay y agente del host (pull, un-feed/N-agentes)

`agente_enforce.py` corre en **cada host protegido** (no en el sensor); trae el feed + firma, verifica
ed25519 y sincroniza su propio nftables:
- **Fail-safe:** firma inválida o feed ilegible → **no toca nada** (conserva reglas) (`:195-201`).
- Tabla aislada `inet cyberflow`, cadena `entrada` (hook input, priority −10, **policy accept**): solo
  cae lo que esté en los sets; nunca bloquea otra cosa (`:97-112`).
- **BLOCK** (`set cyberflow_bloqueados`): `drop` de todo el tráfico de la IP.
- **LIMIT** (`set cyberflow_limitados`): `limit rate over 100/second drop` → **solo cae lo que
  EXCEDE 100/s** (`LIMIT_RATE = "100/second"`, `:39`, `:107-111`). LIMIT **no** corta la conexión.
- Mismo conjunto nunca-bloquear que el publicador (`:40-44`).
- Eleva privilegio solo en `nft` (`sudo -n nft`), mínimo privilegio (`:186-189`).

## 6. Caducidad, reincidencia y reversión (`escalada.py`)

- **LIMIT → 300 s** (plano, no escala, reversible).
- **BLOCK**: 1º → **300 s**; 2º (<24 h) → **1800 s**; 3º+ → **3600 s** (tope automático) + marca de
  **revisión humana**. **Nunca `∞` automático.**
- Decaimiento: sin reincidir en **24 h**, el contador se reinicia (la próxima ofensa vuelve a 300 s).
- "Mismo episodio" (evento ≤120 s del anterior) **no** incrementa el contador.
- **Caducidad ejecutada por el `timeout` NATIVO de nftables** → la regla se retira sola aunque el
  agente muera (`agente_enforce.py:94-96`, `:138-140`).

## 7. Comportamiento cuando una IP deja de aparecer en el feed

Los sets **no se vacían** en cada pasada: si una decisión sale de la ventana de publicación, la
entrada **permanece hasta su `timeout` firmado** y expira sola (`agente_enforce.py:81-96`). Es decir,
salir del feed **no** retira la acción de inmediato; la autoridad de retirada es el timeout nativo.

## 8. Prioridad BLOCK vs LIMIT (sin downgrade automático)

- Por IP se aplica la acción **más severa** (BLOCK > LIMIT), tanto en el publicador como en el agente.
- Un **LIMIT posterior no revoca un BLOCK** vivo en el kernel: no hay downgrade automático; la
  sanción fuerte termina **por timeout o por retiro humano** (`agente_enforce.py:120-137`). Al subir
  a BLOCK, la IP se quita del set LIMIT.

## 9. Cadencias y desfases (lo vigente)

- Motor: ventana/paso **10 s** (`--step-seconds 10`). Feed: timer **cada 10 s** (verificado). Agente:
  pull en el host (cadencia a confirmar con t3 en la campaña).
- Documentado como **cadena de 10 s escalonada (:00/:03/:06)** y **41,4 s** extremo a extremo (N3,
  17-oct). **Supera** la narrativa vieja de "~2 min" (timers de 60 s del 14-oct): esa cifra es
  **histórica** y no debe usarse para la versión actual.
- Relojes NTP cerrados en VLAN 60 → para restar marcas **entre máquinas** hay que medir el desfase
  (ver runbook de la campaña); la detección por replay no lo necesita.

## 10. Discrepancias cerradas

| Tema | Doc viejo | Vigente (verificado) |
|---|---|---|
| Tiempo de respuesta | ~2 min (timers 60 s, 14-oct) | **41,4 s** extremo a extremo (cadena 10 s, N3) |
| Versión de umbrales del feed | `--umbrales 2026-10-06.1` en el unit | feed etiquetado **`2026-10-06.2`** (gana el código) |
| Degradación del modelo | — | el modelo **no** se degrada; LIMIT/BLOCK se derivan en el feed |
| Retiro al salir del feed | (ambiguo) | **no inmediato**: expira por timeout nativo de nftables |
| Modelo → acción | (ambiguo) | modelo `ALERT` → **LIMIT**; heurístico → su regla |

## Pendiente (lo aporta la campaña, 4.4 B–E)

Ensayos completos post-despliegue limpio con los sellos t0–t5 por ensayo (LIMIT por anomalía del IF,
BLOCK por heurístico, caducidad/reversión verificadas), y la figura de 3 paneles
(decisión / feed firmado / nft del host). La duración de inferencia con reloj monótono **no la
registra hoy el motor** → "no medido" salvo instrumentación aparte.
</content>
