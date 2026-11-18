# T — Demo de escenarios, tráfico legítimo y liberación con «Limpiar» (18-nov-2026)

Verificación en vivo antes de la exposición: tres ataques reales desde la Kali
(`10.10.20.30`) contra SRV-DMZ (`10.10.30.10`), comprobados en tres sitios a la vez:
el panel (`https://10.10.60.11:8788/`, vía la extensión de Chrome), el firewall del host
(`~/cf-demo/fw.sh`) y la respuesta HTTP vista desde la Kali.

## Qué corre (referencias por hash, no copias)

| Equipo | Componente | Fuente |
|---|---|---|
| Sensor1 | motor `ppi-motor` | árbol sellado `ec78ca5` (`heuristicos` 2026-11-02.1, sin `icmp_flood`), α 0,01, umbral −0,6223889502 |
| Sensor1 | panel `ppi-dashboard` | producto `a0df76d` (rama `panel/cadena-v2-20261104`), sha256 `6a74fbd6…` |
| SRV-DMZ | agente v2 `--aplicar --sincronizar` | producto `9d67875` (rama `recuperacion/etapa4a-pendientes-20261106`), sha256 `e7836c42…` |

Manifiesto completo y SHA-256 de cada archivo vivo: producto `9d67875`,
`deploy/laboratorio-2026-11-18/MANIFIESTO-ESTADO-2026-11-18.json`.

## Escenarios confirmados

| # | Capa | Ataque (Kali) | Panel | SRV-DMZ | Kali | Tras liberar |
|---|---|---|---|---|---|---|
| 1 | L4 | `nmap -sT -T4 --max-retries 1 -p 1-600 10.10.30.10` | **BLOCK** `port_scan`: 206 intentos/30 s, 0 % completados | BLOQUEADA | HTTP 000 | 200 |
| 2 | L7 | 150 × `curl -u x:x http://10.10.30.10:8081/` | **BLOCK** `brute_force`: 304 req/60 s, 99 % fallo de auth | BLOQUEADA | login 000 | 200 |
| 3 | L7 | `seq 1 900 \| xargs -P20 … curl http://10.10.30.10/` | **LIMIT** `http_abuse`: 1797 req/60 s | LIMITADA | 200 (limitado) | 200 |

Capturas del panel: [`1-escaneo-port_scan-BLOCK.png`](1-escaneo-port_scan-BLOCK.png),
[`2-fuerza-bruta-brute_force-BLOCK.png`](2-fuerza-bruta-brute_force-BLOCK.png),
[`3-flood-http_abuse-LIMIT.png`](3-flood-http_abuse-LIMIT.png).

## Tráfico legítimo (sin alerta)

| Capa | Comando (Kali) | Resultado | Motor |
|---|---|---|---|
| L3 | `ping -c 4 10.10.30.10` | 4/4, 0 % pérdida | PERMIT |
| L4 | `nmap -sT -p 80,443 10.10.30.10` | 80 y 443 abiertos | PERMIT |
| L7 | 5 × `curl http://10.10.30.10/` (uno cada 2 s) | HTTP 200 × 5 | PERMIT (10 req/60 s, 0 % fallo) |

Score del modelo entre −0,48 y −0,56 (por encima del umbral), feed con 0 entradas de la
Kali y firewall vacío. Ninguna regla disparó.

## «Limpiar» libera también el firewall

Antes, «Limpiar» del panel sacaba la Kali del feed (control D5 `reset_origen`) pero el
agente de SRV-DMZ solo **añadía** reglas: la IP seguía en nftables hasta caducar. Se añadió
`--sincronizar` (producto `9d67875`): el feed firmado aceptado manda y lo que sale de él se
quita del firewall. Apagado por omisión; un feed con firma inválida nunca libera nada.
Pruebas: 69 OK / 3 omitidas (Linux). Instalado por Mark con
`sudo bash ~/cf-demo/instalar-sincronizar.sh` (reversible con `revertir-sincronizar.sh`).

Uso: esperar ~60 s tras el ataque antes de «Limpiar»; si el motor aún ve el ataque, vuelve
a publicar la medida.

## Hueco abierto: L3 (inundación ICMP)

`icmp_flood` (≥ 50 % ICMP y > 100 paq/s → BLOCK) está implementada y probada en el
producto (`a0df76d`) y la tarjeta L3 del panel anuncia BLOCK, pero el **motor vivo**
(`ec78ca5`, sellado en solo lectura) no la tiene: un flood de ~4000 paq/s desde la Kali
queda en ALERT del modelo y el ping pasa. Activarla exige un árbol sellado nuevo y
reapuntar el drop-in del motor (sudo de Mark). No se lanza en la exposición.

## Estado que queda

- SRV-DMZ **aplicando** (no sombra). Volver a sombra tras la exposición:
  `sudo rm /etc/systemd/system/ppi-enforce-agent-v2-dmz.service.d/aplicar.conf && sudo systemctl daemon-reload && sudo systemctl restart ppi-enforce-agent-v2-dmz`.
- Ramas subidas; integración en `main` del producto pendiente (después de la exposición).
