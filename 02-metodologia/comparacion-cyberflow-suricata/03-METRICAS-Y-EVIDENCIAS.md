# Metricas y evidencias

## Metricas primarias

| Grupo | Metrica | Formula o definicion |
|---|---|---|
| Deteccion | TPR | episodios detectados / episodios ejecutados |
| Deteccion | FPR | ventanas normales alertadas / ventanas normales |
| Deteccion | Falsos negativos | episodios sin alerta / episodios ejecutados |
| Rapidez | Tiempo de deteccion | `t_primera_alerta - t_inicio_ataque` |
| Rapidez | Tiempo de decision | `t_decision - t_inicio_ataque` |
| Respuesta | Tiempo de bloqueo | `t_bloqueo - t_primera_alerta` |
| Trafico | Paquetes por segundo | paquetes observados / duracion |
| Trafico | Bytes por segundo | bytes observados / duracion |
| Operacion | Perdida de paquetes | drops de captura y paquetes recibidos |
| Operacion | Recursos | CPU, memoria y carga de cada VM |

## Unidad de analisis

La unidad primaria sera el **episodio de ataque**. Las ventanas de CyberFlow y
las alertas de Suricata se agregaran al episodio usando un ID comun, origen,
destino, hora de inicio y hora de fin.

## Artefactos obligatorios por episodio

- PCAP o referencia de captura.
- `eve.json` de Suricata comparador.
- Log de decisiones de CyberFlow.
- Registro de inicio y fin del ataque.
- Version de reglas Suricata.
- Commit y hash del producto.
- Configuracion y manifiesto del modelo.
- CPU, memoria y drops de ambos receptores.
- Resultado JSON/CSV y hash.

## Reglas de interpretacion

- Una alerta no equivale automaticamente a un bloqueo.
- No se comparara una regla Suricata inexistente contra una capacidad que CyberFlow
  no tenia disponible sin reportarlo.
- Los resultados se separaran por familia de ataque.
- Las ventanas relacionadas no se trataran como observaciones independientes sin
  advertencia estadistica.
- La conclusion no usara "mejor" sin indicar la metrica y el escenario.
