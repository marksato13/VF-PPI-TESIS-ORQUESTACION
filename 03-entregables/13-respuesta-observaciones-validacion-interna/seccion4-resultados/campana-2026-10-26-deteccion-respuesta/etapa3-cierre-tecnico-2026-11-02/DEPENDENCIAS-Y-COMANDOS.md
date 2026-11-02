# Dependencias, commits y comandos del cierre técnico

> **Corrección del 2026-11-02.** «`main`, que sigue siendo `7b275b8`, lo desplegado»: `main` es `7b275b8`, pero lo
> desplegado en Sensor1 es el motor **24f8a80** con la cadena v1 as-deployed **f57ca00**
> ([ESTADO-OBSERVADO](../etapa4-preparacion-2026-11-02/ESTADO-OBSERVADO-LABORATORIO.md)).

Todo se ejecutó en el portátil: pruebas, replay y ensayos en el banco Docker aislado (`--network none`). **Ningún comando ha tocado el laboratorio**: no hubo despliegue, reinicios, enforcement, campañas, cambios de modelo o umbrales ni ediciones del Word, y no se intervino en piloto-con-dns.

## Commits

Repo de código `marksato13/VF-Sistema-Open-Source-para-la-Deteccion-Temprana-de-Comportamientos-Anomalos-en-Redes-de-Datos`, rama `candidato/etapa3-20261102`. **No se fusiona en `main`**, que sigue siendo `7b275b8`, lo desplegado.

| Commit | Contenido |
|---|---|
| `585da7b` | punto de partida: candidata de la Etapa 3, sin cambios posteriores al empezar |
| `49a29db` | cierre: lectura continua, `auth_failure` por la vista HTTP, filtro VLAN, banco con VLAN e `ip_forward=0`, `observacion_dns.py`, `cambios_auth_failure.py` (**motor del replay del cierre**) |
| `ec78ca5` | el resumidor de la batería separa los tramos (solo resume; no cambia el motor ni la vía rápida) |

**Commit recomendado:** `ec78ca5` (`ec78ca56a3a8f4bb17fda967a7f0abe0e9a2c742`). El motor es idéntico al de `49a29db`, con el que se hizo el replay.

Las entradas (modelo, `eve-segmento.json`, `marcas.jsonl`, anillo de 5 s, archivo PCAP y segmentos del banco) son las mismas de `../etapa3-deteccion-temprana-2026-11-02/DEPENDENCIAS-Y-COMANDOS.md`, con los mismos sha256.

## Entornos

| Entorno | Versiones |
|---|---|
| Portátil (Windows 11, Git Bash) | Python 3.13.5 para las herramientas; `venv-modelo` (Python 3.14.3, scikit-learn 1.9.0, numpy 2.5.1) para el motor |
| Banco `cyberflow-etapa3-banco:1` (`sha256:59f94126…98c0`, la misma imagen) | Python 3.13, tcpdump 4.99.5, **libpcap 1.10.5 (TPACKET_V3)**, tcpreplay 4.5.1, nftables 1.1.3; kernel 6.18 (WSL2) |

## Comandos

Cada bloque lleva su etiqueta. Todos los ejecuté yo; el banco lo arranqué tras avisar y lo cerré al terminar.

### Regresiones: la versión anterior frente a la corregida

`[LAPTOP PowerShell → Docker]` → lo ejecuté yo. Se usan los tres ficheros de `585da7b` (`git show 585da7b:scripts/engine/<f>`) sobre la copia del árbol corregido.

```
docker run --rm --privileged --network none -v <repo>:/src:ro -v <viejo>:/viejo:ro -v <guiones>:/c:ro \
  cyberflow-etapa3-banco:1 bash /c/regresiones.sh
```

Resultado en `resultados/pruebas/regresiones-y-suite-docker.txt`:

- pruebas nuevas con `585da7b`: **7 fallan y 5 pasan**;
- pruebas nuevas con la corrección: 12 pasan;
- suite completa: **639 pasan y 1 se omite** (sin node).

### Pruebas en el portátil

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python -m pytest -q tests/test_etapa2_cadena.py tests/test_etapa3_publicador.py tests/test_motor_incremental.py \
  tests/test_vista_vivo.py tests/test_escaneo_temprano.py tests/test_detector_rapido_flujo.py \
  tests/test_auth_failure_vista.py tests/test_observacion_dns.py
```

### Ensayos en el banco

`[LAPTOP PowerShell → Docker]` → lo ejecuté yo.

```
docker run --rm --privileged --network none -v <repo>:/src:ro -v <seg>:/seg:ro -v <out>:/out -v <guiones>:/c:ro \
  cyberflow-etapa3-banco:1 bash /c/ensayos_cierre.sh
```

`guiones/ensayos_cierre.sh` ejecuta en orden:

1. las pruebas nuevas en Linux;
2. `ensayo_vlan_captura.py /seg /out/vlan`;
3. `ensayo_via_rapida.py /seg /out/bateria-c C 3 quitar`;
4. `ensayo_via_rapida.py /seg /out/bateria-c-vlan C 3 conservar`.

### Replay completo del 3B y análisis

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
N=49a29db-e5-eventos bash guiones/correr_completo_cierre.sh   # mismo tramo, anillo, modelo y argumentos que e3
N=cierre-49a29db-e5-eventos bash guiones/analizar_cierre.sh   # analizar_3b.py SIN MODIFICAR, comparar_25,
                                                              # comparar_completos (frente a sec-opt y e3),
                                                              # cambios_auth_failure, via_rapida_episodios,
                                                              # matriz_reglas, observacion_dns (ensayo)
```

### Manifiesto

`[LAPTOP Git Bash]` → lo ejecuté yo.

```
python guiones/manifiesto_lf.py <carpeta>     # texto a LF (lo que publica git) y MANIFIESTO.sha256
bash guiones/verificar_github.sh              # cada sha256 contra git show origin/main:<ruta>
```
