param([int]$Veces = 6, [int]$Pausa = 60)
$g="C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad\inst4b\guiones"
$b="C:\Program Files\Git\bin\bash.exe"
Set-Location $g
for ($i=0; $i -lt $Veces; $i++) {
  $o = (& $b r4.sh estado_bateria.sh bastion 2>&1 | Where-Object { $_ -match "rondas=" } | Select-Object -Last 1)
  $o -replace "kali: zsh.*", ""
  if ($o -match "cancelar") { "CANCELADA"; break }
  if ($i -lt $Veces-1) { Start-Sleep -Seconds $Pausa }
}
