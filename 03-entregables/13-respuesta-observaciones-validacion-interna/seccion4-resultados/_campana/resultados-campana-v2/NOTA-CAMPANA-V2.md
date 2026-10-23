# Campaña v2 (NS=1) — validación del escaneo limpio (2026-10-23 19:35–20:07 UTC)

Orquestador `orquestar_campana_v2.sh` (escaneo primero con volumen, DNS×3, flood×3, brute×1, nikto×1).
Modelo limpio + heurísticos 2026-10-06.2. Evidencia: `marcas.jsonl`, `motor_slice.jsonl`,
`analisis/Tabla8-campana-sin-solape.md`.

## Tabla 8 (atribución sin solape)
| Familia | Episodios | IF solo | Heurísticos | Híbrido |
|---|---:|---:|---:|---:|
| DNS | 3 | 0/3 | **3/3** (`dns_entropy`) | 3/3 |
| Escaneo | 1 | 0/1 | **1/1** (`port_scan`, t1≈30 s) | 1/1 |
| Flood | 3 | 0/3 | 0/3 | 0/3 |
| Fuerza bruta | 1 | 0/1 | 0/1 | 0/1 |

## Lo que valida y lo que no (honesto)
- ✅ **Escaneo detectado** por `port_scan` cuando corre **primero (camino abierto) y con volumen**
  (`-p1-5000 --min-rate 2000`, 18 s). Resuelve el "inconcluso" del replay del PCAP anterior (donde el
  escaneo quedó con tráfico mínimo).
- ✅ **DNS 3/3** (`dns_entropy`).
- ⚠️ **Flood 0/3 y brute 0/1 — regresión de esta corrida**, no del detector: el `curl --max-time 2`
  que se añadió para evitar que el enforcement alargara los episodios **estranguló el volumen HTTP**
  por debajo de los umbrales (`http_abuse` ≥100 req/60s; `brute_force` ≥5 req/60s con ≥80 % de fallo).
  En la campaña principal (sin ese timeout) **sí** dispararon `http_abuse` (3/3) y `brute_force` (BLOCK).
- **IF solo 0/10:** el modelo no alertó en ninguna ventana del atacante (débil solo; coherente con 4.1).

## Fix para la corrida completa N≥3
- Flood sin `--max-time 2` (o `--max-time 5` y más peticiones) para asegurar ≥100 req/60s.
- Brute: quitar el `--max-time 2` agresivo; mantener el endpoint 401 respondiendo.
- Escaneo: mantener `-p1-5000 --min-rate 2000`, primero (funciona).
- Captura ≥2000 s para cubrir también Nikto (en v2 Nikto a las 20:05 quedó fuera del PCAP de 1700 s).

## Síntesis de las dos corridas (ninguna capturó las 4 limpias a la vez)
- **Principal:** flood (`http_abuse`) 3/3 y brute (`brute_force`→BLOCK, corte real) ✓; escaneo inconcluso.
- **v2:** escaneo (`port_scan`) ✓ y DNS ✓; flood/brute estrangulados por el timeout.
→ **Las cuatro familias son detectables por el híbrido**; para la Tabla 8 final de publicación conviene
una corrida con el fix de flood/brute de arriba.
</content>
