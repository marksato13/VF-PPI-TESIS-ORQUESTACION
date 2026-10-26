# Verificación de las figuras de componentes

Fuente única: `03055893722a941449624fef19036fd08929a51f`. Sin actualizaciones posteriores al inicio.

Se verifican los bytes del commit y los hashes del antecedente/evaluación. En 15 archivos de texto el manifiesto fuente declara hashes de CRLF mientras Git publicó LF: reconstruir CRLF reproduce exactamente esos 15 hashes. No hay diferencias de contenido; los hashes reales LF y la prueba se documentan en control.json. Este nuevo manifiesto usa los bytes publicados, sin modificar el manifiesto original.

Se reconstruyen detección y primera señal de cada episodio desde el registro por ventana, se contrasta Tabla 8 y se recalculan las cinco matrices por ventana desde las predicciones guardadas. No se ejecuta otra inferencia ni se reprocesan los PCAP externos.

Histórico (solo antecedente, no graficado como actual): modelo contaminado 6/9, heurísticos antiguos 7/9, híbrido 9/9. IF actual: joblib df547da0…, reglas 2026-10-06.2, umbrales −0.5694578968203693 y −0.5898535710336615, operador score_samples < umbral. Los cuantiles se comprueban con 65 553 scores de validación; ninguna validación se usa como evaluación.

## Episodios

Tabla 8: 6/9, 6/9, 9/9, 9/9, 9/9. Ambos componentes: 6; solo IF: 0; solo heurísticos: 3; ninguno: 0, en ambos alfas. Fuerza bruta no evaluada: no se dibuja como cero.

La fuente usa [T0, último paquete+60 s]. Dos escaneos tienen su primera señal después del último paquete. Si se exige señal dentro de T0–fin, los totales pasan a 4/9, 4/9, 7/9, 7/9, 7/9. Esto es una sensibilidad derivada de marcas publicadas, no una sustitución de Tabla 8 ni otra prueba.

La elegibilidad del replay principal se reconstruyó fijando capture_start 60 s antes de la primera observación. No recupera paquetes ausentes. Con historia observada y elegibilidad real los totales son 3/9, 3/9, 7/9, 7/9, 7/9. Al repuntuar el acumulador: 8/9, 6/9, 9/9, 9/9, 9/9; no equivale a un nuevo ensayo en vivo. Las reglas se ajustaron con estos episodios. Se muestran las sensibilidades para no esconder estas dependencias.

## Ventanas

65 421 normales +84 ataques, 65 505 claves únicas iguales a Tabla 7. Se conservan 74 normales Kali y 45 558 normales sin paquetes. IF sin guarda operativa, como Tabla 7. Heurísticos e híbrido son señales binarias verificadas, no aplicación de LIMIT/BLOCK. No se atribuye AUC/AP al híbrido.

| Configuración | TP | FP | TN | FN | FPR |
|---|---:|---:|---:|---:|---:|
| IF_0.05 | 54 | 2955 | 62466 | 30 | 4.516898 % |
| IF_0.03 | 54 | 1723 | 63698 | 30 | 2.633711 % |
| HEUR | 47 | 472 | 64949 | 37 | 0.721481 % |
| HIB_0.05 | 54 | 3417 | 62004 | 30 | 5.223094 % |
| HIB_0.03 | 54 | 2192 | 63229 | 30 | 3.350606 % |

El híbrido añade 462/469 FP sin nuevos TP sobre IF. Entre los 84 ataques: ambos 47, solo IF 7, solo heurísticos 0, ninguno 30. No mezclar con los nueve episodios de otra campaña.

Control normal de 294,8 s y 61 ventanas, configuración operativa y sensibilidad sin Kali permanecen en los archivos fuente; no se combinan con las métricas de la figura. No se reetiquetan ni se modifican exclusiones.

La comprobación de metadatos/exportaciones se guarda en control.json. Reutilizar estos datos no valida de forma independiente la elección de α. Las figuras conservan las limitaciones del análisis de origen.
