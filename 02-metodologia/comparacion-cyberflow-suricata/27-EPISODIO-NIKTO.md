# 27 · Episodio de control: Nikto (ataque CON firma) — comparación de tiempo

## Por qué este episodio

Las familias de la batería (nota `26`) son **anomalías sin firma** (DGA, flood,
escaneo): CyberFlow detecta 3/3 y Suricata 0/9. Eso demuestra **cobertura**, pero
**no permite comparar tiempo de detección**: no se puede medir "quién detecta
primero" cuando uno de los dos **no detecta**.

El profesor pidió explícitamente la métrica de **tiempo / "quién detecta primero"**.
Para que esa métrica tenga sentido hace falta **al menos un ataque que AMBOS
detecten**. Nikto es el candidato ideal: es un escaneo de vulnerabilidades web que
dispara **firmas conocidas** en Suricata (reglas `ET WEB_SERVER` / `ET SCAN`) y a la
vez genera un patrón conductual (muchas peticiones, muchos 404) que CyberFlow ve por
`http_abuse` / tasa de error HTTP.

> **Resultado esperado y honesto:** en este episodio **Suricata será más rápido** (una
> firma casa casi al instante; CyberFlow necesita acumular una ventana de 10–60 s).
> **Eso es lo correcto y refuerza la tesis**: Suricata gana cuando la firma existe;
> CyberFlow gana en lo que no tiene firma. Son **complementarios**. No se trata de
> "ganarle en tiempo", sino de cuantificar el trade-off con un número.

## Ataque (desde la Kali, 10.10.20.30 → DMZ 10.10.30.10:80)

```
nikto -h http://10.10.30.10 -maxtime 120s
```
(Es el escenario `web` del catálogo del panel, `configs/escenarios.json`.)

## ⚠️ Dónde corre cada detector (NO es como las otras familias)

Verificado 2026-10-06: **sensor1 (10.10.60.11) solo tiene 372 reglas base** de
Suricata; **las 53.012 de ET Open están en el comparador (10.10.60.13)**. Por tanto,
para que el lado Suricata sea válido:

| Detector | Host | Qué corre |
|---|---|---|
| **Suricata (ET Open)** | **comparador 10.10.60.13** | `suricata -r nikto.pcap` → `eve.json` |
| **CyberFlow (v2 desplegado)** | **sensor1 10.10.60.11** | extractor v2 + `20-puntuar-por-ventana.py` |

Los dos leen **el MISMO PCAP** → el tiempo se ancla al **reloj del paquete**, sin NTP
(igual que la nota `19`). Correr el lado Suricata en sensor1 daría un **0 falso** (no
tiene ET Open) y arruinaría el episodio.

## Captura del PCAP

El tráfico Kali→DMZ:80 se observa en **sensor1, interfaz `ens37`** (el espejo SPAN).
Captura dedicada que bracketea el ataque (necesita sudo en el sensor):

```
# en sensor1, ANTES de lanzar nikto:
sudo tcpdump -i ens37 -w /tmp/nikto.pcap 'host 10.10.20.30 and host 10.10.30.10' &
# ... lanzar nikto desde la Kali (≈120 s) ...
# al terminar: sudo pkill -f 'tcpdump.*nikto.pcap'
```
(Alternativa sin sudo: fusionar los `live-*.pcap` del anillo
`/var/lib/ppi-motor-capture/` que caigan en la ventana del ataque, con `mergecap`.)

## Medición (reusa el orquestador 22, en modo split)

El orquestador `22-correr-piloto.py` asume un solo host con ambos detectores; aquí el
lado Suricata va en el comparador. Dos formas:

**A) Split manual (recomendado, refleja la realidad):**
```
# 1) Suricata en el COMPARADOR (ET Open), sobre el mismo pcap:
scp /tmp/nikto.pcap adminsuricata@10.10.60.13:/tmp/nikto.pcap
ssh adminsuricata@10.10.60.13 'sudo suricata -r /tmp/nikto.pcap -l /tmp/nikto-suri'
#   -> primera alerta = menor "timestamp" con event_type=alert en /tmp/nikto-suri/eve.json

# 2) CyberFlow en SENSOR1 (extractor v2 + scorer), sobre el mismo pcap:
#    (el extractor necesita un eve.json; usar el del comparador o uno vacío para L3/L4)
python3 extract_multilayer_v2.py --pcap /tmp/nikto.pcap --eve <eve> \
   --schema multilayer-v2.json --entity-network 10.10.0.0/16 \
   --capture-start <t_inicio> --output features.csv
python3 20-puntuar-por-ventana.py --modelo if_recalibrado_desplegable.joblib \
   --manifest manifest-if-recalibrado.json --detector-name if_recalibrado_2026_09 \
   --csv features.csv --t-inicio <t_inicio>
#   -> primera ventana marcada = tiempo de detección de CyberFlow
```

**B) Un host con ambos:** copiar el extractor+modelo+manifest al comparador (que ya
tiene ET Open) y correr `22-correr-piloto.py` allí con `--familia web_vuln_scan`.
Requiere Python+sklearn en el comparador.

En ambos casos el `t_inicio` es el epoch del lanzamiento de nikto (reloj del sensor),
y `tiempo_deteccion_s = ts_primera_detección − t_inicio` para cada detector.

## Qué registrar (tabla del episodio)

| Métrica | Suricata (ET Open) | CyberFlow (v2) |
|---|---|---|
| ¿Detecta? | sí (esperado) | sí (esperado, `http_abuse`/modelo) |
| t_detección (s) | *(medir)* | *(medir)* |
| Qué disparó | firma(s) `ET WEB_SERVER…` | heurístico/modelo |
| **quién primero** | **probablemente Suricata** | — |

## Lectura para la tesis

- Es el **episodio de control** que da la comparación de **tiempo** que faltaba.
- El mensaje correcto: *"Con firma conocida, Suricata detecta antes y es el
  especialista; CyberFlow detecta lo que no tiene firma. La aportación de CyberFlow no
  es velocidad, es cobertura de lo desconocido."*
- **No** usar este episodio para afirmar que CyberFlow es "más rápido" — es lo
  contrario, y decirlo honestamente da credibilidad al resto.

## Limitaciones

- Nikto es ruidoso (cientos de peticiones): buen control "con firma", pero también
  estresa las features HTTP de CyberFlow; interpretar su detección como conductual de
  volumen, no como que "también casó la firma".
- Repetir N≥3 para dar rango/mediana, como el resto de la batería.
- Suricata depende de que ET Open traiga la firma del patrón de Nikto; verificar en
  `eve.json` qué firma(s) dispararon (trazabilidad).
