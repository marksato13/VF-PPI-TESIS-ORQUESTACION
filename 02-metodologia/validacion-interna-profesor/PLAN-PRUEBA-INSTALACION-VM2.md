# Plan — instalación desde cero en la VM2 y verificación de criterios

**Fecha:** 10 de octubre de 2026 · **Producto:** `main@e528165` · **Máquina:**
`cyberflow-sensor2` (10.10.60.12), Ubuntu 24.04.2, sin salida a Internet.

**Objetivo.** Demostrar, siguiendo **solo los manuales publicados**, que un tercero
instala CyberFlow desde cero en una máquina distinta del Sensor1, que el asistente,
el comprobador previo y `doctor.sh` hacen lo que dicen, y dejar una nota de
evidencia (`R`) que sustituya a la `K` del 29-sep con la versión vigente.

---

## Punto de partida (revisado hoy)

**Repositorio (`main`).** Scripts de instalación en `scripts/setup/`:

| Script | Qué hace | Dónde lo documenta |
|---|---|---|
| `configurar.sh` | Asistente: detecta interfaz de captura, MAC y red; escribe `configs/cyberflow.local.toml` | README · INSTALACION §6 |
| `instalar.sh --comprobar` | Diagnóstico **antes** de instalar; no toca nada | README · INSTALACION §6 |
| `instalar.sh` | Instala: requisitos, Suricata, entorno Python (ruedas offline), unidades systemd, comprobación final | README · INSTALACION §6 |
| `doctor.sh` | Salud del sistema **ya en marcha** (8 bloques) | README · INSTALACION §7 · GUIA |
| `cyberflow_usuarios.py` | Cuentas del panel (contraseña por teclado) | README · GUIA · CONFIGURACION |
| `desinstalar.sh [--simular\|--todo]` | Quita CyberFlow (`--todo`: también Suricata) | README |
| `preparar-bundle.sh` | Bundle offline (debs, ruedas, CPython 3.14.4) en una máquina CON red | INSTALACION, anexo A |
| `scripts/demo.sh` | Modo demo, sin red ni sensor | README |

**Corregido hoy en los manuales (`e528165`):** `doctor.sh` no aparecía en ninguno;
el README proponía `instalar.sh --comprobar` para revisar un sistema en marcha; la vía
corta de INSTALACION no nombraba el asistente. El resto de comandos y opciones
citados coinciden con los scripts (revisión automática de rutas y opciones).

**VM2 hoy.** Instalación de la nota `K` (29-sep, `main@99d5005`, sin `.git`) en
marcha: captura, motor, panel, Suricata y temporizadores activos. Tiene
`/opt/python3.14` (3.14.4). **No tiene sudo sin contraseña**: desinstalar e instalar
los ejecuta Mark.

**Avisos que hay que saber antes de empezar:**

1. **Perfil de modelo.** Una instalación limpia usa `configs/cyberflow.toml`, el perfil
   genérico histórico (OCSVM, umbral `1,8126`). `doctor.sh` lo marcará en
   «7. Calibración», y es correcto que lo haga: INSTALACION §8 exige recalibrar en cada
   red. Decisión en el bloque B3.
2. **Panel de `main`.** No tiene todavía las vistas nuevas («Construcción y
   entrenamiento», «Datos en vivo»), que solo están en la rama del sensor. Para esta
   prueba da igual: se prueba la instalación, no la GUI nueva.
3. **Sin Internet.** Las ruedas de Python se instalan desde `ruedas/`. Si se desinstala
   también Suricata (`--todo`), hace falta el bundle completo de `preparar-bundle.sh`.

---

## Bloques

Leyenda: **C** = lo prepara o verifica Claude (solo lecturas en la VM2) · **M** = lo
ejecuta Mark (necesita su contraseña de sudo o su presencia).

### B0 · Preparación (C) — 20 min
- Fijar la versión: `git archive main@e528165` → `cyberflow-e528165.tgz` + SHA-256.
- Copiarlo a la VM2 por el bastión y comprobar que el hash es idéntico en origen y destino.
- Inventario previo de la VM2 (unidades, `/opt/python3.14`, ruedas disponibles, espacio):
  la foto del «antes».
- Guardar `configs/cyberflow.local.toml` actual como referencia, **no** para reutilizarlo.

**Criterio:** hash idéntico; hay ruedas `cp314` para todo `requirements-model.txt` (si
faltan, B0-bis: `preparar-bundle.sh` en WSL/Docker con red).

### B1 · Desinstalar (M) — 10 min
```bash
cd ~/cyberflow
sudo bash scripts/setup/desinstalar.sh --simular   # qué haría
sudo bash scripts/setup/desinstalar.sh             # nivel 1: conserva Suricata
# nivel 2 (opcional, "desde cero total"): sudo bash scripts/setup/desinstalar.sh --todo
```
**Criterio:** termina en «Limpio»; no quedan unidades `ppi-*`/`cyberflow-*`
(`systemctl list-unit-files | grep -E 'ppi-|cyberflow'` vacío); no toca red, SPAN ni
usuario.

**Recomendación:** nivel 1 (igual que la `K`). El nivel 2 añade probar Suricata offline,
pero exige construir el bundle con debs; dejarlo para después si hay tiempo.

### B2 · Clon limpio y verificación de artefactos (M, guiado) — 5 min
```bash
mv ~/cyberflow ~/cyberflow.k-20260929        # se conserva, no se borra
mkdir ~/cyberflow && tar -xzf ~/cyberflow-e528165.tgz -C ~/cyberflow
cd ~/cyberflow && cp -r ~/cyberflow.k-20260929/ruedas ./ruedas
sha256sum -c docs/dataset/SHA256SUMS
```
**Criterio:** todos los hashes `OK`.

### B3 · Asistente de configuración (M) — 10 min
```bash
bash scripts/setup/configurar.sh
```
Anotar qué **detecta solo** y qué hubo que teclear: interfaz de captura (debe proponer
`ens37`, la que no tiene IP), su MAC, la red a vigilar, el modo (`observacion`), el
usuario y la raíz.

**Decisión del modelo (Mark, antes de B4):**
- **(a) Recomendada:** dejar el perfil genérico, como lo haría un tercero, y registrar
  el aviso de calibración. Demuestra instalación + honestidad del comprobador.
- (b) Copiar el IF recalibrado del Sensor1 y apuntar `[motor] detector` a él. Demuestra
  el modelo vigente, pero ya no es «solo con lo publicado».

**Criterio:** `configs/cyberflow.local.toml` escrito sin editar a mano; la interfaz y la
MAC detectadas son las correctas.

### B4 · Comprobación previa (M) — 5 min
```bash
sudo bash scripts/setup/instalar.sh --comprobar
```
**Criterio:** requisitos, configuración válida, interfaz existe, MAC esperada,
**recibe tráfico de verdad**, Suricata apunta a ella → resultado sin fallos. Guardar la
salida completa.

### B5 · Instalación (M) — 15 min
```bash
sudo bash scripts/setup/instalar.sh
python3 scripts/setup/cyberflow_usuarios.py ...   # admin y lector, contraseña por teclado
```
**Criterio:** pasos 1–9 del instalador en verde, sin Internet; «Instalado» al final;
ninguna contraseña en argv, fichero ni historial.

### B6 · Salud con doctor (C lee · M si pide sudo) — 10 min, y otra vez a los 30 min
```bash
bash scripts/setup/doctor.sh
```
**Criterio:** «Todo sano» u «Operativo, con N avisos», y cada aviso explicado (el de
calibración es esperado con la opción a). Repetir a los 30 min para ver que el anillo
rota, el acumulador escribe y no hay descartes de captura.

### B7 · Funcionamiento (C) — 15 min
- Decisiones en `logs/motor_decision.log` (una línea JSON por IP y ventana).
- `live-*.pcap` rotando cada 15 s; `kernel_drops = 0` en eve.json.
- Panel: login `admin` y `lector`; el `lector` recibe 403 en lo de desarrollador.
- Modo demo en la misma VM: `bash scripts/demo.sh` (reproducibilidad).

### B8 · Evidencia y cierre (C) — 30 min
- Nota `04-evidencias/cyberflow/R-instalacion-desde-cero-vm2-AAAA-MM-DD.md` con: versión
  y hash, salidas de B1, B4, B5 y B6, qué detectó el asistente, tiempos de cada bloque, y
  desviaciones entre lo que dice el manual y lo que pasó.
- Cada desviación → corrección en el manual (commit en `main`) o pendiente en
  `PENDIENTES.md`.
- Actualizar `ESTADO.md` (replicabilidad: validada con `e528165`).

---

## Criterios de aceptación (lo que se presenta como «replicable»)

| # | Criterio | Bloque | Se cumple si… |
|---|---|---|---|
| R1 | Instala en otra máquina, sin Internet | B5 | instalador completo con ruedas locales |
| R2 | Solo con lo publicado | B2–B5 | ningún paso fuera de README/INSTALACION |
| R3 | El asistente configura sin editar a mano | B3 | `.local.toml` correcto con lo detectado |
| R4 | El comprobador previo diagnostica antes de tocar | B4 | salida sin fallos y coherente con la máquina |
| R5 | `doctor.sh` refleja el estado real | B6 | sus OK/avisos coinciden con lo comprobado a mano |
| R6 | Se desinstala limpio y se reinstala | B1+B5 | «Limpio» y reinstalación sin restos |
| R7 | Artefactos íntegros | B2 | `sha256sum -c` todo OK |
| R8 | Sin credenciales expuestas | B5 | contraseñas solo por teclado |
| R9 | Funciona: capta, decide, muestra | B7 | decisiones en el log, anillo rotando, panel con roles |

**Fuera de alcance de esta prueba:** recalibrar en la VM2 (INSTALACION §8, necesita
días de línea base), el enforcement distribuido (publicador, relay, agente en el DMZ) y
las vistas nuevas del panel.

## Tiempo total

Unas **2 h 30 min**, de las que Mark está al teclado unos **45 min** (B1–B5). Conviene
hacerlo **antes** de la sesión con el profesor, para presentar R1–R9 con la nota `R`.
