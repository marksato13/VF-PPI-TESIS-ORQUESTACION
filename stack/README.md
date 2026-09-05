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

## Lo que NO está aquí, y por qué

| Componente | Motivo |
|---|---|
| **Hermes Agent**, **Herdr** | No pude verificar que existan como producto instalable. No escribo un instalador para algo que no puedo comprobar |
| **OpenCode** | El registro de npm es inalcanzable desde esta VM (`registry.npmjs.org` no resuelve; `download.docker.com` sí) |
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
