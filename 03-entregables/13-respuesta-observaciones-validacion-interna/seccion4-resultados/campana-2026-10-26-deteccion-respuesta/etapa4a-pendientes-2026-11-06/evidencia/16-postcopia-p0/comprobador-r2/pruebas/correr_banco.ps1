param([string]$Usuario = "65534:65534", [string]$Bundle = "", [string]$Filtro = "", [string]$Salida = "")
# [LAPTOP PowerShell] Banco aislado del comprobador post-copia r2: contenedor efímero SIN RED (--network none), carpetas
# de solo lectura, /tmp en tmpfs. ssh es un doble: no se conecta con el laboratorio.
# -Bundle: git bundle de la rama del producto (contiene 902991e).
$C = Split-Path -Parent $PSScriptRoot                                   # comprobador-r2
$R1 = Join-Path (Split-Path -Parent (Split-Path -Parent $C)) "15-traslado-902991e"
if (-not $Bundle) { throw "Falta -Bundle" }
$a = @("run", "--rm", "--network", "none", "--user", $Usuario, "--tmpfs", "/tmp:exec,mode=1777",
  "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "DIR_R2=/c", "-e", "DIR_R1=/r1", "-e", "PRODUCTO_BUNDLE=/b/producto.bundle",
  "-v", "${C}:/c:ro", "-v", "${R1}:/r1:ro", "-v", "${Bundle}:/b/producto.bundle:ro", "-w", "/c/pruebas")
$cmd = "python3 -m pytest -p no:cacheprovider -v -rfE --tb=short --basetemp=/tmp/bt test_post_copia.py"
if ($Filtro) { $cmd += " -k '$Filtro'" }
$a += @("cyberflow-etapa3-banco:1", "bash", "-c", "$cmd 2>&1; echo RC_PYTEST=`$?")
if ($Salida) { & docker @a | Tee-Object -FilePath $Salida } else { & docker @a }
