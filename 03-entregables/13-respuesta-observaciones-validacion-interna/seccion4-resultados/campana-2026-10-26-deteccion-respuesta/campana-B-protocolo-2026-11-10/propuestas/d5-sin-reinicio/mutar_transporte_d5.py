#!/usr/bin/env python3
"""Mutaciones del transporte distribuido (sensor_control_d5.py y transporte_bastion.py): cada una debe hacer fallar alguna prueba de test_transporte_d5.py (root, contenedor)."""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

AQUI = pathlib.Path(__file__).resolve().parent
S, B = "sensor_control_d5.py", "transporte_bastion.py"
MUT = [
    (S, "        if os.path.exists(reg):\n            return {\"ok\": True, \"estado\": \"ya_recibida\"", "        if False:\n            return {\"ok\": True, \"estado\": \"ya_recibida\""),
    (S, "        if os.path.exists(cfg.control):\n            return {\"ok\": False, \"estado\": \"pendiente_previa\"", "        if False:\n            return {\"ok\": False, \"estado\": \"pendiente_previa\""),
    (S, "    if n == \"solicitar\" and len(r) == 4 and r[0] == \"--id\" and r[2] == \"--origen\" and ID_RE.match(r[1]) and r[3] == ORIGEN:", "    if n == \"solicitar\" and len(r) == 4 and r[0] == \"--id\" and r[2] == \"--origen\" and ID_RE.match(r[1]):"),
    (S, "        if ctl and ctl.get(\"id\") == id_:\n            try:", "        if ctl:\n            try:"),
    (S, "    if reg.get(\"cancelada_en\"):", "    if False:"),
    (S, "    if n in (\"resultado\", \"cancelar\") and len(r) == 2 and r[0] == \"--id\" and ID_RE.match(r[1]):", "    if n in (\"resultado\", \"cancelar\") and len(r) >= 2 and r[0] == \"--id\" and ID_RE.match(r[1]):"),
    (B, "        if p is None:\n            id_ = uuid.uuid4().hex", "        if True:\n            id_ = uuid.uuid4().hex"),
    (B, "            _escribir(self.p_pend, {\"id\": id_, \"t\": self.ahora(), \"origen\": origen})   # ANTES de la primera orden remota", "            pass"),
    (B, "                    return self._fallo(id_, \"sin_transporte\", evid)                         # el pendiente se CONSERVA", "                    self._archivar(id_, {\"estado\": \"sin_transporte\"})\n                    return self._fallo(id_, \"sin_transporte\", evid)"),
    (B, "                return self._fallo(id_, \"desconocida_en_sensor\", evid)", "                self._archivar(id_, r)\n                return self._fallo(id_, \"desconocida_en_sensor\", evid)"),
    (B, "        if not str(quien).strip() or not str(motivo).strip():\n            raise ValueError(\"descartar un pendiente", "        if False:\n            raise ValueError(\"descartar un pendiente"),
    (B, "        self._log({\"evento\": \"pendiente_descartado_manual\"", "        self._log({\"evento\": \"x\""),
]


def main():
    vivos = []
    for i, (f, a, b) in enumerate(MUT):
        src = (AQUI / f).read_text(encoding="utf-8")
        if src.count(a) < 1:
            print(f"M{i:02d} NO APLICA ({f}): {a[:60]!r}")
            vivos.append(i)
            continue
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            for g in AQUI.glob("*.py"):
                shutil.copy(g, t / g.name)
            (t / f).write_text(src.replace(a, b, 1), encoding="utf-8")
            os.chmod(t, 0o755)
            for g in t.iterdir():
                os.chmod(g, 0o755)
            rc = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(t / "test_transporte_d5.py")], capture_output=True, cwd=t).returncode
        print(f"M{i:02d} {'MUERTA' if rc else 'VIVA  '} {f}: {a.strip()[:55]!r}")
        if not rc:
            vivos.append(i)
    print(f"{len(MUT) - len(vivos)}/{len(MUT)} muertas; vivas: {vivos}")
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(main())
