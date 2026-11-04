set -eu
# subir.sh DESTINO(sensor|bastion|srv) DIR_REMOTO FICHERO...  (copia vía bastión y verifica sha256)
H="$1"; R="$2"; shift 2
T=$(mktemp -d); for f in "$@"; do cp "$f" "$T/"; done
(cd "$T" && sha256sum * | sed 's/ \*/  /' > SHA256SUMS && cat SHA256SUMS)
ST="cf-stage-$(date +%s)"
ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes gadmin@10.10.10.30 "mkdir -p $ST"
scp -q -i ~/.ssh/id_ed25519 -o BatchMode=yes "$T"/* gadmin@10.10.10.30:$ST/
case "$H" in
  bastion) ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes gadmin@10.10.10.30 "mkdir -p $R && cp $ST/* $R/ && cd $R && sha256sum -c SHA256SUMS";;
  sensor)  ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'mkdir -p $R' && scp -q -i ~/.ssh/cyberflow-to-sensor $ST/* m4rk@10.10.60.11:$R/ && ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd $R && sha256sum -c SHA256SUMS'";;
  srv)     ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes gadmin@10.10.10.30 "ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'mkdir -p $R' && scp -q -i ~/.ssh/cyberflow-to-srv $ST/* adminsrvdmz@10.10.30.10:$R/ && ssh -o BatchMode=yes -i ~/.ssh/cyberflow-to-srv adminsrvdmz@10.10.30.10 'cd $R && sha256sum -c SHA256SUMS'";;
esac
