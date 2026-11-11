# Paquete de cierre de la Campana B (B3 + B4), 12-nov-2026

Cierra la Campana B como **dos tramos de los 25 episodios previstos**: **B3** (episodios 1-6) y **B4** (episodios 7-25). Branch local `campana-b-cierre-b3-b4`, commit base `f8cef33a470b983cdb93115b6c63543572fd1472`. Ruta del paquete: `03-entregables/13-respuesta-observaciones-validacion-interna/seccion4-resultados/campana-2026-10-26-deteccion-respuesta/campana-B-cierre-b3-b4-2026-11-12/`. **No publicado** (push pendiente de revision).

## Que contiene
| Ruta | Contenido |
|---|---|
| `CONSOLIDADO-25-EPISODIOS.md` | Tabla de los 25 episodios (tramo, estados, E1-E5), denominadores, los ocho `incompleto_timeout`, motivos de indeterminacion de E3 y de no aplicabilidad, cobertura por familia y limitaciones abiertas |
| `HISTORIAL-CAMPANA-B.md` | Corridas, ensayos y correcciones con sus nombres e IDs reales (incluida B1 y B2): que se probo, por que se detuvo, donde esta la evidencia |
| `balances/` | `BALANCE-B3-PARCIAL.md` y `BALANCE-B4.md` **originales** (B4 hasta su cierre tecnico y analisis del 12-nov; la parte anadida despues esta en `reanalisis/`) |
| `reanalisis/` | Reanalisis de E1 por destino bajo el criterio vigente, con pruebas, regresion y trazabilidad por episodio; evidencia complementaria de E3 (no formal) |
| `resultados/` | `resultados-por-episodio.csv/.json` (los 25, con E1-E5, evidencia o motivo, criterio, version del analizador y hashes), salidas crudas de los analizadores y del reanalisis |
| `criterios/` | Criterio E3 fijado el 11-nov y sus antecedentes; limitacion del generador de inundacion. El criterio E1-E5 de origen es `OBJETIVOS-Y-CRITERIOS.md` (ya versionado; ver `INDICE-EVIDENCIA.md`, seccion C) |
| `analisis/` | Scripts y pruebas de los analizadores y del reanalisis, y el constructor de este paquete |
| `pruebas/` | Ejecucion de las pruebas al construir el paquete, y lo que no se pudo re-ejecutar |
| `manifiestos/` | Hashes de los PCAP crudos (514 de B3, 2343 de B4) y de clientes/intentos/salidas; los PCAP **no** estan en el paquete |
| `INDICE-EVIDENCIA.md`, `SHA256SUMS` | Indice con hashes y referencias a los originales; suma de verificacion de este paquete |

## Reglas aplicadas
- **Balances originales conservados**; E1 por destino es un **reanalisis** bajo el criterio vigente, con su codigo y pruebas.
- **Veredictos formales de E3 sin cambios** (5 cumple, 15 indeterminado, 5 no aplica) y **ocho `incompleto_timeout` conservados**.
- **Limitacion abierta:** discrepancia entre el SPAN y los contadores de srv-dmz. El ensayo del contador y la repeticion de los escaneos quedan **fuera del alcance** de este cierre.
- Excluidos: PCAP crudos, credenciales, registros sensibles (ver `INDICE-EVIDENCIA.md`, seccion F).

## Verificar
Desde esta carpeta: `sha256sum -c SHA256SUMS`. Los scripts de `analisis/` usan rutas absolutas del equipo de trabajo (`C:\Users\markp\cf-b3`, `cf-b4`) para leer las copias locales de la evidencia; no se ejecutan sin ellas.
