# Tarea

```
ID:     <PREFIJO-nnn>
Estado: READY | EN CURSO | BLOQUEADA | CERRADA
Fecha:  AAAA-MM-DD
Agente: <quién audita> → <quién implementa>
```

## OBJETIVO
<Qué debe quedar mejor. Una frase.>

## ALCANCE
- **Permitido modificar:**
- **Solo lectura:**

## NO MODIFICAR
<Lista explícita. Los artefactos congelados van siempre.>

## FLUJO OBLIGATORIO
1. Claude audita y señala inconsistencias.
2. Codex implementa lo autorizado.
3. Ejecutar pruebas y verificaciones.
4. Claude revisa el diff adversarialmente.
5. Codex corrige solo hallazgos confirmados.
6. Actualizar informes y cronograma.
7. Reporte final **sin commit ni push**.

## RESTRICCIONES
- Máximo <N> ciclos de revisión.
- Detenerse ante hash alterado o prueba fallida.
- No inventar cifras.

## ACEPTACIÓN
- **Comandos:**
- **Hashes esperados:**
- **Archivos que deben actualizarse:**
- **Estado final:** COMPLETO | CONDICIONADO | BLOQUEADO

## SKILLS
<Cuál se activa y por qué. No todas.>
