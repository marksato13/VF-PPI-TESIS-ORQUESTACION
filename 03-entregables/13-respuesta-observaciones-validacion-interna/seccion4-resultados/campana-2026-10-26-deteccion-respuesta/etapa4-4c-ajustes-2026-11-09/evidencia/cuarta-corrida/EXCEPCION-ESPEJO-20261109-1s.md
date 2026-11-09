# Excepción a la prueba previa del espejo para la cuarta corrida (09-nov-2026)

**Autorizada por Mark el 09-nov (opción A), solo para la prueba previa de esta corrida.** P3, X3 y la lista blanca no se tocan.

- **Prueba:** 30 min seguidos sin segundos por debajo de 20 pkt/s en `ens37` (muestreo de 1 s en el Sensor1; registros `espejo-1s-{f,g,h}-20261109.log`). El Sensor1 se reinició a las 19:24:36Z; la prueba empezó de cero a las 19:33:22Z.
- **Cortes reales previos:** 19:42:46–19:43:02, 19:55:13–19:55:16 y 20:07:45–20:08:13Z (varios segundos a 0 pkt/s).
- **Racha posterior al último corte:** desde 20:08:14Z, más de 36 min hasta 20:44:17Z.
- **Excepción:** un único intervalo de 1 s a las **20:36:57Z (15:36:57 Perú)** con 6 pkt/s (rx_packets 1 232 252 → 1 232 258), entre vecinos de 184 y 192 pkt/s. Muestra válida: intervalos consecutivos de 1 s, contador sin retrocesos (0 en todo el registro), valor del muestreador H (el G había terminado a las 20:36:36Z).
- **Comprobaciones:** por muestreador, no hay otro intervalo < 20 pkt/s en 20:08:14–20:38:44Z (G: 0; H: solo 20:36:57). Intervalos de 2 s (muestra perdida por deriva del `sleep`): G 10, H 7, máximo 2 s; el contador es acumulado, así que no se pierde información, solo resolución. Hasta las 20:44:17Z no hubo cortes nuevos.
- **Nota de método:** una primera verificación mezcló los muestreadores solapados y mostró falsos 0 y 4 pkt/s en 20:30:30 y 20:33:24; era un artefacto de la fusión (desfase de décimas de segundo entre muestreadores), no un dato del espejo. Quedan los resultados por muestreador (`verif_excepcion2.out`).
- **No cambia:** P3 (hueco de anillo > 7 s), X3, lista blanca, criterios I1–I8. Esta excepción no se aplica a ninguna otra prueba ni corrida.
