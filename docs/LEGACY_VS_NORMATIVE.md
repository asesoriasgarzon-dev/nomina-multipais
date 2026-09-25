# Liquidación: resultado heredado vs normativo vs esperado por la norma

> **Generado** el 2026-09-25 ejecutando ambos motores (el heredado es un fixture en `tests/payroll_2026/legacy_fixtures/`).

Regla: **`legacy == normative` NO es prueba de corrección jurídica.** Cada fila separa `LEGACY_RESULT` (lo que calculaba el código heredado), `NORMATIVE_RESULT` (motor normativo) y `EXPECTED_LEGAL_RESULT` (calculado de forma independiente desde el texto de la norma en las pruebas). Donde no hay fuente suficientemente sólida para el resultado esperado, el estado es `PENDING_VERIFICATION`, no `IMPLEMENTED`.

## Totales del mismo caso en ambos motores

| País | Caso | Heredado: prestaciones | Heredado: indemnización | Heredado: total | Normativo: prestaciones | Normativo: indemnización | Normativo: total | Δ total |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PE | sueldo 3000, ingreso 2024-03-10, retiro 2026-07-20, sin justa causa | 3,350.00 | 10,639.73 | 13,989.73 | 1,758.34 | 10,637.50 | 12,395.84 | -1,593.89 |
| AR | sueldo 1000000, ingreso 2020-01-10, retiro 2026-09-15, sin justa causa | 716,666.67 | 9,000,000.00 | 9,716,666.67 | 802,086.75 | 9,500,000.00 | 10,302,086.75 | 585,420.08 |
| CO | sueldo 2000000, ingreso 2023-02-10, retiro 2026-09-15, sin justa causa | 1,953,750.00 | 5,466,666.67 | 7,420,416.67 | 2,797,084.68 | 5,466,666.67 | 8,263,751.35 | 843,334.68 |
| CL | sueldo 2000000, ingreso 2015-03-10, retiro 2026-09-15, sin justa causa | 0.00 | 24,000,000.00 | 24,000,000.00 | 728,767.12 | 24,000,000.00 | 24,728,767.12 | 728,767.12 |
| MX | sueldo 30000, ingreso 2019-03-10, retiro 2026-09-15, sin justa causa | 10,602.74 | 298,214.89 | 308,817.63 | 24,917.80 | 310,666.08 | 335,583.88 | 26,766.25 |
| BR | sueldo 5000, ingreso 2021-03-17, retiro 2026-09-20, sin justa causa | 3,652.78 | 18,500.24 | 22,153.02 | 7,083.33 | 7,500.00 | 14,583.33 | -7,569.69 |
| EC | sueldo 1000, ingreso 2021-03-17, retiro 2026-09-15, sin justa causa | 1,062.10 | 6,754.11 | 7,816.21 | 250.68 | 7,375.00 | 7,625.68 | -190.53 |

Nota: el formulario heredado no informaba el salario del mes de terminación ni calculaba vacaciones proporcionales; el motor normativo agrega los conceptos que la norma exige (por eso el total normativo suele ser mayor). Los países sin validación profesional siguen sujetos a revisión.

## Diferencias con resultado esperado independiente

| Concepto | LEGACY_RESULT | NORMATIVE_RESULT | EXPECTED_LEGAL_RESULT | Diferencia (norm − legacy) | Razón jurídica | Fuente |
|---|---:|---:|---:|---:|---|---|
| PE CTS trunca | 1,675.00 | 666.67 | 666.67 | -1,008.33 | El heredado usaba la misma fórmula (año calendario/360) para ambas; la CTS es por semestre mayo-octubre / noviembre-abril (dozavos y treintavos) y la gratificación por meses calendario completos de enero-junio / julio-diciembre. | TUO CTS D.S. 001-97-TR arts. 2 y 21; D.S. 005-2002-TR art. 5 |
| PE gratificación trunca | 1,675.00 | 0.00 | 0.00 | -1,675.00 | El heredado usaba la misma fórmula (año calendario/360) para ambas; la CTS es por semestre mayo-octubre / noviembre-abril (dozavos y treintavos) y la gratificación por meses calendario completos de enero-junio / julio-diciembre. | TUO CTS D.S. 001-97-TR arts. 2 y 21; D.S. 005-2002-TR art. 5 |
| AR SAC proporcional | 716,666.67 | 208,333.33 | 208,333.33 | -508,333.34 | El heredado contaba el SAC desde el 1-ene (año calendario) aunque el cese fuera en el 2.º semestre; el SAC se calcula por la fracción del semestre en curso (1/12 de lo devengado). | LCT arts. 122-123 (InfoLeg) |
| CO cesantías | 1,416,666.67 | 1,593,108.96 | 1,593,108.96 | 176,442.29 | El heredado excluía el auxilio de transporte de la base de cesantías y prima; el normativo lo incluye (fuente de la inclusión PENDING_VERIFICATION) y liquida días base 360 desde el 1-ene / 1-jul. | CST arts. 249, 253, 306; Ley 52/1975 (pendiente) |
| CO prima | 416,666.67 | 468,561.46 | 468,561.46 | 51,894.79 | El heredado excluía el auxilio de transporte de la base de cesantías y prima; el normativo lo incluye (fuente de la inclusión PENDING_VERIFICATION) y liquida días base 360 desde el 1-ene / 1-jul. | CST arts. 249, 253, 306; Ley 52/1975 (pendiente) |

## Razón de las diferencias por país

| País | Concepto | Razón jurídica | Fuente |
|---|---|---|---|
| PE | CTS y gratificación | El heredado usaba la misma fórmula (año calendario/360) para ambas; la CTS es por semestre mayo-octubre / noviembre-abril (dozavos y treintavos) y la gratificación por meses calendario completos de enero-junio / julio-diciembre. | TUO CTS D.S. 001-97-TR arts. 2 y 21; D.S. 005-2002-TR art. 5 |
| AR | SAC proporcional | El heredado contaba el SAC desde el 1-ene (año calendario) aunque el cese fuera en el 2.º semestre; el SAC se calcula por la fracción del semestre en curso (1/12 de lo devengado). | LCT arts. 122-123 (InfoLeg) |
| CO | Cesantías, intereses y prima | El heredado excluía el auxilio de transporte de la base de cesantías y prima; el normativo lo incluye (fuente de la inclusión PENDING_VERIFICATION) y liquida días base 360 desde el 1-ene / 1-jul. | CST arts. 249, 253, 306; Ley 52/1975 (pendiente) |
| CL | Feriado proporcional, aviso previo y topes | El heredado no calculaba el feriado proporcional y sumaba el aviso previo siempre; el normativo aplica el tope de 330 días y de 90 UF y paga el aviso solo si no se dio. | Código del Trabajo arts. 161, 163, 172, 73 |
| MX | Aguinaldo, vacaciones, prima vacacional, prima de antigüedad | El heredado solo daba aguinaldo (como 'prima'); el normativo agrega vacaciones, prima vacacional, indemnización de 3 meses + 20 días y prima de antigüedad con tope de 2 salarios mínimos. | LFT arts. 48, 50, 76, 80, 87, 162 |
| BR | 13.º, vacaciones + 1/3, aviso, FGTS | El heredado no calculaba vacaciones ni FGTS con el criterio de la CLT; el normativo aplica meses con 15+ días, fracción >14 días, aviso 30+3/año y multa del 40 %. | Lei 4.090/62, CLT arts. 146-147, Lei 12.506/2011, Lei 8.036/90 art. 18 |
| EC | Décimos, vacaciones, desahucio | El heredado no distinguía décimo tercero/cuarto acumulados ni la bonificación del art. 185. | Código del Trabajo arts. 111, 113, 185, 188 |
