"""Guarda evidencia de solo lectura y rutas completas del cierre de pendientes."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT.parent / "producto-as-deployed"
OUT = Path(__file__).resolve().parent


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def main():
    remote = (
        "ssh -o BatchMode=yes -o ConnectTimeout=8 -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 "
        "'date -u; systemctl is-active ppi-motor ppi-dashboard ppi-publicar-feed.timer; "
        "sha256sum /home/m4rk/cyberflow/artifacts/preliminar/limpio-2026-10/if_limpio_2026_10_desplegable.joblib; "
        "systemctl show ppi-motor ppi-dashboard -p ExecStart; "
        "systemctl show ppi-publicar-feed.timer -p TimersCalendar'"
    )
    sensor = run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
                  "gadmin@10.10.10.30", remote], ROOT)
    sensor_path = OUT / "VERIFICACION-SENSOR-2026-10-23.txt"
    sensor_path.write_text(sensor, encoding="utf-8")
    changed = set()
    for repo, base in ((PRODUCT, "1eca484"), (ROOT, "HEAD")):
        names = run(["git", "diff", "--name-only", base], repo).splitlines()
        names += run(["git", "ls-files", "--others", "--exclude-standard"], repo).splitlines()
        changed.update((repo / name).resolve() for name in names)
    changed.add(Path(__file__).resolve())
    files = [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted(changed) if p.is_file()
             and p.name != "MANIFIESTO-CIERRE-PENDIENTES-2026-10-23.json"]
    payload = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "product_commit": run(["git", "rev-parse", "HEAD"], PRODUCT).strip(),
        "product_ci": json.loads(run(["gh", "run", "list", "--branch", "main", "--limit", "1",
                                      "--json", "databaseId,headSha,status,conclusion,url"], PRODUCT)),
        "sensor_read_only": str(sensor_path),
        "files": files,
        "not_closed": ["campana final N>=3", "Nikto completo", "tiempos t0-t5",
                       "QA visual en Sensor1 por rol", "validacion externa", "articulo completo"],
    }
    manifest = OUT / "MANIFIESTO-CIERRE-PENDIENTES-2026-10-23.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(sensor)
    print(manifest)


if __name__ == "__main__":
    main()
