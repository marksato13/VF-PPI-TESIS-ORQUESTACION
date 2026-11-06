param([string]$Modo = "nuevo", [string]$Usuario = "65534:65534", [string]$Filtro = "", [string]$Salida = "")
# Banco Docker sin red. Modo «nuevo»: deploy/etapa4/ecarga del árbol de trabajo. Modo «a12deae»: la versión publicada
# a12deae (git archive), para las regresiones. Modo «c7f24510»: la preparación anterior a a12deae.
$P = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-recuperacion"
$Z = "C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\e4z"
$E = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\etapa4a-pendientes-2026-11-06"
$a = @("run", "--rm", "--network", "none", "--user", $Usuario, "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
  "-e", "OBS06=/obs", "-v", "${P}:/repo:ro", "-v", "$E\evidencia\06-observacion:/obs:ro", "-v", "$Z\a12deae:/a12deae:ro",
  "-v", "$E\ecarga-v2-preparacion\guiones-c7f24510:/old/prep:ro", "-v", "$E\ecarga-v2-preparacion\evaluacion-e83f4be6:/old/eval:ro",
  "-w", "/repo")
if ($Modo -eq "a12deae") { $a += @("-e", "ECARGA_DIRS=/a12deae/deploy/etapa4/ecarga") }
if ($Modo -eq "c7f24510") { $a += @("-e", "ECARGA_DIRS=/old/prep:/old/eval") }
$cmd = "python3 -m pytest -p no:cacheprovider -v -rs --tb=short tests/test_etapa4_ecarga_prep.py"
if ($Filtro) { $cmd += " -k '$Filtro'" }
$a += @("cyberflow-etapa3-banco:1", "bash", "-c", "$cmd 2>&1; echo RC_PYTEST=`$?")
if ($Salida) { & docker @a | Tee-Object -FilePath $Salida } else { & docker @a }
