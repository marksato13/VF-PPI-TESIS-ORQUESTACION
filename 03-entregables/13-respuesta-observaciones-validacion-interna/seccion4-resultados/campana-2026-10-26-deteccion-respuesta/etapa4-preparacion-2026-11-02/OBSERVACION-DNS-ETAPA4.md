# Observación DNS de 7 días (aparte de la 4A, 4B y 4C)

> **Estado: preparada, no iniciada.** Es una observación **pasiva** y **separada** de las fases 4A–4C. No aprueba
> ni activa el LIMIT DNS en DC1, no cambia la tasa (30/minuto) ni la ráfaga (18) y no toca DC1. Criterio y
> herramienta: [PROTOCOLO-OBSERVACION-DNS de la Etapa 3](../etapa3-cierre-tecnico-2026-11-02/PROTOCOLO-OBSERVACION-DNS.md),
> sin cambios. Este documento añade lo que faltaba para hacerla: la copia diaria y cómo se separan las cifras.

## 1. Dos cifras que no se mezclan

| Medida | Resultado | Qué dice | Qué no dice |
|---|---|---|---|
| Atacante en el banco (5 `dns_inusual`) | **734 de 1 044** consultas descartadas (≈ 70,3 %) | la cubeta recorta el escenario grabado | qué hace la herramienta real ante el descarte |
| Legítimos en el banco (mismos 5 segmentos) | **0 de 428** descartadas | favorable en ≈ 3,5 min por episodio de un día | **no aprueba el límite**: falta la observación de días normales |

Ninguna de las dos aprueba el límite. La aprobación solo puede venir de P1 sobre 7 días que cumplan P3.

## 2. Limitaciones declaradas

- **TCP/53 queda fuera del LIMIT** (`FILTRO_LIMIT["dns"]` es solo `udp dport 53`). Es un hueco conocido: un atacante
  podría pasar a TCP. En esta observación solo se **mide** el uso legítimo de TCP/53 y las respuestas truncadas (TC);
  la regla de solo contar en TCP es una propuesta aparte (PROTOCOLO-OBSERVACION-DNS §4, pasos 3–4).
- **Ausencia de eventos DNS no prueba continuidad.** Un origen sin consultas un día puede ser un equipo apagado o
  una captura caída. La continuidad de un día se demuestra con **todos** los eventos del EVE (hueco máximo) y con
  `stats.log` (`kernel_drops` / `kernel_packets`), no con el DNS.
- **Sin medida no es cero.** Un día sin dos muestras de `stats.log` tiene `kernel_drops = null`, no 0, y no cuenta
  para P3.
- La rotación de `eve.json` es diaria y además por tamaño (`maxsize 500M`, `copytruncate`): un día puede repartirse
  en dos o tres ficheros y la retención real no está medida. Por eso la extracción es **diaria**.

## 3. Separación de periodos y orígenes

- Los días que coincidan con la 4B o la 4C se observan igual, pero el origen Kali `10.10.20.30` se excluye
  (`--excluir 10.10.20.30`) y se anotan los intervalos de campaña. Si un día tiene campaña, se publica también la cifra
  sin ese intervalo.
- El tráfico de los clientes a factor 1,0 durante la 4B y la 4C es legítimo pero **generado**: los días con los
  clientes de laboratorio a un factor distinto del habitual se marcan y se publican aparte.
- **piloto-con-dns:** no se demostró su cierre (última fila del 30-sep, sin acta). Hasta que Mark confirme que terminó
  o que es compatible, los días de observación no se mezclan con él (README §5).

## 4. Copia diaria (solo lectura)

`[LAPTOP Git Bash → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuto yo cada día del periodo, después de las 00:30 hora
de Lima (05:30 UTC), con el día **anterior**. Sin sudo: `m4rk` lee `/var/log/suricata` (lo hace ya `s30`).

```
G="/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/orquestacion-limpio/03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/etapa4-preparacion-2026-11-02/guiones"
bash "$G/r4.sh" d01_dns_dia_e4.sh sensor <AAAA-MM-DD>
```

- **Esperado:** `dns=<n> eventos=<n> hueco_max_s=<x> huecos>300s=<k> drops=<d>/<p> reinicios=<r>` y dos sha256.
- **Parada:** `PARAR: ya existe` (no se sobrescribe un día).
- Probado offline: `evidencia/lectura-laboratorio/probar_d01_dns.py` (día repartido en `eve.json` + `eve.json.1.gz`,
  eventos fuera del día, hueco de 400 s, reinicio del contador de `stats.log`): 59 DNS, 150 eventos, hueco 400 s,
  drops 4/3 000, 1 reinicio.

`[LAPTOP Git Bash → BASTIÓN gadmin]` → lo ejecuto yo, el mismo día (copia fuera del sensor):

```
ssh -i ~/.ssh/id_ed25519 gadmin@10.10.10.30 'mkdir -p ~/cf-e4/dns && scp -o BatchMode=yes "sensor1:cf-e4/dns/*-<AAAA-MM-DD>.json*" ~/cf-e4/dns/ && sha256sum ~/cf-e4/dns/*-<AAAA-MM-DD>.json*'
```

- **Esperado:** los mismos dos sha256 que en el sensor.

## 5. Día que cuenta (P3, sin cambios)

Un día cuenta si: hueco máximo del EVE ≤ 300 s (`huecos_mayores_300s` vacío y sin vacíos al inicio o al final del
día > 300 s), `kernel_drops` medido y < 1 % de `kernel_packets`. Hacen falta 7 días consecutivos que cuenten, con 5
laborables. Un día que no cuenta se publica con su motivo y se añade otro.

## 6. Análisis al terminar

`[LAPTOP Git Bash]` → lo ejecuto yo, con los ficheros descargados del bastión y `observacion_dns.py` de la rama
candidata (`producto-etapa3`, `scripts/etapa3/observacion_dns.py`):

```
python -I "/c/Users/markp/Desktop/PY-MEGATRON/PY - PERSONAL/TESIS/CYBERFLOW/producto-etapa3/scripts/etapa3/observacion_dns.py" observacion-dns-7d.json eve-dns-<D1>.json.gz eve-dns-<D2>.json.gz eve-dns-<D3>.json.gz eve-dns-<D4>.json.gz eve-dns-<D5>.json.gz eve-dns-<D6>.json.gz eve-dns-<D7>.json.gz --excluir 10.10.20.30
```

Se publica P1/P2/P3 tal como salgan, con las `continuidad-<día>.json` al lado. Si P1 no se cumple, el límite no se
aprueba tal cual y no se ajusta para que salga.
