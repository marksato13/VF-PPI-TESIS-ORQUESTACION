# 27 · Fase A de la r7 (T_g 09:30Z del 08-nov): conforme, sin arranque

**La r7 no arrancó.** Se conserva la evidencia tal como quedó. Protocolo: [`PROTOCOLO-CARGA-v2-r7.md`](../../PROTOCOLO-CARGA-v2-r7.md), commit `0446555`.

| Paso | Hora (UTC, 08-nov) | Resultado |
|---|---|---|
| F0, F1 | 06:11Z | rc 0; `REQ FORZAR.sin CUMPLE`; copia en clientes = publicada (`19f07ea1…`) |
| F2 (Mark, sudo) | ≈ 06:13Z | `FORZAR_LABORABLE aplicar rc=0`, seis unidades |
| F3, A0c | 06:15Z | rc 0; `REQ FORZAR.con CUMPLE`; temporizadores de los cuatro hosts leídos |
| A0–A5 | 08:35–08:36Z | rc 0 en todos; `RESULTADO_A1 r7 rc=0` |
| A6 (P0 r3x inmediato), A7, A8 | 09:00–09:01Z | rc 0; 9/9, 51/51, P5b `CUMPLE`; paquete idéntico; `A8 CONFORME` |
| Orden de arranque de Mark | **09:23Z** | **Tras el límite de las 09:20Z.** Quedaban < 2 min para P12 (09:25:00Z) |

**Decisión.** No se arrancó nada (ni muestreadores, ni muestreo del bastión, ni generadores). El procedimiento r7 exige la orden antes de las
09:20Z y la franja no se desplaza. No hay `B1`–`B5`, `C1` ni carpeta `ecarga-v2-ejecucion-20261108T0930Z` en los hosts. El drop-in de F2 sigue
aplicado y lo hereda la r8 (T_g 11:00Z), que usa `evidencia/28-franja-r8-1100z` y `evidencia/29-ecarga-r8-ejecucion`.

No es un resultado de E-carga: no hay veredicto ni medida, y no cuenta para el criterio de avance.
