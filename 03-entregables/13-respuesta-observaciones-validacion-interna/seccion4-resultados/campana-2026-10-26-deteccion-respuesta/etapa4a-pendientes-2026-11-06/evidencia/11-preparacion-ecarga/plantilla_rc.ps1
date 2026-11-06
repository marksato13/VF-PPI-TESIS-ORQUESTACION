# [LAPTOP PowerShell] Comprueba que el evaluador publicado (ae2900e, 2026-11-06.4) rechaza la plantilla sin resultados.
$B = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\etapa4a-pendientes-2026-11-06\ecarga-v2-preparacion"
$EV = "C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\producto-recuperacion\deploy\etapa4\sensor1\evaluar_ecarga.py"
$s = "C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\e4x"
$o = @()
$o += "## evaluador sha256 $((Get-FileHash $EV -Algorithm SHA256).Hash.ToLower())"
$o += "## 1) plantilla tal cual (con el campo _PLANTILLA_SIN_RESULTADOS)"
$o += (python -I $EV veredicto --entrada "$B\ENTRADA-VEREDICTO.PLANTILLA-SIN-RESULTADOS.json" 2>&1)
$o += "rc=$LASTEXITCODE"
$j = Get-Content "$B\ENTRADA-VEREDICTO.PLANTILLA-SIN-RESULTADOS.json" -Raw | ConvertFrom-Json
$j.PSObject.Properties.Remove('_PLANTILLA_SIN_RESULTADOS')
$t = "$s\plantilla-sin-marca.json"
[IO.File]::WriteAllText($t, ($j | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding $false))
$o += "## 2) la misma plantilla SIN el campo de marca (todo null): tampoco debe dar veredicto"
$o += (python -I $EV veredicto --entrada $t 2>&1)
$o += "rc=$LASTEXITCODE"
$o | Out-File -Encoding utf8 "$s\plantilla-rc.txt"; $o
