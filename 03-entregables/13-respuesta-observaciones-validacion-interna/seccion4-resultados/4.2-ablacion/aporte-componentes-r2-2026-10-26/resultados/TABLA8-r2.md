# Tabla 8 r2 — detección durante la ejecución (generada por evaluar_r2.py)

Celda: episodios con señal de 10.10.20.30 en una ventana evaluable con window_end entre el inicio y el
fin del generador, sobre los episodios cuyas ventanas durante el ataque son **todas** evaluables.

## Principal: replay con historia real

| Familia | Episodios evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |
|---|---|---|---|---|---|---|
| DNS inusual (alta entropia) | 0 de 3 | — | — | — | — | — |
| Inundacion HTTP | 0 de 3 | — | — | — | — | — |
| Escaneo de puertos | 0 de 3 | — | — | — | — | — |
| **Total** | **0 de 9** | — | — | — | — | — |
| Fuerza bruta HTTP | 0 (no ejecutada) | — | — | — | — | — |

## Sensibilidad: filas del acumulador en vivo (extractor del 05-oct + acotación exacta)

| Familia | Episodios evaluables | IF 0,05 | IF 0,03 | Heurísticos | Híbrido 0,05 | Híbrido 0,03 |
|---|---|---|---|---|---|---|
| DNS inusual (alta entropia) | 3 de 3 | 2/3 | 0/3 | 3/3 | 3/3 | 3/3 |
| Inundacion HTTP | 3 de 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| Escaneo de puertos | 3 de 3 | 1/3 | 1/3 | 1/3 | 1/3 | 1/3 |
| **Total** | **9 de 9** | **6/9** | **4/9** | **7/9** | **7/9** | **7/9** |
| Fuerza bruta HTTP | 0 (no ejecutada) | — | — | — | — | — |

La tabla combinada replay + acumulador **no se publica**: el acumulador no es equivalente al
replay en todas las ventanas comunes (`equivalencia-acumulador.json`).

## Categoría por episodio y configuración

D durante, P posterior (≤ 60 s tras el fin), N sin detección, NE no evaluable. Entre paréntesis, window_end
de la primera señal menos el inicio del generador (no es el instante de emisión).

| Fuente | Episodio | IF 0,05 | IF 0,03 | Heur. | Híb. 0,05 | Híb. 0,03 |
|---|---|---|---|---|---|---|
| replay | e3-r1 | NE | NE | D (62.5 s) | D (62.5 s) | D (62.5 s) |
| replay | e3-r2 | NE | NE | D (48.2 s) | D (48.2 s) | D (48.2 s) |
| replay | e3-r3 | NE | NE | D (43.6 s) | D (43.6 s) | D (43.6 s) |
| replay | e4-r1 | D (49 s) | D (49 s) | D (49 s) | D (49 s) | D (49 s) |
| replay | e4-r2 | D (53.9 s) | D (53.9 s) | D (53.9 s) | D (53.9 s) | D (53.9 s) |
| replay | e4-r3 | D (58.1 s) | D (58.1 s) | D (58.1 s) | D (58.1 s) | D (58.1 s) |
| replay | e1-r1 | NE | NE | NE | NE | NE |
| replay | e1-r2 | NE (señal parcial) | NE | NE (señal parcial) | NE (señal parcial) | NE (señal parcial) |
| replay | e1-r3 | NE | NE | NE | NE | NE |
| acumulador | e3-r1 | N | N | D (12.5 s) | D (12.5 s) | D (12.5 s) |
| acumulador | e3-r2 | D (58.2 s) | N | D (8.2 s) | D (8.2 s) | D (8.2 s) |
| acumulador | e3-r3 | D (33.6 s) | N | D (13.6 s) | D (13.6 s) | D (13.6 s) |
| acumulador | e4-r1 | D (9 s) | D (9 s) | D (9 s) | D (9 s) | D (9 s) |
| acumulador | e4-r2 | D (3.9 s) | D (3.9 s) | D (13.9 s) | D (3.9 s) | D (3.9 s) |
| acumulador | e4-r3 | D (8.1 s) | D (8.1 s) | D (18.1 s) | D (8.1 s) | D (8.1 s) |
| acumulador | e1-r1 | P (22.5 s) | P (22.5 s) | P (22.5 s) | P (22.5 s) | P (22.5 s) |
| acumulador | e1-r2 | D (20.5 s) | D (20.5 s) | D (20.5 s) | D (20.5 s) | D (20.5 s) |
| acumulador | e1-r3 | P (22.2 s) | P (22.2 s) | P (22.2 s) | P (22.2 s) | P (22.2 s) |
