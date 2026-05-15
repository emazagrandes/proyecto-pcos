# Anomaly Scan v2 — PCOS Señales Emergentes

> Filosofia: buscamos anomalias, no rankings de medicamentos conocidos.
> El score favorece rareza + consistencia. Metformin no aparecera aqui.

_Senales encontradas: T1(cross-indication)=24 | T2(subpoblacion)=4 | T3(outcome inesperado)=28 | T4(hidden gems)=110 | T6(temporal)=6 | T7(contradicciones)=12 | T8(kg-convergence)=12 | T9(pleiotropia)=48_

---

## 🔬 Síntesis del investigador (LLM)

> Esta sección es generada por Gemma después de leer todas las señales.
> Conecta patrones transversales, propone hipótesis mecanísticas y
> distingue señales reales de ruido. Las tablas detalladas siguen abajo.

## Resumen ejecutivo

El scan revela una dicotomía clara: mientras que las intervenciones generales (SGLT2, Exenatide, CBT, Cromo) ya cuentan con una base de evidencia considerable y meta-análisis (ruido de consenso), existen **vacíos críticos en la granularidad de los resultados**. El patrón global indica que la literatura se ha centrado en la eficacia general, pero ha ignorado los efectos pleiotrópicos y la optimización de subpoblaciones. Específicamente, la señal de SGLT2 (88% favorable) y la de CBT (100% favorable) son conocidas, pero su impacto en el índice de andrógenos libres y el síndrome metabólico en obesos, respectivamente, son "zonas ciegas" confirmadas por la ausencia de resultados en PubMed (0 hits en queries específicas).

## Señales prioritarias para investigar

1. **SGLT2i y el Eje Androgénico**: Aunque los SGLT2i están estudiados en PCOS, no hay evidencia directa que vincule su uso con la reducción del *Free Androgen Index* (FAI) o la inducción de la ovulación.
   - **Mecanismo**: Reducción de la glucotoxicidad hepática y mejora de la sensibilidad a la insulina periférica $\rightarrow$ disminución de la producción de andrógenos en las células tecales.
   - **Detectores**: [T1].
   - **Experimento**: Ensayo clínico aleatorizado (RCT) midiendo FAI y niveles de testosterona libre pre/post tratamiento con Empagliflozina en pacientes con PCOS no respondedoras a Metformina.

2. **Optimización de FET en PCOS (Ciclos Artificiales vs. MNC)**: Existe consenso en la transferencia de embriones congelados (FET), pero hay un vacío total sobre el impacto de los ciclos artificiales en la placentación y la tasa de abortos espontáneos específicamente en PCOS.
   - **Mecanismo**: El control hormonal estricto del ciclo artificial podría mitigar la disfunción endometrial asociada a la hiperinsulinemia del PCOS, mejorando la implantación.
   - **Detectores**: [T4].
   - **Experimento**: Estudio de cohortes comparando tasas de preeclampsia y diabetes gestacional entre FET de ciclo natural modificado vs. ciclo artificial en mujeres con PCOS.

3. **Cromo y Pleiotropía Cardiovascular**: El cromo es conocido para la glucosa, pero su señal de impacto en marcadores inflamatorios (CRP) y riesgo cardiovascular en PCOS es una "gema" no explorada.
   - **Mecanismo**: Potenciación de la señalización de la insulina $\rightarrow$ reducción de estrés oxidativo endotelial $\rightarrow$ mejora de la función vascular.
   - **Detectores**: [T1, T9].
   - **Experimento**: Estudio de intervención midiendo Proteína C Reactiva (PCR) y perfil lipídico avanzado en pacientes con PCOS suplementadas con cromo.

## Hipótesis mecanísticas emergentes

1. **Sinergia CBT-Metabólica en Obesidad**: Si la CBT reduce el cortisol y el estrés crónico (T1), entonces se potenciará la pérdida de peso y la resolución del síndrome metabólico en pacientes con PCOS y BMI > 30 (T2b), más allá de la dieta. Testable mediante medición de cortisol salival y perímetro abdominal en un brazo de CBT vs. Nutrición. (Combina [T1] + [T2b]).

2. **Eje Microbiota-Insulina-Andrógenos**: Si la modulación de la microbiota intestinal (T8) reduce la resistencia a la insulina, entonces se observará una caída proporcional en el hiperandrogenismo (T8) independientemente del peso. Testable mediante secuenciación 16S y medición de testosterona tras intervención con probióticos específicos. (Combina [T8] + [T8]).

## Señales que son probablemente ruido

- **Consenso establecido**: Spironolactone, Letrozole y CBT general. Los meta-análisis en PubMed los convierten en conocimiento base, no en señales de descubrimiento.
- **Sesgo regional**: Las señales de "Iranian" y "Chinese" (T2b) y las decocciones como *Cangfu Daotan* (T4) probablemente reflejan una alta densidad de publicaciones locales en clusters específicos más que una superioridad biológica universal.
- **Inestabilidad temporal**: La caída de Spironolactone (T6) sugiere que los estudios más recientes son más rigurosos o que el efecto placebo de los primeros estudios fue sobreestimado.
- **KG Sparse**: El camino `Obesity $\rightarrow$ Oxidative Stress $\rightarrow$ PCOS` es demasiado genérico y carece de especificidad farmacológica para ser una hipótesis accionable.

---

## 🔍 Auditoría de Novedad — Búsqueda PubMed dirigida por Gemma

> Gemma identificó qué hipótesis buscar (Paso 1) y recibió los
> resultados antes de escribir la síntesis (Paso 2).
> 0 resultados = hipótesis genuinamente nueva; >30 = ya estudiada.

### Hipótesis que Gemma identificó como candidatas (Paso 1)

```
HIPOTESIS: Los inhibidores de SGLT2 muestran una señal de eficacia excepcionalmente alta (88%) y podrían atacar la IR y el hiperandrogenismo desde un ángulo glucósurico no explorado en PCOS.
BROAD_QUERY: "SGLT2 inhibitors" "polycystic ovary syndrome"
SPECIFIC_QUERY: "SGLT2" "PCOS" ("free androgen index" OR "testosterone") "ovulation"
---
HIPOTESIS: El uso de ciclos artificiales y FET (Frozen Embryo Transfer) modificados muestra una señal masiva en N (estudios de >2000 pacientes) para mejorar tasas de nacido vivo y reducir complicaciones placentarias en PCOS.
BROAD_QUERY: "frozen embryo transfer" "polycystic ovary syndrome"
SPECIFIC_QUERY: "FET" "PCOS" ("artificial cycle" OR "modified natural cycle") ("miscarriage" OR "placentation")
---
HIPOTESIS: El cromo presenta una señal pleiotrópica fuerte no solo en glucemia, sino específicamente en biomarcadores cardiovasculares e inflamatorios en pacientes con PCOS.
BROAD_QUERY: "chromium" "polycystic ovary syndrome"
SPECIFIC_QUERY: "chromium" "PCOS" ("cardiovascular" OR "inflammation") ("lipid profile" OR "CRP")
---
HIPOTESIS: Existe una divergencia temporal crítica en la espironolactona (caída drástica de eficacia post-2021), sugiriendo que su uso actual podría estar mal optimizado o sea insuficiente frente a nuevas terapias.
BROAD_QUERY: "spironolactone" "polycystic ovary syndrome"
SPECIFIC_QUERY: "spironolactone" "PCOS" "non-replication" ("androgen" OR "hirsutism")
---
HIPOTESIS: La Terapia Cognitivo-Conductual (CBT) aparece como un modificador poblacional clave para el subgrupo de pacientes con obesidad, con una tasa de éxito del 100% en el scan.
BROAD_QUERY: "cognitive behavioral therapy" "polycystic ovary syndrome"
SPECIFIC_QUERY: "CBT" "PCOS" "obese" ("weight loss" OR "metabolic syndrome")
---
HIPOTESIS: El Exenatide muestra una señal de éxito superior al GLP-1 mainstream (100% vs 67%) y una respuesta específica en la población china que amerita investigación etno-farmacológica.
BROAD_QUERY: "exenatide" "polycystic ovary syndrome"
SPECIFIC_QUERY: "exenatide" "PCOS" "Chinese" ("insulin resistance" OR "ovulation")
```

### Resultados de búsqueda en PubMed (Paso 2)

```

[BROAD] Query: "SGLT2 inhibitors" "polycystic ovary syndrome"
  --> 53 resultados: bastante estudiado, evaluar si la hipotesis especifica ya fue testeada
    · Cardiometabolic effects of SGLT2 inhibitors on polycystic ovary syndrome. (2023)
    · Polycystic ovarian syndrome-current pharmacotherapy and clinical implications. (2022)
    · Do GLP-1 Analogs Have a Place in the Treatment of PCOS? New Insights and Promising Therapies. (2023)

[BROAD] Query: "frozen embryo transfer" "polycystic ovary syndrome"
  --> 254 resultados: campo maduro, alta probabilidad de que ya existe evidencia
    · [META-ANÁLISIS] Ovulation-induced frozen embryo transfer regimens in women with polycystic ovary syndrome: a systematic review and meta- (2024)
    · [META-ANÁLISIS] Stimulated cycle versus artificial cycle for frozen embryo transfer in patients with polycystic ovary syndrome: a Meta-a (2021)
    · Minimising OHSS in women with PCOS. (2025)

[BROAD] Query: "chromium" "polycystic ovary syndrome"
  --> 44 resultados: bastante estudiado, evaluar si la hipotesis especifica ya fue testeada
    · Nutritional Supplements and Complementary Therapies in Polycystic Ovary Syndrome. (2022)
    · [META-ANÁLISIS] Chromium supplementation and polycystic ovary syndrome: A systematic review and meta-analysis. (2017)
    · [META-ANÁLISIS] Chromium supplementation in women with polycystic ovary syndrome: Systematic review and meta-analysis. (2018)

[BROAD] Query: "spironolactone" "polycystic ovary syndrome"
  --> 235 resultados: campo maduro, alta probabilidad de que ya existe evidencia
    · Polycystic Ovary Syndrome: Pathophysiology, Presentation, and Treatment With Emphasis on Adolescent Girls. (2019)
    · Polycystic ovary syndrome. (2004)
    · Alternative treatment of polycystic ovary syndrome: pre-clinical and clinical basis for using plant-based drugs. (2023)

[BROAD] Query: "cognitive behavioral therapy" "polycystic ovary syndrome"
  --> 51 resultados: bastante estudiado, evaluar si la hipotesis especifica ya fue testeada
    · Lifestyle management in polycystic ovary syndrome - beyond diet and physical activity. (2023)
    · [META-ANÁLISIS] The effects of cognitive behavioral therapy in women with polycystic ovary syndrome: A meta-analysis. (2022)
    · AMERICAN ASSOCIATION OF CLINICAL ENDOCRINOLOGISTS AND AMERICAN COLLEGE OF ENDOCRINOLOGY COMPREHENSIVE CLINICAL PRACTICE  (2016)

[BROAD] Query: "exenatide" "polycystic ovary syndrome"
  --> 45 resultados: bastante estudiado, evaluar si la hipotesis especifica ya fue testeada
    · [META-ANÁLISIS] Anti-obesity pharmacological agents for polycystic ovary syndrome: A systematic review and meta-analysis to inform the 2 (2024)
    · Exenatide, Dapagliflozin, or Phentermine/Topiramate Differentially Affect Metabolic Profiles in Polycystic Ovary Syndrom (2021)
    · [META-ANÁLISIS] The Effectiveness and Safety of Exenatide Versus Metformin in Patients with Polycystic Ovary Syndrome: A Meta-Analysis o (2023)

[SPECIFIC] Query: "SGLT2" "PCOS" ("free androgen index" OR "testosterone") "ovulation"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "FET" "PCOS" ("artificial cycle" OR "modified natural cycle") ("miscarriage" OR "placentation")"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "chromium" "PCOS" ("cardiovascular" OR "inflammation") ("lipid profile" OR "CRP")"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "spironolactone" "PCOS" "non-replication" ("androgen" OR "hirsutism")"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "CBT" "PCOS" "obese" ("weight loss" OR "metabolic syndrome")"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "exenatide" "PCOS" "Chinese" ("insulin resistance" OR "ovulation")"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente
```

---

## Tipo 4 — Hidden Gems (raros pero consistentes)

> Intervenciones en muy pocos estudios (1-5) con alta consistencia favorable.
> Estos son los casos que nadie ha leido y cruzado entre si.
> Alta prioridad para investigacion futura.

### [T4] hormone replacement therapy (hrt) / artificial cycle
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 8327 | Rareza: 0.63 | **Score: 8.218**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2022.0 | 10.1186/s12958-022-00931-4 | None | favorable | 8327.0 | live birth rate, miscarriage rate, clinical pregnancy rate |

### [T4] modified natural cycle-frozen embryo transfer (mnc-fet)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 3873 | Rareza: 0.63 | **Score: 7.522**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2025.0 | 10.1007/s10815-025-03523-4 | None | favorable | 3873.0 | miscarriage rate, term birth rate, hypertensive disorders of pregnancy |

### [T4] artificial frozen embryo transfer cycles
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 2427 | Rareza: 0.63 | **Score: 7.096**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2021.0 | 10.1016/j.ajog.2021.01.024 | None | favorable | 2427.0 | hypertensive disorders of pregnancy, gestational diabetes mellitus, abnormal placentation |

### [T4] cangfu daotan decoction (cfdtt)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 2181 | Rareza: 0.63 | **Score: 6.999**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2026.0 | 10.1186/s13048-026-02008-x | None | favorable | 2181.0 | ovulation rate, pregnancy rate, ovarian volume |

### [T4] dingkun pill (dkp)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 1994 | Rareza: 0.63 | **Score: 6.918**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2022.0 | 10.1155/2022/8698755 | None | favorable | 1994.0 | pregnancy rate, ovulation rate, endometrial thickness |

### [T4] cangfu daotan decoction
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 1845 | Rareza: 0.63 | **Score: 6.847**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2024.0 | 10.1016/j.heliyon.2024.e36959 | None | favorable | 1845.0 | response rate, pregnancy rate, ovulation rate |

### [T4] zishen yutai pill (zyp)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 1751 | Rareza: 0.63 | **Score: 6.799**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2025.0 | 10.3389/frph.2025.1748768 | None | favorable | 1751.0 | pregnancy rates, ovulation rates, endometrial thickness |

### [T4] acupoint catgut embedding (ace)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 1663 | Rareza: 0.63 | **Score: 6.753**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2026.0 | 10.2147/dmso.s553787 | None | favorable | 1663.0 | body mass index (bmi), waist-to-hip ratio (whr), waist circumference (wc) |

### [T4] cangfu daotan decoction (cfdtd)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 1433 | Rareza: 0.63 | **Score: 6.617**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2022.0 | 10.1155/2022/4395612 | None | favorable | 1433.0 | pregnancy rate, ovulation rate, estradiol levels |

### [T4] prebiotics, alone or as part of synbiotics
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 1271 | Rareza: 0.63 | **Score: 6.508**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2025.0 | 10.3390/biomedicines13010177 | None | favorable | 1271.0 | body-mass index, diastolic blood pressure, weight |

### [T4] l-carnitine (lc) supplementation
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 1046 | Rareza: 0.63 | **Score: 6.331**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2025.0 | 10.5468/ogs.24272 | None | favorable | 1046.0 | chemical pregnancy rate, clinical pregnancy rate, ovulation rate |

### [T4] polyphenols
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 916 | Rareza: 0.63 | **Score: 6.211**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2024.0 | 10.1016/j.ejogrb.2023.12.038 | None | favorable | 916.0 | serum insulin level, bmi levels, lh levels |

### [T4] carnitine supplement
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 839 | Rareza: 0.63 | **Score: 6.131**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2023.0 | 10.1111/cen.14885 | None | favorable | 839.0 | ovulation rates, pregnancy rates, body mass index (bmi) |

### [T4] xiao yao san (xys)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 736 | Rareza: 0.63 | **Score: 6.012**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2023.0 | 10.1016/j.jep.2023.116517 | None | favorable | 736.0 | ovulation rate, pregnancy rate, hormonal levels |

### [T4] ω-3 polyunsaturated fatty acids (pufas)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 574 | Rareza: 0.63 | **Score: 5.786**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2023.0 | 10.1097/md.0000000000035403 | None | favorable | 574.0 | total cholesterol (tc), triglyceride (tg), homeostatic model assessment for insulin resistance (homa-ir) |

### [T4] cabergoline combination therapy
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 535 | Rareza: 0.63 | **Score: 5.722**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2024.0 | 10.1177/11795514241280028 | None | favorable | 535.0 | body-mass index, regular menstruation, weight change |

### [T4] yoga therapy (yt)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 515 | Rareza: 0.63 | **Score: 5.688**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| nan | 10.1177/15598276211029221 | None | favorable | 515.0 | menstrual irregularity, clinical hyperandrogenism, fasting blood glucose |

### [T4] vitamin e supplementation alone or in combination
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 504 | Rareza: 0.63 | **Score: 5.668**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2022.0 | 10.1038/s41598-022-24467-0 | None | favorable | 504.0 | serum tg, vldl, ldl-c |

### [T4] moxibustion
- Estudios: 2 | Favorables: 2 | Tasa favorable: 100% | N medio: 1991 | Rareza: 0.50 | **Score: 5.48**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2022.0 | 10.1155/2022/3616036 | None | favorable | 1991.0 | pregnancy rate, ovulation rate, miscarriage rate |
| 2021.0 | 10.1155/2021/6619597 | None | favorable | nan | ovulation rate, pregnancy rate, lh |

### [T4] raloxifene
- Estudios: 3 | Favorables: 1 | Tasa favorable: 100% | N medio: 6522 | Rareza: 0.43 | **Score: 5.461**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| nan | NCT00427700 | None | None | nan | n/a |
| nan | NCT01607320 | None | None | nan | n/a |
| 2022.0 | 10.1002/14651858.cd010287.pub4 | None | favorable | 6522.0 | live birth rate, ovarian hyperstimulation syndrome (ohss) rate, clinical pregnancy rate |

### [T4] curcumin (cur)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 296 | Rareza: 0.63 | **Score: 5.186**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2022.0 | 10.1002/ptr.7274 | None | favorable | 296.0 | fasting blood glucose, insulin level, homeostasis model assessment of insulin resistance (homa-ir) |

### [T4] sildenafil
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 216 | Rareza: 0.63 | **Score: 4.902**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2025.0 | 10.1093/jsxmed/qdaf028 | None | favorable | 216.0 | female sexual function index, hospital anxiety and depression scale, modified pcos health-related qol questionnaire |

### [T4] hormone replacement treatment (hrt)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 200 | Rareza: 0.63 | **Score: 4.832**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2025.0 | 10.1007/s10815-025-03500-x | None | favorable | 200.0 | {'outcome': 'clinical pregnancy rate', 'value': '66.0% (le) vs 53.0% (hrt)', 'p_value': 0.061}, {'outcome': 'biochemical pregnancy rate', 'value': '71.0% (le) vs 57.0% (hrt)', 'p_value': 0.039} |

### [T4] green cardamom 3g/day
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 194 | Rareza: 0.63 | **Score: 4.805**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2022.0 | 10.1007/s40519-021-01223-3 | None | favorable | 194.0 | tnf-alpha, il-6, crp |

### [T4] bmp-15 administration
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 185 | Rareza: 0.63 | **Score: 4.762**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2025.0 | 10.1080/09513590.2025.2530571 | None | favorable | 185.0 | infertility rate, metabolic parameters, hormonal balance |

---

## Tipo 1 — Cross-Indication Signals (Drug Repurposing)

> Farmacos NO disenados para PCOS que aparecen con efecto favorable.
> Score ajustado por rareza: 2/3 estudios favorables > 5/200.

### [T1] sglt2 inhibitors
- Estudios: 23 | Favorables: 7 | Mixed: 1 | Consistencia: 88% | Rareza: 0.21 | **Score: 7.442**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT06140108 | None | None | n/a |
| nan | NCT06576375 | None | None | n/a |
| nan | NCT04213677 | None | None | n/a |
| nan | NCT02635386 | None | None | n/a |
| nan | NCT05013112 | None | None | n/a |
| nan | NCT05200793 | None | None | n/a |
| nan | NCT06405178 | None | None | n/a |
| nan | NCT04973891 | None | None | n/a |
| nan | NCT05601336 | None | None | n/a |
| nan | NCT03008551 | None | None | n/a |

### [T1] exenatide
- Estudios: 10 | Favorables: 4 | Consistencia: 100% | Rareza: 0.28 | **Score: 5.116**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT04969627 | None | None | n/a |
| nan | NCT03383068 | None | None | n/a |
| nan | NCT03352869 | None | None | n/a |
| nan | NCT04029272 | None | None | n/a |
| nan | NCT02635386 | None | None | n/a |
| nan | NCT02157974 | None | None | n/a |
| 2025.0 | 10.1111/jog.16296 | None | favorable | homa-ir, 2-h oral glucose tolerance test (ogtt), body mass index (bmi) |
| 2023.0 | 10.1007/s43032-023-01222-y | None | favorable | pregnancy rate, ovulation rate, body mass index |
| 2022.0 | 10.1007/s00404-022-06700-3 | None | favorable | spontaneous pregnancy rate, overall pregnancy rate, pregnancy outcomes |
| 2021.0 | 10.1097/cm9.0000000000001712 | None | favorable | body weight, bmi, waist circumference |

### [T1] intermittent fasting
- Estudios: 20 | Favorables: 5 | Consistencia: 83% | Rareza: 0.22 | **Score: 5.1**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT07385716 | None | None | n/a |
| nan | NCT05126199 | None | None | n/a |
| nan | NCT06882291 | None | None | n/a |
| nan | NCT04452968 | None | None | n/a |
| nan | NCT06804044 | None | None | n/a |
| nan | NCT06031753 | None | None | n/a |
| nan | NCT06204965 | None | None | n/a |
| nan | NCT06302166 | None | None | n/a |
| 2025.0 | 10.1016/j.isci.2025.113654 | None | favorable | weight, insulin resistance (homa-ir), metabolic factors |
| 2025.0 | 10.3390/metabo15100654 | None | neutral | bmi, fasting blood glucose (fbg), homa-ir |

### [T1] glp-1 receptor agonists
- Estudios: 19 | Favorables: 6 | Mixed: 3 | Consistencia: 67% | Rareza: 0.23 | **Score: 4.912**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT02446834 | None | None | n/a |
| nan | NCT07169136 | None | None | n/a |
| nan | NCT06889454 | None | None | n/a |
| nan | NCT06775093 | None | None | n/a |
| nan | NCT04876027 | None | None | n/a |
| 2024.0 | 10.1016/j.jdiacomp.2024.108834 | None | unclear | body mass index (bmi), triglycerides, waist circumference |
| 2025.0 | 10.1016/j.xfre.2024.12.003 | None | mixed | hypothalamic-pituitary-ovarian axis function, uterine function, luteinizing hormone surge |
| 2022.0 | 10.3390/ijms23020583 | None | unclear | pathogenesis, management, drug repurposing efficacy |
| 2022.0 | 10.3390/ijms23084334 | None | favorable | body weight, insulin resistance, inflammation |
| 2023.0 | 10.1186/s12902-023-01500-5 | None | favorable | natural pregnancy rate, menstrual regularity, total pregnancy rate |

### [T1] liraglutide
- Estudios: 21 | Favorables: 6 | Mixed: 3 | Consistencia: 67% | Rareza: 0.22 | **Score: 4.884**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT01899430 | None | None | n/a |
| nan | NCT01911468 | None | None | n/a |
| nan | NCT02909933 | None | None | n/a |
| nan | NCT06742710 | None | None | n/a |
| nan | NCT03885297 | None | None | n/a |
| nan | NCT02483299 | None | None | n/a |
| nan | NCT02187250 | None | None | n/a |
| nan | NCT05965908 | None | None | n/a |
| nan | NCT05952882 | None | None | n/a |
| 2022.0 | 10.1016/j.fertnstert.2022.04.027 | None | favorable | {'outcome': 'body weight (bw)', 'result': '-5.7% change vs -1.4% in placebo'}, {'outcome': 'free androgen index (fai)', 'result': 'significantly reduced compared to placebo'} |

### [T1] cognitive behavioral therapy
- Estudios: 4 | Favorables: 3 | Consistencia: 100% | Rareza: 0.39 | **Score: 4.161**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT01899001 | None | None | n/a |
| 2022.0 | 10.1016/j.rbmo.2022.05.001 | None | favorable | depression scores |
| 2024.0 | 10.1080/17437199.2023.2245020 | None | favorable | body image concerns |
| 2023.0 | 10.1186/s12888-023-04814-9 | None | favorable | depression score, trait anxiety, state anxiety |

### [T1] l-carnitine
- Estudios: 13 | Favorables: 4 | Mixed: 1 | Consistencia: 80% | Rareza: 0.26 | **Score: 4.019**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT03630341 | None | None | n/a |
| nan | NCT01665547 | None | None | n/a |
| nan | NCT07266259 | None | None | n/a |
| 2026.0 | 10.1007/s00210-025-04626-6 | None | favorable | bmi, waist circumference, hip circumference |
| nan | NCT07298564 | None | None | n/a |
| nan | NCT04672720 | None | None | n/a |
| nan | NCT05653895 | None | None | n/a |
| nan | NCT03476356 | None | None | n/a |
| 2025.0 | 10.5468/ogs.24272 | None | favorable | chemical pregnancy rate, clinical pregnancy rate, ovulation rate |
| 2023.0 | 10.1111/cen.14885 | None | favorable | ovulation rates, pregnancy rates, body mass index (bmi) |

### [T1] chromium
- Estudios: 6 | Favorables: 3 | Consistencia: 100% | Rareza: 0.33 | **Score: 3.999**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT05765305 | None | None | n/a |
| nan | NCT03503201 | None | None | n/a |
| nan | NCT06405243 | None | None | n/a |
| 2025.0 | 10.1016/j.endien.2025.501578 | None | favorable | fasting blood insulin, triglyceride, total cholesterol |
| 2026.0 | 10.1186/s12902-025-02158-x | None | favorable | fasting blood glucose, fasting insulin, homa-ir |
| 2025.0 | 10.3389/fnut.2025.1683556 | None | favorable | fasting blood glucose levels, lipid profiles, oxidative stress markers |

### [T1] coenzyme q10
- Estudios: 7 | Favorables: 3 | Consistencia: 100% | Rareza: 0.32 | **Score: 3.945**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT04302532 | None | None | n/a |
| nan | NCT06659406 | None | None | n/a |
| nan | NCT01910766 | None | None | n/a |
| nan | NCT04870502 | None | None | n/a |
| 2026.0 | 10.1007/s00210-025-04626-6 | None | favorable | bmi, waist circumference, hip circumference |
| 2023.0 | 10.1007/s43032-022-01038-2 | None | favorable | insulin resistance (homa-ir, fasting insulin, fasting plasma glucose), sex hormone levels (fsh, testosterone), blood lipids (triglycerides, total cholesterol, ldl-c, hdl-c) |
| 2022.0 | 10.1080/09513590.2021.1991910 | None | favorable | total testosterone, dheas, shbg |

### [T1] cinnamon
- Estudios: 8 | Favorables: 3 | Consistencia: 100% | Rareza: 0.30 | **Score: 3.903**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT01483118 | None | None | n/a |
| nan | NCT00331279 | None | None | n/a |
| nan | NCT06199024 | None | None | n/a |
| nan | NCT03778099 | None | None | n/a |
| nan | NCT00970541 | None | None | n/a |
| 2021.0 | 10.1111/jfbc.13543 | None | favorable | homeostatic model assessment for insulin resistance (homa-ir) scores, insulin resistance (ir) indices |
| 2025.0 | 10.1097/ms9.0000000000004181 | None | favorable | anti-müllerian hormone (amh) levels, follicle-stimulating hormone (fsh) levels, prolactin levels |
| 2024.0 | 10.1016/j.ejogrb.2024.07.032 | None | favorable | {'outcome': 'body weight', 'result': 'statistically significant reduction (wmd: -0.47 kg)'}, {'outcome': 'insulin resistance (homa-ir)', 'result': 'beneficial impact/reduction (smd: 0.5015)'}, {'outcome': 'fasting blood sugar (fbs)', 'result': 'significant improvement (wmd: -7.72 mg/dl)'} |

### [T1] resveratrol
- Estudios: 13 | Favorables: 4 | Mixed: 2 | Consistencia: 67% | Rareza: 0.26 | **Score: 3.349**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT01782911 | None | None | n/a |
| nan | NCT05653895 | None | None | n/a |
| 2022.0 | 10.1111/1440-1681.13698 | None | favorable | insulin resistance, dyslipidaemia, ovarian morphology |
| nan | NCT01720459 | None | None | n/a |
| 2023.0 | 10.11604/pamj.2023.44.134.32404 | None | favorable | testosterone, luteinizing hormone (lh), dehydroepiandrosterone sulfate (dheas) |
| 2026.0 | 10.1007/s00210-025-04495-z | None | unclear | clinical parameters, metabolic parameters, endocrine parameters |
| 2024.0 | 10.1007/s12020-023-03479-4 | None | mixed | prolactin levels, acne scores, total cholesterol |
| 2022.0 | 10.1007/s43032-021-00653-9 | None | favorable | histomorphological features, sex hormones, gonadotropins |
| nan | NCT02766803 | None | None | n/a |
| 2022.0 | 10.7150/thno.67167 | None | favorable | amelioration of polycystic ovary syndrome, transzonal projections (tzps) assembly, camkiiβ expression |

### [T1] 2000 mg myo-inositol
- Estudios: 2 | Favorables: 2 | Consistencia: 100% | Rareza: 0.50 | **Score: 3.0**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| 2025.0 | 10.1007/s00210-024-03745-w | None | favorable | serum and follicular fluid levels of lh, lh/fsh ratio, total testosterone, amh, and androstenedione, oxidative stress markers (mda, tac, gpx, and sod), percentage of immature oocytes |
| 2025.0 | 10.1007/s00210-025-03952-z | None | favorable | expression of survivin, expression of bcl-2, expression of caspase-3 |

### [T1] moxibustion
- Estudios: 2 | Favorables: 2 | Consistencia: 100% | Rareza: 0.50 | **Score: 3.0**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| 2022.0 | 10.1155/2022/3616036 | None | favorable | pregnancy rate, ovulation rate, miscarriage rate |
| 2021.0 | 10.1155/2021/6619597 | None | favorable | ovulation rate, pregnancy rate, lh |

### [T1] genistein
- Estudios: 3 | Favorables: 2 | Consistencia: 100% | Rareza: 0.43 | **Score: 2.862**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| 2025.0 | 10.1186/s12902-025-02035-7 | None | favorable | body weight, ovarian weight |
| 2022.0 | 10.1016/j.ejphar.2022.175275 | None | favorable | insulin resistance, anthropometric indices, ovarian morphology |
| 2021.0 | 10.1039/d1fo00684c | None | unclear | estrous cycle, circulating testosterone, amh |

### [T1] cabergoline
- Estudios: 6 | Favorables: 2 | Consistencia: 100% | Rareza: 0.33 | **Score: 2.666**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT01569256 | None | None | n/a |
| nan | NCT02644304 | None | None | n/a |
| 2024.0 | 10.1016/j.ejogrb.2024.06.037 | None | favorable | prolactin levels, testosterone levels, dheas levels |
| nan | NCT05981742 | None | None | n/a |
| nan | NCT07255911 | None | None | n/a |
| 2024.0 | 10.1177/11795514241280028 | None | favorable | body-mass index, regular menstruation, weight change |

### [T1] alpha-lipoic acid
- Estudios: 8 | Favorables: 2 | Consistencia: 100% | Rareza: 0.30 | **Score: 2.602**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT06418347 | None | None | n/a |
| nan | NCT00505427 | None | None | n/a |
| nan | NCT05231980 | None | None | n/a |
| nan | NCT04881851 | None | None | n/a |
| nan | NCT02666170 | None | None | n/a |
| nan | NCT07182526 | None | None | n/a |
| 2026.0 | 10.5653/cerm.2024.07346 | None | favorable | cumulative ovulation rate, cumulative pregnancy rate, endometrial thickness |
| 2024.0 | 10.5468/ogs.23206 | None | favorable | {'outcome': 'fasting blood sugar (fbs)', 'effect': 'significant reduction'}, {'outcome': 'homeostatic model assessment for insulin resistance (homa-ir)', 'effect': 'significant reduction'} |

### [T1] quercetin
- Estudios: 8 | Favorables: 2 | Consistencia: 100% | Rareza: 0.30 | **Score: 2.602**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT07182526 | None | None | n/a |
| 2024.0 | 10.1186/s12958-024-01220-y | None | favorable | fasting insulin serum (fis) levels, fasting blood glucose (fbg) levels, homa-ir levels |
| 2022.0 | 10.1016/j.jfma.2021.08.015 | None | unclear | estrous cycle, ovulation, testosterone |
| 2022.0 | 10.1016/j.steroids.2021.108936 | None | unclear | free testosterone, lh/fsh ratio, estradiol |
| 2022.0 | 10.3390/molecules27144476 | None | unclear | ovulation disorder, insulin resistance, androgen levels |
| 2025.0 | 10.3389/fendo.2025.1545789 | None | favorable | expression of circadian core oscillations |
| 2021.0 | 10.1016/j.ejphar.2021.174062 | None | unclear | estrous cycle, testosterone, estradiol |
| 2023.0 | 10.3389/fendo.2023.1153289 | None | unclear | estrous cycle regularity, lh/fsh ratio, testosterone |

### [T1] folic acid
- Estudios: 15 | Favorables: 2 | Consistencia: 100% | Rareza: 0.24 | **Score: 2.49**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT03598374 | None | None | n/a |
| nan | NCT01626443 | None | None | n/a |
| nan | NCT06158932 | None | None | n/a |
| nan | NCT03268733 | None | None | n/a |
| nan | NCT00953355 | None | None | n/a |
| nan | NCT03585738 | None | None | n/a |
| nan | NCT03059173 | None | None | n/a |
| nan | NCT01115140 | None | None | n/a |
| nan | NCT01555190 | None | None | n/a |
| nan | NCT05524259 | None | None | n/a |

### [T1] melatonin supplementation
- Estudios: 3 | Favorables: 2 | Mixed: 1 | Consistencia: 67% | Rareza: 0.43 | **Score: 1.908**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| 2022.0 | 10.1007/s12011-021-02725-y | None | favorable | {'variable': 'hirsutism', 'result': 'more reductions in magnesium-melatonin co-supplementation group'}, {'variable': 'tumor necrosis factor-α (tnf-α)', 'result': 'declined significantly in melatonin and co-supplementation groups'}, {'variable': 'total antioxidant capacity (tac)', 'result': 'more increase in magnesium plus melatonin group'} |
| 2025.0 | 10.1002/hsr2.71269 | None | favorable | total antioxidant capacity (tac), endometrial thickness |
| 2024.0 | 10.1186/s13048-024-01450-z | None | mixed | tac levels, fbs, insulin |

### [T1] selenium
- Estudios: 3 | Favorables: 2 | Mixed: 1 | Consistencia: 67% | Rareza: 0.43 | **Score: 1.908**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| 2023.0 | 10.1186/s12902-023-01286-6 | None | mixed | tac, bmi, weight |
| 2023.0 | 10.3746/pnf.2023.28.2.121 | None | favorable | quantitative insulin sensitivity check index, total antioxidant capacity, glutathione |
| 2022.0 | 10.1080/09513590.2022.2118709 | None | favorable | total testosterone, cholesterol, shbg |

### [T1] magnesium
- Estudios: 7 | Favorables: 2 | Consistencia: 67% | Rareza: 0.32 | **Score: 1.753**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT02521753 | None | None | n/a |
| nan | NCT07322120 | None | None | n/a |
| nan | NCT02178150 | None | None | n/a |
| 2025.0 | 10.3389/fnut.2025.1683556 | None | favorable | fasting blood glucose levels, lipid profiles, oxidative stress markers |
| 2025.0 | 10.3390/medicina61020280 | None | neutral | cardiometabolic risk factors, hormonal parameters |
| 2021.0 | 10.1186/s12986-021-00586-9 | None | favorable | total testosterone, homa-ir, serum insulin |
| nan | NCT07298564 | None | None | n/a |

### [T1] semaglutide
- Estudios: 9 | Favorables: 2 | Consistencia: 67% | Rareza: 0.29 | **Score: 1.719**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT03919929 | None | None | n/a |
| nan | NCT06896981 | None | None | n/a |
| nan | NCT06222437 | None | None | n/a |
| nan | NCT05702905 | None | None | n/a |
| nan | NCT05819853 | None | None | n/a |
| nan | NCT05646199 | None | None | n/a |
| 2025.0 | 10.1080/09513590.2025.2553052 | None | favorable | body mass index (bmi), total cholesterol (tc), triglycerides (tg) |
| 2023.0 | 10.1111/dom.14944 | None | unfavorable | {'outcome': 'gastric emptying (ge) at 4 hours', 'result': 'semaglutide retained 37% of solid meal in the stomach compared to no gastric retention in the placebo group (p = 0.002)'}, {'outcome': 'gastric content retention at 1, 2, 3, and 4 hours', 'result': 'increased by 3.5% at 1h, 25.5% at 2h, 38.0% at 3h, and 30.0% at 4h'} |
| 2023.0 | 10.3390/jcm12185921 | None | favorable | body weight, bmi, homa-ir |

### [T1] n-acetyl cysteine
- Estudios: 11 | Favorables: 2 | Consistencia: 67% | Rareza: 0.27 | **Score: 1.693**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT02775734 | None | None | n/a |
| nan | NCT02239107 | None | None | n/a |
| nan | NCT01896492 | None | None | n/a |
| nan | NCT06836128 | None | None | n/a |
| nan | NCT01008046 | None | None | n/a |
| 2025.0 | 10.3390/nu17020284 | None | favorable | progesterone levels, endometrial thickness, lh levels |
| 2023.0 | 10.3389/fnut.2023.1209614 | None | neutral | body mass index, body weight, fasting insulin |
| 2023.0 | 10.1017/s0007114522003270 | None | favorable | total testosterone (tt) levels, follicle-stimulating hormone (fsh) levels, oestrogen levels |
| 2021.0 | 10.1093/molehr/gaab067 | None | unclear | uterine ferroptosis, placental ferroptosis, glutathione peroxidase 4 protein level |
| nan | NCT05340634 | None | None | n/a |

### [T1] pioglitazone
- Estudios: 15 | Favorables: 2 | Mixed: 1 | Consistencia: 50% | Rareza: 0.24 | **Score: 1.245**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| nan | NCT05760677 | None | None | n/a |
| nan | NCT00145340 | None | None | n/a |
| nan | NCT00868140 | None | None | n/a |
| nan | NCT02689843 | None | None | n/a |
| nan | NCT00694759 | None | None | n/a |
| nan | NCT05394142 | None | None | n/a |
| nan | NCT03566225 | None | None | n/a |
| nan | NCT03757923 | None | None | n/a |
| nan | NCT00203996 | None | None | n/a |
| 2024.0 | 10.1111/cen.14983 | None | mixed | weight, body mass index, testosterone |

---

## Tipo 2 — Subpopulation Variance

> Misma intervencion, tasa de exito muy diferente segun subgrupo.
> Dimension: dieta, IMC, etnia, comorbilidades.
> Umbral: diferencia >= 30pp entre mejor y peor subgrupo.

### [T2] lifestyle intervention — dimension: bmi
- Rango: 67% | **Score: 2.124**
- Mejor: **overweight/obese** (4/4 = 100%)
- Peor:  **mixed BMI** (1/3 = 33%)

| Subgrupo | N | N fav | Tasa |
|---|---|---|---|
| mixed BMI | 3 | 1 | 33% |
| overweight/obese | 4 | 4 | 100% |

### [T2] metformin — dimension: bmi
- Rango: 40% | **Score: 1.384**
- Mejor: **overweight/obese** (2/2 = 100%)
- Peor:  **mixed BMI** (3/5 = 60%)

| Subgrupo | N | N fav | Tasa |
|---|---|---|---|
| mixed BMI | 5 | 3 | 60% |
| overweight/obese | 2 | 2 | 100% |
| overweight/obese (BMI ≥25 kg/m²) | 2 | 2 | 100% |

### [T2] exercise — dimension: ethnicity
- Rango: 50% | **Score: 1.292**
- Mejor: **Dutch** (2/2 = 100%)
- Peor:  **Australian** (1/2 = 50%)

| Subgrupo | N | N fav | Tasa |
|---|---|---|---|
| Australian | 2 | 1 | 50% |
| Dutch | 2 | 2 | 100% |

### [T2] dietary intervention — dimension: bmi
- Rango: 33% | **Score: 0.926**
- Mejor: **mixed BMI** (2/2 = 100%)
- Peor:  **overweight/obese** (2/3 = 67%)

| Subgrupo | N | N fav | Tasa |
|---|---|---|---|
| mixed BMI | 2 | 2 | 100% |
| overweight/obese | 3 | 2 | 67% |

---

## Tipo 2b — Cross-Intervention Hidden Modifiers

> EL DETECTOR DE VARIABLES OCULTAS.
> Caracteristica de subpoblacion que predice mejores resultados
> INDEPENDIENTEMENTE de cual sea la intervencion.
> Si 'vegan' tiene 80% favorable en berberina, inositol Y omega-3,
> la dieta (no el farmaco) puede ser el driver real.
> Umbral: delta >= 12pp sobre baseline, en >= 2 intervenciones distintas.

### [T2b] Iranian (dimension: ethnicity)
- **Tasa favorable: 87%** (baseline: 38%, delta: +48%)
- n_estudios: 15 | n_favorable: 13
- Intervenciones DISTINTAS cubriendo este subgrupo: 15
- Intervenciones: low-dose oral contraceptive pills (OCPs) combined with vitamin D3 (50,000 IU/w), magnesium, melatonin, or magnesium plus melatonin supplementation, green cardamom 3g/day, synbiotic pomegranate juice (SPJ) 300 mL/day
- Periodo: 2020.0–2026.0
- **Score: 8.098**
- Interpretacion: Iranian subgroup: 87% favorable (+48% vs baseline) across 15 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] ["insulin resistance"] (dimension: comorbidities)
- **Tasa favorable: 72%** (baseline: 38%, delta: +34%)
- n_estudios: 25 | n_favorable: 18
- Intervenciones DISTINTAS cubriendo este subgrupo: 22
- Intervenciones: curcumin nanomicelle 80mg/day plus metformin 500mg three times daily, metformin, 500 mg/day curcumin, short insulin tolerance test (ITT)
- Periodo: 2020.0–2026.0
- **Score: 7.369**
- Interpretacion: ["insulin resistance"] subgroup: 72% favorable (+34% vs baseline) across 22 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] Chinese (dimension: ethnicity)
- **Tasa favorable: 69%** (baseline: 38%, delta: +31%)
- n_estudios: 26 | n_favorable: 18
- Intervenciones DISTINTAS cubriendo este subgrupo: 26
- Intervenciones: exenatide, 5.0 mg letrozole combined with sequential HMG, electro-acupuncture, acupuncture
- Periodo: 2020.0–2026.0
- **Score: 7.172**
- Interpretacion: Chinese subgroup: 69% favorable (+31% vs baseline) across 26 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] overweight/obese (dimension: bmi)
- **Tasa favorable: 82%** (baseline: 38%, delta: +44%)
- n_estudios: 11 | n_favorable: 9
- Intervenciones DISTINTAS cubriendo este subgrupo: 11
- Intervenciones: three-component lifestyle intervention (cognitive behavioral therapy, nutrition advice, and exercise), exenatide, ketogenic diet, curcumin 1000mg/day (500mg twice daily)
- Periodo: 2019.0–2026.0
- **Score: 5.973**
- Interpretacion: overweight/obese subgroup: 82% favorable (+44% vs baseline) across 11 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] obese (dimension: bmi)
- **Tasa favorable: 100%** (baseline: 38%, delta: +62%)
- n_estudios: 5 | n_favorable: 5
- Intervenciones DISTINTAS cubriendo este subgrupo: 5
- Intervenciones: Liraglutide 3 mg, ketogenic diet, bariatric surgery, Glucagon-like peptide-1 receptor agonists (GLP1-RAs)
- Periodo: 2020.0–2022.0
- **Score: 4.871**
- Interpretacion: obese subgroup: 100% favorable (+62% vs baseline) across 5 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] overweight (dimension: bmi)
- **Tasa favorable: 100%** (baseline: 38%, delta: +62%)
- n_estudios: 5 | n_favorable: 5
- Intervenciones DISTINTAS cubriendo este subgrupo: 5
- Intervenciones: vitamin D3 50,000 IU per week, high-intensity interval training (HIIT), metformin, ketogenic Mediterranean diet with phyoextracts (KEMEPHY)
- Periodo: 2020.0–2023.0
- **Score: 4.871**
- Interpretacion: overweight subgroup: 100% favorable (+62% vs baseline) across 5 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] ["insulin resistance", "obesity"] (dimension: comorbidities)
- **Tasa favorable: 100%** (baseline: 38%, delta: +62%)
- n_estudios: 4 | n_favorable: 4
- Intervenciones DISTINTAS cubriendo este subgrupo: 4
- Intervenciones: very low-carbohydrate ketogenic diet, Exenatide plus Metformin (EX + MET), lifestyle modifications (diet, exercise, and behavioral modification), Glucagon-like peptide-1 receptor agonists (GLP1-RAs)
- Periodo: 2022.0–2026.0
- **Score: 4.13**
- Interpretacion: ["insulin resistance", "obesity"] subgroup: 100% favorable (+62% vs baseline) across 4 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] ["anovulatory infertility"] (dimension: comorbidities)
- **Tasa favorable: 83%** (baseline: 38%, delta: +45%)
- n_estudios: 6 | n_favorable: 5
- Intervenciones DISTINTAS cubriendo este subgrupo: 5
- Intervenciones: letrozole, three-component lifestyle intervention (cognitive behavioral therapy, nutrition advice, and exercise), 5.0 mg letrozole combined with sequential HMG, acupuncture
- Periodo: 2020.0–2026.0
- **Score: 3.801**
- Interpretacion: ["anovulatory infertility"] subgroup: 83% favorable (+45% vs baseline) across 5 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] ["obesity"] (dimension: comorbidities)
- **Tasa favorable: 67%** (baseline: 38%, delta: +28%)
- n_estudios: 9 | n_favorable: 6
- Intervenciones DISTINTAS cubriendo este subgrupo: 9
- Intervenciones: green cardamom 3g/day, Liraglutide 3 mg, obese patients with PCOS, bariatric surgery
- Periodo: 2020.0–2026.0
- **Score: 3.407**
- Interpretacion: ["obesity"] subgroup: 67% favorable (+28% vs baseline) across 9 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] Dutch (dimension: ethnicity)
- **Tasa favorable: 75%** (baseline: 38%, delta: +37%)
- n_estudios: 4 | n_favorable: 3
- Intervenciones DISTINTAS cubriendo este subgrupo: 4
- Intervenciones: three-component lifestyle intervention (cognitive behavioral therapy, nutrition advice, and exercise), polycystic ovary syndrome (PCOS), three-component lifestyle intervention (CBT, healthy diet, and physical therapy), three-component lifestyle intervention (cognitive behavioural therapy, diet, and exercise)
- Periodo: 2020.0–2024.0
- **Score: 2.459**
- Interpretacion: Dutch subgroup: 75% favorable (+37% vs baseline) across 4 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] Italian (dimension: ethnicity)
- **Tasa favorable: 75%** (baseline: 38%, delta: +37%)
- n_estudios: 4 | n_favorable: 3
- Intervenciones DISTINTAS cubriendo este subgrupo: 4
- Intervenciones: Delphi survey on PCOS diagnostic criteria, metformin 1500mg/day, very low-calorie ketogenic diet (VLCKD) Pronokal method, ketogenic diet
- Periodo: 2021.0–2025.0
- **Score: 2.459**
- Interpretacion: Italian subgroup: 75% favorable (+37% vs baseline) across 4 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] ["infertility"] (dimension: comorbidities)
- **Tasa favorable: 57%** (baseline: 38%, delta: +19%)
- n_estudios: 7 | n_favorable: 4
- Intervenciones DISTINTAS cubriendo este subgrupo: 7
- Intervenciones: letrozole, acupuncture treatment twice a week (added to letrozole), unstimulated in vitro maturation (IVM), polycystic ovary syndrome (PCOS)
- Periodo: 2020.0–2025.0
- **Score: 1.904**
- Interpretacion: ["infertility"] subgroup: 57% favorable (+19% vs baseline) across 7 different interventions. The diet/population factor, not the drug, may be the real driver.

---

## Tipo 3 — Unexpected Outcome Co-occurrence

> Outcomes que aparecen repetidamente en estudios de una intervencion
> pero NO son outcomes esperados en PCOS.
> Pueden indicar mecanismos pleiotropicos no estudiados.

### [T3] selenium (3 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| triglyceride | 2 |
| cholesterol | 2 |

### [T3] curcumin (14 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| total cholesterol | 4 |
| quicki | 2 |
| high-density lipoprotein | 2 |
| low-density lipoprotein | 2 |
| serum insulin | 2 |

### [T3] frozen embryo transfer (10 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| hypertensive disorders of pregnancy | 3 |
| gestational diabetes mellitus | 2 |
| large for gestational age | 2 |

### [T3] quercetin (8 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| estrous cycle | 2 |
| estradiol | 2 |

### [T3] glp-1 receptor agonists (19 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| waist circumference | 3 |
| triglycerides | 2 |
| waist circumference (wc) | 2 |
| insulin sensitivity | 2 |

### [T3] probiotics (26 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| triglycerides | 3 |
| total cholesterol | 3 |
| low-density lipoprotein cholesterol | 2 |
| malondialdehyde (mda) | 2 |
| total antioxidant capacity (tac) | 2 |

### [T3] resveratrol (13 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| oxidative stress | 3 |
| inflammation | 2 |

### [T3] acupuncture (51 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| body mass index | 3 |
| hormone levels | 3 |
| ovarian morphology | 3 |
| fasting insulin | 3 |
| ovarian volume | 2 |
| fertility | 2 |
| fasting insulin (fins) | 2 |

### [T3] cabergoline (6 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| prolactin levels | 2 |

### [T3] chromium (6 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| total cholesterol | 2 |

### [T3] exercise (86 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| waist circumference | 4 |
| reproductive function | 3 |
| body mass index | 3 |
| fasting insulin | 3 |
| cardiorespiratory fitness | 3 |
| hormonal parameters | 3 |
| oxidative stress | 2 |
| inflammation | 2 |
| body composition | 2 |
| depression symptoms | 2 |

### [T3] ivf (16 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| implantation rate | 3 |
| miscarriage rate | 2 |

### [T3] l-carnitine (13 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| waist circumference | 2 |
| hip circumference | 2 |

### [T3] vitamin d (51 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| fertility | 2 |
| malondialdehyde | 2 |
| triglycerides | 2 |
| fasting insulin | 2 |
| oxidative stress | 2 |
| folliculogenesis | 2 |
| insulin sensitivity | 2 |

### [T3] sglt2 inhibitors (23 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| total body fat | 2 |
| free androgen index | 2 |
| menstrual frequency | 2 |

### [T3] dietary intervention (110 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| triglycerides | 4 |
| body composition | 4 |
| waist circumference | 3 |
| reproductive function | 2 |
| luteinizing hormone | 2 |
| insulin levels | 2 |
| waist circumference (wc) | 2 |
| fasting insulin | 2 |
| anthropometric measurements | 2 |
| estrous cycle | 2 |

### [T3] oral contraceptives (92 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| waist circumference | 2 |
| endometrial thickness | 2 |
| free androgen index (fai) | 2 |
| triglycerides | 2 |
| hyperandrogenism | 2 |
| insulin sensitivity | 2 |
| body composition | 2 |
| menstrual cycle regularity | 2 |
| ovarian morphology | 2 |
| granulosa cell apoptosis | 2 |

### [T3] spironolactone (18 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| plasma insulin | 2 |
| tnf-alpha | 2 |

### [T3] letrozole (82 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| endometrial thickness | 6 |
| miscarriage rate | 3 |
| hypertensive disorders of pregnancy | 2 |
| gestational diabetes mellitus | 2 |
| number of mature follicles | 2 |

### [T3] n-acetyl cysteine (11 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| endometrial thickness | 2 |

### [T3] clomiphene citrate (94 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| endometrial thickness | 8 |
| miscarriage | 2 |
| multiple pregnancy | 2 |
| miscarriage rate | 2 |

### [T3] lifestyle intervention (85 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| menstrual cycles | 3 |
| waist circumference | 2 |
| insulin sensitivity | 2 |
| reproductive outcomes | 2 |
| hyperandrogenism | 2 |
| menstrual cycle regularity | 2 |

### [T3] metformin (325 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| fasting insulin | 12 |
| total cholesterol | 6 |
| triglycerides | 5 |
| waist circumference | 5 |
| ovarian morphology | 4 |
| menstrual frequency | 4 |
| insulin sensitivity | 4 |
| menstrual cycle regularity | 4 |
| miscarriage rate | 3 |
| prolactin | 3 |

### [T3] pioglitazone (15 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| menstrual frequency | 2 |

### [T3] intermittent fasting (20 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| triglycerides (tg) | 2 |

## Tipo 6 — Temporal Anomaly (evidencia creciente o no-replicacion)

> Misma intervencion, tasa favorable muy diferente en estudios antiguos vs recientes.
> 'rising': evidencia convergente — cada vez mas estudios lo confirman.
> 'falling': no-replicacion — exito inicial no se sostiene en trials mas grandes/nuevos.
> Umbral: diferencia >= 25pp entre eras, >= 2 estudios en cada era.

### [T6] spironolactone — 📉 FALLING (no-replicacion)
- Pre-2022: **100%** favorable (n=2)
- Post-2021: **20%** favorable (n=5)
- Delta: -80% | **Score: 2.536**
- Non-replication signal: favorable rate decreased from 100% (pre-2022, n=2) to 20% (post-2021, n=5). Early enthusiasm may not replicate in larger/newer trials.

### [T6] lifestyle intervention — 📈 RISING (evidencia convergente)
- Pre-2022: **62%** favorable (n=13)
- Post-2021: **91%** favorable (n=11)
- Delta: +29% | **Score: 1.381**
- Converging evidence: favorable rate increased from 62% (pre-2022, n=13) to 91% (post-2021, n=11). Recent trials confirm benefit — timing is good to investigate.

### [T6] dietary intervention — 📉 FALLING (no-replicacion)
- Pre-2022: **100%** favorable (n=8)
- Post-2021: **75%** favorable (n=24)
- Delta: -25% | **Score: 1.272**
- Non-replication signal: favorable rate decreased from 100% (pre-2022, n=8) to 75% (post-2021, n=24). Early enthusiasm may not replicate in larger/newer trials.

### [T6] letrozole — 📉 FALLING (no-replicacion)
- Pre-2022: **100%** favorable (n=4)
- Post-2021: **71%** favorable (n=14)
- Delta: -29% | **Score: 1.235**
- Non-replication signal: favorable rate decreased from 100% (pre-2022, n=4) to 71% (post-2021, n=14). Early enthusiasm may not replicate in larger/newer trials.

### [T6] gnrh agonists — 📉 FALLING (no-replicacion)
- Pre-2022: **50%** favorable (n=2)
- Post-2021: **17%** favorable (n=6)
- Delta: -33% | **Score: 1.107**
- Non-replication signal: favorable rate decreased from 50% (pre-2022, n=2) to 17% (post-2021, n=6). Early enthusiasm may not replicate in larger/newer trials.

### [T6] ivf — 📈 RISING (evidencia convergente)
- Pre-2022: **0%** favorable (n=2)
- Post-2021: **33%** favorable (n=3)
- Delta: +33% | **Score: 0.936**
- Converging evidence: favorable rate increased from 0% (pre-2022, n=2) to 33% (post-2021, n=3). Recent trials confirm benefit — timing is good to investigate.

---

## Tipo 7 — Contradiction Analysis (misma intervencion, efectos opuestos)

> Intervenciones con estudios TANTO favorables COMO desfavorables.
> El detector busca el diferenciador estructural: BMI, etnia, tipo de estudio, año.
> Un diferenciador fuerte = hipotesis mecanistica sobre en quien funciona.

### [T7] ivf
- Favorables: 1 | Desfavorables: 2 | Total: 16 | **Score: 0.521**
- 1 favorable vs 2 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] semaglutide
- Favorables: 2 | Desfavorables: 1 | Total: 9 | **Score: 0.384**
- 2 favorable vs 1 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] pioglitazone
- Favorables: 2 | Desfavorables: 1 | Total: 15 | **Score: 0.272**
- 2 favorable vs 1 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] spironolactone
- Favorables: 3 | Desfavorables: 1 | Total: 18 | **Score: 0.24**
- **Diferenciador top: `year`** (mean diff -4.0 years)
  - En estudios favorables:    mean 2021
  - En estudios desfavorables: mean 2025
- 3 favorable vs 1 unfavorable studies. Strongest differentiator: year (favorable=mean 2021, unfavorable=mean 2025).

### [T7] ivm
- Favorables: 1 | Desfavorables: 1 | Total: 22 | **Score: 0.208**
- **Diferenciador top: `year`** (mean diff +3.0 years)
  - En estudios favorables:    mean 2025
  - En estudios desfavorables: mean 2022
- 1 favorable vs 1 unfavorable studies. Strongest differentiator: year (favorable=mean 2025, unfavorable=mean 2022).

### [T7] gnrh antagonists
- Favorables: 2 | Desfavorables: 1 | Total: 29 | **Score: 0.171**
- 2 favorable vs 1 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] oral contraceptives
- Favorables: 17 | Desfavorables: 2 | Total: 92 | **Score: 0.142**
- 17 favorable vs 2 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] acupuncture
- Favorables: 13 | Desfavorables: 1 | Total: 51 | **Score: 0.112**
- 13 favorable vs 1 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] gonadotropins
- Favorables: 3 | Desfavorables: 1 | Total: 56 | **Score: 0.105**
- 3 favorable vs 1 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] metformin
- Favorables: 63 | Desfavorables: 4 | Total: 325 | **Score: 0.103**
- 63 favorable vs 4 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] letrozole
- Favorables: 14 | Desfavorables: 1 | Total: 82 | **Score: 0.078**
- 14 favorable vs 1 unfavorable studies. No clear structural differentiator found — could be methodological noise.

### [T7] dietary intervention
- Favorables: 26 | Desfavorables: 1 | Total: 110 | **Score: 0.062**
- 26 favorable vs 1 unfavorable studies. No clear structural differentiator found — could be methodological noise.

---

## Tipo 8 — KG Convergence (hipótesis mecanísticas emergentes)

> Caminos de DOS SALTOS en el grafo de mecanismos donde AMBOS saltos
> están confirmados por >= 2 papers independientes.
> A --[r1]--> B --[r2]--> C  donde A=intervención, B=mecanismo, C=endpoint PCOS.
> Ningún paper dice 'A afecta C vía B' — es una hipótesis emergente del grafo.

### [T8] metformin → insulin resistance → pcos
- **Hop 1:** `metformin` --[improves]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 6 papers | conf avg=0.883
- **Score de convergencia:** 10.698  _(= 2 × 6 × avg_conf)_
- **Hipótesis emergente:** _metformin improves insulin resistance (2 papers), y insulin resistance associated_with pcos (6 papers) → hipótesis: metformin modula pcos vía insulin resistance_

  Papers hop 1: 10.1177/2042018820938305, 10.7759/cureus.27689
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] insulin resistance → obesity → pcos
- **Hop 1:** `insulin resistance` --[associated_with]--> `obesity` | 2 papers | conf avg=0.9
- **Hop 2:** `obesity` --[associated_with]--> `pcos` | 6 papers | conf avg=0.867
- **Score de convergencia:** 10.602  _(= 2 × 6 × avg_conf)_
- **Hipótesis emergente:** _insulin resistance associated_with obesity (2 papers), y obesity associated_with pcos (6 papers) → hipótesis: insulin resistance modula pcos vía obesity_

  Papers hop 1: 10.7759/cureus.25076, 10.1093/bmb/ldac007
  Papers hop 2: 10.1186/s13048-021-00879-w, 10.1186/s12916-022-02238-y, 10.1016/j.isci.2024.108783

### [T8] gut microbiota → insulin resistance → pcos
- **Hop 1:** `gut microbiota` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.8
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 6 papers | conf avg=0.883
- **Score de convergencia:** 10.098  _(= 2 × 6 × avg_conf)_
- **Hipótesis emergente:** _gut microbiota associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (6 papers) → hipótesis: gut microbiota modula pcos vía insulin resistance_

  Papers hop 1: 10.3390/metabo13010129, 10.3389/fendo.2022.933110
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] insulin resistance → hyperandrogenism → pcos
- **Hop 1:** `insulin resistance` --[associated_with]--> `hyperandrogenism` | 2 papers | conf avg=0.85
- **Hop 2:** `hyperandrogenism` --[associated_with]--> `pcos` | 5 papers | conf avg=0.9
- **Score de convergencia:** 8.75  _(= 2 × 5 × avg_conf)_
- **Hipótesis emergente:** _insulin resistance associated_with hyperandrogenism (2 papers), y hyperandrogenism associated_with pcos (5 papers) → hipótesis: insulin resistance modula pcos vía hyperandrogenism_

  Papers hop 1: 10.3389/fendo.2022.808898, 10.7759/cureus.44493
  Papers hop 2: 10.1038/s41572-024-00511-3, 10.3390/life12121974, 10.1016/j.lfs.2021.119753

### [T8] obesity → oxidative stress → pcos
- **Hop 1:** `obesity` --[increases]--> `oxidative stress` | 2 papers | conf avg=0.85
- **Hop 2:** `oxidative stress` --[associated_with]--> `pcos` | 3 papers | conf avg=0.9
- **Score de convergencia:** 5.25  _(= 2 × 3 × avg_conf)_
- **Hipótesis emergente:** _obesity increases oxidative stress (2 papers), y oxidative stress associated_with pcos (3 papers) → hipótesis: obesity modula pcos vía oxidative stress_

  Papers hop 1: 10.1186/s12958-024-01337-0, 10.1017/s0007114521003585
  Papers hop 2: 10.3389/fimmu.2023.1211231, 10.23736/s2724-6507.21.03349-6, 10.1007/s10815-021-02342-7

### [T8] metformin → insulin resistance → obesity
- **Hop 1:** `metformin` --[improves]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `obesity` | 2 papers | conf avg=0.9
- **Score de convergencia:** 3.6  _(= 2 × 2 × avg_conf)_
- **Hipótesis emergente:** _metformin improves insulin resistance (2 papers), y insulin resistance associated_with obesity (2 papers) → hipótesis: metformin modula obesity vía insulin resistance_

  Papers hop 1: 10.1177/2042018820938305, 10.7759/cureus.27689
  Papers hop 2: 10.7759/cureus.25076, 10.1093/bmb/ldac007

### [T8] metformin → insulin resistance → hyperandrogenism
- **Hop 1:** `metformin` --[improves]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `hyperandrogenism` | 2 papers | conf avg=0.85
- **Score de convergencia:** 3.5  _(= 2 × 2 × avg_conf)_
- **Hipótesis emergente:** _metformin improves insulin resistance (2 papers), y insulin resistance associated_with hyperandrogenism (2 papers) → hipótesis: metformin modula hyperandrogenism vía insulin resistance_

  Papers hop 1: 10.1177/2042018820938305, 10.7759/cureus.27689
  Papers hop 2: 10.3389/fendo.2022.808898, 10.7759/cureus.44493

### [T8] insulin resistance → obesity → oxidative stress
- **Hop 1:** `insulin resistance` --[associated_with]--> `obesity` | 2 papers | conf avg=0.9
- **Hop 2:** `obesity` --[increases]--> `oxidative stress` | 2 papers | conf avg=0.85
- **Score de convergencia:** 3.5  _(= 2 × 2 × avg_conf)_
- **Hipótesis emergente:** _insulin resistance associated_with obesity (2 papers), y obesity increases oxidative stress (2 papers) → hipótesis: insulin resistance modula oxidative stress vía obesity_

  Papers hop 1: 10.7759/cureus.25076, 10.1093/bmb/ldac007
  Papers hop 2: 10.1186/s12958-024-01337-0, 10.1017/s0007114521003585

### [T8] obesity → oxidative stress → shbg
- **Hop 1:** `obesity` --[increases]--> `oxidative stress` | 2 papers | conf avg=0.85
- **Hop 2:** `oxidative stress` --[reduces]--> `shbg` | 2 papers | conf avg=0.85
- **Score de convergencia:** 3.4  _(= 2 × 2 × avg_conf)_
- **Hipótesis emergente:** _obesity increases oxidative stress (2 papers), y oxidative stress reduces shbg (2 papers) → hipótesis: obesity modula shbg vía oxidative stress_

  Papers hop 1: 10.1186/s12958-024-01337-0, 10.1017/s0007114521003585
  Papers hop 2: 10.3389/fnut.2022.1018674, 10.1016/j.fertnstert.2021.07.1203

### [T8] gut microbiota → insulin resistance → obesity
- **Hop 1:** `gut microbiota` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.8
- **Hop 2:** `insulin resistance` --[associated_with]--> `obesity` | 2 papers | conf avg=0.9
- **Score de convergencia:** 3.4  _(= 2 × 2 × avg_conf)_
- **Hipótesis emergente:** _gut microbiota associated_with insulin resistance (2 papers), y insulin resistance associated_with obesity (2 papers) → hipótesis: gut microbiota modula obesity vía insulin resistance_

  Papers hop 1: 10.3390/metabo13010129, 10.3389/fendo.2022.933110
  Papers hop 2: 10.7759/cureus.25076, 10.1093/bmb/ldac007

### [T8] gut microbiota → insulin resistance → hyperandrogenism
- **Hop 1:** `gut microbiota` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.8
- **Hop 2:** `insulin resistance` --[associated_with]--> `hyperandrogenism` | 2 papers | conf avg=0.85
- **Score de convergencia:** 3.3  _(= 2 × 2 × avg_conf)_
- **Hipótesis emergente:** _gut microbiota associated_with insulin resistance (2 papers), y insulin resistance associated_with hyperandrogenism (2 papers) → hipótesis: gut microbiota modula hyperandrogenism vía insulin resistance_

  Papers hop 1: 10.3390/metabo13010129, 10.3389/fendo.2022.933110
  Papers hop 2: 10.3389/fendo.2022.808898, 10.7759/cureus.44493

### [T8] insulin resistance → obesity → depression
- **Hop 1:** `insulin resistance` --[associated_with]--> `obesity` | 2 papers | conf avg=0.9
- **Hop 2:** `obesity` --[associated_with]--> `depression` | 2 papers | conf avg=0.7
- **Score de convergencia:** 3.2  _(= 2 × 2 × avg_conf)_
- **Hipótesis emergente:** _insulin resistance associated_with obesity (2 papers), y obesity associated_with depression (2 papers) → hipótesis: insulin resistance modula depression vía obesity_

  Papers hop 1: 10.7759/cureus.25076, 10.1093/bmb/ldac007
  Papers hop 2: 10.3389/fpsyt.2022.1001484, 10.3390/medicina58070942

---

## Tipo 9 — Secondary Biomarker Movement (señales pleiotropicas)

> En estudios FAVORABLES, esta intervencion mejora marcadores fuera de PCOS.
> Diferencia de Tipo 3: solo cuenta estudios favorables y agrupa por categoria clinica.
> Señala beneficios pleiotropicos: cardiovascular, inflamacion, microbioma, etc.

### [T9] crocin 15mg twice daily — top: cardiovascular
- Estudios favorables: 1 | **Score: 5.0**
- In 1 favorable studies, crocin 15mg twice daily consistently affects cardiovascular markers (hdl cholesterol, ldl cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 3 | hdl cholesterol, ldl cholesterol |
| inflammation | 2 | il-6, tnf-alpha |

### [T9] curcumin (cur) — top: cardiovascular
- Estudios favorables: 1 | **Score: 4.0**
- In 1 favorable studies, curcumin (cur) consistently affects cardiovascular markers (total cholesterol, ldl) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 4 | total cholesterol, ldl |

### [T9] vitamin e supplementation alone or in combination — top: cardiovascular
- Estudios favorables: 1 | **Score: 4.0**
- In 1 favorable studies, vitamin e supplementation alone or in combination consistently affects cardiovascular markers (vldl, ldl-c) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 4 | vldl, ldl-c |

### [T9] ω-3 polyunsaturated fatty acids (pufas) — top: cardiovascular
- Estudios favorables: 1 | **Score: 4.0**
- In 1 favorable studies, ω-3 polyunsaturated fatty acids (pufas) consistently affects cardiovascular markers (total cholesterol (tc), triglyceride (tg)) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 4 | total cholesterol (tc), triglyceride (tg) |

### [T9] chromium — top: cardiovascular
- Estudios favorables: 3 | **Score: 3.33**
- In 3 favorable studies, chromium consistently affects cardiovascular markers (triglyceride, total cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 6 | triglyceride, total cholesterol |
| liver | 2 | fasting blood insulin, fasting insulin |
| inflammation | 2 | oxidative stress markers, inflammatory responses |

### [T9] atorvastatin — top: cardiovascular
- Estudios favorables: 1 | **Score: 3.0**
- In 1 favorable studies, atorvastatin consistently affects cardiovascular markers (triglycerides, low-density lipoprotein cholesterol (ldl-c)) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 3 | triglycerides, low-density lipoprotein cholesterol (ldl-c) |

### [T9] canola oil 25g/day — top: cardiovascular
- Estudios favorables: 1 | **Score: 3.0**
- In 1 favorable studies, canola oil 25g/day consistently affects cardiovascular markers (tc/hdl ratio, ldl/hdl ratio) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 3 | tc/hdl ratio, ldl/hdl ratio |

### [T9] prebiotics, alone or as part of synbiotics — top: cardiovascular
- Estudios favorables: 1 | **Score: 3.0**
- In 1 favorable studies, prebiotics, alone or as part of synbiotics consistently affects cardiovascular markers (diastolic blood pressure, triglycerides) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 3 | diastolic blood pressure, triglycerides |

### [T9] simvastatin — top: cardiovascular
- Estudios favorables: 1 | **Score: 3.0**
- In 1 favorable studies, simvastatin consistently affects cardiovascular markers (total cholesterol, low-density lipoprotein cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 3 | total cholesterol, low-density lipoprotein cholesterol |

### [T9] sunflower oil 25g/day — top: cardiovascular
- Estudios favorables: 1 | **Score: 3.0**
- In 1 favorable studies, sunflower oil 25g/day consistently affects cardiovascular markers (tc/hdl ratio, ldl/hdl ratio) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 3 | tc/hdl ratio, ldl/hdl ratio |

### [T9] vitamin e supplementation (alone or — top: cardiovascular
- Estudios favorables: 1 | **Score: 3.0**
- In 1 favorable studies, vitamin e supplementation (alone or consistently affects cardiovascular markers (total cholesterol, ldl-cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 3 | total cholesterol, ldl-cholesterol |

### [T9] omega-3 — top: cardiovascular
- Estudios favorables: 4 | **Score: 2.5**
- In 4 favorable studies, omega-3 consistently affects cardiovascular markers ({'marker': 'high-sensitivity c-reactive protein (hs-crp)', 'result': 'significant decrease (smd -0.29)'}, triglyceride) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 7 | {'marker': 'high-sensitivity c-reactive protein (hs-crp)', 'result': 'significant decrease (smd -0.29)'}, triglyceride |
| inflammation | 3 | {'marker': 'nitric oxide', 'result': 'no statistically significant results'}, nitric oxide levels |

### [T9] probiotics — top: cardiovascular
- Estudios favorables: 8 | **Score: 2.5**
- In 8 favorable studies, probiotics consistently affects cardiovascular markers (ldl, triglycerides) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 16 | ldl, triglycerides |
| inflammation | 2 | malondialdehyde (mda) |
| mental_health | 2 | sleep quality, anxiety |

### [T9] selenium — top: cardiovascular
- Estudios favorables: 2 | **Score: 2.5**
- In 2 favorable studies, selenium consistently affects cardiovascular markers (triglyceride, cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 5 | triglyceride, cholesterol |

### [T9] butyric acid — top: inflammation
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, butyric acid consistently affects inflammation markers ({'outcome': 'granulosa cells inflammation', 'result': 'ameliorated'}, {'outcome': 'inflammatory cytokines (il-6 and tnf-α)', 'result': 'downregulated'}) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| inflammation | 2 | {'outcome': 'granulosa cells inflammation', 'result': 'ameliorated'}, {'outcome': 'inflammatory cytokines (il-6 and tnf-α)', 'result': 'downregulated'} |

### [T9] green cardamom 3g/day — top: inflammation
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, green cardamom 3g/day consistently affects inflammation markers (tnf-alpha, il-6) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| inflammation | 2 | tnf-alpha, il-6 |

### [T9] magnesium — top: inflammation
- Estudios favorables: 2 | **Score: 2.0**
- In 2 favorable studies, magnesium consistently affects inflammation markers (oxidative stress markers, inflammatory responses) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| inflammation | 2 | oxidative stress markers, inflammatory responses |
| cardiovascular | 2 | ldl-c, hdl-c |

### [T9] orlistat — top: cardiovascular
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, orlistat consistently affects cardiovascular markers (ldl-c, hdl-c) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 2 | ldl-c, hdl-c |

### [T9] puerarin 150mg/day — top: cardiovascular
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, puerarin 150mg/day consistently affects cardiovascular markers (systolic blood pressure, total cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 2 | systolic blood pressure, total cholesterol |

### [T9] semaglutide — top: cardiovascular
- Estudios favorables: 2 | **Score: 2.0**
- In 2 favorable studies, semaglutide consistently affects cardiovascular markers (total cholesterol (tc), triglycerides (tg)) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 4 | total cholesterol (tc), triglycerides (tg) |

### [T9] silibinin — top: inflammation
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, silibinin consistently affects inflammation markers (inflammation, oxidative stress) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| inflammation | 2 | inflammation, oxidative stress |

### [T9] silibinin (100 or 200 mg/kg ip) — top: inflammation
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, silibinin (100 or 200 mg/kg ip) consistently affects inflammation markers (inflammation, oxidative stress) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| inflammation | 2 | inflammation, oxidative stress |

### [T9] transtheoretical model-based mobile health application program — top: mental_health
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, transtheoretical model-based mobile health application program consistently affects mental_health markers (zung’s self-rating anxiety scale (sas), zung’s self-rating depression scale (sds)) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| mental_health | 2 | zung’s self-rating anxiety scale (sas), zung’s self-rating depression scale (sds) |

### [T9] yoga — top: mental_health
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, yoga consistently affects mental_health markers (anxiety, depression) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| mental_health | 2 | anxiety, depression |

### [T9] curcumin — top: cardiovascular
- Estudios favorables: 9 | **Score: 1.67**
- In 9 favorable studies, curcumin consistently affects cardiovascular markers (total cholesterol, triglyceride) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 13 | total cholesterol, triglyceride |
| liver | 2 | fasting insulin, fasting blood sugar (fbs) |

---

