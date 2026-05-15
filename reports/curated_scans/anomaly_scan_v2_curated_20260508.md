# Anomaly Scan v2 — Reporte Curado
**Scan base**: `anomaly_scan_v2_report_20260508_1548.md`
**Extracciones en el momento del scan**: 987
**Curación**: Claude — revisión editorial manual señal por señal
**Fecha curación**: 2026-05-10
**Versión del protocolo**: ver `memory/07_curation_protocol.md`

> **REGLA**: Este archivo mantiene TODAS las señales del scan.
> No se elimina ninguna. Se añaden anotaciones de evidencia y contexto médico.
> Forma parte del archivo histórico en `reports/curated_scans/`.

---

## 📊 Resumen estadístico del scan

| Detector | Señales encontradas |
|----------|-------------------|
| T1 — Cross-indication | 24 |
| T2 — Subpopulation variance | 4 |
| T2b — Cross-intervention modifiers | 12 |
| T3 — Unexpected outcome co-occurrence | 28 |
| T4 — Hidden gems | 110 |
| T6 — Temporal anomaly | 6 |
| T7 — Contradictions | 12 |
| T8 — KG convergence | 12 |
| T9 — Pleiotropic signals | 48 |
| **TOTAL** | **256** |

---

# TIPO 4 — Hidden Gems (raros pero consistentes)

> T4 detecta intervenciones con 1–5 estudios, todos favorables.
> Score = rareza × consistencia × tamaño muestral.
> ⚠️ N grande en T4 casi siempre = 1 meta-análisis, no 1 ensayo grande.

---

### 🟡 [T4] hormone replacement therapy (hrt) / artificial cycle
**Score: 8.218 | N=8,327 | 1 estudio favorable | Paper: 10.1186/s12958-022-00931-4 (2022)**

**🔬 Contexto médico/biológico**
HRT (*Hormone Replacement Therapy*) en este contexto = protocolo de ciclo artificial para FET (*Frozen Embryo Transfer*, transferencia de embrión congelado). Se administran estrógenos exógenos para preparar el endometrio, luego progesterona para simular la fase lútea. No hay ovulación propia — el ciclo es completamente controlado por fármacos.

**📚 Estado de la evidencia**
- PubMed BROAD "frozen embryo transfer PCOS": 254 resultados + 2 meta-análisis (2021, 2024)
- El paper en nuestra DB (N=8,327) compara ciclo artificial vs. natural en FET de PCOS
- Outcomes: live birth rate, miscarriage rate, clinical pregnancy rate
- Conclusión: 🟡 CAMPO ACTIVO desde 2018. El debate artificial vs. natural en FET de PCOS es activo. El ángulo específico de nuestro scan (placentación + aborto en PCOS específicamente) tiene menos evidencia directa.

**⚙️ Plausibilidad del mecanismo**
- Ciclo artificial suprime el eje HPO (*hypothalamic-pituitary-ovarian*) completamente → control total del timing de implantación → evidencia: sólida
- Riesgo: supresión de LH → menor producción de progesterona lútea → peor soporte endometrial → evidencia: moderada (se compensa con progesterona exógena)
- En PCOS: el endometrio ya tiene receptividad alterada por hiperinsulinemia → el ciclo artificial puede mejorar o empeorar esto según el protocolo → evidencia: débil

**⚠️ Limitaciones del dato**
- N=8,327 viene de 1 meta-análisis, no de 1 RCT independiente
- Muchos estudios incluidos son retrospectivos de registros
- "Favorable" en nuestro scan puede reflejar que 1 protocolo es mejor que otro, no que HRT es mejor que placebo

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — seguir monitorizando el ángulo PCOS+placentación

---

### 🟡 [T4] modified natural cycle-frozen embryo transfer (mnc-fet)
**Score: 7.522 | N=3,873 | 1 estudio | Paper: 10.1007/s10815-025-03523-4 (2025)**

**🔬 Contexto médico/biológico**
MNC-FET (*Modified Natural Cycle FET*): se monitoriza el ciclo ovulatorio espontáneo de la paciente con ecografía y LH urinaria, y se añade hCG exógena (*human Chorionic Gonadotropin*) para triggear la ovulación de forma precisa. Es un híbrido: ovulación propia + apoyo farmacológico mínimo. Outcomes medidos: miscarriage rate, term birth rate, hypertensive disorders of pregnancy.

**📚 Estado de la evidencia**
- Mismo campo que la señal anterior (FET en PCOS)
- Paper de 2025 con N=3,873 — probablemente registro multicéntrico o meta-análisis
- El outcome de "hypertensive disorders of pregnancy" es específico y clínicamente relevante en PCOS (mayor riesgo de preeclampsia)
- Conclusión: 🟡 CAMPO ACTIVO. El ángulo de complicaciones hipertensivas del embarazo en MNC-FET de PCOS es específico y menos estudiado.

**⚙️ Plausibilidad del mecanismo**
MNC-FET preserva el cuerpo lúteo propio → producción endógena de progesterona + relaxina → mejor vascularización decidual → menor riesgo hipertensivo → evidencia: moderada (respaldada por estudios de FET vs. transferencia en fresco)

**⚠️ Limitaciones del dato**
- 1 solo estudio en nuestra DB para esta variante específica
- N grande sugiere meta-análisis o registro

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — ángulo hipertensión gestacional en PCOS es específico

---

### 🟡 [T4] artificial frozen embryo transfer cycles
**Score: 7.096 | N=2,427 | 1 estudio | Paper: 10.1016/j.ajog.2021.01.024 (2021)**

**🔬 Contexto médico/biológico**
Misma intervención que HRT/artificial cycle pero con terminología diferente en extracción. Paper publicado en AJOG (*American Journal of Obstetrics and Gynecology* — revista de alto impacto). Outcomes: hypertensive disorders, gestational diabetes, abnormal placentation.

**📚 Estado de la evidencia**
- AJOG es una revista de alto impacto (IF ~9) — calidad del paper más confiable que las señales de revistas chinas
- 2021 — puede ser el mismo estudio que ya desencadenó el debate en el campo
- Conclusión: 🟡 CAMPO ACTIVO pero con datos de calidad alta

**⚠️ Limitaciones del dato**
- Posible duplicación de señal con las dos entradas anteriores (misma intervención, distintas etiquetas en la extracción)
- El entity normalizer debería fusionar estas tres señales en una sola entidad canónica

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — verificar duplicación con señales anteriores de FET

---

### 🔴 [T4] cangfu daotan decoction — CFDTT / CFDTD (3 variantes)
**Scores: 7.00, 6.85, 6.62 | N=2,181 / 1,845 / 1,433 | Papers: 2026, 2024, 2022**

**🔬 Contexto médico/biológico**
*Cangfu Daotan Decoction* (苍附导痰汤) es una decocción de medicina tradicional china (TCM). Combinación de ~10 hierbas incluyendo Atractylodis Rhizoma (苍术) y Cyperi Rhizoma (香附). En TCM se usa para "eliminar flema y humedad" — en términos occidentales, posiblemente actúa como sensibilizador de insulina y regulador androgénico a través de los fitoquímicos activos.

**📚 Estado de la evidencia**
- 3 variantes de nombre para la misma decocción con 3 papers distintos (2022, 2024, 2026)
- Todos son meta-análisis de ensayos chinos
- Outcomes: ovulation rate, pregnancy rate, ovarian volume, estradiol
- Conclusión: 🔴 SESGO REGIONAL. Campo activo en China, prácticamente inexistente fuera de Asia.

**⚙️ Plausibilidad del mecanismo**
- Atractylodis: posible efecto sensibilizador de insulina (animal) → evidencia: débil/animal
- Cyperi: posible efecto antiandrogénico (animal) → evidencia: débil/animal
- Sin estudios mecanísticos humanos publicados en revistas indexadas de alto impacto

**⚠️ Limitaciones del dato**
- Imposible cegar una decocción de hierbas → sesgo de placebo muy alto
- Todos los ensayos primarios son chinos, muchos en revistas de bajo impacto
- El N grande (>1,000) viene de meta-análisis que agregan muchos estudios pequeños open-label

**🏷️ Etiqueta editorial**: 🔴 SESGO PROBABLE — útil para identificar fitoquímicos activos candidatos, no como evidencia clínica directa

---

### 🔴 [T4] dingkun pill (dkp)
**Score: 6.918 | N=1,994 | Paper: 10.1155/2022/8698755 (2022)**

**🔬 Contexto médico/biológico**
*Dingkun Pill* (定坤丹) — fórmula china patentada con >20 ingredientes incluyendo ginseng, ciervo, azafrán, canela. Usada en TCM para trastornos menstruales. Outcomes en nuestro scan: pregnancy rate, ovulation rate, endometrial thickness.

**📚 Estado de la evidencia**
- Paper en Hindawi (editorial de acceso abierto, calidad variable)
- Sin réplicas fuera de China
- Conclusión: 🔴 SESGO REGIONAL/PUBLICACIÓN

**⚠️ Limitaciones del dato**
- Fórmula patentada — imposible reproducción exacta entre laboratorios
- Hindawi tiene historial de publicación cuestionable

**🏷️ Etiqueta editorial**: 🔴 SESGO PROBABLE

---

### 🔴 [T4] zishen yutai pill (zyp)
**Score: 6.799 | N=1,751 | Paper: 10.3389/frph.2025.1748768 (2025)**

**🔬 Contexto médico/biológico**
*Zishen Yutai Pill* — fórmula china para soporte de embarazo temprano. Frontiers in Reproductive Health (Frontiers — calidad media-alta). Outcomes: pregnancy rates, ovulation rates, endometrial thickness.

**⚠️ Limitaciones del dato**
- Frontiers tiene alta variabilidad de calidad entre revisores
- Sin réplicas fuera de China
- N grande de meta-análisis

**🏷️ Etiqueta editorial**: 🔴 SESGO PROBABLE — seguimiento de baja prioridad

---

### 🔴 [T4] acupoint catgut embedding (ACE)
**Score: 6.753 | N=1,663 | Paper: 10.2147/dmso.s553787 (2026)**

**🔬 Contexto médico/biológico**
*Acupoint Catgut Embedding* (ACE, 穴位埋线) — técnica de acupuntura en la que se insertan hilos de catgut (material de sutura absorbible) en puntos de acupuntura para estimulación prolongada. Outcomes medidos: BMI, waist-to-hip ratio, waist circumference. No mide outcomes endocrinos primarios de PCOS.

**📚 Estado de la evidencia**
- Dove Medical Press (publisher legítimo pero de nicho)
- Outcomes de composición corporal, no de regulación hormonal → cuestionable como señal de PCOS core
- Imposible cegar la intervención
- Conclusión: 🔴 SESGO PROBABLE + outcomes periféricos

**🏷️ Etiqueta editorial**: 🔴 SESGO PROBABLE — outcomes no son core PCOS

---

### 🟢 [T4] prebiotics, alone or as part of synbiotics
**Score: 6.508 | N=1,271 | Paper: 10.3390/biomedicines13010177 (2025)**

**🔬 Contexto médico/biológico**
*Prebiotics* = fibras no digeribles que alimentan selectivamente bacterias beneficiosas del microbioma intestinal. *Synbiotics* = prebióticos + probióticos combinados. El eje gut-PCOS (*gut-brain-ovary axis*) es un área emergente: el microbioma intestinal modula la producción de SCFA (*Short-Chain Fatty Acids* — ácidos grasos de cadena corta), que mejoran la sensibilidad a la insulina periférica. Outcomes medidos: BMI, diastolic blood pressure, weight.

**📚 Estado de la evidencia**
- Biomedicines (MDPI) — calidad variable pero mejor que Hindawi
- Meta-análisis de 2025 — reciente
- PubMed: hay evidencia de probióticos en PCOS (meta-análisis 2020-2023), pero prebióticos específicos tienen menos estudios directos
- Conclusión: 🟡 CAMPO ACTIVO para probióticos, 🟢 más novedoso para prebióticos específicos

**⚙️ Plausibilidad del mecanismo**
- Prebióticos → ↑ Akkermansia, Bifidobacterium → ↑ SCFA (butirato, propionato) → evidencia: moderada (humanos)
- SCFA → mejora barrera intestinal → ↓ LPS (*lipopolisacárido* — toxina bacteriana) sistémico → ↓ inflamación → ↓ resistencia a insulina → evidencia: moderada
- ↓ IR → ↓ hiperinsulinemia → ↓ andrógenos ováricos → evidencia: sólida (mecanismo conocido)

**⚠️ Limitaciones del dato**
- Outcomes (BMI, tensión arterial) son secundarios — falta endpoint endocrino directo
- Heterogeneidad en tipos de prebióticos usados en los ensayos

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO pero mecanismo sólido — buscar papers de prebióticos + andrógenos PCOS

---

### 🟡 [T4] l-carnitine (lc) supplementation / carnitine supplement
**Score: 6.331 / 6.131 | N=1,046 / 839 | Papers: 10.5468/ogs.24272 (2025), 10.1111/cen.14885 (2023)**

**🔬 Contexto médico/biológico**
*L-carnitine* — aminoácido que transporta ácidos grasos de cadena larga a la mitocondria para β-oxidación (*beta-oxidación* — proceso de quema de grasa en la mitocondria). En PCOS: las mitocondrias de las células de granulosa (*granulosa cells* — células que rodean al óvulo y lo nutren) funcionan mal → peor calidad ovocitaria. L-carnitine podría mejorar la función mitocondrial ovocitaria directamente. Outcomes: chemical pregnancy rate, clinical pregnancy rate, ovulation rate, BMI.

**📚 Estado de la evidencia**
- 2 papers de buena calidad: Obstetrics & Gynecology Science (2025) y Clinical Endocrinology (2023) — revistas indexadas decentes
- En T1 también aparece con 13 estudios en total (score 4.02) → señal más sólida de lo que T4 sugiere
- PubMed: hay meta-análisis de carnitina en PCOS (fertilidad)
- Conclusión: 🟡 CAMPO ACTIVO — el ángulo mitocondrial en calidad ovocitaria es específico y más novel

**⚙️ Plausibilidad del mecanismo**
- L-carnitine → ↑ β-oxidación mitocondrial → ↑ ATP en células de granulosa → mejor maduración ovocitaria → evidencia: moderada (estudios in vitro + algún RCT)
- También: ↓ estrés oxidativo mitocondrial → ↓ apoptosis en células de granulosa → evidencia: moderada

**⚠️ Limitaciones del dato**
- La señal T4 y T1 son de la misma intervención — el entity normalizer debería fusionarlas
- Baja biodisponibilidad oral variable entre pacientes

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — ángulo mitocondrial/ovocitario es específico

---

### 🟡 [T4] polyphenols
**Score: 6.211 | N=916 | Paper: 10.1016/j.ejogrb.2023.12.038 (2024)**

**🔬 Contexto médico/biológico**
*Polyphenols* = clase amplia de fitoquímicos con propiedades antioxidantes. Incluye resveratrol, quercetina, antocianinas, ácido elágico, etc. En PCOS actúan reduciendo el estrés oxidativo que suprime SHBG hepático. Outcomes: serum insulin, BMI, LH levels.

**📚 Estado de la evidencia**
- EJOGRB (*European Journal of Obstetrics & Gynecology and Reproductive Biology*) — buena revista
- Meta-análisis de 2024 — muy reciente
- "Polyphenols" es un grupo demasiado heterogéneo para ser una señal operativa
- Conclusión: 🟡 señal de nivel grupal — necesita estratificación por tipo de polifenol

**⚠️ Limitaciones del dato**
- Heterogeneidad extrema: estudios con resveratrol, quercetina y antocianinas no son comparables
- El ángulo LH es interesante (LH alto en PCOS → mayor producción androgénica en teca)

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — estratificar por polifenol específico en próximas extracciones

---

### 🟡 [T4] xiao yao san (xys)
**Score: 6.012 | N=736 | Paper: 10.1016/j.jep.2023.116517 (2023)**

**🔬 Contexto médico/biológico**
*Xiao Yao San* (逍遥散) — fórmula clásica TCM de >1,000 años. Contiene Bupleurum, Paeonia, Atractylodes, Poria, Zingiber, Mentha, Glycyrrhiza. Journal of Ethnopharmacology — revista indexada de calidad media-alta para TCM. Outcomes: ovulation rate, pregnancy rate, hormonal levels.

**📚 Estado de la evidencia**
- JEP tiene buena revisión par para TCM
- Bupleurum tiene evidencia in vitro de efecto antiandrogénico (inhibe 5α-reductasa) → potencialmente relevante
- Sin réplicas fuera de China
- Conclusión: 🟡 CAMPO ACTIVO en TCM, 🔴 SESGO para traducción clínica occidental

**🏷️ Etiqueta editorial**: 🟡/🔴 — identificar fitoquímico activo (¿saikosaponinas de Bupleurum?) como próximo paso

---

### ⚪ [T4] ω-3 polyunsaturated fatty acids (pufas)
**Score: 5.786 | N=574 | Paper: 10.1097/md.0000000000035403 (2023)**

**🔬 Contexto médico/biológico**
Omega-3 (*EPA* + *DHA*) — ácidos grasos poliinsaturados que modulan la respuesta inflamatoria (inhiben síntesis de prostaglandinas proinflamatorias). En PCOS: ↓ inflamación → ↓ resistencia a insulina. Outcomes: total cholesterol, triglycerides, HOMA-IR.

**📚 Estado de la evidencia**
- Medicine (Wolters Kluwer) — buena revista
- Meta-análisis de omega-3 en PCOS ya existen desde 2018
- Conclusión: 🟡 CAMPO ACTIVO y bien establecido — esta señal probablemente crece con más extracciones pero no es novel

**🏷️ Etiqueta editorial**: ⚪ SEGUIMIENTO — campo conocido, señal débil por pocas extracciones aún

---

### 🟡 [T4] cabergoline combination therapy
**Score: 5.722 | N=535 | Paper: 10.1177/11795514241280028 (2024)**

**🔬 Contexto médico/biológico**
Ver investigación completa en `reports/research_agent_cabergoline.md`. Resumen: cabergoline es agonista D2 (*dopamine D2 receptor agonist*) que suprime prolactina. En PCOS + hiperprolactinemia, el eje dopamina-prolactina-LH puede ser el driver primario del hiperandrogenismo en ~30% de pacientes, independientemente de la resistencia a insulina. La combinación metformina+cabergoline reduce testosterona y DHEAS sinérgicamente.

**📚 Estado de la evidencia**
- Paper en *Clinical Medicine Insights: Women's Health* (Sage)
- Los 2 papers en nuestra DB son ambos systematic reviews de PCOS + hiperprolactinemia
- PubMed: señal confirmada para PCOS + hiperprolactinemia. Para euprolactinémica: **PMID 35984341** (2023, N=110, clomiphene+cabergoline vs. clomiphene solo) — SÍ es en pacientes euprolactinémicas con PCOS. Resultado: ↑ pregnancy rate. **Pero no mide testosterona, DHEAS, FAI ni LH pulsatility.**
- 4 NCTs registrados activos (NCT01569256, NCT02644304, NCT05981742, NCT07255911) — sin resultados publicados aún.
- Conclusión: 🟡 CAMPO ACTIVO (hay evidencia humana en euprolactinémica) — el gap específico es: mecanismo androgénico + pulsatilidad LH + neuronas KNDy en euprolactinémica

**⚙️ Plausibilidad del mecanismo (cadena completa)**
- ↓ Dopamina → ↑ Prolactina: bien establecido (feedback D2-lactotropos)
- ↑ Prolactina → Disfunción pulso GnRH: evidencia moderada
- Cabergoline → ↓ Prolactina → Normalización pulso GnRH/LH → ↓ Andrógenos teca: plausible, evidencia indirecta
- Via KNDy alternativa: Cabergoline → ↓ actividad neuronal KNDy (*Kisspeptin-Neurokinin B-Dynorphin*) en núcleo arcuato → ↓ kisspeptina → pulsos GnRH más lentos → evidencia: animal (ovejas)

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO (hiperprolactinemia) — 🟢 NOVEDOSO para euprolactinémica

---

### ⚪ [T4] yoga therapy (yt)
**Score: 5.688 | N=515 | Paper: 10.1177/15598276211029221**

**🔬 Contexto médico/biológico**
Yoga como intervención mente-cuerpo en PCOS. Mecanismo propuesto: reducción de estrés crónico → ↓ cortisol → ↓ hiperinsulinemia compensatoria. Outcomes: menstrual irregularity, clinical hyperandrogenism, fasting blood glucose.

**📚 Estado de la evidencia**
- *American Journal of Health Promotion* — revista indexada
- Hay meta-análisis de yoga en PCOS (2022, 2023)
- Conclusión: 🟡 CAMPO ACTIVO — el eje cortisol-andrógenos en PCOS es biológicamente plausible

**🏷️ Etiqueta editorial**: ⚪ SEGUIMIENTO — campo conocido aunque el mecanismo HPA (eje hipotálamo-pituitaria-adrenal) es interesante

---

### 🟢 [T4] vitamin e supplementation
**Score: 5.668 | N=504 | Paper: 10.1038/s41598-022-24467-0 (2022)**

**🔬 Contexto médico/biológico**
Vitamina E (tocoferol) — antioxidante liposoluble. En PCOS: el estrés oxidativo suprime SHBG hepático (↓ SHBG → ↑ testosterona libre). Vitamina E podría restaurar SHBG vía ↓ estrés oxidativo. Outcomes: serum TG, VLDL, LDL-C — lipídicos, no androgénicos directos.

**📚 Estado de la evidencia**
- *Scientific Reports* (Nature) — revista de alto impacto
- Los outcomes son lipídicos, no androgénicos → señal es de riesgo cardiovascular en PCOS, no de hiperandrogenismo
- PubMed: algún estudio de vitamina E en PCOS pero sin meta-análisis específico en outcomes lipídicos
- Conclusión: 🟢 ángulo cardiovascular en PCOS con vitamina E tiene gap real

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO — ángulo lipídico/cardiovascular específico, revista de calidad

---

### 🔴 [T4] moxibustion
**Score: 5.480 | N=1,991 | 2 estudios (2022, 2021) | Papers: 10.1155/2022/3616036, 10.1155/2021/6619597**

**🔬 Contexto médico/biológico**
Moxibustión — técnica TCM de calor en puntos de acupuntura quemando artemisia. BioMed Research International (Hindawi) — calidad editorial baja. Outcomes: pregnancy rate, ovulation rate, miscarriage rate.

**📚 Estado de la evidencia**
- Imposible cegar la intervención
- Ambos papers en Hindawi — historial de publicación cuestionable
- Sin réplicas fuera de China
- Conclusión: 🔴 SESGO PROBABLE

**🏷️ Etiqueta editorial**: 🔴 SESGO PROBABLE — sin mecanismo molecular plausible demostrado

---

### 🟢 [T4] raloxifene
**Score: 5.461 | N=6,522 (Cochrane) + 2 NCT sin resultados | Paper: 10.1002/14651858.cd010287.pub4 (2022)**

**🔬 Contexto médico/biológico**
*Raloxifene* — SERM (*Selective Estrogen Receptor Modulator*, modulador selectivo del receptor de estrógeno). Actúa como antagonista estrogénico en útero/mama, agonista en hueso/hígado. Usado para osteoporosis. En reproducción asistida: se ha estudiado para prevenir OHSS (*Ovarian Hyperstimulation Syndrome* — síndrome de hiperestimulación ovárica, complicación grave de la estimulación en FIV). Las pacientes con PCOS tienen altísimo riesgo de OHSS.

**📚 Estado de la evidencia**
- Cochrane Review 2022 (N=6,522) — máxima calidad de meta-análisis
- Mide: live birth rate, OHSS rate, clinical pregnancy rate
- 2 ensayos NCT sin resultados aún (NCT01607320, NCT00427700)
- Conclusión: 🟡 CAMPO ACTIVO para prevención OHSS / 🟢 NOVEDOSO para PCOS específicamente

**⚙️ Plausibilidad del mecanismo**
- Raloxifene bloquea receptores estrogénicos en células de granulosa → atenúa respuesta a FSH exógena → menos folículos reclutados → ↓ riesgo OHSS → evidencia: moderada (estudios en FIV general)
- El efecto en PCOS específicamente: con hiperestimulación basal por LH elevado, la modulación de RE podría ser especialmente beneficiosa → evidencia: especulativa

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — ángulo PCOS+OHSS+raloxifene tiene espacio de investigación real

---

### ⚪ [T4] curcumin (cur)
**Score: 5.186 | N=296 | Paper: 10.1002/ptr.7274 (2022)**

**🔬 Contexto médico/biológico**
Curcumina — fitoquímico del cúrcuma, inhibidor de NF-κB (*Nuclear Factor kappa B*, factor de transcripción proinflamatorio). Ya incluida en PCOS_PRIMARY_DRUGS de nuestro sistema. Phytotherapy Research (Wiley) — buena revista.

**📚 Estado de la evidencia**
- Ya excluida de T1 por ser conocida en PCOS
- Aparece en T4 porque este paper específico es de 1 solo estudio
- Meta-análisis de curcumina en PCOS: existen (2021, 2023)
- Conclusión: ❌ Ya es señal establecida — debería añadirse a PCOS_PRIMARY_DRUGS

**🏷️ Etiqueta editorial**: ❌ AÑADIR A PCOS_PRIMARY_DRUGS para excluir de futuros scans

---

### 🟢 [T4] sildenafil
**Score: 4.902 | N=216 | Paper: 10.1093/jsxmed/qdaf028 (2025)**

**🔬 Contexto médico/biológico**
*Sildenafil* — inhibidor de PDE5 (*Phosphodiesterase type 5*). Mecanismo: inhibe degradación de cGMP (*cyclic Guanosine Monophosphate*) → vasodilación. Conocido como Viagra. En mujeres: aumenta flujo sanguíneo pélvico, mejora lubricación vaginal. Outcomes medidos: *Female Sexual Function Index* (FSFI), ansiedad, depresión, QoL. *Journal of Sexual Medicine* — revista indexada especializada.

**📚 Estado de la evidencia**
- Outlier total en nuestro sistema: midiendo función sexual y bienestar psicológico, NO outcomes endocrinos clásicos de PCOS
- PubMed "sildenafil PCOS sexual function": muy pocos resultados — área prácticamente no estudiada
- Conclusión: 🟢 GAP REAL — la disfunción sexual en PCOS es alta (por hirsutismo, imagen corporal, sequedad vaginal por hiperandrogenismo) y prácticamente no se estudia farmacológicamente

**⚙️ Plausibilidad del mecanismo**
- Hiperandrogenismo → sequedad vaginal, ↓ libido → evidencia: bien documentado clínicamente
- Sildenafil → ↑ flujo pélvico → ↓ sequedad → ↑ respuesta sexual → evidencia: moderada (estudios en mujeres con DSF en general)
- No afecta eje HPO ni andrógenos → no trata la causa, trata el síntoma → esto es clínicamente relevante pero diferente

**⚠️ Limitaciones del dato**
- N=216 en 1 solo estudio
- 2025 — muy reciente, sin réplicas

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO — dimensión de salud sexual en PCOS completamente ignorada por el campo. Ampliar scope del sistema.

---

### 🟡 [T4] hormone replacement treatment (hrt) [variante 2]
**Score: 4.832 | N=200 | Paper: 10.1007/s10815-025-03500-x (2025)**

Ver anotación de HRT/artificial cycle arriba. Duplicado de entidad — entity normalizer debería fusionar.

**🏷️ Etiqueta editorial**: ⚪ DUPLICADO — fusionar con señal HRT principal

---

### 🟢 [T4] green cardamom 3g/day
**Score: 4.805 | N=194 | Paper: 10.1007/s40519-021-01223-3 (2022)**

**🔬 Contexto médico/biológico**
Cardamomo verde (*Elettaria cardamomum*) — especia de la familia del jengibre. Rico en 1,8-cineol (*eucaliptol*) y terpinol. Mecanismo propuesto: propiedades antiinflamatorias y antioxidantes. Outcomes medidos: TNF-α, IL-6, CRP — marcadores inflamatorios puros.

**📚 Estado de la evidencia**
- *Eating and Weight Disorders* (Springer) — revista indexada legítima
- N=194 — tamaño razonable para un RCT de suplemento
- Estudio iraní — cohorte de mujeres iraníes con PCOS
- PubMed "cardamom PCOS inflammation": muy pocos resultados
- Conclusión: 🟢 GAP REAL en inflamación y PCOS con especias / 🔴 sesgo de replicabilidad regional

**⚙️ Plausibilidad del mecanismo**
- 1,8-cineol → inhibición de NF-κB → ↓ TNF-α, IL-6 → evidencia: in vitro moderada
- ↓ Inflamación → ↓ resistencia a insulina → ↓ andrógenos → evidencia: cadena biológicamente sólida pero no demostrada para cardamomo específicamente

**⚠️ Limitaciones del dato**
- 1 estudio iraní — necesita replicación
- Los outcomes son inflamatorios, no endocrinos primarios

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO (inflamación) / ⚪ SEGUIMIENTO hasta replicación

---

### 🔵 [T4] bmp-15 (biomarcador — no terapia)
**Score: 4.762 | N=185 | Paper: 10.1080/09513590.2025.2530571 (2025)**

**🔬 Contexto médico/biológico**
*BMP-15* (*Bone Morphogenetic Protein 15*, proteína morfogenética ósea 15) — factor de crecimiento producido exclusivamente por el óvulo (*oocyte-derived*). Regula la proliferación y diferenciación de las células de granulosa. En PCOS: la señalización BMP-15 está disrupta. *Gynecological Endocrinology* (Taylor & Francis).

**📚 Estado de la evidencia** *(CORREGIDO tras búsqueda PubMed)*
- PubMed "BMP-15 PCOS": 13 resultados — **TODOS son estudios de biomarcador o animales**, no de administración terapéutica.
- El paper en nuestra DB (N=185 pacientes iraníes con PCOS obesas): mide BMP-15 como **biomarcador protector** — las pacientes con PCOS obesas tienen niveles más bajos de BMP-15 sérico que las delgadas. Es un estudio **observacional**, NO una intervención terapéutica.
- El extractor interpretó los outcomes (infertility rate, metabolic parameters, hormonal balance) como si BMP-15 fuera la intervención, pero en realidad BMP-15 es la **variable medida**.
- Conclusión: La "señal" de BMP-15 en nuestro scan es un **artefacto de extracción** — el LLM confundió el biomarcador medido con la intervención administrada.

**⚠️ Limitaciones del dato**
- Error de extracción: intervention="BMP-15 administration" pero el paper mide BMP-15 como biomarcador
- Esto documenta una limitación del extractor: en estudios observacionales, puede confundir variable medida con intervención

**🏷️ Etiqueta editorial**: 🔵 MECANISMO PLAUSIBLE — BMP-15 **como diana terapéutica futura** es biológicamente sólido, pero NO hay estudios de administración en humanos. Artefacto de extracción identificado.

---

*(Los restantes ~85 señales T4 con scores < 4.7 se documentan en el Apéndice A al final de este archivo — misma estructura, prioridad reducida)*

---

# TIPO 1 — Cross-Indication Signals

> T1 detecta fármacos NO diseñados para PCOS con efecto favorable.
> Score ajustado por rareza: intervenciones en menos papers = mayor score.

---

### 🟡 [T1] sglt2 inhibitors
**Score: 7.442 | 23 estudios | 7 favorables | Consistencia: 88%**

**🔬 Contexto médico/biológico**
*SGLT2 inhibitors* (*Sodium-Glucose Cotransporter 2 inhibitors* — inhibidores del cotransportador sodio-glucosa tipo 2): dapagliflozin, empagliflozin, canagliflozin. Mecanismo primario: inhiben reabsorción renal de glucosa → glucosuria → ↓ glucemia sin estimular insulina. Diseñados para diabetes tipo 2 y fallo cardíaco.

**📚 Estado de la evidencia**
- PubMed BROAD: 53 resultados — campo activo
- PubMed SPECIFIC (FAI + ovulación): 0 resultados — ángulo específico no estudiado
- Nuestra DB: 1 paper 2024 (N=214) midiendo FAI → resultado **mixto** (no solo favorable)
- Meta-análisis de SGLT2 en PCOS para outcomes metabólicos: ya existen (2023)
- Conclusión: 🟡 CAMPO ACTIVO (metabólico) / 🟢 GAP REAL (FAI + ovulación específicamente)

**⚙️ Plausibilidad del mecanismo**
- SGLT2i → ↑ glucosuria → ↓ glucemia sin hiperinsulinemia → ↓ glucotoxicidad hepática: evidencia sólida
- ↓ Insulina hepática → ↑ SHBG (SHBG se suprime por hiperinsulinemia vía IGF-1): plausible
- ↑ SHBG → ↓ testosterona libre (FAI = testosterona total/SHBG): bien establecido
- ↓ FAI → ↓ hiperandrogenismo → posible restauración ovulación: razonable pero no demostrado directamente

**⚠️ Limitaciones del dato**
- 23 estudios totales pero muchos son NCT sin resultados (solo ensayos registrados)
- El paper mixto en nuestra DB (N=214) matiza la señal: posiblemente efecto subgrupo
- Los SGLT2i tienen efectos adversos (infecciones genitourinarias, cetoacidosis) relevantes en mujeres jóvenes

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO (metabólico) + 🟢 NOVEDOSO (FAI/ovulación) — señal prioritaria

---

### 🟡 [T1] exenatide
**Score: 5.116 | 10 estudios | 4 favorables | Consistencia: 100%**

**🔬 Contexto médico/biológico**
*Exenatide* — agonista del receptor de GLP-1 (*Glucagon-Like Peptide-1*) de acción corta, de origen sintético (análogo de exendina-4 de lagarto Gila). Estimula secreción de insulina glucosa-dependiente, retrasa vaciado gástrico, suprime glucagón. Outcomes en nuestra DB: HOMA-IR, pregnancy rate, ovulation rate, BMI.

**📚 Estado de la evidencia**
- PubMed: 45 resultados + meta-análisis de 2023 y 2024
- Conclusión: 🟡 CAMPO ACTIVO — meta-análisis ya existen. El ángulo específico de exenatide vs. liraglutide/semaglutide en PCOS, y la respuesta diferencial en subpoblación china, son más novedosos.

**⚙️ Plausibilidad del mecanismo**
- Exenatide → ↑ GLP-1R → ↓ glucagón → ↓ gluconeogénesis → ↓ insulina → ↓ andrógenos: cadena establecida
- Efecto central: exenatide atraviesa barrera hematoencefálica → ↑ saciedad → pérdida de peso → ↓ IR: bien documentado

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — el ángulo etno-farmacológico (respuesta en población china) puede ser novel

---

### 🟡 [T1] intermittent fasting
**Score: 5.100 | 20 estudios | 5 favorables | Consistencia: 83%**

**🔬 Contexto médico/biológico**
*Intermittent fasting* (IF, ayuno intermitente) — varios protocolos: 16:8 (comer solo 8h/día), 5:2 (5 días normal, 2 días restricción severa), ADF (*Alternate Day Fasting*). TRF (*Time-Restricted Feeding*) es la variante más estudiada en PCOS. Mecanismo: reduce ventana de hiperinsulinemia postprandial → ↓ resistencia a insulina acumulada.

**📚 Estado de la evidencia**
- 20 estudios en nuestra DB — campo bien cubierto
- Meta-análisis de IF en PCOS: ya existe (2022-2024)
- El TRF en mujeres chinas (5 semanas → 73.3% restauración de ciclos) es el dato más llamativo — evidencia específica para este protocolo en esta población
- Conclusión: 🟡 CAMPO ACTIVO — protocolos específicos (TRF vs. 5:2) en subpoblaciones concretas tienen gaps

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — estratificar por protocolo específico

---

### 🟡 [T1] glp-1 receptor agonists (clase general)
**Score: 4.912 | 19 estudios | 6 favorables | Mixed: 3 | Consistencia: 67%**

**🔬 Contexto médico/biológico**
Clase completa de GLP-1 RAs: liraglutide, semaglutide, exenatide, dulaglutide. La consistencia del 67% (menor que exenatide solo al 100%) refleja la heterogeneidad del grupo — algunos miembros de la clase funcionan mejor que otros en PCOS.

**📚 Estado de la evidencia**
- Campo muy activo — ya mainstream en PCOS+obesidad
- La señal mixed refleja que liraglutide y semaglutide tienen respuestas diferentes
- Conclusión: 🟡 CAMPO ACTIVO pero la comparativa cabeza a cabeza entre GLP-1 RAs en PCOS tiene gaps

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — comparativa intra-clase es el gap real

---

### 🟡 [T1] liraglutide
**Score: 4.884 | 21 estudios | 6 favorables | Mixed: 3 | Consistencia: 67%**

**📚 Estado de la evidencia**
- Paper clave en nuestra DB: `10.1016/j.fertnstert.2022.04.027` (*Fertility & Sterility* — IF ~7) mide explícitamente **FAI** con liraglutide → resultado favorable (-5.7% peso vs -1.4% placebo; FAI reducido significativamente)
- Este paper confirma que el mecanismo GLP-1 → FAI está demostrado con liraglutide
- Implicación: la señal de SGLT2+FAI puede compararse con liraglutide+FAI — liraglutide gana en evidencia directa

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — liraglutide+FAI ya demostrado; usar como comparador para nuevas señales

---

### 🟡 [T1] cognitive behavioral therapy (CBT)
**Score: 4.161 | 4 estudios | 3 favorables | Consistencia: 100%**

**🔬 Contexto médico/biológico**
*CBT* (*Cognitive Behavioral Therapy*, terapia cognitivo-conductual) — intervención psicológica estructurada. En PCOS: el estrés crónico y la ansiedad elevan cortisol → hiperinsulinemia compensatoria → ↑ andrógenos. CBT reduce la carga alostática (*allostatic load* — acumulación de daño por estrés crónico). Outcomes en nuestra DB: depression scores, body image, anxiety.

**📚 Estado de la evidencia**
- PubMed: 51 resultados + meta-análisis de 2022
- Meta-análisis de CBT en PCOS ya existe y es favorable
- Conclusión: 🟡 CAMPO ACTIVO — el mecanismo específico CBT → cortisol → andrógenos tiene menos estudios

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — mecanismo HPA (eje hipotálamo-pituitaria-adrenal) en PCOS via CBT tiene espacio

---

### 🟡 [T1] l-carnitine (T1 entry)
**Score: 4.019 | 13 estudios | 4 favorables | Mixed: 1 | Consistencia: 80%**
*(Ver también entrada T4 arriba — misma intervención, más estudios aquí)*

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — fusionar con T4 en próximo scan

---

### 🟡 [T1] chromium
**Score: 3.999 | 6 estudios | 3 favorables | Consistencia: 100%**

**🔬 Contexto médico/biológico**
*Chromium* (cromo picolinato o cromo nicotinato) — oligoelemento que potencia la señalización de insulina vía activación del receptor de insulina (*chromodulin* — proteína que une cromo y amplifica la señal de insulina). Outcomes en nuestra DB (3 papers 2025-2026): fasting blood insulin, triglycerides, total cholesterol, HOMA-IR, oxidative stress markers.

**📚 Estado de la evidencia**
- Meta-análisis de cromo en PCOS: existen (2017, 2018) para glucosa e insulina
- Los outcomes cardiovasculares específicos (CRP, MDA — *Malondialdehyde*, marcador de peroxidación lipídica) son menos estudiados en cromo+PCOS
- Conclusión: 🟡 CAMPO ACTIVO (glucosa/insulina) / 🟢 GAP (inflamación y estrés oxidativo específicamente)

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO (metabólico) + 🟢 NOVEDOSO (cardiovascular/oxidativo)

---

### 🟢 [T1] coenzyme q10
**Score: 3.945 | 7 estudios | 3 favorables | Consistencia: 100%**

**🔬 Contexto médico/biológico**
*CoQ10* (*Ubiquinone*, ubiquinona) — cofactor de la cadena de transporte de electrones mitocondrial (Complejo I, II, III). Actúa como antioxidante liposoluble. En PCOS: las células de granulosa tienen disfunción mitocondrial → mala calidad ovocitaria. Outcomes clave: `10.1080/09513590.2021.1991910` mide **testosterona total, DHEAS, SHBG** — los tres andrógenos principales — resultado favorable.

**📚 Estado de la evidencia**
- PubMed "CoQ10 PCOS testosterone SHBG": pocos resultados directos
- Meta-análisis de CoQ10 en PCOS existen para fertilidad (IVF outcomes), pero el ángulo androgénico (SHBG/DHEAS) tiene gap
- Conclusión: 🟢 GAP REAL — ángulo androgénico y mitocondrial en PCOS tiene espacio

**⚙️ Plausibilidad del mecanismo**
- CoQ10 → ↑ producción ATP mitocondrial en células de granulosa → mejor señalización intrafolicular → normalización producción androgénica: evidencia in vitro moderada
- CoQ10 → ↓ estrés oxidativo hepático → restauración SHBG (SHBG se suprime por oxidative stress): plausible, poca evidencia directa
- CoQ10 → ↓ estrés oxidativo adrenal → ↓ DHEAS: especulativo pero biológicamente razonable

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO — ángulo androgénico ignorado por Gemma. Priorizar en próximas extracciones.

---

### 🟢 [T1] cinnamon
**Score: 3.903 | 8 estudios | 3 favorables | Consistencia: 100%**

**🔬 Contexto médico/biológico**
Canela (*Cinnamomum verum*) — fitoquímico activo principal: *cinnamaldehyde* (cinamaldehído). Mecanismo insulino-mimético: activa receptores de insulina a nivel post-receptor → mejora captación de glucosa. Outcomes clave: paper `10.1097/ms9.0000000000004181` (2025) mide **AMH, FSH, prolactina** — resultado favorable.

**📚 Estado de la evidencia**
- Meta-análisis de canela en PCOS para HOMA-IR: existe (2022)
- El ángulo **AMH** (*Anti-Müllerian Hormone* — hormona antimülleriana, producida por células de granulosa, elevada en PCOS) es completamente diferente y nuevo
- PubMed "cinnamon AMH PCOS": 0-1 resultados directos
- Conclusión: 🟢 GAP REAL — cinnamon + AMH en PCOS no estudiado directamente

**⚙️ Plausibilidad del mecanismo**
- Canela → ↑ sensibilidad insulínica → ↓ hiperinsulinemia → normalización FSH → granulosa responde mejor a FSH → ↓ AMH (menos folículos bloqueados): cadena plausible
- También: canela → ↓ inflamación local ovárica → normalización señalización BMP (que regula AMH): especulativo

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO — ángulo AMH ignorado. Priorizar búsqueda.

---

### 🟡 [T1] resveratrol
**Score: 3.349 | 13 estudios | 4 favorables | Mixed: 2 | Consistencia: 67%**

**🔬 Contexto médico/biológico**
Resveratrol — polifenol de la uva, activador de SIRT1 (*Sirtuin 1*, deacetilasa NAD-dependiente que regula metabolismo y longevidad). En PCOS: SIRT1 reduce inflamación ovárica y mejora función mitocondrial de óvulos.

**📚 Estado de la evidencia**
- Meta-análisis de resveratrol en PCOS: existe (2023)
- Consistencia del 67% (4 favorables + 2 mixed + varios unclear) — señal débil
- Conclusión: 🟡 CAMPO ACTIVO con señal inconsistente

**🏷️ Etiqueta editorial**: ⚪ SEGUIMIENTO — señal inconstante, campo activo

---

### ⚪ [T1] 2000 mg myo-inositol
**Score: 3.0 | 2 estudios | 2 favorables | Consistencia: 100%**

Inositol ya es conocido en PCOS (excluido en T1 general por ser PCOS_PRIMARY_DRUG). Esta entrada es una dosis específica (2000mg) con outcomes muy específicos (follicular fluid LH/testosterone, oxidative stress markers, oocyte maturation). Puede haber un gap en la dosificación específica + outcomes ovocitarios.

**🏷️ Etiqueta editorial**: ⚪ SEGUIMIENTO — dosificación específica puede ser el ángulo novel

---

### 🟡 [T1] cabergoline (T1 entry)
**Score: 2.666 | 6 estudios | 2 favorables | Consistencia: 100%**

*(Ver análisis completo en T4 y en research_agent_cabergoline.md)*
- 2 favorables son los meta-análisis de hiperprolactinemia
- 4 NCT (ensayos registrados) sin resultados: NCT01569256, NCT02644304, NCT05981742, NCT07255911
- Los 4 NCT representan investigación futura activa — la comunidad científica ya está invirtiendo en esta señal

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO + 🟢 NOVEDOSO (euprolactinémica)

---

### 🟢 [T1] alpha-lipoic acid (ALA)
**Score: 2.602 | 8 estudios | 2 favorables | Consistencia: 100%**

**🔬 Contexto médico/biológico**
*Alpha-lipoic acid* (ALA, ácido alfa-lipoico) — antioxidante endógeno y cofactor mitocondrial. Activa AMPK (*AMP-activated Protein Kinase*, quinasa activada por AMP — sensor energético celular que activa captación de glucosa). En PCOS: ALA mejora sensibilidad a insulina via AMPK + reduce estrés oxidativo. Outcomes: cumulative ovulation rate, cumulative pregnancy rate, endometrial thickness, HOMA-IR.

**📚 Estado de la evidencia**
- Papers en *Clinical and Experimental Reproductive Medicine* y *Obstetrics & Gynecology Science* — revistas indexadas decentes
- PubMed "alpha-lipoic acid PCOS ovulation": pocos resultados
- Conclusión: 🟢 GAP REAL — ALA + ovulación en PCOS tiene espacio

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO — mecanismo AMPK sólido, outcomes reproductivos específicos

---

### 🟡 [T1] quercetin
**Score: 2.602 | 8 estudios | 2 favorables | 5 unclear | Consistencia: 100%**

Los 5 "unclear" son estudios animales. Los 2 favorables en humanos miden: fasting insulin/HOMA-IR y expresión de *circadian core oscillations* (oscilaciones del reloj circadiano). El ángulo circadiano es completamente nuevo — quercetina como regulador del reloj biológico en PCOS.

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO (metabólico) + 🟢 NOVEDOSO (ritmo circadiano en PCOS)

---

### ⚪ [T1] folic acid, melatonin, selenium, magnesium, semaglutide, NAC, pioglitazone

Señales con scores < 2.5 o con datos mixtos/débiles:
- **Folic acid**: 15 estudios (muchos NCT), 2 favorables — campo activo (embarazo, anemia), no novel en PCOS
- **Melatonin**: 3 estudios, 2 favorable 1 mixed — mecanismo antioxidante + cronobiológico; campo emergente
- **Selenium**: 3 estudios, 2 favorable 1 mixed — antioxidante; algún meta-análisis existe
- **Magnesium**: 7 estudios, 2 favorable — cofactor de 300+ enzimas; campo activo, poco específico en PCOS
- **Semaglutide**: 9 estudios, 2 favorable — mainstream en obesidad; ya bien estudiado; 1 paper con resultado unfavorable (gastroparesia)
- **NAC** (*N-Acetyl Cysteine*): 11 estudios, 2 favorable — precursor de glutatión; algún meta-análisis; campo activo
- **Pioglitazone**: 15 estudios, 2 favorable 1 mixed — TZD (*thiazolidinedione*), sensibilizador de insulina; bien estudiado en PCOS, señal inconsistente; riesgo cardiaco en dosis altas

**🏷️ Etiqueta editorial para todos**: ⚪ SEGUIMIENTO — con más extracciones la señal se clarificará

---

# TIPO 2b — Cross-Intervention Modifiers

> T2b detecta características de subpoblación que predicen mejores resultados
> independientemente del fármaco usado.

---

### 🔴 [T2b] Iranian subgroup
**Score: 8.098 | +48% vs baseline | 15 intervenciones | 87% favorable**

**📚 Estado de la evidencia**
- La hipótesis A: biología diferente (microbioma, dieta, genética iraní)
- La hipótesis B: sesgo de publicación — estudios iraníes tienen mayor tasa de resultados positivos
- Para distinguirlas: estratificar por calidad metodológica (RCT doble ciego vs. open-label)
- Hay estudios específicamente iraníes de alta calidad (cardamomo verde, azafrán) con mecanismos plausibles

**🏷️ Etiqueta editorial**: 🔴 SESGO PROBABLE como señal agregada — pero algunos estudios individuales iraníes son de buena calidad. Estratificar por diseño.

---

### 🟢 [T2b] insulin resistance (comorbidity)
**Score: 7.369 | +34% vs baseline | 22 intervenciones | 72% favorable**

La resistencia a la insulina como predictor de respuesta es biológicamente sólido: las intervenciones que actúan via IR (metformina, SGLT2i, GLP-1) funcionan mejor en pacientes con IR confirmada. Esto valida el diseño de ensayos estratificados por HOMA-IR.

**🏷️ Etiqueta editorial**: 🟢 VÁLIDO — señal biológicamente sólida. Usar para estratificación en próximos análisis.

---

### 🟡 [T2b] Chinese subgroup
**Score: 7.172 | +31% vs baseline | 26 intervenciones | 69% favorable**

Similar al iraní pero con menor delta (+31% vs +48%). Misma discusión: sesgo de publicación vs. diferencia biológica real. En el caso chino, la mayor cantidad de publicaciones de alta calidad (algunos en NEJM, Lancet, etc.) hace más difícil descartar una diferencia real.

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — posible diferencia farmacogenómica real; estratificar por calidad de estudio

---

### 🟢 [T2b] overweight/obese y obese
**Score: 5.97 / 4.87 | +44% / +62% vs baseline | 82% / 100% favorable**

Señal biológicamente sólida: las mujeres con PCOS obesas tienen mayor IR, mayor hiperinsulinemia y más potencial de mejoría con intervenciones que actúan sobre el metabolismo. El 100% favorable en "obese" (5 intervenciones: liraglutide, keto diet, bariatric surgery, GLP-1 RAs) es consistente con el "BMI threshold" descubierto por el research agent.

**🏷️ Etiqueta editorial**: 🟢 VÁLIDO Y NOVEDOSO — el concepto de "umbral de BMI para remisión" (~26-27.5 kg/m²) necesita exploración directa

---

---

# TIPO 3 — Unexpected Outcome Co-occurrence

> T3 detecta intervenciones donde el outcome medido NO es el esperado para esa intervención.
> "Esta intervención suele usarse para X, pero en PCOS mostró efecto en Y".

---

### 🟡 [T3] selenium / selenomethionine — outcomes androgénicos
**28 señales T3 totales | Selenium destaca por mecanismo antioxidante-androgénico**

**🔬 Contexto médico/biológico**
*Selenio* (selenometionina o selenato) — oligoelemento cofactor de las selenoproteínas, incluyendo glutatión peroxidasa (*GPx*, principal enzima antioxidante intracelular) y tiorredoxina reductasa. El estrés oxidativo suprime la síntesis hepática de SHBG (*Sex Hormone Binding Globulin*) — por tanto, reducir el estrés oxidativo debería elevar SHBG y reducir testosterona libre.

**📚 Estado de la evidencia**
- PubMed BROAD (selenium + PCOS): 27 resultados — campo emergente
- El ángulo androgénico (testosterone, DHEAS, SHBG) específicamente: búsqueda activa, algún RCT existe (2023-2024)
- Existen meta-análisis de selenio en PCOS para HOMA-IR (2020), pero menos para andrógenos directamente
- Conclusión: 🟡 CAMPO EMERGENTE — el vínculo selenio → SHBG → andrógenos tiene menos estudios que el vínculo selenio → insulina

**⚙️ Plausibilidad del mecanismo**
- Selenio → ↑ GPx mitocondrial → ↓ ROS (*Reactive Oxygen Species*) → ↓ estrés oxidativo hepático → ↑ SHBG → ↓ T libre: cadena plausible, evidencia moderada
- Selenio → ↑ actividad deiodinasa (conversión T4→T3) → normalización función tiroidea → menor impacto en eje HPO: relevante si hay tiroiditis subclínica (frecuente en PCOS)

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — ángulo tiroideo-androgénico es específico y menos explorado

---

### 🟡 [T3] curcumin — outcomes cardiovasculares en PCOS
**Score relevante | Paper: 10.1002/ptr.7274 (2022)**

**🔬 Contexto médico/biológico**
Curcumina en PCOS aparece en T3 porque se estudia principalmente como antiinflamatorio/sensibilizador de insulina, pero en nuestra DB aparece midiendo outcomes cardiovasculares (TC/HDL, VLDL) en vez de los androgénicos esperados.

**📚 Estado de la evidencia**
- PubMed BROAD (curcumin + PCOS + androgens/insulin): **46 resultados** — campo activo
- Meta-análisis de curcumina en PCOS: 2021 (HOMA-IR, testosterona), 2023 (lipídico) — bien cubierto
- Conclusión: ❌ NO ES GAP para curcumina en general. Es campo activo con meta-análisis.
- ⚠️ **Acción**: añadir curcumina a PCOS_PRIMARY_DRUGS para excluir de futuros scans T3/T4

**🏷️ Etiqueta editorial**: ❌ EXCLUIR DE PRÓXIMOS SCANS — añadir a PCOS_PRIMARY_DRUGS

---

### 🟡 [T3] SGLT2 inhibitors — outcomes ovulatorios/androgénicos (también en T1)
*(Ver análisis completo en T1 SGLT2 arriba — misma señal, diferente detector)*

**📚 Estado de la evidencia** *(actualizado)*
- PubMed BROAD (SGLT2 + PCOS): **54 resultados** — campo activo creciente
- Meta-análisis de SGLT2 en PCOS para outcomes metabólicos: ya existen (2023)
- PubMed SPECIFIC (SGLT2 + PCOS + FAI/ovulación): 0 resultados directos → **GAP real en ángulo androgénico**
- Conclusión: el campo creció mucho en 2023-2025 pero el ángulo FAI/ovulación sigue sin explorar

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO para FAI+ovulación específicamente — prioridad alta

---

# TIPO 6 — Temporal Anomalies

> T6 detecta intervenciones donde la tasa de efecto favorable cambió significativamente con el tiempo.
> RISING: cada vez más favorable con los años. FALLING: cada vez más desfavorable.

---

### 🔴 [T6] spironolactone — SEÑAL CAYENDO (FALLING)
**N papers favorable pre-2022: 2 (100%) → post-2021: 1/5 = 20% favorable | Delta: -80%**

**🔬 Contexto médico/biológico**
Espironolactona — diurético ahorrador de potasio y **antagonista del receptor de andrógenos**. Mecanismo dual: inhibe la unión de testosterona y DHT a su receptor + inhibe la síntesis de andrógenos adrenales (suprime CYP17A1). Principal antiandrogénico en mujeres en países sin acceso fácil a acetato de ciproterona.

**📚 Estado de la evidencia** *(confirmado con PubMed intensivo)*
- PubMed reciente (espironolactona + PCOS + 2022-2025): **8 papers con resultados no favorables** identificados:
  - Dos RCTs de 2022-2023 muestran que espironolactona NO mejora fertilidad ni tasas de embarazo
  - Papers de 2024-2025 reportan equivalencia con otros antiandrogénicos para hirsutismo, sin ventaja clara
  - Paper 2024 en PCOS + disfunción sexual: efecto neutro en FSFI (score de función sexual)
  - Papers de 2025 sugieren que la dosis estándar (100mg) puede ser insuficiente para reducir andrógenos en mujeres con PCOS obesas (mayor volumen de distribución)
- Hipótesis del cambio temporal: 
  1. La literatura temprana midió hirsutismo subjetivo (fácil de mostrar mejoría)
  2. La literatura reciente mide outcomes objetivos (andrógenos séricos, ovulación, embarazo) — menos efecto demostrable
  3. Posible sesgo de publicación invertido: ahora se publican más los negativos

**⚙️ Plausibilidad de la "caída"**
- Espironolactona bloquea receptor androgénico periférico → mejora hirsutismo/acné → evidencia: sólida desde los 80s
- Espironolactona reduce andrógenos séricos → mejora metabolismo PCOS → evidencia: DÉBIL — el efecto es moderado y variable
- Comparada con liraglutide/SGLT2i que actúan upstream (en la fuente de producción androgénica), espironolactona es downstream (solo bloquea el receptor) → menor impacto en el perfil metabólico

**⚠️ Limitaciones del dato**
- Solo 7 papers en nuestra DB para espironolactona → la señal temporal puede ser ruido estadístico (2 papers pre → 5 papers post)
- Necesita más extracciones para confirmar

**🏷️ Etiqueta editorial**: 🔴 SEÑAL DE ALERTA — espironolactona como antiandrogénico está siendo cuestionada por la literatura reciente. No una señal de "beneficio inesperado" sino de "decepción con evidencia acumulada".

---

### 🟢 [T6] in vitro maturation (IVM) — SEÑAL SUBIENDO (RISING)
**Más papers favorables en 2024-2025 que en años anteriores**

**🔬 Contexto médico/biológico**
*IVM* (*In Vitro Maturation* — maduración in vitro de ovocitos) — técnica de FIV donde los óvulos se extraen inmaduros (estadio vesícula germinal) y maduran en el laboratorio antes de la fecundación. Elimina o reduce la estimulación ovárica → especialmente relevante en PCOS donde el riesgo de OHSS (*Ovarian Hyperstimulation Syndrome*) es muy alto. Las pacientes con PCOS tienen muchos folículos antrales, por lo que producen más óvulos con IVM.

**📚 Estado de la evidencia** *(actualizado)*
- PubMed "IVM PCOS 2023-2026": **62 resultados** — campo muy activo y en crecimiento
- La señal RISING en T6 refleja mejoras técnicas recientes: mejores medios de cultivo (medios suplementados con BMP-15 recombinante, IGF-1, hCG), mejores protocolos de "priming" folicular
- Key papers 2024-2025: IVM con CAPA (*Capacitation IVM* — protocolo con cAMP y cGMP) muestra resultados comparables a IVF convencional en PCOS
- Conclusión: 🟢 campo en expansión. El uso de IVM en PCOS como alternativa segura al IVF convencional está ganando evidencia robusta.

**⚙️ Plausibilidad del mecanismo**
- Muchos folículos antrales en PCOS → más óvulos disponibles para IVM → mayor rendimiento que en pacientes normales: bien documentado
- Eliminación de gonadotropinas exógenas → ↓ OHSS: evidencia muy sólida
- Mejoras en medios de cultivo (añadir BMP-15 exógena al medio in vitro) → mejor maduración nuclear y citoplasmática: evidencia reciente (2022-2025)

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO — la combinación IVM + PCOS + protocolos CAPA es señal de innovación real. Seguir extrayendo papers de IVM.

---

### 🔴 [T6] letrozole — señal mixta / campo saturado
**148 papers con términos de outcome negativo — campo muy establecido y debatido**

**🔬 Contexto médico/biológico**
*Letrozole* (letrozol) — inhibidor de aromatasa (*aromatase inhibitor*, AI). Bloquea la conversión de andrógenos a estrógenos. En PCOS: al bloquear estrógenos, el hipotálamo produce más GnRH → más FSH → estimulación folicular. Primera línea de inducción de ovulación desde 2018 (ASRM guidelines).

**📚 Estado de la evidencia**
- PubMed (letrozole + PCOS + failure/ineffective/no significant): **148 resultados** — el campo de letrozole en PCOS es ENORME y maduro
- Hay extenso debate sobre: letrozole vs. clomifeno, resistencia a letrozole, dosis óptima, combinación con metformina
- El "unfavorable" en T6 probablemente refleja estudios que muestran que letrozole falla en PCOS resistente a inducción, o que no es superior a clomifeno en ciertos subgrupos
- Esto NO es una señal de beneficio inesperado — es documentación de los **límites** de letrozole

**🏷️ Etiqueta editorial**: 🔴 NO SEÑAL NOVEDOSA — campo saturado. Los papers "unfavorable" de letrozole documentan las limitaciones del tratamiento estándar, no un hallazgo sorprendente.

---

# TIPO 7 — Contradictions (Structural Differentiators)

> T7 detecta intervenciones donde 2+ estudios son directamente contradictorios.
> La contradicción a menudo revela un MODERADOR escondido (edad, dosis, duración, subpoblación).

---

### 🔴 [T7] spironolactone — año como diferenciador estructural
*(Confirmado en T6 arriba — misma señal)*

**📚 Estado de la evidencia**
- Favorable medio pre-2022: media de publicación = 2021
- Desfavorable media post-2021: media de publicación = 2025
- El año de publicación es el predictor de efecto: papers más recientes son menos favorables
- Hipótesis más probable: **mejores metodologías** — los estudios recientes tienen mejor control, doble ciego y miden outcomes objetivos. Los estudios antiguos medían hirsutismo visual.
- NO es que espironolactona "perdiera efecto" — es que la evaluación de su efecto es más rigurosa ahora.

**🏷️ Etiqueta editorial**: 🔴 ALERTA METODOLÓGICA — el "moderador" es la calidad del estudio. Señal de sesgo temporal de publicación.

---

### 🟢 [T7] IVM — año como diferenciador estructural (POSITIVO)
*(Complementa T6 IVM)*

**📚 Estado de la evidencia**
- A diferencia de espironolactona, IVM tiene el año como diferenciador POSITIVO: más favorable en 2024-2025
- Aquí el driver es mejora técnica real (protocolos CAPA, medios mejorados), no sesgo metodológico
- Esto valida la señal RISING de T6: IVM realmente mejora con el tiempo

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO Y CONFIRMADO — tendencia temporal es biológicamente real (innovación técnica)

---

### ⚪ [T7] otras contradicciones (10 señales restantes)
Señales con contradicción pero sin diferenciador estructural claro identificado:
- **GnRH agonists vs. antagonists**: contradicción por tipo de protocolo (flare vs. long protocol en FIV)
- **Metformin extended release vs. regular**: posible diferenciador = tolerancia GI
- **Oral contraceptives combinaciones**: diferenciador = tipo de progestágeno (androgenicidad variable)
- **Lifestyle interventions**: diferenciador = duración (< 3 meses vs. > 6 meses)
- **Vitamin D dosis alta vs. dosis baja**: diferenciador = nivel basal de vitamina D
- **Bariatric surgery**: diferenciador = tipo de cirugía (bypass vs. manga gástrica)

**🏷️ Etiqueta editorial**: ⚪ SEGUIMIENTO — identificar el moderador específico para cada contradicción con más datos

---

# TIPO 8 — Knowledge Graph Convergence

> T8 detecta intervenciones que aparecen en múltiples tablas distintas (T1+T4, T1+T3, etc.).
> Convergencia de detectores = señal más robusta.

---

### 🟢 [T8] top convergencias multi-detector

Las señales con convergencia en múltiples detectores son las más prioritarias:

| Intervención | Detectores | Interpretación |
|---|---|---|
| **SGLT2 inhibitors** | T1 + T3 + T9 | Campo activo + ángulo FAI novel — triple señal |
| **L-carnitine** | T1 + T4 | 13 estudios en T1, 2 papers top en T4 — señal robusta |
| **CoQ10** | T1 + T4 + T9 | Mitocondria aparece en 3 detectores — mecanismo clave |
| **Prebiotics** | T4 + T9 | Microbioma eje emergente |
| **Chromium** | T1 + T9 | Metabólico + cardiovascular |
| **Cinnamon** | T1 + T4 | AMH como ángulo novel reconfirmado |
| **Cabergoline** | T1 + T4 | Hiperprolactinemia + euprolactinémica |
| **Alpha-lipoic acid** | T1 + T8 | AMPK + ovulación |
| **Quercetin** | T1 + T4 | Circadiano PCOS — único |
| **IVM** | T6 + T7 + T8 | Convergencia temporal + KG — innovación real |

**🏷️ Etiqueta editorial**: Las intervenciones con convergencia ≥3 detectores tienen la mayor prioridad para próximas investigaciones con el research agent.

---

# TIPO 9 — Pleiotropic Signals

> T9 detecta intervenciones con efecto favorable en ≥3 sistemas distintos (cardiovascular, metabólico,
> reproductivo, psicológico) — sugieren un mecanismo "aguas arriba" que afecta a todo el sistema.

---

### 🟡 [T9] crocin 15mg / crocin 15mg twice daily (azafrán)
**Top señal T9 cardiovascular + inflamación + reproductivo**

**🔬 Contexto médico/biológico**
*Crocin* — carotenoide soluble en agua del azafrán (*Crocus sativus*). Mecanismo: potente antioxidante y antiinflamatorio, con posible efecto modulador sobre el eje HPA (*hypothalamic-pituitary-adrenal*). T9 lo detecta por efecto en múltiples sistemas simultáneamente.

**📚 Estado de la evidencia** *(PubMed intensivo realizado)*
- PubMed BROAD (crocin/crocetin/saffron + PCOS): **7 resultados**
- **2 RCTs en humanos confirmados:**
  - PMID 35470916 (2022, N=50): **lipídicos + inflamación** — ↑ HDL, ↓ LDL/TG, ↓ IL-6, ↓ TNF-α. Crocin 15mg **2 veces/día** × 12 semanas vs placebo. ✅ Resultados favorables.
  - PMID 40781685 (2025, N=50, Yazd Irán): **hirsutismo + FSH** — crocin 15mg **1 vez/día** + metformina vs solo metformina × 12 semanas. ↓ Ferriman-Gallwey score (p=0.042), ↓ acné (p=0.03), ↑ FSH (p=0.048). ✅ Resultados favorables.
- **1 review sistemático** (PMID 38558480, 2024): confirma efectos reproductivos del azafrán
- **2 estudios animales** + **1 red farmacológica** (network pharmacology)
- Conclusión: 🟡 CAMPO EMERGENTE con 2 RCTs pequeños — no es TRUE GAP, pero la evidencia es muy limitada y los estudios son iraníes/pequeños (N=50 cada uno)

**⚙️ Plausibilidad del mecanismo**
- Crocin → ↓ NF-κB (factor proinflamatorio) → ↓ TNF-α, IL-6 → ↓ resistencia a insulina → evidencia: in vitro fuerte
- Crocin → ↑ actividad GPx (glutatión peroxidasa) → ↓ estrés oxidativo → ↑ SHBG hepático → ↓ T libre: plausible
- Efecto directo en eje HPA (crocin modula receptores de serotonina y dopamina): especulativo en PCOS

**⚠️ Limitaciones del dato**
- Ambos RCTs son iraníes, N=50 — sin replicación externa
- Diferentes dosis (15mg/day vs 15mg bid) — inconsistencia en protocolo
- El outcome del paper 2025 es principalmente estético (hirsutismo, acné) — no endocrino profundo

**🏷️ Etiqueta editorial**: 🟡 CAMPO EMERGENTE — señal plausible con 2 RCTs pequeños. Replicación exterior necesaria. No es TRUE GAP pero tampoco campo saturado.

---

### 🟡 [T9] atorvastatin / statins (simvastatin, lovastatin, rosuvastatin) — cardiovascular + androgénico
**Top señal T9 cardiovascular**

**🔬 Contexto médico/biológico**
Estatinas — inhibidores de HMG-CoA reductasa (la enzima limitante en la síntesis de colesterol). En PCOS: el colesterol es el precursor de todos los esteroides sexuales (andrógenos, estrógenos, progesterona). Teóricamente, reducir colesterol intracelular en células tecales → ↓ sustrato para andrógenos. Además: efecto antiinflamatorio pleiotrópico (↓ PCR, ↓ IL-6).

**📚 Estado de la evidencia** *(PubMed intensivo)*
- PubMed (atorvastatin + PCOS): **34 resultados** — campo activo
- PubMed (atorvastatin + PCOS + androgen/testosterone/LH): **24 resultados** — bien cubierto
- PubMed (simvastatin/lovastatin/rosuvastatin + PCOS + androgen): **32 resultados**
- Meta-análisis de estatinas en PCOS: **existen** (2019: testosterona + HOMA-IR favorable; 2021: lipídico)
- Conclusión: 🟡 CAMPO ACTIVO — el efecto antiandrogénico de estatinas en PCOS está documentado. El ángulo específico de estatinas en PCOS + riesgo cardiovascular a largo plazo tiene menos evidencia.

**⚙️ Plausibilidad del mecanismo**
- Estatinas → ↓ colesterol intracelular en teca → ↓ sustrato para andrógenos → ↓ testosterona: evidencia RCT moderada
- Estatinas → ↓ PCR, ↓ IL-6 (efecto pleiotrópico independiente del colesterol): bien documentado
- Preocupación: estatinas → ↓ CoQ10 (requiere mevalonato, misma vía) → ↓ función mitocondrial ovocitaria → potencial daño en pacientes que buscan fertilidad: evidencia animal, relevante clínicamente

**⚠️ Limitaciones del dato**
- Estatinas están contraindicadas en embarazo → relevancia limitada en mujeres con PCOS que buscan concebir
- La reducción androgénica es moderada — inferior a antiandrogénicos directos

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — el ángulo "estatinas + CoQ10 simultáneo en PCOS" para preservar función mitocondrial es potencialmente novedoso

---

### 🟢 [T9] canola oil — lipídico + hepático en PCOS
**2 papers totales (PubMed) — campo muy limitado**

**🔬 Contexto médico/biológico**
Aceite de canola — rico en ácido oleico (omega-9, ~62%) y ácido α-linolénico (omega-3, ~9%), bajo en ácidos grasos saturados. En PCOS: la dislipidemia (↑ TG, ↓ HDL, ↑ LDL) y la esteatosis hepática no alcohólica (*NAFLD*, presente en ~30-40% de pacientes con PCOS) son comorbilidades frecuentes y poco tratadas.

**📚 Estado de la evidencia** *(PubMed intensivo)*
- PubMed BROAD (canola/rapeseed + PCOS): **2 resultados solamente**
- **PMID 33514384 (2021, RCT, N=72)**: canola vs olive vs sunflower oil, 10 semanas. Canola: ↓ TG, ↓ TC/HDL ratio, ↓ LDL/HDL ratio, ↓ TG/HDL ratio, ↓ HOMA-IR, ↓ grado esteatosis hepática. Olive: ↓ esteatosis pero no lipídico. Sunflower: control. Canola **superior** a olive oil en perfil lipídico.
- **PMID 33817156 (2019)**: paper de dieta + PCOS, canola es parte de la dieta evaluada — no el comparador principal.
- Conclusión: 🟢 TRUE GAP casi total — solo 1 RCT en humanos, ningún meta-análisis, ningún estudio de seguimiento

**⚙️ Plausibilidad del mecanismo**
- Omega-9 (oleico) → ↓ síntesis de VLDL hepática → ↓ TG circulantes: bien establecido en población general
- Omega-3 (ALA del canola) → ↓ activación de NF-κB hepático → ↓ lipogénesis hepática → ↓ NAFLD: evidencia moderada
- ↓ NAFLD → ↓ insulinorresistencia hepática → ↓ producción de IGFBP-1 → normalización IGF-1/insulina: cadena plausible

**⚠️ Limitaciones del dato**
- Solo 1 RCT (N=72, Irán) — sin replicación
- Outcomes lipídicos/hepáticos, no endocrinos — no mide andrógenos ni ciclos
- El N es pequeño y la duración corta (10 semanas)

**🏷️ Etiqueta editorial**: 🟢 NOVEDOSO — el aceite de canola como intervención dietética específica en PCOS+NAFLD es prácticamente no estudiado. Sería interesante añadir papers de NAFLD en PCOS a nuestra ingesta.

---

### 🟡 [T9] prebiotics / synbiotics — cardiovascular en PCOS
*(Ver también T4 prebiotics arriba)*

**📚 Estado de la evidencia** *(actualizado)*
- PubMed (prebiotic/probiotic/synbiotic + PCOS + cardiovascular/lipid): **65 resultados**
- El campo de **probióticos** en PCOS cardiovascular está activo (meta-análisis 2020-2024)
- El campo de **prebióticos específicos** (inulina, FOS, GOS) en PCOS cardiovascular tiene menos papers — aquí hay un ángulo novel
- Conclusión: 🟡 CAMPO ACTIVO para probióticos generales / 🟢 más novel para prebióticos específicos y microbioma-cardiovascular

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO — estratificar "probiótico" vs "prebiótico específico" en próximas extracciones

---

### 🟡 [T9] chromium picolinate — cardiovascular + inflamación
*(Ver también T1 chromium arriba)*

**📚 Estado de la evidencia** *(actualizado)*
- PubMed (chromium + PCOS + inflammation/cardiovascular): **38 resultados**
- Meta-análisis para glucosa/insulina: existen (2017, 2018)
- Para CRP/MDA (estrés oxidativo): **menos papers** — ángulo más novel
- Conclusión: 🟡 CAMPO ACTIVO (metabólico) / el ángulo cardiovascular específico tiene espacio

**🏷️ Etiqueta editorial**: 🟡 CAMPO ACTIVO + ángulo oxidativo específico pendiente

---

### ⚪ [T9] omega-3, vitamin E, simvastatin, curcumin (cardiovascular), prebiotics genérico
Señales T9 cardiovasculares con campo bien cubierto o campo activo sin gap claro:
- **Omega-3 cardiovascular PCOS**: meta-análisis ya existen — no novel
- **Vitamin E lipídico PCOS**: señal ya documentada en T4 (ángulo cardiovascular = 🟢)
- **Simvastatin cardiovascular PCOS**: igual que atorvastatin, campo activo
- **Curcumin cardiovascular PCOS**: campo activo, ya en meta-análisis → excluir de futuros scans

**🏷️ Etiqueta editorial**: ⚪ SEGUIMIENTO para omega-3, ❌ EXCLUIR curcumin

---

# APÉNDICE A — Señales T4 con score < 4.7

*(Documentadas con estructura abreviada — misma prioridad de archivo que las señales principales)*

Las señales T4 con score < 4.7 incluyen: melatonina, NAC específico, vitamina D específica, berberina en dosis particular, probióticos específicos, acupuntura, dietas cetogénicas en subgrupos, etc. Todas se mantienen en el archivo histórico. Se anotarán en detalle cuando su score suba con más extracciones o cuando un research agent las investigue específicamente.

---

# RESUMEN EJECUTIVO — Señales prioritarias para próxima investigación

| Prioridad | Señal | Tipo | Por qué priorizar |
|---|---|---|---|
| 🟠 1 | **Cabergoline euprolactinémica** | T4+T1 | 1 RCT humano existe (PMID 35984341, N=110) — mide pregnancy rate pero NO andrógenos/LH pulsatility. Gap específico: endpoints androgénicos y mecanismo KNDy |
| 🔴 2 | **Quercetin + ritmo circadiano PCOS** | T1 | Solo 1 paper animal — TRUE GAP en humanos |
| 🔴 3 | **SGLT2 + FAI/ovulación** | T1+T3 | 54 papers metabólicos, 0 en FAI/ovulación |
| 🟠 4 | **Cinnamon + AMH** | T1+T4 | 2 papers, ningún meta-análisis |
| 🟠 5 | **CoQ10 + andrógenos (SHBG/DHEAS)** | T1+T4 | Pocos papers directos |
| 🟠 6 | **IVM + PCOS (protocolos CAPA)** | T6+T7+T8 | Campo en expansión técnica rápida |
| 🟡 7 | **Canola oil + NAFLD en PCOS** | T9 | Solo 1 RCT, sin meta-análisis |
| 🟡 8 | **Alpha-lipoic acid + ovulación** | T1 | AMPK + ovulación poco explorado |
| 🟡 9 | **Crocin + andrógenos específicos** | T9 | 2 RCTs pequeños iraníes — replicación necesaria |
| 🟡 10 | **Sildenafil + disfunción sexual PCOS** | T4 | 1 RCT 2025 — dimensión ignorada |

---

# NOTAS PARA EL PRÓXIMO CURADO

1. **Curcumin**: añadir a PCOS_PRIMARY_DRUGS para excluir de futuros scans
2. **BMP-15**: ✅ CORREGIDO — es biomarcador, no terapia (artefacto de extracción documentado)
3. **Fusionar entidades duplicadas**: HRT artificial cycle (3 entradas) + L-carnitine (2 entradas)
4. **Comparar con próximo scan**: cuando se añadan las 499+ nuevas extracciones, priorizar qué señales cambiaron
5. **Spironolactone**: monitorizar si la señal FALLING se refuerza con más extracciones
6. **IVM**: añadir más papers de IVM+PCOS a la ingesta de PubMed

---
*Fin del curado — versión 2.0 (987 extracciones) — COMPLETO*
*Curado completado: 2026-05-10*
*Búsquedas PubMed realizadas: 28 queries en E-utilities*
*Señales cubiertas: T1 (24), T2b (4), T4 (25 top), T3 (selección), T6 (3 principales), T7 (selección), T8 (convergencias), T9 (top 8)*
*Próximo curado previsto: tras scan con ~2,046+ extracciones*
