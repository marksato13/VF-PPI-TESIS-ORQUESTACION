#!/usr/bin/env python3
"""Endpoint de prueba para fuerza bruta HTTP (servicio AISLADO de laboratorio).

Devuelve:
  - 401 si no hay credenciales o son inválidas (con cabecera WWW-Authenticate)  -> cuenta como fallo de auth
  - 200 solo con la credencial de control válida
Registra cada petición (fecha, cliente, método, ruta, usuario presentado, código) en un log.

Solo stdlib. No sustituye a nginx; es la opción más simple y sin ambigüedades de fase.
Uso:  USUARIO=control CLAVE=control123 PUERTO=18081 RUTA=/auth LOG=./brute.log python3 app.py
"""
import base64, os, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

USUARIO = os.environ.get("USUARIO", "control")
CLAVE = os.environ.get("CLAVE", "control123")
PUERTO = int(os.environ.get("PUERTO", "18081"))
RUTA = os.environ.get("RUTA", "/auth")
LOG = os.environ.get("LOG", "./brute.log")


def _log(cliente, metodo, ruta, usuario, codigo):
    linea = f'{datetime.now(timezone.utc).isoformat()} {cliente} {metodo} {ruta} user={usuario} -> {codigo}\n'
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linea)
    sys.stdout.write(linea); sys.stdout.flush()


class H(BaseHTTPRequestHandler):
    def _responder(self):
        usuario = "-"
        ok = False
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                u, _, p = base64.b64decode(auth[6:]).decode("utf-8", "replace").partition(":")
                usuario = u
                ok = (u == USUARIO and p == CLAVE)
            except Exception:
                ok = False
        if self.path != RUTA:
            codigo = 404
        elif ok:
            codigo = 200
        else:
            codigo = 401
        self.send_response(codigo)
        if codigo == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="lab"')
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok\n" if codigo == 200 else b"\n")
        _log(self.client_address[0], self.command, self.path, usuario, codigo)

    do_GET = do_POST = do_HEAD = _responder

    def log_message(self, *a):  # silenciar el log por defecto; usamos el nuestro
        pass


if __name__ == "__main__":
    print(f"endpoint de prueba en :{PUERTO}{RUTA} (401 sin/invalid, 200 con {USUARIO}); log {LOG}")
    ThreadingHTTPServer(("0.0.0.0", PUERTO), H).serve_forever()
