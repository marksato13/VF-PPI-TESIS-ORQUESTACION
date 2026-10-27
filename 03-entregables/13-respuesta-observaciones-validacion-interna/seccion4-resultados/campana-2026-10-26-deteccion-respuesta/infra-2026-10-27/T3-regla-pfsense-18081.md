# T3 — Regla pfSense (Kali → srv-dmz:18081) + telemetría

**Estado previo (medido 2026-10-27, solo lectura):**
- pfSense-A es **MASTER** (`carp: MASTER` en `vmx3.10`) → la regla se aplica en **A**.
- **No existe regla para 18081** (`10.10.30.10` ya aparece en 7 reglas de prácticas previas, otros puertos).
- Interfaz VLAN20 = `vmx3.20` (opt4).

## Regla  `[pfSense-A, GUI o php]`  → la aplicas tú (el clasificador me bloquea pfSense)

`Firewall > Rules > VLAN20_USUARIOS`, **por encima** del bloqueo base
`CODEX_BASE_DENY_VLAN20_TO_VLAN30_OTHER`:

| Campo | Valor |
|---|---|
| Action | Pass |
| Protocol | TCP |
| Source | `10.10.20.30` (host único = Kali) |
| Destination | `10.10.30.10` |
| Dest port | `18081` |
| Descr | `PPI brute-lab tesis campaña A (temporal)` |

Plantilla en el repo de Franco's: `PFSENSE/BIN/lab_b4_vlan20_8081.php` → clonar cambiando `8081` por `18081`.
XMLRPC ya sincroniza (RA-20 cerrado): debería aparecer también en pfSense-B; **verifícalo**.

**Orden:** la regla va **por encima** del bloqueo. Debajo no se evaluaría nunca y el síntoma sería idéntico
al de no tenerla (conexión rechazada), con la regla escrita y visible.

### Verificación  `[Kali 10.10.20.30]`
```
curl -s -o /dev/null -w "%{http_code}\n" http://10.10.30.10:18081/       # ABIERTO
curl -s -o /dev/null -w "%{http_code}\n" http://control:control123@10.10.30.10:18081/auth   # 401/401/200 segun credencial
```

### Reversión
Deshabilitar o borrar esa regla (`lab_b4...php quitar` si usas el php).

## Telemetría  `[SENSOR 10.10.60.11]`  → la corres tú (el Claude de infra no tiene cuenta ahí)
```
sudo grep '"dest_port":18081' /var/log/suricata/eve.json | grep '"event_type":"http"' | tail   # debe haber 401 y 200
grep 10.10.20.30 ~/cyberflow/logs/motor_decision.log | grep http_request_count_60s | tail        # entidad con conteo > 0
```
Si 18081 **no se parsea como HTTP**: añadir `18081` a `HTTP_PORTS` en `/etc/suricata/suricata.yaml`,
reiniciar `suricata`, y repetir — e informar de que hubo que tocarlo.
