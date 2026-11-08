#!/usr/bin/env python3
"""Banco de la enmienda P1: arma un HOME «tipo Sensor1» para correr s50 (4b) con datos REALES del 3B (motor, ciclos e
inventario del 2026-11-01) y datos de salud/EVE SINTÉTICOS con eventos de diseño conocido (comprueban código, no son medidas).

  generar_entorno_4b.py HOME escenario variante
    escenario  limpio | eventos        (eventos = ráfaga de descartes + hueco de EVE + stats sin kernel_drops)
    variante   p1 | congelada          (p1 = salud_captura 2026-11-06.1 en herramientas-20261106; congelada = la de ec78ca5)
Variables: HERR (herramientas planas), D3B (evidencia/sensor del 3B), CONGELADA (salud_captura de ec78ca5), AQUI (esta carpeta).
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

AQUI = Path(os.environ.get("AQUI", Path(__file__).resolve().parent))
sys.path.insert(0, str(AQUI))
import datos_sinteticos as ds  # noqa: E402

HERR = Path(os.environ["HERR"])
D3B = Path(os.environ["D3B"])
CONGELADA = Path(os.environ.get("CONGELADA", "/congelada/salud_captura.py"))

DIA = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)


def utc(h, m, s=0):
    return (DIA + dt.timedelta(hours=h, minutes=m, seconds=s)).timestamp()


CD, CH = utc(7, 32), utc(8, 5)              # control (como el del 3B: 2 644 ventanas)
INI, FIN = utc(7, 20), utc(8, 16)           # cobertura de las fuentes de salud
INV = ("2026-11-01T07:24:40Z", "2026-11-01T10:05:30Z")
EVENTOS = {"rafagas": [(utc(7, 45, 0), 23)],
           "huecos": [(utc(7, 52, 10), utc(7, 53, 50))],
           "sin_drops": [(utc(7, 58, 0), utc(7, 58, 40))]}
# Para la enmienda de p_7/4C no se usan marcas; s50 4b crea marcas vacías.


def sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def muestras(t0: float, t1: float) -> str:
    out, t, n = [], t0, 0
    while t <= t1:
        n += 1
        out.append({
            "t": round(t, 3), "utc": dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(), "version": "2026-11-06.1",
            "suricata": {"ok": False, "motivo": "sin bloque con capture.kernel_drops en la cola del fichero"},
            "unidades": {u: {"ok": True, "pid": 100 + i, "nrestarts": 0, "activo": "active", "arranque_mono_us": 1000 + i}
                         for i, u in enumerate(("ppi-motor", "ppi-motor-capture", "ppi-via-rapida@ens37",
                                                "ppi-publicar-feed-v2", "suricata"))},
            "anillo": {"ok": True, "ficheros": 180, "mas_nuevo": "live-x.pcap", "inicio_mas_nuevo": t, "mtime_mas_nuevo": t,
                       "salto_max_s": 5, "saltos_contados": 39},
            "archivador": {"ok": True, "estado": "OK", "lineas_ok": 10 * n, "lineas_fallo": 0, "perdidos": 0},
            "via_rapida": {"ok": True, "paquetes_tcp": 1000 * n, "bytes_pendientes": 0, "cpu_s": 1.0, "bloque_hasta": t - 0.4,
                           "antiguedad_s": 0.4},
            "motor": {"ok": True, "duracion_s": 2.0, "retraso_pcap_s": 3.0, "ventanas_pendientes": 0, "fin_ciclo": t - 1,
                      "antiguedad_s": 1.0}})
        t += 10.0
    return "\n".join(json.dumps(m, sort_keys=True) for m in out) + "\n"


def main(home: Path, escenario: str, variante: str) -> None:
    ev = EVENTOS if escenario == "eventos" else {}
    h = home
    for d in ("cyberflow/.venv/bin", "cf-e4/herramientas", "cyberflow-e4/ec78ca5/scripts/etapa4",
              "cyberflow-e4/herramientas-20261106", "cf-e4/4b/salud", "cf-e4/4b/copias/feed-v2", "cf-e4/4b/replay",
              "cf-e4/4b/eve", "cf-e4/4b/estado-inicial", "cf-e4/4b/archivo-pcap"):
        (h / d).mkdir(parents=True, exist_ok=True)
    py = h / "cyberflow/.venv/bin/python"
    if not py.exists():
        py.symlink_to(Path(sys.executable))
    # herramientas planas: las 10 + 2 de herramientas-e4.sha256 (salud_captura va aparte)
    nombres = ["analizar.py", "analizar_3b.py", "poblacion.py", "calidad_fuentes.py", "extraer_evidencia_destino.py",
               "recalcular_caracteristicas.py", "generar_respaldos.py", "verificar_integridad.py", "control_4b.py",
               "referencia_trafico_4c.py", "config-campana-4c.json", "escenarios-4c.json"]
    for n in nombres:
        shutil.copy2(HERR / n, h / "cf-e4/herramientas" / n)
    if os.environ.get("CONTROL_4B"):          # banco del defecto: el control_4b ORIGINAL (2026-11-02.1)
        shutil.copy2(os.environ["CONTROL_4B"], h / "cf-e4/herramientas/control_4b.py")
    (h / "cf-e4/herramientas/herramientas-e4.sha256").write_text(
        "".join(f"{sha(h / 'cf-e4/herramientas' / n)}  {n}\n" for n in nombres), encoding="utf-8")
    # salud_captura: P1 en herramientas-20261106 (con su SHA256SUMS) o la congelada en ec78ca5
    p1 = h / "cyberflow-e4/herramientas-20261106"
    shutil.copy2(HERR / "salud_captura.py", p1 / "salud_captura.py")
    (p1 / "SHA256SUMS").write_text(f"{sha(p1 / 'salud_captura.py')}  ./salud_captura.py\n", encoding="utf-8")
    e4 = h / "cyberflow-e4/ec78ca5"
    if variante == "congelada":
        shutil.copy2(CONGELADA, e4 / "scripts/etapa4/salud_captura.py")
    else:
        (e4 / "scripts/etapa4/salud_captura.py").write_text("# marcador: el código candidato no se usa para medir salud\n")
    (e4 / "SHA256SUMS").write_text(f"{sha(e4 / 'scripts/etapa4/salud_captura.py')}  scripts/etapa4/salud_captura.py\n",
                                   encoding="utf-8")
    shutil.copy2(e4 / "scripts/etapa4/salud_captura.py", e4 / "scripts/etapa4/trafico_observado.py")
    (e4 / "SHA256SUMS").write_text("".join(f"{sha(e4 / 'scripts/etapa4' / n)}  scripts/etapa4/{n}\n"
                                            for n in ("salud_captura.py", "trafico_observado.py")), encoding="utf-8")
    b = h / "cf-e4/4b"
    # datos REALES del 3B
    with gzip.open(D3B / "copias/motor_decision.log.gz", "rb") as src, open(b / "copias/motor_decision.log", "wb") as dst:
        shutil.copyfileobj(src, dst)
    shutil.copy2(D3B / "copias/ciclos.jsonl", b / "copias/ciclos.jsonl")
    with gzip.open(D3B / "replay/motor_decision.log.gz", "rb") as src, open(b / "replay/motor_decision.log", "wb") as dst:
        shutil.copyfileobj(src, dst)
    # datos SINTÉTICOS de salud y EVE
    (b / "salud/muestras.jsonl").write_text(muestras(INI, FIN), encoding="utf-8")
    (b / "salud/tcpdump-anillo.log").write_text(ds.tcpdump_log(INI - 60, FIN + 60, pid=777), encoding="utf-8")
    (b / "salud/tcpdump-via.log").write_text(ds.tcpdump_log(INI - 60, FIN + 60, pid=888), encoding="utf-8")
    (b / "copias/eve-segmento.json").write_bytes(ds.eve_stats(INI - 60, FIN + 60, arranque=INI - 86400, **ev))
    (b / "copias/feed-v2/senales-rapidas.jsonl").write_text("", encoding="utf-8")
    (b / "copias/feed-v2/traza.jsonl").write_text("", encoding="utf-8")
    (b / "copias/stats-inicio.log").write_text("", encoding="utf-8")
    (b / "eve/inicio.json").write_text(json.dumps({"t": INI, "inode": 1, "size": 0}), encoding="utf-8")
    (b / "estado-inicial/arranque-motor.t").write_text("1\n", encoding="utf-8")
    print(json.dumps({"home": str(h), "escenario": escenario, "variante": variante, "control": [ds.iso(CD), ds.iso(CH)],
                      "inventario": INV, "eventos": {k: [[ds.iso(x) if isinstance(x, float) else x for x in e] for e in v]
                                                        for k, v in ev.items()}}))


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], sys.argv[3])
