# Guion de campaña instrumentada — modelo limpio `if_limpio_2026_10`

**Objetivo:** una sola corrida produce las entradas de las tres tablas de la Sección 4:
- **Tabla 8 (4.2, ablación):** IF limpio / heurísticos / combinado, por ventana y por episodio.
- **Tabla 9 (4.3, Suricata):** CyberFlow actual vs Suricata sobre el **mismo PCAP** (replay).
- **Tabla 10 (4.4, tiempos):** t0–t5 de la cadena de respuesta.

**Diseño:** ataques **en vivo** (el motor decide y queda en `motor_decision.log`) **+ captura de
PCAP simultánea** (para el replay offline a Suricata y al modelo limpio). Reúsa el método de
replay ya validado (`19-METODO-REPLAY-PCAP.md`, `22-correr-piloto.py`, `20-puntuar-por-ventana.py`).

**Reglas que respeta:** no reentrena, no cambia el despliegue, no modifica reglas/config/artefactos.
Enforcement real SÍ ocurre (es lo que medimos), pero el modelo y los umbrales quedan intactos.

> **Qué hago yo y qué haces tú.** Tú ejecutas lo que necesita tu `sudo` / la Kali (captura PCAP,
> lanzar ataques). Yo preparo, y luego **mido en solo lectura** por el relay y corro los análisis.

---

## Parámetros fijos (modelo limpio desplegado)

```
Modelo     : /home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib
Manifest   : /home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json
Detector   : if_limpio_2026_10
Umbral     : score_samples < -0,569397  (= decision_function < -0,069397)
Extractor  : /home/m4rk/cyberflow/scripts/features/extract_multilayer_v2.py
Esquema    : /home/m4rk/cyberflow/configs/features/multilayer-v2.json
Heuristicos: producto-main/scripts/engine/heuristicos.py  (VERSION_UMBRALES 2026-10-06.2)
Atacante   : 10.10.20.30 (Kali)   Objetivo DMZ: 10.10.30.10   Resolver: 10.10.10.20
```

## 0) Prerrequisitos (verificar antes)

1. Motor vivo con el modelo limpio: `systemctl is-active ppi-motor` y la línea de arranque
   apunta a `if_limpio_2026_10` (ya verificado el 23-oct).
2. Endpoint 401 para fuerza bruta levantado en srv-dmz:8081 (ver `GUION-DEMO-EN-VIVO.md`):
   ```
   ssh gadmin@10.10.10.30 "ssh -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 \
     'setsid python3 /home/adminsrvdmz/endpoint_401.py --port 8081 >/tmp/ep.log 2>&1 </dev/null &'"
   ```
   Comprobar: `nmap -Pn -p8081 10.10.30.10` → `open`.
3. Camino a la DMZ abierto: `nmap -Pn -p80,443 10.10.30.10` → `open`.
4. Suricata instalado con ET Open congelado (ver `09`/`12`/`14` de comparacion-cyberflow-suricata)
   y su **versión + SHA del ruleset anotados**.
5. Espacio en disco en el sensor para el PCAP (una campaña de ~40 min con host 10.10.20.30 es
   modesta, pero confírmalo).

## 1) Sincronización de relojes (clave para 4.4 entre máquinas)

NTP está cerrado en VLAN 60 (nota 19). Para poder restar marcas entre Kali/sensor/host, **captura
el desfase**. Desde tu terminal, lo más cercano posible en el tiempo:
```
date -u +%s.%N                                             # tu reloj (ref)
ssh gadmin@10.10.10.30 "date -u +%s.%N; ssh -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 date -u +%s.%N"
ssh gadmin@10.10.10.30 "ssh -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 date -u +%s.%N"
```
Anota los cuatro valores. Si las máquinas NO están sincronizadas, los **t0–t5 entre máquinas** se
corrigen con esos desfases (y se declara la incertidumbre). La detección de 4.3 no necesita esto:
el replay usa el reloj del propio paquete.

## 2) Arranque de la captura PCAP (en el SENSOR, tu `sudo`)

```
sudo tcpdump -i ens37 -w /home/m4rk/campana-limpio-$(date -u +%Y%m%dT%H%M%SZ).pcap host 10.10.20.30
```
Déjalo corriendo en una terminal. (El espejo duplica tramas; la deduplicación la hace el extractor
en el replay, igual que en producción — nota 19.)

## 3) Lanzar el orquestador (en la KALI)

Copia `orquestar_campana.sh` a la Kali. Desde tu terminal:
```
B64=$(base64 -w0 < "orquestar_campana.sh")          # (en Windows: usa certutil o pégalo a mano)
ssh -t gadmin@10.10.10.30 "ssh -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 \
  'echo $B64 | base64 -d > /tmp/orquestar_campana.sh && chmod +x /tmp/orquestar_campana.sh'"
```
Ejecuta (N=3 por familia, 1 de fuerza bruta):
```
ssh -t gadmin@10.10.10.30 "ssh -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 \
  'N=3 NB=1 bash /tmp/orquestar_campana.sh'"
```
Dura ~35–45 min (las esperas de expiración del BLOCK dominan). Al final imprime y guarda
`/tmp/campana-limpio/marcas.jsonl` (t0/t_fin por episodio, reloj de pared + monotónico) y los
`*-corte.gnmap` (prueba del corte real).

## 4) Parar captura y recolectar evidencia

- Detén el `tcpdump` (Ctrl-C en el sensor).
- Avísame con el rango horario de inicio/fin. Yo recojo en **solo lectura** por el relay:
  - `motor_decision.log` (recorte de la ventana de la campaña),
  - el feed firmado (`/home/m4rk/feed/feed.json` + journal de `ppi-publicar-feed`),
  - el log del agente / `nft list ruleset` **en el host protegido** (sello t3/t4/t5),
  - `marcas.jsonl` y los `*-corte.gnmap` de la Kali,
  - el PCAP de la campaña (o lo troceas tú por episodio con los tiempos de `marcas.jsonl`).

## 5) Análisis 4.2 + 4.4 en vivo (`analizar_vivo.py`)

Con `marcas.jsonl` + el recorte de `motor_decision.log`:
```
python analizar_vivo.py --marcas marcas.jsonl --log motor_slice.jsonl \
  --entity 10.10.20.30 --margen 150 --out ../4.2-ablacion/campana
```
Produce `Tabla8-campana.md`, `detalle-por-episodio.csv` (modelo/heur/combinado + t1 por episodio)
y `ablacion-campana.json` (entrada para `30-metricas.py`, que da cobertura y latencia mediana).

## 6) Análisis 4.3 replay a Suricata (reúsa `22-correr-piloto.py` con el modelo LIMPIO)

Trocea el PCAP por episodio (con los t0/t_fin de `marcas.jsonl`), p. ej. con `editcap -A/-B` o
`tshark`. Por cada episodio, en el SENSOR (tiene el extractor y el modelo):
```
python3 22-correr-piloto.py --id E-scan-1 --pcap episodio-E-scan-1.pcap \
  --t-inicio <t0 ISO del episodio> --familia scan \
  --extractor /home/m4rk/cyberflow/scripts/features/extract_multilayer_v2.py \
  --schema  /home/m4rk/cyberflow/configs/features/multilayer-v2.json \
  --modelo  /home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib \
  --manifest /home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/manifest-if-limpio-2026-10.json \
  --detector-name if_limpio_2026_10 \
  --scorer ./20-puntuar-por-ventana.py --entity-network 10.10.0.0/16 \
  --outdir ./resultados-campana-limpio
```
Esto da, por episodio, primera alerta de Suricata vs primera ventana del modelo limpio sobre el
MISMO PCAP (Tabla 9). Suricata con la versión/ruleset congelados (anótalos). Nikto como control
aparte, con su N real.

> El heurístico en el camino de replay no lo da `20-puntuar-por-ventana.py` (solo el modelo). El
> veredicto heurístico por ventana sale del `motor_decision.log` en vivo (paso 5), o se calcula
> sobre el `features.csv` que emite el extractor con `heuristicos_por_ventana.py` (incluido aquí).

## 7) Tiempos t0–t5 (4.4) — fuente de cada sello

| Sello | Qué es | Fuente |
|---|---|---|
| t0 | lanzamiento del ataque | `marcas.jsonl` (Kali) |
| t1 | primera señal atribuible | `motor_decision.log` (1ª ventana con `decision != PERMIT`) |
| t2 | emisión de la acción (feed) | `feed.json` / journal de `ppi-publicar-feed` |
| t3 | regla nftables aplicada | log del agente / `nft` en el **host protegido** |
| t4 | efecto en el tráfico | `*-corte.gnmap` (open→filtered) |
| t5 | expiración/reversión | agente + nmap tras la caducidad |

Cálculos: detección t1−t0; señal→decisión t2−t1; propagación t3−t2; total t3−t0. **Entre máquinas,
aplicar el desfase del paso 1 y declarar la incertidumbre.** La **duración de inferencia** con reloj
monótono **no la registra hoy el motor** → se reporta **"no medido"** (instrumentarla sería un
experimento aparte que toca el código del motor; no se hace durante el análisis).

## 8) Honestidad (va en el análisis, no se esconde)
- N=3 por familia sin firma, N=1 fuerza bruta (control) y N=1 Nikto (control con firma). Es piloto
  ampliado, no campaña grande: reportar el N real, no como estimación estable.
- "No detectado" donde no haya señal; nunca 0 s ni ventaja ficticia.
- Suricata 0/9 (si se repite) es alcance del ruleset ET Open por defecto, no un absoluto.
- Una captura del panel no prueba aplicación en el host: el sello t3 sale del `nft`/agente.
</content>
