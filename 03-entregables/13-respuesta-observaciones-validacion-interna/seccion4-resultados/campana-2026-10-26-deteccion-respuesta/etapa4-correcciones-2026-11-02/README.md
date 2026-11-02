# Etapa 4: correcciones de las herramientas de preparación (2026-11-02)

> **No autoriza la Etapa 4.** Nada se ha instalado, reiniciado ni modificado en el laboratorio; no hay enforcement,
> controles ni campañas. La secuencia sigue siendo **4A** (instalación en sombra) → **4B** (control normal) →
> **4C** (campaña A, 25 episodios, α 0,05 / 0,03 / 0,01 y vía rápida aparte) → **Etapa 5** (campaña B).

## 1. Punto de partida verificado

| Qué | Referencia | Comprobado |
|---|---|---|
| Documentación | `main` @ `d3464bf` (preparación de la Etapa 4) | `git ls-remote`; sin correcciones posteriores |
| Herramientas | `candidato/etapa3-20261102` @ `acc6588` | idem |
| Detector | `ec78ca5` | sin cambios |
| Sensor1 | motor `24f8a80` con la cadena v1, sin checkout de git | [ESTADO-OBSERVADO](../etapa4-preparacion-2026-11-02/ESTADO-OBSERVADO-LABORATORIO.md) |

## 2. Resultado

| Qué | Dónde |
|---|---|
| Producto | `candidato/etapa3-20261102` @ **`f9cf801`** (herramientas) → **`3a9f26b`** (solo pruebas). No se fusiona en `main` (`7b275b8`). Código del detector = `ec78ca5` |
| Generador con compuerta | [`../scripts-4c/generar_campana.py`](../scripts-4c/generar_campana.py) `99e6bdae…` (+ `esquema_campana.py` `e762e604…`, sin cambios) |
| Guiones corregidos | `../etapa4-preparacion-2026-11-02/guiones/` (`g01`, `b20`, `c03`, `r4`, `s50`) y su banco `../tests/ensayo_errores_s50_r4.sh` |
| Documentos de la preparación actualizados | SALUD-CAPTURA, PROTOCOLO-4C, PROCEDIMIENTO, README, ORDEN-4C, CAMBIOS y `evidencia/paquete/` (ver su [CAMBIOS](../etapa4-preparacion-2026-11-02/CAMBIOS.md)) |
| Tabla de correcciones | [TABLA-CORRECCIONES.md](TABLA-CORRECCIONES.md) |
| Detección oportuna por familia | [DETECCION-OPORTUNA.md](DETECCION-OPORTUNA.md) |
| Condiciones del laboratorio y diagnóstico de Suricata para la 4A | [CONDICIONES-LABORATORIO.md](CONDICIONES-LABORATORIO.md) |
| Evidencia | `evidencia/pruebas/` (pytest Windows y Linux, carga concurrente, regresión sobre la versión anterior), `evidencia/banco/` (estado de sombra; errores de `s50`/`r4`), `evidencia/paquete/` |
| Lecturas del laboratorio | `lectura-laboratorio/` (guiones y salidas literales) |
| Integridad | `MANIFIESTO.sha256` (esta carpeta) y el de la preparación, regenerado |

Sin cambios: modelo, escalador, 28 características, tres α, reglas, `config-campana-4c.json`, `escenarios-4c.json`,
`herramientas-e4.sha256`, la evidencia anterior, la imagen Docker y el Word.

## 3. Conclusión

**Los cuatro defectos están resueltos offline:**

1. cobertura SIGUSR1 insuficiente → C3, nunca C0 (la versión anterior falla 9 regresiones);
2. estado de sombra de srv-dmz sin autoconteo y con `desconocido` ante cualquier lectura fallida;
3. P1–P5 y X1–X3 conectados a la ejecución mediante permiso de fallo cerrado, probado de punta a punta con el
   generador real;
4. errores propagados en `s50` y `r4`, con dependientes omitidos, rc ≠ 0 y manifiesto parcial etiquetado.

Lo que queda **solo puede comprobarse en vivo** (TABLA-CORRECCIONES, última columna). Lo principal:

- `sudo -n journalctl` para m4rk en el Sensor1 (las lecturas SIGUSR1 dependen de ello);
- `g01` completo, probado hasta ahora por componentes;
- copiar `scripts-4c/` a la Kali;
- coste del vigía en el Sensor1;
- **aceptar el cambio de protocolo:** un canal SSH persistente con la Kali durante la batería, en lugar de «ningún
  acceso».

**¿Puede solicitarse la 4A?** **Sí, puede solicitarse.** La 4A instala en sombra y observa; ninguno de los
pendientes la bloquea. Al contrario, varios se resuelven dentro de ella:

- verificar el `sudo -n journalctl`;
- medir el `sensor` del vigía;
- ejecutar `estado_sombra.py` real;
- hacer el diagnóstico de descartes de Suricata.

Siguen vigentes las condiciones de [README §5 de la preparación](../etapa4-preparacion-2026-11-02/README.md#5-condiciones-antes-de-instalar). La de `piloto-con-dns` queda satisfecha por lectura (CONDICIONES §1).

**No se ha iniciado.** La 4C exige además:

- 4A y 4B cerradas;
- I1–I8;
- la aceptación del canal de control.

Con la tasa de descartes de Suricata observada, I5 (0 descartes en 30 min) puede no cumplirse: el diagnóstico de la 4A
debe llegar antes.
