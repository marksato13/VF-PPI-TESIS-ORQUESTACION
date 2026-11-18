set -u
H=$HOME/cf-b/herramientas; T=$(date -u +%Y%m%dT%H%M%SZ); R=$HOME/cf-b/respaldo-d5/$T-d5-corregido
echo "##### despliegue D5 corregido en el bastión $T"
[ "$(sha256sum /dev/shm/d5c.py | cut -c1-16)" = 00c1bb2922d30138 ] || { echo "PARAR: hash del d5_episodio_corregido recibido"; exit 2; }
[ "$(sha256sum /dev/shm/d5bc.py | cut -c1-16)" = 58f715e2a55405f4 ] || { echo "PARAR: hash del derivado recibido"; exit 2; }
ps -eo args | grep -v 'bash -c' | grep -qE '[l]anzador_puerta|[v]igia_4c|[g]01' && { echo "PARAR: hay una puerta/campaña viva"; exit 2; }
mkdir -p $R; cp -p $H/d5_episodio_banco.py $H/d5_episodio.py $R/; (cd $R && sha256sum * | tee SHA256SUMS | cut -c1-16,65-)
install -m 0644 /dev/shm/d5c.py $H/d5_episodio_corregido.py
install -m 0644 /dev/shm/d5bc.py $H/d5_episodio_banco.py.nuevo
python3 -I $H/hacer_d5_episodio_banco.py $H/d5_episodio_corregido.py - 2>/dev/null | cmp - $H/d5_episodio_banco.py.nuevo && echo "derivado reproducible desde el corregido: OK"
mv -f $H/d5_episodio_banco.py.nuevo $H/d5_episodio_banco.py; chmod 664 $H/d5_episodio_banco.py
rm -f /dev/shm/d5c.py /dev/shm/d5bc.py
echo "--- después"; sha256sum $H/d5_episodio.py $H/d5_episodio_corregido.py $H/d5_episodio_banco.py $H/transporte_bastion.py $H/lanzador_puerta_banco.py $H/hacer_d5_episodio_banco.py | cut -c1-16,65-
python3 -I $H/lanzador_puerta_banco.py ejecutar --help >/dev/null 2>&1 && echo "lanzador arranca (--help): OK"
python3 -I -c "
import importlib.util,sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('d5b','$H/d5_episodio_banco.py'); m=importlib.util.module_from_spec(s); sys.modules['d5b']=m; s.loader.exec_module(m)
print('importa; SETS_APLICACION', m.SETS_APLICACION)"
echo "respaldo: $R"
