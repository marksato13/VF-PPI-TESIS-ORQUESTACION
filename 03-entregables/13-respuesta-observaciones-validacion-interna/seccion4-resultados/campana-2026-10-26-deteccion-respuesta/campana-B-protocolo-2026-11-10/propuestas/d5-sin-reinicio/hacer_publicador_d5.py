#!/usr/bin/env python3
"""PROPUESTA DE BANCO (no instalada, no desplegada): deriva publicar_feed_v2_d5.py del publicar_feed_v2.py desplegado
(sha256 5733f17d…) con un canal de control para la limpieza D5 SIN reiniciar el proceso. v3 (tras el banco de adaptador).

Problema que resuelve: d5_episodio.py limpia el estado del publicador matándolo (SIGKILL); systemd lo reinicia y el clasificador de
calidad de captura cuenta cada reinicio como C3. Con esta propuesta D5 escribe un fichero de control; el publicador, en su bucle,
quita de su estado en memoria las claves del origen del experimento (`vigentes` «ip|…» y `escalada` «ip@…»), conserva `eventos`,
persiste, republica y SOLO ENTONCES escribe el acuse (con la secuencia del feed ya publicado sin ese origen).

Reglas: solo actúa con --control-d5 y --d5-origen (sin ellos, comportamiento idéntico al original); acepta ÚNICAMENTE
{"accion": "reset_origen", "origen": <== --d5-origen>, "id": <str>}; cualquier otra cosa se rechaza con acuse de error y sin tocar el
estado. Un `id` ya procesado es un NO-OP idempotente (acuse `duplicada: true`). Un fallo al escribir el acuse o la auditoría NUNCA
tumba el bucle. v3: con --d5-auditoria RUTA el publicador agrega a un JSONL propio, independiente del acuse, una línea `consumido`
(id, ok, quitado) al consumir el control, una `publicado` (id, secuencia) tras republicar y una `ack_fallido` si el acuse no se pudo
escribir: es la evidencia que permite distinguir, sin adivinar, si una solicitud sin acuse se consumió y qué secuencia se publicó.
Cada sustitución se aplica exactamente una vez. Uso: hacer_publicador_d5.py <publicar_feed_v2.py> <salida>."""
import sys

FUNC = '''_D5_IDS: set = set()


def _auditar_d5(ruta_log, reg: dict) -> None:
    """Auditoría D5 (JSONL, solo agrega), independiente del acuse. Sin ruta no hace nada; un fallo nunca interrumpe al publicador."""
    if ruta_log is None:
        return
    try:
        with open(ruta_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(reg, sort_keys=True) + "\\n")
    except OSError as ex:
        print("d5: no se pudo escribir la auditoría (%s)" % ex.__class__.__name__, file=sys.stderr, flush=True)


def _escribir_ack_d5(ruta: Path, resp: dict) -> bool:
    """Acuse atómico (tmp + rename). Un fallo no interrumpe el publicador: devuelve False y lo cuenta en stderr."""
    ack = ruta.with_name(ruta.name + ".ack")
    try:
        tmp = ack.with_name(ack.name + ".tmp")
        tmp.write_text(json.dumps(resp, sort_keys=True), encoding="utf-8")
        os.replace(tmp, ack)
        return True
    except OSError as ex:
        print("d5: no se pudo escribir el acuse (%s)" % ex.__class__.__name__, file=sys.stderr, flush=True)
        return False


def _aplicar_control_d5(ruta: Path, estado: dict, origen_permitido: str, ahora: float) -> dict:
    """D5 sin reinicio (propuesta de banco): consume el control y devuelve la respuesta (ok o error); el acuse de un
    control válido lo escribe el bucle DESPUÉS de republicar y persistir."""
    resp = {"t": ahora, "id": None, "ok": False}
    try:
        ctl = json.loads(ruta.read_text(encoding="utf-8"))
        resp["id"] = ctl.get("id") if isinstance(ctl, dict) else None
        if not isinstance(ctl, dict) or ctl.get("accion") != "reset_origen" or not isinstance(resp["id"], str):
            resp["error"] = "control mal formado"
        elif not origen_permitido or ctl.get("origen") != origen_permitido:
            resp["error"] = "origen no permitido"
        elif resp["id"] in _D5_IDS:
            resp.update(ok=True, duplicada=True, quitado={"vigentes": [], "escalada": []})
        else:
            o = ctl["origen"]
            quitado = {"vigentes": [k for k in estado.get("vigentes", {}) if k.split("|", 1)[0] == o],
                       "escalada": [k for k in estado.get("escalada", {}) if k.split("@", 1)[0] == o]}
            for k in quitado["vigentes"]:
                del estado["vigentes"][k]
            for k in quitado["escalada"]:
                del estado["escalada"][k]
            _D5_IDS.add(resp["id"])
            resp.update(ok=True, duplicada=False, quitado=quitado)
    except (OSError, ValueError) as ex:
        resp["error"] = "control ilegible: %s" % ex.__class__.__name__
    try:
        ruta.unlink()
    except OSError:
        pass
    return resp


'''

SUST = [
    ("def main(argv=None, reloj=time.time, dormir=time.sleep) -> int:", FUNC + "def main(argv=None, reloj=time.time, dormir=time.sleep) -> int:"),
    ('    p.add_argument("--max-iteraciones", type=int, default=0, help="pruebas: corta tras N sondeos")\n',
     '    p.add_argument("--max-iteraciones", type=int, default=0, help="pruebas: corta tras N sondeos")\n'
     '    p.add_argument("--control-d5", type=Path, default=None, help="B: fichero de control para limpiar el estado de un origen sin reiniciar")\n'
     '    p.add_argument("--d5-origen", default="", help="B: único origen que el control puede limpiar")\n'
     '    p.add_argument("--d5-auditoria", type=Path, default=None, help="B: JSONL de auditoría del control (consumido/publicado/ack_fallido)")\n'),
    ("        nuevos = incorporar(rapidas + decisiones, estado, NUNCA_BLOQUEAR_V2, a.politica, leido_en)\n",
     "        nuevos = incorporar(rapidas + decisiones, estado, NUNCA_BLOQUEAR_V2, a.politica, leido_en)\n"
     "        d5_resp = None\n"
     "        if a.control_d5 is not None and a.control_d5.exists():\n"
     "            d5_resp = _aplicar_control_d5(a.control_d5, estado, a.d5_origen, reloj())\n"
     '            _auditar_d5(a.d5_auditoria, dict({"evento": "consumido", "t": d5_resp["t"]}, **{k: d5_resp[k] for k in ("id", "ok", "duplicada", "quitado", "error") if k in d5_resp}))\n'
     '            if not d5_resp["ok"]:\n'
     "                _escribir_ack_d5(a.control_d5, d5_resp)\n"
     '        d5_forzar = bool(d5_resp and d5_resp["ok"])\n'),
    ("        toca = (not a.seguir or nuevos or ultima_pub is None\n", "        toca = (not a.seguir or nuevos or d5_forzar or ultima_pub is None\n"),
    ("            ultima_pub = ahora\n            _guardar_estado(a.estado, estado)\n",
     "            ultima_pub = ahora\n            _guardar_estado(a.estado, estado)\n"
     "            if d5_forzar:   # el acuse significa: estado limpio, persistido y feed republicado (secuencia N) sin ese origen\n"
     '                d5_resp["secuencia"] = obj["secuencia"]\n'
     '                _auditar_d5(a.d5_auditoria, {"evento": "publicado", "id": d5_resp["id"], "secuencia": obj["secuencia"], "t": reloj()})\n'
     "                if not _escribir_ack_d5(a.control_d5, d5_resp):\n"
     '                    _auditar_d5(a.d5_auditoria, {"evento": "ack_fallido", "id": d5_resp["id"], "t": reloj()})\n'),
]


def main(origen, salida):
    t = open(origen, encoding="utf-8").read()
    mal = []
    for a, b in SUST:
        if t.count(a) != 1:
            mal.append((t.count(a), a[:70]))
        t = t.replace(a, b, 1)
    open(salida, "w", encoding="utf-8", newline="\n").write(t)
    print("sustituciones: %d, fallidas: %s" % (len(SUST), mal or "ninguna"))
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
