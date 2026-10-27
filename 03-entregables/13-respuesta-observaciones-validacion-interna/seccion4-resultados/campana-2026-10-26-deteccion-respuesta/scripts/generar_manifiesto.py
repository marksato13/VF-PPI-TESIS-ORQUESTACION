#!/usr/bin/env python3
"""Genera MANIFIESTO-CAMPANA.json con el sha256 de los BYTES PUBLICADOS por git (no los del árbol de trabajo).

En Windows los ficheros de texto se guardan con CRLF en disco, pero git los versiona con LF: hashear el fichero
local daría un sha256 que no coincide con lo que GitHub publica. Este generador hashea `git show :<ruta>` (el
contenido EN STAGE = los bytes que se publicarán), así el manifiesto coincide con el commit.

Uso (desde cualquier sitio):  python3 generar_manifiesto.py --repo <raiz-git> --carpeta <ruta-relativa-de-la-campana>
Primero haz `git add -A` de la carpeta para que el stage refleje lo que vas a publicar.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from datetime import datetime, timezone

MANIFIESTO = "MANIFIESTO-CAMPANA.json"


def git(repo, *args) -> bytes:
    return subprocess.run(["git", "-C", repo, *args], check=True, stdout=subprocess.PIPE).stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--carpeta", required=True, help="ruta de la campaña relativa a la raíz del repo (con /)")
    a = ap.parse_args()
    carpeta = a.carpeta.rstrip("/")
    rutas = git(a.repo, "ls-files", "--", carpeta).decode("utf-8").splitlines()
    archivos = {}
    for ruta in sorted(rutas):
        rel = ruta[len(carpeta) + 1:]
        if rel == MANIFIESTO:
            continue
        datos = git(a.repo, "show", f":{ruta}")          # bytes EN STAGE = los que se publican (LF)
        archivos[rel] = hashlib.sha256(datos).hexdigest()
    obj = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "repo": "orquestacion-limpio / VF-PPI-TESIS-ORQUESTACION",
        "fase": "preparacion (sin ejecutar ataques)",
        "normalizacion": "sha256 sobre los BYTES VERSIONADOS POR GIT (git show :<ruta>), que se publican con saltos "
                         "LF; NO sobre el fichero local (que en Windows puede tener CRLF). Reproducible con "
                         "scripts/generar_manifiesto.py. Verificado contra git show HEAD:<ruta> tras el commit.",
        "archivos_sha256": dict(sorted(archivos.items())),
    }
    salida = f"{a.repo}/{carpeta}/{MANIFIESTO}"
    with open(salida, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(archivos)} archivos en {MANIFIESTO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
