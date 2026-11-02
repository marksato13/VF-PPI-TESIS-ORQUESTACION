# DNS: atribución al cliente y política del LIMIT

Datos: EVE del 3B (`eve-segmento.json`, 07:24–10:06 UTC, 27 908 eventos DNS). Son datos de **desarrollo**: el mismo día que se usa para ajustar no sirve de confirmación independiente.

## 1. Qué pasaba

| Hecho medido | Cifra |
|---|---|
| Ventanas con `dns_entropy` sobre DC1 (10.10.10.20) en el replay de referencia | 382 (casi todas fuera de los episodios) |
| Ventanas sobre un cliente legítimo (10.10.20.22) | 4 |
| Ventanas sobre la Kali en `dns_inusual` | 72 |
| Consultas que salen de DC1 hacia su servidor superior (10.10.10.1) | 2 981 |
| …de ellas, **reenvíos** de una consulta de cliente (mismo nombre y tipo en los 2 s anteriores) | 2 946 (98,8 %) |
| …de ellas, con NXDOMAIN | 2 901 |
| Respuestas de DC1 a los clientes con NXDOMAIN | 0 (contesta NOERROR) |
| Copias del espejo SPAN descartadas (misma consulta en VLAN de origen y de destino, < 5 ms) | 10 286 |

**Conclusión.** La NXDOMAIN la recibía DC1 al reenviar; el cliente recibía NOERROR. Por eso la regla veía a DC1 como «el que pregunta nombres inexistentes». Además, la doble copia del espejo duplicaba la cuenta: 10.10.20.22, con 19 consultas reales en 60 s y subdominios hexadecimales (tráfico legítimo confundible del generador), llegaba a 36–38 y pasaba el umbral de 20.

## 2. Cambio: vista DNS de los heurísticos

`scripts/engine/dns_heuristica.py` (`VistaDns`, versión 2026-11-02.1). **No toca las 28 entradas del IF.**

- Deduplica las copias del espejo: misma consulta o respuesta (flujo, id, nombre, tipo, rcode) en menos de 5 ms. Los **reintentos** (> 5 ms) sí cuentan, porque son tráfico nuevo en el cable.
- En un resolvedor interno (DC1, DC2) marca como **reenvío** cada consulta hacia fuera cuyo (nombre, tipo) preguntó un cliente a un resolvedor en los 2 s anteriores. La regla solo cuenta las **propias**. El resolvedor **no** se excluye: sus consultas propias siguen contando y sus filas del IF no cambian.
- La NXDOMAIN se atribuye a quien preguntó en **ese** flujo, como hace el extractor.
- Es causal: el reenvío siempre es posterior a la consulta del cliente, y todo lo usado tiene marca ≤ fin de ventana.
- El motor alimenta la vista con las mismas líneas del EVE (`motor_decision.py`) y entrega a los heurísticos una **copia** de la fila con los campos `dnsh_*`. La fila que puntúa el IF no cambia. Cada decisión registra `dns_vista`.
- `dns_entropy` solo lee la vista. Sin ella **no dispara**: no se vuelve en silencio a las características del IF.

## 3. Umbral, con margen y sensibilidad

Peor cliente legítimo en la vista: **19 consultas/60 s** (10.10.20.26). Consultas propias de DC1: como máximo 4 por ventana. La Kali en `dns_inusual` llega a 140 por ventana, con nombres 100 % únicos.

Sensibilidad (`resultados/dns/dns-heuristica-3b.json`), con NXDOMAIN ≥ 0,5 o nombres únicos ≥ u:

| Consultas ≥ | Episodios detectados (de 5) | Antes del fin | Ventanas legítimas | 1.ª ventana desde el inicio (s): r1, r2, r3, r4, r5 |
|---|---|---|---|---|
| 20 | 5 | 5 | 0 | 10,9 · 10,0 · 14,9 · 17,4 · 16,0 |
| 25 | 5 | 5 | 0 | 10,9 · 20,0 · 14,9 · 17,4 · 16,0 |
| **30** | **5** | **5** | **0** | **20,9 · 20,0 · 14,9 · 17,4 · 16,0** |
| 40 | 5 | 5 | 0 | 20,9 · 20,0 · 24,9 · 17,4 · 26,0 |
| 50 | 5 | 5 | 0 | 30,9 · 30,0 · 24,9 · 27,4 · 26,0 |
| 60 | 5 | 5 | 0 | 30,9 · 30,0 · 34,9 · 27,4 · 26,0 |

El orden de la columna de tiempos sigue el de los episodios (r1–r5). El umbral de nombres únicos (0,45 / 0,8 / 0,9) no cambia nada en estos datos: manda la cuenta.

Regla vigente (características del IF con copias): primera ventana a 4,9–10,9 s, pero con 382 + 4 ventanas sobre legítimos.

**Elegido: 30 consultas propias/60 s y (NXDOMAIN ≥ 0,5 o nombres únicos ≥ 0,8).** Es 1,6 veces el peor legítimo y deja la detección a 15–21 s del inicio, con más de 69 s de actividad restante en los cinco episodios. Con 20 el margen sobre el legítimo sería de una consulta. **Limitación:** un solo día del mismo laboratorio; el umbral se revisa con más días de tráfico.

## 4. Política del LIMIT de DNS

El LIMIT de 5 paquetes/s con ráfaga 10 **no recorta** el escenario (unas 2,3 consultas/s). No se convierte en BLOCK.

**Unidad: consulta UDP/53 por origen.** En UDP, una consulta es un paquete y los reintentos cuentan. En TCP, una consulta son varios paquetes: no se limita (en el 3B hubo 0 consultas DNS por TCP hacia los resolvedores) y lo cubre el BLOCK. Esto queda declarado como **hueco**: un atacante podría pasar a TCP.

**Método** (`scripts/etapa3/politica_limit_dns.py`). Para cada origen legítimo se calcula la envolvente de cubeta de fichas: la ráfaga mínima b(r) con la que una cubeta (r, b) **no descartaría ninguna** de sus consultas. Después se simula la cubeta sobre las consultas reales del atacante.

| Tasa r (consultas/s) | b mínima del peor legítimo | b elegida (2 × legítimo) | Consultas del atacante descartadas mientras está limitado (simulado) |
|---|---|---|---|
| 0,25 | 8,98 | 18 | 77,8 % |
| **0,5** | **8,97** | **18** | **67,6 %** |
| 1,0 | 8,94 | 18 | 46,9 % |
| 2,0 | 8,87 | 18 | 5,4 % |
| 3,0 | 8,81 | 18 | 0 % |

La envolvente legítima (b ≈ 9) la marcan hosts de VLAN 50/60 que lanzan 9 consultas en un segundo, probablemente al arrancar un servicio.

**Candidata: 30/minuto (0,5/s), ráfaga 18, solo UDP/53** (`scripts/enforce/cf_nft_helper.py`, `TASA["dns"]`, `RAFAGA["dns"]`, `FILTRO_LIMIT["dns"]`). Un legítimo limitado por error no perdería ninguna consulta. Al origen del escenario se le descarta alrededor del 68 % **mientras está limitado**.

**Lo que no se sabe:**

- Qué hace la herramienta del atacante ante el descarte. `dig +tries=1` no reintenta, pero otra herramienta podría hacerlo, y eso aumenta los paquetes.
- El efecto real sobre la exfiltración: se mide en la campaña B.

**Ensayo en el banco** (`deploy/pruebas-aisladas/ensayo_limit_dns.py`; `resultados/dns/limit-dns/`):

- **Montaje:**
  - veth con la IP de DC1 y el helper **real** con perfil `dns`;
  - todos los orígenes de cada segmento en `limitados` desde el principio (el atacante y los legítimos, como si se hubieran limitado por error); el helper rechaza DC1 y DC2 (`NUNCA`);
  - segmentos de los 5 `dns_inusual` (inicio − 60 s a fin + 60 s) con solo las consultas UDP/53 hacia DC1, sin VLAN y sin copias del espejo (`scripts/etapa3/segmento_dns_dc1.py`), reproducidos a velocidad original.

| Episodio | Atacante: enviadas / descartadas | Legítimos limitados | Legítimos: enviadas / descartadas |
|---|---|---|---|
| r1 | 210 / 148 (70,5 %) | 9 | 98 / 0 |
| r2 | 207 / 145 (70,0 %) | 9 | 94 / 0 |
| r3 | 209 / 147 (70,3 %) | 6 | 62 / 0 |
| r4 | 208 / 146 (70,2 %) | 8 | 94 / 0 |
| r5 | 210 / 148 (70,5 %) | 6 | 80 / 0 |
| **Total** | **1 044 / 734 (70,3 %)** | — | **428 / 0** |

La regla nft que quedó cargada es la del texto del helper: `udp dport 53 ip saddr @limitados … limit rate over 30/minute burst 18 packets … drop`. El resultado coincide con la simulación de cubeta (67,6 % sobre 1 080 consultas: estas incluyen las resoluciones inversas de los escaneos, fuera de los segmentos). Un replay no reintenta, así que la reacción de `dig` u otra herramienta al descarte sigue siendo desconocida.

**No está aprobada.** Falta la medida de varios días de tasas legítimas por origen (R-E2 de la Etapa 2); el banco usa los legítimos de 5 ventanas de unos 3,5 min.

## 5. Pruebas

`tests/test_etapa3_dns.py` (12 pruebas): copias del espejo; reintento ≠ copia; reenvío excluido y su NXDOMAIN fuera; consultas propias del resolvedor siguen contando; causalidad (la consulta del resolvedor anterior a la del cliente es propia); otro tipo ≠ reenvío; ventana (A − 60, A] y poda; líneas no DNS; sin vista no dispara; DGA frente al legítimo hexadecimal; umbral justo; texto nft del LIMIT (solo UDP, 30/minute, ráfaga 18; el BLOCK sigue cubriendo TCP).
