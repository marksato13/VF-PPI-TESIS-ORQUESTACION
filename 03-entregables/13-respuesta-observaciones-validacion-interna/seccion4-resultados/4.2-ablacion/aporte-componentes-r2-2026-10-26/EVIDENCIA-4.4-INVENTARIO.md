# Evidencia disponible para 4.4 (respuesta activa) — inventario, sin mezclar con 4.2

**Fecha:** 26-oct-2026. Es solo un inventario: no redacta 4.4 ni recalcula tiempos.

## Cadena que se busca

1. Ataque
2. Señal
3. Feed
4. Agente / nftables
5. Efecto
6. Retirada o caducidad

En la tabla, **✓** significa que hay evidencia guardada del eslabón y **—** que no la hay.

**Modelo en vivo:**

- Hasta el 19-oct: `if_recalibrado_2026_09` (contaminado, umbral −0,568892).
- Desde el 19-oct: `if_limpio_2026_10`.

## Tabla de ensayos

Rutas relativas a `orquestacion-limpio/`, salvo que se indique `producto-main/`.

| Fecha | Ensayo | Modelo | Ataque | Señal | Feed | Agente/nft | Efecto | Retirada | Dónde |
|---|---|---|---|---|---|---|---|---|---|
| 30-sep | E2E del agente con feed firmado **generado a mano** | — (sin motor) | ✓ curl | — | ✓ manual | ✓ `ip saddr … drop`, 12 paquetes | ✓ http_000 | ✓ caducidad nativa; tabla eliminada a mano | `04-evidencias/cyberflow/N-e2e-enforcement-2026-09-30.md` |
| 30-sep | Cadena completa en **dry-run** | recalibrado | — (tráfico real) | ✓ | ✓ | dry-run (no aplica) | — | — | misma nota, sección «Pipeline completo» |
| 01-oct | Primera campaña con enforcement **en vivo** | recalibrado | ✓ DNS + nmap | ✓ ALERT 03:17:40 | ✓ LIMIT | ✓ `shadow.log` «aplicado», `limit:[10.10.20.30]` | — (no se midió) | ✓ «lo retiró al cesar» (sin hora) | `04-evidencias/cyberflow/O-enforcement-vivo-campana-ataque-2026-10-01.md` |
| 05-oct | Batería 3×3 de 4.2 | recalibrado + heurísticos `09-30.1` | ✓ | ✓ (offline) | ✓ recuento por minuto en `publicar.log` | — sin registro del agente | e3/e4: ninguno visible; e1-r3: srv-dmz responde con BLOCK publicado | — | `4.2-ablacion/aporte-componentes-r2-2026-10-26/NOTA-R2.md` §6 |
| 13-oct | Recorrido escaneo | recalibrado | ✓ nmap | ✓ `motor_decision.log` (`port_scan` + IF) | ✓ | ✓ set `cyberflow_bloqueados` | ✓ `nmap` posterior → `filtered` | ✓ caducidad según escalera (descrita; sin medición) | `02-metodologia/validacion-interna-profesor/recorrido-ataque-2026-10-13/` |
| 14/15-oct | Recorrido multi-ataque (4 familias) | recalibrado | ✓ | ✓ | ✓ | ✓ `cyberflow_bloqueados { 10.10.20.30 timeout 58m }` | ✓ 80/443 `filtered`; brute: timeouts | caducidad descrita | `…/recorrido-multiataque-2026-10-14/RECORRIDO-MULTIATAQUE-RESPUESTA.md` |
| 15-oct | Cadena de 10 s con tiempos | recalibrado | ✓ | ✓ | ✓ | ✓ «aplicación en nftables 12:48:16» | — | ✓ prueba segura de caducidad nativa (TEST-NET; retirada manual al final) | `producto-main/docs/evidencias/tiempos-2026-10-15-cadena-10s.md` |
| 15-oct | Demo en vivo | recalibrado | ✓ | ✓ | ✓ | ✓ `nft list set` con `expires 57m52s` | ✓ | comando de verificación; sin observación de la expiración | `…/recorrido-demo-en-vivo-2026-10-15/RECORRIDO-DEMO-EN-VIVO.md` |
| 23-oct | Campaña instrumentada | **IF limpio** + heurísticos `10-06.2` | ✓ `marcas.jsonl` | ✓ `motor_slice.jsonl` | ✓ (publicado cada 10 s; **secuencia no guardada**) | ✓ brute_force: `cyberflow_bloqueados` con Kali, timeout ~1 800 s | ✓ corte real 80/443 `filtered` (brute) | ✓ «expiró» (sin hora exacta: t5 no medido) | `seccion4-resultados/_campana/resultados-2026-10-23/RESULTADOS-CAMPANA-2026-10-23.md` |

## Lectura

- **Única evidencia con el IF limpio: el 23-oct.**
  - Cadena completa para la **fuerza bruta**: señal `brute_force` → BLOCK → nft con la Kali → corte real → expiración.
  - Los eslabones feed y retirada **no tienen marca temporal por episodio**.
  - El BLOCK escalado (1 800 s) **contaminó el escaneo posterior**.
  - Para DNS y flood: LIMIT propuesto y publicado, sin efecto medido (LIMIT 100 paq/s no corta).
- **Del 1-oct al 15-oct** la cadena completa está demostrada, pero con el **modelo anterior**. Sirve para mostrar que
  el mecanismo funciona, no para medir el sistema evaluado en 4.1/4.2.
- **El 30-sep es una prueba aislada del agente** con un feed hecho a mano. **No es una respuesta automática completa** y
  no debe describirse así.
- **El 5-oct no es evidencia de respuesta:** no hay registro del agente, y en e1-r3 el destino siguió respondiendo
  después de publicarse un BLOCK.
- **No hay ningún ensayo con el IF limpio que mida la retirada de un LIMIT**, ni el instante exacto del feed o de la
  regla nft por episodio.

Lo que habría que ejecutar está en `PROTOCOLO-ENSAYOS-NUEVOS.md`, parte B.
