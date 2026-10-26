# 4.2 r2 — Aporte de los componentes (revisión del 26-oct)

Revisión de `../aporte-componentes-2026-10-26/`, que se conserva intacta. Por dónde empezar:

| Archivo | Contenido |
|---|---|
| `NOTA-R2.md` | **Documento principal:** historia real, configuraciones, criterio temporal, Tabla 8 revisada, métricas por ventana, qué está listo, qué se puede afirmar y qué falta |
| `config-r2.json` | Reglas registradas **antes** de calcular (commit `d60495f`) |
| `evaluar_r2.py` | Cálculo completo: `python evaluar_r2.py --datos <copia del sensor>` |
| `resultados/TABLA8-r2.md` | Tabla 8 principal (replay con historia real), sensibilidad (acumulador) y categoría D/P/N/NE por episodio |
| `resultados/contexto-episodios.csv` | Marcas del generador, paquetes, cobertura de PCAP y EVE, huecos y ventanas evaluables |
| `resultados/categorias-episodio.csv` | Categoría, primera señal, latencias, componente y acción propuesta, por fuente, episodio y configuración |
| `resultados/anclas-por-episodio.csv.gz` | Estado y señal de cada ventana de 10.10.20.30 en [inicio, fin + 60 s], en las dos fuentes |
| `resultados/senales-compartidas-durante.csv` | Señales IF y heurístico compartidas y exclusivas durante el ataque |
| `resultados/equivalencia-acumulador.json` | Comparación de las 28 variables entre acumulador y replay (no equivalentes) |
| `resultados/respuesta-05oct-por-episodio.csv` · `feed-05oct-por-minuto.csv` | Feed publicado, lecturas del relay y efecto observable el 5-oct |
| `resultados/ventanas-verificacion-r2.json` · `ventanas-metricas.json` · `ventanas-predicciones.csv.gz` | Métricas por ventana (Tabla 7), verificadas desde las predicciones, con FP clasificadas como señal o medida |
| `resultados/umbrales-verificados.json` | Umbrales α 0,05 y 0,03 recalculados |
| `evidencia/sensor-05oct/` | Extractos de `auth.log`, cron y `publicar.log` del sensor, con sha256 de los ficheros fuente |
| `evidencia/scripts-inventario/` | Scripts con los que se obtuvo la evidencia |
| `EVIDENCIA-4.4-INVENTARIO.md` | Ensayos de respuesta activa disponibles, separados de 4.2 |
| `PROTOCOLO-ENSAYOS-NUEVOS.md` | Protocolo para ensayos nuevos (no ejecutado) |
| `MANIFIESTO-R2.json` | sha256 de las entradas y de los archivos publicados |

**Resultado:** con la historia que realmente existe, ningún episodio del 5-oct es evaluable. La Tabla 8 principal
queda 0 de 9 evaluables y no se reutiliza 6/9 · 7/9 · 9/9.
