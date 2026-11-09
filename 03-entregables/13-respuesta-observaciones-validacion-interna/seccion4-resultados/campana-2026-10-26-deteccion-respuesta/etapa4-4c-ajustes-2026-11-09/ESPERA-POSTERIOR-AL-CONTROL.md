# Espera entre el fin del control y el arranque de la batería (Campaña A, 09-nov-2026)

**Se registra aparte para que no se confunda con el control ni con la batería.**

| Qué | Hora UTC | Hora Perú |
|---|---|---|
| Control normal declarado (`b01 4c`) | 08:15:00Z → 08:45:00Z | 03:15 → 03:45 |
| Fin del control = inicio de la espera | 08:45:00Z | 03:45:00 |
| Intento 1 de `g01` (v2): `PARAR: ya hay un generador` (falso positivo de `pgrep`) | 08:46:21Z | 03:46:21 |
| Intento 2 de `g01` (v3): rc 0 **sin lanzar nada** (el `ssh` interno sin `-n` consume el guion enviado por stdin; causa probable) | 09:20:00Z | 04:20:00 |
| Intento 3 de `g01` (v3, desde fichero con `ssh -n`, hash `05b729eb…`): **lanzado** | 09:34:33Z | 04:34:33 |
| **Inicio real de la batería** (`campana_inicio`, reloj de la Kali) | **09:34:50.276Z** | **04:34:50** |
| Duración de la espera (fin del control → inicio de la batería) | 49 min 50 s | |

## Qué ocurrió durante la espera
- **Clientes:** los seis perfiles siguieron a factor 1,0 (desde 08:09:11Z) sin cambios. No se tocó ningún componente.
- **Sin tráfico de ataque:** ningún generador, `permiso.json`, `corrida/` ni `marcas.jsonl` hasta el intento 3. Los dos intentos fallidos no iniciaron episodios (comprobado en solo lectura en la Kali y el bastión antes del intento 3).
- **Salud:** captura, motor, vía rápida y Suricata `active` sin reinicios; I1–I8 e I5 se reevaluaron inmediatamente antes de cada intento y cumplieron (08:45:54Z, 09:19:38Z y 09:34:05Z).
- **Registro:** la vigilancia de `b01` (una línea por minuto) cubre toda la espera. Esos 50 min **no forman parte del control comparable** (ya declarado y cerrado en 08:45:00Z) **ni de la batería**; el análisis de la 4C debe tratarlos como tiempo de espera con clientes normales, sin episodios.
- **Canal SSH a la Kali:** `ctl-kali` se abrió en el intento 1 y se reutilizó (ControlPersist 5 h); `accesos-kali.log` registra cada lanzamiento (nonces `…084632Z-0ec0efdc5515`, `…092011Z-a15dba8ea50b`, `…093448Z-96a2520f2a6d`).
- **Desviación del procedimiento:** el intento 3 ejecutó el mismo `g01` v3 (hash verificado antes y después de copiarlo, sin BOM ni CR) desde `~/cf-e4/g01_lanzar_bateria_e4.sh` con `ssh -n`, en lugar de por stdin con `r4.sh`. Mismos argumentos (`2026-11-09T08:45:00Z srvdmz-20261109T072027Z`), mismo directorio (`~`) y mismo entorno (solo cambia `XDG_SESSION_ID`).
