# CyberFlow bloque D - validacion del espejo

> Registro generado por `BIN/serial_lib.ps1`. **No se escribe a mano.**
> Cada entrada lleva el comando tal cual se envio y la salida integra del equipo.
> Las contrasenas aparecen como `<REDACTADO>`: el arnes las sustituye antes de escribir.

| Dato | Valor |
|---|---|
| Equipo | CORE-STACK |
| Acceso | consola serie SSH 10.10.99.10 a 0 8N1 |
| Operador | Superadmin Mk |
| Inicio | 2026-09-17 13:06:14 |

**Proposito de la sesion.** Criterio 4 de 03_ESTADO_DEL_SENSOR.md seccion 5: OutDiscards de Gi2/0/19 sigue en 0 tras una ventana de captura. SOLO LECTURA.

---

### Comando 1 - 13:06:14

```text
terminal length 0
```

**Salida**

```text
(sin salida)
```

### Comando 2 - 13:06:14

```text
show interfaces GigabitEthernet2/0/19 counters errors
```

**Salida**

```text
Port           Align-Err     FCS-Err    Xmit-Err     Rcv-Err  UnderSize  OutDiscards 
Gi2/0/19               0           0           0           0          0            0 

Port         Single-Col  Multi-Col   Late-Col  Excess-Col  Carri-Sen      Runts 
Gi2/0/19              0          0          0           0          0          0 

Port           OverSize 
Gi2/0/19              0 
```

### Comando 3 - 13:06:14

```text
show interfaces GigabitEthernet2/0/19 | include packets output|rate
```

**Salida**

```text
  Queueing strategy: fifo
  5 minute input rate 0 bits/sec, 0 packets/sec
  5 minute output rate 21000 bits/sec, 20 packets/sec
     1441226 packets output, 159234326 bytes, 0 underruns
```

---

**Fin de la sesion.** 2026-09-17 13:06:14 - 3 comandos registrados.

Sesion de solo lectura.

