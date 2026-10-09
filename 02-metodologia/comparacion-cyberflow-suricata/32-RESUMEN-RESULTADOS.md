# 32 · Resumen de resultados (para la defensa)

Síntesis honesta de la comparación CyberFlow vs Suricata y de la evaluación interna
de CyberFlow. Detalle y reproducibilidad en las notas 24–31.

## 1. Cobertura — el resultado principal

Mismos ataques, misma línea base, método de replay del mismo PCAP (sin desfase de
relojes):

| Familia (sin firma) | CyberFlow | Suricata (ET Open) |
|---|---|---|
| DNS alta entropía (DGA) | **3/3** | 0/3 |
| Flood HTTP | **3/3** | 0/3 |
| Escaneo de puertos | **3/3** | 0/3 |
| **Total** | **9/9** | **0/9** |

**Lectura:** CyberFlow detecta lo que **no tiene firma**; Suricata, por diseño, no.
Es la contribución, cuantificada.

## 2. Episodio de control (ataque CON firma) — honestidad

| Nikto (escaneo web, con firma) | CyberFlow | Suricata |
|---|---|---|
| ¿Detecta? | sí (conducta, 12,0 s) | sí (firma, **3,4 s**) |

**Suricata gana cuando la firma existe.** Se reporta así: son **complementarios**,
no competidores. (Nota 28.)

## 3. Ablación interna (aporte de cada componente de CyberFlow)

| Configuración | Cobertura |
|---|---|
| Modelo solo | 6/9 |
| Heurísticos solos | 7/9 |
| **Combinado (modelo + heurísticos)** | **9/9** |

Ninguno basta solo (el modelo no ve DNS; los heurísticos perdían escaneos); el
**diseño híbrido** llega a 9/9. (Nota 31, con `30-metricas.py`.)

## 4. Operación

- **FPR:** recalibración en la red real **92,4 % → 4,45 %** (respuesta al
  distribution shift sim→real). Heurísticos ~0,01 % sobre 712 450 ventanas.
- **Tiempos (honestos):** detección ~2–40 s; respuesta total hasta BLOCK ~1–2,5 min
  (dominada por la cadencia del feed firmado, configurable). Corte real
  200→000 confirmado.
- **Respuesta automática:** PERMIT / LIMIT / BLOCK con feed firmado (ed25519) y
  caducidad escalada; nunca ∞ automático.

## 5. Mejora aplicada en esta evaluación

- `port_scan` pasaba 1/3 (el espejo dejaba el ratio de unicidad bordeando 0,45). Se
  añadió una rama OR para ráfaga masiva de baja completitud (`flow≥200 & syn≤0,1`),
  FPR neutro (validado sobre 712 450 ventanas). Desplegado (`VERSION_UMBRALES
  2026-10-06.2`) y validado en vivo. **Confirmación N=3: 3/3** (antes 1/3).
  (Ver [`producto/docs/MEJORA-PORT-SCAN.md`](https://github.com/marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos/blob/8d696e5d61d3f90b4c3c2106ea503db83ca26950/docs/MEJORA-PORT-SCAN.md).)

## 6. Límites declarados (no esconder)

- N=3 por familia (piloto ampliado); para la tesis conviene N mayor.
- Suricata 0/9 con ET Open **por defecto** + `-sT` + HOME_NET=DMZ: alcance, no
  absoluto (un ruleset afinado podría variar).
- 4ª familia **fuerza bruta real (401)**: ✅ confirmada tras abrir 8081 en pfSense
  (regla aplicada por Mark). CyberFlow detecta `brute_force`→BLOCK ("240 req
  HTTP/60s con 100% de fallo de auth"), chequeo rápido en vivo (N=1). Pendiente: la
  medición de 3 tiempos (la mató la presión de memoria de la laptop) y la
  comparación vs Suricata por replay.
- Variables de **capa 2** no entran al scoring del modelo v2 (sí en la dedup y en
  v3, no desplegado): ARP spoofing es trabajo futuro (reentrenar v3).
