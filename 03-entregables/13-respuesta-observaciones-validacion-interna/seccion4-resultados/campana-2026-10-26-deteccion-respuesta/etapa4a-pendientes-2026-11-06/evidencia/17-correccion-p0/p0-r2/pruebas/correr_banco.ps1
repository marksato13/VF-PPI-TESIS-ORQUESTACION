param([string]$Usuario = "65534:65534", [string]$Producto = "", [string]$Filtro = "", [string]$Salida = "")
# [LAPTOP PowerShell] Banco aislado de P0 r2: contenedor efímero SIN RED (--network none), carpetas en solo lectura y
# /tmp en tmpfs. ssh es un doble: no conecta con el laboratorio.
#   /c   = p0-r2 (este banco)
#   /p16 = ../16-postcopia-p0 (manejador antiguo y salida real de precheck del 06-nov)
#   /r   = árbol del producto en la rama con sensor1_muestreadores.sh 2026-11-06.3 (-Producto)
$C = Split-Path -Parent $PSScriptRoot                                  # p0-r2
$P16 = Join-Path (Split-Path -Parent (Split-Path -Parent $C)) "16-postcopia-p0"
if (-not $Producto) { throw "Falta -Producto (árbol del producto con la 2026-11-06.3)" }
$a = @("run", "--rm", "--network", "none", "--user", $Usuario, "--tmpfs", "/tmp:exec,mode=1777",
  "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "DIR_P16=/p16", "-e", "PRODUCTO=/r",
  "-v", "${C}:/c:ro", "-v", "${P16}:/p16:ro", "-v", "${Producto}:/r:ro", "-w", "/c/pruebas")
$cmd = "python3 -m pytest -p no:cacheprovider -v -rfEs --tb=short --basetemp=/tmp/bt test_p0_r2.py"
if ($Filtro) { $cmd += " -k '$Filtro'" }
$a += @("cyberflow-etapa3-banco:1", "bash", "-c", "$cmd 2>&1; echo RC_PYTEST=`$?")
if ($Salida) { & docker @a | Tee-Object -FilePath $Salida } else { & docker @a }
