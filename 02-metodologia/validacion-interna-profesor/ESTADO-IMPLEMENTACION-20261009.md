# Estado de implementación — cobertura de audios

Corte: 2026-10-09. Fuente: plan por bloques de esta carpeta. **No equivale a validación del profesor**: la sesión y el despliegue vivo del panel siguen pendientes.

| Bloque | Estado | Evidencia / siguiente gate |
|---|---|---|
| B0 preflight | Cerrado | [`producto-as-deployed`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/tree/8d696e5d61d3f90b4c3c2106ea503db83ca26950) tenía HEAD `8118d7d`, cuatro commits locales previos sin publicar; `dashboard.py` vivo SHA `53499d6c...70a2ec32f` vs candidato local SHA `aa0fe58f...ac7f6d5`. Diff revisado: 277 inserciones, 22 eliminaciones (principalmente tres vistas, visor de código y las correcciones B1). |
| B1 GUI | Implementado local; **no visible en el servicio vivo** | Detector dinámico por `status.model.detector_name`, tour de tres vistas/visor/pruebas previas, ficha de artefacto desde manifiesto activo. `test_dashboard_gui_contract.py`: 4 OK, incluye `node --check` del JS servido, servidor demo, 403 de ruta no permitida y lectura de script permitido. Falta comprobación visual autenticada con roles reales en Sensor1. |
| B2 modelo/documentos | Implementado local | `docs/RECONCILIACION-MANIFIESTO-MOTOR.md` y `docs/dataset/MODEL_CARD_IF_RECALIBRADO.md`. Ficha OCSVM marcada histórica. `.toml` genérico no se cambió, para no regenerar una unidad con rutas incorrectas. |
| B3 reentrenamiento | Contrato implementado, ensayo **sintético** cerrado; real pendiente | Runbook corregido, `puntuar_deteccion.py` soporta paquete preliminar y Pipeline con verificación de hash; comparador exige evaluación pareada y falla cerrado. `test_retraining_demo.py`: 2 OK (ciclo aislado y rechazo de SHA incompatible). ANTES real existe solo en Sensor1: `ensayo-if-v2.json` SHA `ec3ed063...86421`. Falta hold-out normal **nuevo** y episodios nuevos, tabla real; sin ellos no se emite promoción. |
| B4 mapa/guion | Implementado local; validar en sesión | Mapa de los siete requisitos separa código local/vivo y test sintético/real; guion corrige FPR de distintos entornos, heurístico vs modelo y tres tiempos. Contradicción hallada: motor `VERSION_UMBRALES=2026-10-06.2`, unidad del publicador `--umbrales 2026-10-06.1`; queda por reconciliar antes de afirmar versión única. |
| B5 publicación | **Candidato preparado, NO activo** | Panel copiado a `Sensor1:/home/m4rk/cyberflow/scripts/engine/dashboard.py.candidate-audios`, SHA `aa0fe58f01d86bf1aebb5097e4c133b615d22a20c635e4bdfccd543c0ac7f6d5`, sintaxis Python validada con cache fuera del repo. `ppi-dashboard` sigue `active` sirviendo el archivo anterior. Falta QA de rol autenticado, respaldo vivo y decisión de Mark para reemplazar/reiniciar. |
| B6 sesión interna | Pendiente | Ensayo, sesión grabada y observaciones del profesor. No se lanzó Kali ni se alteró firewall, modelo o feed durante B0–B5. |
| B7 editorial/externa | Parcial, pendiente | README de SUS rotulado histórico; lista de tablas/figuras y TAM + juicio de expertos requieren el equipo de tesis y respuestas reales. |

## Verificaciones y límites

- `python -m unittest discover -s tests -p test_dashboard_gui_contract.py`: **4 OK**.
- `python -m unittest discover -s tests -p test_retraining_demo.py`: **2 OK**.
- `python -m py_compile` en los tres scripts editados y `git diff --check`: sin errores de sintaxis/espacios.
- Suite completa bajo **Windows**: 98 pruebas, **4 fallos y 3 errores** en `test_f1_dataset_builder.py` (gate de hash Git de fixtures), `test_f1_preflight.py` (Bash recibe ruta Windows), `test_storage_audit.py` (`/dev/sda` normalizado a `C:\dev\sda`). No surgieron de los módulos tocados; no se cambió la lógica de esas pruebas. Repetir la suite en entorno Linux antes de desplegar si es parte del gate CI.
- Ninguna cifra sintética del test B3 entra a los resultados de tesis. El 4,45 % normal retenido de IF no borra el FPR de F6 antiguo; 9/9 es del stack híbrido, no del modelo solo.

## Entrega reversible del panel (aún no ejecutada)

1. Mark revisa el diff y el resultado de QA; verifica que el archivo vivo sigue en SHA `53499d6c...70a2ec32f` y que el candidato sigue en `aa0fe58f...ac7f6d5`.
2. Mark acuerda desplegar el candidato. Guardar un respaldo del `dashboard.py` vivo en Sensor1, sustituir solo ese archivo, conservar propietario/permisos y pedirle a Mark el reinicio de `ppi-dashboard` con sudo. No reiniciar motor/Suricata.
3. Verificar `systemctl is-active ppi-dashboard`, HTTPS/login, vistas, tour, visor por rol y valores del detector. Si falla, restaurar el archivo anterior y reiniciar únicamente el panel.

Se mantiene el árbol de cambios **sin commit ni push**; Mark publicará cuando revise. Los cuatro commits anteriores al trabajo están preservados.
