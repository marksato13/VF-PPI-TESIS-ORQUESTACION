# Etapa 3: detección temprana y mejora de reglas (2026-11-02)

> **Alcance:** desarrollo, diagnóstico, replays y ensayos aislados en el portátil, más la lectura de datos de entrenamiento y de configuración.
>
> **Nada desplegado:** no se ha tocado el laboratorio. No hay reinicios, reglas nuevas, enforcement, ataques ni campañas, y el Word no se ha editado.
>
> **No autoriza** el despliegue ni las campañas A/B.

Base: código `6b6ef82` y documentación `20e8630` (cierre offline de la Etapa 2, que se conserva sin cambios). Rama de código: `candidato/etapa3-20261102`. Commits y hashes en [DEPENDENCIAS-Y-COMANDOS.md](DEPENDENCIAS-Y-COMANDOS.md).

## Qué se conserva

- El IF, el escalador, las 28 características y el modelo `if_limpio_2026_10` (sha256 `df547da0…fd60`).
- Los tres α (0,05 / 0,03 / 0,01) y las 7 configuraciones.
- En el replay completo: **0 vectores, 0 scores y 0 decisiones del IF distintos** de 12 726.
- No se elige α: los 25 episodios del 3B son de desarrollo.
- No se ha reentrenado. No se convierte ningún LIMIT en BLOCK.

## Candidata recomendada

Rama `candidato/etapa3-20261102`, commit **`585da7b`**. Pruebas: 626 pasan y 1 se omite (sin node) en el banco; 8/8 mutaciones detectadas.

| Componente | Cambio | Resultado (datos de desarrollo) | Documento |
|---|---|---|---|
| Vía rápida `port_scan_temprano` | detector por par, K = 8, W = 2 s, g = 0,1 s; alternativa C (flujo continuo) | evidencia 0,10 s tras la ráfaga y 4,1–4,5 s antes del último SYN en 5/5 breves; 0 disparos legítimos en 7,2 h; 0 en el control | [VIA-RAPIDA-ESCANEO.md](VIA-RAPIDA-ESCANEO.md) |
| Presupuesto de respuesta (banco) | cadena real sobre veth | 120/120 ejecuciones con aplicación y 1.er descarte antes del último SYN; C con carga: aplicada p95 1,59 s, margen mínimo 2,98 s | [VIA-RAPIDA-ESCANEO.md](VIA-RAPIDA-ESCANEO.md) §6 |
| Vista DNS + dns_entropy ≥ 30 | sin copias del espejo ni reenvíos de DC1/DC2 | DC1 pasa de 382 ventanas a 0 y 10.10.20.22 de 4 a 0; 5/5 `dns_inusual` detectados | [DNS.md](DNS.md) |
| LIMIT DNS (candidata, **no aprobada**) | 30/minuto, ráfaga 18, solo UDP/53 | atacante: 67,6 % descartado (simulado) y 70,3 % (banco con el helper real); legítimos limitados: 0/428 descartadas | [DNS.md](DNS.md) §4 |
| Vista HTTP + http_abuse 600 + port_scan con puertos distintos | se excluyen los registros tardíos de Suricata | 0 confusiones cruzadas; 10.10.20.26 pasa de 6 ventanas a 0; C10 corregida | [HTTP-CONFUSIONES-Y-RENOVACIONES.md](HTTP-CONFUSIONES-Y-RENOVACIONES.md) |
| Publicador | renovación solo con evidencia nueva; una restricción por (IP, destino, alcance) | pruebas unitarias | ídem §6 |
| Contrato flow_duration | **sin cambio** (230 s) | la alternativa empeora los legítimos; propuesta de reentrenamiento sin ejecutar | [CONTRATO-Y-ATRIBUCION.md](CONTRATO-Y-ATRIBUCION.md) |

**Efecto en conjunto** (replay completo frente a `6b6ef82`; [VALIDACION.md](VALIDACION.md)):

- **Restricciones heurísticas a legítimos:** 392 → **0**.
- **Control:** HEUR 92 → **0**. HIB queda igual que el IF (395/254/83).
- **Población principal (15/25):**
  - con HEUR + vía rápida y con HIB + vía rápida (los 3 α), **15/15 con señal antes del fin**;
  - HEUR sola baja a 12/15 porque escaneo_breve-r1 pierde una detección que era un artefacto.
- **R1–R4** se cumplen en el portátil.

## Limitaciones (no se promete 25/25)

1. **Detección no es respuesta.** «Antes del fin» mide la evidencia. El bloqueo efectivo en el laboratorio real (espejo, SSH, CPU de Sensor1) y la reacción de nmap al descarte se desconocen: se miden en la campaña B, no autorizada.
2. **Datos de desarrollo.** Umbrales elegidos con un día del mismo laboratorio y con los mismos ataques que se evalúan. Necesitan episodios y días nuevos.
3. Las **características L7 del IF** siguen contando los registros HTTP tardíos (contrato del modelo).
4. **LIMIT DNS:** TCP/53 queda sin limitar (hueco declarado); falta la medida de varios días.
5. La vía rápida solo protege hosts con punto de aplicación (srv-dmz).
6. Suricata offline con reglas ET: el sistema lo terminó por memoria y no se ha relanzado.

## Documentos

- [MATRIZ.md](MATRIZ.md): problema → cambio → prueba → resultado → pendiente.
- [VIA-RAPIDA-ESCANEO.md](VIA-RAPIDA-ESCANEO.md): anatomía, regla, rejilla, margen legítimo, alternativas y presupuesto temporal.
- [DNS.md](DNS.md): atribución al cliente y política del LIMIT.
- [HTTP-CONFUSIONES-Y-RENOVACIONES.md](HTTP-CONFUSIONES-Y-RENOVACIONES.md).
- [CONTRATO-Y-ATRIBUCION.md](CONTRATO-Y-ATRIBUCION.md): flow_duration_mean_30s y los 8 casos excluidos.
- [VALIDACION.md](VALIDACION.md): 25 episodios, control, reglas, configuraciones y rendimiento.
- [PROCEDIMIENTO-ETAPA4.md](PROCEDIMIENTO-ETAPA4.md): instalación en sombra, comprobación y reversión (**no ejecutado**).
- [DEPENDENCIAS-Y-COMANDOS.md](DEPENDENCIAS-Y-COMANDOS.md): commits, hashes, entornos y comandos.
- `resultados/`, `guiones/` y `MANIFIESTO.sha256`.
