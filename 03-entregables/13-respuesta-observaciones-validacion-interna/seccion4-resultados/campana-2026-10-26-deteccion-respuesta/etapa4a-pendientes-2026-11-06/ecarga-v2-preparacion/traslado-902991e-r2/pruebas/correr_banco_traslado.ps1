param([string]$Version = "r2", [string]$Usuario = "65534:65534", [string]$Bundle = "", [string]$Filtro = "", [string]$Salida = "", [string]$Tb = "line")
# [LAPTOP PowerShell] Banco aislado de los guiones de traslado: contenedor efímero, SIN RED (--network none), carpetas
# montadas solo lectura, /tmp y /sim en tmpfs. ssh y scp son dobles: no se conecta con el laboratorio.
# -Version r2 | anterior   -Bundle: `git bundle` de la rama del producto (git bundle create X recuperacion/etapa4a-pendientes-20261106)
$T = Split-Path -Parent $PSScriptRoot                                   # traslado-902991e-r2
$E = Split-Path -Parent (Split-Path -Parent $T)                          # etapa4a-pendientes-2026-11-06
$Ant = Join-Path $E "evidencia\13-correccion-s14"
if (-not $Bundle) { throw "Falta -Bundle" }
$a = @("run", "--rm", "--network", "none", "--user", $Usuario, "--tmpfs", "/tmp:exec,mode=1777", "--tmpfs", "/sim:exec,mode=1777",
  "-e", "HOME=/sim", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "TRASLADO_VERSION=$Version", "-e", "DIR_R2=/t",
  "-e", "DIR_ANTERIOR=/anterior", "-e", "PRODUCTO_BUNDLE=/b/producto.bundle",
  "-v", "${T}:/t:ro", "-v", "${Ant}:/anterior:ro", "-v", "${Bundle}:/b/producto.bundle:ro", "-w", "/t/pruebas")
$cmd = "python3 -m pytest -p no:cacheprovider -v -rfE --tb=$Tb --basetemp=/sim/bt test_traslado.py"
if ($Filtro) { $cmd += " -k '$Filtro'" }
$a += @("cyberflow-etapa3-banco:1", "bash", "-c", "$cmd 2>&1; echo RC_PYTEST=`$?")
if ($Salida) { & docker @a | Tee-Object -FilePath $Salida } else { & docker @a }
