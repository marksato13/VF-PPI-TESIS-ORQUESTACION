# Comparación de ventanas al reducir α (IF limpio, validación sin Kali)

Columna FP/TP = falsas alarmas por detección correcta (FP÷TP); **no es «fiabilidad»** y **no** es
criterio único de selección. Si TP=0 queda indefinida.

**Limitación (datos de este conjunto):** el fichero de ataques (`scores-ataques-84.csv.gz`) solo trae
`campaign_id, entity_ip, window_end_utc, score_samples` (84 ventanas, todas de `10.10.20.30`). **No** incluye
etiqueta de escenario ni de episodio, así que aquí se identifican las ventanas por su **clave original** y su
`window_end_utc`, pero **no** se puede comprobar cobertura por episodio ni detección durante el ataque: perder
una ventana **no** equivale a perder un ataque completo. Esa comprobación queda pendiente de la campaña A.

## α = 0,010 → α = 0,008
- FP evitados: **106** (567 → 461).
- TP perdidos: **18** (50 → 32).
- FP/TP: 11.34 → 14.406.
- Ventanas de ataque que dejan de detectarse (18):
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:12:30+00:00` (score -0.626666)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:12:40+00:00` (score -0.625830)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:12:50+00:00` (score -0.625237)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:13:00+00:00` (score -0.625237)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:13:10+00:00` (score -0.624912)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:13:20+00:00` (score -0.624912)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:13:30+00:00` (score -0.624912)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:13:40+00:00` (score -0.624106)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:13:50+00:00` (score -0.624292)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:31:10+00:00` (score -0.626835)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:31:20+00:00` (score -0.625830)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:31:30+00:00` (score -0.625237)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:31:40+00:00` (score -0.625237)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:31:50+00:00` (score -0.625237)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:32:00+00:00` (score -0.624912)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:32:10+00:00` (score -0.624912)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:32:20+00:00` (score -0.624546)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:32:30+00:00` (score -0.624106)

## α = 0,008 → α = 0,005
- FP evitados: **182** (461 → 279).
- TP perdidos: **6** (32 → 26).
- FP/TP: 14.406 → 10.731.
- Ventanas de ataque que dejan de detectarse (6):
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:33:50+00:00` (score -0.634855)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:34:00+00:00` (score -0.632087)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:34:40+00:00` (score -0.633330)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:34:50+00:00` (score -0.637599)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:35:20+00:00` (score -0.634837)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:35:30+00:00` (score -0.637158)

## α = 0,030 → α = 0,010
- FP evitados: **1156** (1723 → 567).
- TP perdidos: **4** (54 → 50).
- FP/TP: 31.907 → 11.34.
- Ventanas de ataque que dejan de detectarse (4):
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:32:40+00:00` (score -0.590856)
  - `piloto-con-dns|10.10.20.30|2026-09-30T00:35:40+00:00` (score -0.605225)
  - `piloto-con-dns|10.10.20.30|2026-09-30T01:27:40+00:00` (score -0.611440)
  - `piloto-con-dns|10.10.20.30|2026-09-30T01:28:10+00:00` (score -0.598140)

