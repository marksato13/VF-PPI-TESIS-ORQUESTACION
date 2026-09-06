# Stack

Infraestructura de la capa de orquestación. **Verificado en VM01 el 4 de
septiembre de 2026**: 4 vCPU, 11 GB de RAM, Ubuntu 26.04, Python 3.14.4.

---

## Lo que funciona ahora mismo, sin instalar nada

`ppi-trace` y `ppi-secrets` usan solo la biblioteca estándar de Python.
Ninguno necesita Docker, PostgreSQL ni permisos de administrador.

```bash
stack/bin/ppi-trace ingest        # reconstruye el índice desde los .md y .csv
stack/bin/ppi-trace cifra 88,8    # ¿de dónde sale este número?
stack/bin/ppi-trace req  REQ-013  # cadena completa de un requisito
stack/bin/ppi-trace check         # ¿sigue siendo cierto lo declarado?
stack/bin/ppi-secrets --todo      # ¿hay algo que no deba publicarse?
```

**La base de datos no es fuente de verdad.** Se reconstruye entera con
`ingest` desde archivos versionados. Si se borra, no se pierde nada — por eso
`stack/var/*.db` está en `.gitignore`.

### Por qué SQLite y no PostgreSQL

Porque `sudo` pide contraseña en esta VM, y un núcleo que depende de Docker no
se puede **probar** aquí. Funcionar importa más que ser vistoso. PostgreSQL con
pgvector queda disponible en `compose/` para cuando haga falta búsqueda
semántica sobre 180 documentos de campaña — hoy no hace falta.

---

## Lo que requiere instalación

```bash
stack/preflight.sh                # sin root, no modifica nada
sudo stack/install.sh             # todo
sudo stack/install.sh docs        # solo un bloque
stack/verify.sh                   # comprueba qué quedó funcionando

`verify.sh` **ejecuta** cada componente en vez de mirar si el paquete está
instalado. La diferencia no es teórica: con `pdflatex` presente decía que la
cadena documental estaba lista, y no lo estaba.

`docker sin sudo` seguirá en rojo hasta que **cierre la sesión y vuelva a
entrar**: la pertenencia a un grupo solo se aplica al iniciar sesión.
```

| Bloque | Qué instala | Para qué |
|---|---|---|
| `base` | git, jq, python3-venv, pipx, sqlite3 | requisito de los demás |
| `docs` | pandoc, LaTeX (+ luatex y xetex), graphviz | **el PDF del artículo de IJIES** |
| `docker` | docker.io 29.x, compose v2 | servicios opcionales |
| `backup` | restic, age | copias cifradas |

Todo viene de los repositorios de Ubuntu 26.04. **No se añade ningún
repositorio de terceros**: menos superficie y menos mantenimiento.

Los instaladores son idempotentes: repetirlos no reinstala ni rompe nada.

---

### La cadena documental necesita un motor Unicode

`ppi-doc` elige motor en este orden: **lualatex → xelatex → pdflatex**.

`pdflatex` no sirve para estos documentos. Falla con un error de LaTeX
ilegible en cuanto aparece `τ`, `ν`, `α`, `→` o `≥`, y aquí aparecen
constantemente. Por eso `texlive-luatex` y `texlive-xetex` son obligatorios en
el bloque `docs`, no opcionales.

Un glifo que la tipografía no tiene **no sale en el PDF: desaparece sin dejar
hueco**. Si es un símbolo de una tabla de cumplimiento, el documento cambia de
significado en silencio. Por eso `ppi-doc` los lista al terminar:

```
Caracteres que NO aparecen en el PDF (3 distintos):
  ⏳ (U+23F3)
  ✅ (U+2705)
  ❌ (U+274C)
```

Los emoji no están en ninguna tipografía de texto. Sustitúyalos en el `.md`
por palabras antes de entregar el documento.

---

## Servicios opcionales

```bash
cp stack/compose/.env.example stack/.env   # y rellenar
cd stack/compose
docker compose --profile indice up -d      # PostgreSQL + pgvector
docker compose --profile git    up -d      # Gitea
```

Van tras un *profile* a propósito: `docker compose up` sin argumentos **no
levanta nada**. Todo escucha solo en `127.0.0.1`.

---

## Hermes Agent

Instalado el 5 de septiembre de 2026 a petición expresa del usuario.

```
hermes --version
  Hermes Agent v0.19.0 (2026.7.20)
  Python: 3.13.15 · OpenAI SDK: 2.24.0
  /home/m4rk/.local/share/pipx/venvs/hermes-agent
```

Binarios: `hermes`, `hermes-acp`, `hermes-agent` en `~/.local/bin`.

### Por qué hizo falta un Python aparte

Hermes exige `>=3.11,<3.14` y Ubuntu 26.04 trae **3.14.4**, que queda excluido.
El repositorio de Ubuntu **no tiene** `python3.12` ni `python3.13`, así que
`pipx` habría rechazado el paquete por incompatible.

La vía fue `uv`, que descarga un Python autónomo a `~/.local` sin `sudo` y sin
tocar el sistema:

```bash
pipx install uv
uv python install 3.13
pipx install hermes-agent \
  --python "$HOME/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu/bin/python3.13"
```

Verificado tras instalar: el Python del sistema **no** ve el paquete; vive solo
en su venv de pipx. `uv` ya figuraba en el plan original, no es una pieza
añadida para esto.

### La versión de npm no sirve

`npm install hermes-agent` trae un **puente no oficial** de un tercero
(`wyrtensi/hermes-agent-npm`), no el producto. El oficial es el de PyPI, de
**Nous Research**. Y `herdr`, el otro componente que nombraba el plan, es en
npm un **nombre reservado en versión 0.0.0**: no hay software que instalar.

### Hermes consulta la trazabilidad por MCP

`stack/bin/ppi-trace-mcp` expone el índice a Hermes como servidor MCP. Siete
herramientas, todas de solo lectura salvo `ppi_reindexar`, que reconstruye la
base desde los archivos versionados:

```
ppi_cifra        de dónde sale un número
ppi_requisito    cadena completa de un requisito
ppi_afirmacion   una afirmación y su respaldo
ppi_estado       resumen del proyecto
ppi_pendientes   qué falta, con fecha y responsable
ppi_verificar    ¿sigue siendo cierto lo declarado?
ppi_reindexar    reconstruye el índice
```

Registrado con:

```bash
hermes mcp add ppi-trace --command /usr/bin/python3 \
  --args ~/…/stack/bin/ppi-trace-mcp
hermes mcp test ppi-trace     # ✓ Connected · 7 tools
```

Habla MCP `2024-11-05` por stdio **con biblioteca estándar**: no necesita el
paquete `mcp` ni ningún otro, así que corre con el Python del sistema, con el
de Hermes o con cualquier otro. Devuelve JSON estructurado, no el texto
coloreado de `ppi-trace` — un agente necesita datos, no una tabla bonita.

Regla que el código respeta y conviene no romper: **nada escribe en `stdout`
salvo JSON-RPC**. Un solo `print` fuera de protocolo rompe la sesión entera;
los diagnósticos van a `stderr`.

Lo que **no** se conectó, y por qué: `hermes mcp serve` expone diez
herramientas que resultaron ser todas de mensajería —WhatsApp, Slack,
Telegram—, incluida `messages_send`, que envía mensajes en nombre del usuario.
Ninguna toca requisitos, evidencias ni afirmaciones. Se comprobó antes de
cablear precisamente para esto.

### Límites de uso, y no son de estilo

**Hermes orquesta; no toca artefactos ni cifras.** Se describe a sí mismo como
*self-improving — creates skills from experience, improves them during use*.
Un componente que cambia entre ejecuciones por diseño **no es reproducible**, y
esta tesis defiende exactamente lo contrario: un modelo congelado con hash
verificable. Si participa en producir un resultado, ese resultado deja de ser
defendible ante el jurado.

Reparto que sí se sostiene: Hermes planifica y lleva estados · Codex implementa
· Claude audita. Ninguno decide lo que dice `metricas_offline.txt`.

**La clave de API nunca va a un archivo versionado.** Hermes trae `openai` como
dependencia dura y pedirá una. Va en `stack/.env` o en `hermes secrets`.
`ppi-secrets` la detectaría y bloquearía el commit, pero es mejor no llegar
ahí: si una clave llega a un commit publicado, borrarla no basta — hay que
rotarla.

**Usar `--safe-mode`, no `--yolo`.** Hermes trae subcomandos que van mucho más
allá de orquestar una tesis —`computer-use`, `whatsapp`, `cron`, `serve`,
`gateway`—. Ninguno hace falta aquí.

Sin configurar no hace nada: `hermes setup` es el asistente y `hermes model`
elige proveedor y modelo.

---

## Lo que NO está aquí, y por qué

| Componente | Motivo |
|---|---|
| **Herdr** | Verificado el 5 sep 2026: en npm es un **nombre reservado en versión 0.0.0**, sin software. No hay nada que instalar |
| **OpenCode** | Existe y está muy activo (`opencode-ai`, MIT). No instalado: nadie lo ha pedido todavía, y un servicio sin usuario es deuda |
| **Tailscale** | Necesita cuenta y clave de autenticación del usuario. VM01 ya tiene RustDesk |
| **JupyterLab** | El propio plan dice que ningún resultado nace en un notebook. Añadirlo sería contradecirlo |
| **Cloudflare Quick Tunnel** | La URL cambia y no tiene garantía. No es infraestructura |

---

## Copias

```bash
stack/bin/ppi-backup        # snapshot cifrado con restic
stack/bin/ppi-restore-test  # restaura y COMPARA HASHES
```

`ppi-restore-test` existe porque **un backup que nunca se restauró no es un
backup**. Restaura el último snapshot en un directorio temporal y compara
SHA-256 archivo por archivo contra el original.

El destino debe estar **fuera de esta VM**: un backup dentro de la VM muere
con la VM.

---

## Gate antes de publicar

```bash
stack/bin/ppi-secrets --hook   # se instala como pre-commit
```

Respeta `.gitignore`: escanea lo que git realmente publicaría. Sin eso, las
colecciones vendorizadas de Ansible producían 22 falsos ALTA — y un gate con
ruido es un gate que nadie lee.

Probado en ambos sentidos: detecta clave privada, token de GitHub, URL con
credenciales y la contraseña del laboratorio; y da cero sobre los 587 archivos
publicables del producto.
