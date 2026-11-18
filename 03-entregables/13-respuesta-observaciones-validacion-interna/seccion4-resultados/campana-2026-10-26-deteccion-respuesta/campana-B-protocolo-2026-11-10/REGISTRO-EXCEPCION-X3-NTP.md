# Registro de la excepción de X3 para la repetición de la Campaña B

**Aprobada por Mark el 2026-11-10 16:30:05Z (11:30 Perú), antes de ejecutar la repetición.** Es un cambio de regla declarado de antemano; no se decidió a la vista de resultados de la repetición.

## Regla original (vigía 2026-11-06.1, sha256 `2fe00200e755fd02…`, intacto)
X3: cualquier flujo de la Kali hacia un destino fuera de la lista blanca (10.10.10.20 y 10.10.30.10) **durante un episodio** cancela la campaña.

## Qué ocurrió con la regla original
La primera ejecución (10-nov, 10:41–11:12 Perú) se canceló con 5 de 25 episodios completos: a las 16:09:43Z el vigía cancelo por «tráfico de la Kali a 200.25.3.17:123 (flow) durante un episodio». Se verificó (solo lectura) que ese flujo es la sincronización horaria de `systemd-timesyncd` de la Kali (servidor 200.25.3.17 = 2.debian.pool.ntp.org, intervalo 2.048 s; 28 flujos de 1 paquete y 94 B por sentido, con puertos de origen efímeros e intervalo 2.040–2.057 s) y que fue el único flujo fuera de la lista blanca durante los cinco episodios.

## Excepción aprobada
Un evento EVE `flow` queda exento de X3 **solo si cumple todo**:
1. origen = Kali (10.10.20.30);
2. protocolo UDP, puerto de destino 123;
3. destino = **200.25.3.17** (lista cerrada `--ntp-permitido`);
4. **como máximo 4 paquetes y 400 bytes en cada sentido** (lo observado: 1 paquete y 94 B).
Todo lo demás sigue cancelando (otro destino, otro puerto o servicio del mismo servidor, TCP, flujos mayores, eventos que no sean `flow`, flows sin tamaños). Cada exención se cuenta (`ntp_excepcion_total`) y queda en la ronda del vigía (`eve_ntp_excepcion`).

## Implementación (ficheros y hashes)
- `generador/vigia_4c_b.py` sha256 `a4b64381fc54313f…` (8 sustituciones exactas sobre el vigía firmado, `herramientas/hacer_vigia_b.py`); instalado junto a los originales en `~/cf-e4/vigia-20261106/` de bastión y Sensor1 (originales `vigia_4c.py` 2fe00200e755fd02 y `salud_captura.py` 274b4d613357be60 intactos).
- `guiones/g01b_lanzar_bateria_b.sh` sha256 `96f4f69dc67df403…`: usa la variante con `--ntp-permitido 200.25.3.17`, comprueba su hash en ambos hosts y exige que el servidor NTP de la Kali (`timedatectl show-timesync -p ServerAddress`) sea 200.25.3.17 antes de lanzar. Si `timesyncd` cambiase de servidor, X3 volvería a cancelar (fallo seguro).
- Pruebas: `tests/test_vigia_b.py` (21), `tests/test_g01b_comillas.py` (2); 12/12 mutaciones; 172 pruebas en el banco.

## Consecuencias para la lectura de resultados
- La repetición usa X3 con esta excepción; los 5 episodios de la primera ejecución se hicieron con X3 original y **se conservan solo como evidencia parcial** (no se mezclan con la repetición): Sensor1 `~/cf-e4/4c-B-cancelada-X3-completo-20261110T1615Z`; Kali `/home/adminatacante/cf-e4-4c-B-cancelada-X3-20261110T1626Z`; bastión `/home/gadmin/cf-e4/4c-B-cancelada-X3-20261110T1626Z`; srv-dmz `/var/lib/cyberflow/reversion-B/` y `traza-B-20261110T161315Z.jsonl`.
- La campaña A (4.ª corrida) usó X3 sin excepción; en esa corrida no ocurrió coincidencia entre una consulta NTP y un episodio.