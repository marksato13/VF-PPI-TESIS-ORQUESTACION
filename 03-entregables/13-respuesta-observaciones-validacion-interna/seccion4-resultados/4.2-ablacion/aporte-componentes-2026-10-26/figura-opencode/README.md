# Versión gráfica de la sección 4.2

Fuente: [03055893722a941449624fef19036fd08929a51f](https://github.com/marksato13/VF-PPI-TESIS-ORQUESTACION/commit/03055893722a941449624fef19036fd08929a51f); revisión gráfica nueva, separada de los datos originales.

Advertencia de trazabilidad: 15 hashes del manifiesto fuente corresponden a saltos CRLF; el commit contiene LF. La equivalencia exacta se verifica y documenta en `control.json`, sin alterar los originales. El manifiesto de estas figuras registra los hashes reales del commit.

- `componentes.png`, `.svg`, `.pdf`: matriz de nueve episodios y FPR de las cinco configuraciones sobre las 65 505 ventanas de Tabla 7. Son poblaciones distintas, indicadas en paneles separados.
- `sensibilidad.png`, `.svg`, `.pdf`: cuatro condiciones de atribución/historia sobre los mismos nueve episodios. No son nuevos experimentos ni una selección del mejor resultado.
- `previa.png`, `previa-sens.png`: renderizados PDF a 180 dpi para inspección al tamaño de inserción; `gris.png`, `gris-sens.png`: control visual en gris.
- `episodios.csv`: 45 registros utilizados, con las cuatro condiciones, primera señal, origen y destino.
- `ventanas.csv`: métricas recalculadas de las cinco configuraciones desde las predicciones completas publicadas.
- `generar.py`: auditoría y generación; `control.md`, `control.json`: verificación y límites; `MANIFIESTO.json`: commits, hashes y versiones.

## Reproducir

Se necesita el historial Git con el commit fuente y el de calibración 4.1. Bibliotecas: numpy, Matplotlib, Pillow y PyMuPDF. No se necesita SSH, PCAP, joblib ni entorno del sensor para reproducir esta imagen, porque se auditan los registros publicados, no la generación original de esos registros.

**[LAPTOP PowerShell / markp] → lo ejecuto yo**, desde `C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\4.2-ablacion\aporte-componentes-2026-10-26\figura-opencode`:

```powershell
python generar.py --solo-auditar
python generar.py
```

`--solo-auditar` no escribe archivos. Las imágenes son de 18 cm de ancho a 600 dpi; SVG/PDF vectoriales. No se toca el Word, los modelos, las reglas ni el despliegue.

## Lectura prudente

El histórico 6/9–7/9–9/9 corresponde al IF contaminado y reglas anteriores; no se representa como resultado actual. La principal reproduce la Tabla 8 offline bajo su criterio T0–fin+60 s y elegibilidad reconstruida; el complemento muestra que las detecciones dependen de esas decisiones y de la historia. Ninguna figura presenta el 9/9 como detección durante los nueve ataques o como validación independiente.

FP son señales sobre referencia normal, no bloqueos de usuarios. No se calcula ni asigna ROC-AUC/AP al híbrido. En ventanas, el híbrido no aumenta los TP y sí aumenta FP; en episodios los heurísticos cubren los mismos nueve episodios que el híbrido. El IF llega diez segundos antes que los heurísticos en HTTP-r3, dato disponible en el registro fuente, aunque no se infiera superioridad global de ese caso.
