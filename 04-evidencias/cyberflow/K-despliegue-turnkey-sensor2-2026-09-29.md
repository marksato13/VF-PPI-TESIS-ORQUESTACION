# K · Despliegue llave-en-mano en la 2ª VM (ciclo desinstalar → reinstalar)

**Fecha:** 29 de septiembre de 2026
**Máquina:** `cyberflow-sensor2` (10.10.60.12), Ubuntu 24.04, aislada (sin Internet)
**Objetivo:** probar que la guía instala **desde cero, sin depender del sensor 1**,
ejecutando el ciclo completo desinstalar → reinstalar desde un clon **fresco** de
`main` → `doctor.sh`. Esto convierte «reinstalable» en «replicable».

## Qué se hizo

1. Se transfirió a la VM (dos saltos por el bastión) un `git archive` de
   `main@99d5005` — 211 ficheros, **hash SHA-256 verificado idéntico** en origen
   y destino (`093289a2…8a12d0f`).
2. Se ejecutó un guion de ciclo en la terminal del operador (la contraseña de
   `sudo` y las del panel se tecleron; **ninguna** viajó por argv, fichero ni
   historial: `sudo` usa su prompt y las cuentas del panel van por `read -s` →
   `--stdin`).

## Resultados medidos

**Desinstalador** (versión de `main`, no la vieja del clon): salida
`Comprobacion → Limpio`. Quita todas las unidades, **incluida
`cyberflow-acumular.timer`** (el clon que había en el sensor, `dc8343c`, era
anterior al fix `99d5005` y no la borraba). No toca red, SPAN, usuario, claves
ni `/opt/python3.14`.

**Reinstalación offline** (`instalar.sh`, sin red, desde `ruedas/`):

```
2.1 Interprete que ejecutara el motor
  se creara con: /opt/python3.14/bin/python3.14
  OK    CPython 3.14.4, coincide con el manifiesto
7 Entorno de Python
  OK    instalando sin red desde ruedas/
  OK    dependencias instaladas
  OK    modelo cargado: 28 variables
```

`configurar.sh` en auto-detección (sin preguntas) fijó `interfaz=ens37`,
`mac_esperada=00:0c:29:ea:45:d3`, `red_entidades=10.10.0.0/16`,
`modo=observacion`, y validó el `.toml`.

**`doctor.sh`** (verificación independiente, por runner separado):

```
1. Servicios            7/7 OK (suricata, capture-nic, motor-capture, motor,
                        ppi-dashboard, acumular.timer, limpieza.timer)
2. Captura (ens37)      OK  +1124 paquetes en 4 s
3. Suricata (eve.json)  OK  crece
4. Motor de decision    OK  decidiendo (5 → 50 decisiones en la 2ª pasada)
                        AVISO pcaps ilegibles (acumulado): 1  (benigno, ver abajo)
                        OK  duplicados de espejo descartados: 61708
5. Linea base           OK  multilayer-v3.csv: 6753 filas
6. Disco                OK  48 %
7. Calibracion          AVISO modelo SIN calibrar en esta red (esperado)
8. Panel                OK  escuchando en 8788
```

`ppi-dashboard`: `ActiveState=active`, `SubState=running`, **`NRestarts=0`**
(estable). Panel con TLS + login por rol; huella del certificado
`C2:50:22:5D:DA:67:…`.

## Los dos avisos

- **`sin calibrar`**: esperado. El umbral publicado es de otra red; recalibrar
  está bloqueado por [[cyberflow-prueba-funcional]] / decisión 3 del `ESTADO.md`
  (la línea base es casi todo plano de control STP/CARP, no tráfico de usuarios).
- **`pcaps ilegibles: 1`**: artefacto benigno confirmado. El primer PCAP
  (`live-…072247.pcap`) quedó `tcpdump:tcpdump` antes de que el servicio bajara
  al grupo `m4rk`; el resto son `tcpdump:m4rk`, legibles. Contador acumulado
  desde el arranque del motor; se limpia al salir ese PCAP del anillo (240 s) o
  con `sudo systemctl restart ppi-motor`.

## Defecto encontrado y corregido en esta prueba

`instalar.sh` arrancaba `ppi-dashboard` **antes** de que existieran sus ficheros
de auth (se crean aparte con `cyberflow_usuarios.py`), y su comprobación final
lo marcaba como **`FALLO`** aunque el resto del sistema estuviera sano. Quien
siguiera la guía al pie vería un FALLO alarmante en una instalación correcta.

Corregido: si el panel está habilitado pero faltan `usuarios.json` /
`clave-sesion` / `panel.crt`, ahora se reporta **`AVISO`** con la receta para
crear las cuentas; cualquier otro fallo del panel sigue siendo `FALLO`.

Referencia (producto): `scripts/setup/instalar.sh`, commit **`131ac27`**.

## Post-despliegue: dos bugs más, hallados y corregidos

Vigilando el sistema tras el ciclo aparecieron dos defectos, ambos corregidos:

1. **Los timers se quedaban sin próximo disparo tras reinstalar.** Medido: el
   acumulador corrió cada 10 min de 06:19 a 07:19 y **se paró en la reinstalación
   (07:19)**; `NextElapseUSecMonotonic=infinity`. Causa: los timers usaban
   `OnUnitActiveSec`, que agenda relativo a la última activación del `.service`;
   el `reset-failed`/`daemon-reload` de la reinstalación borra esa marca
   (`ExecMainStartTimestamp=` vacío) y el timer queda *active* pero muerto. Sin
   esto, **la línea base nunca volvería a crecer y la recalibración se quedaría
   sin datos nuevos, sin que nada lo indicara**. Corregido a `OnCalendar`
   (`*:0/10` acumular, `*:0/5` limpieza), que siempre tiene próximo disparo.
   Verificado: tras aplicarlo, `NextElapse=2026-09-29 07:50:00` y la línea base
   pasó de **6753 → 7762 filas** (+1009 en una pasada). Producto: commit `56c01e8`.
2. **`doctor.sh` infravaloraba los avisos.** El aviso de «pcaps ilegibles» se
   imprimía desde el bloque Python sin pasar por la función `aviso()` de bash, así
   que el resumen decía «1 aviso» mostrando 2. Corregido: Python solo extrae los
   números y bash da el veredicto. Producto: commit `f7d0fe8`.

Ambos son del tipo que solo se caza **operando y midiendo**, no leyendo el código.

## Conclusión

La guía instala **de cero, offline, sin depender del sensor 1**, y `doctor.sh`
la da operativa. La replicabilidad queda demostrada; lo único pendiente para
cerrar F08 es la **pertinencia (TAM)** y la **recalibración**, ambas gobernadas
por decisiones abiertas, no por herramienta.
