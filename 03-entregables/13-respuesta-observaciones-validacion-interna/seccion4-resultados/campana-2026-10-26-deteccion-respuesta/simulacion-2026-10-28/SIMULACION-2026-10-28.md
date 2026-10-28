# Simulación del generador de la campaña A (2026-10-28, 23:44 UTC)

Revisión final del plan **sin tráfico**. El generador se ejecutó en la Kali **sin `--autorizado`**, en un directorio nuevo
y exclusivo (`/home/adminatacante/cf-simulacion-A-20261028T234452Z`). Ese directorio **no se reutiliza** para la ejecución
real: `marcas.jsonl` se abre en modo anexar y mezclaría la simulación con la campaña.

No se inició el control normal ni la campaña, y no se cambió ningún servicio ni configuración.

## Versiones usadas (Kali = repositorio en dd7bb0f)

| Fichero | sha256 |
|---|---|
| `scripts/generar_campana.py` | `c586d813472d5853ae43fe512b5a53d22654699ace10894e43f57b3ddc4b171b` |
| `scripts/esquema_campana.py` | `e762e60421b4721b1e8ce32549049ae10c7e86596b0fbd37f9a35517ab904144` |
| `escenarios/escenarios.json` | `67798012cbd306e9c06ebccf5ec293c7d9db12951d93119f739c3f86a83c64ec` |

## Resultado

- `rc=0`, duración **0,107 s**: no hubo calentamiento, contexto ni observación (esperas que solo corren con
  `--autorizado`). Cabecera: «SIMULACIÓN (no lanza tráfico) · 25 episodios · calentamiento 60 s · contexto previo 120 s ·
  observación 90 s».
- `config-efectiva.json`: semilla 20261026, 5 repeticiones, `tiempos_s` = {60, 120, 90}, `_autorizado: false`.
- `marcas.jsonl`: `campana_inicio`, **25 `inicio`** (5 por escenario), **0 `fin`** y `campana_fin` «completa». En simulación
  `correr_episodio` vuelve antes de `subprocess.Popen`, por eso no hay `fin` ni salidas.
- `salidas/` quedó vacío (sin `.out`/`.err`). No se versiona porque git no guarda carpetas vacías.
- `pgrep` de `nmap|hping3|hydra|nikto|slowhttptest|generar_campana|dig |curl ` antes y después: **ninguno**. `strace` no está
  instalado en la Kali; la prueba de que no se lanzó nada son el código (salida antes de `Popen`), la duración de 0,1 s,
  la ausencia de salidas y `pgrep`.
- Validación local con el repositorio: `esquema_campana.validar` sin problemas; el orden de `plan_orden` es **idéntico**
  al de la Kali; los 25 comandos coinciden con `comando_de`, y cada escenario tiene **un único comando**, igual en sus 5
  repeticiones.

## Matriz de escenarios

| Escenario | Comando exacto generado | Origen | Destino | Duración | Concurrencia / tasa | Timeout | Rep. |
|---|---|---|---|---|---|---|---|
| `dns_inusual` | `bash -c 'c=0; fin=$((SECONDS+90)); while [ $SECONDS -lt $fin ]; do dig +time=1 +tries=1 @10.10.10.20 "$(openssl rand -hex 8).lab-ppi" +short >/dev/null 2>&1; c=$((c+1)); sleep 0.4; done; echo "intentos=$c"'` | 10.10.20.30 | 10.10.10.20 UDP/53 | 90 s | 1 bucle, `sleep 0.4` (~2,3 consultas/s) | 150 s | 5 |
| `inundacion_http` | `bash -c 'fin=$((SECONDS+90)); n=8; d=$(mktemp -d); for i in $(seq $n); do ( c=0; while [ $SECONDS -lt $fin ]; do curl -s -o /dev/null --max-time 2 http://10.10.30.10/ ; c=$((c+1)); done; echo $c > "$d/$i" ) & done; wait; echo "intentos=$(cat "$d"/* \| awk '{s+=$1} END{print s+0}')"; rm -rf "$d"'` | 10.10.20.30 | 10.10.30.10 TCP/80 | 90 s | concurrencia fija 8, `--max-time 2` | 150 s | 5 |
| `escaneo_breve` | `nmap -sT -T4 --max-retries 1 -p 1-1000 10.10.30.10` | 10.10.20.30 | 10.10.30.10 TCP 1–1000 | natural | `-T4`, `--max-retries 1` | 180 s | 5 |
| `escaneo_sostenido` | `nmap -sT -T4 --max-retries 0 --max-rate 1500 -p 1-65535 10.10.30.10` | 10.10.20.30 | 10.10.30.10 TCP 1–65535 | natural (≥ ~44 s) | `--max-rate 1500`, `--max-retries 0` | 900 s | 5 |
| `fuerza_bruta_http` | `bash -c 'c=0; fin=$((SECONDS+90)); while [ $SECONDS -lt $fin ]; do curl -s -o /dev/null -w "%{http_code}\n" --max-time 2 -u fake:fake$RANDOM http://10.10.30.10:18081/auth ; c=$((c+1)); done; echo "intentos=$c"'` | 10.10.20.30 | 10.10.30.10:18081/auth | 90 s | 1 bucle secuencial, `--max-time 2` | 150 s | 5 |

Los comandos están copiados literalmente de `marcas.jsonl`. En la tabla, `\|` es el carácter `|` escapado para Markdown.

## Orden simulado (semilla 20261026)

| # | Episodio | # | Episodio | # | Episodio |
|---|---|---|---|---|---|
| 1 | escaneo_sostenido-r2 | 10 | fuerza_bruta_http-r3 | 19 | escaneo_breve-r4 |
| 2 | inundacion_http-r1 | 11 | fuerza_bruta_http-r5 | 20 | escaneo_breve-r3 |
| 3 | dns_inusual-r3 | 12 | dns_inusual-r5 | 21 | dns_inusual-r4 |
| 4 | inundacion_http-r4 | 13 | escaneo_sostenido-r3 | 22 | fuerza_bruta_http-r1 |
| 5 | inundacion_http-r2 | 14 | dns_inusual-r2 | 23 | inundacion_http-r5 |
| 6 | inundacion_http-r3 | 15 | fuerza_bruta_http-r2 | 24 | escaneo_breve-r2 |
| 7 | escaneo_sostenido-r4 | 16 | fuerza_bruta_http-r4 | 25 | escaneo_sostenido-r1 |
| 8 | escaneo_sostenido-r5 | 17 | dns_inusual-r1 | | |
| 9 | escaneo_breve-r5 | 18 | escaneo_breve-r1 | | |

## Duración estimada de la ejecución real

- Partes fijas: 60 + 120 s al inicio; 15 episodios de 90 s; 25 observaciones de 90 s; 24 contextos de 120 s. Suman 6660 s.
- Escaneos: entre ~5 × 44 s (sostenido, mínimo por ritmo) y el peor caso de los timeouts, 5 × 180 + 5 × 900 s.
- Total: **~1 h 55 min como mínimo y 3 h 21 min como máximo**. Cabe en la franja de 08:00 a 13:00 UTC (factor horario 1,0).

## Configuraciones comparativas

`config-campana.json` conserva los tres α (0,05 / 0,03 / 0,01) y las siete configuraciones (IF_0.05, IF_0.03, IF_0.01,
HEUR, HIB_0.05, HIB_0.03, HIB_0.01). `analizar.py` recibe un único `--marcas` y un único `--motor`, y calcula las siete
configuraciones sobre las mismas ventanas y puntuaciones. El generador no lee α ni configuraciones: el tráfico es el
mismo para todas. Se ejecutará una sola campaña. El motor en vivo mantiene el umbral desplegado
−0,5693969936322356.

## Ficheros

| Fichero | Contenido |
|---|---|
| `marcas.jsonl` | Marcas de la simulación, tal como salieron de la Kali (sha256 `a1cc3ca0dd05ed54…`) |
| `config-efectiva.json` | Configuración efectiva registrada por el generador (`ce0585f56392448a…`) |
| `stdout.txt`, `stderr.txt` | Salida del generador; `stderr` vacío |
| `sesion-simulacion.txt` | Sesión completa: hashes, `pgrep` antes y después, rc, duración y listado del directorio |

El directorio se copió de la Kali como `cf-simulacion-A-20261028T234452Z.tar` (sha256 `196b654f…`). Se aplanó
aquí porque la ruta anidada superaba el límite de rutas de Windows.
