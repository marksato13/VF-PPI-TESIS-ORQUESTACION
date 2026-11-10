# Adenda: la vía rápida de escaneo en la cuarta corrida (10-nov-2026)

**Estado:** adenda LOCAL, no publicada. Completa `RESULTADOS-S50-V2-CUARTA-CORRIDA.md`, no lo sustituye. Los números salen de `senales-rapidas.jsonl` del Sensor1 (copia de `s40`), leído en solo lectura (`evidencia/via_rapida_A.out`, `via_rapida_A.sh`).

## Qué faltaba en el informe
Las siete configuraciones comparadas (`IF_α`, `HEUR`, `HIB_α`) son decisiones por **ventana de 10 s** del motor. La **vía rápida** (`port_scan_temprano`, parámetros K = 8, W = 2,0 s, g = 0,1 s) es un detector aparte, de latencia de segundos, que `s50` v2 no evalúa ni cuenta como regla prevista (DB-12 sigue abierta). El informe dice que el escaneo breve «casi nunca se detecta a tiempo con ninguna configuración»: eso es cierto **solo para las siete configuraciones por ventana**; no describe a la vía rápida.

## Qué observó la vía rápida
Una señal `port_scan_temprano` por episodio, de 10.10.20.30 a 10.10.30.10, en los 10 episodios de escaneo; ninguna fuera de ellos:

| Episodio | Duración (s) | Señal rápida (s desde `inicio` del generador) |
|---|---|---|
| escaneo_breve-r1 | 5,0 | 1,16 |
| escaneo_breve-r2 | 5,0 | 0,37 |
| escaneo_breve-r3 | 5,0 | 0,68 |
| escaneo_breve-r4 | 4,7 | 0,57 |
| escaneo_breve-r5 | 4,6 | 0,46 |
| escaneo_sostenido-r1…r5 | 52,3–52,9 | 0,23–0,25 |

- **Control:** 0 señales rápidas en el control de la A (21:23–21:53Z) y 0 en las 8 h de la 4B (`control-4b.json`, `via_rapida.senales`). 0 propuestas del publicador v2 en ambos.
- Las otras 3 de las 13 líneas del fichero son escaneos de las corridas canceladas del mismo día (2.ª y 3.ª; por recuento 1 + 2).
- **Incertidumbre temporal:** tiempos = `emitido_en` − marca `inicio` del generador (relojes Kali/Sensor1 con desfase medido < 0,01 s); orden de magnitud 1 s, muy por debajo de los 4,6–5 s del escaneo breve.

## Qué NO se puede afirmar
- Que la vía rápida «cumple» E1 del escaneo breve: eso requiere decidir DB-12 (si `port_scan_temprano` cuenta como la regla prevista) y pasar por la misma cadena de atribución e integridad del análisis. No se ha hecho.
- Que la respuesta habría llegado a tiempo: en sombra nadie aplica (E2/E3 son de la Campaña B). La señal llega a ~0,4–1,2 s; falta sumar publicación, relé y aplicación (`t_pub`, `t_relay`, `t_apl`), de los que la A no tiene medida.
- Una tasa de falsos disparos de la vía rápida más allá de «0 en 8 h 30 min de control».

## Consecuencia
Para el escaneo breve (n = 1 en la población principal), la A solo respalda «las siete configuraciones por ventana llegan tarde» y «la vía rápida emitió en 5/5 a ≤ 1,2 s». La pregunta real (¿se aplica la restricción antes del fin de un barrido de ~5 s?) queda para la Campaña B.
