# F7 — Deduplicación del espejo SPAN

Evidencia de la observación F7 (§3.3.2 del artículo): la deduplicación quita
copias del espejo y conserva el tráfico parecido pero legítimo.

- `f7_dedup.py` — se ejecutó en el sensor (10.10.60.11) el 23-oct-2026. Llama a
  la función real del extractor, `deduplicar_espejo` de
  `scripts/features/extract_multilayer_v3.py`, y replica su criterio para sacar
  los pares y sus diferencias. `coinciden: true` confirma que la réplica cuenta
  lo mismo que la función.
- `f7_resultado.json` — salida tal cual.

| Captura | Tramas IPv4 | Copias quitadas | ΔTTL | Δt máx. | Parecidas conservadas |
|---|---:|---:|---|---:|---:|
| `/tmp/campana-v2/pass.pcap` | 17 238 | 3 595 (20,9 %) | 1: 3 595 | 2 178 µs | 39 |
| `/tmp/campana-pcap/pass.pcap` | 9 466 | 4 738 (50,1 %) | 1: 4 729 · 0: 9 | 918 µs | 2 213 |

Criterio: misma tupla (protocolo, IP, puertos, id IP, longitud, secuencia TCP,
tipo/id ICMP), Δt ≤ 5 ms y ΔTTL ≤ 1; se conserva la copia de mayor TTL.
«Parecidas conservadas» = misma 5-tupla a ≤ 5 ms pero distinto id IP o
secuencia: no son copias y no se quitan.

La deduplicación es por paquete; no elimina ventanas por similitud.
