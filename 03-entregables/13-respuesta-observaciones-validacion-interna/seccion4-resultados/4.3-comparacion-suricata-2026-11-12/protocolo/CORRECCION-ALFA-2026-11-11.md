# Corrección de la configuración principal de CyberFlow para el 4.3 (α = 0,01)

Registrada el 2026-11-11 (UTC; ver `FIJADO.txt`, anexo de esta corrección), **después** del `PROTOCOLO-REPLAY-4.3.md` y **durante** el replay de Suricata (14 de 22 rebanadas procesadas cuando se recibió el cambio). El protocolo original **no se edita**: su sha256 sigue siendo `829853b179e9bc7e132c5fd9b1789d772fea8a8e3385fbe1df150e69c291a42d`. Esta nota lo corrige en un solo punto y lo precisa en dos.

## 1. Qué se corrige y por qué
- El protocolo (§3) fijó como principal `HIB_0.03` (IF α = 0,03, umbral −0,5898535710336618) **porque lo tomé del manuscrito** (§3.3.5: «percentil 3»). El manuscrito consultado estaba desactualizado: no comprobé esa elección contra el registro de decisiones del repositorio.
- **Decisión previa que prevalece (Mark, 10-nov-2026):** **α = 0,01, umbral congelado −0,6223889502095352**, el mismo que se usó en la Campaña B. Referencias:
  - `campana-B-protocolo-2026-11-10/PREPARACION-B-RESULTADOS-2026-11-10.md`, §1 «Elección de α = 0,01 (DB-17)» y §16 «Dónde se aplica α = 0,01» (sha256 del fichero `f360032760814441e7a4035c125dafb0ede113d177ea92e5f9ca5d4e36b97a87`). Razones registradas allí: 4B, con α = 0,01 cumplen L1/L2 3 de 6 perfiles (con 0,03 y 0,05, 2 y 1); Campaña A, control: falsas alarmas del IF 2,43 % con α = 0,01; población principal: el IF con α = 0,01 señala a tiempo 16 de 21.
  - Registro en el Sensor1 `~/cf-b/alfa-b.json` (sha256 `c61c4e015e68eb36d313f148df78cf2b70a9f1d738b3749f58bdb63a052ac9e6`): `alfa_experimento 0.01`, `umbral_alfa_experimento −0.6223889502095352`, manifiesto `b3ad680595128189574527208e53058f613822f56f542f914faef6495aa2a9e7`, modelo `df547da098e51171aa267c8466edc6624bc1bd5c6b602639cc00bd4711a2fd60` (el mismo `if_limpio_2026_10` de la Campaña A).
  - Procedencia del umbral verificada el 10-nov (`s50` v2, 16 de 16 comprobaciones): cuantil 0,01 de las 65 553 puntuaciones de validación sin Kali.
- **Matiz que debe acompañar la cifra:** el motor desplegado conserva su umbral de α = 0,05 (−0,5693969936322356) y con la política `if_senal` el IF no escribe restricciones; α = 0,01 define la **señal analizada**. En la Campaña A (modo sombra) `HIB_0.01` es, igual que `HIB_0.03`, una configuración **derivada** de los registros del motor (`score_samples` registrado frente al umbral), no una decisión del motor en vivo.

## 2. Configuración vigente de CyberFlow para el 4.3
| Papel | Configuración |
|---|---|
| **Principal** | **`HIB_0.01`** = IF α = 0,01 (`score < −0,6223889502095352`) **o** heurístico (`VERSION_UMBRALES 2026-11-02.1`) |
| Componentes | `IF_0.01` (solo IF) y `HEUR` (solo heurísticos) |
| **Sensibilidad separada** | `HIB_0.03` (y su componente `IF_0.03`), tal como estaba fijado en el protocolo original |
Los demás elementos del protocolo **no cambian**: población (21 elegibles, 4 escaneos breves excluidos), regla de alerta válida, Suricata (principal `HOME_NET [10.10.10.0/24,10.10.30.0/24]` y S1 con el YAML original), PCAP y hashes, unidades de control (entidad-ventana y ventana de 10 s), regla de latencia (marca de tiempo de los datos). Se actualizan únicamente: §3 (principal = `HIB_0.01`), la referencia del control de §6 (`HIB_0.01`: 54/2 218 = 2,43 %; `IF_0.01` 54; `HEUR` 0; reproducido desde `motor_decision.log` antes del cambio, junto con 200 para `IF_0.03`) y la configuración de CyberFlow citada en §7 (latencia con `HIB_0.01`). El código `analizar_replay.py` se parametriza con esa configuración; no se toca ninguna regla de atribución.

## 3. ¿Había consultado resultados comparativos al recibir el cambio?
Declaración completa (sin cifras nuevas de este análisis):
- **Comparación CyberFlow vs Suricata:** **no** había calculado ni visto ninguna tabla por episodio, cobertura, coincidencia, latencia ni control comparativos. `analizar_replay.py` **no se había ejecutado**. Estado del replay: 14 de 22 rebanadas procesadas, sin abrir sus salidas.
- **Salida de Suricata vista:** durante la validación del procedimiento abrí la lista de alertas (firma, origen, destino, conteos) de **una** rebanada, `escaneo_breve-r4`, para las dos configuraciones de HOME_NET: solo vi alertas STREAM, `ET SCAN Potential SSH Scan OUTBOUND` entre equipos de gestión (10.10.10.30→10.10.60.11, solo con el HOME_NET ampliado) y `GPL ICMP PING *NIX` de un cliente. No las comparé con CyberFlow ni las atribuí a ningún episodio.
- **Salida de CyberFlow vista (sin Suricata):** al hacer el inventario ya había leído los resultados de `s50` v2 por configuración (siete configuraciones, incluidas `HIB_0.01`, `IF_0.01` y `HIB_0.03`: oportunas por familia, control con 14,56/9,02/2,43/0 % de falsas alarmas). Esas cifras son anteriores y ajenas a Suricata. Con ellas, `HIB_0.01` y `HIB_0.03` tienen la misma cobertura oportuna en la población principal; lo único que cambia es la tasa de falsas alarmas del control.
- La elección α = 0,01 viene de una decisión del 10-nov previa a todo esto; ni la elección original de 0,03 (mía, por el manuscrito) ni este cambio se hicieron a la vista de resultados de Suricata.

## 4. Qué hay que actualizar en el manuscrito (α seleccionado)
Referencias a α = 0,03 (percentil 3) que ya no describen el punto operativo; los números de párrafo son los del texto extraído `articulo.txt`:
1. **§3.3.5 Calibración del umbral** (párrafos 276–282): «Se adopta α … para conservar la detección observada con … y reducir los falsos positivos» → α = 0,01 con su justificación real (criterios operativos: control 2,43 %, 4B por perfil) ya que offline 0,01 detecta menos; «percentil 3» → **percentil 1**; `−0,0898535710336618` (escala de la función de decisión) → **−0,1223889502095352** (= −0,6223889502095352 + 0,5; comprobar contra el fichero de calibración antes de publicar); `−0,5898535710336618` → **−0,6223889502095352**; «no garantiza un 3 % de falsos positivos» → **1 %**. Las ecuaciones (3)–(5) conservan su forma; cambian los valores.
2. **§3.3.4 Evaluación** (párrafo 269) y **§4.1** (399): «Sus resultados también se utilizan para comparar los valores de α y seleccionar el punto operativo» → la selección también usó la Campaña A y la 4B, no solo el conjunto de evaluación.
3. **§4.1 selección de α** (367–370): el texto actual justifica 0,03 («conservar la detección … 1 723 frente a 2 955 … se seleccionó 0,03 como compromiso»). Con 0,01 (Tabla 7: 50 TP, 567 FP, recall 59,52 %, precisión 8,10 %, FPR 0,87 %) la frase «los valores inferiores a 0,03 … disminuyeron la detección» pasa a ser el coste asumido; hay que explicar por qué se elige 0,01.
4. **Párrafo 398** («no equivalen a la precisión obtenida con α = 0,03») → α = 0,01 (precisión 8,10 %).
5. **Resumen** (párrafo 8): conserva los tres niveles evaluados, pero debe indicar cuál es el punto operativo adoptado y por qué; hoy la frase termina en «Al reducirlo a 0,01, disminuyeron … las ventanas de ataque detectadas» sin decir que es el valor elegido.
6. **Tabla 9 y Figura 5** (párrafos 732, 897–899): la comparación de métodos «bajo α = 0,03» (y 0,05) no coincide con el punto operativo; o se recalcula a 0,01 o se presenta como sensibilidad.
7. **Tabla 5**, filas «Sensibilidad de α» y «Comparación con Suricata»: declarar α = 0,01 y la población realmente evaluada.
8. **Campaña B / respuesta** (sección de respuestas): precisar que el motor desplegado usa α = 0,05 y que la señal analizada en B es α = 0,01 (`if_senal`).
9. **Sección 4.3** (nueva): usar `HIB_0.01` como principal, con `IF_0.01` y `HEUR` como componentes y `HIB_0.03` en la sensibilidad.
