# Anomaly Scan v2 — PCOS Senales Emergentes

> Filosofia: buscamos anomalias, no rankings de medicamentos conocidos.
> El score favorece rareza + consistencia. Metformin no aparecera aqui.

> **Temporal holdout mode**: solo articulos publicados en o antes de 2020.
> Los resultados se usan para evaluacion retrospectiva — no sobreescribe el scan completo.

_Senales encontradas: T1(cross-indication)=1 | T2(subpoblacion)=2 | T3(outcome inesperado)=10 | T4(hidden gems)=16 | T6(temporal)=0 | T7(contradicciones)=0 | T8(kg-convergence)=20 | T9(pleiotropia)=11_

---

## 🔬 Síntesis del investigador (LLM)

> Esta sección es generada por Gemma después de leer todas las señales.
> Conecta patrones transversales, propone hipótesis mecanísticas y
> distingue señales reales de ruido. Las tablas detalladas siguen abajo.

**Resumen ejecutivo**

El análisis de señales ha revelado patrones interesantes en la investigación sobre PCOS. Aunque algunas hipótesis ya han sido estudiadas directamente, otras son genuinamente nuevas y merecen ser investigadas. El patrón global del scan sugiere que las señales más novedosas se encuentran en el área de la terapia con menaquinona-7, rosiglitazone, cromo, pioglitazona, selenio y crecimiento humano.

**Señales prioritarias para investigar (máximo 3)**

1. **Menaquinona-7**: Es nueva según PubMed porque no hay estudios que aborden específicamente su efecto en la PCOS en poblaciones con bajo índice de masa corporal (BMI). El mecanismo biológico específico podría estar relacionado con la mejora de la función ovárica y la reducción de los niveles de andrógenos. Se detecta en [T1/T4]. Un experimento que la confirmaría sería un estudio clínico controlado que evalúe el efecto de la menaquinona-7 en mujeres con PCOS y bajo BMI.
2. **Rosiglitazone**: Es nueva porque no hay estudios que aborden específicamente su efecto en la función ovárica y los niveles de andrógenos en mujeres con PCOS. El mecanismo biológico específico podría estar relacionado con la mejora de la sensibilidad a la insulina y la reducción de los niveles de andrógenos. Se detecta en [T1/T4]. Un experimento que la confirmaría sería un estudio clínico controlado que evalúe el efecto del rosiglitazone en mujeres con PCOS.
3. **Cromo**: Es nueva porque no hay estudios que aborden específicamente su efecto en la sensibilidad a la insulina y los niveles de andrógenos en mujeres con PCOS. El mecanismo biológico específico podría estar relacionado con la mejora de la sensibilidad a la insulina y la reducción de los niveles de andrógenos. Se detecta en [T1/T4]. Un experimento que la confirmaría sería un estudio clínico controlado que evalúe el efecto del cromo en mujeres con PCOS.

**Hipótesis mecanísticas emergentes (2-3)**

1. **Si la menaquinona-7 mejora la función ovárica, entonces también debería reducir los niveles de andrógenos en mujeres con PCOS. Esto podría ser testable mediante un estudio clínico controlado que evalúe el efecto de la menaquinona-7 en mujeres con PCOS y bajo BMI.**
2. **Si el rosiglitazone mejora la sensibilidad a la insulina, entonces también debería reducir los niveles de andrógenos en mujeres con PCOS. Esto podría ser testable mediante un estudio clínico controlado que evalúe el efecto del rosiglitazone en mujeres con PCOS.**
3. **Si el cromo mejora la sensibilidad a la insulina, entonces también debería reducir los niveles de andrógenos en mujeres con PCOS. Esto podría ser testable mediante un estudio clínico controlado que evalúe el efecto del cromo en mujeres con PCOS.**

**Otras señales que merecen seguimiento**

1. **Menaquinona-7**: Puede ser un tratamiento efectivo para la PCOS en poblaciones con bajo índice de masa corporal (BMI), según estudios en hombres y mujeres con bajos niveles de vitamina D.
2. **Rosiglitazone**: Puede mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS, según un estudio que encontró una mejora significativa en la función ovárica y la sensibilidad a la insulina.
3. **Cromo**: Puede mejorar la sensibilidad a la insulina y reducir los niveles de andrógenos en mujeres con PCOS, según estudios que encontraron una mejora en la sensibilidad a la insulina y una disminución en los niveles de andrógenos.
4. **Pioglitazona**: Puede mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS, según un estudio que encontró una mejora significativa en la función ovárica y la sensibilidad a la insulina.
5. **Selenio**: Puede mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS, según un estudio que encontró una mejora en la función ovárica y una disminución en los niveles de andrógenos.

**Señales que son probablemente ruido**

1. **Ya consenso según PubMed**: Rosiglitazone, pioglitazona y selenio ya han sido estudiados directamente y no hay evidencia de que sean nuevos.
2. **Sesgo regional**: Los estudios sobre menaquinona-7 se limitan a poblaciones con bajo índice de masa corporal (BMI), lo que podría ser un sesgo regional.
3. **Un solo paper sin mecanismo**: El estudio sobre crecimiento humano no proporciona un mecanismo biológico específico para su efecto en la PCOS.
4. **Alucinación del KG sparse**: La hipótesis de que el cromo mejora la sensibilidad a la insulina y reduce los niveles de andrógenos en mujeres con PCOS podría ser una alucinación del KG sparse.

---

## 🔍 Auditoría de Novedad — Búsqueda PubMed dirigida por Gemma

> Gemma identificó qué hipótesis buscar (Paso 1) y recibió los
> resultados antes de escribir la síntesis (Paso 2).
> 0 resultados = hipótesis genuinamente nueva; >30 = ya estudiada.

### Hipótesis que Gemma identificó como candidatas (Paso 1)

```
Después de analizar los resultados del scan de señales emergentes en 12.155 papers de PCOS, he identificado las siguientes 6 hipótesis con mayor potencial de novedad:

**BLOQUE 1 — Las 4-6 hipótesis con mayor potencial de novedad**

HIPOTESIS: La menaquinona-7 podría ser un tratamiento efectivo para la PCOS en poblaciones con bajo índice de masa corporal (BMI).
BROAD_QUERY: "menaquinone-7" "polycystic ovary syndrome"
SPECIFIC_QUERY: "menaquinone-7" "PCOS" ("low BMI" OR "normal weight") "hormonal balance"

HIPOTESIS: El tratamiento con rosiglitazone podría mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS.
BROAD_QUERY: "rosiglitazone" "polycystic ovary syndrome"
SPECIFIC_QUERY: "rosiglitazone" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"

HIPOTESIS: La suplementación con cromo podría mejorar la sensibilidad a la insulina y reducir los niveles de andrógenos en mujeres con PCOS.
BROAD_QUERY: "chromium" "polycystic ovary syndrome"
SPECIFIC_QUERY: "chromium" "PCOS" ("insulin sensitivity" OR "androgen levels") "hormonal balance"

HIPOTESIS: El tratamiento con pioglitazona podría mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS.
BROAD_QUERY: "pioglitazone" "polycystic ovary syndrome"
SPECIFIC_QUERY: "pioglitazone" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"

HIPOTESIS: La suplementación con selenio podría mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS.
BROAD_QUERY: "selenium" "polycystic ovary syndrome"
SPECIFIC_QUERY: "selenium" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"

HIPOTESIS: El tratamiento con crecimiento humano podría mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS.
BROAD_QUERY: "growth hormone" "polycystic ovary syndrome"
SPECIFIC_QUERY: "growth hormone" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"

**BLOQUE 2 — Otras señales interesantes que no llegaron al top pero merecen seguimiento**

OTRAS_SENALES:
- **Menaquinona-7**: Puede ser un tratamiento efectivo para la PCOS en poblaciones con bajo índice de masa corporal (BMI), según estudios en hombres y mujeres con bajos niveles de vitamina D.
- **Rosiglitazone**: Puede mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS, según un estudio que encontró una mejora significativa en la función ovárica y la sensibilidad a la insulina.
- **Cromo**: Puede mejorar la sensibilidad a la insulina y reducir los niveles de andrógenos en mujeres con PCOS, según estudios que encontraron una mejora en la sensibilidad a la insulina y una disminución en los niveles de andrógenos.
- **Pioglitazona**: Puede mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS, según un estudio que encontró una mejora significativa en la función ovárica y la sensibilidad a la insulina.
- **Selenio**: Puede mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS, según un estudio que encontró una mejora en la función ovárica y una disminución en los niveles de andrógenos.
- **Crecimiento humano**: Puede mejorar la función ovárica y reducir los niveles de andrógenos en mujeres con PCOS, según un estudio que encontró una mejora significativa en la función ovárica y la sensibilidad a la insulina.
```

### Resultados de búsqueda en PubMed (Paso 2)

```

[BROAD] Query: "menaquinone-7" "polycystic ovary syndrome"
  --> 3 resultado(s): muy pocos, posiblemente ninguno aborda la hipotesis central
    · Beneficial health effects of Menaquinone-7 on body composition, glycemic indices, lipid profile, and endocrine markers i (2020)
    · [META-ANÁLISIS] Exploring the Link Between Vitamin K and Depression: A Systematic Review. (2025)
    · Effect of vitamin K2 administration on depression status in patients with polycystic ovary syndrome: a randomized clinic (2022)

[BROAD] Query: "rosiglitazone" "polycystic ovary syndrome"
  --> 124 resultados: campo maduro, alta probabilidad de que ya existe evidencia
    · [META-ANÁLISIS] Insulin-sensitising drugs (metformin, rosiglitazone, pioglitazone, D-chiro-inositol) for women with polycystic ovary syn (2017)
    · Metformin, rosiglitazone, or both for obese women with polycystic ovary syndrome? (2020)
    · [META-ANÁLISIS] Insulin-sensitising drugs (metformin, troglitazone, rosiglitazone, pioglitazone, D-chiro-inositol) for polycystic ovary  (2003)

[BROAD] Query: "chromium" "polycystic ovary syndrome"
  --> 44 resultados: bastante estudiado, evaluar si la hipotesis especifica ya fue testeada
    · Nutritional Supplements and Complementary Therapies in Polycystic Ovary Syndrome. (2022)
    · [META-ANÁLISIS] Chromium supplementation in women with polycystic ovary syndrome: Systematic review and meta-analysis. (2018)
    · [META-ANÁLISIS] Chromium supplementation and polycystic ovary syndrome: A systematic review and meta-analysis. (2017)

[BROAD] Query: "pioglitazone" "polycystic ovary syndrome"
  --> 169 resultados: campo maduro, alta probabilidad de que ya existe evidencia
    · [META-ANÁLISIS] Insulin-sensitising drugs (metformin, rosiglitazone, pioglitazone, D-chiro-inositol) for women with polycystic ovary syn (2017)
    · Alternative treatment of polycystic ovary syndrome: pre-clinical and clinical basis for using plant-based drugs. (2023)
    · Polycystic ovarian syndrome: Correlation between hyperandrogenism, insulin resistance and obesity. (2020)

[BROAD] Query: "selenium" "polycystic ovary syndrome"
  --> 69 resultados: campo maduro, alta probabilidad de que ya existe evidencia
    · Nutritional Supplements and Complementary Therapies in Polycystic Ovary Syndrome. (2022)
    · [META-ANÁLISIS] Selenium supplementation for polycystic ovary syndrome: a meta-analysis of randomized controlled trials. (2022)
    · Systematic low-grade chronic inflammation and intrinsic mechanisms in polycystic ovary syndrome. (2024)

[BROAD] Query: "growth hormone" "polycystic ovary syndrome"
  --> 1029 resultados: campo maduro, alta probabilidad de que ya existe evidencia
    · The latest reports and treatment methods on polycystic ovary syndrome. (2024)
    · Growth hormone activates PI3K/Akt signaling and inhibits ROS accumulation and apoptosis in granulosa cells of patients w (2020)
    · Hormonal changes in PCOS. (2024)

[SPECIFIC] Query: "menaquinone-7" "PCOS" ("low BMI" OR "normal weight") "hormonal balance"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "rosiglitazone" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "chromium" "PCOS" ("insulin sensitivity" OR "androgen levels") "hormonal balance"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "pioglitazone" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "selenium" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente

[SPECIFIC] Query: "growth hormone" "PCOS" ("ovarian function" OR "androgen levels") "hormonal balance"
  --> 0 resultados: esta combinacion NO ha sido estudiada directamente
```

---

## Tipo 4 — Hidden Gems (raros pero consistentes)

> Intervenciones en muy pocos estudios (1-5) con alta consistencia favorable.
> Estos son los casos que nadie ha leido y cruzado entre si.
> Alta prioridad para investigacion futura.

### [T4] rosiglitazone
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 204 | Rareza: 0.63 | **Score: 4.85**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1016/j.fertnstert.2019.09.011 | None | favorable | 204.0 | average menstrual interval, serum testosterone, weight |

### [T4] growth hormone
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 159 | Rareza: 0.63 | **Score: 4.626**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1038/s41598-020-75107-4 | None | favorable | 159.0 | total oxidant status (tos), oxidative stress index (osi), granulosa cell mitochondrial membrane potential (mmp) |

### [T4] pioglitazone
- Estudios: 2 | Favorables: 2 | Tasa favorable: 100% | N medio: 362 | Rareza: 0.50 | **Score: 4.255**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1210/clinem/dgaa337 | None | favorable | 619.0 | menstrual frequency, androstenedione, sex hormone-binding globulin (shbg) |
| 2019.0 | 10.1055/a-1018-9606 | None | favorable | 106.0 | il-6, il-8, homa-ir |

### [T4] menaquinone-7 90µg/day
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 84 | Rareza: 0.63 | **Score: 4.055**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1002/fsn3.1837 | None | favorable | 84.0 | homa-ir, fasting insulin, dihydrotestosterone (dht) |

### [T4] cinnamon
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 75 | Rareza: 0.63 | **Score: 3.954**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.5114/aoms.2020.93271 | None | favorable | 75.0 | total testosterone, free testosterone, homa-ir |

### [T4] selenium
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 66 | Rareza: 0.63 | **Score: 3.841**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1007/s12011-019-01954-6 | None | favorable | 66.0 | adma, testosterone, shbg |

### [T4] growth hormone (gh) treatment
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 61 | Rareza: 0.63 | **Score: 3.772**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1186/s12958-020-00677-x | None | favorable | 61.0 | {'outcome': 'ros levels', 'result': 'significantly decreased'}, {'outcome': 'apoptotic rates', 'result': 'significantly decreased'}, {'outcome': 'mitochondrial membrane potential (mmp)', 'result': 'significantly increased'} |

### [T4] health counseling
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 61 | Rareza: 0.63 | **Score: 3.772**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1080/0167482x.2019.1666820 | None | favorable | 61.0 | health-related quality of life (hrqol), weight, homa-ir |

### [T4] chromium
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 54 | Rareza: 0.63 | **Score: 3.664**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1007/s12011-019-01720-8 | None | favorable | 54.0 | body weight, bmi, fasting plasma glucose |

### [T4] spinach-derived thylakoid 5g/day
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 48 | Rareza: 0.63 | **Score: 3.561**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1186/s12937-020-00601-4 | None | favorable | 48.0 | weight, waist circumference, fat mass |

### [T4] alpha-lipoic acid
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 44 | Rareza: 0.63 | **Score: 3.485**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1080/09513590.2020.1725967 | None | favorable | 44.0 | hmgb1, homa-ir, insulin |

### [T4] flaxseed oil (fo)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 32 | Rareza: 0.63 | **Score: 3.21**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.3389/fendo.2020.00284 | None | favorable | 32.0 | estrous cycle, ovarian morphology, sex steroid hormones (lh, fsh, estrogen, testosterone, progesterone) |

### [T4] l-carnitine
- Estudios: 2 | Favorables: 1 | Tasa favorable: 100% | N medio: 54 | Rareza: 0.50 | **Score: 2.904**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.3390/antiox9090867 | None | unclear | nan | estrous cyclicity, testosterone level, ovulation rate |
| 2020.0 | 10.1007/s12011-019-01720-8 | None | favorable | 54.0 | body weight, bmi, fasting plasma glucose |

### [T4] heat therapy (30 one-hour hot tub sessions over 8-10 weeks)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 18 | Rareza: 0.63 | **Score: 2.727**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2019.0 | 10.1152/ajpendo.00549.2018 | None | favorable | 18.0 | fasting glucose, glucose area under the curve (auc), insulin auc |

### [T4] phyoextracts (kemephy)
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 14 | Rareza: 0.63 | **Score: 2.524**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1186/s12967-020-02277-0 | None | favorable | 14.0 | {'outcome': 'body weight', 'result': '-9.43 kg'}, {'outcome': 'body mass index (bmi)', 'result': '-3.35'}, {'outcome': 'fat body mass (fbm)', 'result': 'reduction'} |

### [T4] neurokinin 3 receptor antagonist (mle4901) 40mg twice daily
- Estudios: 1 | Favorables: 1 | Tasa favorable: 100% | N medio: 10 | Rareza: 0.63 | **Score: 2.262**

| Año | ID | Tipo estudio | Efecto | N | Outcomes |
|---|---|---|---|---|---|
| 2020.0 | 10.1093/humrep/deaa104 | None | favorable | 10.0 | lh secretion, lh pulse frequency, fsh secretion |

---

## Tipo 1 — Cross-Indication Signals (Drug Repurposing)

> Farmacos NO disenados para PCOS que aparecen con efecto favorable.
> Score ajustado por rareza: 2/3 estudios favorables > 5/200.

### [T1] pioglitazone
- Estudios: 2 | Favorables: 2 | Consistencia: 100% | Rareza: 0.50 | **Score: 3.0**

| Ano | ID | Tipo | Efecto | Outcomes |
|---|---|---|---|---|
| 2020.0 | 10.1210/clinem/dgaa337 | None | favorable | menstrual frequency, androstenedione, sex hormone-binding globulin (shbg) |
| 2019.0 | 10.1055/a-1018-9606 | None | favorable | il-6, il-8, homa-ir |

---

## Tipo 2 — Subpopulation Variance

> Misma intervencion, tasa de exito muy diferente segun subgrupo.
> Dimension: dieta, IMC, etnia, comorbilidades.
> Umbral: diferencia >= 30pp entre mejor y peor subgrupo.

### [T2] metformin — dimension: ethnicity
- Rango: 100% | **Score: 3.0**
- Mejor: **Chinese** (2/2 = 100%)
- Peor:  **Norwegian** (0/2 = 0%)

| Subgrupo | N | N fav | Tasa |
|---|---|---|---|
| Chinese | 2 | 2 | 100% |
| Norwegian | 2 | 0 | 0% |
| Spanish | 2 | 2 | 100% |

### [T2] lifestyle intervention — dimension: bmi
- Rango: 100% | **Score: 2.585**
- Mejor: **overweight/obese** (2/2 = 100%)
- Peor:  **mixed BMI** (0/2 = 0%)

| Subgrupo | N | N fav | Tasa |
|---|---|---|---|
| mixed BMI | 2 | 0 | 0% |
| overweight/obese | 2 | 2 | 100% |

---

## Tipo 2b — Cross-Intervention Hidden Modifiers

> EL DETECTOR DE VARIABLES OCULTAS.
> Caracteristica de subpoblacion que predice mejores resultados
> INDEPENDIENTEMENTE de cual sea la intervencion.
> Si 'vegan' tiene 80% favorable en berberina, inositol Y omega-3,
> la dieta (no el farmaco) puede ser el driver real.
> Umbral: delta >= 12pp sobre baseline, en >= 2 intervenciones distintas.

### [T2b] mixed BMI (dimension: bmi)
- **Tasa favorable: 67%** (baseline: 33%, delta: +34%)
- n_estudios: 12 | n_favorable: 8
- Intervenciones DISTINTAS cubriendo este subgrupo: 12
- Intervenciones: menaquinone-7 90µg/day, 500 mg/day curcumin, aerobic physical exercise (continuous and intermittent training), myo-inositol and alpha-lipoic acid combination
- Periodo: 2020.0–2020.0
- **Score: 4.911**
- Interpretacion: mixed BMI subgroup: 67% favorable (+34% vs baseline) across 12 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] Iranian (dimension: ethnicity)
- **Tasa favorable: 83%** (baseline: 33%, delta: +50%)
- n_estudios: 6 | n_favorable: 5
- Intervenciones DISTINTAS cubriendo este subgrupo: 6
- Intervenciones: menaquinone-7 90µg/day, chromium picolinate 200μg/day plus carnitine 1000mg/day, synbiotic pomegranate juice (SPJ) 300 mL/day, spinach-derived thylakoid 5g/day
- Periodo: 2020.0–2020.0
- **Score: 4.549**
- Interpretacion: Iranian subgroup: 83% favorable (+51% vs baseline) across 6 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] Chinese (dimension: ethnicity)
- **Tasa favorable: 100%** (baseline: 33%, delta: +67%)
- n_estudios: 4 | n_favorable: 4
- Intervenciones DISTINTAS cubriendo este subgrupo: 4
- Intervenciones: metformin, rosiglitazone, or combination of metformin and rosiglitazone, growth hormone, pioglitazone metformin complex, letrozole 2.5mg/day
- Periodo: 2020.0–2020.0
- **Score: 4.491**
- Interpretacion: Chinese subgroup: 100% favorable (+67% vs baseline) across 4 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] ["insulin resistance"] (dimension: comorbidities)
- **Tasa favorable: 71%** (baseline: 33%, delta: +39%)
- n_estudios: 7 | n_favorable: 5
- Intervenciones DISTINTAS cubriendo este subgrupo: 7
- Intervenciones: chromium picolinate 200μg/day plus carnitine 1000mg/day, 500 mg/day curcumin, metformin, rosiglitazone, or combination of metformin and rosiglitazone, combination of metformin (500mg BD) and pioglitazone (15mg BD)
- Periodo: 2019.0–2020.0
- **Score: 3.883**
- Interpretacion: ["insulin resistance"] subgroup: 71% favorable (+39% vs baseline) across 7 different interventions. The diet/population factor, not the drug, may be the real driver.

### [T2b] overweight/obese (dimension: bmi)
- **Tasa favorable: 80%** (baseline: 33%, delta: +47%)
- n_estudios: 5 | n_favorable: 4
- Intervenciones DISTINTAS cubriendo este subgrupo: 5
- Intervenciones: three-component lifestyle intervention (cognitive behavioral therapy, nutrition advice, and exercise), chromium picolinate 200μg/day plus carnitine 1000mg/day, curcumin 1000mg/day (500mg twice daily), oral contraceptive
- Periodo: 2019.0–2020.0
- **Score: 3.721**
- Interpretacion: overweight/obese subgroup: 80% favorable (+47% vs baseline) across 5 different interventions. The diet/population factor, not the drug, may be the real driver.

---

## Tipo 3 — Unexpected Outcome Co-occurrence

> Outcomes que aparecen repetidamente en estudios de una intervencion
> pero NO son outcomes esperados en PCOS.
> Pueden indicar mecanismos pleiotropicos no estudiados.

### [T3] letrozole (5 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| fasting insulin | 2 |
| ovarian morphology | 2 |
| estrous cycle regularity | 2 |

### [T3] carboxymethylcellulose (cmc) solution (2 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| fasting insulin | 2 |

### [T3] curcumin (2 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| serum insulin | 2 |

### [T3] dietary intervention (6 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| triglycerides | 2 |
| fasting insulin | 2 |
| ovarian morphology | 2 |

### [T3] ivf (2 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| miscarriage rate | 2 |

### [T3] probiotics (2 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| total cholesterol | 2 |

### [T3] myo-inositol (4 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| fertility | 2 |

### [T3] exercise (13 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| body composition | 2 |
| androgen levels | 2 |
| free androgen index (fai) | 2 |

### [T3] lifestyle intervention (10 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| free androgen index (fai) | 2 |
| menstrual cycles | 2 |

### [T3] metformin (20 estudios)

| Outcome inesperado | N estudios donde aparece |
|---|---|
| fasting insulin | 3 |
| ovarian hyperstimulation syndrome (ohss) | 2 |
| estrous cycle regularity | 2 |

## Tipo 6 — Temporal Anomaly (evidencia creciente o no-replicacion)

> Misma intervencion, tasa favorable muy diferente en estudios antiguos vs recientes.
> 'rising': evidencia convergente — cada vez mas estudios lo confirman.
> 'falling': no-replicacion — exito inicial no se sostiene en trials mas grandes/nuevos.
> Umbral: diferencia >= 25pp entre eras, >= 2 estudios en cada era.

_No se detectaron anomalias temporales. Puede indicar pocos estudios por intervencion o distribucion uniforme en el tiempo._
---

## Tipo 7 — Contradiction Analysis (misma intervencion, efectos opuestos)

> Intervenciones con estudios TANTO favorables COMO desfavorables.
> El detector busca el diferenciador estructural: BMI, etnia, tipo de estudio, año.
> Un diferenciador fuerte = hipotesis mecanistica sobre en quien funciona.

_No se detectaron contradicciones con los umbrales actuales._
---

## Tipo 8 — KG Convergence (hipótesis mecanísticas emergentes)

> Caminos de DOS SALTOS en el grafo de mecanismos donde AMBOS saltos
> están confirmados por >= 2 papers independientes.
> A --[r1]--> B --[r2]--> C  donde A=intervención, B=mecanismo, C=endpoint PCOS.
> Ningún paper dice 'A afecta C vía B' — es una hipótesis emergente del grafo.

### [T8] metformin → insulin resistance → pcos
- **Hop 1:** `metformin` --[improves]--> `insulin resistance` | 7 papers | conf avg=0.886
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 55.912  _(= 7 × 9 × avg_conf)_
- **Hipótesis emergente:** _metformin improves insulin resistance (7 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: metformin modula pcos vía insulin resistance_

  Papers hop 1: 10.1177/2042018820938305, 10.7759/cureus.27689, 10.3389/fendo.2021.701590
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] tyg-bmi → insulin resistance → pcos
- **Hop 1:** `tyg-bmi` --[indicates]--> `insulin resistance` | 3 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 24.152  _(= 3 × 9 × avg_conf)_
- **Hipótesis emergente:** _tyg-bmi indicates insulin resistance (3 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: tyg-bmi modula pcos vía insulin resistance_

  Papers hop 1: 10.2147/ijwh.s387942, 10.3390/medicina62020291, 10.1186/s12884-024-07131-5
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] metformin → insulin resistance → hyperandrogenism
- **Hop 1:** `metformin` --[improves]--> `insulin resistance` | 7 papers | conf avg=0.886
- **Hop 2:** `insulin resistance` --[associated_with]--> `hyperandrogenism` | 4 papers | conf avg=0.825
- **Score de convergencia:** 23.954  _(= 7 × 4 × avg_conf)_
- **Hipótesis emergente:** _metformin improves insulin resistance (7 papers), y insulin resistance associated_with hyperandrogenism (4 papers) → hipótesis: metformin modula hyperandrogenism vía insulin resistance_

  Papers hop 1: 10.1177/2042018820938305, 10.7759/cureus.27689, 10.3389/fendo.2021.701590
  Papers hop 2: 10.3389/fendo.2022.808898, 10.7759/cureus.44493, 10.1007/s13668-024-00601-4

### [T8] obesity → insulin resistance → pcos
- **Hop 1:** `obesity` --[increases]--> `insulin resistance` | 3 papers | conf avg=0.867
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 23.706  _(= 3 × 9 × avg_conf)_
- **Hipótesis emergente:** _obesity increases insulin resistance (3 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: obesity modula pcos vía insulin resistance_

  Papers hop 1: 10.7570/jomes24035, 10.33549/physiolres.934521, 10.1155/carm/5825601
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] insulin resistance → hyperandrogenism → pcos
- **Hop 1:** `insulin resistance` --[associated_with]--> `hyperandrogenism` | 4 papers | conf avg=0.825
- **Hop 2:** `hyperandrogenism` --[associated_with]--> `pcos` | 5 papers | conf avg=0.9
- **Score de convergencia:** 17.25  _(= 4 × 5 × avg_conf)_
- **Hipótesis emergente:** _insulin resistance associated_with hyperandrogenism (4 papers), y hyperandrogenism associated_with pcos (5 papers) → hipótesis: insulin resistance modula pcos vía hyperandrogenism_

  Papers hop 1: 10.3389/fendo.2022.808898, 10.7759/cureus.44493, 10.1007/s13668-024-00601-4
  Papers hop 2: 10.1038/s41572-024-00511-3, 10.3390/life12121974, 10.1016/j.lfs.2021.119753

### [T8] hyperandrogenemia → insulin resistance → pcos
- **Hop 1:** `hyperandrogenemia` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 16.101  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _hyperandrogenemia associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: hyperandrogenemia modula pcos vía insulin resistance_

  Papers hop 1: 10.3390/ijms24043140, 10.3390/jcm10040829
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] oxidative stress → insulin resistance → pcos
- **Hop 1:** `oxidative stress` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 16.101  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _oxidative stress associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: oxidative stress modula pcos vía insulin resistance_

  Papers hop 1: 10.1515/bmc-2022-0038, 10.1007/s11010-024-05113-x
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] glp-1 receptor agonists → insulin resistance → pcos
- **Hop 1:** `glp-1 receptor agonists` --[improves]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 16.101  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _glp-1 receptor agonists improves insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: glp-1 receptor agonists modula pcos vía insulin resistance_

  Papers hop 1: 10.17219/acem/151695, 10.1177/20420188251383064
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] myo-inositol → insulin resistance → pcos
- **Hop 1:** `myo-inositol` --[reduces]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 16.101  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _myo-inositol reduces insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: myo-inositol modula pcos vía insulin resistance_

  Papers hop 1: 10.1155/2020/6276187, 10.1007/s11033-025-10553-9
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] shbg → insulin resistance → pcos
- **Hop 1:** `shbg` --[indicates]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 16.101  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _shbg indicates insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: shbg modula pcos vía insulin resistance_

  Papers hop 1: 10.3390/biomedicines14010187, 10.3390/medicina62020291
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] homa-ir → insulin resistance → pcos
- **Hop 1:** `homa-ir` --[indicates]--> `insulin resistance` | 2 papers | conf avg=0.9
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 16.101  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _homa-ir indicates insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: homa-ir modula pcos vía insulin resistance_

  Papers hop 1: 10.3390/medicina62020291, 10.1186/s12884-024-07131-5
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] prolactin → insulin resistance → pcos
- **Hop 1:** `prolactin` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.85
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 15.651  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _prolactin associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: prolactin modula pcos vía insulin resistance_

  Papers hop 1: 10.3389/fendo.2021.571229, 10.1038/s41598-025-98028-6
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] subclinical hypothyroidism → insulin resistance → pcos
- **Hop 1:** `subclinical hypothyroidism` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.85
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 15.651  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _subclinical hypothyroidism associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: subclinical hypothyroidism modula pcos vía insulin resistance_

  Papers hop 1: 10.3389/fendo.2021.734638, 10.7759/cureus.8142
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] fetuin-a → insulin resistance → pcos
- **Hop 1:** `fetuin-a` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.85
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 15.651  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _fetuin-a associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: fetuin-a modula pcos vía insulin resistance_

  Papers hop 1: 10.1186/s12902-020-0538-1, 10.3389/fendo.2020.568500
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] ros → insulin resistance → pcos
- **Hop 1:** `ros` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.85
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 15.651  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _ros associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: ros modula pcos vía insulin resistance_

  Papers hop 1: 10.1016/j.intimp.2026.116251, 10.1016/j.intimp.2026.116375
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] probiotics → insulin resistance → pcos
- **Hop 1:** `probiotics` --[improves]--> `insulin resistance` | 2 papers | conf avg=0.85
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 15.651  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _probiotics improves insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: probiotics modula pcos vía insulin resistance_

  Papers hop 1: 10.1016/j.prostaglandins.2025.106989, 10.1139/cjpp-2025-0095
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] gut microbiota → insulin resistance → pcos
- **Hop 1:** `gut microbiota` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.8
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 15.201  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _gut microbiota associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: gut microbiota modula pcos vía insulin resistance_

  Papers hop 1: 10.3390/metabo13010129, 10.3389/fendo.2022.933110
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] vitamin d → insulin resistance → pcos
- **Hop 1:** `vitamin d` --[improves]--> `insulin resistance` | 2 papers | conf avg=0.75
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 14.751  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _vitamin d improves insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: vitamin d modula pcos vía insulin resistance_

  Papers hop 1: 10.3390/jcm11154509, 10.3390/metabo11020116
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] sirt1 → insulin resistance → pcos
- **Hop 1:** `sirt1` --[inhibits]--> `insulin resistance` | 2 papers | conf avg=0.75
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 14.751  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _sirt1 inhibits insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: sirt1 modula pcos vía insulin resistance_

  Papers hop 1: 10.1007/s00210-025-04517-w, 10.1016/j.biopha.2025.118361
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

### [T8] foxo1 → insulin resistance → pcos
- **Hop 1:** `foxo1` --[associated_with]--> `insulin resistance` | 2 papers | conf avg=0.7
- **Hop 2:** `insulin resistance` --[associated_with]--> `pcos` | 9 papers | conf avg=0.889
- **Score de convergencia:** 14.301  _(= 2 × 9 × avg_conf)_
- **Hipótesis emergente:** _foxo1 associated_with insulin resistance (2 papers), y insulin resistance associated_with pcos (9 papers) → hipótesis: foxo1 modula pcos vía insulin resistance_

  Papers hop 1: 10.1016/j.omtn.2020.12.008, 10.3389/fphys.2021.649295
  Papers hop 2: 10.1186/s13048-025-01621-6, 10.1016/j.isci.2024.108783, 10.3390/life13041056

---

## Tipo 9 — Secondary Biomarker Movement (señales pleiotropicas)

> En estudios FAVORABLES, esta intervencion mejora marcadores fuera de PCOS.
> Diferencia de Tipo 3: solo cuenta estudios favorables y agrupa por categoria clinica.
> Señala beneficios pleiotropicos: cardiovascular, inflamacion, microbioma, etc.

### [T9] probiotics — top: cardiovascular
- Estudios favorables: 1 | **Score: 5.0**
- In 1 favorable studies, probiotics consistently affects cardiovascular markers (total cholesterol, ldl-c) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 5 | total cholesterol, ldl-c |

### [T9] cinnamon — top: cardiovascular
- Estudios favorables: 1 | **Score: 4.0**
- In 1 favorable studies, cinnamon consistently affects cardiovascular markers (total cholesterol, triglycerides) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 4 | total cholesterol, triglycerides |

### [T9] chromium — top: cardiovascular
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, chromium consistently affects cardiovascular markers (triglycerides, ldl cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 2 | triglycerides, ldl cholesterol |

### [T9] curcumin — top: cardiovascular
- Estudios favorables: 2 | **Score: 2.0**
- In 2 favorable studies, curcumin consistently affects cardiovascular markers (total cholesterol, ldl-cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 4 | total cholesterol, ldl-cholesterol |

### [T9] l-carnitine — top: cardiovascular
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, l-carnitine consistently affects cardiovascular markers (triglycerides, ldl cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 2 | triglycerides, ldl cholesterol |

### [T9] rosiglitazone — top: cardiovascular
- Estudios favorables: 1 | **Score: 2.0**
- In 1 favorable studies, rosiglitazone consistently affects cardiovascular markers (total cholesterol, triglycerides) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 2 | total cholesterol, triglycerides |

### [T9] metformin — top: cardiovascular
- Estudios favorables: 10 | **Score: 1.6**
- In 10 favorable studies, metformin consistently affects cardiovascular markers (high-density lipoprotein (hdl) cholesterol, low-density lipoprotein (ldl) cholesterol) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 7 | high-density lipoprotein (hdl) cholesterol, low-density lipoprotein (ldl) cholesterol |
| inflammation | 5 | il-1β, il-6 |
| liver | 4 | fasting insulin, central and hepatic fat |

### [T9] clomiphene citrate — top: cardiovascular
- Estudios favorables: 3 | **Score: 1.33**
- In 3 favorable studies, clomiphene citrate consistently affects cardiovascular markers (total cholesterol, triglycerides) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| cardiovascular | 4 | total cholesterol, triglycerides |

### [T9] spironolactone — top: liver
- Estudios favorables: 2 | **Score: 1.0**
- In 2 favorable studies, spironolactone consistently affects liver markers (central and hepatic fat, fasting insulin) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| liver | 2 | central and hepatic fat, fasting insulin |

### [T9] oral contraceptives — top: liver
- Estudios favorables: 3 | **Score: 0.67**
- In 3 favorable studies, oral contraceptives consistently affects liver markers (fasting insulin, central and hepatic fat) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| liver | 2 | fasting insulin, central and hepatic fat |

### [T9] exercise — top: mental_health
- Estudios favorables: 7 | **Score: 0.43**
- In 7 favorable studies, exercise consistently affects mental_health markers (psychological well-being, anxiety (hads-a)) alongside primary PCOS endpoints — pleiotropic benefit signal.

| Categoria | N hits | Outcomes ejemplo |
|---|---|---|
| mental_health | 3 | psychological well-being, anxiety (hads-a) |

---

