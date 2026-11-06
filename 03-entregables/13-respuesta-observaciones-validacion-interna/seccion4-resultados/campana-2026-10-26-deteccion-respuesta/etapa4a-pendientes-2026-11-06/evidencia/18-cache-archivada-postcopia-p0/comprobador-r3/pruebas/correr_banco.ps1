param([string]$Usuario = "65534:65534", [string]$Bundle = "", [string]$I18n = "", [string]$Filtro = "", [string]$Salida = "")
# [LAPTOP PowerShell] Banco aislado del comprobador post-copia r3: contenedor efímero SIN RED (--network none), carpetas
# de solo lectura, /tmp en tmpfs. ssh es un doble: no se conecta con el laboratorio.
# -Bundle: git bundle de la rama del producto (contiene 902991e).
# -I18n:   fuentes de locales de glibc (locales/ y charmaps/) para compilar es_PE.UTF-8 y en_US.UTF-8 sin root.
# Monta también la r2 (conservada, ../../16-postcopia-p0/comprobador-r2) para las pruebas de regresión.
$C = Split-Path -Parent $PSScriptRoot                                   # comprobador-r3
$EV = Split-Path -Parent (Split-Path -Parent $C)                        # evidencia
$R2 = Join-Path $EV "16-postcopia-p0\comprobador-r2"
$R1 = Join-Path $EV "15-traslado-902991e"
if (-not $Bundle) { throw "Falta -Bundle" }
if (-not $I18n) { throw "Falta -I18n" }
$a = @("run", "--rm", "--network", "none", "--user", $Usuario, "--tmpfs", "/tmp:exec,mode=1777",
  "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "DIR_R3=/c", "-e", "DIR_R2=/r2", "-e", "DIR_R1=/r1",
  "-e", "I18N=/i18n", "-e", "PRODUCTO_BUNDLE=/b/producto.bundle",
  "-v", "${C}:/c:ro", "-v", "${R2}:/r2:ro", "-v", "${R1}:/r1:ro", "-v", "${Bundle}:/b/producto.bundle:ro",
  "-v", "${I18n}:/i18n:ro", "-w", "/c/pruebas")
$cmd = "python3 -m pytest -p no:cacheprovider -v -rfE --tb=short --basetemp=/tmp/bt test_post_copia_r3.py"
if ($Filtro) { $cmd += " -k '$Filtro'" }
$a += @("cyberflow-etapa3-banco:1", "bash", "-c", "$cmd 2>&1; echo RC_PYTEST=`$?")
if ($Salida) { & docker @a | Tee-Object -FilePath $Salida } else { & docker @a }
