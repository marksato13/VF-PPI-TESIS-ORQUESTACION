# 33 · Protocolo de la campaña C3 (CyberFlow frente a Suricata)

**Estado:** planificada, sin ejecutar · **Sustituye a:** el plan de la nota 29 en lo que
corrige · **Evaluador:** `producto/scripts/evaluacion/comparacion.py` (rama del sensor
`9636dbd`), que ya reproduce la batería N=3 (notas 26, 28 y 31).

## Qué corrige respecto de la batería N=3

| Problema de la batería | Corrección en C3 |
|---|---|
| Precisión y F1 mezclaban episodios con ventanas | Se dejan de reportar. Detección por episodio y falsos positivos en su propia unidad |
| Suricata sin falsos positivos medidos | Se mide sobre el mismo tráfico normal: alertas por hora |
| Un solo episodio con firma (Nikto, N=1) | N=5 de Nikto |
| Sin fuerza bruta en la comparación | N=5 contra el endpoint 401 (puerto 8081 abierto en pfSense) |
| Sin control de tráfico legítimo intenso | Tráfico legítimo pesado como episodio negativo: no debe dar acción |
| La latencia arrancaba en distintos puntos | Siempre desde el lanzamiento según el orquestador (referencia) |

## Diseño

**Referencia independiente.** El orquestador escribe, para cada episodio:
- `id`, `familia`, `con_firma`;
- `t_inicio` y `t_fin` (lanzamiento y fin en la Kali, en el reloj del sensor);
- la IP atacante.

Nada de eso sale de las alertas ni de las decisiones.

**Entrada común.** Un PCAP por episodio, deduplicado, reproducido a Suricata (ET Open,
mismo ruleset que en la nota 12) y al extractor y motor de CyberFlow con el umbral y
los heurísticos congelados (versión `2026-10-06.2`).

| Familia | Con firma | N | Duración | Comando base |
|---|---|---|---|---|
| Escaneo de puertos | no | 5 | 60 s | `nmap -sT -T4 -p 1-1000 10.10.30.10` |
| DNS de alta entropía | no | 5 | 90 s | ráfaga `dig` contra **10.10.10.20** |
| Flood HTTP | no | 5 | 60 s | carga HTTP contra 10.10.30.10 |
| Fuerza bruta | no | 5 | 60 s | Basic Auth fallida contra `:8081` |
| Nikto | sí | 5 | 75 s | `nikto -h http://10.10.30.10 -maxtime 75s` |
| Legítimo intenso (control) | — | 5 | 120 s | perfiles del generador al máximo |

Entre episodios hay 5 minutos de reposo, para que caduquen las acciones y el reposo no
contamine el siguiente.

**Normal para falsos positivos.** Al menos 2 h de tráfico de los 6 perfiles sin ataques,
reproducidas igual a las cuatro condiciones:
- CyberFlow: ventanas con acción;
- Suricata: alertas por hora.

## Salida

Un `comparacion-suricata-c3.json` con el mismo formato que
`docs/evaluacion/comparacion-suricata.json`:
- una entrada por episodio con la latencia de cada condición, `null` si no detectó o `"no medido"`;
- el bloque `benigno` con los falsos positivos.

El panel lo muestra pasando `--comparacion` al servicio, y la tabla del artículo sale de
`comparacion.py --markdown`.

## Quién

- **Mark:** Kali, regla 8081 en pfSense (solo lectura para el resto), endpoint 401 en el host DMZ.
- **Claude:** orquestador sobre `22-correr-piloto.py`, replay, cálculo y nota de evidencia.
