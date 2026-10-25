# Referencias verificadas — comparación de detectores (25-oct-2026)

Cada referencia se comprobó el 25-oct-2026 en el registro bibliográfico (editorial, DBLP/BibTeX del autor
o repositorio institucional). La columna «Verificación» dice qué se comprobó. Ninguna referencia
respalda los resultados de esta comparación: los números son nuestros, sobre nuestros datos.

## Método original de cada detector

| # | Referencia | DOI / URL | Qué respalda | Verificación |
|---|---|---|---|---|
| R1 | F. T. Liu, K. M. Ting, Z.-H. Zhou, «Isolation Forest», *Proc. 8th IEEE ICDM*, Pisa, 2008, pp. 413–422. | 10.1109/ICDM.2008.17 | IF aísla anomalías mediante particiones aleatorias en lugar de perfilar los datos normales. Coste lineal con submuestreo. | DOI, autores, páginas |
| R2 | B. Schölkopf, J. C. Platt, J. Shawe-Taylor, A. J. Smola, R. C. Williamson, «Estimating the support of a high-dimensional distribution», *Neural Computation* 13(7):1443–1471, 2001. | 10.1162/089976601750264965 | OCSVM: frontera de soporte con núcleo que encierra la mayor parte de los datos de una sola clase. `nu` acota la fracción de atípicos del entrenamiento. | DOI, volumen y páginas; resumen |
| R3 | M. M. Breunig, H.-P. Kriegel, R. T. Ng, J. Sander, «LOF: identifying density-based local outliers», *Proc. ACM SIGMOD 2000*, pp. 93–104. | 10.1145/342009.335388 | LOF: grado de atipicidad según la densidad local relativa a los k vecinos (enfoque de densidad o vecindad). | DOI (BibTeX DBLP), páginas; PDF de los autores |
| R4 | P. J. Rousseeuw, K. Van Driessen, «A fast algorithm for the minimum covariance determinant estimator», *Technometrics* 41(3):212–223, 1999. | 10.2307/1270566 | Elliptic Envelope: localización y covarianza robustas por MCD (FAST-MCD). La anomalía es la distancia de Mahalanobis robusta, con supuesto gaussiano y unimodal. | Revista, volumen y páginas. El DOI JSTOR aparece en los registros; no se pudo resolver el DOI de Taylor & Francis (10.1080/…) |
| R5 | A. Lakhina, M. Crovella, C. Diot, «Diagnosing network-wide traffic anomalies», *Proc. ACM SIGCOMM 2004*, Portland, pp. 219–230. | Registro del autor: 10.1145/1030194.1015492 (versión CCR). Ver P1. | **PCA como detector por error de reconstrucción en tráfico de red:** subespacio normal con los componentes principales y anomalía si el SPE = ‖ỹ‖² del residuo supera un umbral al nivel 1−α (estadístico Q). | **Texto completo leído:** definición del SPE, umbral Q a 1−α (99,5 % y 99,9 %), selección de componentes por 3σ |
| R6 | M.-L. Shyu, S.-C. Chen, K. Sarinnapakorn, L. Chang, «A novel anomaly detection scheme based on principal component classifier», *Proc. ICDM Foundation and New Direction of Data Mining Workshop*, 2003. Reeditado como capítulo en *Foundations and Novel Approaches in Data Mining*, Springer, 2006, pp. 311–329. | https://discovery.fiu.edu/display/pub104244 | Detector de intrusiones con componentes principales «mayores y menores» de instancias normales; la anomalía es la distancia en el espacio de componentes. | Registro institucional (FIU). Sin DOI verificado para la versión de 2003 |

## Entrenamiento con datos normales y elección de enfoques diferentes

| # | Referencia | DOI / URL | Qué respalda | Verificación |
|---|---|---|---|---|
| R7 | M. A. F. Pimentel, D. A. Clifton, L. Clifton, L. Tarassenko, «A review of novelty detection», *Signal Processing* 99:215–249, 2014. | 10.1016/j.sigpro.2013.12.026 | Detección de novedades / clasificación de una clase: se modela la normalidad con los datos de entrenamiento y se señala lo que se aparta. Además, una taxonomía en cinco familias: probabilística, de distancia, de reconstrucción, de dominio y teórico-informativa. | DOI, volumen y páginas. Resumen: verificado («one-class classification», modelo de los datos normales de entrenamiento). Taxonomía: solo por fuente secundaria (SciTePress 2021); falta comprobarla en el texto completo (pendiente P4) |
| R8 | V. Chandola, A. Banerjee, V. Kumar, «Anomaly detection: a survey», *ACM Computing Surveys* 41(3), art. 15, 2009. | 10.1145/1541880.1541882 | Categorías de técnicas (clasificación, vecinos más cercanos, estadísticas, espectrales) con sus supuestos y su coste. También el modo semisupervisado: entrenar solo con normales. | DOI, volumen y número |
| R9 | R. Sommer, V. Paxson, «Outside the closed world: on using machine learning for network intrusion detection», *Proc. IEEE S&P 2010*, pp. 305–316. | 10.1109/SP.2010.25 | Límites de la evaluación de la detección de anomalías en redes: coste de los falsos positivos, diversidad del tráfico y dificultad de evaluar. Respalda las advertencias de alcance, no el rendimiento. | DOI (IEEE Xplore 5504793) |

## Implementación

| # | Referencia | DOI / URL | Qué respalda |
|---|---|---|---|
| R10 | F. Pedregosa et al., «Scikit-learn: Machine Learning in Python», *JMLR* 12:2825–2830, 2011. | https://jmlr.org/papers/v12/pedregosa11a.html | Implementación de `IsolationForest`, `OneClassSVM`, `LocalOutlierFactor(novelty=True)`, `EllipticEnvelope` y `PCA`. En el laptop se usó scikit-learn 1.9.1 y en el sensor, 1.9.0 (ver el manifiesto). |
| R11 | Documentación de scikit-learn, «Novelty and Outlier Detection». | https://scikit-learn.org/stable/modules/outlier_detection.html | Diferencia entre detección de novedades (entrenar con normales, `novelty=True`) y de atípicos. Signo de `score_samples`. |

## Distinción importante

R1–R6 describen los **métodos originales**; R5 y R6 son además **aplicaciones a tráfico o intrusiones**.
La configuración concreta (por ejemplo, `nu=0,05`, k=20, PCA al 95 % de varianza, umbral por cuantil sobre validación)
es **decisión nuestra**, registrada en `config-comparacion.json` antes de entrenar. No proviene de esas fuentes.
En particular, el umbral por cuantil empírico **no** es el estadístico Q de R5.

## Pendientes bibliográficos

- **P1. DOI de Lakhina et al. 2004:** la página del autor da 10.1145/1030194.1015492 (*SIGCOMM CCR* 34(4)). Las actas suelen citarse como 10.1145/1015467.1015492. Hay que confirmar en ACM DL cuál citar.
- **P2. Lazarevic et al., «A comparative study of anomaly detection schemes in network intrusion detection», SIAM SDM 2003:** es una aplicación directa de LOF y otros métodos a redes, pero no se pudo leer el texto completo (el servidor rechaza el certificado). **No citar** hasta comprobar qué métodos compara.
- **P3. Aplicación a redes de OCSVM y Elliptic Envelope:** sin fuente primaria verificada todavía.
- **P4. Taxonomía de Pimentel et al.:** confirmar en el texto completo las cinco familias antes de usarla para justificar la elección de «enfoques distintos».
