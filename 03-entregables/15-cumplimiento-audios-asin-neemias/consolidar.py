#!/usr/bin/env python3
"""Consolida solo los entregables de esta delegación; no cambia fuentes ni código."""
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCES = (
    ("Asin", "Agente de instrumento", "01-asin/CUMPLIMIENTO-ASIN.csv", {
        "observacion": "tarea", "fuente_audio": "fuente_temporal", "estado_avance": "estado_actual_comprobado",
        "avance": "entregable_preparado", "dependencia": "dependencia_humana", "criterio_cierre": "criterio_de_cierre"}),
    ("Neemias", "Agente de métricas", "02-metricas/CUMPLIMIENTO-METRICAS.csv", {
        "observacion": "observacion", "fuente_audio": "fuente_temporal", "estado_avance": "estado_comprobado",
        "avance": "avance_concreto", "dependencia": "dependencia", "criterio_cierre": "criterio_cierre"}),
    ("Neemias", "Agente de metodología", "03-metodologia/CUMPLIMIENTO-METODOLOGIA.csv", {
        "observacion": "subtarea", "fuente_audio": "fuente_audio", "estado_avance": "estado_actual",
        "avance": "avance_concreto", "dependencia": "dependencia", "criterio_cierre": "criterio_cierre"}),
    ("Neemias", "Agente de validación", "04-validacion/CUMPLIMIENTO-VALIDACION.csv", {
        "observacion": "solicitud", "fuente_audio": "tiempo_original", "estado_avance": "estado",
        "avance": "avance_concreto", "dependencia": "dependencias", "criterio_cierre": "criterio_cierre"}),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path, value):
    path.write_text(value, encoding="utf-8", newline="\n")


def save_json(path, data):
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    tasks = []
    source_hashes = {}
    for origin, agent, relative, columns in SOURCES:
        path = HERE / relative
        source_hashes[str(path)] = digest(path)
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            assert None not in reader.fieldnames
            for row in reader:
                assert None not in row and all(row.get(v, "").strip() for v in columns.values()), relative
                task = {"id": row["id"], "origen": origin,
                        "nivel": "subtarea" if "." in row["id"] else "observacion_primaria",
                        "agente_encargado": agent, **{k: row[v] for k, v in columns.items()},
                        "csv_detalle": str(path),
                        "cierre_humano_o_aplicacion": "No acreditado por preparar este material"}
                tasks.append(task)
    ids = [row["id"] for row in tasks]
    assert len(ids) == len(set(ids)) == 24
    expected = {f"A-{n:02}" for n in range(1, 7)} | {f"N-{n:02}" for n in range(1, 10)}
    assert {r["id"] for r in tasks if r["nivel"] == "observacion_primaria"} == expected
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=list(tasks[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(tasks)
    write_text(HERE / "TAREAS.csv", csv_buffer.getvalue())
    save_json(HERE / "TAREAS.json", {"observaciones_primarias": 15, "subtareas": 9, "tasks": tasks,
                                   "assignment_note": "Agentes y prioridades son propuestas del coordinador; no asignaciones del audio"})
    # Comprobar las referencias locales de los archivos preparados sin afirmar
    # que sus autores/asesores los hayan aprobado o que estén desplegados.
    refs = set()
    for path in HERE.rglob("*.md"):
        if path.name == "README.md":
            continue
        import re
        for reference in re.findall(r"`(C:\\[^`\n]+)`", path.read_text(encoding="utf-8")):
            candidate = Path(reference)
            if candidate.is_file():
                refs.add(candidate)
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
    files = sorted(p for p in HERE.rglob("*") if p.is_file() and p.name not in ("MANIFIESTO.json", "README.md") and "__pycache__" not in p.parts)
    index = ["# Paquete de cumplimiento de audios", "", "Cuatro frentes delegados, doce entregables de agentes y una lista maestra de 15 observaciones primarias más nueve subtareas.",
             "Leer primero PLAN-MAESTRO.md. Son insumos preparados; no se acredita validación humana ni aplicación editorial por existir los archivos.",
             "Todo queda local, sin commit/push en esta tarea. Los materiales anteriores y el trabajo GUI/TAM concurrente se conservan.", "", "## Archivos (rutas absolutas)", ""]
    index += [f"- `{p}`" for p in sorted(files + [HERE / "README.md", HERE / "MANIFIESTO.json"])]
    write_text(HERE / "README.md", "\n".join(index) + "\n")
    files.append(HERE / "README.md")
    save_json(HERE / "MANIFIESTO.json", {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "documental_head": head,
        "primary_tasks": 15, "subtasks": 9, "agents_executed": 4,
        "agent_outputs": 12, "source_task_csv_sha256": source_hashes,
        "referenced_local_inputs_sha256": {str(p): digest(p) for p in sorted(refs)},
        "outputs_sha256": {str(p.relative_to(HERE)).replace("\\", "/"): digest(p) for p in sorted(files)},
        "human_validation_completed": False, "word_modified": False, "deployment_modified": False,
        "messages_sent": False, "committed_or_pushed_by_this_task": False,
        "independent_review": "Interrumpida; no se declara aprobada", "self_hash": "Omitido para evitar autorreferencia"})
    print("VERIFICADO: cuatro CSV, 24 IDs únicos, 15 observaciones primarias y nueve subtareas.")
    for path in sorted(files + [HERE / "MANIFIESTO.json"]):
        print(path)


if __name__ == "__main__":
    main()
