# CyberFlow desplegado sobre tráfico real — primera medición

**2026-09-17, `cyberflow-sensor` (10.10.60.11).** Motor en **modo observación**, sin
`--enforce`.

---

## 1. Lo que está corriendo

```
suricata.service               active
cyberflow-capture-nic.service  active     promiscuo, sin descargas, sin IPv6
ppi-motor-capture.service      active     anillo de 16 x 15 s = 240 s en ens37
ppi-motor.service              active     OCSVM, modo observacion
```

## 2. Lo que hubo que adaptar del repositorio

Las unidades publicadas asumen el laboratorio anterior. Ninguna funcionaba tal cual:

| Parámetro | Repositorio | Esta topología |
|---|---|---|
| Interfaz de captura | `ens35` | `ens37` |
| Filtro BPF | `10.20.0.0/24 ↔ 10.30.0.0/24` | sin filtro |
| `--entity-network` | `10.20.0.0/24` | `10.10.0.0/16` |
| Usuario / rutas | `useransible`, `/home/useransible/vf-sistema-final` | `m4rk`, `/home/m4rk/cyberflow` |
| Enforcement | `--enforce --block-timeout-seconds 120` | **desactivado** |

El `--enforce` se desactiva a propósito: con un espejo SPAN el sensor observa pero no
está en el camino del tráfico. Ver `03_ESTADO_DEL_SENSOR.md` §7.

**Lo que sí funcionó sin tocar nada:** el extractor salta etiquetas 802.1Q y QinQ
(`while ether_type in (0x8100, 0x88A8)`), así que las tramas espejadas se parsean
correctamente. Era el riesgo mayor y no se materializó.

## 3. El entorno congelado no es reproducible en el sensor

`requirements-model.txt` está fijado para **CPython 3.14.4**. El sensor tiene 3.12.3, y
tres de las seis dependencias **no existen** para esa versión:

| Fijado | Máximo disponible para cp312 |
|---|---|
| `numpy==2.5.1` | 2.2.6 |
| `scikit-learn==1.9.0` | 1.7.2 |
| `scipy==1.18.0` | 1.16.3 |

El modelo carga y puntúa con las versiones disponibles, pero scikit-learn avisa:

```
Trying to unpickle estimator OneClassSVM from version 1.9.0 when using
version 1.7.2. This might lead to breaking code or invalid results.
```

Prueba funcional: `n_features_in_ = 28`, `decision_function(zeros) = -1.813083`.

> **Esta configuración sirve para ver el sistema en marcha. No sirve para ninguna
> medición que vaya a la tesis.** Un resultado obtenido sobre una combinación que la
> propia biblioteca marca como no soportada no es defendible ante un tribunal.

## 4. La medición: 92,4 % de falsos positivos

Primeros minutos sobre tráfico real, sin ningún ataque en curso:

```
decisiones totales : 92  en 7 ventanas
  ALERT     85    92,4 %
  PERMIT     7     7,6 %
umbral : 1,8126
```

**Ninguna de esas alertas es un ataque.** Las entidades señaladas son:

```
10.10.40.2   10.10.50.2   10.10.60.2   10.10.70.2   10.10.90.2   10.10.99.254
```

Son **las interfaces de VLAN de pfSense**, emitiendo sus anuncios CARP. El motor está
marcando como anómalo el latido normal del cortafuegos.

Ejemplos con sus cuentas de paquetes:

```json
{"decision":"ALERT","entity_ip":"10.10.40.10","packet_count_10s":6,"score":0.366}
{"decision":"ALERT","entity_ip":"10.10.60.10","packet_count_10s":6,"score":1.039}
{"decision":"ALERT","entity_ip":"10.10.99.254","packet_count_10s":1,"score":0.0}
```

Ventanas de 1 a 6 paquetes. El modelo se entrenó con campañas de laboratorio donde una
ventana normal tenía órdenes de magnitud más tráfico; aquí **cualquier cosa parece
anómala porque no hay casi nada**.

### Por qué esto es un buen resultado

`04_FEATURES_OSI.md` §6 y `06_PENDIENTES_Y_TRAMPAS.md` §3 predijeron que el modelo
entrenado con datos simulados no sería trasladable. **Ahora está medido, no supuesto.**
La cifra —92,4 % de falsos positivos sobre tráfico real— es exactamente la línea base
contra la que se medirá la mejora de la recalibración.

## 5. Vuelta atrás

```bash
sudo systemctl disable --now ppi-motor ppi-motor-capture
sudo rm /etc/systemd/system/ppi-motor.service /etc/systemd/system/ppi-motor-capture.service
sudo systemctl daemon-reload
rm -rf ~/cyberflow
```

## 6. Lo que queda abierto

| # | Asunto |
|---|---|
| 1 | **El entorno congelado no es reproducible**: 3.14 frente a 3.12. Decidir entre montar 3.14 o recongelar sobre 3.12 |
| 2 | **Recalibrar**: bloqueado hasta que haya tráfico que merezca llamarse línea base |
| 3 | **Generar tráfico**: sigue siendo lo único que desbloquea la tesis |
| 4 | Panel web: `ppi-dashboard.service` sin desplegar |
