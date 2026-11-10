# D3: los cuatro escaneos breves sin anclas de la Kali (10-nov-2026)

**Decisión de Mark (10-nov):** conservar la regla de cobertura y documentar aparte estos cuatro episodios. La regla **no se ha tocado**.

## Qué ocurre
`escaneo_breve-r1`, `-r2`, `-r3` y `-r5` quedan **fuera de la población principal** únicamente por el requisito `cobertura_durante` de la integridad («durante incompleta»); los otros once requisitos de cada uno están verificados (pcap, eve, decisiones, características, cobertura previa/posterior, continuidad, sin faltantes, captura sin errores, reinicios, relojes). En la cobertura de `analizar.cobertura`: `anclas_ataque_esperadas = 0` y `observadas = 0` → «faltan 0 de 0 anclas de la Kali durante el ataque», y la regla actual devuelve `suficiente = false` cuando no hay ninguna ancla esperada. El motor sí fue continuo en los cuatro (`motor_continuo = true`; hueco máximo del motor 15,0 s en r3, 11,0 s en r1, 10,8 s en r2 y 10,4 s en r5).

| Episodio | Duración (s) | Anclas esperadas / observadas | `durante_completa` | En población principal |
|---|---|---|---|---|
| escaneo_breve-r1 | 5,0 | 0 / 0 | no | no |
| escaneo_breve-r2 | 5,0 | 0 / 0 | no | no |
| escaneo_breve-r3 | 5,0 | 0 / 0 | no | no |
| **escaneo_breve-r4** | 4,7 | **1 / 1** | **sí** | **sí** |
| escaneo_breve-r5 | 4,6 | 0 / 0 | no | no |

## Causa probable (a confirmar por Mark; no cambia ninguna regla)
Con `nmap -sT -n -T4 --max-retries 1 -p 1-1000 10.10.30.10` el barrido dura unos 5 s (en la corrida 2, sin `-n`, duraba 18 s por la resolución DNS). Las anclas de la Kali son marcas periódicas dentro del ataque; con un episodio tan corto, en r4 cayó una y en los otros cuatro ninguna. No es una pérdida de datos: no se esperaba ancla alguna, pero la regla trata «0 esperadas» como insuficiente. Este efecto es consecuencia del cambio `nmap -n` (autorizado el 9-nov) y no existía con episodios de 18 s.

## Cómo se tratan
- Los cuatro se **conservan visibles** como **exploratorios** (no entran en la población principal ni en sus recuentos): el resultado por configuración figura en `RESULTADOS-S50-V2-CUARTA-CORRIDA.md`.
- Consecuencia para la comparación: la familia **escaneo breve tiene n = 1** en la población principal (r4). Cualquier afirmación sobre escaneo breve debe declararlo; con n = 1 no se puede estimar tasa alguna.
- Revisar la regla «0 anclas esperadas» sería un cambio de criterio y queda a decisión de Mark; no se ha hecho ni se hará sin su orden.
