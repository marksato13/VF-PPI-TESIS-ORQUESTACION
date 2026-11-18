#!/usr/bin/env python3
"""[COPIA DE BANCO: D5 sin reinicio, decisión E; no instalada, no conectada al orquestador]
Limpieza D5 por episodio de la Campaña B. Solo biblioteca estándar.

Qué limpia (y SOLO esto): del estado del publicador, las claves del origen del experimento (Kali) en `vigentes`
("ip|destino|alcance") y en `escalada` ("ip@destino"). No toca `eventos` (impide releer lo ya procesado), ni
`secuencia`, ni ninguna otra IP, ni ningún registro: traza.jsonl, senales-*.jsonl, via-rapida-*.jsonl, la traza del agente y el
estado del agente se conservan. Cada limpieza deja una copia del estado anterior y una línea en `d5.jsonl`.

Cómo limpia sin sudo: el publicador es un servicio de m4rk con Restart=always. Se congela (SIGSTOP), se reescribe su estado de
forma atómica y se mata (SIGKILL): congelado no puede volver a escribir el estado viejo, y systemd lo reinicia ya con el limpio.

Puerta previa a cada episodio (`puerta`): 1) limpiar el estado; 2) esperar un feed NUEVO, vigente y sin entradas del origen;
3) comprobar en srv-dmz que nftables no contiene al origen (si lo contiene, `retirar_origen` y volver a comprobar);
4) esperar más que un refresco del feed y comprobar que el agente no volvió a aplicarlo, que el set sigue sin él y que el
feed sigue limpio. Si algo falla, el episodio ESPERA (se reintenta la puerta; agotados los intentos, no inicia).
Subcomandos locales (cada uno se ejecuta en su host y escribe JSON): sensor-limpiar, sensor-feed, srv-nft, srv-retirar, srv-agente.
"""
import argparse
import copy
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

ORIGEN = "10.10.20.30"
UNIDAD = "ppi-publicar-feed-v2.service"
HELPER = "/usr/local/sbin/cf-nft-helper"
REFRESCO_S = 20.0           # --refresco-segundos del publicador
ESPERA_AGENTE_S = 25.0      # > un refresco: da tiempo a que un feed viejo se relea
ESPERA_FEED_S = 60.0


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ estado del publicador
def limpiar_estado(estado: dict, origen: str):
    nuevo = copy.deepcopy(estado)
    quitado = {"vigentes": [], "escalada": []}
    for k in list(nuevo.get("vigentes", {})):
        if k.split("|", 1)[0] == origen:
            quitado["vigentes"].append(k)
            del nuevo["vigentes"][k]
    for k in list(nuevo.get("escalada", {})):
        if k.split("@", 1)[0] == origen:
            quitado["escalada"].append(k)
            del nuevo["escalada"][k]
    return nuevo, quitado


def pid_unidad(unidad: str = UNIDAD) -> int:
    r = subprocess.run(["systemctl", "show", unidad, "-p", "MainPID", "--value"], capture_output=True, text=True)
    return int((r.stdout or "0").strip() or 0)


def sensor_limpiar(estado_p, origen, auditoria, real, ahora=time.time, pid_de=pid_unidad, senal=os.kill):
    ruta = os.fspath(estado_p)
    crudo = open(ruta, "rb").read()
    try:
        estado = json.loads(crudo)
        assert isinstance(estado, dict) and ("vigentes" in estado or "escalada" in estado)
    except (ValueError, AssertionError):
        return {"ok": False, "rc": 2, "motivo": "estado del publicador ilegible o con otra forma"}
    nuevo, quitado = limpiar_estado(estado, origen)
    t = ahora()
    rep = {"ok": True, "rc": 0, "t": t, "origen": origen, "modo": "real" if real else "seco", "quitado": quitado,
           "sha_antes": sha(crudo), "hay_que_quitar": bool(quitado["vigentes"] or quitado["escalada"])}
    if not real:
        return rep
    os.makedirs(auditoria, exist_ok=True)
    copia = os.path.join(auditoria, "estado-antes-%d.json" % int(t * 1000))
    with open(copia, "wb") as fh:                                  # conservar lo anterior ANTES de cambiar nada
        fh.write(crudo)
    pid = pid_de()
    if pid <= 1:
        return dict(rep, ok=False, rc=3, motivo="el publicador no está en marcha (MainPID=%s)" % pid)
    senal(pid, signal.SIGSTOP)
    try:
        nuevo_b = json.dumps(nuevo, sort_keys=True).encode()
        tmp = ruta + ".d5.tmp"
        with open(tmp, "wb") as fh:
            fh.write(nuevo_b)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, ruta)
    finally:
        senal(pid, signal.SIGKILL)                                  # muere sin escribir; systemd lo reinicia
    rep.update(pid=pid, sha_despues=sha(open(ruta, "rb").read()), copia_anterior=copia)
    with open(os.path.join(auditoria, "d5.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rep, sort_keys=True) + "\n")
    return rep


def sensor_feed(feed_p, origen, desde, ahora=time.time):
    try:
        obj = json.load(open(os.fspath(feed_p), encoding="utf-8"))
        gen, exp, ent = float(obj["generado"]), float(obj["expira"]), list(obj["entradas"])
    except (OSError, ValueError, KeyError, TypeError):
        return {"ok": False, "rc": 2, "motivo": "feed ilegible"}
    propias = [e.get("id") or e.get("accion") for e in ent if isinstance(e, dict) and e.get("ip") == origen]
    return {"ok": True, "rc": 0, "secuencia": obj.get("secuencia"), "generado": gen, "fresco": gen > desde,
            "vigente": exp > ahora(), "entradas_origen": propias, "limpio": not propias}


# ------------------------------------------------------------------ srv-dmz
def _helper(peticion, orden=("sudo", "-n", HELPER), correr=subprocess.run):
    r = correr(list(orden), input=json.dumps(peticion), capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"ok": False, "rechazo": "salida_ilegible", "stderr": (r.stderr or "")[:200]}


SETS_APLICACION = ("bloqueados", "limitados")   # los únicos sets sobre los que las reglas de la cadena hacen match (y descartan)
RESIDUAL = "descartes_limite"                  # contador dinámico de INSTRUMENTACIÓN (paquetes descartados por exceder la tasa): nunca descarta nada


def srv_nft(origen, helper=_helper):
    """Estado del origen en nftables. `presente`/`donde` cuentan SOLO los sets de aplicación: una restricción activa los bloquea. El contador `descartes_limite`
    es evidencia, no restricción (en el 11-nov-2026 su resto de la inundación bloqueó la puerta sin que ninguna regla pudiera actuar): se informa aparte en `residual`
    y NUNCA se borra. Fallo cerrado: si el estado no se puede verificar (helper, formato, sets de aplicación ausentes o ilegibles) devuelve `ok` False."""
    r = helper({"perfil": "dmz", "operaciones": [{"op": "listar"}]})
    if not r.get("ok"):
        return {"ok": False, "rc": 2, "motivo": "listar falló: %s" % (r.get("rechazo") or r.get("error_nft"))}
    est = r.get("estado")
    if not isinstance(est, dict):
        return {"ok": False, "rc": 2, "motivo": "estado ilegible"}
    sets = est.get("sets")
    if not isinstance(sets, dict) or any(not isinstance(sets.get(s), dict) for s in SETS_APLICACION):
        return {"ok": False, "rc": 2, "motivo": "sets de aplicación ausentes o ilegibles"}
    desc = est.get(RESIDUAL)
    if desc is not None and not isinstance(desc, dict):
        return {"ok": False, "rc": 2, "motivo": "%s ilegible" % RESIDUAL}
    donde = [s for s, el in sets.items() if s != RESIDUAL and el and origen in el]
    residual = {RESIDUAL: desc[origen]} if desc and origen in desc else {}
    return {"ok": True, "rc": 0, "tabla": True, "presente": bool(donde), "donde": donde, "residual": residual}


def srv_estado(origen, helper=_helper, ahora=time.time):
    """Sustituye a estado_sombra.py en la vigilancia de B (X2 -> P1). Primera línea del vigía: epoch; aquí, el campo `t`.
    rc 0: ninguna restricción, o solo sobre el origen del experimento; rc 1: restricción sobre OTRA IP (cancela, P1);
    rc 2: no se pudo leer (pausa, no se presume nada)."""
    r = helper({"perfil": "dmz", "operaciones": [{"op": "listar"}]})
    t = ahora()
    if not r.get("ok"):
        return {"ok": False, "rc": 2, "t": t, "motivo": "listar falló: %s" % (r.get("rechazo") or r.get("error_nft"))}
    est = r.get("estado") or {}
    ajenas = sorted({ip for el in (est.get("sets") or {}).values() for ip in (el or {}) if ip != origen})
    sin_id = sorted({ip for el in (est.get("sets") or {}).values() for ip, v in (el or {}).items() if v is not None and not v.get("id")})
    if ajenas:
        return {"ok": True, "rc": 1, "t": t, "ajenas": ajenas, "resumen": "P1 restricción sobre IP distinta de %s: %s" % (origen, ",".join(ajenas))}
    return {"ok": True, "rc": 0, "t": t, "ajenas": [], "sin_id": sin_id, "propias": sorted(
        s for s, el in (est.get("sets") or {}).items() if el and origen in el)}


def srv_retirar(origen, real, helper=_helper):
    antes = srv_nft(origen, helper)
    if not antes["ok"]:
        return antes
    if not antes["presente"]:
        return {"ok": True, "rc": 0, "retirado": False, "motivo": "no estaba"}
    if not real:
        return {"ok": True, "rc": 0, "retirado": False, "seco": True, "habria_retirado_de": antes["donde"]}
    r = helper({"perfil": "dmz", "operaciones": [{"op": "retirar_origen", "ip": origen}]})
    if not r.get("ok"):
        return {"ok": False, "rc": 3, "motivo": "retirar_origen falló: %s" % (r.get("rechazo") or r.get("error_nft"))}
    return {"ok": True, "rc": 0, "retirado": True, "t": time.time()}


def srv_agente(traza_p, origen, desde, max_bytes=8 << 20):
    try:
        with open(os.fspath(traza_p), "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - max_bytes))
            lineas = fh.read().splitlines()
    except OSError:
        return {"ok": False, "rc": 2, "motivo": "traza del agente ilegible"}
    n, ult = 0, None
    for l in lineas:
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if e.get("evento") == "aplicacion" and e.get("aplicado_en", 0) > desde:
            if any(x.get("ip") == origen for x in e.get("nuevos", [])):
                n += 1
                ult = e["aplicado_en"]
    return {"ok": True, "rc": 0, "aplicaciones_nuevas": n, "ultima": ult}


# ------------------------------------------------------------------ puerta (en el bastión)
class Puerta:
    """runners.sensor(cmd, **kw) y runners.srv(cmd, **kw) devuelven el dict JSON del subcomando remoto."""

    def __init__(self, runners, origen=ORIGEN, ahora=time.time, dormir=time.sleep, espera_agente=ESPERA_AGENTE_S,
                 espera_feed=ESPERA_FEED_S, sondeo=2.0):
        self.r, self.origen, self.ahora, self.dormir = runners, origen, ahora, dormir
        self.espera_agente, self.espera_feed, self.sondeo = espera_agente, espera_feed, sondeo

    def _feed_limpio(self, desde):
        lim = self.ahora() + self.espera_feed
        ult = None
        while True:
            ult = self.r.sensor("feed", origen=self.origen, desde=desde)
            if ult.get("ok") and ult["fresco"] and ult["vigente"] and ult["limpio"]:
                return True, ult
            if self.ahora() >= lim:
                return False, ult
            self.dormir(self.sondeo)

    def una_vez(self):
        pasos, motivos = [], []

        def paso(nombre, r):
            pasos.append({"paso": nombre, "t": self.ahora(), **{k: v for k, v in r.items() if k != "t"}})
            return r
        r = paso("limpiar", self.r.sensor("limpiar", origen=self.origen))
        if not r.get("ok"):
            return {"lista": False, "motivos": ["limpieza falló: %s" % r.get("motivo")], "pasos": pasos}
        t_limpio = r.get("t_limpio", self.ahora())          # BANCO: desde la solicitud, no desde el retorno
        ok, f = self._feed_limpio(t_limpio)
        paso("feed_tras_limpiar", f or {})
        if not ok:
            return {"lista": False, "pasos": pasos,
                    "motivos": ["no hay un feed nuevo, vigente y sin propuesta heredada: %s" % json.dumps(f, sort_keys=True)[:200]]}
        n = paso("nft_antes", self.r.srv("nft", origen=self.origen))
        if not n.get("ok"):
            return {"lista": False, "motivos": ["no se pudo leer nftables: %s" % n.get("motivo")], "pasos": pasos}
        if n["presente"]:
            ret = paso("retirar", self.r.srv("retirar", origen=self.origen))
            if not ret.get("ok"):
                return {"lista": False, "motivos": ["retirar_origen falló: %s" % ret.get("motivo")], "pasos": pasos}
        t_ret = self.ahora()
        self.dormir(self.espera_agente)
        n2 = paso("nft_despues", self.r.srv("nft", origen=self.origen))
        if not n2.get("ok") or n2["presente"]:
            motivos.append("nftables aún contiene al origen o no se pudo leer: %s" % n2.get("donde", n2.get("motivo")))
        a = paso("agente", self.r.srv("agente", origen=self.origen, desde=t_ret))
        if not a.get("ok") or a["aplicaciones_nuevas"]:
            motivos.append("el agente volvió a aplicar al origen (%s)" % a.get("aplicaciones_nuevas", a.get("motivo")))
        f2 = paso("feed_final", self.r.sensor("feed", origen=self.origen, desde=t_ret))
        if not (f2.get("ok") and f2["fresco"] and f2["vigente"] and f2["limpio"]):
            motivos.append("el feed final no es nuevo, vigente y limpio: %s" % json.dumps(f2, sort_keys=True)[:200])
        residual = {}
        for p in pasos:
            if p.get("residual"):
                residual = p["residual"]
        return {"lista": not motivos, "motivos": motivos, "pasos": pasos, "residual_conservado": residual}

    def preparar_episodio(self, intentos=5, espera_entre=30.0, auditoria=None):
        hist = []
        for i in range(1, intentos + 1):
            res = self.una_vez()
            res["intento"] = i
            res["t"] = self.ahora()
            hist.append(res)
            if auditoria:
                with open(auditoria, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(res, sort_keys=True) + "\n")
            if res["lista"]:
                return {"lista": True, "intentos": i, "historial": hist}
            self.dormir(espera_entre)
        return {"lista": False, "intentos": intentos, "historial": hist}


# ------------------------------------------------------------------ BANCO: D5 sin reinicio (decisión E, solo banco)
def limpiar_sin_reinicio(adaptador, origen, real, ahora=time.time):
    """Sustituye a `sensor_limpiar`: pide la limpieza por el canal de control (adaptador aislado) y SOLO un acuse válido devuelve ok.
    `t_limpio` = instante de la solicitud (el feed posterior es el «nuevo»). Sin acuse, o con resultado incierto: ok False con la evidencia."""
    if origen != ORIGEN:
        return {"ok": False, "rc": 2, "motivo": "la limpieza D5 solo admite el origen del experimento %s" % ORIGEN}
    t = ahora()
    base = {"t": t, "t_limpio": t, "origen": origen, "modo": "real" if real else "seco"}
    if not real:
        return dict(base, ok=True, rc=0, hay_que_quitar=None)
    r = adaptador.limpiar(origen)
    if r["ok"]:
        q = r.get("quitado") or {}
        return dict(base, ok=True, rc=0, quitado=q, hay_que_quitar=bool(q.get("vigentes") or q.get("escalada")), secuencia=r.get("secuencia"),
                    acuse=True, duplicada=bool(r.get("duplicada")))
    return dict(base, ok=False, rc=r.get("rc") or 1, incierto=bool(r.get("incierto")), publicacion=r.get("publicacion"), secuencia=r.get("secuencia"),
                evidencia=r.get("evidencia"), traza_auditoria=r.get("traza_auditoria"),
                motivo="sin acuse válido: %s%s" % (r.get("estado"), (" / " + r["categoria"]) if r.get("categoria") else ""))


class RunnersBanco:
    """Los `runners` de `Puerta` para el banco: sensor (limpiar/feed) con el adaptador y el feed local; srv (nft/retirar/agente) con un ayudante inyectable."""

    def __init__(self, adaptador, feed_p, traza_p, helper, real=True, ahora=time.time):
        self.adaptador, self.feed_p, self.traza_p, self.helper, self.real, self.ahora = adaptador, feed_p, traza_p, helper, real, ahora

    def sensor(self, cmd, **kw):
        if cmd == "limpiar":
            return limpiar_sin_reinicio(self.adaptador, kw["origen"], self.real, self.ahora)
        if cmd == "feed":
            return sensor_feed(self.feed_p, kw["origen"], kw["desde"], self.ahora)
        raise ValueError(cmd)

    def srv(self, cmd, **kw):
        if cmd == "nft":
            return srv_nft(kw["origen"], self.helper)
        if cmd == "retirar":
            return srv_retirar(kw["origen"], self.real, self.helper)
        if cmd == "agente":
            return srv_agente(self.traza_p, kw["origen"], kw["desde"])
        raise ValueError(cmd)


class PuertaBanco(Puerta):
    """Puerta con BLOQUEO: solo un acuse válido (y el resto de comprobaciones) deja pasar. Tras cualquier `lista = False` queda bloqueada:
    las llamadas siguientes devuelven la evidencia del caso y NO emiten solicitudes (ni con id nuevo). `reanudar_manual` exige quién y por qué.
    La puerta REAL crea una `Puerta` nueva en cada llamada (`compuerta_b.puerta_fn`) y el proceso puede reiniciarse: por eso, con `estado_bloqueo`,
    el bloqueo vive en un FICHERO (escritura atómica) y un cerrojo `flock` serializa las instancias; un fichero ilegible cuenta como bloqueado."""

    def __init__(self, runners, registro=None, estado_bloqueo=None, **kw):
        super().__init__(runners, **kw)
        self.registro, self.estado_bloqueo = registro, estado_bloqueo
        self.bloqueada, self.intentos_de_puerta, self.omitidas = None, 0, 0

    def _log(self, reg):
        if self.registro is not None:
            with open(self.registro, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(reg, t=self.ahora()), sort_keys=True, default=str) + "\n")

    def _cerrojo(self):
        if not self.estado_bloqueo:
            return None
        try:
            import fcntl
        except ImportError:                                   # pragma: no cover (solo Linux)
            return None
        fh = open(self.estado_bloqueo + ".lock", "a")
        fcntl.flock(fh, fcntl.LOCK_EX)
        return fh

    def _bloqueo_actual(self):
        if self.estado_bloqueo and os.path.exists(self.estado_bloqueo):
            try:
                with open(self.estado_bloqueo, encoding="utf-8") as fh:
                    return json.load(fh)
            except (OSError, ValueError):
                return {"motivos": ["fichero de bloqueo ilegible: se trata como bloqueado"], "pasos": [], "ilegible": True}
        return self.bloqueada

    def _fijar_bloqueo(self, res):
        self.bloqueada = res
        if self.estado_bloqueo:
            tmp = self.estado_bloqueo + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(res, sort_keys=True, default=str))
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.estado_bloqueo)

    def una_vez(self):
        cerrojo = self._cerrojo()
        try:
            b = self._bloqueo_actual()
            if b is not None:
                self.bloqueada = b
                self.omitidas += 1
                self._log({"evento": "omitida_por_puerta_bloqueada", "motivos": b.get("motivos")})
                return {"lista": False, "bloqueada": True, "pasos": [], "evidencia_del_caso": b,
                        "motivos": ["puerta bloqueada tras un caso fallido o incierto: requiere reanudación manual registrada"]}
            self.intentos_de_puerta += 1
            res = super().una_vez()
            self._log({"evento": "puerta_lista" if res["lista"] else "puerta_bloqueada", "motivos": res.get("motivos"), "pasos": [p["paso"] for p in res.get("pasos", [])]})
            if not res["lista"]:
                self._fijar_bloqueo(res)
            return res
        finally:
            if cerrojo:
                cerrojo.close()

    def preparar_episodio(self, intentos=5, espera_entre=30.0, auditoria=None):
        """Un solo intento: no hay reintento automático (repetiría la solicitud)."""
        res = self.una_vez()
        res["intento"], res["t"] = 1, self.ahora()
        if auditoria:
            with open(auditoria, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(res, sort_keys=True, default=str) + "\n")
        return {"lista": res["lista"], "intentos": 1, "historial": [res], "bloqueada": self._bloqueo_actual() is not None}

    def reanudar_manual(self, quien, motivo):
        if not str(quien).strip() or not str(motivo).strip():
            raise ValueError("la reanudación requiere quién la decide y por qué")
        cerrojo = self._cerrojo()
        try:
            b = self._bloqueo_actual()
            if b is None:
                raise ValueError("no hay un bloqueo que reanudar")
            self._log({"evento": "reanudacion_manual", "por": quien, "motivo": motivo,
                       "caso_bloqueado": [p.get("evidencia") for p in b.get("pasos", []) if p.get("evidencia")]})
            if self.estado_bloqueo and os.path.exists(self.estado_bloqueo):                  # el caso bloqueado se ARCHIVA, no se borra
                os.replace(self.estado_bloqueo, "%s.reanudado-%d.json" % (self.estado_bloqueo, int(self.ahora() * 1000)))
            self.bloqueada = None
        finally:
            if cerrojo:
                cerrojo.close()


def puerta_fn_banco(directorio, runners, **kw):
    """Equivale al `puerta_fn` de `compuerta_b.puerta` (que crea una Puerta NUEVA en cada llamada): el bloqueo persiste en `puerta-bloqueo.json`."""
    return PuertaBanco(runners, registro=os.path.join(directorio, "puerta-banco.jsonl"), estado_bloqueo=os.path.join(directorio, "puerta-bloqueo.json"),
                       **kw).preparar_episodio(auditoria=os.path.join(directorio, "puertas-D5.jsonl"))

# ------------------------------------------------------------------ CLI
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("sensor-limpiar", "sensor-feed", "srv-nft", "srv-retirar", "srv-agente", "srv-estado"):
        s = sub.add_parser(n)
        s.add_argument("--origen", default=ORIGEN)
        s.add_argument("--real", action="store_true")
        s.add_argument("--estado", default=os.path.expanduser("~/feed-v2/estado.json"))
        s.add_argument("--auditoria", default=os.path.expanduser("~/feed-v2/d5-auditoria"))
        s.add_argument("--feed", default=os.path.expanduser("~/feed-v2/feed.json"))
        s.add_argument("--traza", default="/var/lib/cyberflow/agente/traza.jsonl")
        s.add_argument("--desde", type=float, default=0.0)
    a = p.parse_args(argv)
    if a.origen != ORIGEN:
        print(json.dumps({"ok": False, "rc": 2, "motivo": "la limpieza D5 solo admite el origen del experimento %s" % ORIGEN}))
        return 2
    r = {"sensor-limpiar": lambda: sensor_limpiar(a.estado, a.origen, a.auditoria, a.real),
         "sensor-feed": lambda: sensor_feed(a.feed, a.origen, a.desde),
         "srv-nft": lambda: srv_nft(a.origen),
         "srv-retirar": lambda: srv_retirar(a.origen, a.real),
         "srv-agente": lambda: srv_agente(a.traza, a.origen, a.desde),
         "srv-estado": lambda: srv_estado(a.origen)}[a.cmd]()
    if a.cmd == "srv-estado":                       # contrato del vigía: 1.ª línea = epoch, resto = resumen, rc = estado
        print("%.6f" % r["t"])
        print(r.get("resumen") or json.dumps(r, sort_keys=True))
        return r["rc"]
    print(json.dumps(r, sort_keys=True))
    return r.get("rc", 0)


if __name__ == "__main__":
    sys.exit(main())
