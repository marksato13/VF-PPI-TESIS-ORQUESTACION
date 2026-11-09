$s = "C:\Users\markp\AppData\Local\Temp\claude\f17b3819211dc686\51c74eee-a71d-4dd3-9ea4-b614ec3c2579\scratchpad"
$D = "$s\db3_4b\datos"; $O = "$s\db3_4b\salida"
if (Test-Path $O) { [IO.Directory]::Delete($O, $true) }
New-Item -ItemType Directory $O | Out-Null
# ahora_epoch: el mismo instante con el que s50 midió Suricata (control-4b.json), para que el resultado sea reproducible
$ahora = (Get-Content "$D\analisis\control-4b.json" -Raw | ConvertFrom-Json).fuentes.suricata_eve.ahora_epoch
"ahora_epoch = $ahora"
docker run --rm --network none --user 65534:65534 --tmpfs /tmp:exec,mode=1777 -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 `
  -v "$s\e4b\herr:/herr:ro" -v "${D}:/d:ro" -v "${O}:/out" -w /herr cyberflow-etapa3-banco:1 `
  python3 -I /herr/analisis_db3.py --motor /d/copias/motor_decision.log --inventario /d/replay/motor_decision.log --config /herr/config-campana-4c.json `
  --desde 2026-11-08T18:00:00Z --hasta 2026-11-09T02:00:00Z --salud-captura /herr/salud_captura.py --incrementos /d/analisis/incrementos.jsonl `
  --tcpdump-anillo /d/salud/tcpdump-anillo.log --suricata-eve /d/copias/eve-segmento.json --ahora $ahora --salida /out/db3-4b.json `
  > "$O\db3-4b.stdout" 2> "$O\db3-4b.stderr"
"rc=$LASTEXITCODE"; Get-Content "$O\db3-4b.stdout"; "--- stderr:"; Get-Content "$O\db3-4b.stderr" -TotalCount 20
