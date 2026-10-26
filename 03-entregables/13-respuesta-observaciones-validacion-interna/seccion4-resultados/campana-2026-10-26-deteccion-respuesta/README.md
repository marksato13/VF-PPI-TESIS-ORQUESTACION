# Campaña nueva — detección (4.2) y respuesta (4.4)

**Fase actual: preparación. No se ha ejecutado ningún ataque.** La campaña A se autoriza en la siguiente instrucción.

Carpeta independiente: no modifica `../4.2-ablacion/aporte-componentes-r2-2026-10-26/` ni ninguna evaluación anterior.

| Archivo | Contenido |
|---|---|
| `PLAN-CAMPANA.md` | Plan: separación A (detección, sombra) / B (respuesta, aplicar), historia y registros, marcas temporales, criterios de evaluación, verificación de respuesta, bloqueos |
| `config-campana.json` | Configuración **congelada y registrada antes de ejecutar**: IF y escalador con sha256, 28 características, umbrales verificados, commits/blobs/sha256 del código, lógica de combinación, escenarios, repeticiones, semilla, emitidas vs derivadas |
| `COMPROBACIONES-PREVIAS.md` | Comprobaciones benignas del 26-oct (resultados) y los 6 bloqueos que requieren intervención humana, con comandos etiquetados |
| `escenarios/FICHAS-ESCENARIOS.md` · `escenarios/escenarios.json` | Ficha por escenario y parámetros legibles por máquina |
| `scripts/generar_campana.py` | Generador (Kali). **Seguro por defecto:** simula si no se pasa `--autorizado`; aborta fuera de la lista blanca. Escribe `marcas.jsonl` (pared + monotónico) |
| `scripts/capturar.sh` | PCAP continuo sin huecos (sensor) |
| `scripts/comprobar_relojes.sh` | Desfase NTP por host, antes y después |
| `scripts/modo_sombra.sh` · `scripts/restaurar_enforcement.sh` | Pasar el enforcement a sombra para A y restaurarlo para B (imprimen el procedimiento; no aplican) |
| `scripts/endpoint_brute_prueba.md` | Preparación reproducible del endpoint 401 de fuerza bruta |
| `scripts/analizar.py` | Esqueleto del análisis posterior; reutiliza la lógica de `evaluar_r2.py` |
| `evidencia-precheck/` | Salida cruda de las comprobaciones y los scripts que las produjeron |
| `MANIFIESTO-CAMPANA.json` | sha256 de todos los archivos de esta carpeta, commit y enlace |

## Estado en una línea

Preparado: plan, configuración congelada, fichas, scripts (validados en seco) y comprobaciones. **Seis bloqueos**
pendientes de intervención humana antes de la campaña A (NTP del sensor, modo sombra, zona DNS de laboratorio, endpoint
de fuerza bruta, captura continua/disco y encender la Kali). Ninguno se resuelve en esta fase. Detalle en
`COMPROBACIONES-PREVIAS.md` §1–6.
