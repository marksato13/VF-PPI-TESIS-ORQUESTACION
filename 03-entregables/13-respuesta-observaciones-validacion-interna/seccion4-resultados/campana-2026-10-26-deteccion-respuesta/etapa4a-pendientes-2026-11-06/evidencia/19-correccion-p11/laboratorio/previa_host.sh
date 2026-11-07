#!/usr/bin/env bash
# [HOST] Comprobación previa de SOLO LECTURA: ¿hay generadores o muestreadores del ensayo en marcha? No escribe nada.
# 1) Cribado CONSERVADOR por texto en la lista de procesos (clases de caracteres para no coincidir consigo mismo): si
#    encuentra algo, se informa y la comprobación NO es conforme (un falso positivo detiene; nunca aprueba).
# 2) En Sensor1 además: identificación por argv con el código de sensor1_muestreadores.sh 2026-11-06.4 (producto 975e715),
#    sha del código a651f76f6f6d154e8f5809f0ffc43a53aa55776ecb4bb4437956f18160fe2e4c.
# Salida final: RESULTADO <host> rc=<0 ninguno | 1 hay procesos | 3 lectura fallida>
set -u -o pipefail
export LC_ALL=C
N=${N:-?}
echo "INFO $N $(id -un) $(hostname) $(date -u +%FT%TZ)"
l=$(ps -eo pid=,etimes=,args=) || { echo "RESULTADO $N rc=3 ps falló"; exit 3; }
[ -n "$l" ] || { echo "RESULTADO $N rc=3 ps sin salida"; exit 3; }
echo "INFO procesos listados: $(printf '%s\n' "$l" | wc -l)"
m=$(printf '%s\n' "$l" | grep -E '[c]lientes_lab[.]py|[g]eneradores[.]sh|[m]uestreo_bastion[.]sh|[s]alud_captura[.]py muestrear|[m]uestreo_fino[.]py|[o]bs_pcap[.]py|[m]uestreo_s14[.]py|[d]erivar_pcap[.]py'); r=$?
case $r in
  0) printf '%s\n' "$m" | cut -c1-220 | sed 's/^/CRIBADO_PRESENTE /'; rc=1;;
  1) echo "CRIBADO ninguno"; rc=0;;
  *) echo "CRIBADO ERROR grep rc $r"; rc=3;;
esac
if [ "$N" = sensor1 ]; then
  CODIGO=$(cat <<'FIN_CODIGO_PUBLICADO'
import json, os, re, sys

OBJETIVO = ("muestreo_fino.py", "obs_pcap.py", "muestreo_s14.py")
INTERPRETE = re.compile(r"python[0-9.]*\Z")


def muestreador(argv):
    """Nombre del muestreador que ejecuta este argv, o None."""
    if not argv or not INTERPRETE.match(os.path.basename(argv[0])):
        return None
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--":
            i += 1
            break
        if a == "-" or not a.startswith("-"):
            break
        if a.startswith("--"):
            i += 2 if a == "--check-hash-based-pycs" else 1
            continue
        for j, c in enumerate(a[1:], 1):
            if c in "cm":
                return None
            if c in "XW":
                if j == len(a) - 1:
                    i += 1
                break
        i += 1
    if i >= len(argv):
        return None
    nombre = os.path.basename(argv[i])
    if nombre in OBJETIVO:
        return nombre
    if nombre == "salud_captura.py" and i + 1 < len(argv) and argv[i + 1] == "muestrear":
        return "salud_captura.py muestrear"
    return None


def leer(proc="/proc", listar=os.listdir, abrir=open, existe=os.path.exists):
    presentes, desaparecidos, ilegibles, revisados = [], 0, [], 0
    for pid in sorted((p for p in listar(proc) if p.isdigit()), key=int):
        ruta = os.path.join(proc, pid)
        try:
            with abrir(os.path.join(ruta, "cmdline"), "rb") as f:
                crudo = f.read()
        except (FileNotFoundError, ProcessLookupError):
            desaparecidos += 1
            continue
        except OSError as e:
            if existe(ruta):
                ilegibles.append("%s: %s" % (pid, e))
            else:
                desaparecidos += 1
            continue
        revisados += 1
        argv = [x.decode("utf-8", "surrogateescape") for x in crudo.split(b"\0")]
        if argv and argv[-1] == "":
            argv.pop()
        n = muestreador(argv)
        if n:
            presentes.append((int(pid), n, argv))
    return presentes, desaparecidos, ilegibles, revisados


def main():
    try:
        presentes, desaparecidos, ilegibles, revisados = leer()
    except OSError as e:
        print("DESCONOCIDO no se pudo enumerar /proc: %s" % e)
        return 2
    for pid, n, argv in presentes:
        print("MUESTREADOR pid=%d %s argv=%s" % (pid, n, json.dumps(argv)))
    for x in ilegibles[:5]:
        print("ILEGIBLE %s" % x)
    print("CONSULTA revisados=%d desaparecidos=%d ilegibles=%d presentes=%d"
          % (revisados, desaparecidos, len(ilegibles), len(presentes)))
    if presentes:
        return 10
    if ilegibles:
        print("DESCONOCIDO argv ilegible en %d proceso(s) vivo(s)" % len(ilegibles))
        return 2
    if revisados == 0:
        print("DESCONOCIDO ningun proceso legible en /proc")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
FIN_CODIGO_PUBLICADO
)
  hc=$(printf '%s\n' "$CODIGO" | sha256sum | cut -c1-64)
  if [ "$hc" != a651f76f6f6d154e8f5809f0ffc43a53aa55776ecb4bb4437956f18160fe2e4c ]; then echo "ARGV ERROR código distinto del publicado ($hc)"; rc=3
  else
    o=$(python3 -I -B -S -c "$CODIGO" 2>&1); ra=$?
    printf '%s\n' "$o" | sed 's/^/ARGV /'
    case $ra in 0) echo "ARGV ausencia confirmada";; 10) echo "ARGV PRESENCIA"; [ $rc = 3 ] || rc=1;; *) echo "ARGV DESCONOCIDO rc $ra"; rc=3;; esac
  fi
fi
echo "RESULTADO $N rc=$rc"
exit $rc
