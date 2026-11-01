# Referencias y hashes congelados (preparación 3A, 2026-11-01)

Todos los sha256 se calculan sobre el contenido con fin de línea LF, tal como lo guarda git.

## Commits de referencia

| Qué | Commit |
|---|---|
| Código del motor (rama `candidato/motor-rendimiento-20261031`, repo del producto) | `24f8a80` |
| Procedimiento de instalación y reversión (paso 1) | `e66f436` |
| Paso 2, validación en vivo | `99fe3e8` |

## Analizador y configuración del 3B (este repositorio)

| Fichero | sha256 |
|---|---|
| `scripts/analizar_3b.py` | `27e67fd1620762d7ec7cb172ea45465ad6edb7db77cf8d69c7c8102c8167050f` (corrección 3A; en e0ba9e0 era `bdd44729…`) |
| `scripts/analizar.py` | `71674908e4fc7f938fc9687cf4b7ad2e4c2b77ad35ff20c0c0fcf59ec92c763a` |
| `scripts/poblacion.py` | `7b140ae42905428e0a2b615c8de88ff9d036c0c7021e2bc096b921597d33511b` |
| `scripts/calidad_fuentes.py` | `d63ca6e96e8de90aec0ee8cd6274d91f006511248223c48658ad3535b642046d` |
| `scripts/extraer_evidencia_destino.py` | `48d13aba2082a044a311a1966817bd6ec62be0c3759bbd1618e5f2dd5b3d508c` |
| `tests/test_analizar_3b.py` | `a1ba06d42b2e15955ef0dfdfb7a77716f5ab9ef6dc17aef6fd382e64a4623db2` (90 comprobaciones; en e0ba9e0 era `ae1a366d…`, 57) |
| `preparacion-3a-2026-11-01/config-campana-3b.json` | `cbf72fbb0f112e3db5cc3724640ee18fb3d42f1bc5e24680f5af25faf1939d60` (versión 3b-2026-11-01.2; en e0ba9e0 era `15686790…`, 3b-2026-11-01.1) |
| `config-campana.json` (primera campaña A, sin cambios) | `1642ba310b7f4b665d2f505cd70e8ccbdf2c4c7fe4f38db45a69dbc10976e65b` |

Las mismas cinco herramientas están en el sensor, en `~/cf-paso3a-20261101T0523Z/herramientas3b/`, con estos hashes.
`analizar_3b.py` se volvió a subir a las 05:48Z, después de añadir la lectura de destinos de formato «a».

## Generador y escenarios (Kali = repositorio)

| Fichero | sha256 |
|---|---|
| `scripts/generar_campana.py` | `c586d813472d5853ae43fe512b5a53d22654699ace10894e43f57b3ddc4b171b` |
| `scripts/esquema_campana.py` | `e762e60421b4721b1e8ce32549049ae10c7e86596b0fbd37f9a35517ab904144` |
| `escenarios/escenarios.json` | `67798012cbd306e9c06ebccf5ec293c7d9db12951d93119f739c3f86a83c64ec` |
| Plan sin tráfico: `config-efectiva.json` | `778c05cdff5e804ccdf33522a983a2dedb4afd94a4bfbaa1af3e5b11902e2019` |
| Plan sin tráfico: `marcas.jsonl` | `025de8e089739c51c7212c8743c4add3fef03e9b630448d8a844170daeeeb723` |

## Sensor (implementación desplegada, verificada al empezar y al terminar el 3A)

| Fichero | sha256 (prefijo) |
|---|---|
| `motor_decision.py` | `6c274d9e3529e3fb…` |
| `motor_incremental.py` | `a403307aa5f76d38…` |
| `heuristicos.py` | `10deb05d22fa0215…` |
| `publicar_feed.py` | `f7bc4c7d8e7ac0cd…` |
| `escalada.py` | `7d80ab4a926457efb37f4c6c9778e53eda67a5840ca255ff4504f333ca638479` |
| Modelo desplegable | `df547da098e51171…` |

Los hashes completos están en `evidencia/sensor/estado-inicial/sha256-implementacion.txt`.

**Procedencia por commit** (corrección 3A, 06:23Z; `evidencia/salidas/out_s11_sensor_codigo.txt` y
`out_s11b_comparacion_local.txt`; el Sensor1 no es un clon git, así que la comparación se hace en local):

| Fichero | Blob desplegado | Commit de procedencia |
|---|---|---|
| `motor_decision.py` | `068c025dc867e753d59167b0e73d9df10db00c64` | `24f8a80` |
| `motor_incremental.py` | `1197907c0d3f8e1c28001485bb43b1ed5fc12375` | `24f8a80` |
| `heuristicos.py` | `ec0fe9e870c2f3c98c0cc9140011674df327f1f3` | `24f8a80` (también 6d92ff3) |
| `feed.py` | `fa30b818f03bf389554559312fc3e596314f3750` | `24f8a80` (también 6d92ff3) |
| `extract_multilayer_v2.py` | `ec46849dc8454976b056622e334cc35b7cc95d26` | `24f8a80` |
| `extract_multilayer_v3.py` | `0739e4cda326c640facb5b6d1def1182a1d8b09c` | `24f8a80` |
| `configs/features/multilayer-v2.json` (sha256 `e032a1a2…`) | `9560ce9e49f569e930dff07f12c3a85a1e7d0a82` | `24f8a80` con CRLF; blob LF `20a89b81…` |
| `publicar_feed.py` | `bf2b73f49fbbd48df8931540d2ff475403f12d15` | **as-deployed** `f57ca00` = tag `validacion-interna-2026-10-15` (6d92ff3); en 24f8a80 es `f73db5af…` |
| `escalada.py` | `7bd55de8fbb261e521ebfbe40ad0a9bf04277dfb` | **as-deployed** `f57ca00` = 6d92ff3; en 24f8a80 es `8f260bd0…` |
| srv-dmz `agente_enforce.py` (sha256 `2985c123…`) | `b769b01cac1cef9c3f1ee5f2ace4d16dc8aabec3` | 6d92ff3; timer y servicio inactive |
| Manifiesto del modelo | — | sha256 `b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7` |

Commits completos: `24f8a80e376d89b78454fd16854d2239a1b7d278`, `f57ca00771030296f0d83d60d8a39b4aad1f5a94`,
`6d92ff3ed7c3573d5def6cb276904501eb5d646a`.

**Herramientas del 3B en el sensor** (`~/cf-paso3a-20261101T0523Z/herramientas3b/`): `analizar_3b.py` = `27e67fd1…`
(la de e0ba9e0 se conserva como `analizar_3b.e0ba9e0.py`, `bdd44729…`); las otras cuatro, iguales a la tabla de arriba.

**Guion de Mark para logrotate** (`~/cf-paso3a-20261101T0523Z/mark/`):

| Fichero | sha256 |
|---|---|
| `04_logrotate_global.sh` (v2, vigente) | `5481d99b1fff5bed7d697017537bfbff35881dfb60a1c9ccb3f21e732e92bfdb` |
| `04_logrotate_global.v1.sh` (e0ba9e0, devolvía el rc de `tail`; no usar) | `af99e727…` |
| `mark-04-logrotate-global-20261101T071105Z.log` (ejecución de Mark, 07:11:05Z: rc_logrotate=0, errores=0, RESULTADO OK) | `7cae51694c5ce508fa7d76bfba6587f08bef1b87693efe8622ae14a54ff0c47b` |
| `mark-04-logrotate-global-20261101T071105Z.salida` (salida completa de `sudo logrotate -d`, 233 líneas) | `b34f523251e10b37fdef1823ec04285a624f9514457754ccda573d97939fd45a` |
| `/etc/logrotate.conf` evaluado | `fc0877189d2feacbfca441dfa4ddeffaebbd074635c48fbf1c70672e62954fe9` |

## Clientes legítimos

| Fichero | sha256 |
|---|---|
| `clientes_factor1.py` | `69d79937f2fee84d8d63a38eb1171ed822858a54fa48d5a1e9266fb4e5a4c6c6` |
| `clientes_lab.py` | `ae5134a778e66d90f5c3fbcd47323e328f3422cf4ba8d5197649f402c1d4cdc3` |

## Feed y escalada (copias con hash)

**Inicio del 3A (05:24Z), en `evidencia/sensor/estado-inicial/`:**

| Fichero | sha256 (prefijo) |
|---|---|
| `feed.json` | `9c7b9835…` |
| `feed.sig` | `73743cf5…` |
| `estado.json` | `5f9c45cc…` |

Los valores completos están en `sha256-feed.txt`.

**Final del 3A (05:44:14Z), en `evidencia/sensor/escalada/`:**

| Fichero | sha256 |
|---|---|
| `feed.json` | `175ffa0571580b66896bd223327d58a9f1eb969a78a6ecb83e7cf21875968f68` |
| `feed.sig` | `01791b5fc2322a819ba18166cfc4fd8893839e5499852084c2343f3af6bda36c` |
| `estado.json` | `0a487138cca5019bd3d82ccc42b679a46849a4ecdd523caf3d3f778f777d3131` |

## Respaldo de logrotate (verificado por Mark con el guion 03, 05:05:21Z)

Directorio `/var/backups/cyberflow-paso2-20261101T0254Z`, root:root 700:

| Fichero | sha256 |
|---|---|
| `antes-paso2` = `cyberflow.anterior` | `7832acf2bb33e0f1fbff6861b6c89d9b65f5eb195170b89fadd713d219123f3d` |
| `suricata.orig-cyberflow` | `f95789a4166f06c69695c31de79bf586cd72c0a862cf50292e35d2ae342f6c96` |
| `/etc/logrotate.d/cyberflow` vigente | `183e7bc4…` |
| Registro de Mark `mark-03-verificar-respaldo.log` | `4dd4cd84…` |

## Evidencia de entrada del re-análisis del paso 2

| Fichero | sha256 |
|---|---|
| `motor_decision.log` (de `p2_motor_decision.log.gz`) | `f344dfa004223fc54a10129bb143346397c78561b07acfa3ea1ac09f1bc30327` |
| Registro de la repetición (de `p2_replay_motor_decision.log.gz`) | `e43f2ce2827cd60a414f01191bd785d79844c55e5822488977814675b3ed5936` |
| `reanalisis-paso2/destinos-3b.csv` | `b6ca71f895307e95bb638f742fe0447b9006f9a76234b308e30df86975f0e16b` (copia del repositorio, LF). En el sensor el módulo `csv` lo escribió con CRLF: `b3d0b11a47d9e053994faea52e57946d2df575acf524594015c2a1fd9f23528f`. El contenido es el mismo. |
| `reanalisis-paso2/calidad-fuentes.json` | `ac1d5080ddd90ec65dacf13253e92f77c27a13fb6870be8a462b04fd8cf4923b` |
| `reanalisis-paso2/actividad-3b.json` | `f9fcf8a2db6d8ce300a0aacfaa9b91c3c43941706a25818b80bb603a97241cf8` |
