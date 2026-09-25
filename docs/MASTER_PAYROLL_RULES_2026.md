# Matriz Maestra Normativa 2026

> **Generado** por `tools/generate_payroll_docs.py` el 2026-09-25 desde `config/payroll/<PAIS>/2026/` (motor v1.1.0). No editar a mano: edite los datos y regenere.

**Estados.** `source.status`: OFFICIAL · SECONDARY · PENDING · CONFLICTING · NOT_APPLICABLE. `interpretation`: UNREVIEWED · INTERPRETED · VALIDATED · CONFLICTING. `professional_validation`: PENDING · VALIDATED (solo una persona puede firmarla; **ninguna lo está**). `implementation`: NOT_IMPLEMENTED · PARTIAL · IMPLEMENTED. Una fuente oficial NO implica interpretación correcta.

## CO — Colombia

- **Estado derivado del manifiesto:** `parcial` · ruta `NEW_ENGINE` · versión de reglas `CO-2026.2.0` · fecha normativa 2026-09-24 · moneda COP
- `local_payroll_engine`: true · `consolidation_context`: false
- **Cobertura:** 52 reglas — 31 implementadas, 21 parciales, 0 NOT_IMPLEMENTED · 37 sin fuente oficial · 52 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `ARL_RATE_CLASS_I` | NATIONAL | 0.00522 | ratio | 2026-01-01 | — | SECONDARY | Decreto 1772 de 1994, art. 13 (tabla de tarifas por clase de riesgo) https://coriesgos.com/blog/arl-independientes-colombia-2026 |
| `SMMLV` | NATIONAL | 1750905 | COP/mes | 2026-01-01 | — | OFFICIAL | Decreto 1469 de 2025 art. 1 (SMMLV 2026 = $1.750.905), suspendido provisionalmente por el Consejo de Estado (rad. 11001-03-25-000-2026-00004-00); Decr https://www.cancilleria.gov.co/normograma/compilacion/docs/decreto_0159_2026.htm |
| `SUNDAY_HOLIDAY_SURCHARGE` | NATIONAL | 0.80 | fracción sobre el salario ordinario | 2025-07-01 | 2026-06-30 | OFFICIAL | Ley 2466 de 2025 art. 14 (CST art. 179): recargo dominical/festivo 100 %, gradual: 80 % desde el 1-jul-2025, 90 % desde el 1-jul-2026, 100 % desde el  https://www.secretariasenado.gov.co/senado/basedoc/ley_2466_2025.html |
| `SUNDAY_HOLIDAY_SURCHARGE` | NATIONAL | 0.90 | fracción sobre el salario ordinario | 2026-07-01 | 2027-06-30 | OFFICIAL | Ley 2466 de 2025 art. 14 (CST art. 179): recargo dominical/festivo 100 %, gradual: 80 % desde el 1-jul-2025, 90 % desde el 1-jul-2026, 100 % desde el  https://www.secretariasenado.gov.co/senado/basedoc/ley_2466_2025.html |
| `SUNDAY_HOLIDAY_SURCHARGE` | NATIONAL | 1.00 | fracción sobre el salario ordinario | 2027-07-01 | — | OFFICIAL | Ley 2466 de 2025 art. 14 (CST art. 179): recargo dominical/festivo 100 %, gradual: 80 % desde el 1-jul-2025, 90 % desde el 1-jul-2026, 100 % desde el  https://www.secretariasenado.gov.co/senado/basedoc/ley_2466_2025.html |
| `TRANSPORT_ALLOWANCE` | NATIONAL | 249095 | COP/mes | 2026-01-01 | — | OFFICIAL | Decreto 1470 de 2025 art. 1-2 (Diario Oficial 53.350, 29-dic-2025) https://www.cancilleria.gov.co/normograma/compilacion/docs/decreto_1470_2025.htm |
| `WORKWEEK_HOURS` | NATIONAL | 44 | horas/semana | 2025-07-15 | 2026-07-14 | OFFICIAL | Ley 2101 de 2021, art. 3 (Diario Oficial 51.736, 15-jul-2021) https://www.cancilleria.gov.co/normograma/compilacion/docs/ley_2101_2021.htm |
| `WORKWEEK_HOURS` | NATIONAL | 42 | horas/semana | 2026-07-15 | — | OFFICIAL | Ley 2101 de 2021, art. 3 (Diario Oficial 51.736, 15-jul-2021) https://www.cancilleria.gov.co/normograma/compilacion/docs/ley_2101_2021.htm |

### Bases

| Base | Descripción | Límites | Fuente |
|---|---|---|---|
| `IBC` | Ingreso Base de Cotización (salud, pensión y FSP). Tope 25 SMMLV; mínimo 1 SMMLV. | {"maximum":{"value":{"reference":{"code":"SMMLV","multiple":"25"}},"enforcement":"ENFORCE… | OFFICIAL |
| `RISK_BASE` | Base de cotización a riesgos laborales (ARL), con el tope de 25 SMMLV. | {"maximum":{"value":{"reference":{"code":"SMMLV","multiple":"25"}},"enforcement":"ENFORCE… | PENDING |
| `PARAFISCAL_BASE` | Nómina mensual de salarios (Caja, SENA, ICBF). | — | SECONDARY |
| `BENEFIT_BASE` | Base de prestaciones sociales (prima, cesantías, intereses). | — | PENDING |
| `VACATION_BASE` | Base de la provisión de vacaciones. | — | PENDING |
| `EXONERATION_BASE` | Salario devengado en el mes para la exoneración del art. 114-1 ET. | — | SECONDARY |
| `CO.CESANTIAS_BASE` | Base de cesantías: salario (art. 253) + auxilio de transporte | — | OFFICIAL |
| `CO.PRIMA_BASE` | Base de prima de servicios: salario + auxilio de transporte | — | OFFICIAL |
| `CO.VACATION_BASE` | Base de vacaciones: salario ordinario, sin auxilio de transporte (art. 192) | — | OFFICIAL |
| `CO.INDEMNITY_BASE` | Salario para la indemnización del art. 64 (salario integral completo si aplica) | — | OFFICIAL |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `BASE_SALARY` | EARNING | valor_salario_devengado | IBC→INCLUDE; IBC→INCLUDE; RISK_BASE→INCLUDE; RISK_BASE→INCLUDE*; PARAFISCAL_BASE→INCLUDE; PARAFISCAL_BASE→INCLUDE*; BENEFIT_BASE→INCLUDE; VACATION_BASE→INCLUDE; EXONERATION_BASE→INCLUDE |
| `VACATION_ENJOYED` | EARNING | valor_vac_disfrutadas | IBC→INCLUDE; RISK_BASE→EXCLUDE*; PARAFISCAL_BASE→INCLUDE; BENEFIT_BASE→INCLUDE; VACATION_BASE→INCLUDE*; EXONERATION_BASE→INCLUDE |
| `VACATION_COMPENSATED` | EARNING | valor_vac_compensadas | IBC→INCLUDE*; RISK_BASE→EXCLUDE; PARAFISCAL_BASE→INCLUDE*; BENEFIT_BASE→EXCLUDE; VACATION_BASE→EXCLUDE; EXONERATION_BASE→INCLUDE |
| `INCAPACITY_EMPLOYER` | EARNING | incapacidad_empresa | IBC→INCLUDE; RISK_BASE→EXCLUDE; PARAFISCAL_BASE→EXCLUDE*; BENEFIT_BASE→INCLUDE; VACATION_BASE→INCLUDE*; EXONERATION_BASE→INCLUDE |
| `INCAPACITY_EPS` | EARNING | incapacidad_valor_eps | IBC→INCLUDE; RISK_BASE→EXCLUDE; PARAFISCAL_BASE→EXCLUDE*; BENEFIT_BASE→INCLUDE; VACATION_BASE→INCLUDE*; EXONERATION_BASE→INCLUDE |
| `BONUS_SALARY` | EARNING | bonos_comisiones | IBC→INCLUDE; RISK_BASE→INCLUDE; PARAFISCAL_BASE→INCLUDE; BENEFIT_BASE→INCLUDE; VACATION_BASE→INCLUDE*; EXONERATION_BASE→INCLUDE |
| `BONUS_NON_SALARY` | EARNING | bonificaciones_no_salariales | IBC→SPECIAL_RULE*; RISK_BASE→EXCLUDE; PARAFISCAL_BASE→EXCLUDE; BENEFIT_BASE→EXCLUDE; VACATION_BASE→EXCLUDE; EXONERATION_BASE→EXCLUDE |
| `TRM_ADJUSTMENT` | EARNING | ajuste_trm | IBC→INCLUDE*; RISK_BASE→INCLUDE*; PARAFISCAL_BASE→INCLUDE*; BENEFIT_BASE→INCLUDE*; VACATION_BASE→INCLUDE*; EXONERATION_BASE→INCLUDE* |
| `TRANSPORT_ALLOWANCE` | EARNING | auxilio_transporte | IBC→EXCLUDE*; RISK_BASE→EXCLUDE*; PARAFISCAL_BASE→EXCLUDE*; BENEFIT_BASE→INCLUDE*; VACATION_BASE→EXCLUDE; EXONERATION_BASE→EXCLUDE* |
| `WITHHOLDING_TAX` | EMPLOYEE_DEDUCTION | retencion_fuente | — |
| `AFC_DEDUCTION` | EMPLOYEE_DEDUCTION | descuento_afc | — |
| `VOLUNTARY_PENSION` | EMPLOYEE_DEDUCTION | aportes_voluntarios_pension | — |
| `LOANS_ADVANCES` | EMPLOYEE_DEDUCTION | prestamos_avances | — |
| `HEALTH_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_salud_empleado | — |
| `PENSION_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_pension_empleado | — |
| `FSP_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_fsp_empleado | — |
| `HEALTH_EMPLOYER` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `PENSION_EMPLOYER` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `ARL` | EMPLOYER_CONTRIBUTION | arl | — |
| `COMPENSATION_FUND` | EMPLOYER_CONTRIBUTION | caja_compensacion | — |
| `SENA` | EMPLOYER_CONTRIBUTION | sena | — |
| `ICBF` | EMPLOYER_CONTRIBUTION | icbf | — |
| `VACATION_ACCRUAL` | ACCRUAL | vacaciones | — |
| `PRIMA_ACCRUAL` | ACCRUAL | prima | — |
| `CESANTIAS_ACCRUAL` | ACCRUAL | cesantias | — |
| `CESANTIAS_INTEREST_ACCRUAL` | ACCRUAL | intereses_cesantias | — |
| `MONTHLY_WORK_HOURS` | INFO | — | — |
| `CO_T_SALARY_12M` | INFO | — | CO.CESANTIAS_BASE→INCLUDE; CO.VACATION_BASE→INCLUDE; CO.INDEMNITY_BASE→INCLUDE |
| `CO_T_SALARY_6M` | INFO | — | CO.PRIMA_BASE→INCLUDE |
| `CO_T_TRANSPORT` | INFO | — | CO.CESANTIAS_BASE→INCLUDE*; CO.PRIMA_BASE→INCLUDE* |
| `CO_T_DAYS_MONTH` | INFO | — | — |
| `CO_T_DAYS_YEAR` | INFO | — | — |
| `CO_T_CESANTIAS_PRIOR` | INFO | — | — |
| `CO_T_INTEREST_PRIOR` | INFO | — | — |
| `CO_T_PRIMA_PRIOR` | INFO | — | — |
| `CO_T_UNPAID_SALARY` | INFO | — | — |
| `CO_CESANTIAS` | EARNING | — | — |
| `CO_CESANTIAS_INTERESES` | EARNING | — | — |
| `CO_PRIMA` | EARNING | — | — |
| `CO_VACACIONES_PROPORCIONALES` | EARNING | — | — |
| `CO_VACACIONES_PENDIENTES` | EARNING | — | — |
| `CO_INDEMNIZACION_INDEFINIDO_MENOR_10` | EARNING | — | — |
| `CO_INDEMNIZACION_INDEFINIDO_MAYOR_IGUAL_10` | EARNING | — | — |
| `CO_INDEMNIZACION_TERMINO_FIJO` | EARNING | — | — |
| `CO_INDEMNIZACION_OBRA_LABOR` | EARNING | — | — |
| `CO_SALARIO_MES_TERMINACION` | EARNING | — | — |
| `CO_AUXILIO_TRANSPORTE_MES` | EARNING | — | — |
| `CO_CESANTIAS_ANTERIORES` | EARNING | — | — |
| `CO_INTERESES_ANTERIORES` | EARNING | — | — |
| `CO_PRIMA_ANTERIOR` | EARNING | — | — |
| `CO_SALARIOS_PENDIENTES` | EARNING | — | — |
| `CO_OVERTIME` | EARNING | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `CO.AFC_DEDUCTION.1` | AFC_DEDUCTION | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.AFC_DEDUCTION","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.ARL_CLASS_I.1` | ARL | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / ERROR | rate_on_base {"base":"RISK_BASE","rate":{"reference":{"code":"ARL_RATE_CLASS_I"}}} | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.BASE_SALARY.1` | BASE_SALARY | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.BONUS_NON_SALARY.1` | BONUS_NON_SALARY | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS_NON_SALARY","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.BONUS_SALARY.1` | BONUS_SALARY | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS_SALARY","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.CESANTIAS.1` | CO_CESANTIAS | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"CO.CESANTIAS_BASE"},"window":{"type":"CALENDAR_YEAR"},"count":… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.CESANTIAS_ACCRUAL.1` | CESANTIAS_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BENEFIT_BASE","rate":"1/12"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CO.CESANTIAS_INTERESES.1` | CO_CESANTIAS_INTERESES | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"CO_CESANTIAS"},"factor":"0.12","proration":{"type":"FIXED_DI… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CO.CESANTIAS_INTEREST_ACCRUAL.1` | CESANTIAS_INTEREST_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BENEFIT_BASE","rate":"0.01"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CO.COMPENSATION_FUND.1` | COMPENSATION_FUND | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PARAFISCAL_BASE","rate":"0.04"} | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.FSP_EMPLOYEE.1` | FSP_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / ERROR | bracket_rate_on_base {"base":"IBC","lookup":{"type":"BASE_MULTIPLE_OF_REFERENCE","reference":"SMMLV"… | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CO.HEALTH_EMPLOYEE.1` | HEALTH_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"IBC","rate":"0.04"} | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.HEALTH_EMPLOYER.1` | HEALTH_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"IBC","rate":"0.085"} | SECONDARY | INTERPRETED | PENDING | IMPLEMENTED |
| `CO.ICBF.1` | ICBF | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PARAFISCAL_BASE","rate":"0.03"} | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.IN.CO_T_CESANTIAS_PRIOR.1` | CO_T_CESANTIAS_PRIOR | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.cesantias_unpaid_prior","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.IN.CO_T_INTEREST_PRIOR.1` | CO_T_INTEREST_PRIOR | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.interest_unpaid_prior","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.IN.CO_T_PRIMA_PRIOR.1` | CO_T_PRIMA_PRIOR | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.prima_unpaid_prior","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.IN.CO_T_UNPAID_SALARY.1` | CO_T_UNPAID_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.unpaid_salary","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.IN.DAYS_MONTH.1` | CO_T_DAYS_MONTH | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"COMMERCIAL_DAYS_IN_MONTH"} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.IN.DAYS_YEAR.1` | CO_T_DAYS_YEAR | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"WINDOW_UNITS","window":{"type":"CALENDAR_YEAR"},"count":{"unit":"DA… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.IN.SALARY_12M.1` | CO_T_SALARY_12M | INFO | 2026-01-01→… | termination_date / ERROR | history_value {"history_input":"salary_history","method":"AVERAGE_IF_VARIED","window_months":… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.IN.SALARY_6M.1` | CO_T_SALARY_6M | INFO | 2026-01-01→… | termination_date / ERROR | history_value {"history_input":"salary_history","method":"AVERAGE_IF_VARIED","window_months":… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `CO.IN.TRANSPORT.1` | CO_T_TRANSPORT | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"reference":{"code":"TRANSPORT_ALLOWANCE"}}} | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CO.INCAPACITY_EMPLOYER.1` | INCAPACITY_EMPLOYER | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CO.INCAPACITY_EPS.1` | INCAPACITY_EPS | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.INCAPACITY_EPS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.INDEMNIZACION_FIJO.1` | CO_INDEMNIZACION_TERMINO_FIJO | EARNING | 2026-01-01→… | termination_date / ERROR | remaining_term_amount {"base":{"base":"CO.INDEMNITY_BASE"},"unit":"DAYS_360"} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.INDEMNIZACION_INDEF_GE10.1` | CO_INDEMNIZACION_INDEFINIDO_MAYOR_IGUAL_10 | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"CO.INDEMNITY_BASE"},"unit_days_per_month":"30","tiers":[{"over… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.INDEMNIZACION_INDEF_LT10.1` | CO_INDEMNIZACION_INDEFINIDO_MENOR_10 | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"CO.INDEMNITY_BASE"},"unit_days_per_month":"30","tiers":[{"over… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.INDEMNIZACION_OBRA.1` | CO_INDEMNIZACION_OBRA_LABOR | EARNING | 2026-01-01→… | termination_date / ERROR | remaining_term_amount {"base":{"base":"CO.INDEMNITY_BASE"},"unit":"DAYS_360","min_days":"15"} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.LOANS_ADVANCES.1` | LOANS_ADVANCES | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LOANS_ADVANCES","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.MONTHLY_WORK_HOURS.1` | MONTHLY_WORK_HOURS | INFO | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"reference":{"code":"WORKWEEK_HOURS"}},"factor":"5"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `CO.OVERTIME.1` | CO_OVERTIME | EARNING | 2026-01-01→… | period_end / SPLIT_BY_DAYS | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `CO.PASS.CO_CESANTIAS_ANTERIORES.1` | CO_CESANTIAS_ANTERIORES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"CO_T_CESANTIAS_PRIOR"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.PASS.CO_INTERESES_ANTERIORES.1` | CO_INTERESES_ANTERIORES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"CO_T_INTEREST_PRIOR"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.PASS.CO_PRIMA_ANTERIOR.1` | CO_PRIMA_ANTERIOR | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"CO_T_PRIMA_PRIOR"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.PASS.CO_SALARIOS_PENDIENTES.1` | CO_SALARIOS_PENDIENTES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"CO_T_UNPAID_SALARY"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.PENSION_EMPLOYEE.1` | PENSION_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"IBC","rate":"0.04"} | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.PENSION_EMPLOYER.1` | PENSION_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"IBC","rate":"0.12"} | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.PRIMA.1` | CO_PRIMA | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"CO.PRIMA_BASE"},"window":{"type":"RECURRING_PERIODS","periods"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.PRIMA_ACCRUAL.1` | PRIMA_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BENEFIT_BASE","rate":"1/12"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CO.SALARIO_MES.1` | CO_SALARIO_MES_TERMINACION | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"CO.VACATION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","d… | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `CO.SENA.1` | SENA | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PARAFISCAL_BASE","rate":"0.02"} | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.TRANSPORTE_MES.1` | CO_AUXILIO_TRANSPORTE_MES | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"CO_T_TRANSPORT"},"proration":{"type":"THIRTY_DAY_MONTH","day… | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `CO.TRANSPORT_ALLOWANCE.1` | TRANSPORT_ALLOWANCE | EARNING | 2026-01-01→… | period_end / ERROR | fixed_amount_prorated {"amount":{"reference":{"code":"TRANSPORT_ALLOWANCE"}},"proration":{"type":"THI… | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CO.TRM_ADJUSTMENT.1` | TRM_ADJUSTMENT | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.TRM_ADJUSTMENT","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.VACACIONES_PEND.1` | CO_VACACIONES_PENDIENTES | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"CO.VACATION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","d… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.VACACIONES_PROP.1` | CO_VACACIONES_PROPORCIONALES | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"CO.VACATION_BASE"},"window":{"type":"SERVICE_YEAR"},"count":{"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CO.VACATION_ACCRUAL.1` | VACATION_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"VACATION_BASE","rate":"15/360"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CO.VACATION_COMPENSATED.1` | VACATION_COMPENSATED | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.VACATION_ENJOYED.1` | VACATION_ENJOYED | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.VOLUNTARY_PENSION.1` | VOLUNTARY_PENSION | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.VOLUNTARY_PENSION","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.WITHHOLDING_TAX.1` | WITHHOLDING_TAX | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.WITHHOLDING_TAX","default":"0"}} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CO.VAL.ACCOUNTED_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días trabajados, de incapacidad y de vacaciones superan 30 (mes co | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.VAL.ARL_CLASS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Solo está implementada la clase de riesgo I de ARL; las clases II-V es | SECONDARY | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.VAL.INTEGRAL_MINIMUM.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: El salario integral no puede ser inferior a 13 SMMLV (10 SMMLV + 30% d | SECONDARY | INTERPRETED | PENDING | IMPLEMENTED |
| `CO.VAL.OT_LIMIT_DAY.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Horas extra diarias por encima de 2 (CST art. 167A, Ley 2466/2025 art. | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CO.VAL.OT_LIMIT_WEEK.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Horas extra semanales por encima de 12 (CST art. 167A, Ley 2466/2025 a | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CO.VAL.SALARY_BELOW_MINIMUM.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: El salario mensual es inferior al SMMLV (posible jornada parcial); ver | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.VAL.SALARY_TYPE.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: employment.salary_type debe ser ORDINARY o INTEGRAL. | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CO.VAL.TERM_CESANTIAS_REGIME.1` | — | VALIDATION | 2026-01-01→… | termination_date / USE_ANCHOR | VALIDATION: Solo está implementado el régimen de cesantías de la Ley 50/1990 (fond | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

> El redondeo de aportes en la PILA (múltiplos de 100/1000) no fue verificado; se conserva 2 decimales para no alterar el motor heredado.

### Brechas conocidas

- Retención en la fuente (tabla UVT): NOT_IMPLEMENTED.
- Piso de incapacidad (SMMLV) y tramos por día: PENDING_VERIFICATION.
- Mínimo de IBC (1 SMMLV) para periodos parciales: solo advertencia.
- Redondeo de aportes PILA: PENDING_VERIFICATION.
- Tratamiento de vacaciones compensadas, variables e incapacidades en cada base: interpretación sin revisar.
- ARL clases II-V: PENDING_VERIFICATION.
- Bases sin política de partición: un período que cruza el cambio de una referencia usada por una base se bloquea.
- Indemnización moratoria art. 65 CST: NOT_IMPLEMENTED.
- Intereses de cesantías (Ley 52/1975) y auxilio de transporte en bases de cesantías/prima: fuente PENDING_VERIFICATION.
- Ley 1393/2010 art. 30 (40 %): fórmula literal implementada; alcance del 'total de la remuneración' según UGPP/Consejo de Estado NO verificado (ver docs/CO_LEY_1393_AUDITORIA.md).
- Cesantías del régimen tradicional (contratos anteriores a 1991): NOT_IMPLEMENTED (validación bloquea).
- Retención en la fuente sobre la liquidación: NOT_IMPLEMENTED.

## MX — México

- **Estado derivado del manifiesto:** `parcial` · ruta `NEW_ENGINE` · versión de reglas `MX-2026.2.0` · fecha normativa 2026-09-24 · moneda MXN
- `local_payroll_engine`: true · `consolidation_context`: false
- **Cobertura:** 44 reglas — 8 implementadas, 36 parciales, 0 NOT_IMPLEMENTED · 26 sin fuente oficial · 44 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `SM_GENERAL_DAILY` | NATIONAL | 315.04 | MXN/día | 2026-01-01 | — | OFFICIAL | Resolución del H. Consejo de Representantes de la CONASAMI (3-dic-2025): salario mínimo general $315.04 y ZLFN $440.87 diarios, desde el 1-ene-2026 https://www.gob.mx/conasami/articulos/incremento-a-los-salarios-minimos-para-2026?idiom=es |
| `SM_ZLFN_DAILY` | NATIONAL | 440.87 | MXN/día | 2026-01-01 | — | OFFICIAL | Resolución del H. Consejo de Representantes de la CONASAMI (3-dic-2025): salario mínimo general $315.04 y ZLFN $440.87 diarios, desde el 1-ene-2026 https://www.gob.mx/conasami/articulos/incremento-a-los-salarios-minimos-para-2026?idiom=es |
| `UMA_DAILY` | NATIONAL | 113.14 | MXN/día | 2025-02-01 | 2026-01-31 | PENDING | Valor 2025 de la UMA inferido del incremento de 3.69% reportado; no verificado contra INEGI.  |
| `UMA_DAILY` | NATIONAL | 117.31 | MXN/día | 2026-02-01 | — | SECONDARY | INEGI, Comunicado de prensa 1/26 (UMA); DOF 9-ene-2026 https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/uma/uma2026.pdf |
| `WORKWEEK_HOURS` | NATIONAL | 48 | horas/semana | 2026-01-01 | 2026-12-31 | OFFICIAL | Decreto de reducción gradual de jornada (DOF 1-may-2026): 48 horas semanales en 2026 https://dof.gob.mx/nota_detalle.php?codigo=5786537&fecha=01%2F05%2F2026 |
| `WORKWEEK_HOURS` | NATIONAL | 46 | horas/semana | 2027-01-01 | 2027-12-31 | OFFICIAL | Decreto de reducción gradual de jornada a 40 horas (DOF 1-may-2026): arts. 59, 61, 66-69 LFT y transitorios (48 h en 2026, 46 en 2027, 44 en 2028, 42  https://dof.gob.mx/nota_detalle.php?codigo=5786537&fecha=01%2F05%2F2026 |
| `WORKWEEK_HOURS` | NATIONAL | 44 | horas/semana | 2028-01-01 | 2028-12-31 | OFFICIAL | Decreto de reducción gradual de jornada a 40 horas (DOF 1-may-2026): arts. 59, 61, 66-69 LFT y transitorios (48 h en 2026, 46 en 2027, 44 en 2028, 42  https://dof.gob.mx/nota_detalle.php?codigo=5786537&fecha=01%2F05%2F2026 |
| `WORKWEEK_HOURS` | NATIONAL | 42 | horas/semana | 2029-01-01 | 2029-12-31 | OFFICIAL | Decreto de reducción gradual de jornada a 40 horas (DOF 1-may-2026): arts. 59, 61, 66-69 LFT y transitorios (48 h en 2026, 46 en 2027, 44 en 2028, 42  https://dof.gob.mx/nota_detalle.php?codigo=5786537&fecha=01%2F05%2F2026 |
| `WORKWEEK_HOURS` | NATIONAL | 40 | horas/semana | 2030-01-01 | — | OFFICIAL | Decreto de reducción gradual de jornada a 40 horas (DOF 1-may-2026): arts. 59, 61, 66-69 LFT y transitorios (48 h en 2026, 46 en 2027, 44 en 2028, 42  https://dof.gob.mx/nota_detalle.php?codigo=5786537&fecha=01%2F05%2F2026 |

### Bases

| Base | Descripción | Límites | Fuente |
|---|---|---|---|
| `SBC` | Salario Base de Cotización IMSS (simplificado: salario diario × días con tope de 25 UMA; sin integración de pr | {"maximum":{"value":{"reference":{"code":"UMA_DAILY","multiple":"25"}},"scale_by":{"input… | PENDING |
| `MX_SALARY_EARNED_BASE` | Salario devengado del periodo (base de la provisión de aguinaldo). | — | PENDING |
| `MX.DAILY_BASE` | Salario diario (cuota diaria) para aguinaldo, vacaciones y salario | — | OFFICIAL |
| `MX.SDI_BASE` | Salario diario integrado para indemnizaciones (art. 89 y 84) | — | OFFICIAL |
| `MX.PA_BASE_GENERAL` | Salario para prima de antigüedad, tope 2 × salario mínimo general (zona general) | {"maximum":{"value":{"reference":{"code":"SM_GENERAL_DAILY"}},"scale_by":"2","enforcement… | OFFICIAL |
| `MX.PA_BASE_ZLFN` | Salario para prima de antigüedad, tope 2 × salario mínimo de la ZLFN | {"maximum":{"value":{"reference":{"code":"SM_ZLFN_DAILY"}},"scale_by":"2","enforcement":"… | OFFICIAL |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `SALARY_EARNED` | EARNING | valor_salario_devengado | MX_SALARY_EARNED_BASE→INCLUDE |
| `SBC_SALARY` | INFO | — | SBC→INCLUDE |
| `BONUS` | EARNING | bonos_comisiones | SBC→EXCLUDE*; MX_SALARY_EARNED_BASE→EXCLUDE |
| `IMSS_EE_EXCESS` | EMPLOYEE_DEDUCTION | aporte_salud_empleado | — |
| `IMSS_EE_CASH` | EMPLOYEE_DEDUCTION | aporte_salud_empleado | — |
| `IMSS_EE_PENSIONERS` | EMPLOYEE_DEDUCTION | aporte_salud_empleado | — |
| `IMSS_EE_DISABILITY` | EMPLOYEE_DEDUCTION | aporte_pension_empleado | — |
| `IMSS_EE_RETIREMENT` | EMPLOYEE_DEDUCTION | aporte_pension_empleado | — |
| `INFONAVIT_CREDIT` | EMPLOYEE_DEDUCTION | descuento_credito_vivienda | — |
| `LOANS` | EMPLOYEE_DEDUCTION | prestamos_avances | — |
| `ISR_WITHHOLDING` | EMPLOYEE_DEDUCTION | retencion_impuesto_renta | — |
| `IMSS_ER_FIXED` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `IMSS_ER_EXCESS` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `IMSS_ER_CASH` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `IMSS_ER_PENSIONERS` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `IMSS_ER_NURSERY` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `IMSS_ER_DISABILITY` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `IMSS_ER_RETIREMENT` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `IMSS_ER_SEVERANCE_OLD_AGE` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `IMSS_ER_RISK` | EMPLOYER_CONTRIBUTION | aporte_riesgo_laboral_empleador | — |
| `INFONAVIT_ER` | EMPLOYER_CONTRIBUTION | aporte_vivienda_empleador | — |
| `AGUINALDO_ACCRUAL` | ACCRUAL | prima | — |
| `MX_T_DAILY_SALARY` | INFO | — | MX.DAILY_BASE→INCLUDE; MX.SDI_BASE→INCLUDE; MX.PA_BASE_GENERAL→INCLUDE; MX.PA_BASE_ZLFN→INCLUDE |
| `MX_T_DAILY_EXTRA` | INFO | — | MX.SDI_BASE→INCLUDE |
| `MX_T_UNPAID_SALARY` | INFO | — | — |
| `MX_T_VACATION_DAYS` | INFO | — | — |
| `MX_T_VACATION_DAYS_PRORATED` | INFO | — | — |
| `MX_T_VACATION_DAYS_DUE` | INFO | — | — |
| `MX_T_SDI_AGUINALDO` | INFO | — | MX.SDI_BASE→INCLUDE |
| `MX_T_SDI_VAC_PREMIUM` | INFO | — | MX.SDI_BASE→INCLUDE |
| `MX_AGUINALDO_PROPORCIONAL` | EARNING | — | — |
| `MX_VACACIONES` | EARNING | — | — |
| `MX_PRIMA_VACACIONAL` | EARNING | — | — |
| `MX_INDEMNIZACION_3_MESES` | EARNING | — | — |
| `MX_INDEMNIZACION_20_DIAS` | EARNING | — | — |
| `MX_INDEMNIZACION_PLAZO_DETERMINADO` | EARNING | — | — |
| `MX_PRIMA_ANTIGUEDAD_GENERAL` | EARNING | — | — |
| `MX_PRIMA_ANTIGUEDAD_ZLFN` | EARNING | — | — |
| `MX_T_DAYS_MONTH` | INFO | — | — |
| `MX_SALARIO_MES_TERMINACION` | EARNING | — | — |
| `MX_SALARIOS_PENDIENTES` | EARNING | — | — |
| `MX_OVERTIME` | EARNING | — | — |
| `MX_SUNDAY_PREMIUM` | EARNING | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `MX.AGUINALDO.1` | MX_AGUINALDO_PROPORCIONAL | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"MX.DAILY_BASE"},"factor":"15","window":{"type":"CALENDAR_YEAR"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `MX.AGUINALDO_ACCRUAL.1` | AGUINALDO_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"MX_SALARY_EARNED_BASE","rate":"0.0417"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.BONUS.1` | BONUS | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.IMSS_EE_CASH.1` | IMSS_EE_CASH | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.0025"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_EE_DISABILITY.1` | IMSS_EE_DISABILITY | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.00625"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_EE_EXCESS.1` | IMSS_EE_EXCESS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_excess {"base":"SBC","threshold":{"reference":{"code":"UMA_DAILY","multiple":"3"}},"sc… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_EE_PENSIONERS.1` | IMSS_EE_PENSIONERS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.00375"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_EE_RETIREMENT.1` | IMSS_EE_RETIREMENT | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.01125"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_CASH.1` | IMSS_ER_CASH | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.007"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_DISABILITY.1` | IMSS_ER_DISABILITY | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.0175"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_EXCESS.1` | IMSS_ER_EXCESS | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_excess {"base":"SBC","threshold":{"reference":{"code":"UMA_DAILY","multiple":"3"}},"sc… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_FIXED.1` | IMSS_ER_FIXED | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_reference_amount {"amount":{"reference":{"code":"UMA_DAILY"}},"scale_by":{"input":"time.worked_d… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_NURSERY.1` | IMSS_ER_NURSERY | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.01"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_PENSIONERS.1` | IMSS_ER_PENSIONERS | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.0105"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_RETIREMENT.1` | IMSS_ER_RETIREMENT | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.02"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_RISK.1` | IMSS_ER_RISK | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.005"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IMSS_ER_SEVERANCE_OLD_AGE.1` | IMSS_ER_SEVERANCE_OLD_AGE | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.0524"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.IN.DAILY_SALARY.1` | MX_T_DAILY_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"FIXED_DIVI… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.IN.DAYS_MONTH.1` | MX_T_DAYS_MONTH | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"COMMERCIAL_DAYS_IN_MONTH"} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.IN.MX_T_DAILY_EXTRA.1` | MX_T_DAILY_EXTRA | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.extra_daily_benefits","default":"0"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.IN.MX_T_UNPAID_SALARY.1` | MX_T_UNPAID_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.unpaid_salary","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.IN.SDI_AGUINALDO.1` | MX_T_SDI_AGUINALDO | INFO | 2026-01-01→… | termination_date / ERROR | rate_on_base {"base":"MX.DAILY_BASE","rate":"15/365"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.IN.SDI_VAC_PREMIUM.1` | MX_T_SDI_VAC_PREMIUM | INFO | 2026-01-01→… | termination_date / ERROR | rate_on_base {"base":"MX.DAILY_BASE","rate":"25/36500","factor":{"line":"MX_T_VACATION_DAYS"… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.IN.VAC_DAYS.1` | MX_T_VACATION_DAYS | INFO | 2026-01-01→… | termination_date / ERROR | service_quantity {"years_basis":"COMPLETED_YEARS","year_offset":1,"table":[{"min":1,"max":1,"val… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.IN.VAC_DUE.1` | MX_T_VACATION_DAYS_DUE | INFO | 2026-01-01→… | termination_date / ERROR | adjusted_quantity {"quantity":{"line":"MX_T_VACATION_DAYS_PRORATED"},"add":[{"input":"vacation_hi… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.IN.VAC_PRORATED.1` | MX_T_VACATION_DAYS_PRORATED | INFO | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"line":"MX_T_VACATION_DAYS"},"window":{"type":"SERVICE_YEAR"},"count":… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.INDEMNIZACION_20D.1` | MX_INDEMNIZACION_20_DIAS | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"MX.SDI_BASE"},"unit_days_per_month":"1","tiers":[{"over_years"… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.INDEMNIZACION_3M.1` | MX_INDEMNIZACION_3_MESES | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"MX.SDI_BASE"},"factor":"90"} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `MX.INDEMNIZACION_PLAZO.1` | MX_INDEMNIZACION_PLAZO_DETERMINADO | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"MX.SDI_BASE"},"unit_days_per_month":"1","tiers":[{"over_years"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `MX.INFONAVIT_CREDIT.1` | INFONAVIT_CREDIT | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.HOUSING_CREDIT","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.INFONAVIT_ER.1` | INFONAVIT_ER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"SBC","rate":"0.05"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.ISR_WITHHOLDING.1` | ISR_WITHHOLDING | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.ISR_WITHHOLDING","default":"0"}} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.LOANS.1` | LOANS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LOANS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.OVERTIME.1` | MX_OVERTIME | EARNING | 2026-01-01→2026-04-30 | period_end / ERROR | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.OVERTIME.2` | MX_OVERTIME | EARNING | 2026-05-01→… | period_end / ERROR | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.PRIMA_ANTIGUEDAD_GENERAL.1` | MX_PRIMA_ANTIGUEDAD_GENERAL | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"MX.PA_BASE_GENERAL"},"unit_days_per_month":"1","tiers":[{"over… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.PRIMA_ANTIGUEDAD_ZLFN.1` | MX_PRIMA_ANTIGUEDAD_ZLFN | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"MX.PA_BASE_ZLFN"},"unit_days_per_month":"1","tiers":[{"over_ye… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.PRIMA_VACACIONAL.1` | MX_PRIMA_VACACIONAL | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"MX_VACACIONES"},"factor":"0.25"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `MX.REM_PENDIENTES.1` | MX_SALARIOS_PENDIENTES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"MX_T_UNPAID_SALARY"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.SALARIO_MES.1` | MX_SALARIO_MES_TERMINACION | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"MX.DAILY_BASE"},"factor":{"line":"MX_T_DAYS_MONTH"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `MX.SALARY_EARNED.1` | SALARY_EARNED | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.SBC_SALARY.1` | SBC_SALARY | INFO | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `MX.SUNDAY_PREMIUM.1` | MX_SUNDAY_PREMIUM | EARNING | 2026-01-01→… | period_end / ERROR | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `MX.VACACIONES.1` | MX_VACACIONES | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"MX.DAILY_BASE"},"factor":{"line":"MX_T_VACATION_DAYS_DUE"}} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `MX.VAL.INCAPACITY_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días de incapacidad superan los días trabajados. | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `MX.VAL.WORKED_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días trabajados superan 30. | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- ISR (art. 96 LISR) y subsidio: NOT_IMPLEMENTED.
- SBC: integración de prestaciones y bonos pendiente.
- Cesantía y vejez: tabla progresiva pendiente.
- Prima de riesgo IMSS por empresa.
- PTU, prima vacacional, vacaciones.
- Impuesto estatal sobre nómina y salario mínimo de zona fronteriza en cálculos.
- Períodos que cruzan el cambio de UMA (1-feb) se bloquean: las bases no declaran política de partición.
- Salarios vencidos (art. 48), PTU y reparto: NOT_IMPLEMENTED.
- Salario integrado: solo prestaciones de ley (aguinaldo + prima vacacional) más lo informado.
- Fracción de año en indemnización de 20 días y en prima de antigüedad: prorrateo sin verificar.
- Tope de 2 salarios mínimos de la prima de antigüedad: art. 486 no reproducido en la extracción.
- Horas extra 2028-2030 (10/11/12 h): versiones futuras sin cargar.
- El sitio de la Cámara de Diputados no fue accesible: el texto primario salió del Orden Jurídico Nacional (reforma 30-sep-2024).

## PE — Perú

- **Estado derivado del manifiesto:** `parcial` · ruta `NEW_ENGINE` · versión de reglas `PE-2026.2.0` · fecha normativa 2026-09-24 · moneda PEN
- `local_payroll_engine`: true · `consolidation_context`: false
- **Cobertura:** 31 reglas — 15 implementadas, 16 parciales, 0 NOT_IMPLEMENTED · 20 sin fuente oficial · 31 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `RMV` | NATIONAL | 1130 | PEN/mes | 2025-01-01 | — | SECONDARY | D.S. N° 006-2024-TR (RMV S/ 1,130), según fuentes secundarias https://trendperu.com/sueldo-minimo-peru-2026/ |
| `WORKWEEK_HOURS` | NATIONAL | 48 | horas/semana | 2026-01-01 | — | PENDING | Jornada máxima. Valor tomado del motor heredado / NORMATIVA_PAISES.md (Perú), resumen interno sin cita oficial verificada en esta ejecución.  |

### Bases

| Base | Descripción | Límites | Fuente |
|---|---|---|---|
| `PE_REMUNERATION_BASE` | Remuneración base de aportes AFP, EsSalud y provisiones (simplificada). | — | PENDING |
| `PE.CTS_BASE` | Remuneración computable para CTS (art. 9, 16, 18 TUO CTS) | — | OFFICIAL |
| `PE.GRATIFICATION_BASE` | Remuneración computable para gratificación (D.S. 005-2002-TR art. 3.1/5.3) | — | OFFICIAL |
| `PE.VACATION_BASE` | Remuneración vacacional (D.S. 012-92-TR art. 16: computable CTS sin periódicas) | — | OFFICIAL |
| `PE.INDEMNITY_BASE` | Remuneración ordinaria mensual para la indemnización por despido arbitrario | — | OFFICIAL |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `REMUNERATION` | EARNING | valor_salario_devengado | PE_REMUNERATION_BASE→INCLUDE |
| `BONUS` | EARNING | bonos_comisiones | PE_REMUNERATION_BASE→EXCLUDE* |
| `FAMILY_ALLOWANCE` | EARNING | asignacion_familiar | PE_REMUNERATION_BASE→EXCLUDE* |
| `AFP_MANDATORY` | EMPLOYEE_DEDUCTION | aporte_pension_privada_empleado | — |
| `AFP_INSURANCE` | EMPLOYEE_DEDUCTION | aporte_pension_privada_empleado | — |
| `AFP_COMMISSION` | EMPLOYEE_DEDUCTION | aporte_pension_privada_empleado | — |
| `LOANS` | EMPLOYEE_DEDUCTION | prestamos_avances | — |
| `INCOME_TAX_5TH` | EMPLOYEE_DEDUCTION | retencion_impuesto_renta | — |
| `ESSALUD` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `GRATIFICATION_ACCRUAL` | ACCRUAL | prima | — |
| `CTS_ACCRUAL` | ACCRUAL | cesantias | — |
| `PE_T_BASIC` | INFO | — | PE.CTS_BASE→INCLUDE; PE.GRATIFICATION_BASE→INCLUDE; PE.VACATION_BASE→INCLUDE; PE.INDEMNITY_BASE→INCLUDE |
| `PE_T_FAMILY` | INFO | — | PE.CTS_BASE→INCLUDE; PE.GRATIFICATION_BASE→INCLUDE; PE.VACATION_BASE→INCLUDE; PE.INDEMNITY_BASE→INCLUDE |
| `PE_T_VARIABLE` | INFO | — | PE.CTS_BASE→INCLUDE; PE.GRATIFICATION_BASE→INCLUDE; PE.VACATION_BASE→INCLUDE; PE.INDEMNITY_BASE→INCLUDE |
| `PE_T_LAST_GRATIFICATION` | INFO | — | PE.CTS_BASE→INCLUDE |
| `PE_T_GRATIFICATION_PRIOR` | INFO | — | — |
| `PE_T_UNPAID_SALARY` | INFO | — | — |
| `PE_CTS_TRUNCA` | EARNING | — | — |
| `PE_GRATIFICACION_TRUNCA` | EARNING | — | — |
| `PE_BONIFICACION_EXTRAORDINARIA` | EARNING | — | — |
| `PE_VACACIONES_TRUNCAS` | EARNING | — | — |
| `PE_VACACIONES_ADQUIRIDAS` | EARNING | — | — |
| `PE_VACACIONES_INDEMNIZACION` | EARNING | — | — |
| `PE_T_PROBATION_MONTHS` | INFO | — | — |
| `PE_INDEMNIZACION_DESPIDO_ARBITRARIO` | EARNING | — | — |
| `PE_INDEMNIZACION_PLAZO_FIJO` | EARNING | — | — |
| `PE_SALARIO_PENDIENTE_DIAS` | EARNING | — | — |
| `PE_T_DAYS_WORKED` | INFO | — | — |
| `PE_GRATIFICACION_ANTERIOR` | EARNING | — | — |
| `PE_REMUNERACIONES_PENDIENTES` | EARNING | — | — |
| `PE_OVERTIME` | EARNING | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `PE.AFP_COMMISSION.1` | AFP_COMMISSION | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PE_REMUNERATION_BASE","rate":"0.0155"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `PE.AFP_INSURANCE.1` | AFP_INSURANCE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PE_REMUNERATION_BASE","rate":"0.0137"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `PE.AFP_MANDATORY.1` | AFP_MANDATORY | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PE_REMUNERATION_BASE","rate":"0.10"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `PE.BONIFICACION_EXTRAORDINARIA.1` | PE_BONIFICACION_EXTRAORDINARIA | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"PE_GRATIFICACION_TRUNCA"},"factor":"0.09"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `PE.BONUS.1` | BONUS | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.CTS_ACCRUAL.1` | CTS_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PE_REMUNERATION_BASE","rate":"1/12"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `PE.CTS_TRUNCA.1` | PE_CTS_TRUNCA | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"PE.CTS_BASE"},"window":{"type":"RECURRING_PERIODS","periods":[… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `PE.ESSALUD.1` | ESSALUD | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PE_REMUNERATION_BASE","rate":"0.09"} | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.FAMILY_ALLOWANCE.1` | FAMILY_ALLOWANCE | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.FAMILY_ALLOWANCE","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.GRATIFICACION_TRUNCA.1` | PE_GRATIFICACION_TRUNCA | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"PE.GRATIFICATION_BASE"},"window":{"type":"RECURRING_PERIODS","… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `PE.GRATIFICATION_ACCRUAL.1` | GRATIFICATION_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"PE_REMUNERATION_BASE","rate":"1/6"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `PE.IN.DAYS_WORKED.1` | PE_T_DAYS_WORKED | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"COMMERCIAL_DAYS_IN_MONTH"} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.IN.PE_T_BASIC.1` | PE_T_BASIC | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"employment.monthly_salary"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.IN.PE_T_FAMILY.1` | PE_T_FAMILY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.family_allowance","default":"0"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.IN.PE_T_GRATIFICATION_PRIOR.1` | PE_T_GRATIFICATION_PRIOR | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.gratification_unpaid_prior","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.IN.PE_T_LAST_GRATIFICATION.1` | PE_T_LAST_GRATIFICATION | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.last_gratification","default":"0"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.IN.PE_T_PROBATION_MONTHS.1` | PE_T_PROBATION_MONTHS | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"employment.probation_months","default":"3"}} | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.IN.PE_T_UNPAID_SALARY.1` | PE_T_UNPAID_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.unpaid_salary","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.IN.PE_T_VARIABLE.1` | PE_T_VARIABLE | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.regular_variable_average","default":"0"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.INCOME_TAX_5TH.1` | INCOME_TAX_5TH | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.INCOME_TAX_5TH","default":"0"}} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `PE.INDEMNIZACION_DESPIDO.1` | PE_INDEMNIZACION_DESPIDO_ARBITRARIO | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"PE.INDEMNITY_BASE"},"unit_days_per_month":"1","tiers":[{"over_… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `PE.INDEMNIZACION_PLAZO_FIJO.1` | PE_INDEMNIZACION_PLAZO_FIJO | EARNING | 2026-01-01→… | termination_date / ERROR | remaining_term_amount {"base":{"base":"PE.INDEMNITY_BASE"},"unit":"MONTHS_AND_DAYS","multiplier":"1.5… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `PE.LOANS.1` | LOANS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LOANS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.OVERTIME.1` | PE_OVERTIME | EARNING | 2026-01-01→… | period_end / ERROR | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `PE.PASS.GRATIFICACION_ANTERIOR.1` | PE_GRATIFICACION_ANTERIOR | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"PE_T_GRATIFICATION_PRIOR"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.REMUNERATION.1` | REMUNERATION | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.REM_PENDIENTES.1` | PE_REMUNERACIONES_PENDIENTES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"PE_T_UNPAID_SALARY"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.SALARIO_MES_CESE.1` | PE_SALARIO_PENDIENTE_DIAS | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"PE.VACATION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","d… | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `PE.VACACIONES_ADQUIRIDAS.1` | PE_VACACIONES_ADQUIRIDAS | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"PE.VACATION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","d… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `PE.VACACIONES_INDEMNIZACION.1` | PE_VACACIONES_INDEMNIZACION | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"PE.VACATION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","d… | SECONDARY | UNREVIEWED | PENDING | PARTIAL |
| `PE.VACACIONES_TRUNCAS.1` | PE_VACACIONES_TRUNCAS | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"PE.VACATION_BASE"},"window":{"type":"SERVICE_YEAR"},"count":{"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `PE.VAL.TERM_REGIME.1` | — | VALIDATION | 2026-01-01→… | termination_date / USE_ANCHOR | VALIDATION: Solo está implementado el régimen laboral general (D.Leg. 728). MYPE/a | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `PE.VAL.WORKED_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días trabajados superan 30 (mes comercial). | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- ONP y selector AFP/ONP.
- Renta de quinta categoría.
- Bonificación extraordinaria 9%.
- Régimen laboral (MYPE, agrario).
- Regímenes MYPE/agrario/construcción civil: NOT_IMPLEMENTED (validación bloquea la corrida).
- Indemnización de plazo fijo (art. 76 TUO 728): fuente PENDING_VERIFICATION.
- Descuento de días no laborados (1/30) en gratificación y CTS no modelado.
- Renta de quinta y retenciones sobre la liquidación: NOT_IMPLEMENTED.
- Cese antes del 15-jul/15-dic: la gratificación ordinaria del semestre anterior aún no pagada es un dato de entrada (amounts.gratification_unpaid_prior).

## CL — Chile

- **Estado derivado del manifiesto:** `parcial` · ruta `NEW_ENGINE` · versión de reglas `CL-2026.2.0` · fecha normativa 2026-09-24 · moneda CLP
- `local_payroll_engine`: true · `consolidation_context`: false
- **Cobertura:** 29 reglas — 14 implementadas, 15 parciales, 0 NOT_IMPLEMENTED · 16 sin fuente oficial · 29 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `INDEMNITY_CAP_UF` | NATIONAL | 90 | UF | 2026-01-01 | — | OFFICIAL | Código del Trabajo art. 172: ninguna remuneración mensual superior a 90 UF del último día del mes anterior al pago para las indemnizaciones de los art https://www.bcn.cl/leychile/navegar?idNorma=207436 |
| `MIN_INCOME` | NATIONAL | 539000 | CLP/mes | 2026-01-01 | 2026-04-30 | OFFICIAL | Ley N° 21.751 (D.O. 28-jun-2025): ingreso mínimo mensual $539.000 desde el 1-ene-2026 https://www.mintrab.gob.cl/ya-es-una-realidad-diario-oficial-publica-ley-21-751-que-reajusta-el-monto-del-ingreso-minimo-mensual/ |
| `MIN_INCOME` | NATIONAL | 553553 | CLP/mes | 2026-05-01 | — | PENDING | Fuentes secundarias (Senado, Garrigues, Carey) indican $553.553 desde el 1-may-2026, pero la página oficial de la Ley 21.751 consultada solo llega a $  |
| `TAX_CAP_UF_PENSION` | NATIONAL | 89.9 | UF | 2026-01-01 | 2026-01-31 | OFFICIAL | Res. exenta SP N°27 de 9-ene-2026 (89,9 UF desde el 1-ene) y N°237 de 2026 (90,0 UF desde el 1-feb-2026): tope imponible AFP, salud y accidentes del t https://www.dt.gob.cl/portal/1628/w3-article-118076.html |
| `TAX_CAP_UF_PENSION` | NATIONAL | 90.0 | UF | 2026-02-01 | — | OFFICIAL | Res. exenta SP N°27 de 9-ene-2026 (89,9 UF desde el 1-ene) y N°237 de 2026 (90,0 UF desde el 1-feb-2026): tope imponible AFP, salud y accidentes del t https://www.dt.gob.cl/portal/1628/w3-article-118076.html |
| `TAX_CAP_UF_UNEMPLOYMENT` | NATIONAL | 135.1 | UF | 2026-01-01 | 2026-01-31 | OFFICIAL | Res. exenta SP N°26 de 9-ene-2026 (135,1 UF desde el 1-ene) y N°236 de 2026 (135,2 UF desde el 1-feb-2026): tope imponible del seguro de cesantía https://www.dt.gob.cl/portal/1628/w3-article-118077.html |
| `TAX_CAP_UF_UNEMPLOYMENT` | NATIONAL | 135.2 | UF | 2026-02-01 | — | OFFICIAL | Res. exenta SP N°26 de 9-ene-2026 (135,1 UF desde el 1-ene) y N°236 de 2026 (135,2 UF desde el 1-feb-2026): tope imponible del seguro de cesantía https://www.dt.gob.cl/portal/1628/w3-article-118077.html |
| `WORKWEEK_HOURS` | NATIONAL | 44 | horas/semana | 2024-04-26 | 2026-04-25 | OFFICIAL | Ley N° 21.561 (jornada de 40 horas): 44 h desde 26-abr-2024, 42 h desde 26-abr-2026, 40 h desde 26-abr-2028 https://www.mintrab.gob.cl/40horas/ |
| `WORKWEEK_HOURS` | NATIONAL | 42 | horas/semana | 2026-04-26 | 2028-04-25 | OFFICIAL | Ley N° 21.561 (jornada de 40 horas): 44 h desde 26-abr-2024, 42 h desde 26-abr-2026, 40 h desde 26-abr-2028 https://www.mintrab.gob.cl/40horas/ |
| `WORKWEEK_HOURS` | NATIONAL | 40 | horas/semana | 2028-04-26 | — | OFFICIAL | Ley N° 21.561 (jornada de 40 horas): 44 h desde 26-abr-2024, 42 h desde 26-abr-2026, 40 h desde 26-abr-2028 https://www.mintrab.gob.cl/40horas/ |

### Bases

| Base | Descripción | Límites | Fuente |
|---|---|---|---|
| `CL_TAXABLE_BASE` | Renta imponible simplificada (solo REMUNERATION) con el tope imponible mensual en UF (AFP, salud, accidentes). | {"maximum":{"value":{"reference":{"code":"UF"}},"scale_by":{"reference":{"code":"TAX_CAP_… | OFFICIAL |
| `CL_UNEMPLOYMENT_BASE` | Renta imponible simplificada con el tope imponible del seguro de cesantía en UF. | {"maximum":{"value":{"reference":{"code":"UF"}},"scale_by":{"reference":{"code":"TAX_CAP_… | OFFICIAL |
| `CL.INDEMNITY_BASE` | Última remuneración mensual, con tope de 90 UF del último día del mes anterior al pago (art. 172) | {"maximum":{"value":{"reference":{"code":"UF","multiple":"90","date_rule":{"type":"PREVIO… | OFFICIAL |
| `CL.VACATION_BASE` | Remuneración íntegra para el feriado (art. 71) | — | OFFICIAL |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `REMUNERATION` | EARNING | valor_salario_devengado | CL_TAXABLE_BASE→INCLUDE; CL_UNEMPLOYMENT_BASE→INCLUDE |
| `BONUS` | EARNING | bonos_comisiones | CL_TAXABLE_BASE→EXCLUDE*; CL_UNEMPLOYMENT_BASE→EXCLUDE* |
| `LEGAL_GRATIFICATION` | EARNING | gratificacion_legal | CL_TAXABLE_BASE→EXCLUDE*; CL_UNEMPLOYMENT_BASE→EXCLUDE* |
| `AFP_CONTRIBUTION` | EMPLOYEE_DEDUCTION | aporte_pension_privada_empleado | — |
| `AFP_COMMISSION` | EMPLOYEE_DEDUCTION | aporte_pension_privada_empleado | — |
| `AFC_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_pension_privada_empleado | — |
| `HEALTH` | EMPLOYEE_DEDUCTION | aporte_salud_empleado | — |
| `LOANS` | EMPLOYEE_DEDUCTION | prestamos_avances | — |
| `SINGLE_TAX` | EMPLOYEE_DEDUCTION | retencion_impuesto_renta | — |
| `SIS_EMPLOYER` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `PENSION_REFORM_EMPLOYER` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `MUTUAL_EMPLOYER` | EMPLOYER_CONTRIBUTION | aporte_riesgo_laboral_empleador | — |
| `AFC_EMPLOYER` | EMPLOYER_CONTRIBUTION | fondo_garantia_empleador | — |
| `VACATION_ACCRUAL` | ACCRUAL | vacaciones | — |
| `CL_T_LAST_MONTHLY_REMUNERATION` | INFO | — | CL.INDEMNITY_BASE→INCLUDE; CL.VACATION_BASE→INCLUDE |
| `CL_T_UNPAID_SALARY` | INFO | — | — |
| `CL_INDEMNIZACION_ANOS_SERVICIO` | EARNING | — | — |
| `CL_INDEMNIZACION_AVISO_PREVIO` | EARNING | — | — |
| `CL_T_VACATION_DAYS` | INFO | — | — |
| `CL_T_VACATION_DAYS_PRORATED` | INFO | — | — |
| `CL_T_VACATION_DAYS_DUE` | INFO | — | — |
| `CL_FERIADO_PROPORCIONAL` | EARNING | — | — |
| `CL_T_DAYS_MONTH` | INFO | — | — |
| `CL_REMUNERACION_MES_TERMINACION` | EARNING | — | — |
| `CL_REMUNERACIONES_PENDIENTES` | EARNING | — | — |
| `CL_OVERTIME` | EARNING | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `CL.AFC_EMPLOYEE.1` | AFC_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_UNEMPLOYMENT_BASE","rate":"0.006"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CL.AFC_EMPLOYER.1` | AFC_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_UNEMPLOYMENT_BASE","rate":"0.024"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CL.AFP_COMMISSION.1` | AFP_COMMISSION | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.01"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CL.AFP_CONTRIBUTION.1` | AFP_CONTRIBUTION | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.10"} | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.AVISO_PREVIO.1` | CL_INDEMNIZACION_AVISO_PREVIO | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"CL.INDEMNITY_BASE"},"factor":"1"} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CL.BONUS.1` | BONUS | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.FERIADO.1` | CL_FERIADO_PROPORCIONAL | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"CL.VACATION_BASE"},"factor":"7/5","proration":{"type":"FIXED… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `CL.HEALTH.1` | HEALTH | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.07"} | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.IN.CL_T_UNPAID_SALARY.1` | CL_T_UNPAID_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.unpaid_salary","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.IN.DAYS_MONTH.1` | CL_T_DAYS_MONTH | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"COMMERCIAL_DAYS_IN_MONTH"} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.IN.LAST_REMUNERATION.1` | CL_T_LAST_MONTHLY_REMUNERATION | INFO | 2026-01-01→… | termination_date / ERROR | history_value {"history_input":"salary_history","method":"AVERAGE_IF_VARIED","window_months":… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CL.IN.VAC_DAYS.1` | CL_T_VACATION_DAYS | INFO | 2026-01-01→… | termination_date / ERROR | service_quantity {"years_basis":"COMPLETED_YEARS_PLUS_PRIOR","prior_cap":"10","linear":{"base_qu… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CL.IN.VAC_DUE.1` | CL_T_VACATION_DAYS_DUE | INFO | 2026-01-01→… | termination_date / ERROR | adjusted_quantity {"quantity":{"line":"CL_T_VACATION_DAYS_PRORATED"},"add":[{"input":"vacation_hi… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `CL.IN.VAC_PRORATED.1` | CL_T_VACATION_DAYS_PRORATED | INFO | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"line":"CL_T_VACATION_DAYS"},"window":{"type":"SERVICE_YEAR"},"count":… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CL.INDEMNIZACION_ANOS.1` | CL_INDEMNIZACION_ANOS_SERVICIO | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"CL.INDEMNITY_BASE"},"unit_days_per_month":"30","tiers":[{"over… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CL.LEGAL_GRATIFICATION.1` | LEGAL_GRATIFICATION | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LEGAL_GRATIFICATION","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.LOANS.1` | LOANS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LOANS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.MUTUAL_EMPLOYER.1` | MUTUAL_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.009"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CL.OVERTIME.1` | CL_OVERTIME | EARNING | 2026-01-01→… | period_end / SPLIT_BY_DAYS | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `CL.PENSION_REFORM_EMPLOYER.1` | PENSION_REFORM_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→2026-07-31 | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.01"} | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CL.PENSION_REFORM_EMPLOYER.2` | PENSION_REFORM_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-08-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.035"} | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CL.REMUNERATION.1` | REMUNERATION | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.REM_PENDIENTES.1` | CL_REMUNERACIONES_PENDIENTES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"CL_T_UNPAID_SALARY"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `CL.SINGLE_TAX.1` | SINGLE_TAX | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.SINGLE_TAX","default":"0"}} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CL.SIS_EMPLOYER.1` | SIS_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→2026-03-31 | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.0154"} | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CL.SIS_EMPLOYER.2` | SIS_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-04-01→2026-07-31 | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.0162"} | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CL.SIS_EMPLOYER.3` | SIS_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-08-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.0162"} | OFFICIAL | CONFLICTING | PENDING | IMPLEMENTED |
| `CL.SUELDO_MES.1` | CL_REMUNERACION_MES_TERMINACION | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"CL.VACATION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","d… | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `CL.VACATION_ACCRUAL.1` | VACATION_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"CL_TAXABLE_BASE","rate":"0.0417"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `CL.VAL.OT_LIMIT_DAY.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Horas extraordinarias diarias por encima de 2 (Código del Trabajo art. | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `CL.VAL.WORKED_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días trabajados superan 30 (mes comercial). | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- Impuesto único de segunda categoría.
- Gratificación legal automática.
- Ingreso mínimo desde el 1-may-2026.
- Obra o faena (art. 163 inc. 3: 2,5 días por mes) y recargos de los arts. 168-169: NOT_IMPLEMENTED.
- Gratificación legal proporcional y feriado progresivo con años previos: dato de entrada.
- SIS a partir del 1-ago-2026: la Superintendencia indica que el 3,5 % de la reforma 'incluye la tasa para el financiamiento del SIS'; se mantiene el 1,62 % del SIS con interpretación CONFLICTING (posible doble conteo).
- Serie UF cubierta solo hasta el 9-oct-2026.

## BR — Brasil

- **Estado derivado del manifiesto:** `parcial` · ruta `NEW_ENGINE` · versión de reglas `BR-2026.2.0` · fecha normativa 2026-09-24 · moneda BRL
- `local_payroll_engine`: true · `consolidation_context`: false
- **Cobertura:** 34 reglas — 12 implementadas, 22 parciales, 0 NOT_IMPLEMENTED · 19 sin fuente oficial · 34 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `INSS_CEILING` | NATIONAL | 8475.55 | BRL/mês | 2026-01-01 | — | SECONDARY | Portaria Interministerial MPS/MF nº 13, de 9-jan-2026 (teto do INSS) https://documentacao.senior.com.br/exigenciaslegais/noticias/trabalhista-previdenciaria/2026/2026-01-12-trabalhista-portaria-interministerial-mps-mf-n-13-nova-tabela-de-contribuicao-do-inss-para-2026/ |
| `MIN_WAGE` | NATIONAL | 1621 | BRL/mês | 2026-01-01 | — | SECONDARY | Decreto nº 12.797/2025 (salário mínimo 2026 = R$ 1.621) https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12797.htm |
| `WORKWEEK_HOURS` | NATIONAL | 44 | horas/semana | 2026-01-01 | — | OFFICIAL | Constituição Federal art. 7º XIII: duração do trabalho normal não superior a oito horas diárias e quarenta e quatro semanais https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm |

### Bases

| Base | Descripción | Límites | Fuente |
|---|---|---|---|
| `BR_INSS_EMPLOYEE_BASE` | Salário-de-contribuição do empregado (con techo del INSS). | {"maximum":{"value":{"reference":{"code":"INSS_CEILING"}},"enforcement":"ENFORCE"}} | SECONDARY |
| `BR_PAYROLL_BASE` | Base de la contribución patronal (sin techo): salario + bonos. | — | PENDING |
| `BR_SALARY_BASE` | Salario devengado (base de las provisiones de 13º y férias). | — | PENDING |
| `BR.RESCISSION_BASE` | Remuneración base de la rescisión (salario + variables habituales) | — | OFFICIAL |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `SALARY_EARNED` | EARNING | valor_salario_devengado | BR_INSS_EMPLOYEE_BASE→INCLUDE; BR_PAYROLL_BASE→INCLUDE; BR_SALARY_BASE→INCLUDE |
| `BONUS` | EARNING | bonos_comisiones | BR_INSS_EMPLOYEE_BASE→INCLUDE; BR_PAYROLL_BASE→INCLUDE; BR_SALARY_BASE→EXCLUDE |
| `INSS_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_pension_empleado | — |
| `LOANS` | EMPLOYEE_DEDUCTION | prestamos_avances | — |
| `IRRF` | EMPLOYEE_DEDUCTION | retencion_impuesto_renta | — |
| `INSS_EMPLOYER` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `RAT` | EMPLOYER_CONTRIBUTION | aporte_riesgo_laboral_empleador | — |
| `SYSTEM_S` | EMPLOYER_CONTRIBUTION | aporte_capacitacion_empleador | — |
| `FGTS` | EMPLOYER_CONTRIBUTION | fondo_garantia_empleador | — |
| `THIRTEENTH_ACCRUAL` | ACCRUAL | prima | — |
| `VACATION_ACCRUAL` | ACCRUAL | vacaciones | — |
| `BR_T_SALARY` | INFO | — | BR.RESCISSION_BASE→INCLUDE |
| `BR_T_VARIABLE` | INFO | — | BR.RESCISSION_BASE→INCLUDE |
| `BR_T_UNPAID_SALARY` | INFO | — | — |
| `BR_T_DAYS_MONTH` | INFO | — | — |
| `BR_SALDO_SALARIO` | EARNING | — | — |
| `BR_13O_PROPORCIONAL` | EARNING | — | — |
| `BR_13O_PEDIDO_DEMISSAO` | EARNING | — | — |
| `BR_T_13_ADVANCE` | INFO | — | — |
| `BR_13O_ADELANTO_DESCUENTO` | EMPLOYEE_DEDUCTION | — | — |
| `BR_FERIAS_PROPORCIONAIS` | EARNING | — | — |
| `BR_FERIAS_VENCIDAS` | EARNING | — | — |
| `BR_FERIAS_TERCO_PROPORCIONAIS` | EARNING | — | — |
| `BR_FERIAS_TERCO_VENCIDAS` | EARNING | — | — |
| `BR_T_NOTICE_DAYS` | INFO | — | — |
| `BR_AVISO_PREVIO_INDENIZADO` | EARNING | — | — |
| `BR_AVISO_PREVIO_ACORDO` | EARNING | — | — |
| `BR_AVISO_PREVIO_DESCUENTO` | EMPLOYEE_DEDUCTION | — | — |
| `BR_FGTS_RESCISAO` | EMPLOYER_CONTRIBUTION | — | — |
| `BR_T_FGTS_BALANCE` | INFO | — | — |
| `BR_FGTS_MULTA_40` | EMPLOYER_CONTRIBUTION | — | — |
| `BR_FGTS_MULTA_20` | EMPLOYER_CONTRIBUTION | — | — |
| `BR_REMUNERACOES_PENDENTES` | EARNING | — | — |
| `BR_OVERTIME` | EARNING | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `BR.13O.1` | BR_13O_PROPORCIONAL | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"BR.RESCISSION_BASE"},"window":{"type":"CALENDAR_YEAR"},"count"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `BR.13O_ADELANTO.1` | BR_13O_ADELANTO_DESCUENTO | EMPLOYEE_DEDUCTION | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"BR_T_13_ADVANCE"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.13O_RENUNCIA.1` | BR_13O_PEDIDO_DEMISSAO | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"BR.RESCISSION_BASE"},"window":{"type":"CALENDAR_YEAR"},"count"… | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `BR.AVISO_ACUERDO.1` | BR_AVISO_PREVIO_ACORDO | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"BR.RESCISSION_BASE"},"factor":"0.5","proration":{"type":"THI… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `BR.AVISO_DESCUENTO.1` | BR_AVISO_PREVIO_DESCUENTO | EMPLOYEE_DEDUCTION | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"BR.RESCISSION_BASE"}} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `BR.AVISO_INDENIZADO.1` | BR_AVISO_PREVIO_INDENIZADO | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"BR.RESCISSION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH",… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `BR.BONUS.1` | BONUS | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.FERIAS_PROP.1` | BR_FERIAS_PROPORCIONAIS | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"base":"BR.RESCISSION_BASE"},"window":{"type":"SERVICE_YEAR"},"count":… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `BR.FERIAS_TERCO_PROPORCIONAIS.1` | BR_FERIAS_TERCO_PROPORCIONAIS | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"BR_FERIAS_PROPORCIONAIS"},"factor":"1/3"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `BR.FERIAS_TERCO_VENCIDAS.1` | BR_FERIAS_TERCO_VENCIDAS | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"BR_FERIAS_VENCIDAS"},"factor":"1/3"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `BR.FERIAS_VENCIDAS.1` | BR_FERIAS_VENCIDAS | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"BR.RESCISSION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH",… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `BR.FGTS.1` | FGTS | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BR_PAYROLL_BASE","rate":"0.08"} | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.FGTS_DEPOSITO.1` | BR_FGTS_RESCISAO | EMPLOYER_CONTRIBUTION | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"BR_SALDO_SALARIO"},"factor":"0.08"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `BR.FGTS_MULTA_20.1` | BR_FGTS_MULTA_20 | EMPLOYER_CONTRIBUTION | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"BR_T_FGTS_BALANCE"},"factor":"0.2"} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `BR.FGTS_MULTA_40.1` | BR_FGTS_MULTA_40 | EMPLOYER_CONTRIBUTION | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"BR_T_FGTS_BALANCE"},"factor":"0.4"} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `BR.IN.BR_T_13_ADVANCE.1` | BR_T_13_ADVANCE | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.thirteenth_advance_paid","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.IN.BR_T_FGTS_BALANCE.1` | BR_T_FGTS_BALANCE | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.fgts_balance","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.IN.BR_T_UNPAID_SALARY.1` | BR_T_UNPAID_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.unpaid_salary","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.IN.BR_T_VARIABLE.1` | BR_T_VARIABLE | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.variable_average","default":"0"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.IN.DAYS_MONTH.1` | BR_T_DAYS_MONTH | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"COMMERCIAL_DAYS_IN_MONTH"} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.IN.NOTICE_DAYS.1` | BR_T_NOTICE_DAYS | INFO | 2026-01-01→… | termination_date / ERROR | service_quantity {"years_basis":"COMPLETED_YEARS","linear":{"base_quantity":"30","per_completed_… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `BR.IN.SALARY.1` | BR_T_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"employment.monthly_salary"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.INSS_EMPLOYEE.1` | INSS_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / ERROR | progressive_brackets {"base":"BR_INSS_EMPLOYEE_BASE","brackets":[{"from":"0","to":"1621.00","rate":"… | SECONDARY | INTERPRETED | PENDING | PARTIAL |
| `BR.INSS_EMPLOYER.1` | INSS_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BR_PAYROLL_BASE","rate":"0.20"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `BR.IRRF.1` | IRRF | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.IRRF","default":"0"}} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `BR.LOANS.1` | LOANS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LOANS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.OVERTIME.1` | BR_OVERTIME | EARNING | 2026-01-01→… | period_end / ERROR | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | CONFLICTING | PENDING | PARTIAL |
| `BR.RAT.1` | RAT | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BR_PAYROLL_BASE","rate":"0.02"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `BR.REM_PENDENTES.1` | BR_REMUNERACOES_PENDENTES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"BR_T_UNPAID_SALARY"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.SALARY_EARNED.1` | SALARY_EARNED | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.SALDO_SALARIO.1` | BR_SALDO_SALARIO | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"BR.RESCISSION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH",… | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `BR.SYSTEM_S.1` | SYSTEM_S | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BR_PAYROLL_BASE","rate":"0.058"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `BR.THIRTEENTH_ACCRUAL.1` | THIRTEENTH_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BR_SALARY_BASE","rate":"1/12"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `BR.VACATION_ACCRUAL.1` | VACATION_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"BR_SALARY_BASE","rate":"1/9"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `BR.VAL.FGTS_BALANCE.1` | — | VALIDATION | 2026-01-01→… | termination_date / USE_ANCHOR | VALIDATION: No se informó el saldo del FGTS (amounts.fgts_balance): la multa se ca | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `BR.VAL.OT_LIMIT_DAY.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Horas extra diarias por encima de 2 (CLT art. 59). | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `BR.VAL.WORKED_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días trabajados superan 30 (mes comercial). | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- IRRF y deducciones.
- Simples Nacional / CPRB.
- 13º por avos y férias proporcionales en la liquidación.
- Aviso prévio proporcional y multa FGTS con histórico.
- Adicional noturno, horas extras.
- eSocial.
- Proyección del aviso previo indemnizado sobre 13.º y vacaciones (Súmula 371 TST): NOT_IMPLEMENTED.
- INSS e IRRF sobre las verbas rescisórias: NOT_IMPLEMENTED (sin motor tributario).
- Vacaciones en dobro (CLT art. 137) y períodos vencidos con prescripción: NOT_IMPLEMENTED.
- FGTS sobre 13.º y aviso indemnizado y depósitos del mes anterior: PENDING_VERIFICATION.
- Hora nocturna reducida (52'30"), DSR y reflejos de las horas extra: NOT_IMPLEMENTED.
- Salario mínimo (R$ 1.621) y techo del INSS con fuente secundaria: sin cambio.

## AR — Argentina

- **Estado derivado del manifiesto:** `parcial` · ruta `NEW_ENGINE` · versión de reglas `AR-2026.2.0` · fecha normativa 2026-09-24 · moneda ARS
- `local_payroll_engine`: true · `consolidation_context`: false
- **Cobertura:** 31 reglas — 11 implementadas, 20 parciales, 0 NOT_IMPLEMENTED · 16 sin fuente oficial · 31 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `SMVM` | NATIONAL | 341000 | ARS/mes | 2026-01-01 | 2026-01-31 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 346800 | ARS/mes | 2026-02-01 | 2026-02-28 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 352400 | ARS/mes | 2026-03-01 | 2026-03-31 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 357800 | ARS/mes | 2026-04-01 | 2026-04-30 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 363000 | ARS/mes | 2026-05-01 | 2026-05-31 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 367800 | ARS/mes | 2026-06-01 | 2026-06-30 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 372400 | ARS/mes | 2026-07-01 | 2026-07-31 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 376600 | ARS/mes | 2026-08-01 | 2026-08-31 | SECONDARY | Resolución 9/2025 del Consejo del Salario (valores mensuales 2026) https://estudiodelamo.com/evolucion-salario-minimo-vital-movil-argentina/ |
| `SMVM` | NATIONAL | 383800 | ARS/mes | 2026-09-01 | 2026-09-30 | OFFICIAL | Resolución 4/2026 (Boletín Oficial 2-sep-2026): SMVM mensualizados https://www.boletinoficial.gob.ar/detalleAviso/primera/346775/20260902 |
| `SMVM` | NATIONAL | 391200 | ARS/mes | 2026-10-01 | 2026-10-31 | OFFICIAL | Resolución 4/2026 (Boletín Oficial 2-sep-2026): SMVM mensualizados https://www.boletinoficial.gob.ar/detalleAviso/primera/346775/20260902 |
| `SMVM` | NATIONAL | 398800 | ARS/mes | 2026-11-01 | 2026-11-30 | OFFICIAL | Resolución 4/2026 (Boletín Oficial 2-sep-2026): SMVM mensualizados https://www.boletinoficial.gob.ar/detalleAviso/primera/346775/20260902 |
| `SMVM` | NATIONAL | 406400 | ARS/mes | 2026-12-01 | 2026-12-31 | OFFICIAL | Resolución 4/2026 (Boletín Oficial 2-sep-2026): SMVM mensualizados https://www.boletinoficial.gob.ar/detalleAviso/primera/346775/20260902 |
| `WORKWEEK_HOURS` | NATIONAL | 48 | horas/semana | 2026-01-01 | — | PENDING | Jornada semanal (Ley 11.544). Valor tomado del motor heredado / NORMATIVA_PAISES.md (Argentina), resumen interno sin cita oficial verificada en esta e  |

### Bases

| Base | Descripción | Límites | Fuente |
|---|---|---|---|
| `AR_REMUNERATION_BASE` | Remuneración base de aportes y contribuciones (simplificada, sin topes). | — | PENDING |
| `AR.VACATION_BASE` | Sueldo mensual para vacaciones (art. 155: sueldo / 25) | — | OFFICIAL |
| `AR.NOTICE_BASE` | Remuneración del preaviso (art. 232), sin el tope del art. 245 | — | OFFICIAL |
| `AR.INDEMNITY_BASE` | Base del art. 245 (mejor remuneración mensual normal y habitual) | — | OFFICIAL |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `REMUNERATION` | EARNING | valor_salario_devengado | AR_REMUNERATION_BASE→INCLUDE |
| `BONUS` | EARNING | bonos_comisiones | AR_REMUNERATION_BASE→EXCLUDE* |
| `RETIREMENT_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_pension_empleado | — |
| `PAMI_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_pension_empleado | — |
| `HEALTH_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_salud_empleado | — |
| `LOANS` | EMPLOYEE_DEDUCTION | prestamos_avances | — |
| `INCOME_TAX_4TH` | EMPLOYEE_DEDUCTION | retencion_impuesto_renta | — |
| `UNIFIED_CONTRIBUTION` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `HEALTH_EMPLOYER` | EMPLOYER_CONTRIBUTION | salud_empleador | — |
| `ART_EMPLOYER` | EMPLOYER_CONTRIBUTION | aporte_riesgo_laboral_empleador | — |
| `SAC_ACCRUAL` | ACCRUAL | prima | — |
| `VACATION_ACCRUAL` | ACCRUAL | vacaciones | — |
| `AR_T_MONTHLY_SALARY` | INFO | — | AR.VACATION_BASE→INCLUDE; AR.NOTICE_BASE→INCLUDE |
| `AR_T_BEST_REMUNERATION` | INFO | — | AR.INDEMNITY_BASE→INCLUDE |
| `AR_T_UNPAID_SALARY` | INFO | — | — |
| `AR_T_SAC_ACCRUED` | INFO | — | — |
| `AR_SAC_PROPORCIONAL` | EARNING | — | — |
| `AR_T_VACATION_ENTITLEMENT_DAYS` | INFO | — | — |
| `AR_T_VACATION_DAYS_PRORATED` | INFO | — | — |
| `AR_T_VACATION_DAYS_DUE` | INFO | — | — |
| `AR_VACACIONES_NO_GOZADAS` | EARNING | — | — |
| `AR_T_PROBATION_MONTHS` | INFO | — | — |
| `AR_INDEMNIZACION_ART_245` | EARNING | — | — |
| `AR_T_NOTICE_MONTHS` | INFO | — | — |
| `AR_PREAVISO_SUSTITUTIVO` | EARNING | — | — |
| `AR_T_MONTH_END_DAYS` | INFO | — | — |
| `AR_INTEGRACION_MES_DESPIDO` | EARNING | — | — |
| `AR_T_DAYS_MONTH` | INFO | — | — |
| `AR_SUELDO_MES_TERMINACION` | EARNING | — | — |
| `AR_REMUNERACIONES_PENDIENTES` | EARNING | — | — |
| `AR_OVERTIME` | EARNING | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `AR.ART_EMPLOYER.1` | ART_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"0.015"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `AR.BONUS.1` | BONUS | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.HEALTH_EMPLOYEE.1` | HEALTH_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"0.03"} | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.HEALTH_EMPLOYER.1` | HEALTH_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"0.06"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `AR.IN.AR_T_MONTHLY_SALARY.1` | AR_T_MONTHLY_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"employment.monthly_salary"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.IN.AR_T_PROBATION_MONTHS.1` | AR_T_PROBATION_MONTHS | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"employment.probation_months","default":"6"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.IN.AR_T_UNPAID_SALARY.1` | AR_T_UNPAID_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.unpaid_salary","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.IN.BEST_REMUNERATION.1` | AR_T_BEST_REMUNERATION | INFO | 2026-01-01→… | termination_date / ERROR | history_value {"history_input":"salary_history","method":"MAX","window_months":12,"fallback":… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.IN.DAYS_MONTH.1` | AR_T_DAYS_MONTH | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"COMMERCIAL_DAYS_IN_MONTH"} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.IN.MONTH_END_DAYS.1` | AR_T_MONTH_END_DAYS | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"DAYS_REMAINING_IN_MONTH"} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.IN.NOTICE_MONTHS.1` | AR_T_NOTICE_MONTHS | INFO | 2026-01-01→… | termination_date / ERROR | service_quantity {"years_basis":"COMPLETED_YEARS","table_decimal":[{"up_to":"5","value":"1"},{"u… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `AR.IN.SAC_ACCRUED.1` | AR_T_SAC_ACCRUED | INFO | 2026-01-01→… | termination_date / ERROR | accrued_in_window {"window":{"type":"RECURRING_PERIODS","periods":[{"start":"01-01","end":"06-30"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.IN.VAC_DUE.1` | AR_T_VACATION_DAYS_DUE | INFO | 2026-01-01→… | termination_date / ERROR | adjusted_quantity {"quantity":{"line":"AR_T_VACATION_DAYS_PRORATED"},"add":[{"input":"vacation_hi… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.IN.VAC_ENTITLEMENT.1` | AR_T_VACATION_ENTITLEMENT_DAYS | INFO | 2026-01-01→… | termination_date / ERROR | service_quantity {"years_basis":"YEARS_AT_YEAR_END","table_decimal":[{"up_to":"5","value":"14"},… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.IN.VAC_PRORATED.1` | AR_T_VACATION_DAYS_PRORATED | INFO | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"line":"AR_T_VACATION_ENTITLEMENT_DAYS"},"window":{"type":"CALENDAR_YE… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.INCOME_TAX_4TH.1` | INCOME_TAX_4TH | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.INCOME_TAX_4TH","default":"0"}} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `AR.INDEMNIZACION_245.1` | AR_INDEMNIZACION_ART_245 | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"AR.INDEMNITY_BASE"},"unit_days_per_month":"1","tiers":[{"over_… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.INTEGRACION_MES.1` | AR_INTEGRACION_MES_DESPIDO | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"AR.NOTICE_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","day… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.LOANS.1` | LOANS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LOANS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.OVERTIME.1` | AR_OVERTIME | EARNING | 2026-01-01→… | period_end / ERROR | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `AR.PAMI_EMPLOYEE.1` | PAMI_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"0.03"} | PENDING | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.PREAVISO.1` | AR_PREAVISO_SUSTITUTIVO | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"AR.NOTICE_BASE"},"factor":{"line":"AR_T_NOTICE_MONTHS"}} | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.REMUNERATION.1` | REMUNERATION | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.REM_PENDIENTES.1` | AR_REMUNERACIONES_PENDIENTES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"AR_T_UNPAID_SALARY"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.RETIREMENT_EMPLOYEE.1` | RETIREMENT_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"0.11"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `AR.SAC_ACCRUAL.1` | SAC_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"1/12"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `AR.SAC_PROPORCIONAL.1` | AR_SAC_PROPORCIONAL | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"AR_T_SAC_ACCRUED"},"factor":"1/12"} | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `AR.SUELDO_MES.1` | AR_SUELDO_MES_TERMINACION | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"AR.VACATION_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","d… | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `AR.UNIFIED_CONTRIBUTION.1` | UNIFIED_CONTRIBUTION | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"0.18"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `AR.VACACIONES_NO_GOZADAS.1` | AR_VACACIONES_NO_GOZADAS | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"AR.VACATION_BASE"},"proration":{"type":"FIXED_DIVISOR","divi… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `AR.VACATION_ACCRUAL.1` | VACATION_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"AR_REMUNERATION_BASE","rate":"14/360"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `AR.VAL.SALARY_BELOW_SMVM.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: El salario mensual es inferior al SMVM vigente del mes (posible jornad | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `AR.VAL.WORKED_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días trabajados superan 30 (mes comercial). | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- Ganancias 4ª categoría.
- Topes de base y de 3x convenio.
- Ley 27.802: solo descrita en NORMATIVA_PAISES.md (REQUIERE VALIDACIÓN PROFESIONAL).
- Convenios colectivos.
- Tope del art. 245 por convenio colectivo: requiere amounts.cct_average_salary (sin el dato no se aplica).
- Fondo de Asistencia Laboral (Ley 27.802 Título II): vigencia prorrogada al 1-nov-2026 (Decreto 408/2026): NOT_IMPLEMENTED.
- Regímenes especiales (construcción, servicio doméstico, agrario, PyME) y contratos a plazo: NOT_IMPLEMENTED.
- Requisito de mitad de días trabajados para vacaciones completas (art. 151): no verificado.
- SAC sobre preaviso e integración, y sobre vacaciones: criterio jurisprudencial NOT_IMPLEMENTED.

## EC — Ecuador

- **Estado derivado del manifiesto:** `parcial` · ruta `NEW_ENGINE` · versión de reglas `EC-2026.2.0` · fecha normativa 2026-09-24 · moneda USD
- `local_payroll_engine`: true · `consolidation_context`: false
- **Cobertura:** 29 reglas — 10 implementadas, 19 parciales, 0 NOT_IMPLEMENTED · 16 sin fuente oficial · 29 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `SBU` | NATIONAL | 482 | USD/mes | 2026-01-01 | — | OFFICIAL | Comunicado oficial: SBU 2026 = USD 482 (consenso, 15-dic-2025); Acuerdo Ministerial MDT-2025-195 según fuentes secundarias https://www.trabajo.gob.ec/despues-de-casi-una-decada-hay-consenso-gobierno-empleadores-y-trabajadores-acuerdan-fijar-el-salario-basico-unificado-de-2026-en-usd-482-no-hay-imposicion-hay-union/ |
| `WORKWEEK_HOURS` | NATIONAL | 40 | horas/semana | 2026-01-01 | — | OFFICIAL | Código del Trabajo art. 47: jornada máxima de ocho horas diarias, sin exceder de cuarenta horas semanales https://www.uafe.gob.ec/wp-content/uploads/downloads/2020/04/A2-CODIGO-DEL-TRABAJO.pdf |

### Bases

| Base | Descripción | Límites | Fuente |
|---|---|---|---|
| `EC_REMUNERATION_BASE` | Remuneración base de aportes IESS y provisiones (simplificada). | — | PENDING |
| `EC.INDEMNITY_BASE` | Remuneración del art. 95 (salario + variables habituales) | — | OFFICIAL |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `REMUNERATION` | EARNING | valor_salario_devengado | EC_REMUNERATION_BASE→INCLUDE |
| `BONUS` | EARNING | bonos_comisiones | EC_REMUNERATION_BASE→EXCLUDE* |
| `IESS_EMPLOYEE` | EMPLOYEE_DEDUCTION | aporte_pension_empleado | — |
| `LOANS` | EMPLOYEE_DEDUCTION | prestamos_avances | — |
| `INCOME_TAX` | EMPLOYEE_DEDUCTION | retencion_impuesto_renta | — |
| `IESS_EMPLOYER` | EMPLOYER_CONTRIBUTION | pension_empleador | — |
| `IECE_SECAP` | EMPLOYER_CONTRIBUTION | aporte_capacitacion_empleador | — |
| `THIRTEENTH_ACCRUAL` | ACCRUAL | prima | — |
| `FOURTEENTH_ACCRUAL` | ACCRUAL | prima | — |
| `RESERVE_FUND_ACCRUAL` | ACCRUAL | fondo_garantia_empleador | — |
| `EC_T_SALARY` | INFO | — | EC.INDEMNITY_BASE→INCLUDE |
| `EC_T_VARIABLE` | INFO | — | EC.INDEMNITY_BASE→INCLUDE |
| `EC_T_UNPAID_SALARY` | INFO | — | — |
| `EC_T_RESERVE_FUND` | INFO | — | — |
| `EC_T_YEAR_ACCRUED` | INFO | — | — |
| `EC_DECIMO_TERCERO` | EARNING | — | — |
| `EC_DECIMO_CUARTO_SIERRA` | EARNING | — | — |
| `EC_DECIMO_CUARTO_COSTA` | EARNING | — | — |
| `EC_T_VACATION_DAYS` | INFO | — | — |
| `EC_T_VACATION_DAYS_PRORATED` | INFO | — | — |
| `EC_T_VACATION_DAYS_DUE` | INFO | — | — |
| `EC_VACACIONES` | EARNING | — | — |
| `EC_INDEMNIZACION_DESPIDO_INTEMPESTIVO` | EARNING | — | — |
| `EC_BONIFICACION_DESAHUCIO` | EARNING | — | — |
| `EC_T_DAYS_MONTH` | INFO | — | — |
| `EC_REMUNERACION_MES_TERMINACION` | EARNING | — | — |
| `EC_REMUNERACIONES_PENDIENTES` | EARNING | — | — |
| `EC_FONDO_RESERVA_PENDIENTE` | EARNING | — | — |
| `EC_OVERTIME` | EARNING | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `EC.BONIFICACION_185.1` | EC_BONIFICACION_DESAHUCIO | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"EC.INDEMNITY_BASE"},"unit_days_per_month":"1","tiers":[{"over_… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `EC.BONUS.1` | BONUS | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.BONUS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.DECIMO_CUARTO_COSTA.1` | EC_DECIMO_CUARTO_COSTA | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"reference":{"code":"SBU"}},"window":{"type":"RECURRING_PERIODS","peri… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `EC.DECIMO_CUARTO_SIERRA.1` | EC_DECIMO_CUARTO_SIERRA | EARNING | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"reference":{"code":"SBU"}},"window":{"type":"RECURRING_PERIODS","peri… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `EC.DECIMO_TERCERO.1` | EC_DECIMO_TERCERO | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"line":"EC_T_YEAR_ACCRUED"},"factor":"1/12"} | OFFICIAL | CONFLICTING | PENDING | PARTIAL |
| `EC.FOURTEENTH_ACCRUAL.1` | FOURTEENTH_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / ERROR | fixed_amount_prorated {"amount":{"reference":{"code":"SBU"}},"factor":"1/12"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `EC.IECE_SECAP.1` | IECE_SECAP | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"EC_REMUNERATION_BASE","rate":"0.01"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `EC.IESS_EMPLOYEE.1` | IESS_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"EC_REMUNERATION_BASE","rate":"0.0945"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `EC.IESS_EMPLOYER.1` | IESS_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"EC_REMUNERATION_BASE","rate":"0.1115"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `EC.IN.DAYS_MONTH.1` | EC_T_DAYS_MONTH | INFO | 2026-01-01→… | termination_date / ERROR | date_measure {"measure":"COMMERCIAL_DAYS_IN_MONTH"} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.IN.EC_T_RESERVE_FUND.1` | EC_T_RESERVE_FUND | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.reserve_fund_unpaid","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.IN.EC_T_UNPAID_SALARY.1` | EC_T_UNPAID_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.unpaid_salary","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.IN.EC_T_VARIABLE.1` | EC_T_VARIABLE | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"amounts.regular_variable_average","default":"0"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.IN.SALARY.1` | EC_T_SALARY | INFO | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"input":"employment.monthly_salary"}} | OFFICIAL | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.IN.VAC_DAYS.1` | EC_T_VACATION_DAYS | INFO | 2026-01-01→… | termination_date / ERROR | service_quantity {"years_basis":"COMPLETED_YEARS","linear":{"base_quantity":"15","per_completed_… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `EC.IN.VAC_DUE.1` | EC_T_VACATION_DAYS_DUE | INFO | 2026-01-01→… | termination_date / ERROR | adjusted_quantity {"quantity":{"line":"EC_T_VACATION_DAYS_PRORATED"},"add":[{"input":"vacation_hi… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `EC.IN.VAC_PRORATED.1` | EC_T_VACATION_DAYS_PRORATED | INFO | 2026-01-01→… | termination_date / ERROR | service_period_proration {"base":{"line":"EC_T_VACATION_DAYS"},"window":{"type":"SERVICE_YEAR"},"count":… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `EC.IN.YEAR_ACCRUED.1` | EC_T_YEAR_ACCRUED | INFO | 2026-01-01→… | termination_date / ERROR | accrued_in_window {"window":{"type":"CALENDAR_YEAR"},"history_input":"salary_history","fallback_m… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `EC.INCOME_TAX.1` | INCOME_TAX | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.INCOME_TAX","default":"0"}} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `EC.INDEMNIZACION_188.1` | EC_INDEMNIZACION_DESPIDO_INTEMPESTIVO | EARNING | 2026-01-01→… | termination_date / ERROR | tiered_service_amount {"base":{"base":"EC.INDEMNITY_BASE"},"unit_days_per_month":"1","max_units":"25"… | OFFICIAL | INTERPRETED | PENDING | PARTIAL |
| `EC.LOANS.1` | LOANS | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":{"input":"amounts.LOANS","default":"0"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.OVERTIME.1` | EC_OVERTIME | EARNING | 2026-01-01→… | period_end / ERROR | hours_at_multipliers {"hourly":{"monthly_base":{"input":"employment.monthly_salary"},"hours_per_mont… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `EC.PASS.EC_FONDO_RESERVA_PENDIENTE.1` | EC_FONDO_RESERVA_PENDIENTE | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"EC_T_RESERVE_FUND"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.PASS.EC_REMUNERACIONES_PENDIENTES.1` | EC_REMUNERACIONES_PENDIENTES | EARNING | 2026-01-01→… | termination_date / ERROR | pass_through {"amount":{"line":"EC_T_UNPAID_SALARY"}} | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.REMUNERATION.1` | REMUNERATION | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | fixed_amount_prorated {"amount":{"input":"employment.monthly_salary"},"proration":{"type":"THIRTY_DAY… | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |
| `EC.RESERVE_FUND_ACCRUAL.1` | RESERVE_FUND_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"EC_REMUNERATION_BASE","rate":"0.0833"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `EC.SUELDO_MES.1` | EC_REMUNERACION_MES_TERMINACION | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"EC.INDEMNITY_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","… | NOT_APPLICABLE | UNREVIEWED | PENDING | PARTIAL |
| `EC.THIRTEENTH_ACCRUAL.1` | THIRTEENTH_ACCRUAL | ACCRUAL | 2026-01-01→… | period_end / SPLIT_BY_DAYS | rate_on_base {"base":"EC_REMUNERATION_BASE","rate":"1/12"} | PENDING | UNREVIEWED | PENDING | PARTIAL |
| `EC.VACACIONES.1` | EC_VACACIONES | EARNING | 2026-01-01→… | termination_date / ERROR | fixed_amount_prorated {"amount":{"base":"EC.INDEMNITY_BASE"},"proration":{"type":"THIRTY_DAY_MONTH","… | OFFICIAL | UNREVIEWED | PENDING | PARTIAL |
| `EC.VAL.OT_WEEK.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Horas suplementarias semanales por encima de 12 (Código del Trabajo ar | OFFICIAL | INTERPRETED | PENDING | IMPLEMENTED |
| `EC.VAL.WORKED_DAYS.1` | — | VALIDATION | 2026-01-01→… | period_end / USE_ANCHOR | VALIDATION: Los días trabajados superan 30 (mes comercial). | NOT_APPLICABLE | UNREVIEWED | PENDING | IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- Impuesto a la renta.
- Décimo tercero/cuarto por ventana y región.
- Fondo de reserva desde el segundo año.
- Mejor remuneración en indemnización.
- Jubilación patronal proporcional (20-25 años, art. 188) y participación de utilidades: NOT_IMPLEMENTED.
- Décimo tercero: período calendario vs 1-dic a 30-nov (CONFLICTING); solo si se acumula.
- Fondo de reserva: solo dato de entrada (pasa por el motor sin cálculo).
- La copia del Código del Trabajo consultada es de 2020 (reformas posteriores sin verificar).

## US — Estados Unidos

- **Estado derivado del manifiesto:** `no_implementado` · ruta `NONE` · versión de reglas `US-2026.1.0` · fecha normativa 2026-09-24 · moneda USD
- `local_payroll_engine`: false · `consolidation_context`: false
- **Cobertura:** 7 reglas — 0 implementadas, 0 parciales, 7 NOT_IMPLEMENTED · 7 sin fuente oficial · 7 sin validación profesional

### Referencias (unidades y parámetros con vigencia)

| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |
|---|---|---:|---|---|---|---|---|
| `FEDERAL_MIN_WAGE` | FEDERAL | 7.25 | USD/hora | 2009-07-24 | — | OFFICIAL | Fair Labor Standards Act (29 U.S.C. §206, §207); 29 CFR Chapter V https://www.dol.gov/agencies/whd/flsa |
| `FICA_SS_RATE` | FEDERAL | 0.062 | ratio | 2026-01-01 | — | SECONDARY | IRC §3101/§3111 (FICA) https://www.paycom.com/resources/blog/fica-tax/ |
| `MEDICARE_RATE` | FEDERAL | 0.0145 | ratio | 2026-01-01 | — | SECONDARY | IRC §3101(b)/§3111(b) (Medicare) https://www.paycom.com/resources/blog/fica-tax/ |
| `OVERTIME_MULTIPLIER` | FEDERAL | 1.5 | multiplicador | 2009-07-24 | — | OFFICIAL | Fair Labor Standards Act (29 U.S.C. §206, §207); 29 CFR Chapter V https://www.dol.gov/agencies/whd/flsa |
| `OVERTIME_THRESHOLD_HOURS` | FEDERAL | 40 | horas/semana | 2009-07-24 | — | OFFICIAL | Fair Labor Standards Act (29 U.S.C. §206, §207); 29 CFR Chapter V https://www.dol.gov/agencies/whd/flsa |
| `SS_WAGE_BASE` | FEDERAL | 184500 | USD/año | 2026-01-01 | — | SECONDARY | Social Security Administration — Contribution and Benefit Base 2026 https://www.ssa.gov/oact/cola/cbb.html |

### Conceptos y tratamiento por base

| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |
|---|---|---|---|
| `FLSA_OVERTIME` | EARNING | — | — |
| `FICA_SS_EMPLOYEE` | EMPLOYEE_DEDUCTION | — | — |
| `FICA_SS_EMPLOYER` | EMPLOYER_CONTRIBUTION | — | — |
| `MEDICARE_EMPLOYEE` | EMPLOYEE_DEDUCTION | — | — |
| `MEDICARE_EMPLOYER` | EMPLOYER_CONTRIBUTION | — | — |
| `FUTA` | EMPLOYER_CONTRIBUTION | — | — |
| `FEDERAL_WITHHOLDING` | EMPLOYEE_DEDUCTION | — | — |

\* tratamiento con `status: PENDING_VERIFICATION`.

### Reglas

| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |
|---|---|---|---|---|---|---|---|---|---|
| `US.FEDERAL_WITHHOLDING.1` | FEDERAL_WITHHOLDING | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":"0"} | PENDING | UNREVIEWED | PENDING | NOT_IMPLEMENTED |
| `US.FICA_SS_EMPLOYEE.1` | FICA_SS_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":"0"} | PENDING | UNREVIEWED | PENDING | NOT_IMPLEMENTED |
| `US.FICA_SS_EMPLOYER.1` | FICA_SS_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":"0"} | PENDING | UNREVIEWED | PENDING | NOT_IMPLEMENTED |
| `US.FLSA_OVERTIME.1` | FLSA_OVERTIME | EARNING | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":"0"} | PENDING | UNREVIEWED | PENDING | NOT_IMPLEMENTED |
| `US.FUTA.1` | FUTA | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":"0"} | PENDING | UNREVIEWED | PENDING | NOT_IMPLEMENTED |
| `US.MEDICARE_EMPLOYEE.1` | MEDICARE_EMPLOYEE | EMPLOYEE_DEDUCTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":"0"} | PENDING | UNREVIEWED | PENDING | NOT_IMPLEMENTED |
| `US.MEDICARE_EMPLOYER.1` | MEDICARE_EMPLOYER | EMPLOYER_CONTRIBUTION | 2026-01-01→… | period_end / USE_ANCHOR | pass_through {"amount":"0"} | PENDING | UNREVIEWED | PENDING | NOT_IMPLEMENTED |

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- Jurisdicciones FEDERAL / STATE / LOCAL y EXEMPT / NON_EXEMPT: estructura preparada, sin reglas estatales ni locales.
- Acumulados anuales para FICA/FUTA/SUTA.
- Retenciones federal, estatal y local.

## HK — Hong Kong

- **Estado derivado del manifiesto:** `consolidacion` · ruta `NONE` · versión de reglas `HK-2026.1.0` · fecha normativa 2026-09-24 · moneda HKD
- `local_payroll_engine`: false · `consolidation_context`: true

### Redondeo

`{"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP", "currency": {"precision": 2, "mode": "ROUND_HALF_UP"}, "tax": {"precision": 2, "mode": "ROUND_HALF_UP"}, "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"}, "display": {"precision": 2, "mode": "ROUND_HALF_UP"}, "status": "PENDING_VERIFICATION"}`

### Brechas conocidas

- Moneda base del grupo y tasas de cambio: NOT_IMPLEMENTED.
- MPF y demás reglas locales: fuera de alcance (NO se infieren).

