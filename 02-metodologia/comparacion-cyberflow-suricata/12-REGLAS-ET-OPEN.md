# Reglas del comparador: instantanea ET Open

Fecha de preparacion: 2026-10-02. No se cambio Sensor1 ni se inicio el
Suricata del comparador.

## Por que hace falta un conjunto de firmas

Sensor1 ejecuta Suricata `7.0.3` y alimenta CyberFlow con `eve.json`, pero
su `rule-files` solo incluye `/var/lib/suricata/rules/suricata.rules`, que
actualmente mide **0 bytes** (SHA-256 de archivo vacio `e3b0c442...`). Tampoco
existe `/etc/suricata/rules/local.rules`. Esto no demuestra que no haya
telemetria, pero no permite afirmar deteccion por firmas en ese despliegue.

El comparador se define como **Suricata 7.0.3 + ET Open congelado**, mientras
CyberFlow usa Suricata como fuente de eventos mas su propio detector. La
comparacion sera entre dos estrategias de decision, no entre dos productos
completamente independientes en la obtencion de telemetria.

## Instantanea preparada fuera de los sensores

En un contenedor Ubuntu 24.04 con Suricata `7.0.3` y `suricata-update 1.3.0`, se
ejecuto `suricata-update --suricata-version 7.0.3 --no-test --no-reload --fail`
con destino aislado. El programa descargó su fuente por omision:

`https://rules.emergingthreats.net/open/suricata-7.0.3/emerging.rules.tar.gz`

Salida: 68966 reglas escritas en el archivo, 53013 habilitadas, 14 desactivadas
por el procesamiento de protocolo. Los numeros proceden de la salida del
generador; la carga real debe confirmarse con `suricata -T` en el comparador.

| Artefacto | SHA-256 |
|---|---|
| `suricata.rules` dentro del tarball | `7b674459975dd56af2d03363b27df4ad6ff53e724e3c04ff65913701ddd5f4e9` |
| Tarball `et-open-20261002.tar.gz` | `3facf0eaed30caf56d2eba43d96ccd2b79dcc851c8d6be4c822e67b4120a7355` |

Ruta local del tarball:

`C:\Users\markp\AppData\Local\Temp\opencode\et-open-20261002.tar.gz`

Mark copio el tarball al comparador por Tailscale y se verifico su SHA-256.
Igual que para el bundle APT, el
transporte directo Windows/Tailscale es el camino que funciono; Mark introduce
su contrasena en su terminal:

```powershell
scp 'C:\Users\markp\AppData\Local\Temp\opencode\et-open-20261002.tar.gz' adminsuricata@10.10.60.13:/home/adminsuricata/
```

En el comparador se preparo una configuracion de prueba sin privilegios en
`/home/adminsuricata/suricata-compare-trial-20261002/`. Se comprobaron el hash
del tarball y el SHA-256 de `suricata.rules` antes de extraer archivos. La
configuracion de prueba apunto a reglas y clasificaciones en ese directorio,
sin cambiar `/etc/suricata`.

La ejecucion de `suricata -T -c .../suricata.yaml -l .../logs` tuvo resultado
correcto: **53013 reglas cargadas, 0 fallidas** y mensaje de configuracion
validada. Se genero `13-preparar-prueba.py` para repetir la preparacion de la
prueba sin tocar el servicio.

Para el paso definitivo se preparo `14-aplicar-config-suricata.sh` en la VM
comparadora, verificado con `bash -n` y hash
`3563edb11856444635f97f3e30144dfc29229729b74309fea71f1f2c104ec8a4`.
Verifica los hashes, respalda YAML/clasificacion/reglas, aplica solo en el
comparador y vuelve a ejecutar `suricata -T`. Si falla, restaura archivos; no
arranca el servicio. Mark lo ejecuto con sudo y supero la validacion definitiva:

```text
Configuracion proporcionada cargada correctamente.
/etc/suricata/suricata.yaml SHA-256:
d0ea918591040108586e43fb30e51c3583f6d61f6ed1acd8dff938150b303650
/etc/suricata/classification.config SHA-256:
3924e356b2c645763a058a66607f0612e10e01fe817d0eb7b07c34ede5021d16
/var/lib/suricata/rules/suricata.rules SHA-256:
7b674459975dd56af2d03363b27df4ad6ff53e724e3c04ff65913701ddd5f4e9
Respaldo: /root/suricata-compare-backup.NnRaLU8Z
```

Consulta SSH posterior: Suricata `7.0.3`, servicio `disabled`/`inactive`,
`ens34` conserva `10.10.60.13/24`, `ens37` sigue UP/PROMISC sin IP, y hay 11 GB
disponibles en `/`. No se hicieron cambios en Sensor1. Los `53013` cargados
provienen de la prueba aislada; la prueba definitiva salio bien, pero aun no
se habian registrado eventos de una sesion viva.

Configuracion propuesta: AF_PACKET
`ens37`, `HOME_NET=[10.10.30.0/24]` para el servidor protegido, y
`EXTERNAL_NET=!$HOME_NET` (incluye Kali y clientes de VLAN 20). Es una decision
metodologica previa al ensayo; no se ajustara despues de ver el resultado.

Las dos validaciones `-T` ya pasaron. Se ejecuto una prueba pasiva acotada con
`15-piloto-pasivo-suricata.sh`, que arranca el servicio unicamente en el
comparador, observa eventos y contadores durante 75 s y detiene el servicio al
salir, incluso si hay fallo. Resultado en `16-PILOTO-PASIVO-20261002.md`.

El ensayo debera guardar hash de YAML, reglas, fecha de descarga,
versiones, filtros y eventos EVE. No se ha demostrado aun que estas firmas
alerten sobre los ataques elegidos.
