# Limitación del generador para E3 de la inundación HTTP, y evidencia que haría falta (11-nov-2026)

**Estado: documento de análisis. No cambia ningún criterio ni ningún veredicto.** El criterio E3 fijado el 11-nov (`CRITERIO-E3-FIJADO-NUEVA-CORRIDA.md`) y los veredictos de **B2** (E3 inundación = indeterminado 2/2, I2) y de **B3** (E3 inundación = indeterminado 2/2, I2; E3 fuerza bruta = cumple 2/2) se conservan tal cual.

## Qué se midió en B3 (episodios `inundacion_http-r4` y `-r3`, regla `limitados` aplicada a +18,7 s y +17,6 s)
| Magnitud | `inundacion_http-r4` | `inundacion_http-r3` |
|---|---|---|
| Conexiones aceptadas por s (SPAN), 10 s antes → después de la regla | 311,6 → 32,6 (**−89,5 %**) | 312,2 → 32,6 (**−89,6 %**) |
| SYN de la Kali por s (SPAN), B0 → después | 311,6 → 38,2 | 312,2 → 37,9 |
| Iteraciones del generador por s (salida con hora), antes → después | 155,6 → 16,5 | 155,9 → 16,5 |
| Iteraciones con respuesta del servidor, después | 16,1/s | 16,2/s |
| Latencia media de una iteración, después | 0,48 s | 0,48 s |
| Umbral de continuidad (0,5 × B0): SPAN / salida | 155,8 / 78,0 por s | 156,1 / 78,0 por s |
| Resultado E3 | **indeterminado (I2: ni SPAN ni salida)** | **indeterminado (I2)** |

El efecto es real (las aceptadas bajan ≈ 90 %), pero **no se puede afirmar** porque el criterio exige además demostrar que el generador *siguió intentando* con al menos el 50 % de su ritmo previo, y ni el SPAN (≈ 12 % del B0) ni la salida con hora (≈ 11 % del B0) lo alcanzan.

## Por qué el generador no puede cumplirlo (causa, no una avería)
El comando de la inundación (`esquema_campana.comando_de`, sin cambios en B3 salvo el registro) es un **bucle síncrono**: 8 lazos paralelos, cada uno `curl --max-time 2` y a continuación el siguiente `curl`. Cada lazo no emite el intento n+1 hasta que termina el n. Por eso **el ritmo de intentos depende de la latencia de la respuesta**: sin limitación, una iteración tarda ≈ 0,05 s (≈ 156 it/s con 8 lazos); con la regla `limit rate over 100/second`, las iteraciones tardan 0,48 s de media y el ritmo cae a ≈ 16 it/s, casi exactamente en proporción a la reducción de aceptadas. Es decir, **el ritmo de intentos de este generador cae *a causa* del efecto que se quiere medir**: la condición «siguió intentando ≥ 50 % de B0» y la condición «las aceptadas bajaron ≥ 50 %» no pueden cumplirse a la vez con una carga de bucle cerrado. Lo midió B2 (38 SYN/s frente a 156 requeridos) y lo confirma B3 con la salida con hora (que fue la vía añadida precisamente para esto: **no resolvió el problema**, porque la limitación está en la forma de la carga, no en el instrumento).

La instrumentación de B3 sí funcionó: la salida con hora y el SPAN son coherentes entre sí (≈ 156 it/s antes frente a ≈ 312 SYN/s en el SPAN, es decir ≈ 2 SYN por iteración; ese factor 2 no se ha explicado ni verificado) y la v2 del script costó −1,7 % de carga frente al original medido en loopback.

## Qué evidencia haría falta para resolverlo en una corrida futura
Ninguna de estas opciones se aplica retroactivamente ni a B3; cada una requiere una decisión **antes** de la corrida y un cambio de criterio o de generador declarado de antemano.
1. **Generador de bucle abierto (carga ofrecida fija).** Un emisor que lance intentos a **tasa constante** (p. ej. 300/s con `--max-time` corto y sin esperar la respuesta para el siguiente), de modo que lo ofrecido no dependa de la latencia. Con eso «siguió intentando ≥ 50 % de B0» pasa a ser verdad por construcción mientras corra el generador, y E3 mide solo el efecto (aceptadas ≤ 50 % de B0). Evidencia a aportar: registro por intento con hora de **emisión** (no solo de fin), prueba en banco de que la tasa ofrecida es independiente de la latencia (con y sin limitación), y medición de que el generador no satura a la Kali (CPU, descriptores).
2. **Medir la oferta en la red, no en la respuesta:** SYN *salientes* de la Kali por bloque de 1 s desde un SPAN **del lado de la Kali** (o contadores de `tc`/`nft` en la Kali), que cuentan intentos aunque el servidor no conteste. Hoy el SPAN es del lado del servidor/espejo y los SYN contados dependen de las retransmisiones y del cierre de conexiones; evidencia necesaria: un punto de captura de la salida de la Kali verificado por separado.
3. **Redefinir la continuidad (decisión de criterio, no de herramienta):** sustituir «≥ 0,5 × B0 de intentos» por «el generador está activo y emite ≥ N intentos por bloque (valor absoluto, como ya hace BLOCK con ≥ 1)». Es lo que ya se acordó para BLOCK, pero para LIMIT cambiaría el significado del criterio; debe fijarlo Mark antes de lanzar y no se aplica a B2/B3.
4. **Evidencia complementaria sin cambiar el criterio:** publicar junto al veredicto la serie conjunta (aceptadas, SYN y iteraciones por bloque de 1 s) y la latencia por iteración, que muestran que el efecto es del orden del 90 % y que la caída de intentos es consecuencia del límite. Es evidencia, no un veredicto.

## Lo que NO se afirma
- No se afirma que la regla limitara el tráfico «verificado» (E3 sigue indeterminado): la relación entre la caída de intentos y la limitación es una explicación de la causa con los datos de B3, no una demostración de E3 con el criterio vigente.
- No se reinterpretan B2 ni B3.

Fuentes: `corrida-2026-11-11\analisis\resultado-b3.json`, `cf-b3\cf-b3-kali\intentos\intentos-inundacion_http-r{3,4}.tsv`, `instrumentacion\analizar_b_instrumentado.py` (`e3_v2`, 23 pruebas).
