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
| `scripts/analizar_3b.py` | `bdd44729a3f6e6b6619f5ec6c0671b03ea31704ca7f8813608b5505493316000` |
| `scripts/analizar.py` | `71674908e4fc7f938fc9687cf4b7ad2e4c2b77ad35ff20c0c0fcf59ec92c763a` |
| `scripts/poblacion.py` | `7b140ae42905428e0a2b615c8de88ff9d036c0c7021e2bc096b921597d33511b` |
| `scripts/calidad_fuentes.py` | `d63ca6e96e8de90aec0ee8cd6274d91f006511248223c48658ad3535b642046d` |
| `scripts/extraer_evidencia_destino.py` | `48d13aba2082a044a311a1966817bd6ec62be0c3759bbd1618e5f2dd5b3d508c` |
| `tests/test_analizar_3b.py` | `ae1a366dfea333e6c49f8693f684569fb9c2b2dcbb31ac9f2506a02daeccd23c` |
| `preparacion-3a-2026-11-01/config-campana-3b.json` | `156867908a9e6853699c456f845c44d0a099c55a3953149cfa5c594b6c3823fc` |
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
