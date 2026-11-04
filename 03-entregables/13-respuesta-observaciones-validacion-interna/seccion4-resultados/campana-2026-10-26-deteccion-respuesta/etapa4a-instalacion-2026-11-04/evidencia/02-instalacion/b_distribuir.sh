set -u
cd ~/cf-e4 && sha256sum -c cyberflow-e4-ec78ca5.tar.gz.sha256 \
  && mkdir paquete && tar -xzf cyberflow-e4-ec78ca5.tar.gz -C paquete \
  && ( cd paquete && sha256sum -c --quiet SHA256SUMS ) && echo "bastion: SHA256SUMS OK" && cat paquete/VERSION-ETAPA4 || { echo "PARADA bastion"; exit 1; }
for d in "cyberflow-to-sensor m4rk@10.10.60.11" "cyberflow-to-srv adminsrvdmz@10.10.30.10"; do
  set -- $d
  echo "=== $2"
  ssh -n -o BatchMode=yes -i ~/.ssh/$1 $2 'mkdir -p ~/cf-e4 && [ ! -e ~/cf-e4/paquete ]' || { echo "PARADA $2"; break; }
  scp -q -o BatchMode=yes -i ~/.ssh/$1 ~/cf-e4/cyberflow-e4-ec78ca5.tar.gz ~/cf-e4/cyberflow-e4-ec78ca5.tar.gz.sha256 $2:cf-e4/
  ssh -n -o BatchMode=yes -i ~/.ssh/$1 $2 'cd ~/cf-e4 && sha256sum -c cyberflow-e4-ec78ca5.tar.gz.sha256 \
    && mkdir paquete && tar -xzf cyberflow-e4-ec78ca5.tar.gz -C paquete \
    && ( cd paquete && sha256sum -c --quiet SHA256SUMS ) && echo "SHA256SUMS OK" && cat paquete/VERSION-ETAPA4'
done
