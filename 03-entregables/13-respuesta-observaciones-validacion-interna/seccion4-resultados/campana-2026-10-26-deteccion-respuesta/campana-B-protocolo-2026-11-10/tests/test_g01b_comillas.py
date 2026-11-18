"""Los comandos que g01b envía por ssh a la Kali deben llegar como shell válido (el guion usa comillas dobles anidadas)."""
import re
import subprocess
from pathlib import Path

G = Path(__file__).resolve().parent.parent / "guiones" / "g01b_lanzar_bateria_b.sh"


def bloques_ssh_kali(texto):
    """Cada `ssh -n $CTL kali "...."` completo, hasta la comilla de cierre (la que va seguida de fin de línea o `|| exit 2`)."""
    out, i = [], 0
    while True:
        a = texto.find('ssh -n $CTL kali "', i)
        if a < 0:
            return out
        j = a + len('ssh -n $CTL kali "')
        while True:
            j = texto.index('"', j)
            if texto[j - 1] != "\\" and re.match(r'"(\s*\|\| exit 2)?\s*(\n|$)', texto[j:j + 14]):
                break
            j += 1
        out.append(texto[a:j + 1])
        i = j + 1


def test_los_dos_comandos_remotos_son_shell_valido_y_llevan_la_comprobacion_ntp(tmp_path):
    bl = bloques_ssh_kali(G.read_text(encoding="utf-8"))
    assert len(bl) == 2
    arnes = ("K=/home/x; KS=/home/y; CTL='-o X'; NONCE=n\n"
             "ssh() { local n=${NREM:-0}; printf '%s\\n' \"${@: -1}\" > " + str(tmp_path) + "/remoto$n.sh; NREM=$((n + 1)); }\n"
             "NREM=0\n" + "\n".join(bl) + "\n")
    p = tmp_path / "arnes.sh"
    p.write_text(arnes)
    r = subprocess.run(["bash", str(p)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for n in (0, 1):
        assert subprocess.run(["bash", "-n", str(tmp_path / f"remoto{n}.sh")], capture_output=True).returncode == 0
    r0 = (tmp_path / "remoto0.sh").read_text()
    assert "show-timesync -p ServerAddress --value" in r0 and "200.25.3.17" in r0 and "PARAR: el servidor NTP de la Kali" in r0
    assert "generar_campana_b.py" in (tmp_path / "remoto1.sh").read_text()
    assert "--permiso-por-episodio" in (tmp_path / "remoto1.sh").read_text()


def test_el_vigia_y_la_orden_del_sensor_usan_la_variante_y_la_lista_ntp():
    t = G.read_text(encoding="utf-8")
    assert t.count("vigia_4c_b.py") >= 4 and "--ntp-permitido 200.25.3.17" in t
    assert 'vigia_4c.py" bucle' not in t and "vigia-20261106/vigia_4c.py sensor" not in t
    assert "VBH=a4b64381fc54313f" in t
