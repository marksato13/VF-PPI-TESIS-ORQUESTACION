# Auditoría funcional del panel actual — Playwright, 12-oct-2026

**Alcance:** lectura de `producto-as-deployed` en HEAD `bfe7e40`, ejecución de `dashboard.py --demo` en localhost y Chromium headless con Playwright Python. No se modificaron código ni servicios. Complementa `AUDITORIA-GUI-2026-10-12.md`, que examinó la versión anterior `473e758`; G1–G7 ya fueron implementados en commits posteriores y **no se reabren** por defecto.

**Límite:** VM-GESTION aparecía offline en Tailscale durante la prueba. No se pudo comprobar el panel vivo autenticado ni las cuentas `admin`/`lector`. Las conclusiones de navegador se refieren al modo demo local y a código estático; no representan una medición del Sensor1.

## Lo comprobado

- Chromium 153 en viewport 1440×900: `GET /` 200, banner de demo visible, detector `if_recalibrado_2026_09` mostrado como IsolationForest, APIs sin respuestas >=400 en esta sesión; sin errores de consola, `pageerror` ni fallos de red, incluido al menos un ciclo de polling de cinco segundos.
- Modo desarrollo: las **siete vistas** (`Red y captura`, `Operacional`, `Decisión`, `Respuesta`, `Construcción y entrenamiento`, `Fases del método`, `Validación`) cambian y renderizan nodos/detalle. El visor de archivos abrió un script permitido de 31 131 caracteres; el tour inició. El test local `test_dashboard_gui_contract.py` cubre además parser JS servido y rechazo de ruta fuera de whitelist.
- A 390×844, `visualViewport.width=390` pero el documento se ensancha a **574 px**; el navegador reduce la interfaz para encajarla. El menú horizontal de la barra mide aproximadamente 975 px y expande su contenedor.
- Reproducción sintética aislada: una ventana `PERMIT` del modelo con heurístico `dns_entropy`→`LIMIT` da `compute_counters`: `limit=1`, `alert_model=0`, `alert_auth_heuristic=0`. `renderHealthbar()` con esos contadores y servicios activos muestra **«Todo operando con normalidad»** y **«sin alertas reales»**. Esta combinación puede ocultar una acción efectiva del sistema.
- Tests existentes del repo: 10 pruebas `test_dashboard*.py` y 10 de `test_alertas_panel.py` pasaron en Windows; el test de contadores comprueba BLOCK/LIMIT pero no la semántica de la barra de salud.

## Correcciones propuestas, priorizadas

| Prioridad | Hallazgo y ubicación | Corrección verificable |
|---|---|---|
| **P0 — verdad operativa** | `renderHealthbar` (dashboard.py ~1303) suma solo `alert_model + alert_auth_heuristic`; `compute_counters` (~4679) sí cuenta BLOCK/LIMIT por `accion_de`, incluidos heurísticos DNS/HTTP/scan. Un LIMIT-only puede mostrar «Todo operando con normalidad». La tarjeta `Alertas reales (1h)` (~1298) también solo refleja modelo. | Separar salud de servicio de **actividad de respuesta**. Mostrar `BLOCK`, `LIMIT`, anomalías del modelo y reglas por separado. Una acción heurística debe producir mensaje «acción LIMIT/BLOCK reciente» sin llamarla alerta del modelo. Añadir fixture de heurístico solo para frontend y API; no cambiar la lógica de enforcement. |
| **P1 — móvil** | CSS `.shell`/`.side`/`.wrap` (~82–135): a 390 px el documento mide 574 px por mínimo intrínseco y navegación horizontal. Visualmente texto/KPIs se reducen. | Aplicar `min-width:0` en ítems de grid, `width:100%; box-sizing:border-box` en `.wrap` y contener el scroll horizontal dentro de `.side nav`/barra, no en el documento. Gate Playwright a 390 y 320 px: `documentElement.scrollWidth <= visualViewport.width`, controles táctiles visibles, textos legibles. |
| **P1 — fiabilidad de captura** | `renderHealthbar` (~1315) y tarjetas de captura (~1718) tratan `kernel_drops > 0` como pérdida **actual**, aunque Suricata expone contadores acumulados desde el arranque (lector de `eve.json` ~5088). | Informar el acumulado **desde arranque** y calcular delta/rate entre muestras de `medido_en`; estado rojo solo con incremento reciente. Si el evento stats está viejo o ausente, mostrar «dato no disponible/atrasado» y no «sin drops». Probar con dos muestras: contador constante vs creciente. |
| **P1 — evidencia de validación** | `VALIDACION` (~2591) es una matriz estática. Por ejemplo «Respuesta distribuida» todavía dice «falta fuerza bruta», aunque la confirmación de fuerza bruta en vivo se documentó después; el subtotal 4 cumplidos/5 parciales/0 pendientes se muestra también en demo. | Versionar/fechar la matriz con enlaces a evidencias actuales; actualizar estados solo al verificar fuente. Etiquetar «estado documental» y «demo, no medición en vivo». No derivar éxito en producción de un array de JS. |
| **P2 — frescura de datos** | `renderHealthbar` confía en servicios activos; la sección Pulso muestra edades, pero la franja principal puede decir normal aunque no haya nueva decisión/captura reciente. | Definir umbrales de frescura para último `stats` de EVE, PCAP y decisión; mostrar «sin tráfico» separadamente de «ingesta detenida». Evaluar silencio esperado de la red antes de fijar números. |

## Gates antes de despliegue

1. Corregir primero P0 con test que reproduzca `PERMIT` del modelo + heurístico `LIMIT` y `BLOCK` sin `ALERT` del modelo.
2. Repetir Playwright en demo de escritorio/móvil; verificar CSS a 390/320 px, consola y llamadas API tras polling; conservar capturas de antes/después fuera de Git si contienen datos reales.
3. Cuando vuelva VM-GESTION, comprobar que el `dashboard.py` vivo coincide con el código revisado y probar una sesión `lector` real. Sin login no se pueden validar permisos ni la experiencia externa de la demo. No colocar credenciales en el repositorio ni en chats.

Capturas de esta ejecución local: `C:\Users\markp\AppData\Local\Temp\opencode\cyberflow-demo-audit.png` y `cyberflow-demo-mobile-audit.png`. Son **capturas del demo**, no evidencias de tráfico vivo.
