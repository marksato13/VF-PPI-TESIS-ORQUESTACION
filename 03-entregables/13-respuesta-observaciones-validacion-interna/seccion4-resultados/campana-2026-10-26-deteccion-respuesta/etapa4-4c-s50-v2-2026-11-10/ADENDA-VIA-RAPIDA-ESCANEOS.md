# Adenda: la vía rápida de escaneo y los escaneos breves de la cuarta corrida (10-nov-2026)

**Estado:** publicada en `main` el 10-nov-2026 (autorizada por Mark, DB-18). Completa `RESULTADOS-S50-V2-CUARTA-CORRIDA.md`; no lo sustituye ni cambia ninguna de sus cifras.

## 0. A qué se refiere la conclusión del informe sobre los escaneos breves
La frase del informe «el barrido breve (~5 s) casi nunca se detecta a tiempo» describe **solo las siete configuraciones de su tabla**: `IF_0,05`, `IF_0,03`, `IF_0,01`, `HEUR`, `HIB_0,05`, `HIB_0,03` y `HIB_0,01`. Las siete clasifican **ventanas de 10 s** del motor. No describe a la vía rápida, que es un detector distinto y que `s50` v2 no evalúa (ver §1). El informe se corrigió en ese sentido.

## 1. Evidencia de la vía rápida (presentada por separado)
**Qué es:** `port_scan_temprano`, parámetros K = 8, W = 2,0 s, g = 0,1 s: un detector de latencia de segundos sobre intentos de conexión a puertos distintos, separado de las decisiones por ventana. **Fuente:** `senales-rapidas.jsonl` del Sensor1 (copia de `s40`), leído en solo lectura (`evidencia/via_rapida_A.out`, `via_rapida_A.sh`). **Medida:** `emitido_en` menos la marca `inicio` del generador; relojes Kali/Sensor1 con desfase medido < 0,01 s.

| Episodio | Duración (s) | Señal rápida (s desde `inicio`) |
|---|---|---|
| escaneo_breve-r1 | 5,0 | 1,16 |
| escaneo_breve-r2 | 5,0 | 0,37 |
| escaneo_breve-r3 | 5,0 | 0,68 |
| escaneo_breve-r4 | 4,7 | 0,57 |
| escaneo_breve-r5 | 4,6 | 0,46 |
| escaneo_sostenido-r1…r5 | 52,3–52,9 | 0,23–0,25 |

- Una señal por episodio, de 10.10.20.30 a 10.10.30.10, en los 10 episodios de escaneo; ninguna en otro episodio.
- **Control:** 0 señales en el control de la A (21:23–21:53Z) y 0 en las 8 h de la 4B (`control-4b.json`, `via_rapida.senales`); 0 propuestas del publicador v2 en ambos.
- Las otras 3 de las 13 líneas del fichero corresponden, por recuento (1 + 2), a escaneos de las corridas canceladas del mismo día.

## 2. Señal temprana no es restricción aplicada
Una respuesta tiene cuatro momentos distintos; la A solo midió el primero de la vía rápida:

| Nivel | Qué es | Estado en la A (sombra) |
|---|---|---|
| 1. Señal emitida | la vía rápida escribe `senal_rapida` (`emitido_en`) | **medida** (tabla de §1) |
| 2. Propuesta | el publicador v2 convierte señales en una entrada firmada del feed | no evaluada por episodio en la A |
| 3. Restricción cargada | el agente de srv-dmz carga la regla (`t_apl`) | **no aplica**: en sombra nadie aplica |
| 4. Efecto | el destino deja de responder o la tasa baja mientras el generador sigue intentando (`t_efecto`) | **no aplica** |

Que la señal llegue a los 0,4–1,2 s **no demuestra** que una restricción se hubiera cargado a tiempo: faltan la publicación, el relé y la aplicación, de los que la A no tiene medida.

## 3. Qué no se puede afirmar
- Que la vía rápida «cumple» E1 del escaneo breve: depende de DB-12 (si `port_scan_temprano` cuenta como regla prevista) y de pasar por la misma atribución e integridad del análisis. No se ha hecho.
- Que la respuesta habría llegado antes del fin de un barrido de ~5 s (niveles 2–4).
- Una tasa de falsos disparos de la vía rápida más allá de «0 en 8 h 30 min de control».

## 4. Consecuencia
Para el escaneo breve (n = 1 en la población principal), la A respalda dos cosas por separado: «las siete configuraciones por ventana llegan tarde» y «la vía rápida emitió en 5/5 a ≤ 1,2 s». La pregunta real (¿se aplica la restricción antes del fin del barrido?) es de la Campaña B.
