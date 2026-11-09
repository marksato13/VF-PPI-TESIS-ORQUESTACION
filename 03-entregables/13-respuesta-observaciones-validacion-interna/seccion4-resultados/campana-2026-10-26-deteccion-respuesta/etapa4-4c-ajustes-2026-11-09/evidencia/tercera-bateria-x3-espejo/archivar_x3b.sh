cd "$HOME"
TS=20261109T1625Z
N=4c-x3b-cancelada-$TS
B="ssh -n -o BatchMode=yes -i $HOME/.ssh/id_ed25519 gadmin@10.10.10.30"
echo "== Sensor1"
$B "ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-sensor m4rk@10.10.60.11 'cd ~/cf-e4 && [ -d 4c ] && [ ! -e $N ] && mv -n 4c $N; ls -d ~/cf-e4/4c*; du -sh ~/cf-e4/$N | cut -f1; ls ~/cf-e4/$N | head -30 | tr \"\\n\" \" \"'"
echo; echo "== Bastión"
$B "cd ~/cf-e4 && [ -d 4c ] && [ ! -e $N ] && mv -n 4c $N; ls -d ~/cf-e4/4c*"
echo "== Kali"
$B "ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-atacante adminatacante@10.10.20.30 'cd ~ && [ -d cf-e4-4c ] && [ ! -e cf-e4-4c-x3b-cancelada-$TS ] && mv -n cf-e4-4c cf-e4-4c-x3b-cancelada-$TS; ls -d cf-e4-4c*; echo generadores: \$(pgrep -fc \"[g]enerar_campana.py --config\"); grep -c \"\\\"evento\\\": \\\"fin\\\"\" cf-e4-4c-x3b-cancelada-$TS/corrida/marcas.jsonl'"
echo "== clientes"
$B "ssh -n -o BatchMode=yes -i ~/.ssh/cyberflow-to-clientes adminclientes@10.10.20.20 'cd ~/cf-e4 && [ -d 4c ] && [ ! -e $N ] && mv -n 4c $N; ls -d ~/cf-e4/4c*'"
