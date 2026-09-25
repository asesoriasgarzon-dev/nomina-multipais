# KILLCRITIC — Gate de calidad de Colombia (2026)

> **Generado** el 2026-09-25 ejecutando la suite real. Motor v1.1.0, reglas `CO-2026.2.0`.

## Resultado de la suite

`============================= 930 passed in 8.67s =============================`

| passed | failed | skipped | errors |
|---:|---:|---:|---:|
| 930 | 0 | 0 | 0 |

## Gate (sección 34 del encargo)

| # | Criterio | Estado | Evidencia | Pruebas |
|---|---|---|---|---|
| 1 | Las reglas tienen fuente | CUMPLE (pruebas en verde) | Cada regla, referencia, base y concepto tiene bloque `source`; las oficiales exigen autoridad, referencia legal, URL y fecha. | test_schema_and_sources::test_todo_dato_normativo_tiene_vigencia_fuente_y_verificacion, test_las_fuentes_oficiales_tienen_autoridad_referencia_url_y_fecha |
| 2 | Las vigencias están modeladas | CUMPLE (pruebas en verde) | effective.from/to en todo; SMVM mensual, UMA 1-feb, jornada 15-jul, SIS/reforma Chile con versiones. | test_colombia::test_co_workweek_2026_*, test_countries_2026::test_ar_el_smvm_*, test_mx_la_uma_*, test_cl_sis_y_reforma_* |
| 3 | Los límites están probados | CUMPLE (pruebas en verde) | Fronteras -1/=/+1 en auxilio (2 SMMLV), IBC (25 SMMLV), integral (13 SMMLV), exoneración (10 SMMLV), FSP y topes de cada país. | test_colombia::test_co_transport_boundary, test_co_social_security_cap, test_co_integral_salary_*, test_co_exoneracion_*, test_co_fsp_* |
| 4 | Las excepciones están probadas | CUMPLE (pruebas en verde) | Exoneración art. 114-1 (línea en cero con motivo), caja nunca exonerada, empleador no exonerado. | test_colombia::test_co_exoneracion_*, test_co_empleador_no_exonerado_*, test_co_la_caja_* |
| 5 | Las bases están separadas | CUMPLE (pruebas en verde) | IBC, RISK_BASE, PARAFISCAL_BASE, BENEFIT_BASE, VACATION_BASE, EXONERATION_BASE; no hay una base genérica. | test_colombia::test_co_bases_separadas_para_cada_proposito |
| 6 | Los redondeos están probados | CUMPLE (pruebas en verde) | Política por país; redondeo por línea registrado en la auditoría; líneas suman los totales. | test_core::test_el_redondeo_queda_registrado_*, test_las_lineas_suman_exactamente_los_totales, test_politica_de_redondeo_* |
| 7 | El audit trail funciona | CUMPLE (pruebas en verde) | Toda línea tiene regla, versión, fórmula, redondeo y fuente; reglas no aplicadas quedan explicadas. | test_colombia::test_co_toda_linea_tiene_traza_*, test_co_la_explicacion_sale_de_la_ejecucion_real |
| 8 | Las explicaciones corresponden a las reglas | CUMPLE (pruebas en verde) | La explicación se construye del registro de ejecución (operandos leídos, condición evaluada). | test_colombia::test_co_transport_explicacion_muestra_la_regla_de_2_smmlv, test_co_exoneracion_la_linea_en_cero_explica_por_que |
| 9 | Los tests de frontera pasan | CUMPLE (pruebas en verde) | Ver resultado de la suite abajo. | tests/payroll_2026/ |
| 10 | Sin fórmulas legales duplicadas | CUMPLE (pruebas en verde) | Un mecanismo genérico por operación (rate_on_base, progressive_brackets…); las diferencias son parámetros. | test_architecture::test_el_nucleo_no_contiene_paises_ni_reglas_de_pais |
| 11 | Sin reglas colombianas en otros países | CUMPLE (pruebas en verde) | Cada país tiene sus propios conceptos y referencias; el núcleo no contiene códigos de país. | test_architecture::*, test_countries_2026::test_pe_no_trata_la_gratificacion_como_el_13o_de_otro_pais |

**Lo que este gate NO afirma:** que las reglas estén validadas por un profesional (ninguna lo está: `professional_validation = PENDING` en todas), ni que los resultados de la liquidación y de las horas extra sean jurídicamente definitivos (fuentes oficiales para muchas reglas, pero con interpretaciones sin revisar y varias fuentes PENDING), ni que exista motor tributario (la retención es un valor digitado, `EXTERNAL_INPUT`).

## Fuentes de las reglas de Colombia

| Estado de la fuente | Reglas |
|---|---:|
| OFFICIAL | 17 |
| SECONDARY | 10 |
| PENDING | 8 |
| NOT_APPLICABLE | 25 |
| CONFLICTING | 0 |

Fuentes OFICIALES verificadas en esta ejecución: SMMLV (Decretos 1469/2025 y 159/2026), auxilio de transporte (Decreto 1470/2025), IBC 25 SMMLV / mínimo 1 SMMLV / salario integral 70% (Ley 797/2003 art. 5), FSP (art. 8), jornada (Ley 2101/2021 art. 3). El resto (tasas de salud/pensión/parafiscales, ARL, ET art. 114-1, CST art. 132, Ley 1393 art. 30, provisiones) se contrastó solo con fuentes SECUNDARIAS o quedó PENDING: **no se marca oficial sin respaldo verificable**.

## Hallazgos de la investigación normativa que afectan el diseño

- **El SMMLV 2026 está en litigio.** El Decreto 1469/2025 fue suspendido provisionalmente por el Consejo de Estado (13-feb-2026); el Decreto 159/2026 (DO 53.403, 19-feb-2026) fijó el mismo valor $1.750.905 de forma transitoria «hasta que se dicte sentencia» (rad. 11001-03-25-000-2026-00004-00). Si la sentencia cambia el valor, se agrega una versión de la referencia con su vigencia; no se edita la actual.
- **Conflicto con la documentación interna:** `NORMATIVA_PAISES.md` dice «≤10 SMMLV» para la exoneración; el art. 114-1 ET dice «menos de diez (10)». Se implementó el texto de la norma (estricto) y se probó la frontera exacta (10 SMMLV NO está exonerado). Requiere validación profesional.
- **Chile:** el ingreso mínimo de $553.553 desde el 1-may-2026 solo consta en fuentes secundarias; la página oficial consultada de la Ley 21.751 llega a $539.000. Se marcó PENDING. La jornada de 42 h desde el 26-abr-2026 sí tiene fuente oficial (Mintrab).
- **Argentina:** el SMVM cambia cada mes; septiembre a diciembre 2026 tienen fuente oficial (Boletín Oficial, Res. 4/2026); enero a agosto solo secundaria.
- **México:** la UMA cambia cada 1 de febrero (117,31 desde el 1-feb-2026); el valor anterior (113,14) quedó PENDING de verificación.
- **Cobertura del auxilio de transporte:** el límite de 2 SMMLV tiene fuente oficial; el tratamiento de variables, vacaciones/incapacidad y periodos parciales quedó PENDING.

## Reglas de Colombia SIN test de frontera dedicado

- `CO.AFC_DEDUCTION`
- `CO.BONUS_SALARY`
- `CO.CESANTIAS`
- `CO.CESANTIAS_ACCRUAL`
- `CO.CESANTIAS_INTERESES`
- `CO.CESANTIAS_INTEREST_ACCRUAL`
- `CO.IN.CO_T_CESANTIAS_PRIOR`
- `CO.IN.CO_T_INTEREST_PRIOR`
- `CO.IN.CO_T_PRIMA_PRIOR`
- `CO.IN.CO_T_UNPAID_SALARY`
- `CO.IN.DAYS_MONTH`
- `CO.IN.DAYS_YEAR`
- `CO.IN.SALARY_12M`
- `CO.IN.SALARY_6M`
- `CO.IN.TRANSPORT`
- `CO.INCAPACITY_EMPLOYER`
- `CO.INCAPACITY_EPS`
- `CO.INDEMNIZACION_FIJO`
- `CO.INDEMNIZACION_INDEF_GE10`
- `CO.INDEMNIZACION_INDEF_LT10`
- `CO.INDEMNIZACION_OBRA`
- `CO.LOANS_ADVANCES`
- `CO.OVERTIME`
- `CO.PASS.CO_CESANTIAS_ANTERIORES`
- `CO.PASS.CO_INTERESES_ANTERIORES`
- `CO.PASS.CO_PRIMA_ANTERIOR`
- `CO.PASS.CO_SALARIOS_PENDIENTES`
- `CO.PRIMA`
- `CO.PRIMA_ACCRUAL`
- `CO.SALARIO_MES`
- `CO.TRANSPORTE_MES`
- `CO.TRM_ADJUSTMENT`
- `CO.VACACIONES_PEND`
- `CO.VACACIONES_PROP`
- `CO.VACATION_ACCRUAL`
- `CO.VACATION_COMPENSATED`
- `CO.VACATION_ENJOYED`
- `CO.VAL.OT_LIMIT_DAY`
- `CO.VAL.OT_LIMIT_WEEK`
- `CO.VAL.SALARY_BELOW_MINIMUM`
- `CO.VAL.SALARY_TYPE`
- `CO.VAL.TERM_CESANTIAS_REGIME`
- `CO.VOLUNTARY_PENSION`
- `CO.WITHHOLDING_TAX`

## Riesgos reales que siguen abiertos

1. **Ninguna regla tiene validación profesional**: fuente oficial no es interpretación correcta ni implementación completa (ver docs/SOURCES_REGISTRY_2026.md).
2. **Ley 1393 (Colombia):** fórmula literal verificada, alcance del 'total de la remuneración' PENDING_VERIFICATION: cálculo PROVISIONAL (docs/CO_LEY_1393_AUDITORIA.md).
3. **Impuesto:** los 7 países reciben la retención como valor digitado; no hay motor tributario (capacidad `tax` NOT_IMPLEMENTED).
4. **Fuentes secundarias/pendientes:** tasas de salud/pensión/parafiscales de Colombia, UMA, RMV del Perú, SM/INSS de Brasil, ingreso mínimo de Chile desde mayo, SMVM de Argentina (ene-ago), intereses de cesantías, auxilio en la base de cesantías/prima, art. 76 TUO 728 (Perú).
5. **Interpretaciones abiertas en liquidación y horas extra:** divisores del valor hora (PE, AR, EC, MX), acumulación de recargos (CO), fracciones de año (MX, EC), décimo tercero de Ecuador (período), SIS desde ago-2026 en Chile (posible doble conteo), conversión de días hábiles a corridos del feriado (CL).
6. **Fuente primaria inaccesible:** el texto de la Cámara de Diputados de México no se pudo descargar; se usó el Orden Jurídico Nacional (reforma 30-sep-2024) y el decreto del DOF del 1-may-2026 por lectura automática.
7. **Períodos que cruzan el cambio de una referencia usada por una BASE** se bloquean (las bases no declaran política de partición); las reglas con SPLIT_BY_DAYS prorratean por días (aproximación para horas extra).
8. **Notas normativas, etiquetas de conceptos y advertencias:** disponibles en español (etiquetas también en inglés); los datos están en español.
9. **Seguridad:** sin autenticación ni CSRF; datos DEMO y reales comparten tablas (bandera `es_demo`). NO es un sistema seguro para producción.
10. **Recálculo histórico:** parcial (compara y explica; no genera el ajuste contable ni encadena recálculos).

