"""Integracion del camino SSH REAL de srv-dmz en la puerta D5 (hallazgo del 11-nov 07:27Z).
`orquestar_b.SshRunners.srv` ejecuta `<remoto> srv-nft ...` por SSH; si <remoto> es el d5_episodio.py ORIGINAL, el contador `descartes_limite`
cuenta como "presente" y la puerta no se libera. Aqui: ssh falso (ejecuta la orden con sh -c) + `sudo` falso en PATH que atiende cf-nft-helper
con un estado fijo; se llama a `SshRunners.srv` con remoto = original y con remoto = corregido, y se comprueba que `lanzador_puerta_banco.ejecutar`
pasa `--remoto-srv` a SshRunners. Ejecutar en Linux (banco): python3 -m unittest test_srv_remoto_ssh -v
"""
import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from types import SimpleNamespace

AQUI = os.path.dirname(os.path.abspath(__file__))
K = "10.10.20.30"
ESTADO = {"ok": True, "estado": {"sets": {"bloqueados": {}, "limitados": {}},
                                  "descartes_limite": {K: {"bytes": 7665, "expira_s": 3687, "id": None, "paquetes": 101}}}}


def _ejecutable(ruta, texto):
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)
    os.chmod(ruta, os.stat(ruta).st_mode | stat.S_IEXEC)


class TestSrvRemotoSsh(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # sudo falso: `sudo -n /usr/local/sbin/cf-nft-helper` -> devuelve el estado fijo (op listar) o ok (otras)
        _ejecutable(os.path.join(self.tmp, "sudo"), '#!/bin/sh\ncat >/dev/null\ncat "%s/estado.json"\n' % self.tmp)
        json.dump(ESTADO, open(os.path.join(self.tmp, "estado.json"), "w"))
        # ssh falso: ignora el destino y ejecuta la ultima palabra como orden local
        _ejecutable(os.path.join(self.tmp, "fakessh"), '#!/bin/sh\neval "$@"\n')
        self.env = dict(os.environ, PATH=self.tmp + os.pathsep + os.environ["PATH"])
        os.environ["PATH"] = self.env["PATH"]
        sys.path.insert(0, AQUI)
        import orquestar_b as ob
        self.ob = ob

    def _srv_nft(self, fichero):
        remoto = "python3 -I %s" % os.path.join(AQUI, fichero)
        r = self.ob.SshRunners("%s/fakessh" % self.tmp, "%s/fakessh" % self.tmp, remoto=remoto)
        return r.srv("nft", origen=K)

    def test_original_cuenta_el_contador_como_presente(self):
        r = self._srv_nft("d5_episodio.py")
        self.assertTrue(r["presente"], "el original debe reproducir el defecto (falso bloqueo)")

    def test_corregido_por_ssh_no_cuenta_el_contador(self):
        r = self._srv_nft("d5_episodio_corregido.py")
        self.assertTrue(r["ok"])
        self.assertFalse(r["presente"])
        self.assertEqual(r["donde"], [])
        self.assertIn("descartes_limite", r["residual"])

    def test_corregido_por_ssh_con_restriccion_activa_si_esta_presente(self):
        e = json.loads(json.dumps(ESTADO)); e["estado"]["sets"]["limitados"] = {K: {"bytes": 1, "expira_s": 100, "id": "a" * 16, "paquetes": 1}}
        json.dump(e, open(os.path.join(self.tmp, "estado.json"), "w"))
        r = self._srv_nft("d5_episodio_corregido.py")
        self.assertTrue(r["presente"])
        self.assertEqual(r["donde"], ["limitados"])

    def test_lanzador_pasa_remoto_srv_a_sshrunners(self):
        spec = importlib.util.spec_from_file_location("lanzador_puerta_banco", os.path.join(AQUI, "lanzador_puerta_banco.py"))
        lz = importlib.util.module_from_spec(spec); spec.loader.exec_module(lz)
        visto = {}

        class Falso:
            def __init__(self, s, v, remoto=None):
                visto["remoto"] = remoto
                self.srv = lambda *a, **k: {}

        import compuerta_b as cb
        orig = (self.ob.SshRunners, cb.bucle, lz.cargar_banco)
        self.ob.SshRunners, cb.bucle, lz.cargar_banco = Falso, (lambda *a, **k: None), (lambda ruta: None)
        try:
            for extra, esperado in ((["--remoto-srv", "python3 -I ~/cf-b/herramientas/d5_episodio_corregido.py"], "python3 -I ~/cf-b/herramientas/d5_episodio_corregido.py"), ([], None)):
                visto.clear()
                d = tempfile.mkdtemp()
                lz.main(["ejecutar", "--dir", d, "--d5-banco", "x", "--sensor", "u@h", "--clave", "k", "--known-hosts", "h", "--herramientas", AQUI,
                         "--ssh-sensor-legado", "ssh s", "--ssh-srv-legado", "ssh v"] + extra)
                self.assertEqual(visto.get("remoto"), esperado)
        finally:
            self.ob.SshRunners, cb.bucle, lz.cargar_banco = orig


if __name__ == "__main__":
    unittest.main()
