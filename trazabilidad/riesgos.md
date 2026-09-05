# Riesgos

| ID | Riesgo | Impacto | Estado | Mitigación |
|---|---|---|---|---|
| `RISK-001` | El FPR operativo (25,81 %) hace el sistema inviable para operación desatendida | **Crítico** | **Materializado y medido** | Recalibrar con tráfico pesado como normalidad — `P-1`, 10 oct |
| `RISK-002` | La selección posterior del modelo invalida la estimación de desempeño | **Crítico** | **Materializado y declarado** | Jornada nueva no observada — `P-2`, 24 oct |
| `RISK-003` | Sin validación con usuarios, el eje de pertinencia queda en cero | Alto | Abierto | Sesión SUS de 2 h — `P-3`, 9 sep |
| `RISK-004` | La partición mide repetición, no generalización | Alto | Abierto | Misma campaña que `RISK-002` |
| `RISK-005` | Documentos que envejecen respecto a los artefactos | Medio | **Materializado 2 veces** | Verificador de consistencia + auditoría cruzada |
| `RISK-006` | Un `.docx` desincronizado de su `.md` | Medio | **Materializado** | Comprobar que el Word se genera desde el Markdown |
| `RISK-007` | Artefactos no deterministas entre ejecuciones | Medio | **Materializado y corregido** | Ordenar todo `set` antes de iterarlo |
| `RISK-008` | El plazo de la revista se pasa y sube el APC | Bajo | Abierto | Envío el 28 sep, 3 días de margen |
| `RISK-009` | La orquestación consume el tiempo de la tesis | Medio | Abierto | Pasos 1–4 dan valor; 5–12 son opcionales |
| `RISK-010` | Duplicar información entre repositorios | Medio | Prevenido | Aquí solo referencias con hash |
