# Protocolo de observación del DNS legítimo (varios días, sin restringir)

> **Estado: preparado, no ejecutado.** La observación se hará en el laboratorio en su etapa, con autorización de Mark y después de comprobar que no interfiere con otros ensayos (en particular **piloto-con-dns**). Hasta entonces el LIMIT DNS **no se activa en DC1** y su valor (30/minuto, ráfaga 18, solo UDP/53) **no se cambia**.

## 1. Lo que ya se sabe y lo que no

Son dos cifras distintas y no se mezclan:

| Medida | Resultado | Qué significa |
|---|---|---|
| Atacante en el banco (5 `dns_inusual`, helper real) | **734 de 1 044 consultas descartadas (≈ 70,3 %)** mientras está limitado | la cubeta recorta el escenario grabado; no dice qué hace la herramienta real ante el descarte |
| Legítimos en el banco (los mismos 5 segmentos, limitados a propósito) | **0 de 428 descartadas** | favorable, pero son unos 3,5 min por episodio de un solo día: **no aprueba el límite** |

Lo que falta para aprobarlo es saber cómo consultan los equipos legítimos durante días normales (arranques, actualizaciones, horas pico, fines de semana) y si alguno superaría la cubeta en el caso de que lo limitaran por error.

## 2. Qué se mide (pasivo)

Fuente: los `eve.json` de Suricata en Sensor1 (eventos `dns`), que **ya se registran**. No se añaden reglas, capturas ni procesos en DC1. Herramienta: `scripts/etapa3/observacion_dns.py` (rama candidata; prueba `tests/test_observacion_dns.py`).

Por **día local** (Lima, UTC−5) y por **origen** (cliente → DC1/DC2):

| Métrica | Para qué |
|---|---|
| consultas UDP/53 y TCP/53 | volumen y uso de TCP |
| máximo en 1, 10 y 60 s (UDP) | ráfagas y picos |
| ráfaga mínima b(0,5) de la envolvente | con b ≥ b(0,5) la cubeta 30/minuto no descartaría nada de ese origen |
| descartes simulados con (30/minuto, ráfaga 18) **si el origen estuviera limitado todo el día** | peor caso del impacto legítimo |
| NXDOMAIN, SERVFAIL y otros rcode | errores (un cliente roto puede parecer DGA) |

Se excluyen las copias del espejo (la misma deduplicación que la vista DNS) y las consultas de los propios resolvedores. Si en esos días hay campañas, sus orígenes atacantes se pasan con `--excluir` y se anota.

## 3. Criterio de impacto legítimo aceptable (fijado ANTES de medir)

- **P1 (aprobación):** **0 consultas UDP/53 legítimas descartadas** en la simulación de la cubeta candidata, en todo origen y en todo día observado, suponiendo que el origen estuviera limitado por error **todo el día**. Es deliberadamente más severo que la realidad: un LIMIT dura minutos.
- **P2 (aviso, no rechazo):** un origen-día con b(0,5) > 12 (margen inferior a 1,5 veces la ráfaga 18) se lista y se revisa qué lo produce.
- **P3 (cobertura mínima):** al menos **7 días consecutivos con 5 laborables**. Además, sin huecos del EVE de más de 5 min (continuidad de marcas de tiempo) y con `capture.kernel_drops` de Suricata < 1 % del día (`stats.log`). Un día que no cumple P3 no cuenta, y se añade otro.

**Si P1 no se cumple, el límite no se aprueba tal cual.** Se documentan el origen, la hora, la actividad que lo causó y los descartes. Cambiar la tasa o la ráfaga sería una **propuesta nueva** que tendría que validarse otra vez, con el atacante y con los legítimos. No vale como ajuste para que las cifras salgan bien.

## 4. TCP/53 fuera del LIMIT

El LIMIT candidato solo cubre `udp dport 53` (`cf_nft_helper.FILTRO_LIMIT["dns"]`). Una consulta por TCP no se limita: es un **hueco declarado**, porque un atacante podría pasar a TCP.

> **Nota de coherencia:** el comentario de cabecera de `politica_limit_dns.py` dice que la política limita «solo los SYN de TCP dport 53». El helper **no** lo hace: el texto nft cargado es solo UDP (lo verifica `tests/test_etapa3_dns.py`). Manda el helper. El comentario se corrige en esta rama.

Propuesta para evaluarlo **sin bloquear servicios DNS necesarios**, en este orden:

1. **Medir el uso legítimo de TCP/53** en la misma observación: consultas TCP por origen y día, y respuestas UDP truncadas (TC), que son el motivo legítimo de pasar a TCP. Las transferencias de zona entre DC1 y DC2 no cuentan: los dos están en `NUNCA` y nunca se limitan.
2. **Simular** sobre esos datos una cubeta por **conexiones nuevas** (`tcp dport 53`, SYN sin ACK) con el mismo método de la envolvente. La unidad es la conexión, no el paquete.
3. **Banco:** variante del helper con una regla TCP que **solo cuenta** (`counter`, sin `drop`), sobre segmentos con DNS por TCP generado en el banco. Comprueba el texto nft y los contadores sin cortar nada.
4. **Laboratorio (etapa aparte):** la misma regla de solo contar en DC1, en sombra, durante la observación. Solo si P1 se cumple también para TCP se propondría convertirla en límite, con autorización.

Los pasos 3 y 4 implican cambiar el helper. No se hacen en este cierre: quedan como propuesta.

## 5. Procedimiento (cuando se autorice)

**Paso 0. Comprobar el estado del laboratorio antes de nada.**

`[BASTIÓN gadmin]` → lo ejecuto yo: son lecturas por SSH, sin sudo.

```bash
ssh m4rk@10.10.60.11 'systemctl is-active ppi-motor suricata; ls -la /var/log/suricata/ | head; df -h /var/log'
```

- Confirmar con Mark que **piloto-con-dns** terminó o que la observación no interfiere con él. Es pasiva, pero conviene no mezclar sus días.
- Retención de `eve.json`: si la rotación no conserva 7 días, Mark decide cómo guardar copias diarias. Por ejemplo, una copia diaria del subconjunto `dns` al bastión. Es un cambio en Sensor1, así que necesita autorización.

**Pasos 1–7.** Cada día, copiar el subconjunto DNS del día al bastión (solo lectura en Sensor1) y anotar si hubo campañas.

**Paso 8. Al terminar, en el portátil.**

`[LAPTOP Git Bash]` → lo ejecuto yo:

```bash
python scripts/etapa3/observacion_dns.py observacion-dns.json eve-dns-dia1.json.gz ... eve-dns-dia7.json.gz
```

- Para P3: continuidad del EVE y `kernel_drops`.
- Se publica el resultado con el criterio de §3, sin reinterpretarlo.

## 6. Ensayo de la herramienta sobre datos ya disponibles

Para comprobar la herramienta (no para aprobar nada) se pasó sobre el EVE del tramo del 3B: ver `README.md` §4 y `resultados/dns/observacion-3b-ensayo.json`. Es **un solo tramo de un día**, con campañas en curso: no cumple P3.
