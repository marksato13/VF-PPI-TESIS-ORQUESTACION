# Cierre técnico de la Etapa 3 (2 de noviembre de 2026)

**Objetivo de la Etapa 3:** detectar y aplicar una respuesta efectiva mientras el ataque sigue activo, sin restringir injustificadamente a usuarios legítimos.

Este cierre resuelve los tres hallazgos abiertos de `../etapa3-deteccion-temprana-2026-11-02/`, que se conserva sin cambios salvo la corrección de redacción del §5. Todo se hizo en el portátil y en el banco aislado.

> **Ningún cambio en el laboratorio.** No hubo despliegue, reinicios ni enforcement. No se lanzaron campañas. No cambiaron el modelo, los umbrales ni el Word, y no se intervino en piloto-con-dns. El código está en la rama `candidato/etapa3-20261102` y **no** se fusionó en `main`, que sigue siendo `7b275b8`, lo desplegado.

## Estado de los tres hallazgos

| # | Hallazgo | Archivos y pruebas | Banco | Sensor1 |
|---|---|---|---|---|
| 1 | `detector_rapido.py --flujo` no emitía la ráfaga recibida en una sola escritura mientras la tubería seguía abierta (select + búfer) | **Resuelto.** La regresión falla en `585da7b` y pasa corregida | Repetida la alternativa C: 60/60 aplicadas antes del último SYN | **Pendiente:** que la unidad emita en vivo (procedimiento, paso 1) |
| 2 | `auth_failure_heuristic` bloqueaba o renovaba con HTTP tardío | **Resuelto.** 3 de 5 pruebas fallan en `585da7b`, incluido el recorrido motor → feed firmado | Replay del 3B: −36 decisiones finales, IF puro idéntico, feed 66 → 58 | **Pendiente:** campos `decision_if` y `auth_failure` en el registro en vivo |
| 3 | Captura de la vía rápida con las VLAN del espejo sin validar | **Resuelto.** Filtro `tcp or (vlan and tcp)` y prueba de coherencia unidad = banco | Muestras con y sin etiqueta, fuera de línea y en vivo; SYN/SYN-ACK/RST y deduplicación iguales a la referencia; batería con VLAN 30/30 | **Pendiente:** libpcap de Sensor1, `tcpdump -d` y captura en vivo de SYN etiquetados |

Además:

- **DNS:** las dos cifras se separan: atacante 734/1 044 (≈ 70,3 %) y legítimos 0/428. La segunda es favorable, pero **no aprueba el límite**. Queda un protocolo de 7 días con el criterio fijado antes de medir, y TCP/53 como hueco declarado con una propuesta de evaluación.
- **«392 restricciones»:** se corrige la redacción. Eran ventanas de decisión con disparo heurístico, no restricciones.

## Qué hay en esta carpeta

| Documento | Contenido |
|---|---|
| [INFORME-HALLAZGOS.md](INFORME-HALLAZGOS.md) | Problema, causa, cambio, evidencia y resultado de cada hallazgo; DNS y «392» |
| [COMPARACION-REFERENCIA.md](COMPARACION-REFERENCIA.md) | Banco (por tramos, con y sin VLAN) y replay del 3B frente a la referencia: IF puro, 25 episodios, población, control y feed |
| [MATRIZ.md](MATRIZ.md) | Cada punto del encargo: estado, evidencia y lo que falta |
| [PROTOCOLO-OBSERVACION-DNS.md](PROTOCOLO-OBSERVACION-DNS.md) | Observación pasiva de varios días, criterio previo y TCP/53 |
| [PROCEDIMIENTO-ETAPA4.md](PROCEDIMIENTO-ETAPA4.md) | Instalación en sombra, comprobaciones y reversión. **No ejecutado** |
| [DEPENDENCIAS-Y-COMANDOS.md](DEPENDENCIAS-Y-COMANDOS.md) | Commits, entornos y los comandos ejecutados |
| `resultados/` | Salidas sin editar: pruebas, VLAN, baterías, replay y análisis, comparaciones y ensayo DNS |
| `guiones/` | Los guiones que produjeron `resultados/`, el generador del manifiesto y la verificación contra GitHub |
| `MANIFIESTO.sha256` | sha256 de cada fichero, con el texto en LF tal como lo publica git |

## Qué es medido, qué es banco y qué falta

- **Medido en archivos** (replay del 3B, mismas entradas): IF puro, scores y vectores idénticos; 36 decisiones finales que dejan de ser `auth_failure_heuristic`; población principal 15/25 y control sin cambios.
- **Ensayado en el banco** (Docker sin red; tcpdump 4.99.5, libpcap 1.10.5, kernel 6.18 de WSL2):
  - regresiones en Linux con la versión anterior y la corregida;
  - captura con VLAN;
  - 60 ejecuciones de la alternativa C.

  Son **los mismos 5 escaneos** del 3B reinyectados: comparan versiones, no confirman de forma independiente.
- **Pendiente en Sensor1** (Etapa 4, en sombra, con autorización): ver [MATRIZ.md](MATRIZ.md) §3.

## 4. Ensayo de la herramienta DNS sobre el tramo del 3B

`observacion_dns.py` sobre el EVE del 3B, excluido el atacante 10.10.20.30 (`resultados/dns/observacion-3b-ensayo.json`):

- 17 orígenes;
- 4 046 consultas UDP/53 y 0 TCP/53;
- 10 286 copias del espejo descartadas;
- 0 descartes simulados con (30/minuto, ráfaga 18), y ningún aviso P2.

**Solo comprueba que la herramienta funciona.** Es un tramo de un día con campañas en curso, no cumple P3 y **no aprueba el límite**.

## Respuesta del cierre

- **Los tres hallazgos quedan resueltos** en código, pruebas y banco.
- **Ninguno está comprobado aún en Sensor1.** Lo que falta para empezar la Etapa 4 en sombra está en [MATRIZ.md](MATRIZ.md) §3 y en el paso 0 de [PROCEDIMIENTO-ETAPA4.md](PROCEDIMIENTO-ETAPA4.md).
