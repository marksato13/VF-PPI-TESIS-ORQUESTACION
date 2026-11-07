param([string]$Usuario = "65534:65534", [string]$Producto = "", [string]$Filtro = "", [string]$Salida = "", [string]$BloqueSensor1 = "")
# [LAPTOP PowerShell] Banco aislado de P0 r3: contenedor efímero SIN RED (--network none), carpetas en solo lectura y
# /tmp en tmpfs. ssh es un doble: no conecta con el laboratorio. Los procesos «muestreadores» son del contenedor.
#   /c   = p0-r3 (este banco)
#   /p16 = ../16-postcopia-p0 (manejador antiguo y salida real de precheck del 06-nov)
#   /p17 = ../17-correccion-p0 (P0 r2 conservado: sensor1_r2.sh para la reproducción y las regresiones)
#   /r   = árbol del producto con sensor1_muestreadores.sh 2026-11-06.4 (-Producto)
#   tmpfs en /var/lib/ppi-motor-capture y /var/log/suricata (anillo y eve.json del «Sensor1 sano» simulado)
# -BloqueSensor1 /p17/p0-r2/bloques/sensor1_r2.sh: las pruebas «regresion_p11» con el bloque ANTERIOR (deben fallar).
$C = Split-Path -Parent $PSScriptRoot                                  # p0-r3
$EV = Split-Path -Parent (Split-Path -Parent $C)                       # evidencia
$P16 = Join-Path $EV "16-postcopia-p0"
$P17 = Join-Path $EV "17-correccion-p0"
if (-not $Producto) { throw "Falta -Producto (árbol del producto con la 2026-11-06.4)" }
$a = @("run", "--rm", "--network", "none", "--user", $Usuario, "--tmpfs", "/tmp:exec,mode=1777",
  "--tmpfs", "/var/lib/ppi-motor-capture:mode=1777", "--tmpfs", "/var/log/suricata:mode=1777",
  "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "DIR_P16=/p16", "-e", "DIR_P17=/p17", "-e", "PRODUCTO=/r",
  "-v", "${C}:/c:ro", "-v", "${P16}:/p16:ro", "-v", "${P17}:/p17:ro", "-v", "${Producto}:/r:ro", "-w", "/c/pruebas")
if ($BloqueSensor1) { $a += @("-e", "BLOQUE_SENSOR1=$BloqueSensor1") }
$cmd = "python3 -m pytest -p no:cacheprovider -v -rfEs --tb=short --basetemp=/tmp/bt test_p0_r3.py"
if ($Filtro) { $cmd += " -k '$Filtro'" }
$a += @("cyberflow-etapa3-banco:1", "bash", "-c", "$cmd 2>&1; echo RC_PYTEST=`$?")
if ($Salida) { & docker @a | Tee-Object -FilePath $Salida } else { & docker @a }
