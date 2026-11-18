$sc="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad"
$log="C:\Users\markp\Desktop\PY-MEGATRON\PY - PERSONAL\TESIS\CYBERFLOW\orquestacion-limpio\03-entregables\13-respuesta-observaciones-validacion-interna\seccion4-resultados\campana-2026-10-26-deteccion-respuesta\campana-B-protocolo-2026-11-10\corrida-2026-11-11\monitor.log"
$fallos=0
while($true){
  $o = (& "$sc\run_react.ps1" -Hop local -Script mon2.sh -T 50 | Out-String).Trim()
  if($o -notmatch 'ALARMA'){ $fallos++; Add-Content $log "$(Get-Date -AsUTC -Format s)Z LECTURA FALLIDA ($fallos): $o"; if($fallos -ge 4){ Add-Content $log "ALARMA: monitor sin lectura"; "ALARMA monitor sin lectura"; break } }
  else { $fallos=0; Add-Content $log $o; if($o -notmatch 'ALARMA \[\]'){ "ALARMA: $o"; break } }
  Start-Sleep 150
}
