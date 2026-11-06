param([string]$Modo = "nuevo", [string]$Usuario = "65534:65534", [string]$Filtro = "", [string]$Salida = "")
$P = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-recuperacion"
$E = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\etapa4a-pendientes-2026-11-06"
$args2 = @("run", "--rm", "--network", "none", "--user", $Usuario, "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
  "-e", "OBS06=/obs", "-v", "${P}:/repo:ro", "-v", "$E\evidencia\06-observacion:/obs:ro",
  "-v", "$E\ecarga-v2-preparacion\guiones-c7f24510:/old/prep:ro", "-v", "$E\ecarga-v2-preparacion\evaluacion-e83f4be6:/old/eval:ro",
  "-w", "/repo")
if ($Modo -eq "anterior") { $args2 += @("-e", "ECARGA_DIRS=/old/prep:/old/eval") }
$cmd = "python3 -m pytest -p no:cacheprovider -v -rs --tb=short tests/test_etapa4_ecarga_prep.py"
if ($Filtro) { $cmd += " -k '$Filtro'" }
$args2 += @("cyberflow-etapa3-banco:1", "bash", "-c", "$cmd 2>&1; echo RC_PYTEST=`$?")
if ($Salida) { & docker @args2 | Tee-Object -FilePath $Salida } else { & docker @args2 }
