"""Datos sintéticos compartidos por las pruebas de la enmienda P1 de la 4B (comprueban CÓDIGO, no son resultados)."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

T0 = 1794200000.0          # múltiplo de 10 (08-nov-2026 ≈ 01:33Z)
INTERVALO = 8.0            # stats.interval del suricata.yaml desplegado
U05, U03, U01 = -0.5694578968203694, -0.5898535710336618, -0.6223889502095352
IPS = ("10.10.20.21", "10.10.20.22", "10.10.20.23")


def iso(t: float) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_eve(t: float) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "+0000"


def eve_stats(t0: float, t1: float, *, huecos=(), rafagas=(), sin_drops=(), arranque=None, reinicios=(),
              paquetes_por_s: int = 1000, otras_lineas: bool = True, basura_en=None) -> bytes:
    """Líneas EVE: un evento stats cada 8 s y, entre ellos, otros eventos.

    huecos     [(a, b)]  sin eventos stats en [a, b]
    rafagas    [(t, n)]  el contador kernel_drops sube n en la muestra que cae en t (la primera ≥ t)
    sin_drops  [(a, b)]  eventos stats sin la clave kernel_drops en [a, b]
    reinicios  [t]       Suricata se reinicia: uptime y contadores vuelven a 0 en la primera muestra ≥ t
    basura_en  t         una línea stats corrupta (no JSON) en mitad del fichero
    """
    arranque = arranque if arranque is not None else t0 - 4 * 3600
    reinicios = sorted(reinicios)
    out, drops, pk, t, n = [], 0, 0, t0, 0
    pend_rafagas = sorted(rafagas)
    pend_reinicios = list(reinicios)
    while t <= t1:
        while pend_reinicios and t >= pend_reinicios[0]:
            arranque = t - 1.0
            drops, pk = 0, 0
            pend_reinicios.pop(0)
        pk += paquetes_por_s * int(INTERVALO)
        while pend_rafagas and t >= pend_rafagas[0][0]:
            drops += pend_rafagas[0][1]
            pend_rafagas.pop(0)
        en_hueco = any(a <= t <= b for a, b in huecos)
        if not en_hueco:
            cap = {"kernel_packets": pk}
            if not any(a <= t <= b for a, b in sin_drops):
                cap["kernel_drops"] = drops
            ev = {"timestamp": ts_eve(t), "event_type": "stats",
                  "stats": {"uptime": int(t - arranque), "capture": cap}}
            if basura_en is not None and abs(t - basura_en) < 1e-6:
                out.append('{"timestamp": "' + ts_eve(t) + '", "event_type":"stats", "stats": {"uptime": ')
            else:
                out.append(json.dumps(ev, separators=(",", ":")).replace('"event_type":"stats"', '"event_type":"stats"'))
        if otras_lineas:
            out.append(json.dumps({"timestamp": ts_eve(t + 1), "event_type": "flow", "src_ip": "10.10.20.21"}))
        t += INTERVALO
        n += 1
    return ("\n".join(out) + "\n").encode()


def incrementos(t0: float, t1: float, paso: float = 10.0) -> list:
    """Incrementos de salud 'sanos' cada 10 s (anillo, motor y vía rápida medidos; ninguna unidad reiniciada)."""
    out, t = [], t0
    while t < t1:
        out.append({"desde": t, "hasta": t + paso, "reinicios": [],
                    "anillo": {"ok": True, "salto_max_s": 5, "motivo": None},
                    "motor": {"ok": True, "retraso_pcap_s": 3.0, "duracion_s": 2.0},
                    "via_rapida": {"ok": True, "paquetes_tcp": 100, "antiguedad_s": 0.4, "bytes_pendientes": 0},
                    "unidades": {"ppi-motor": {"ok": True, "reinicio_o_parada": False}}})
        t += paso
    return out


def tcpdump_log(t0: float, t1: float, pid: int = 777, cada: float = 30.0, descartes: int = 0) -> str:
    """Líneas del journal (short-iso-precise) con las estadísticas SIGUSR1 de tcpdump."""
    out, t, n = [], t0, 0
    while t <= t1:
        n += 1000
        when = dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "+0000"
        out.append(f"{when} sensor1 tcpdump[{pid}]: {n} packets captured, {n} packets received by filter, "
                   f"{descartes} packets dropped by kernel")
        t += cada
    return "\n".join(out) + "\n"


def decision(ip: str, w: float, score, decision_="PERMIT") -> dict:
    return {"event": "decision", "logged_at": w + 5, "entity_ip": ip, "window_end_utc": iso(w),
            "decision": decision_, "packet_count_10s": 10, "score": score, "detector_name": "if_limpio_2026_10",
            "umbral": U05}


def motor_log(t0: float, t1: float, ips=IPS) -> str:
    """Una decisión por entidad y por ventana de 10 s; la entidad i marca IF_0.05 cada (i+2)-ésima ventana."""
    regs, w, k = [], t0, 0
    while w <= t1:
        for i, ip in enumerate(ips):
            alerta = (k % (i + 2) == 0)
            regs.append(decision(ip, w, -0.60 if alerta else -0.40))
        w += 10.0
        k += 1
    return "\n".join(json.dumps(r) for r in regs) + "\n"


def config(tmp: Path) -> Path:
    p = tmp / "config.json"
    p.write_text(json.dumps({"umbrales": {"0.05": U05, "0.03": U03, "0.01": U01},
                             "poblacion": {"excepciones_respuesta": [], "exclusiones_poblacion": []}}))
    return p
