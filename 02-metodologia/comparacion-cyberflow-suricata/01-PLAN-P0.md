# Plan P0

## Resultado que debe producir P0

Un experimento reproducible que ejecute los mismos episodios de ataque contra el
mismo servidor y permita comparar la primera deteccion de CyberFlow y Suricata.

## Tabla priorizada

| ID | Tarea | Dependencia | Criterio de salida | Estado |
|---|---|---|---|---|
| P0-01 | Aprobar pregunta e hipotesis | Este documento | Pregunta y hipotesis firmadas | Pendiente |
| P0-02 | Confirmar host y conexion virtual del comparador | Capturas ESXi | Mismo host `172.17.25.2` y adaptador 2 conectado a `PG-CYBERFLOW-SPAN` en ambas VMs | Verificado por capturas; ver nota 05 |
| P0-03 | Validar la recepcion por el PG compartido | P0-02 | PROMISC continuo, trafico VLAN 20/30 y equivalencia de captura/drops comprobados | Parcial: PROMISC y RX continuo verificados; VLAN 20/30 y equivalencia de PCAP pendientes |
| P0-04 | Instalar y fijar Suricata en la VM comparadora | Captura pasiva estable y bundle verificado | `suricata -T` correcto; version y reglas registradas | Hecho: Suricata 7.0.3 y ET Open SHA congelados, 53013 firmas cargadas; piloto pasivo con EVE valido, servicio detenido al final |
| P0-05 | Sincronizar relojes | — | Tiempo común para comparar detección | **No bloqueante para P0:** el replay de PCAP usa el timestamp del paquete como reloj común (nota `19`). NTP/pfSense solo haría falta para el run en vivo opcional. |
| P0-06 | Definir ataques y episodios | P0-01 | Cada episodio tiene ID, origen, destino, duracion e intensidad | **Parcial:** familias definidas (nota `21`); umbrales **justificados por la línea base** (nota `24`) para DNS; faltan cifras de ataque de E1/E2/E4 |
| P0-07 | Definir eventos comparables | P0-05 | Regla clara para primera alerta y deteccion por ventana | Pendiente |
| P0-08 | Definir metricas y formulas | P0-07 | Manifiesto de analisis versionado | Pendiente |
| P0-09 | Ejecutar piloto de un episodio | P0-02 a P0-08 | Ambos sistemas registran el mismo episodio | **Hecho (E3-dns-01, nota `23`):** CyberFlow-modelo detecta ~131 s; Suricata 0 alertas; heurístico `dns_entropy` no dispara por bug de features |
| P0-10 | Ejecutar campana formal | Piloto aprobado | Logs, PCAP, EVE y decisiones preservados | **Parcial (N=3, nota `26`):** 9 episodios automatizados; falta N mayor y E2-brute |
| P0-11 | Analizar resultados | P0-10 | Tabla comparativa con intervalos y limitaciones | Pendiente |
| P0-12 | Actualizar metodologia y resultados | P0-11 | Trazabilidad requisito -> prueba -> resultado | Pendiente |

## P0-01 · Pregunta e hipótesis (propuesta para firmar)

**Pregunta de investigación.** Ante los mismos ataques controlados y la misma
línea base, ¿detecta CyberFlow (basado en comportamiento) los comportamientos
anómalos **antes** y con **menos falsos negativos** que Suricata (basado en
firmas), en particular los ataques **sin firma disponible**?

**Hipótesis (H1).** El desempeño difiere **según la familia de ataque**:
- Suricata detecta antes y mejor lo **cubierto por una firma** (ET Open).
- CyberFlow detecta **desviaciones conductuales sin firma** (p. ej. DNS de alta
  entropía / DGA, o volúmenes que superan la línea base) donde Suricata no alerta.

**Hipótesis nula (H0).** No hay diferencia medible en tiempo de detección ni en
TPR/FPR entre ambos, por familia de ataque.

**Alcance.** La afirmación es de **detección temprana**, no de predicción completa
ni (en P0) de bloqueo inline. "Mejor" se reporta siempre con **métrica + familia +
escenario** (ver `03-METRICAS-Y-EVIDENCIAS.md`); nunca como promedio único.

*(Firmar con el asesor antes de P0-06. Esto cierra P0-01.)*

## Siguiente paso operativo (actualizado: vía replay, nota `19`)

El camino crítico ya no es el NTP sino el **replay de PCAP** (nota `19`), que da
input idéntico y reloj común sin tocar pfSense. Orden:

1. **Firmar P0-01** (pregunta/hipótesis de arriba) con el asesor.
2. **Construir el scorer por ventana** (variante de `puntuar_deteccion.py` que
   conserve `window_end_utc` y marque la primera alerta). Único componente nuevo.
3. **P0-06:** definir 3-4 familias de ataque con intensidad **justificada** (MITRE
   ATT&CK + literatura + línea base medida: pps/ancho de banda/tamaño de paquete).
4. **P0-09 (piloto):** un episodio → `episodio-<id>.pcap` → Suricata `-r` +
   CyberFlow offline → primera alerta de cada uno contra `t_inicio` del PCAP.

No se necesitan VLAN, segundo SPAN, ni NTP/pfSense para P0. El run en vivo por
SPAN queda como confirmación secundaria.

## Restricciones

- No lanzar la Kali sin autorizacion expresa para la campana.
- No cambiar el modelo desplegado en Sensor1 durante el piloto actual.
- No activar bloqueo real.
- No tocar pfSense o CORE-STACK como parte de P0 sin aprobacion.
- No usar contrasenas en scripts, documentos o commits.
