# [LAPTOP PowerShell] Pruebas de guardia.py y de las herramientas de evaluación en el banco Docker aislado
# (sin red, usuario 65534, todo montado en solo lectura). Los datos del 06-nov solo sirven para probar herramientas.
$s = "C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\e4x"
$e = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\etapa4a-pendientes-2026-11-06\evidencia\06-observacion"
$p = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-recuperacion"
$cmd = @'
cd /tmp
echo "## banco $(python3 --version) usuario $(id -u) red none; evaluador sha256 $(sha256sum /prod/deploy/etapa4/sensor1/evaluar_ecarga.py | cut -c1-64)"
echo "## guiones (prep) y evaluacion: SHA256SUMS"
(cd /e4x/prep && sha256sum -c --strict SHA256SUMS); (cd /e4x/eval && sha256sum -c --strict SHA256SUMS)
echo "## test_guardia.py"
python3 -m pytest -q -p no:cacheprovider --rootdir=/tmp /e4x/prep/test_guardia.py; echo "rc=$?"
echo "## test_evaluacion.py"
python3 -m pytest -q -p no:cacheprovider --rootdir=/tmp /e4x/eval/test_evaluacion.py; echo "rc=$?"
'@
docker run --rm --network none --user 65534:65534 -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 `
  -v "${s}:/e4x:ro" -v "${e}:/obs06:ro" -v "${p}:/prod:ro" `
  -e OBS06=/obs06 -e EVALUADOR=/prod/deploy/etapa4/sensor1/evaluar_ecarga.py -e MUESTRAS_06NOV=/obs06/bastion/muestras.txt `
  cyberflow-etapa3-banco:1 sh -c $cmd 2>&1 | Out-File -Encoding utf8 "$s\pruebas-banco.txt"
Get-Content "$s\pruebas-banco.txt"
