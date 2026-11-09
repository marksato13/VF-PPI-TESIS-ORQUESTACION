# Prueba del vigía desplegado antes de repetir la batería (09-nov-2026 11:38-11:44Z)
- Vigía 2026-11-06.1 (sha 2fe00200e755fd02) + salud_captura 2026-11-06.1 (274b4d613357be60), en ~/cf-e4/vigia-20261106 de Sensor1; importa salud_captura de su propio directorio (vigia_4c.py:64) y pasa el EVE al clasificador (líneas 189-190: suricata_eve=se).
- Seis intervalos de la corrida cancelada (datos en 4c-cancelada-20261109T1058Z): 6 x C0 (prueba_vigia_final.out, paso 4). El vigía del paquete del 4-nov daba 6 x C3 (prueba_vigia_real.out).
- Medida de Suricata faltante (EVE sin eventos stats): 6 x C3 'Suricata (EVE) ausente' (paso 5).
- X1 con decidir/condiciones del vigía desplegado: 6 x C0 -> sin X1; 6 x C3 -> X1 (paso 7). Pruebas del repo test_etapa4_vigia_decision.py: 14 pasan (test_x1_solo_cuando_es_seguro).
- Nota (comportamiento previo, ajeno a P1, NO modificado): sin NINGUNA muestra de salud que cubra el periodo, clasificar devuelve 'insuficiente' (prueba_vigia_fuera.out), que el X1 no cuenta; se cubre por las pausas del vigía si el muestreador se cae.
- El paso 6 de prueba_vigia_final.out (08:00Z) fue un intervalo con cobertura (muestras desde 07:36Z) y por eso da C0; el caso sin cobertura es prueba_vigia_fuera.out.
