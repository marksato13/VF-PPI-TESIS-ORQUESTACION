# Orden de trabajo para el Claude de infraestructura — preparación entorno campaña A

**Contexto.** Laboratorio CyberFlow. Estamos en PREPARACIÓN de la "campaña A" (detección). Procedimientos en el
commit `0773801` del repo `VF-PPI-TESIS-ORQUESTACION`, carpeta
`03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/`.

**Reglas (obligatorias).** NO ejecutes ataques ni inicies la campaña. NO toques el modelo, escalador, umbrales,
heurísticos ni la política de respuesta. NO modifiques Word. Todo cambio: **registra el estado previo, aplica, y deja
la reversión escrita**. Trabaja solo en el laboratorio autorizado.

**Objetivo.** Resolver 3 pendientes críticos que yo (otra sesión) no puedo por falta de acceso, y devolverme la
**evidencia trazable** de cada uno para que yo cierre la verificación y marque "LISTO PARA CAMPAÑA A".

Hosts: bastión VM-GESTION 10.10.10.30 · sensor 10.10.60.11 · srv-dmz 10.10.30.10 · Kali 10.10.20.30 ·
DNS/AD 10.10.10.20 · pfSense (IP de gestión: la tuya). Origen de ataques en la campaña = Kali 10.10.20.30.

Ya hecho por mí (no rehacer): endpoint de prueba **desplegado** en `srv-dmz:18081` como servicio `ppi-brute-lab`
(`/opt/brute-lab/app.py`), credencial de control `control:control123`, ruta `/auth`. Verificado en local:
sin credenciales→401, inválidas→401, control→200.

---

## Tarea 1 — NTP del sensor (va −47,8 s respecto al bastión)

`[SENSOR root]` (o m4rk con sudo):
```
# estado previo
timedatectl; timedatectl timesync-status 2>/dev/null | sed -n '1,8p'
# corregir
sudo timedatectl set-ntp false; sudo timedatectl set-ntp true; sleep 5
sudo systemctl restart systemd-timesyncd; sleep 5
timedatectl timesync-status
```
El sensor ya apunta al bastión (`Server=10.10.10.30`). Si no converge, usa `chrony` con un paso único
(`sudo chronyd -q 'server 10.10.10.30 iburst'`) o documenta la corrección aplicada.

**Verificación y evidencia a devolver:** desfase sensor↔bastión **antes y después**, con incertidumbre. Método:
desde el bastión, 3 muestras `A=$(date +%s.%N); S=$(ssh sensor date +%s.%N); B=$(date +%s.%N)` y offset = `S-(A+B)/2`.
Objetivo: |offset| ≤ 1 s. Devuélveme las 3 muestras antes y las 3 después.
**Reversión:** NTP es estado benigno; no requiere reversión (documenta el valor previo).

---

## Tarea 2 — Zona DNS local reservada en 10.10.10.20 (hoy reenvía a Internet)

Crea una zona de laboratorio que resuelva **local** y **no reenvíe** a terceros. Dominio sugerido: `lab-ppi`.

**BIND (Linux):**
```
# estado previo: guarda named.conf.local y la lista de forwarders
cat >> /etc/bind/named.conf.local <<'EOF'
zone "lab-ppi" { type master; file "/etc/bind/db.lab-ppi"; };
EOF
cat > /etc/bind/db.lab-ppi <<'EOF'
$TTL 60
@   IN SOA ns.lab-ppi. admin.lab-ppi. ( 1 60 60 86400 60 )
@   IN NS  ns.lab-ppi.
ns  IN A   10.10.10.20
*   IN A   10.10.30.10
EOF
named-checkzone lab-ppi /etc/bind/db.lab-ppi && rndc reload
```
**Windows DNS/AD (PowerShell admin):**
```
Add-DnsServerPrimaryZone -Name "lab-ppi" -ZoneFile "lab-ppi.dns"
Add-DnsServerResourceRecordA -ZoneName "lab-ppi" -Name "*" -IPv4Address 10.10.30.10
# asegúrate de que la zona NO reenvía (es autoritativa; sin forwarders por-zona)
```

**Verificación y evidencia (clave: que NO sale a terceros):**
1. `[Kali]` o `[bastión]`: `dig +time=2 +tries=1 @10.10.10.20 probe-$(date +%s).lab-ppi +short` → debe devolver
   `10.10.30.10` (local), NO una IP pública.
2. **Captura de egress** en el borde/pfSense o en la WAN del DNS mientras se lanza esa consulta: confirmar **cero**
   paquetes 53/udp hacia Internet para `*.lab-ppi` (p.ej. `tcpdump -ni <wan> 'udp port 53 and not host 10.10.10.0/24'`
   durante la consulta → 0 coincidencias de ese nombre). Devuélveme el conteo/evidencia.
3. (Contraste) `dig @10.10.10.20 example.com +short` puede seguir resolviendo: eso es aparte; lo que importa es que
   `*.lab-ppi` NO egrese.

**Reversión:** quitar la zona (`zone "lab-ppi"` de named.conf.local + `rndc reload`, o `Remove-DnsServerZone -Name lab-ppi`).

---

## Tarea 3 — Regla pfSense para el endpoint + verificación de telemetría

**Regla (solo esa):** permitir `source 10.10.20.30` → `dest 10.10.30.10` **TCP/18081**, en la interfaz de la VLAN de
la Kila. Descripción: "lab brute-force endpoint (campaña A)". Registra la regla previa (no la había) para revertir.

`[pfSense]` por GUI (Firewall → Rules) o `easyrule`:
```
easyrule pass <interfaz_vlan_kali> tcp 10.10.20.30 10.10.30.10 18081
```

**Verificación end-to-end (BENIGNA, no es la campaña) y evidencia a devolver:**
1. `[Kali]` conectividad + códigos (pocas peticiones):
   ```
   timeout 3 bash -c 'echo >/dev/tcp/10.10.30.10/18081' && echo ABIERTO
   curl -s -o /dev/null -w 'sin  -> %{http_code}\n' --max-time 5 http://10.10.30.10:18081/auth
   curl -s -o /dev/null -w 'mala -> %{http_code}\n' --max-time 5 -u fake:fake http://10.10.30.10:18081/auth
   curl -s -o /dev/null -w 'ok   -> %{http_code}\n' --max-time 5 -u control:control123 http://10.10.30.10:18081/auth
   ```
   Esperado: ABIERTO, 401, 401, 200. Anota la hora UTC.
2. `[SENSOR m4rk]` que Suricata parsea HTTP en ese puerto:
   `sudo grep '"dest_port":18081' /var/log/suricata/eve.json | grep '"event_type":"http"' | tail -3`
   → debe haber eventos http con `"status":401` y `"status":200` para 10.10.30.10:18081.
3. `[SENSOR m4rk]` que el extractor lo recibe: en la ventana de la prueba, en `~/cyberflow/logs/motor_decision.log`
   la entidad `10.10.20.30` debe tener `http_request_count_60s > 0`:
   `grep '"entity_ip": "10.10.20.30"' ~/cyberflow/logs/motor_decision.log | tail -2`
   (si el puerto 18081 no se parsea como HTTP, añade `HTTP_PORTS` en `/etc/suricata/suricata.yaml` e informa; es un
   cambio de infra a documentar).

**Reversión:** borrar la regla pfSense añadida.

---

## Qué devolverme (para cerrar la verificación)

Por cada tarea, en formato trazable (lo consume mi verificador de integridad como "informe externo"):
`{ maquina, herramienta, resultado: "ok"/"fallo", referencia: <ruta/evidencia>, salida_cruda }`.

Concretamente:
- **T1:** las 3 muestras de offset antes y después (y método).
- **T2:** salida del `dig` a `*.lab-ppi` (local) y el conteo de egress 53/udp (0).
- **T3:** los 4 códigos desde la Kali (ABIERTO/401/401/200), las 3 líneas de eve.json (http 401/200 en :18081) y las
  líneas del motor con `http_request_count_60s`.

No inicies la campaña ni generes tráfico de ataque (solo las pocas peticiones benignas de verificación de T3). Cuando
me pases la evidencia, yo actualizo `escenarios.json`/`config-campana.json` con los valores verificados, regenero el
manifiesto y, si nada crítico queda, marco **LISTO PARA CAMPAÑA A** (sin iniciarla).
