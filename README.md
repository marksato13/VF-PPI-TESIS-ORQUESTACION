# VF-PPI-TESIS-ORQUESTACIÓN

Capa de coordinación de la tesis **«Sistema open source para la detección
temprana de comportamientos anómalos en redes de datos»** (Universidad Peruana
Unión).

| | |
|---|---|
| **Autores** | Rubén Mark Salazar Tocas · Uziel Elias Sauñe Fernandez |
| **Asesores** | Ing. Nemias Saboya Ríos · Ing. Fernando Manuel Asin Gómez |
| **Creado** | 4 de septiembre de 2026 |

---

## Procedimiento de las fases

[`fases/PROCEDIMIENTO.md`](fases/PROCEDIMIENTO.md) responde, por fase: qué se
hizo, con qué comando y qué artefacto verificable produjo. Incluye la
correspondencia entre la numeración de este repositorio y la del producto,
que **no coinciden**.

## Qué es y qué no es este repositorio

**Es** la capa que conecta requisito → fase → decisión → prueba → evidencia →
afirmación → entregable.

**No es** el repositorio del producto. El código, el dataset, los modelos y las
evidencias técnicas viven en
[`VF-Sistema-Open-Source-…`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos)
y **no se duplican aquí**.

| Este repositorio guarda | El repositorio del producto guarda |
|---|---|
| Matriz de requisitos y trazabilidad | Código, scripts y tests |
| Estado de cada afirmación científica | Dataset y modelos congelados |
| Handoffs entre agentes y auditorías | Documentación por fases |
| Planificación, riesgos y cronograma | PCAP, EVE y evidencias brutas |
| Punteros con hash a los artefactos | Los artefactos |

> **Regla que sostiene todo:** aquí se guardan **referencias con hash**, nunca
> copias. Una copia se desincroniza; un hash no miente.

---

## Por dónde empezar

| Si vas a… | Lee |
|---|---|
| Ejecutar la tarea activa | [`TASK-ACTUAL.md`](TASK-ACTUAL.md) |
| Saber en qué punto está todo | [`ESTADO.md`](ESTADO.md) |
| Trabajar como agente (Claude o Codex) | [`REGLAS-Y-LIMITES.md`](REGLAS-Y-LIMITES.md) |
| Entender el proyecto desde cero | [`CONTEXTO-PROYECTO.md`](CONTEXTO-PROYECTO.md) |
| Ver el plan completo | [`PLANIFICACION.md`](PLANIFICACION.md) |

## Estructura

```
arquitectura/     decisiones técnicas y mapa de servicios
fases/            F00 a F09, con criterios de entrada y salida
trazabilidad/     requisitos, afirmaciones, riesgos y entregables
auditorias/       revisiones por agente y por dominio
handoffs/         la interfaz entre Claude y Codex
evidencia/        manifiestos, hashes, comandos e inventarios
automatizacion/   compose, systemd, scripts y healthchecks
informes/         los entregables del curso y de la defensa
plantillas/       formatos obligatorios
```

## La pregunta que este repositorio existe para responder

Ante cualquier cifra del proyecto, en menos de un minuto:

1. ¿De dónde sale?
2. ¿Qué comando la produjo?
3. ¿Qué artefacto la demuestra?
4. ¿Qué versión estaba activa?
5. ¿Está **obtenida**, **validada** o **planificada**?
6. ¿Qué limitación tiene?
7. ¿En qué entregable debe aparecer?

Si alguna no tiene respuesta, es un hallazgo, no un detalle.
