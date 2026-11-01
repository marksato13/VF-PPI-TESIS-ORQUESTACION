# Diseño de la validación independiente (Etapas 2 a 5)

**Principio:** los registros anteriores (paso 2, 3A, 3B y su revisión) sirven para **desarrollo** —diagnosticar, dimensionar y probar offline—, pero **no como prueba independiente**. Una candidata ajustada con ellos y evaluada sobre ellos se validaría a sí misma.

La prueba se hace con:

1. **tráfico normal nuevo**, capturado después de congelar la candidata;
2. una **campaña A** (sombra) nueva con la candidata congelada;
3. la **campaña B** (respuesta).

Los criterios de [OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) se congelan **antes** del paso 1, con D1–D8 resueltas.

**Reglas generales de todas las etapas:**

- **No se cambian criterios para aprobar.** Si una condición de salida no se cumple, la etapa no sale, y se documenta. Un cambio de criterio exige versión nueva, fechada y publicada **antes** de los datos a los que se aplica.
- **Fallo del experimento ≠ fallo del detector** ([OBJETIVOS-Y-CRITERIOS.md](OBJETIVOS-Y-CRITERIOS.md) §6). Un fallo del experimento se repite con un identificador nuevo y no borra el original. Un fallo del detector cuenta.
- **Ningún despliegue, sudo ni cambio en un host sin decisión de Mark.** Los comandos con sudo los prepara Claude y los ejecuta Mark.

---

## Etapa 2 · Corregir la captura y la cadena

**Objetivo:**

- bajar los descartes que excluyeron 9/25 episodios;
- instrumentar t_pub, t_apl y t_efecto;
- medir el presupuesto de la cadena con los cambios.

| | Contenido |
|---|---|
| Entrada | Etapa 1 publicada; D7 (agente y contadores) y la parte de D5 que afecta al procedimiento, decididas por Mark; motor `24f8a80` como base |
| Trabajo | (1) Causa de los `kernel_drops` de Suricata: af-packet (ring, hilos), CPU y su correlación con las inundaciones. **Ajustar af-packet es decisión de Mark.** (2) Rotación o lectura incremental del PCAP, conservando la regla de «paquetes decodificados». (3) Ciclo por eventos (inotify) y cadena publicador → relé → agente por eventos. (4) Registro de t_pub, t_apl (hora y retorno del commit, lote, lectura del set) y `counter` en las reglas. (5) Corregir `--umbrales` del servicio y el comentario de `relay-feed.sh`. |
| Pruebas | Offline sobre los PCAP del 3B: el replay debe reproducir **las 28 características** y las decisiones. Repetición en sombra con tráfico normal **sin ataques** para medir los descartes. |
| Salida | (a) 0 `kernel_drops` y 0 descartes de tcpdump en un control normal de ≥ 30 min al ritmo de los perfiles, **y** en una inundación HTTP de prueba en sombra. (b) Presupuesto E–I medido por episodio, con la cota del peor caso publicada. (c) t_apl registrado con precisión ≤ 0,1 s en una prueba en un host de laboratorio. |
| Parada | Un cambio rompe la equivalencia del replay; un descarte persiste sin causa identificada; aparece un riesgo para la red (afecta a otra VLAN o a la gestión) |
| Reversión | Cada cambio de servicio con su unidad anterior respaldada y el procedimiento de vuelta probado. Las mismas pautas que el paso 1/2: commit candidato en rama, hashes antes y después. |

## Etapa 3 · Mejorar los heurísticos

**Objetivo:** que las familias tengan una señal **correcta y temprana**.

| | Contenido |
|---|---|
| Entrada | Etapa 2 cerrada (fuente C0 disponible); D2 y D3 decididas |
| Trabajo | (1) **Escaneo breve:** decisión con evidencia parcial (umbral de ráfaga evaluado en cuanto se supera) y sin usar la IP del generador. (2) **Atribución DNS:** `dns_entropy` dispara 88 veces sobre el resolvedor 10.10.10.20, que *reenvía* consultas: la regla debe atribuir al cliente que origina la consulta, no al resolvedor. (3) **Separación del abuso HTTP:** la inundación HTTP produce `port_scan` → BLOCK (en las 5 repeticiones, a los 112–117 s) y, en un escaneo, `brute_force` mal atribuido (breve r1, sostenido r3). (4) La acción del IF según D3. |
| Pruebas offline | Sobre los registros del 3B y anteriores (**desarrollo**): sensibilidad por familia y falsas alarmas en el control del 3B. Una prueba de regresión por cada error de atribución citado. Comparación de las 28 características. **Ninguna cifra de esta prueba se presenta como validación.** |
| Salida | Cada mejora con su prueba de regresión; la candidata identificada por commit y hash de cada fichero; los umbrales nuevos **fijados por escrito** |
| Parada | Una mejora solo funciona si se usa la IP, los horarios o los identificadores del generador; o empeora otra familia en la prueba offline |
| Reversión | Rama candidata; el motor desplegado no cambia en esta etapa |

### Congelación

Al salir de la Etapa 3 se congela la **candidata**: commit, hashes, umbrales, α (si D3 mantiene el IF en la respuesta, se **elige** aquí con una regla escrita antes del tráfico nuevo) y estos criterios en una versión fechada. **Desde aquí no se toca nada hasta el final de la campaña B.**

## Etapa 4 · Validar la candidata en sombra con tráfico nuevo

| | Contenido |
|---|---|
| Entrada | Candidata congelada e instalada en sombra con el procedimiento del paso 2; D1–D8 resueltas; protocolo congelado |
| Trabajo | (1) **Control normal nuevo** de duración T, fijada por P1/P2 (≥ 2,4 h con 10 entidades legítimas para P2): M1 y M2 medidos, M3 simulado. (2) **Campaña A nueva** con la candidata: n episodios por familia según D4, orden aleatorio con semilla nueva publicada antes. (3) **Prueba del agente sin ataques**, si D7 lo autoriza: control con el agente activo para medir M3 y M4 reales. |
| Análisis | Cadena v2 (sin cambios); clases C0–C3; Q1 por familia con la cota de Clopper-Pearson; t_apl estimado con la herramienta de esta etapa, ya con t_pub medido |
| Salida | Q1 cumple la evidencia mínima en las familias con criterio definido; P1–P4 cumplen; t_apl estimado < t_fin con margen en todas las familias con punto de aplicación |
| Parada | Fallo de la fuente (C2/C3) en > 20 % de los episodios ejecutados: el problema es de captura y se vuelve a la Etapa 2. La parada es por evidencia, no por resultado. |
| Reversión | Retirar la candidata y volver al motor desplegado con el procedimiento del paso 2 |

## Etapa 5 · Campaña B (respuesta)

| | Contenido |
|---|---|
| Entrada | Etapa 4 cumplida. Agente activo en srv-dmz con contadores. Procedimiento de limpieza entre episodios (D5) **probado**. Autorización escrita de Mark para activar el bloqueo en el laboratorio. |
| Ejecución | Por episodio: (1) verificar que el estado de escalada y los sets nft del origen están vacíos; si no, el episodio es un fallo del experimento; (2) relojes; (3) ataque con `t_fin_programado` fijado; (4) registro de t_det, t_pub, t_apl y t_efecto; (5) intentos posteriores al corte (SPAN); (6) retirada verificada. Transacciones de control activas durante toda la campaña. |
| Análisis | Q2 y Q3 por familia con la evidencia mínima de D4; P1–P4 sobre los clientes. Las ventanas posteriores al corte **no** se usan para comparar detectores. |
| Salida | Criterio de éxito de cada familia cumplido y publicado con los indeterminados y los fallos del experimento |
| Parada inmediata | Cualquier BLOCK a una entidad legítima o a la gestión; una restricción que afecte a otra VLAN; un fallo del agente que deje reglas sin caducidad. En esos casos se retiran las reglas y se pasa a sombra. |
| Reversión | Desactivar el timer del agente (sudo de Mark), `nft delete table inet cyberflow` y verificar con el control |

---

## Separación de las campañas

| | Campaña A (Etapa 4) | Campaña B (Etapa 5) |
|---|---|---|
| Agente | inactivo | activo |
| Qué responde | Q1: detectores comparados, con el ataque completo visible | Q2 y Q3: aplicación y efecto |
| Ventanas tras la señal | se usan (FN, latencias, persistencia) | solo hasta t_apl, para detección; después solo para t_efecto |
| Falsas alarmas | M1 y M2 medidos, M3 simulado | M3 y M4 medidos |
| Sustituye a la otra | no | no |
