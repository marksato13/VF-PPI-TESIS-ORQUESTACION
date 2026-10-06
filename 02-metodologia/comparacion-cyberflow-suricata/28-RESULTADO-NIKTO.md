# 28 · Resultado — episodio de control Nikto (comparación de TIEMPO)

**Fecha:** 2026-10-06 · Método: replay offline del MISMO PCAP a ambos detectores,
tiempo anclado al reloj del paquete (sensor). Es el **único episodio donde ambos
detectan**, por lo que es el que permite comparar *tiempo de detección* (lo que pidió
el asesor). Ataque: `nikto -h http://10.10.30.10 -maxtime 75s` desde la Kali
(10.10.20.30). PCAP = 9 trozos del anillo de captura fusionados (3,5 MB).

## Resultado

| Detector | ¿Detecta? | **t_detección** | Qué disparó |
|---|---|---:|---|
| **Suricata (ET Open, 53 k reglas)** | ✅ | **3,4 s** | **590 alertas** sobre el atacante, 34 firmas distintas |
| **CyberFlow (modelo v2 recalibrado)** | ✅ | **12,0 s** | score −0,664 < umbral −0,569 (8/227 ventanas marcadas) |
| **Quién detecta primero** | — | **Suricata, por ~8,6 s** | — |

Primera firma de Suricata: *ET WEB_SERVER Tilde in URI - potential .php~ source
disclosure*. Otras disparadas: `/etc/passwd`/`/etc/shadow` en URI, XSS en URI,
CodeRed, Shellshock (CVE-2014-6271), Spring Cloud traversal (CVE-2020-5410),
accesos `.htaccess`/`.htpasswd`, `cmd.exe`/`/system32/` en URI, etc.

## Lectura (la que hay que dar en la defensa)

- **Con firma conocida, Suricata es más rápido y más específico** (nombra la
  vulnerabilidad). Es su terreno: Nikto golpea rutas y patrones que ET Open conoce.
- **CyberFlow también lo detecta** (12 s), pero por **conducta** (el modelo ve la
  anomalía de volumen/errores), no porque "conozca" Nikto. Es más lento porque
  necesita acumular una ventana.
- **Conclusión: son complementarios.** Suricata gana donde hay firma; CyberFlow
  gana donde NO la hay (DGA, flood, escaneo → Suricata 0/9, nota 26). La aportación
  de CyberFlow **no es velocidad, es cobertura de lo desconocido**.

> **Por eso este episodio es honesto y fuerte:** demuestra que no se está "haciendo
> trampa" a favor de CyberFlow. Donde Suricata debe ganar (firma), gana; y aun así
> CyberFlow no se queda ciego. Un jurado confía en una comparación que reconoce las
> fortalezas del rival.

## Detalle metodológico

- Reloj único: ambos tiempos se miden como `t_detección = t_evento − t_lanzamiento`
  sobre el **mismo PCAP** (mismos timestamps de paquete), así que **no hay desfase de
  relojes** entre detectores (el problema que el método de replay resuelve, nota 19).
- Suricata: primera línea `event_type=alert` que involucra al atacante en `eve.json`.
- CyberFlow: primera ventana con `score < umbral` (`20-puntuar-por-ventana.py` sobre
  el modelo congelado `if_recalibrado_2026_09`). El extractor usó el `eve.json` del
  comparador para las features HTTP.
- **Nota:** aquí solo se midió el **modelo** de CyberFlow; el heurístico `http_abuse`
  (≥100 req/60s) también habría disparado (Nikto genera cientos de peticiones). El
  tiempo del modelo (12 s) ya basta para la comparación.

## Limitaciones

- N=1 (un episodio de control). Repetir N≥3 para rango/mediana, como la batería.
- Suricata corre en el comparador (10.10.60.13, ET Open); CyberFlow en sensor1
  (modelo desplegado). Mismo PCAP a ambos.
- Latencia de CyberFlow cuantizada a la rejilla de ventanas de 10 s.
