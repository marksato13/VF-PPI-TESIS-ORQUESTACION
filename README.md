# VF-PPI-TESIS-ORQUESTACIÓN

Gestión documental de la tesis **«Sistema open source para la detección
temprana de comportamientos anómalos en redes de datos»**.

| | |
|---|---|
| **Autores** | Rubén Mark Salazar Tocas · Uziel Elias Sauñe Fernandez |
| **Asesores** | Ing. Nemias Saboya Ríos · Ing. Fernando Manuel Asin Gómez |
| **Institución** | Universidad Peruana Unión — E.P. de Ingeniería de Sistemas |
| **Producto** | [`VF-Sistema-Open-Source-…`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos) |

---

## Qué es y qué no es este repositorio

**Es** la documentación de la tesis: cómo se llegó a cada resultado, qué se
midió, con qué comando, y qué entregable salió de ahí.

**No es** el repositorio del producto. El código instalable, el modelo y el
dataset viven aparte y **no se duplican aquí**.

| Aquí | En el producto |
|---|---|
| Metodología, fases y trazabilidad | Código, scripts y tests |
| Entregables de la tesis (`.docx`) | Dataset y modelos congelados |
| Evidencias medidas, con su comando | Guías de instalación y uso |
| Decisiones de arquitectura y su porqué | Los artefactos publicados |
| Punteros con hash a los artefactos | Los artefactos |

> **La regla que lo sostiene todo: aquí se guardan referencias con hash, nunca
> copias.** Una copia se desincroniza en silencio; un hash no miente.

---

## Estructura

```
README.md              este fichero: el mapa
ESTADO.md              dónde está el proyecto hoy, y qué bloquea
PLANIFICACION.md       plan, riesgos y cronograma

01-arquitectura/       cómo está construido y por qué
02-metodologia/        fases del trabajo y trazabilidad
03-entregables/        lo que se entrega: informes, artículo, PPI
04-evidencias/         lo medido, con su comando y su salida
plantillas/            formatos para no improvisar
```

### `01-arquitectura/`

La arquitectura general, el mapa de servicios, la red y seguridad, y las
**decisiones técnicas** con su justificación (`DEC-nnn-titulo.md`).

Una decisión se documenta cuando cambia algo que costaría revertir. Lleva:
el contexto, las opciones consideradas, la elegida, y **qué la invalidaría**.

### `02-metodologia/`

Una carpeta por fase, y la trazabilidad que las une:

```
requisito → fase → decisión → prueba → evidencia → afirmación → entregable
```

`trazabilidad/afirmaciones-cientificas.md` es el fichero más importante del
repositorio: **cada afirmación que aparece en la tesis, con el dato que la
sostiene**. Si una afirmación no tiene evidencia enlazada, no se escribe.

### `03-entregables/`

Los documentos que se entregan. **Solo la versión vigente.** Las anteriores no
se guardan aquí: para eso está el historial de Git.

### `04-evidencias/`

Medidas, no impresiones. Cada evidencia lleva **el comando y su salida
íntegra**, con las credenciales enmascaradas.

```
04-evidencias/
  <ambito>/
    <letra>-<asunto>-<AAAA-MM-DD>.md
```

Ejemplo: `cyberflow/G-suricata-2026-09-17.md`.

Una evidencia sin comando detrás no es una evidencia: es una opinión con
formato. Si algo no se midió, se escribe **«sin verificar»**.

---

## Cómo se mantiene

### Las cinco reglas

**1. Medir antes de afirmar.** Nada de «está configurado» sin un comando y su
salida. Si no se midió, se dice.

**2. La evidencia se genera, no se escribe a mano.** Un arnés captura comando y
salida en un `.md`, con los secretos enmascarados.

**3. Cada cambio lleva su verificación y su vuelta atrás escritas antes de
aplicarlo.**

**4. Nada de credenciales.** Ni en un fichero, ni en un commit, ni en un
comando que quede en el historial. Viven en variables de entorno y en
`~/.ssh/`.

**5. Solo la versión vigente.** Nada de `informe-v2-final-FINAL.docx`. Si hace
falta una versión anterior, está en el historial de Git.

### Qué se actualiza y cuándo

| Cuándo | Qué |
|---|---|
| Al terminar una medición | Una evidencia nueva en `04-evidencias/` |
| Al cambiar algo que costaría revertir | Una decisión en `01-arquitectura/decisiones-tecnicas/` |
| Al cerrar una fase | El `README.md` de esa fase y la trazabilidad |
| Al entregar un documento | Se sustituye en `03-entregables/`, no se añade |
| Cuando cambia lo que bloquea | `ESTADO.md` |
| Cuando una afirmación gana o pierde respaldo | `trazabilidad/afirmaciones-cientificas.md` |

### Nombres

| Tipo | Formato | Ejemplo |
|---|---|---|
| Evidencia | `<letra>-<asunto>-<AAAA-MM-DD>.md` | `D-validacion-espejo-2026-09-17.md` |
| Decisión | `DEC-<nnn>-<titulo>.md` | `DEC-001-repositorio-separado.md` |
| Fase | `F<nn>-<nombre>/` | `F04-dataset/` |
| Entregable | `<Nombre-del-documento>.docx` | `Informe-validacion-confiabilidad.docx` |

Fechas siempre `AAAA-MM-DD`, y **absolutas**: «el martes pasado» no significa
nada dentro de seis meses.

---

## Por dónde empezar

| Si busca… | Vaya a |
|---|---|
| en qué punto está el proyecto | [`ESTADO.md`](ESTADO.md) |
| qué se ha medido y cuándo | `04-evidencias/` |
| por qué se decidió algo | `01-arquitectura/decisiones-tecnicas/` |
| qué sostiene una afirmación de la tesis | `02-metodologia/trazabilidad/` |
| cómo instalar el sistema | el repositorio del producto, `docs/INSTALACION.md` |

---

## Licencia

Documentación bajo los términos del repositorio. El código del producto es MIT.
