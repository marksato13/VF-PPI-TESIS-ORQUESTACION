# [LAPTOP PowerShell 7] Reproduce, sin red, la causa del «bash: line 19: $'\r': command not found» de
# ../../15-traslado-902991e/post-copia-3-hosts.txt. Uso: & .\reproducir_causa.ps1 > causa-cr.txt
$f = Join-Path $PSScriptRoot "..\..\15-traslado-902991e\post_copia_host.sh"
$bash = "C:\Program Files\Git\bin\bash.exe"
$b = [IO.File]::ReadAllBytes($f)
"PowerShell $($PSVersionTable.PSVersion)"
"fichero r1: bytes=$($b.Length) CR=$(@($b | Where-Object { $_ -eq 13 }).Count) LF=$(@($b | Where-Object { $_ -eq 10 }).Count) ultimo_byte=$($b[-1])"
"1) Get-Content -Raw | bash (primer envío): bytes recibidos = " + (Get-Content $f -Raw | & $bash --noprofile --norc -c 'wc -c')
"   cola recibida: " + ((Get-Content $f -Raw | & $bash --noprofile --norc -c 'od -An -c | tail -1') -join ' ')
"2) -replace CR antes de la tubería (envío publicado): bytes recibidos = " + ((Get-Content $f -Raw) -replace "`r", "" | & $bash --noprofile --norc -c 'wc -c')
"   cola recibida: " + (((Get-Content $f -Raw) -replace "`r", "" | & $bash --noprofile --norc -c 'od -An -c | tail -1') -join ' ')
"3) lo que bash ejecuta con esa cola: la línea 19 es solo «\r» -> «\$'\r': command not found» (banco: test_regresion_r1_con_el_transporte_de_powershell)"
"4) redirección de bash (bash -s < fichero): bytes recibidos = " + (& $bash --noprofile --norc -c 'wc -c < "$1"' _ ((Resolve-Path $f).Path -replace '\\', '/' -replace '^C:', '/c'))
