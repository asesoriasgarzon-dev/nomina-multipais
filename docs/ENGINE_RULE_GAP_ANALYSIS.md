# Análisis de brechas: motor heredado vs. reglas maestras

> Parcialmente **generado** el 2026-09-25 por `tools/generate_payroll_docs.py`. Las tablas de estado salen de los datos; el resultado de las pruebas se ejecutó al generar este documento.

## 1. Resultado de la suite de pruebas al generar este documento

`============================ 954 passed in 10.96s =============================` — passed **954** · failed **0** · skipped **0** · errors **0**

## 2. Arquitectura implementada

| Capa | Módulo | Qué hace |
|---|---|---|
| 1 Normative Data | `config/payroll/<PAIS>/2026/*.json` | Reglas, referencias, conceptos, bases, redondeo y manifiesto por país y año |
| 2 Reference Resolver | `payroll_engine/references.py` | Resuelve SMMLV, UMA, SMVM… por país, jurisdicción, fecha y código; detecta faltantes y conflictos |
| 3 Rule Resolver | `payroll_engine/resolver.py` | Vigencia, ancla de fecha por regla, prioridad, cambio dentro del período (ERROR / USE_ANCHOR / SPLIT_BY_DAYS) |
| 4 Dependency Graph | `payroll_engine/graph.py` | Ciclos, dependencias faltantes, orden determinista |
| 5 Bases Engine | `payroll_engine/bases.py` | Bases nombradas por país; INCLUDE / EXCLUDE / INCLUDE_WITH_CAP / SPECIAL_RULE; registro de inclusiones y exclusiones |
| 6 Calculation Engine | `payroll_engine/mechanisms.py` | Mecanismos tipados (el JSON describe, el código ejecuta); sin lenguaje de fórmulas |
| 7 Validation Engine | `payroll_engine/schema.py`, reglas `VALIDATION` en los datos | Esquema, integridad de fuentes y validación de entradas |
| 8 Payroll Run | `payroll_engine/run.py` | Tipos de corrida, pipeline, estado COMPLETE / WITH_WARNINGS / INCOMPLETE |
| 9 Explanation Engine | `payroll_engine/explain.py` | Explicación generada de la ejecución real |
| 10 Audit Trail | `payroll_engine/audit.py` | Reglas seleccionadas/descartadas, condiciones evaluadas, operandos, bases, redondeos |
| 11 Snapshot / Versioning | `run.py`, `models.py` (`payroll_runs`, `normative_snapshots`) | Entrada + normativa + versión del motor = resultado reproducible; tablas inmutables |
| 12 Capability Manifest | `manifest.json`, `payroll_engine/capabilities.py` | Estado real que lee la UI |

## 3. Estado de los hallazgos de las auditorías anteriores

| ID | Sev. | País | Hallazgo | Estado actual |
|---|---|---|---|---|
| CO-01 | P0 | CO | Auxilio de transporte sin tope de 2 SMMLV | CORREGIDO (mensual y liquidación): regla CO.TRANSPORT_ALLOWANCE y CO_T_TRANSPORT, fuente Decreto 1470/2025; fronteras 3.501.809/810/811/7.003.620 probadas |
| CO-02 | P0 | CO | Exoneración art. 114-1 con umbral erróneo (25 SMMLV / SENA-ICBF sin umbral) | CORREGIDO: 'menos de 10 SMMLV'; conflicto con NORMATIVA_PAISES.md ('<=10') documentado; frontera 10 SMMLV -1/=/+1 probada |
| CO-03 | P1 | CO | Sin tope de 25 SMMLV en pensión empleador, ARL y FSP | CORREGIDO (IBC/RISK_BASE con tope; FSP sobre el IBC) |
| CO-04 | P1 | CO | Base distinta para vacaciones compensadas (trabajador vs empleador) | CORREGIDO: una sola base; el tratamiento queda PENDING_VERIFICATION |
| CO-05 | P1 | 7 países | Impuesto/retención manual | ABIERTO: valor digitado marcado EXTERNAL_INPUT; capacidad tax NOT_IMPLEMENTED (no se construyó un motor tributario incompleto) |
| CO-06 | P0 | CO | Ley 1393 art. 30: 'implementada con interpretación sin revisar' | AUDITADO (docs/CO_LEY_1393_AUDITORIA.md): fórmula literal verificada contra el texto oficial; alcance del 'total de la remuneración' PENDING_VERIFICATION => cálculo PROVISIONAL declarado en manifiesto, concepto y corrida; fronteras 40 % probadas |
| CO-07 | P1 | CO | Cesantías/prima de la liquidación sin auxilio de transporte | CORREGIDO en el motor normativo (la inclusión del auxilio en la base queda con fuente PENDING); el código heredado ya no se ejecuta |
| CO-12 | P3 | CO | Factores redondeados 0,0417/0,0833 | CORREGIDO: razones exactas (1/12, 15/360) |
| PE-01 | P0 | PE | CTS y gratificación truncadas con la misma fórmula | CORREGIDO: CTS por semestre mayo-octubre/noviembre-abril (dozavos y treintavos), gratificación por meses calendario completos ene-jun/jul-dic; fuentes oficiales D.S. 001-97-TR y 005-2002-TR |
| AR-01 | P0 | AR | SAC proporcional desde 1-ene en vez del semestre | CORREGIDO: 1/12 de lo devengado en la fracción del semestre (art. 123 LCT, InfoLeg); indemnización con el texto del art. 245 según Ley 27.802 |
| CL-02 | P1 | CL | SIS y reforma previsional sin vigencia | CORREGIDO con fuente oficial de la SP: SIS 1,54 % (ene-mar) y 1,62 % (desde abr); reforma 1 % hasta jul y 3,5 % desde ago (posible doble conteo del SIS desde ago: CONFLICTING) |
| CL-01 | P1 | CL | Sin tope imponible de 90 UF (serie UF) | CORREGIDO: serie diaria UF del SII como referencia con fecha; topes 89,9 → 90,0 UF (AFP/salud) y 135,1 → 135,2 UF (cesantía) por vigencia; tope de 90 UF de las indemnizaciones (art. 172 CT) |
| BR-09 | P3 | BR | Tramos INSS con huecos de R$ 0,01 | CORREGIDO: tramos contiguos |
| MX-08 / G-19 | P3 | MX | Tope SBC duplicado (constante derivada) y UMA sin vigencia | CORREGIDO: 25 × UMA por referencia con vigencia (cambia el 1-feb) |
| AR (vigencia) | P1 | AR | SMVM de un único valor anual | CORREGIDO: 12 valores mensuales con fuente |
| G-01 | P0 | Todos | Estado 'Motor activo' sin respaldo | CORREGIDO: estado derivado del Capability Manifest; ninguno es 'implementado' |
| G-03/G-04 | P1 | Todos | Sin vigencia, sin versión de reglas, sin snapshot | CORREGIDO: reglas con vigencia, Release por hash, snapshots de entrada y normativos |
| G-05 | P1 | Todos | Sin validación de entradas (negativos, días inválidos, 500) | CORREGIDO: errores tipificados (400 con mensaje) también en la liquidación |
| G-06 | P1 | 7 países | Tipo de contrato ignorado en la liquidación; mutuo acuerdo = 0 | CORREGIDO: el contrato y la causa son datos obligatorios; cada país declara en su manifiesto las causas y contratos soportados |
| G-11 | P2 | Todos | float y líneas que no suman el total | CORREGIDO (mensual y liquidación): Decimal, redondeo por línea, totales exactos |
| G-08 | P1 | Todos | Sin autenticación/CSRF | ABIERTO (fuera del alcance; documentado en README y KILLCRITIC; no se presenta como producción segura) |
| G-09 | P1 | Todos | Datos DEMO y reales comparten tablas | ABIERTO: separados solo por la bandera es_demo; sin separación física |

## 4. Capacidades por país (del manifiesto)

| País | payroll_monthly | reference_units | working_hours | overtime_and_premiums | surcharges | vacation | social_security | income_tax_withholding | benefit_accruals | termination |
|---|---|---|---|---|---|---|---|---|---|---|
| CO | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| MX | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| PE | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| CL | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| BR | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| AR | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| EC | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| US | NOT_IMPLEMENTED | PENDING_VALIDATION | — | — | — | — | — | NOT_IMPLEMENTED | — | — |
| HK | — | — | — | — | — | — | — | — | — | — |

### Componentes críticos (matriz estándar)

| País | monthly_payroll | overtime | surcharges | vacation | social_security | benefits | termination | tax | audit | historical_recalculation | ¿motor completo? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CO | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | NO |
| MX | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | NO |
| PE | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | NO |
| CL | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | NO |
| BR | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | NO |
| AR | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | NO |
| EC | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | NO |
| US | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NO |
| HK | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NO |

## 5. Brechas conocidas por país

### CO

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
- Retención en la fuente: solo procedimiento 1 mensual; sin procedimiento 2, sin retención sobre prima/cesantías/liquidación, sin redondeo al múltiplo de mil; tope de 1.340 UVT, intereses de vivienda y límites de AFC/pensión voluntaria con fuente PENDING_VERIFICATION.

### MX

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

### PE

- ONP y selector AFP/ONP.
- Renta de quinta categoría.
- Bonificación extraordinaria 9%.
- Régimen laboral (MYPE, agrario).
- Regímenes MYPE/agrario/construcción civil: NOT_IMPLEMENTED (validación bloquea la corrida).
- Indemnización de plazo fijo (art. 76 TUO 728): fuente PENDING_VERIFICATION.
- Descuento de días no laborados (1/30) en gratificación y CTS no modelado.
- Renta de quinta y retenciones sobre la liquidación: NOT_IMPLEMENTED.
- Cese antes del 15-jul/15-dic: la gratificación ordinaria del semestre anterior aún no pagada es un dato de entrada (amounts.gratification_unpaid_prior).

### CL

- Impuesto único de segunda categoría.
- Gratificación legal automática.
- Ingreso mínimo desde el 1-may-2026.
- Obra o faena (art. 163 inc. 3: 2,5 días por mes) y recargos de los arts. 168-169: NOT_IMPLEMENTED.
- Gratificación legal proporcional y feriado progresivo con años previos: dato de entrada.
- SIS a partir del 1-ago-2026: la Superintendencia indica que el 3,5 % de la reforma 'incluye la tasa para el financiamiento del SIS'; se mantiene el 1,62 % del SIS con interpretación CONFLICTING (posible doble conteo).
- Serie UF cubierta solo hasta el 9-oct-2026.

### BR

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

### AR

- Ganancias 4ª categoría.
- Topes de base y de 3x convenio.
- Ley 27.802: solo descrita en NORMATIVA_PAISES.md (REQUIERE VALIDACIÓN PROFESIONAL).
- Convenios colectivos.
- Tope del art. 245 por convenio colectivo: requiere amounts.cct_average_salary (sin el dato no se aplica).
- Fondo de Asistencia Laboral (Ley 27.802 Título II): vigencia prorrogada al 1-nov-2026 (Decreto 408/2026): NOT_IMPLEMENTED.
- Regímenes especiales (construcción, servicio doméstico, agrario, PyME) y contratos a plazo: NOT_IMPLEMENTED.
- Requisito de mitad de días trabajados para vacaciones completas (art. 151): no verificado.
- SAC sobre preaviso e integración, y sobre vacaciones: criterio jurisprudencial NOT_IMPLEMENTED.

### EC

- Impuesto a la renta.
- Décimo tercero/cuarto por ventana y región.
- Fondo de reserva desde el segundo año.
- Mejor remuneración en indemnización.
- Jubilación patronal proporcional (20-25 años, art. 188) y participación de utilidades: NOT_IMPLEMENTED.
- Décimo tercero: período calendario vs 1-dic a 30-nov (CONFLICTING); solo si se acumula.
- Fondo de reserva: solo dato de entrada (pasa por el motor sin cálculo).
- La copia del Código del Trabajo consultada es de 2020 (reformas posteriores sin verificar).

### US

- Jurisdicciones FEDERAL / STATE / LOCAL y EXEMPT / NON_EXEMPT: estructura preparada, sin reglas estatales ni locales.
- Acumulados anuales para FICA/FUTA/SUTA.
- Retenciones federal, estatal y local.

### HK

- Moneda base del grupo y tasas de cambio: NOT_IMPLEMENTED.
- MPF y demás reglas locales: fuera de alcance (NO se infieren).

## 6. Motor heredado vs. motor normativo (ejecución real al generar)

### Colombia: diferencias intencionales del cálculo mensual (Δ = normativo − heredado, COP)

El código heredado es un FIXTURE de regresión, no la fuente de verdad: la columna de causa cita la norma.

| Caso | Concepto | Heredado | Normativo | Δ | Causa |
|---|---|---:|---:|---:|---|
| 8.000.000, 28 días, 2 incap. | auxilio_transporte | 232,488.67 | 0.00 | -232,488.67 | Auxilio solo hasta 2 SMMLV (Decreto 1470/2025) |
| 8.000.000, 28 días, 2 incap. | neto_pagado | 7,281,709.89 | 7,049,221.23 | -232,488.66 | Consecuencia del auxilio |
| 20.000.000, 30 días | salud_empleador | 0.00 | 1,700,000.00 | 1,700,000.00 | Exoneración solo para menos de 10 SMMLV (art. 114-1 ET) |
| 20.000.000, 30 días | sena | 0.00 | 400,000.00 | 400,000.00 | ídem |
| 20.000.000, 30 días | icbf | 0.00 | 600,000.00 | 600,000.00 | ídem |
| 50.000.000, 30 días | pension_empleador | 6,000,000.00 | 5,252,715.00 | -747,285.00 | Tope de 25 SMMLV también para el empleador |
| 50.000.000, 30 días | aporte_fsp_empleado | 1,000,000.00 | 875,452.50 | -124,547.50 | FSP sobre el IBC con tope |
| 3.000.000, 30 días | prima | 249,900.00 | 270,757.92 | 20,857.92 | Razón exacta 1/12 y auxilio en la base |
| 3.000.000, 30 días | vacaciones | 125,100.00 | 125,000.00 | -100.00 | Razón exacta 15/360 |

### Otros países: cálculo mensual, coincidencia con el heredado (solo detecta cambios NO intencionales)

| País | Estado de la corrida | Δ máx. línea | Δ neto | Nota |
|---|---|---:|---:|---|
| MX | COMPLETE_WITH_WARNINGS | 0.0016 | -0.0016 | Sin cambio normativo; solo redondeo por línea (salarios por debajo de los topes nuevos) |
| PE | COMPLETE_WITH_WARNINGS | 0.0033 | 0.0000 | Sin cambio normativo; solo redondeo por línea (salarios por debajo de los topes nuevos) |
| CL | COMPLETE_WITH_WARNINGS | 0.0000 | 0.0000 | Sin cambio normativo; solo redondeo por línea (salarios por debajo de los topes nuevos) |
| BR | COMPLETE_WITH_WARNINGS | 0.0033 | -0.0023 | Sin cambio normativo; solo redondeo por línea (salarios por debajo de los topes nuevos) |
| AR | COMPLETE_WITH_WARNINGS | 0.0033 | 0.0000 | Sin cambio normativo; solo redondeo por línea (salarios por debajo de los topes nuevos) |
| EC | COMPLETE_WITH_WARNINGS | 0.0050 | -0.0050 | Sin cambio normativo; solo redondeo por línea (salarios por debajo de los topes nuevos) |

## 7. Hardcoding pendiente

Ver `docs/HARDCODING_INVENTORY.md` (generado del AST). El cálculo mensual, la liquidación y las horas extra de los 7 países viven en `config/payroll`; el código heredado se movió a `tests/payroll_2026/legacy_fixtures/` (no se ejecuta en la app) y `CountryConfig` ya no tiene parámetros legales. LEGAL_RULE sin justificar en producción: 0.

