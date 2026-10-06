# Piloto pasivo de Suricata comparador

Fecha: 2026-10-02. Ejecutado por Mark en `suricata-comparator` mediante
`sudo bash /home/adminsuricata/15-piloto-pasivo-suricata.sh`.

## Alcance y resultado

- Solo se arranco Suricata en la VM comparadora; sin ataques, sin IPS/bloqueo y
  sin cambios de pfSense, CORE-STACK ni Sensor1.
- `suricata.service` cargo `53013` reglas correctamente (`0` fallidas), en modo
  IDS con AF_PACKET en `ens37`.
- El script observo el servicio activo, espero 75 s despues del arranque,
  resumio los logs y lo detuvo en su salida. Consulta posterior por SSH:
  `inactive` y `disabled`.
- En el periodo se registraron 3 eventos `stats` y 10 eventos `http`; no hubo
  lineas JSON invalidas. Los 10 HTTP etiquetados indicaron VLAN 10. No hubo
  `alert` en este piloto benigno; eso no prueba la tasa de deteccion.
- `ens37` siguio UP/PROMISC, sin IP; `ens34` siguio en `10.10.60.13/24`.

## Contadores observados

| Metrica | Antes | Despues | Delta |
|---|---:|---:|---:|
| RX interfaz ens37 | 529719 | 535626 | +5907 |
| rx_dropped interfaz ens37 | 47750 | 48827 | +1077 |
| `capture.kernel_packets` de Suricata en ultima muestra de stats.log | — | 1657 | No comparable directamente con RX de todo el script |

Las muestras de `capture.kernel_packets` leidas del log fueron 264, 625, 1230
y 1657. El periodo de RX de interfaz cubre tambien el tiempo de inicio/carga
de firmas antes de que Suricata quede capturando. `rx_dropped` de Linux no se
interpreta automaticamente como paquetes perdidos por la aplicacion; los
contadores del driver vmxnet3 y de captura se revisaran conjuntamente antes de
atribuir perdidas. En el stats.log leido no aparecio un contador no nulo
`capture.kernel_drops`.

## Evidencias de integridad

| Archivo en comparador | SHA-256 tras el piloto |
|---|---|
| `/var/log/suricata/eve.json` | `e053daa596f50be64b8be65fb069d1266c872b1506c0ad82c3fed30df1394479` |
| `/var/log/suricata/stats.log` | `9ecf1e47f7f26f9c1b15af2d016f6c924da82d40251f3af3d48862a606571b31` |
| `/var/log/suricata/suricata.log` | `9568350a6b1f893077a0b6e0596fbdd7d15a0e5ef1736055f03b5eb9d03741ed` |

Son archivos locales de la VM y contienen metadatos de red: no se copiaron al
repositorio. Si se vuelve a iniciar el servicio, esos logs pueden cambiar y
sus hashes historicos dejan de representar el estado nuevo.

## Limites antes del experimento formal

1. Solo se observaron eventos HTTP de VLAN 10 en este periodo; no se comprobo
   el procesamiento por Suricata de trafico de Kali/clientes VLAN 20 a la DMZ
   VLAN 30. El SPAN recibe etiquetas de otras VLAN en pruebas previas, pero no
   equivale a una prueba de esta ruta bajo un episodio conocido.
2. No comparar marcas de tiempo todavia. Lecturas cercanas por SSH indican
   desfase aproximado de 179 s entre comparador y Sensor1. Ambos estan sin
   NTP sincronizado.
3. El piloto no mide TPR, FPR ni latencia de alerta. Tampoco prueba bloqueo:
   el comparador esta en IDS pasivo y el modelo CyberFlow se observa por SPAN.
