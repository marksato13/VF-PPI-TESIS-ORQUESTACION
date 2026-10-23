# Runbook campaña v2 — cierre de 4.2/4.3 (escaneo limpio + Suricata ET Open + Nikto)

Corrige los confounds de la corrida del 2026-10-23 (escaneo con tráfico mínimo; Suricata del sensor
sin reglas; desfase de relojes). Orquestador: `orquestar_campana_v2.sh`.

## 0. Prerrequisitos
- Motor con `if_limpio_2026_10` activo; endpoint 401 en srv-dmz:8081 (ver `GUION-CAMPANA-LIMPIO.md`).
- `nikto` instalado en la Kali (`which nikto`); si no, `sudo apt install nikto` o quítalo con `NK=0`.
- Camino DMZ abierto (`nmap -Pn -p80,443 10.10.30.10`).
- **Comparador Suricata+ET Open disponible:** VM `suricata-comparator` **10.10.60.13** (`adminsuricata`),
  Suricata 7.0.3, `/var/lib/suricata/rules/suricata.rules` SHA `7b674459…` (53 013 reglas), HOME_NET
  `[10.10.30.0/24]`, servicio *disabled* (se arranca solo para el ensayo). **Tú tienes acceso; yo no
  tengo llave a esa VM.**

## 1. Captura PCAP en el SENSOR (tu sudo, ya hay wrapper)
```
ssh ... m4rk@10.10.60.11
mkdir -p /tmp/campana-v2
setsid sudo -n /usr/local/sbin/cf-capturar /tmp/campana-v2/pass.pcap 7200 >/tmp/cap.log 2>&1 &
```
(7200 s cubre la campaña con escaneos N=3 y sus esperas de BLOCK; ajusta si usas NS=1.)

## 2. Lanzar el orquestador en la KALI
Transfiérelo (`transferir_a_kali.ps1` apuntando a `orquestar_campana_v2.sh`) y lanza en segundo plano:
```
N=3 NS=3 NB=1 NK=1 setsid bash /tmp/orquestar_campana_v2.sh >/tmp/campana-v2/run.log 2>&1 &
```
- **Escaneo primero** (path abierto, `--min-rate 2000 -p1-5000` para llenar ventanas antes del corte),
  con espera **1 850 s** entre escaneos (la escalera de BLOCK llega a 1 800 s en la 2ª ofensa).
- Duración con N=3/NS=3: ~90–110 min. Para una corrida rápida usa `NS=1` (y captura 1 200 s).
- marcas en `/tmp/campana-v2/marcas.jsonl`.

## 3. Cosecha (yo, en solo lectura, cuando termine)
Te pido el rango horario; recojo `marcas.jsonl` (Kali), recorte de `motor_decision.log` y `pass.pcap`
(sensor), y los `*-corte.gnmap`.

## 4. Análisis CyberFlow
- **En vivo (4.2):** `analizar_vivo.py` + `atribuir_campana.py` (atribución sin solape) → Tabla 8 con
  **escaneo ahora con volumen** → debe disparar `port_scan`→BLOCK y detectarse.
- **Replay (4.3, lado CyberFlow):** `replay_43.py` sobre `pass.pcap`.
- **Tiempos (4.4):** `medir_tiempos.py` con t3 del host (`cf-nft-mostrar`).

## 5. Replay Suricata **ET Open** (TÚ, en la comparadora 10.10.60.13)
1. Copia el PCAP a la comparadora (Tailscale):
   `scp <pass.pcap> adminsuricata@10.10.60.13:/home/adminsuricata/pass.pcap`
2. En la comparadora, corre Suricata **offline** con su config ET Open (sin arrancar el servicio):
   ```
   sudo suricata -r /home/adminsuricata/pass.pcap -l /home/adminsuricata/pass-etopen -k none
   sha256sum /var/lib/suricata/rules/suricata.rules   # debe ser 7b674459...
   suricata -V                                         # 7.0.3
   ```
3. Pásame `/home/adminsuricata/pass-etopen/eve.json` (o el conteo de alertas por IP/firma) y los hashes
   (reglas, YAML). Con eso hago la **Tabla 9 válida** (CyberFlow vs Suricata-ET-Open, mismo PCAP),
   incluido **Nikto** (ET Open debería cazarlo por firma; CyberFlow por conducta).

## 6. Tiempos anclados al reloj del paquete (4.3/4.4)
Hay **desfase Kali↔sensor (~40 s)**. Para "t desde el inicio" usa el **primer paquete del ataque** en el
PCAP (reloj del paquete) como t0, no la marca de la Kali. Entre máquinas (host↔sensor) mide el desfase
antes de restar (ver `GUION-CAMPANA-LIMPIO.md` §1). La comparación interna por replay (quién detecta
primero, mismo PCAP) no necesita esto.

## Qué cierra esto
- **4.2:** escaneo detectado con volumen (ablación 3×3 limpia).
- **4.3:** Tabla 9 válida con Suricata-ET-Open sobre el mismo PCAP + Nikto.
- **4.4:** tiempos t0–t5 con reloj del paquete + t3 del host.
</content>
