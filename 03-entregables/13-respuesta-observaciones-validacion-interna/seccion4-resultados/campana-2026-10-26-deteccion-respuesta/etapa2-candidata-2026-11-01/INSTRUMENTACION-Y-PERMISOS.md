# Instrumentación de la cadena y permisos (Etapa 2, puntos 5 y 7)

## 1. Puntos de medida e identificadores

Cada punto deja un registro JSON con la hora del host que lo escribe. Las claves de unión entre registros están en la última columna.

| # | Punto | Dónde | Campo de tiempo | Identificador / unión |
|---|---|---|---|---|
| 1 | Inicio y fin del episodio | Kali, `marcas.jsonl` (ya existía) | `reloj.pared_utc` (+ monotónico) | `episodio_id` |
| 2 | Fin de ventana | motor, `motor_decision.log` | `window_end_utc` | `decision_id = entidad|ventana` |
| 3 | Disponibilidad de los datos | motor, decisión y `ciclos.jsonl` | `marca_pcap`, `marca_eve`, `pendiente_desde`, `inicio_ciclo` | `ciclo_n`, `disparo` (periodo / pcap_cerrado / plazo) **(nuevo)** |
| 4 | Decisión | motor | `decidido_en` | `decision_id` **(nuevo)**, `heuristicos` (todas las reglas, **nuevo**) |
| 5 | Escritura | motor | `logged_at` (antes del write); `registro_escrito_en` en `ciclos.jsonl` (después) | `ciclo_n` |
| 6 | Lectura por el publicador | publicador v2, `traza.jsonl` | `nuevos[].leido_en` | `evento_id = decision_id|regla`, `id` de entrada |
| 7 | Publicación | publicador v2 | `generado`, `publicado_en` (firma y feed ya renombrados) | `secuencia`, `entradas[]` (ids) |
| 8 | Traída y entrega por el relé | relé v2, `traza.jsonl` (bastión) | `traido_en`; `destinos.<d>.entregado_en` o `error` | `secuencia`, `sha256_feed` |
| 9 | Recepción del feed | agente v2, `traza.jsonl` (cada host) | `recibido_en`, `mtime_feed` | `secuencia`, `ids`, motivo de rechazo |
| 10 | Aplicación confirmada | agente v2 | `aplicado_en` (transacción nft aceptada); `confirmado_en` (los sets releídos contienen el elemento) | `id`, `evento_id`, `confirmadas` / `no_confirmadas` |
| 11 | Retirada | agente v2 | evento `retirada` (el elemento desapareció: caducidad o limpieza) | `ip`, `set` |
| 12 | Primer efecto | agente v2 | evento `primer_efecto`: primera observación con contador del elemento > 0 | `ip`, `set`, paquetes y bytes |

**Cadena completa de un episodio:**

```
episodio_id →(origen, intervalo) decision_id →(regla) evento_id → id → secuencia → recepcion/aplicacion/confirmacion → primer_efecto/retirada
```

**Precisión y límites declarados:**

- **Retirada y primer efecto** se observan cada `--observar-segundos` (5 s): son cotas superiores, con esa resolución. Para un BLOCK, el contador del elemento son paquetes **descartados**. Para un LIMIT son paquetes **vistos** del origen (pasen o no); los descartes del LIMIT solo existen como total de la regla, no por origen.
- **Relojes:** NTP en todos los hosts. En el 3B se midió |desfase| ≤ 0,0036 s en 4 hosts (`relojes-3b.log`). **El desfase de DC1 no se ha medido;** hay que añadirlo antes de la campaña B.
- **Instrumentar no es activar (D7):** el publicador y el agente en sombra (sin `--aplicar`) dejan los puntos 6–9 y no los 10–12.
- No se renueva ninguna restricción por reprocesar: el punto 6 solo registra `evento_id` nuevos. Los releídos no generan nada.

## 2. Permisos

| Host | Usuario | Antes (v1 desplegado) | Candidato v2 |
|---|---|---|---|
| Sensor1 | m4rk | Publicador con la clave privada ed25519 (0600) | Igual. Directorio propio `~/feed-v2`, que no pisa `~/feed` del v1. |
| Bastión | gadmin | Relé con llaves `cyberflow-to-sensor` y `cyberflow-to-srv` (scp) | Relé con las mismas llaves y una nueva `cyberflow-to-dc1`. En los destinos, la llave lleva `command="/usr/local/bin/cf-feed-ssh.sh …",restrict`: solo puede leer o escribir `feed.json` y `feed.sig` en un directorio fijo (`deploy/enforcement/candidato-etapa2/cf-feed-ssh.sh`, con prueba de rechazos). |
| srv-dmz | adminsrvdmz | `sudo -n nft -f -` (**cualquier regla**) y `nft -j list` | **Solo** `sudo -n /usr/local/sbin/cf-nft-helper` **sin argumentos** (sudoers `… NOPASSWD: /usr/local/sbin/cf-nft-helper ""`). La regla de `nft` del v1 se retira al instalar. |
| DC1 | (nuevo) `cfagente`, sin privilegios | — | El mismo helper con el perfil `dns`. **No se ha creado ni instalado nada en DC1.** |

**El helper** (`/usr/local/sbin/cf-nft-helper`, 0755 root:root, shebang `#!/usr/bin/python3 -I`, solo biblioteca estándar):

- lee una petición JSON de hasta 256 KiB por stdin;
- valida, antes de tocar nada:
  - el perfil (dmz o dns);
  - la operación (`asegurar`, `anadir`, `quitar`, `listar`, `retirar_origen`, `desinstalar`), con un conjunto exacto de campos por operación;
  - el set (`bloqueados` o `limitados`);
  - la IPv4 en forma canónica (rechaza loopback, multicast, 0.0.0.0, reservadas, link-local y broadcast, además de NUNCA_BLOQUEAR, DC2 incluido);
  - el timeout, entero entre 1 y 3720;
  - un máximo de 512 operaciones;
- si una sola operación es inválida, rechaza la petición entera;
- genera el texto nft de su tabla y lo aplica con `nft -f -` en **una** transacción.

Pruebas de rechazo: 16 casos parametrizados más el lote mixto y la orden con argumentos (`tests/test_etapa2_cadena.py`). Entre ellos están:

- la inyección `"10.10.20.30 }; flush ruleset"` en la IP;
- el set `"x; flush ruleset"`;
- una IP no canónica `10.10.20.030`;
- `127.0.0.1`;
- `10.10.10.21`;
- un timeout `True`, 0 o 99999;
- un campo extra `tabla`;
- `listar` junto a otra operación.

**Lo que el helper no puede hacer**, por construcción:

- tocar otra tabla, cadena o familia;
- vaciar el ruleset;
- abrir puertos;
- añadir reglas distintas de las dos fijas de su perfil;
- aceptar texto nft del llamador.
