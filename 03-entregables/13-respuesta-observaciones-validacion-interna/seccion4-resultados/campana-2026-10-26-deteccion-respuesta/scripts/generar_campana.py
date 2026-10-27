#!/usr/bin/env python3
"""Generador de la campaña (corre en la Kali del laboratorio autorizado).

Valida la configuración congelada, ordena los episodios con la semilla fija, respeta calentamiento,
contexto previo y observación posterior, y registra inicio y fin por separado (reloj de pared + monotónico),
con la salida COMPLETA de cada episodio.

SEGURO POR DEFECTO: sin --autorizado solo simula (no lanza tráfico). Aborta si la config no valida o quedan
marcadores/valores sin resolver en un escenario habilitado. Las variables de entorno NO cambian parámetros.

Uso (cuando se autorice la campaña A):
    python3 generar_campana.py --config ../escenarios/escenarios.json --salida-dir ./corrida --autorizado
"""
from __future__ import annotations
import argparse, json, os, random, signal, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import esquema_campana as esq  # noqa: E402


def reloj() -> dict:
    return {"pared_utc": datetime.now(timezone.utc).isoformat(), "monotonico": round(time.monotonic(), 6)}


def jsonl(fh, obj):
    fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


def plan_orden(cfg: dict) -> list[tuple[dict, int]]:
    plan = [(s, r) for r in range(1, cfg["repeticiones"] + 1) for s in cfg["escenarios"]]
    random.Random(cfg["semilla"]).shuffle(plan)
    return plan


def correr_episodio(cfg, s, rep, salida_dir: Path, marcas, autorizado: bool) -> str:
    sid = s["id"]
    ep_id = f"{sid}-r{rep}"
    cmd = esq.comando_de(cfg, s)
    (salida_dir / "salidas").mkdir(exist_ok=True)
    out_p = salida_dir / "salidas" / f"{ep_id}.out"
    err_p = salida_dir / "salidas" / f"{ep_id}.err"
    # inicio: se escribe INMEDIATAMENTE y por separado del fin
    jsonl(marcas, {"evento": "inicio", "campana": cfg.get("_campana", "deteccion-respuesta-2026-10-26"),
                   "episodio_id": ep_id, "escenario": sid, "repeticion": rep,
                   "destino": s["destino"], "servicio": s["servicio"], "comando": cmd,
                   "timeout_s": s["timeout_s"], "reloj": reloj()})
    if not autorizado:
        return "simulado"
    estado, cod = "completo", None
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    try:
        with open(out_p, "wb") as fo, open(err_p, "wb") as fe:
            try:
                proc = subprocess.Popen(cmd, stdout=fo, stderr=fe, **kw)
            except OSError as ex:                       # fallo al INICIAR el proceso
                jsonl(marcas, {"evento": "fin", "episodio_id": ep_id, "estado": "error_inicio",
                               "error": str(ex), "reloj": reloj()})
                return "error_inicio"
            pgid = None if os.name == "nt" else os.getpgid(proc.pid)   # se captura AL CREAR, no al matar
            try:
                proc.wait(timeout=s["timeout_s"])
            except subprocess.TimeoutExpired:
                estado = "incompleto_timeout"
            except KeyboardInterrupt:
                estado = "incompleto_interrumpido"
            finally:
                _terminar(proc, pgid)
                if not _grupo_terminado(proc, pgid):
                    estado = (estado if estado != "completo" else "incompleto") + "+grupo_no_terminado"
        cod = proc.poll()
    except KeyboardInterrupt:
        estado = "incompleto_interrumpido"
        _terminar(proc, pgid)
        if not _grupo_terminado(proc, pgid):
            estado += "+grupo_no_terminado"
        cod = proc.poll()
    if estado == "completo" and cod not in (0, None):   # un comando con código != 0 NO es 'completo'
        estado = f"incompleto_error_rc_{cod}"
    intentos = _leer_intentos(out_p)
    jsonl(marcas, {"evento": "fin", "episodio_id": ep_id, "estado": estado, "codigo_salida": cod,
                   "reloj": reloj(), "bytes_stdout": out_p.stat().st_size, "bytes_stderr": err_p.stat().st_size,
                   "intentos_generador": intentos,
                   "intentos_fuente": ("contador de iteraciones del bucle (INTENTOS, no peticiones enviadas ni "
                                       "respuestas)" if intentos is not None else "nmap: su stdout"),
                   "medida_real_en": "peticiones/respuestas/errores/timeouts se miden con PCAP/EVE/servidor",
                   "salida_stdout": str(out_p), "salida_stderr": str(err_p)})
    return estado


def _leer_intentos(out_p: Path):
    """Lee 'intentos=<N>' (iteraciones del bucle) que imprime el comando. None si no lo produce (p.ej. nmap)."""
    try:
        for linea in reversed(out_p.read_text(encoding="utf-8", errors="replace").splitlines()):
            if linea.startswith("intentos="):
                return int(linea.split("=", 1)[1])
    except (OSError, ValueError):
        pass
    return None


def _terminar(proc, pgid):
    """Termina el proceso y TODO su grupo, aunque el padre ya haya terminado (usa el pgid capturado al crear)."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):        # SIGKILL no se puede ignorar
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            break
        time.sleep(0.5 if sig == signal.SIGTERM else 1.5)
    try:
        proc.wait(timeout=10)                            # recoge al padre (evita zombie)
    except subprocess.TimeoutExpired:
        pass


def _grupo_terminado(proc, pgid) -> bool:
    """True si no queda ningún proceso vivo en el grupo. En Windows, aproxima con el padre."""
    if os.name == "nt":
        return proc.poll() is not None
    try:
        os.killpg(pgid, 0)        # señal 0: solo comprueba existencia de procesos en el grupo
        return False
    except ProcessLookupError:
        return True
    except PermissionError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--salida-dir", default="corrida")
    ap.add_argument("--autorizado", action="store_true", help="lanza tráfico real; sin esto, simula")
    ap.add_argument("--solo-habilitados", action="store_true",
                    help="omite (sin abortar) los escenarios con habilitado:false; sin esto, un escenario "
                         "deshabilitado o no resuelto aborta")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))

    problemas = esq.validar(cfg, exigir_herramientas=a.autorizado)
    activos = [s for s in cfg["escenarios"] if s.get("habilitado")]
    pendientes = [s for s in cfg["escenarios"] if not s.get("habilitado")]
    if pendientes and not a.solo_habilitados:
        problemas += [f"escenario {s['id']} deshabilitado: {s.get('motivo_deshabilitado','?')} "
                      f"(usa --solo-habilitados para omitirlo)" for s in pendientes]
    if problemas:
        print("CONFIG INVÁLIDA — abortando. Problemas:", file=sys.stderr)
        for p in problemas:
            print("  -", p, file=sys.stderr)
        return 2

    sd = Path(a.salida_dir)
    sd.mkdir(parents=True, exist_ok=True)
    # registra la config EFECTIVA tal como se usó (solo los habilitados que se correrán)
    efectiva = dict(cfg)
    efectiva["escenarios"] = activos
    efectiva["_efectiva_utc"] = datetime.now(timezone.utc).isoformat()
    efectiva["_autorizado"] = a.autorizado
    (sd / "config-efectiva.json").write_text(json.dumps(efectiva, ensure_ascii=False, indent=1), encoding="utf-8")

    plan = [(s, r) for (s, r) in plan_orden(cfg) if s.get("habilitado")]
    modo = "AUTORIZADO (lanza tráfico)" if a.autorizado else "SIMULACIÓN (no lanza tráfico)"
    t = cfg["tiempos_s"]
    print(f"{modo} · {len(plan)} episodios · calentamiento {t['calentamiento_inicial']} s · "
          f"contexto previo {t['contexto_antes']} s · observación {t['observacion_despues']} s")
    marcas = open(sd / "marcas.jsonl", "a", encoding="utf-8")
    jsonl(marcas, {"evento": "campana_inicio", "modo": modo, "orden": [f"{s['id']}-r{r}" for s, r in plan],
                   "reloj": reloj()})
    if a.autorizado:
        time.sleep(t["calentamiento_inicial"] + t["contexto_antes"])
    fin_estado = "completa"
    try:
        for n, (s, rep) in enumerate(plan, 1):
            print(f"[{n}/{len(plan)}] {s['id']}-r{rep}: {' '.join(esq.comando_de(cfg, s)[:3])}…")
            estado = correr_episodio(cfg, s, rep, sd, marcas, a.autorizado)
            print(f"        -> {estado}")
            if "grupo_no_terminado" in estado:
                # no se pudo asegurar la terminación: NO iniciar otro episodio con un generador quizá vivo
                fin_estado = "abortada_grupo_no_terminado"
                print("ABORTA: no se aseguró la terminación del grupo; no se inicia el siguiente episodio", flush=True)
                break
            if estado == "incompleto_interrumpido":
                # tras una interrupción: detener la campaña y recoger registros; NO seguir con el siguiente
                fin_estado = "interrumpida"
                break
            if a.autorizado:
                time.sleep(t["observacion_despues"])        # cola/observación del episodio actual
                if n < len(plan):
                    time.sleep(t["contexto_antes"])          # historia previa del siguiente
    except KeyboardInterrupt:
        fin_estado = "interrumpida"
        print("interrumpida: se detiene la campaña y se recogen los registros", flush=True)
    jsonl(marcas, {"evento": "campana_fin", "estado": fin_estado, "reloj": reloj()})
    marcas.close()
    return 0 if fin_estado == "completa" else 130


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrumpido", file=sys.stderr)
        raise SystemExit(130)
