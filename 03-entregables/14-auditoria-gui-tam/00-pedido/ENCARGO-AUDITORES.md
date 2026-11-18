# Encargo para los agentes auditores (opencode · openai/gpt-6.1-sol)

Eres auditor de **solo lectura** de la GUI de CyberFlow (panel web de un IDS híbrido: Isolation
Forest + heurísticos, con respuesta LIMIT/BLOCK distribuida por un feed firmado a agentes nftables).
La auditoría prepara la **validación externa con el modelo TAM**. El pedido completo del asesor
está en `00-pedido/PEDIDO-TAM-21oct.txt` (misma carpeta que este archivo, un nivel arriba). Léelo entero.

## Reglas

1. **No modifiques ningún archivo** salvo tu archivo de salida. No ejecutes servicios, no hagas git,
   no instales nada, no te conectes a ningún host.
2. Cada hallazgo debe citar el código: `archivo:línea` (rutas relativas a la carpeta `CYBERFLOW`).
3. No inventes: si algo no se puede saber leyendo el código (p. ej., qué devuelve el sensor en vivo),
   márcalo **«A VERIFICAR EN VIVO»** y di qué habría que mirar. El coordinador lo comprobará.
4. Distingue: **ya resuelto** (el código ya cumple), **parcial**, **pendiente**. El pedido es del
   21-oct y el código ha cambiado desde entonces.
5. Español. Sin relleno.

## Código a auditar (ruta base: carpeta `CYBERFLOW`)

- `producto-main/scripts/engine/dashboard.py` (~8 400 líneas). El HTML/CSS/JS va dentro de la
  cadena Python `HTML = """..."""`. Secciones: `id="s-salud"` (≈934), `s-topologia` (943),
  `s-despliegue` (987), `s-variables` (994), `s-vivo` (1019), `s-modelo` (1046), `s-comparacion`
  (1081), `s-alcance` (1123), `s-simulacion` (1134), `s-aprendizaje` (1300), `s-scores` (1322),
  `s-actividad` (1331), `s-alertas` (1367), `s-bloqueos` (1379), `s-decisiones` (1399).
  Endpoints en `do_GET` (≈8093): `/api/status`, `/api/decisions`, `/api/activity`,
  `/api/acciones`, `/api/score-histogram`, `/api/despliegue`, etc.
- `producto-main/scripts/engine/vista_vivo.py`, `producto-main/tests/test_dashboard_*.py`.
- Contexto vigente (para detectar textos/umbrales viejos): modelo `if_limpio_2026_10`,
  umbral `score_samples < −0,569397` (decision_function < −0,069397), FPR prueba 4,53 % (IF offline),
  heurísticos `VERSION_UMBRALES 2026-10-06.2`. Valores **históricos** que no deben presentarse como
  vigentes: `if_recalibrado_2026_09`, θ −0,568892, FPR 4,45 %, ablación 6/9·7/9·9/9.

## Formato de salida (obligatorio)

Un archivo Markdown con una tabla por bloque y una fila por tarea:

| ID | Ruta GUI | Estado actual (con `archivo:línea`) | Cambio propuesto | Aceptación | Estado | Prioridad |

- **ID**: el del pedido + correlativo (`UP1-01`, `FU2-03`, `COR-ALERTAS-01`, `IU1-01`…).
- **Ruta GUI**: navegación del usuario, p. ej. `Menú → Vigilancia → Decisiones → filtros`.
- **Estado**: resuelto / parcial / pendiente / A VERIFICAR EN VIVO.
- **Prioridad**: P1 (corrige un mensaje que lleva a conclusión equivocada), P2 (función que la
  evaluación necesita), P3 (mejora).
- Al final: «Orden de implementación sugerido» (encaja con el orden 1–6 del pedido) y
  «Riesgos» (qué cambio podría romper otra vista o las pruebas `test_dashboard_gui_contract.py`).
