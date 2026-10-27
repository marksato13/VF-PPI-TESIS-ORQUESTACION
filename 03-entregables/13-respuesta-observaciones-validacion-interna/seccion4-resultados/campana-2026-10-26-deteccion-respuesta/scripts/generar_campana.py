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
    estado = "completo"
    # el proceso y sus hijos quedan en su propio grupo/sesión -> poder terminarlos a todos
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with open(out_p, "wb") as fo, open(err_p, "wb") as fe:
        proc = subprocess.Popen(cmd, stdout=fo, stderr=fe, **kw)
        try:
            proc.wait(timeout=s["timeout_s"])
        except subprocess.TimeoutExpired:
            estado = "incompleto_timeout"
        except KeyboardInterrupt:
            estado = "incompleto_interrumpido"
        finally:
            if proc.poll() is None:
                _matar_grupo(proc)
    cod = proc.poll()
    jsonl(marcas, {"evento": "fin", "episodio_id": ep_id, "estado": estado,
                   "codigo_salida": cod, "reloj": reloj(),
                   "bytes_stdout": out_p.stat().st_size, "bytes_stderr": err_p.stat().st_size,
                   "salida_stdout": str(out_p), "salida_stderr": str(err_p)})
    return estado


def _matar_grupo(proc):
    if os.name == "nt":                       # Windows: termina el árbol de procesos
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    try:                                      # POSIX (Kali): termina el grupo entero
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        time.sleep(3)
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()


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
    for n, (s, rep) in enumerate(plan, 1):
        print(f"[{n}/{len(plan)}] {s['id']}-r{rep}: {' '.join(esq.comando_de(cfg, s)[:3])}…")
        estado = correr_episodio(cfg, s, rep, sd, marcas, a.autorizado)
        print(f"        -> {estado}")
        if a.autorizado and n < len(plan):
            time.sleep(t["observacion_despues"])   # cola del episodio actual
            time.sleep(t["contexto_antes"])        # historia previa del siguiente
    jsonl(marcas, {"evento": "campana_fin", "reloj": reloj()})
    marcas.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrumpido", file=sys.stderr)
        raise SystemExit(130)
