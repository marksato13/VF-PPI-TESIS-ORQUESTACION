# Comprobaciones previas y bloqueos pendientes

**Fecha:** 26-oct-2026 ~23:33–23:36 UTC. Benignas y de solo lectura; **no se generó tráfico de ataque.**
Salida cruda: `evidencia-precheck/precheck-2026-10-26.txt`.

## Lo que está listo

- **Motor en vivo con el IF limpio:** `ppi-motor` activo, `detector = if_limpio_2026_10`. Captura (`ppi-motor-capture`),
  Suricata y panel activos. `motor_decision.log` en escritura.
- **Hashes de código y modelo** cuadran con lo esperado (ver `config-campana.json`); el joblib desplegado es
  `df547da0…fd60`.
- **Alcance a servicios** (desde el bastión): srv-dmz 10.10.30.10 responde 200 en `/` (80 y 443 abiertos). El DNS
  10.10.10.20 resuelve.
- **Bastión sincronizado por NTP** (chrony, offset ~1 ms).
- **Sin bloqueos residuales:** `cyberflow_bloqueados` y `cyberflow_limitados` sin elements ahora.

## Bloqueos que requieren intervención humana antes de la campaña A

Cada acción con su etiqueta de máquina. Por defecto las ejecuto yo salvo que necesiten consola/contraseña/root.

### 1. NTP del sensor sin disciplinar (crítico para 4.4)

El sensor no tiene `chrony`; su reloj no está sincronizado (coherente con el desfase ~47 s observado antes). 4.4 mide
tiempos entre sensor, bastión, Kali y srv-dmz: necesitan reloj comparable.

- `[SENSOR root] → lo ejecutas tú` (sudo con contraseña): instalar/activar `chrony` y verificar
  `chronyc tracking`. Guardar el desfase antes y después.
- Alternativa sin cambiar el sistema: medir el desfase sensor↔bastión al inicio y al fin de la campaña y corregirlo en
  el análisis. Hay que decidir cuál.

### 2. Poner el enforcement en modo sombra para A (crítico)

Estado en vivo: agente de srv-dmz en `--aplicar`, publicador cada 10 s, relay activo. En A el tráfico no debe alterarse.

- `[srv-dmz adminsrvdmz] → lo ejecutas tú` (sudo con contraseña): editar `ppi-enforce-agent.service` quitando
  `--aplicar` y `systemctl restart`; **o**
- `[SENSOR m4rk] → lo ejecuto yo`: `systemctl stop ppi-publicar-feed.timer` (y reactivar tras A).
- Verificar sets sin elements y **revertir** al terminar A. El procedimiento está en `scripts/modo_sombra.sh` y
  `scripts/restaurar_enforcement.sh`.

### 3. Zona DNS de laboratorio reservada

El resolutor 10.10.10.20 **reenvía a Internet** (resolvió `www.example.com` a IPs públicas) y no tiene zona de
laboratorio (`srv-dmz.lab` no resuelve). El escenario DNS debe usar un dominio reservado que resuelva local y no
consulte a terceros.

- `[DNS/AD 10.10.10.20] → lo ejecutas tú` (requiere acceso al servidor, fuera de mis llaves): crear una zona local
  (p.ej. `*.lab-ppi`) con comodín, o un sinkhole, y confirmar con `dig` que no sale al exterior. Registrar el dominio en
  `escenarios.json` (`ZONA_LAB`).

### 4. Endpoint de fuerza bruta (401)

No existe: `/login` → 404 y 8081 cerrado. Hace falta un servicio aislado que devuelva 401 ante credenciales inválidas.

- `[srv-dmz adminsrvdmz] → lo ejecutas tú`: levantar el endpoint de prueba según `scripts/endpoint_brute_prueba.md`
  (servicio aislado, puerto de laboratorio, Basic Auth con 401). Confirmar con `curl` que da 401 (no 404).

### 5. Captura continua y disco

El anillo `/var/lib/ppi-motor-capture/` guarda ~19 min (76 ficheros de 15 s) y recicla; quedan 21 GB (41 % usado). Para
≥ 120 s antes y ≥ 90 s después por episodio, con ≥ 5 repeticiones × 5 escenarios, hay que archivar en paralelo sin
huecos y prever espacio.

- `[SENSOR m4rk] → lo ejecuto yo`: `scripts/capturar.sh` archiva el PCAP de forma continua durante la ventana de campaña
  y estima el espacio. Decidir la ruta de archivado (disco con sitio).

### 6. Kali

- `[Kali 10.10.20.30] → lo enciendes tú`: ahora está encendida (22 abierto); confirmar en el momento de la campaña. El
  generador corre desde la Kali (`scripts/generar_campana.sh`), **no** en esta fase.

## Comprobaciones benignas que sí puedo repetir sin intervención

- Relojes (`scripts/comprobar_relojes.sh`), alcance a servicios y estado de sets, todo de solo lectura. Se repetirán al
  inicio y al fin de la campaña.
