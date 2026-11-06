# [SENSOR1 m4rk] SOLO LECTURA: ¿la ruta del verificador (comprobar_importaciones.sh:29, «$PY motor_decision.py --help»
# sin -B) ha escrito caché en ~/cyberflow-e4/ec78ca5? Lista los .pyc con su nacimiento y modificación, y el entorno
# de la unidad ppi-motor. No ejecuta Python ni importa nada.
D=~/cyberflow-e4/ec78ca5
echo "== $(hostname) $(id -un) $(date -u +%FT%TZ)"
echo "-- entorno de ppi-motor (¿PYTHONDONTWRITEBYTECODE?):"; systemctl show -p Environment -p ExecMainStartTimestamp ppi-motor
echo "-- .pyc bajo $D (nacido | modificado | ruta), ordenados por nacimiento:"
find "$D" -name '*.pyc' -printf '%B+ | %T+ | %p\n' 2>&1 | sort | sed "s|$D/||"
echo "-- total .pyc: $(find "$D" -name '*.pyc' 2>/dev/null | wc -l); directorios __pycache__: $(find "$D" -type d -name __pycache__ 2>/dev/null | wc -l)"
echo "-- .pyc nacidos o modificados el 06-nov a partir de las 19:00Z:"
find "$D" -name '*.pyc' -newermt '2026-11-06 19:00:00 UTC' -printf '%T+ %p\n' 2>&1 | sort | sed "s|$D/||"
echo "-- ¿SHA256SUMS de ec78ca5 lista .pyc? $(grep -c '\.pyc' "$D/SHA256SUMS" 2>&1)"
exit 0
