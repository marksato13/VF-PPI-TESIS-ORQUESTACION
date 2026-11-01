# Comandos del paso 3B (ID 20261101T0721Z), en orden

Los guiones están en `guiones/` y sus salidas en `guiones/salidas/`.

**Cómo se lanzaron.**

- Se lanzaron desde el portátil con `guiones/r.sh <guion> <host>`.
- `r.sh` pasa el guion por SSH al bastión (`gadmin@10.10.10.30`, llave `~/.ssh/id_ed25519`). Desde allí, cuando
  hace falta, salta al host destino con su propia llave: sensor `m4rk@10.10.60.11`, srv-dmz
  `adminsrvdmz@10.10.30.10`, Kali `adminatacante@10.10.20.30` y clientes `adminclientes@10.10.20.20`.
- No hay contraseñas en ningún guion. El único paso con sudo y contraseña lo ejecutó Mark (paso 10).

## 1. Comprobaciones previas (07:21–07:24)

`[LAPTOP Git Bash → BASTIÓN gadmin]` → lo ejecuté yo
```
bash r.sh c00_bastion.sh bastion        # hosts, HTTP/HTTPS 200, DNS
bash r.sh p10b_relojes.sh bastion       # relojes
```
`[LAPTOP → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuté yo
```
bash r.sh c01_sensor.sh sensor          # motor, sombra, 11 hashes, feed inicial, disco/memoria, logrotate, drops
```
`[LAPTOP → BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → lo ejecuté yo
```
bash r.sh c02_srv.sh srv                # agente en sombra, sin tabla nft, ppi-brute-lab activo
```
`[LAPTOP → BASTIÓN gadmin → KALI adminatacante]` → lo ejecuté yo
```
bash r.sh c03_kali.sh kali              # hashes del generador, esquema y escenarios
```
`[LAPTOP → BASTIÓN gadmin → CLIENTES adminclientes]` → lo ejecuté yo
```
bash r.sh c04_clientes.sh clientes
```
`[LAPTOP → BASTIÓN gadmin]` → lo ejecuté yo (la credencial de control se lee en una variable y no se imprime)
```
bash r.sh c05a_brute_prep_completa.sh bastion   # 401 / 401 / 200 / 404 desde 10.10.10.30
```

## 2. Archivo y muestreo (07:24:32)

`[LAPTOP → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuté yo
```
bash r.sh s10_sensor_archivador.sh sensor   # archivar_captura.sh (2181af5f), intervalo 20 s; registra el byte inicial del EVE
bash r.sh s11_sensor_muestreador.sh sensor  # muestreo de recursos (relanzado tras el fallo del primer intento)
```

## 3. Clientes a factor 1,0 (07:26:15)

`[LAPTOP → BASTIÓN gadmin → CLIENTES adminclientes]` → lo ejecuté yo (`sudo -n` sin contraseña, permitido en ese host)
```
bash r.sh k01_clientes_factor1.sh clientes  # para cyberflow-lab.target y lanza los seis envoltorios a factor 1,0
```

## 4. Declaración del control (07:28:02)

`[LAPTOP → BASTIÓN gadmin]` → lo ejecuté yo
```
bash r.sh b01_bastion_control.sh bastion    # control-declarado.json [07:32:00, 08:05:00] + vigilancia de accesos
```

## 5. Batería (08:05:21)

`[LAPTOP → BASTIÓN gadmin]` → lo ejecuté yo. El guion comprueba la sombra en el sensor y en srv-dmz, hace la c05
mínima y mide los relojes. Después entra por SSH en la Kali y lanza:
```
bash r.sh g01_lanzar_bateria.sh bastion
```
`[KALI adminatacante]` (lanzado por g01, con setsid nohup)
```
python3 -u /home/adminatacante/cf-campana-A/scripts/generar_campana.py \
  --config /home/adminatacante/cf-campana-A/escenarios/escenarios.json \
  --salida-dir /home/adminatacante/cf-3b-20261101T0721Z/corrida --autorizado
```
`[BASTIÓN gadmin]` (programado por g01, a las 08:49:02): `c05_brute_prep.sh minima`

## 6. Fin, copia de marcas y relojes (10:05)

`[LAPTOP → BASTIÓN gadmin → KALI adminatacante]` → lo ejecuté yo: comprobar el rc del generador, copiar
`corrida/` al bastión y al sensor, y medir los relojes (`p10b_relojes.sh`). Los accesos quedan en
`evidencia/bastion/accesos-kali.log`.

## 7. Cierre (10:05:58 – 10:36:39)

`[LAPTOP → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuté yo
```
bash s20_verificar_cierre.sh 1793527325.818114                         # condiciones 1-4
bash s30_replay.sh 2026-11-01T07:24:40Z 2026-11-01T10:05:30Z           # segmento EVE + replay_motor.py (c93c80c8)
bash s40_cierre.sh                                                      # tras rc=0 del replay: para el archivador y copia las fuentes
```

## 8. Restauración (10:36:55)

`[LAPTOP → BASTIÓN gadmin → CLIENTES adminclientes]` → lo ejecuté yo: `bash ~/cf-3b-20261101T0721Z/clientes_restaurar.sh`.

`[LAPTOP → BASTIÓN gadmin → SRV-DMZ adminsrvdmz]` → lo ejecuté yo: `sudo -n systemctl stop ppi-brute-lab`.

## 9. Análisis (10:37:46 – 11:25:45)

`[LAPTOP → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuté yo (setsid nohup; salida en `~/cf-3b-20261101T0721Z/s50.out`)
```
bash s50_analisis.sh 2026-11-01T07:24:40Z 2026-11-01T10:05:30Z
```
Pasos y argumentos exactos en `guiones/s50_analisis.sh`.

## 10. Descartes de tcpdump (10:51:44)

`[BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecutó Mark, porque necesita sudo con contraseña (tcpdump corre como el
usuario `tcpdump` y m4rk no puede enviarle la señal)
```
ssh -t -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'bash ~/cf-3b-20261101T0721Z/mark/05_descartes_tcpdump.sh'
```

## 11. Hashes de los voluminosos (10:43)

`[LAPTOP → BASTIÓN gadmin → SENSOR1 m4rk]` → lo ejecuté yo
```
bash r.sh s60_hashes_voluminosos.sh sensor    # → ~/cf-3b-20261101T0721Z/voluminosos-sha256.txt
```

## 12. Descarga, tablas y manifiesto

`[LAPTOP Git Bash]` → lo ejecuté yo. La descarga se hace con `tar` por SSH a través del bastión. Los
`SHA256SUMS` de `copias/` y `analisis/` se verificaron con `sha256sum -c`, y los registros grandes se comprimieron
con `gzip -n -9` (originales en `evidencia/sensor/SHA256-ORIGINALES-COMPRIMIDOS.txt`).
```
python -I herramientas-informe/resumir_3b.py --evidencia evidencia/sensor \
  --umbrales-alfa ../../4.1-modelos/calibracion-alfa-2026-10-24/umbrales-alfa-precision-completa.json --salida tablas
find . -type f ! -name MANIFIESTO.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFIESTO.sha256
sha256sum -c MANIFIESTO.sha256
```
