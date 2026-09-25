# Perfil laboral comparado 2026 (estado de la cobertura normativa)

> **Generado** el 2026-09-25 desde `config/payroll/`. Lo que dice "SIN DATOS" o `NOT_IMPLEMENTED` **no fue investigado ni implementado**: no se infiere del código heredado ni de otro país.

Cada celda es el estado real del dato: para salarios mínimos y jornada, el peor `source.status` entre sus vigencias (OFFICIAL / SECONDARY / PENDING); para el resto, el estado de la capacidad del manifiesto (`PENDING_VALIDATION` = implementado y probado, sin validación profesional).

| País | Salario mínimo / unidad | Jornada | Horas extra | Recargos | Vacaciones | Seguridad social | Impuesto / retención | Prestaciones legales | Terminación |
|---|---|---|---|---|---|---|---|---|---|
| **CO** Colombia | OFFICIAL (1 vigencia) | OFFICIAL (2 vigencias) | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PENDING_VALIDATION | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| **MX** México | OFFICIAL (1 vigencia) | OFFICIAL (5 vigencias) | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| **PE** Perú | SECONDARY (1 vigencia) | PENDING (1 vigencia) | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| **CL** Chile | PENDING (2 vigencias) | OFFICIAL (3 vigencias) | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| **BR** Brasil | SECONDARY (1 vigencia) | OFFICIAL (1 vigencia) | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| **AR** Argentina | SECONDARY (12 vigencias) | PENDING (1 vigencia) | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| **EC** Ecuador | OFFICIAL (1 vigencia) | OFFICIAL (1 vigencia) | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | PARTIALLY_IMPLEMENTED | PARTIALLY_IMPLEMENTED |
| **US** Estados Unidos | OFFICIAL (1 vigencia) | OFFICIAL (1 vigencia) | NOT_IMPLEMENTED | SIN DATOS | SIN DATOS | NOT_IMPLEMENTED | NOT_IMPLEMENTED | SIN DATOS | NOT_IMPLEMENTED |
| **HK** Hong Kong | SIN DATOS | SIN DATOS | SIN DATOS | SIN DATOS | SIN DATOS | SIN DATOS | SIN DATOS | SIN DATOS | SIN DATOS |

## Referencias con cambios de vigencia durante 2026

| País | Código | Versiones | Detalle |
|---|---|---:|---|
| CO | `SUNDAY_HOLIDAY_SURCHARGE` | 3 | 2025-07-01→2026-06-30: 0.80; 2026-07-01→2027-06-30: 0.90; 2027-07-01→…: 1.00 |
| CO | `WORKWEEK_HOURS` | 2 | 2025-07-15→2026-07-14: 44; 2026-07-15→…: 42 |
| MX | `UMA_DAILY` | 2 | 2025-02-01→2026-01-31: 113.14; 2026-02-01→…: 117.31 |
| MX | `WORKWEEK_HOURS` | 5 | 2026-01-01→2026-12-31: 48; 2027-01-01→2027-12-31: 46; 2028-01-01→2028-12-31: 44; 2029-01-01→2029-12-31: 42; 2030-01-01→…: 40 |
| CL | `MIN_INCOME` | 2 | 2026-01-01→2026-04-30: 539000; 2026-05-01→…: 553553 |
| CL | `TAX_CAP_UF_PENSION` | 2 | 2026-01-01→2026-01-31: 89.9; 2026-02-01→…: 90.0 |
| CL | `TAX_CAP_UF_UNEMPLOYMENT` | 2 | 2026-01-01→2026-01-31: 135.1; 2026-02-01→…: 135.2 |
| CL | `WORKWEEK_HOURS` | 3 | 2024-04-26→2026-04-25: 44; 2026-04-26→2028-04-25: 42; 2028-04-26→…: 40 |
| AR | `SMVM` | 12 | 2026-01-01→2026-01-31: 341000; 2026-02-01→2026-02-28: 346800; 2026-03-01→2026-03-31: 352400; 2026-04-01→2026-04-30: 357800; 2026-05-01→2026-05-31: 363000; 2026-06-01→2026-06-30: 367800; 2026-07-01→2026-07-31: 372400; 2026-08-01→2026-08-31: 376600; 2026-09-01→2026-09-30: 383800; 2026-10-01→2026-10-31: 391200; 2026-11-01→2026-11-30: 398800; 2026-12-01→2026-12-31: 406400 |

## Por país

### CO — Colombia

- **Estado:** `parcial` (ruta `NEW_ENGINE`)
- `payroll_monthly`: **PARTIALLY_IMPLEMENTED** — Nómina mensual normativa con retención manual y sin horas extra/recargos.
- `reference_units`: **PENDING_VALIDATION** — SMMLV y auxilio con fuente oficial; SMMLV sujeto a proceso judicial (Consejo de Estado).
- `transport_allowance`: **PENDING_VALIDATION** — Límite de 2 SMMLV implementado y probado en frontera.
- `social_security`: **PENDING_VALIDATION** — IBC con tope de 25 SMMLV, FSP, salud y pensión; tasas con fuente secundaria.
- `parafiscales_exoneration`: **PENDING_VALIDATION** — Exoneración art. 114-1 ET (menos de 10 SMMLV).
- `integral_salary`: **PENDING_VALIDATION** — Mínimo 13 SMMLV e IBC al 70%; variables e integración con no salariales pendientes.
- `working_hours`: **PENDING_VALIDATION** — Jornada por vigencia: 44 h hasta 14-jul-2026; 42 h desde 15-jul-2026.
- `benefit_accruals`: **PARTIALLY_IMPLEMENTED** — Provisiones mensuales; sin calendario de pago ni consignación.
- `non_salary_share_40`: **PENDING_VALIDATION** — Ley 1393 art. 30: fórmula literal (exceso sobre el 40 % del total de la remuneración integra el IBC) ejecutada como CÁLCULO PROVISIONAL; alcance del 'total de la remuneración' según UGPP/jurisprudencia de unificación y salario integral NO verificados.
- `income_tax_withholding`: **PARTIALLY_IMPLEMENTED** — Retención de nómina mensual (procedimiento 1, art. 383 ET) con UVT 2026 oficial, deducciones del art. 387, tope 40 % y renta exenta del 25 % (790 UVT), como modo CALCULATED opt-in. Modo MANUAL (por defecto en la API) sigue digitado. Sin validación profesional.
- `overtime_and_premiums`: **PARTIALLY_IMPLEMENTED** — Recargos nocturno/extra/dominical (Ley 2466: 80 % → 90 % el 1-jul-2026 → 100 % el 1-jul-2027) desde datos; acumulación de recargos y clasificación de horas: interpretación sin validar.
- `termination`: **PARTIALLY_IMPLEMENTED** — Cesantías, intereses, prima, vacaciones e indemnización del art. 64 (indefinido <10/>=10 SMMLV, término fijo, obra o labor) ejecutan desde datos con fuentes oficiales del CST; intereses de cesantías y auxilio en las bases con fuente PENDING; sin validación profesional; sin indemnización moratoria (art. 65).
- `vacation`: **PARTIALLY_IMPLEMENTED** — Compensación de vacaciones proporcionales y pendientes al retiro; goce/programación no modelados.
- `surcharges`: **PARTIALLY_IMPLEMENTED** — Recargo nocturno 35 % y dominical/festivo 80 % → 90 % (1-jul-2026) → 100 % (1-jul-2027) desde datos (Ley 2466/2025); acumulación con horas extra: interpretación sin validar.

### MX — México

- **Estado:** `parcial` (ruta `NEW_ENGINE`)
- `payroll_monthly`: **PARTIALLY_IMPLEMENTED** — Nómina mensual normativa equivalente al motor heredado; ISR manual; SBC sin integrar.
- `reference_units`: **PENDING_VALIDATION** — SM general y ZLFN con fuente oficial (CONASAMI); UMA con fuente secundaria y cambio el 1-feb.
- `working_hours`: **PARTIALLY_IMPLEMENTED** — Reducción gradual 48 → 40 h (2026-2030) declarada como referencia con vigencia.
- `overtime_and_premiums`: **PARTIALLY_IMPLEMENTED** — Horas extra dobles/triples con versiones por vigencia (reforma DOF 1-may-2026, extraída por lectura automática) y prima dominical; descanso obligatorio NOT_IMPLEMENTED.
- `vacation`: **PARTIALLY_IMPLEMENTED** — Tabla del art. 76 (reforma 2023) y pago proporcional al término; goce no modelado.
- `social_security`: **PARTIALLY_IMPLEMENTED** — IMSS: SBC simplificado (sin integración), cesantía y vejez a tasa plana.
- `income_tax_withholding`: **NOT_IMPLEMENTED** — El impuesto es un valor digitado (EXTERNAL_INPUT); no existe motor tributario.
- `benefit_accruals`: **PARTIALLY_IMPLEMENTED** — Solo provisión de aguinaldo.
- `termination`: **PARTIALLY_IMPLEMENTED** — Aguinaldo proporcional, vacaciones y prima vacacional, indemnización de 3 meses y de 20 días por año (plazo indeterminado/determinado) y prima de antigüedad con tope de 2 salarios mínimos por zona desde datos con fuente oficial (Orden Jurídico Nacional). Fracciones de año, salario integrado, salarios vencidos y PTU: interpretación sin validar o NOT_IMPLEMENTED.
- `surcharges`: **PARTIALLY_IMPLEMENTED** — Prima dominical del 25 % (art. 71); descanso obligatorio y séptimo día trabajado (arts. 73 y 75): NOT_IMPLEMENTED.

### PE — Perú

- **Estado:** `parcial` (ruta `NEW_ENGINE`)
- `payroll_monthly`: **PARTIALLY_IMPLEMENTED** — Nómina mensual normativa equivalente al motor heredado; solo AFP; renta manual.
- `reference_units`: **PENDING_VALIDATION** — RMV con fuente secundaria.
- `working_hours`: **NOT_IMPLEMENTED** — Jornada sin verificar.
- `overtime_and_premiums`: **PARTIALLY_IMPLEMENTED** — Sobretasas 25 %/35 % (D.S. 007-2002-TR art. 10); divisor del valor hora sin verificar.
- `vacation`: **PARTIALLY_IMPLEMENTED** — Vacaciones truncas y adquiridas al cese; goce/programación no modelados.
- `social_security`: **PARTIALLY_IMPLEMENTED** — AFP y EsSalud sobre remuneración (sin bonos ni tope); ONP NOT_IMPLEMENTED.
- `income_tax_withholding`: **NOT_IMPLEMENTED** — El impuesto es un valor digitado (EXTERNAL_INPUT); no existe motor tributario.
- `benefit_accruals`: **PARTIALLY_IMPLEMENTED** — Provisión mensual simple; liquidación de CTS/gratificación por semestre en corrida TERMINATION.
- `termination`: **PARTIALLY_IMPLEMENTED** — CTS trunca, gratificación trunca, vacaciones truncas e indemnización por despido arbitrario ejecutan desde datos (semestres jurídicos distintos por beneficio). Régimen general únicamente; indemnización de plazo fijo con fuente pendiente; sin validación profesional.
- `surcharges`: **NOT_IMPLEMENTED** — Sobretasa nocturna (D.S. 007-2002-TR) y trabajo en feriado no investigados.

### CL — Chile

- **Estado:** `parcial` (ruta `NEW_ENGINE`)
- `payroll_monthly`: **PARTIALLY_IMPLEMENTED** — Nómina mensual normativa con tope imponible en UF; impuesto manual; tasas AFC/mutual con fuente pendiente.
- `reference_units`: **PENDING_VALIDATION** — UF diaria (SII, oficial) y topes imponibles (SP); ingreso mínimo de mayo-2026 sin norma oficial verificada.
- `working_hours`: **PENDING_VALIDATION** — Jornada por vigencia (Ley 21.561): 44 h, 42 h desde 26-abr-2026, 40 h desde 2028.
- `overtime_and_premiums`: **PARTIALLY_IMPLEMENTED** — Horas extraordinarias al 50 % con el divisor de la Dirección del Trabajo y la jornada por vigencia.
- `vacation`: **PARTIALLY_IMPLEMENTED** — 15 días hábiles + progresivo (art. 68) y compensación proporcional al término.
- `social_security`: **PARTIALLY_IMPLEMENTED** — AFP, salud, SIS, reforma y mutual con topes de 89,9→90,0 UF y 135,1→135,2 UF (cesantía) por vigencia; tasas de AFC/mutual/comisión AFP aún con fuente pendiente.
- `income_tax_withholding`: **NOT_IMPLEMENTED** — El impuesto es un valor digitado (EXTERNAL_INPUT); no existe motor tributario.
- `benefit_accruals`: **PARTIALLY_IMPLEMENTED** — Solo provisión de vacaciones.
- `termination`: **PARTIALLY_IMPLEMENTED** — Indemnización por años de servicio (art. 163, tope 330 días), aviso previo sustitutivo (art. 161) y feriado proporcional (art. 73) con la base topada a 90 UF del último día del mes anterior al pago (art. 172, serie UF del SII). Conversión de días hábiles a corridos, recargos de los arts. 168-169 y obra o faena: sin validar / no implementados.
- `surcharges`: **NOT_IMPLEMENTED** — Recargos por domingo/festivo y nocturno no investigados.

### BR — Brasil

- **Estado:** `parcial` (ruta `NEW_ENGINE`)
- `payroll_monthly`: **PARTIALLY_IMPLEMENTED** — Nómina mensual normativa equivalente al motor heredado; régimen general; IRRF manual.
- `reference_units`: **PENDING_VALIDATION** — Salario mínimo y techo del INSS con fuente secundaria.
- `working_hours`: **PENDING_VALIDATION** — Jornada de 44 h semanales (CF art. 7º XIII) verificada; cambios futuros no cargados.
- `overtime_and_premiums`: **PARTIALLY_IMPLEMENTED** — 50 % (CF/CLT), adicional nocturno 20 %; divisor 220 vs 240 en conflicto (CONFLICTING).
- `vacation`: **PARTIALLY_IMPLEMENTED** — Vacaciones proporcionales y vencidas con 1/3 al término; goce no modelado.
- `social_security`: **PARTIALLY_IMPLEMENTED** — INSS progresivo con techo; patronal solo régimen general.
- `income_tax_withholding`: **NOT_IMPLEMENTED** — El impuesto es un valor digitado (EXTERNAL_INPUT); no existe motor tributario.
- `benefit_accruals`: **PARTIALLY_IMPLEMENTED** — 13º y férias + 1/3 como provisión.
- `termination`: **PARTIALLY_IMPLEMENTED** — Saldo de salario, 13.º proporcional (mes con 15+ días), vacaciones proporcionales y vencidas + 1/3, aviso previo (30 + 3 por año, máx. 90) indemnizado o por mitad en acuerdo (art. 484-A), depósito FGTS y multa 40 %/20 % desde datos con fuentes oficiales del Planalto. Sin proyección del aviso, sin INSS/IRRF sobre la rescisión, sin vacaciones en dobro (art. 137).
- `surcharges`: **PARTIALLY_IMPLEMENTED** — Adicional noturno 20 % (CLT art. 73) y feriado trabajado en dobro; hora reducida y DSR: NOT_IMPLEMENTED.

### AR — Argentina

- **Estado:** `parcial` (ruta `NEW_ENGINE`)
- `payroll_monthly`: **PARTIALLY_IMPLEMENTED** — Nómina mensual normativa equivalente al motor heredado; sin topes; Ganancias manual.
- `reference_units`: **PENDING_VALIDATION** — SMVM mensual completo (ene-dic 2026): sep-dic con fuente oficial (BO), ene-ago secundaria.
- `working_hours`: **NOT_IMPLEMENTED** — Jornada sin verificar.
- `overtime_and_premiums`: **PARTIALLY_IMPLEMENTED** — Recargos 50 %/100 % (art. 201); divisor del valor hora sin verificar.
- `vacation`: **PARTIALLY_IMPLEMENTED** — Escala 14/21/28/35 y pago proporcional al egreso; requisito de mitad de días del año no verificado.
- `social_security`: **PARTIALLY_IMPLEMENTED** — Aportes y contribuciones sin base máxima; contribución unificada 18%.
- `income_tax_withholding`: **NOT_IMPLEMENTED** — El impuesto es un valor digitado (EXTERNAL_INPUT); no existe motor tributario.
- `benefit_accruals`: **PARTIALLY_IMPLEMENTED** — Provisión mensual simple; SAC por semestre en corrida TERMINATION.
- `termination`: **PARTIALLY_IMPLEMENTED** — SAC proporcional por semestre jurídico (art. 123), vacaciones (arts. 150-156), indemnización art. 245 (texto Ley 27.802), preaviso e integración del mes de despido desde datos con fuente oficial (InfoLeg). Tope de convenio, SAC sobre preaviso/vacaciones, FAL (vigente desde 1-nov-2026 por Decreto 408/2026) y regímenes especiales: no implementados.
- `surcharges`: **NOT_IMPLEMENTED** — Recargos de jornada nocturna y feriados no investigados (solo horas suplementarias del art. 201).

### EC — Ecuador

- **Estado:** `parcial` (ruta `NEW_ENGINE`)
- `payroll_monthly`: **PARTIALLY_IMPLEMENTED** — Nómina mensual normativa equivalente al motor heredado; renta manual.
- `reference_units`: **PENDING_VALIDATION** — SBU 2026 con comunicado oficial del Ministerio del Trabajo.
- `working_hours`: **PENDING_VALIDATION** — Jornada de 40 h (art. 47) con copia del Código de 2020.
- `overtime_and_premiums`: **PARTIALLY_IMPLEMENTED** — Recargos de los arts. 49 y 55; divisor 240 sin verificar.
- `vacation`: **PARTIALLY_IMPLEMENTED** — 15 días + 1 por año excedente de cinco (máx. 30) y pago proporcional.
- `social_security`: **PARTIALLY_IMPLEMENTED** — IESS sobre remuneración (sin bonos).
- `income_tax_withholding`: **NOT_IMPLEMENTED** — El impuesto es un valor digitado (EXTERNAL_INPUT); no existe motor tributario.
- `benefit_accruals`: **PARTIALLY_IMPLEMENTED** — Décimos y fondo de reserva como provisión sin ventanas ni región.
- `termination`: **PARTIALLY_IMPLEMENTED** — Despido intempestivo (art. 188: 3 meses hasta 3 años; 1 mes por año, fracción = año, máx. 25), bonificación por desahucio (art. 185), vacaciones (art. 69), décimo tercero y cuarto acumulados desde datos con el Código del Trabajo (copia de 2020). Jubilación patronal, utilidades y fondo de reserva: NOT_IMPLEMENTED/dato de entrada; décimo tercero con interpretación CONFLICTING (período).
- `surcharges`: **PARTIALLY_IMPLEMENTED** — Recargo nocturno 25 % (art. 49) y trabajo en sábado/domingo 100 % (art. 55 num. 4).

### US — Estados Unidos

- **Estado:** `no_implementado` (ruta `NONE`)
- `payroll_monthly`: **NOT_IMPLEMENTED** — Sin motor: EE. UU. no se trata como un país único.
- `reference_units`: **PENDING_VALIDATION** — Salario mínimo federal y horas extra FLSA con fuente oficial (DOL); base salarial máxima con fuente secundaria.
- `federal`: **NOT_IMPLEMENTED** — Reglas federales cargadas como datos (NOT_IMPLEMENTED).
- `state`: **NOT_IMPLEMENTED** — Salario mínimo, retención y SUTA estatales sin datos.
- `local`: **NOT_IMPLEMENTED** — Salarios mínimos e impuestos locales sin datos.
- `overtime_flsa`: **NOT_IMPLEMENTED** — Umbral y multiplicador con fuente oficial; sin cálculo (empleados exentos/no exentos).
- `payroll_taxes`: **NOT_IMPLEMENTED** — FICA, Medicare y FUTA sin cálculo (requieren acumulados anuales).
- `income_tax_withholding`: **NOT_IMPLEMENTED** — Retención federal, estatal y local sin motor.
- `paid_leave_and_termination`: **NOT_IMPLEMENTED** — Depende del estado; sin investigación normativa.

### HK — Hong Kong

- **Estado:** `consolidacion` (ruta `NONE`)
- `local_payroll`: **NOT_APPLICABLE** — Hong Kong es contexto de consolidación; no tiene motor de nómina local. Habilitarlo exige investigación normativa independiente.
- `consolidation`: **PARTIALLY_IMPLEMENTED** — Panel consolidado por país sin conversión de moneda ni totales del grupo.
- `fx_conversion`: **NOT_IMPLEMENTED** — Sin tasas de cambio ni moneda base del grupo definida.

