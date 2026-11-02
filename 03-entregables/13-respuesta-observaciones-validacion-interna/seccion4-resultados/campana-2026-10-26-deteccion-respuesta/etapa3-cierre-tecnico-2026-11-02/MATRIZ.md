# Matriz del cierre técnico de la Etapa 3

Estados:

- **Resuelto:** comprobado en archivos o en el banco.
- **Declarado:** límite conocido, escrito, sin resolver en este alcance.
- **Pendiente:** requiere Sensor1 o el laboratorio, con autorización.

## 1. Puntos del encargo

| # | Punto | Estado | Evidencia |
|---|---|---|---|
| 1a | Lectura continua: procesar los bytes recibidos sin esperar a otro paquete ni al cierre | Resuelto | `detector_rapido.py` (hilo `os.read` + `AnalizadorPcapIncremental`); `test_detector_rapido_flujo.py` |
| 1b | Causalidad: no adelantar el reloj de evidencia | Resuelto | `avanzar(det.t)` solo con marcas de paquete; prueba «sin paquete posterior no hay señal» |
| 1c | Separar evidencia, disponibilidad y emisión | Resuelto | `t_evidencia`, `disponible_en`, `emitido_en`; tramos en COMPARACION §1.2 |
| 1d | Regresiones: ráfaga en una escritura, cabeceras/paquetes partidos, tráfico escaso y cierre sin espera activa, emisión sin bytes adicionales | Resuelto | 4 pruebas de proceso + 3 del analizador; en `585da7b` fallan 4 de ellas (`resultados/pruebas/`) |
| 2a | `auth_failure_heuristic` no bloquea con HTTP tardío | Resuelto | `motor_decision.py` (vista HTTP) + `publicar_feed_v2.py` (defensa en profundidad) |
| 2b | Separar la señal histórica de la autorización | Resuelto | `auth_failure = {historico, vista, autoriza}` en el registro |
| 2c | Sin tocar el modelo, el escalador, las 28 características ni los 3 α | Resuelto | 0 vectores y 0 scores distintos en 12 773 claves (COMPARACION §2.1) |
| 2d | Cambios de decisión final, separados del IF puro | Resuelto | `decision_if`; 36 cambios, todos ALERT → PERMIT, IF puro igual (COMPARACION §3) |
| 2e | Cinco pruebas, incluido el recorrido motor → feed | Resuelto | `test_auth_failure_vista.py`: 3 fallan en `585da7b` y 5 pasan corregidas |
| 3a | Comando de captura completo con muestras con y sin etiqueta | Resuelto | `ensayo_vlan_captura.py`; `resultados/vlan/` |
| 3b | SYN, SYN-ACK, RST y deduplicación | Resuelto | En vivo, 100 % con ambos filtros; deduplicación = referencia |
| 3c | Actualizar unidad, banco y procedimiento | Resuelto | `ppi-via-rapida@.service`, `ensayo_via_rapida.py` (variante con VLAN, `ip_forward=0`), PROCEDIMIENTO pasos 0 y 1 |
| 3d | No tocar switch, interfaces ni offloads del laboratorio | Cumplido | Solo banco |
| 4a | Separar 734/1 044 del atacante y 0/428 legítimos; 0/428 no aprueba | Resuelto | INFORME §4; PROTOCOLO §1 |
| 4b | Protocolo de varios días con el criterio fijado antes de medir | Resuelto (preparado) | PROTOCOLO §3 (P1/P2/P3); `observacion_dns.py` + prueba |
| 4c | TCP/53 fuera del LIMIT, con propuesta de evaluación | Declarado | PROTOCOLO §4; docstring de `politica_limit_dns.py` corregido |
| 4d | No activar nada en DC1 ni cambiar el valor | Cumplido | — |
| 5a | Pruebas que fallan en la versión anterior y pasan en la corregida | Resuelto | 7 fallan en `585da7b` y 12 pasan; suite 639 + 1 omitida |
| 5b | Repetir ensayos de la vía rápida (escaso, carga, VLAN) con tramos separados | Resuelto | 4 condiciones × 15; COMPARACION §1 |
| 5c | 25 episodios y control, con admitidos, excluidos y motivos, sin cambiar criterios | Resuelto | 0 diferencias de categoría frente a e3; 15/25; control igual (COMPARACION §2) |
| 5d | Características, scores e IF puro frente a la referencia | Resuelto | COMPARACION §2.1 |
| 5e | Las 120 ejecuciones son 5 escaneos reutilizados | Declarado | COMPARACION, cabecera; README |
| 6a | Rama candidata, sin fusionar en main | Cumplido | `candidato/etapa3-20261102` |
| 6b | Corregir «392 restricciones» | Resuelto | INFORME §5; README y VALIDACION de la Etapa 3 |
| 6c | Informe, comparación, comandos, procedimiento, matriz y manifiesto verificado | Resuelto | esta carpeta; `MANIFIESTO.sha256` + `guiones/verificar_github.sh` |
| 6d | No declarar confirmación independiente reutilizando el 3B | Cumplido | COMPARACION, cabecera |

## 2. Limitaciones declaradas

| Limitación | Consecuencia |
|---|---|
| Banco ≠ Sensor1 (libpcap 1.10.5, kernel 6.18 de WSL2, veth) | El comportamiento de la VLAN en vivo depende de la pila de Sensor1: se comprueba antes de instalar |
| Solo etiqueta simple; no hay QinQ en el laboratorio | `vlan and tcp` cubre una etiqueta dentro de la trama |
| Banco y replay usan los 5 escaneos y el tramo del 3B | Comparan versiones; no estiman ataques nuevos |
| En el banco siempre hay bytes tras la señal | La corrección 1 no mejora la latencia del banco; su efecto es en tráfico escaso (regresión) |
| Reloj «coste» del replay | Los instantes `disponible_utc` varían entre ejecuciones; las categorías no |
| TCP/53 sin limitar | Hueco declarado; propuesta en el PROTOCOLO §4 |
| DNS legítimo: un solo día observado | El LIMIT no está aprobado |

## 3. Comprobaciones pendientes para iniciar la Etapa 4 en sombra

En orden. Todas con autorización de Mark; las que piden `sudo` las ejecuta Mark.

1. **Estado del laboratorio** antes de tocar nada:
   - servicios (`ppi-motor`, `suricata`, publicador y relé);
   - commit desplegado (`7b275b8`);
   - disco y rotación;
   - que **piloto-con-dns** terminó o no se interfiere.
2. **libpcap de Sensor1:** `tcpdump --version` y `tcpdump -d 'tcp or (vlan and tcp)'`, con la rama 0x8100.
3. **Capacidades de tcpdump** en la unidad (usuario, `CAP_NET_RAW`) y la interfaz `<IFAZ>` del espejo.
4. **Instalación en sombra** de `ec78ca5` (PROCEDIMIENTO, paso 1), sin enforcement.
5. **Captura en vivo con VLAN:** la vía rápida ve SYN, SYN-ACK y RST etiquetados del tráfico normal; `kernel_drops` = 0 en su resumen y en Suricata; sin ataques, `senales-rapidas.jsonl` vacío.
6. **Registro del motor:** aparecen `decision_if` y `auth_failure`; ninguna ALERT `auth_failure_heuristic` sin `auth_failure.autoriza`.
7. **Retardo del espejo** frente al reloj de Sensor1, medido en vivo. Es la parte de «evidencia → emisión» que el banco no ve.
8. **Observación DNS de 7 días** (PROTOCOLO), en paralelo y pasiva; incluye el uso de TCP/53.
9. Solo con una autorización aparte: paso a aplicar y una **campaña nueva**, que sería la primera confirmación independiente.
