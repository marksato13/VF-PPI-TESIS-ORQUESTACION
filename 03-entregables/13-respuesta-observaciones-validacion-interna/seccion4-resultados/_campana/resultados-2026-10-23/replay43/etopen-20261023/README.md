# Replay ET Open — 23 de octubre de 2026

Replay offline del PCAP de 9 470 paquetes ya utilizado por CyberFlow. Ejecutado en la comparadora 10.10.60.13 con Suricata 7.0.3, sin sudo ni arranque del servicio.

Comando: `suricata -r /tmp/cf-qc-20261023-pass.pcap -c /etc/suricata/suricata.yaml -S /var/lib/suricata/rules/suricata.rules -l /tmp/cf-qc-20261023-etopen -k none --runmode single`.

La salida advirtió que no pudo crear el socket de administración; el motor arrancó y procesó los 9 470 paquetes. El log confirma **53 013 reglas cargadas y cero fallidas**.

## Resultado verificado

- **55 alertas**, no cero: 28 `SURICATA STREAM Packet with invalid timestamp` (SID 2210044), 26 `SURICATA STREAM CLOSEWAIT FIN out of window` (SID 2210016) y una `ET INFO POSSIBLE Web Crawl using Curl` (SID 2002825).
- Las 54 alertas STREAM van del servidor al atacante y se reportan separadas de las firmas ET.
- La alerta ET INFO va del atacante al servidor HTTP, a las `17:19:04.951150 UTC`, con `curl/8.17.0`, URL `/` y respuesta HTTP 200. Su metadata la clasifica como **Informational**. Reconoce la herramienta; no confirma por sí sola una inundación HTTP.
- **No es defendible afirmar que Suricata produjo cero alertas**, ni convertir la alerta informativa en detección confirmada de flood sin un criterio de atribución declarado.
- CyberFlow ya tiene evidencia de DNS/flood en el mismo PCAP; el replay ET Open de este directorio cierra la falta de ejecución del comparador para ese archivo, pero no la Tabla 9 final de toda la campaña.

## Procedencia

| Fuente | SHA-256 |
|---|---|
| PCAP | `9db1b269dcf19a4281130081ffb79582e9d29ea85cb01b4d87618d5f5a809070` |
| ET Open | `7b674459975dd56af2d03363b27df4ad6ff53e724e3c04ff65913701ddd5f4e9` |
| YAML | `d0ea918591040108586e43fb30e51c3583f6d61f6ed1acd8dff938150b303650` |

HOME_NET: `10.10.30.0/24`; EXTERNAL_NET: `!$HOME_NET`. El DNS externo a HOME_NET tiene un alcance de reglas distinto: la configuración debe acompañar cualquier comparación. No se cambió el YAML ni el ruleset.

`resumir_replay.py` reproduce los conteos y genera `resumen.json`. Se conservan EVE y log de ejecución como evidencia primaria.

El PCAP no contiene una captura completa del control Nikto; el escaneo tiene tráfico mínimo. Este replay no cierra esas dos limitaciones ni las mediciones extremo a extremo.
