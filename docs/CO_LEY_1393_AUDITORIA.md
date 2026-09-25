# Auditoría de la Ley 1393 de 2010, art. 30 (Colombia) — límite del 40 % de pagos no salariales

**Estado:** `PENDING_VERIFICATION` (cálculo **PROVISIONAL**). Fuente oficial verificada, fórmula literal implementada y probada; el
alcance de «total de la remuneración» **no** está verificado. Nada de esto está validado profesionalmente.

## 1. Texto oficial verificado

Secretaría del Senado (compilación oficial), <https://www.secretariasenado.gov.co/senado/basedoc/ley_1393_2010.html>, verificado el 2026-09-24:

> «Sin perjuicio de lo previsto para otros fines, para los efectos relacionados con los artículos 18 y 204 de la Ley 100 de 1993, los pagos
> laborales no constitutivos de salario de los trabajadores particulares no podrán ser superiores al 40 % del total de la remuneración.»

La página oficial marca **«Jurisprudencia Unificación»** sobre este artículo. Ese contenido **no se leyó** en esta ejecución.

## 2. Dónde está implementado

| Qué | Dónde |
|---|---|
| Regla (datos) | `config/payroll/CO/2026/concepts.json`, concepto `BONUS_NON_SALARY`, tratamiento `SPECIAL_RULE` `SHARE_EXCESS` sobre la base `IBC` |
| Ejecución (mecanismo genérico) | `payroll_engine/bases.py::compute_base` (no conoce Colombia: recibe `share`, `non_salary_concepts`, `total_of`) |
| Estado declarado | `manifest.json` → `non_salary_share_40 = PENDING_VALIDATION`; concepto con `open_question: true`; la corrida emite `PENDING_TREATMENTS` |
| Pruebas | `tests/payroll_2026/test_co_ley_1393_y_horas.py` |

## 3. Qué hace exactamente

- **Numerador (pagos no salariales):** solo el concepto `BONUS_NON_SALARY` (entrada `bonificaciones_no_salariales`). Cualquier otro pago laboral no
  constitutivo de salario debe clasificarlo el usuario en ese campo; el motor no distingue tipos.
- **Denominador («total de la remuneración»):** `BASE_SALARY + VACATION_ENJOYED + VACATION_COMPENSATED + INCAPACITY_EMPLOYER + INCAPACITY_EPS + BONUS_SALARY +
  TRM_ADJUSTMENT + BONUS_NON_SALARY`. **No** incluye el auxilio de transporte ni prestaciones sociales pagadas en el mes.
- **Fórmula:** `exceso = max(NS − 40 % × (salario + NS), 0)`; el exceso se suma **una sola vez** al IBC (aunque haya varias líneas).
- **Base afectada:** solo `IBC` (salud, pensión y FSP), que es lo que dice el texto (arts. 18 y 204 de la Ley 100). No afecta ARL ni parafiscales.
- **Vigencia:** sin fecha de inicio propia en los datos (aplica todo 2026). Sin versiones anteriores.

## 4. Verificado vs no verificado

| Punto | Estado |
|---|---|
| El límite es 40 % del total de la remuneración y el exceso integra la base | **Verificado** con el texto oficial |
| La fórmula `NS − 40 % × (S + NS)` es la lectura literal | **Verificado** (lectura del texto) |
| Base afectada = artículos 18 y 204 (pensión y salud) | **Verificado** (referencia expresa del texto) |
| Qué conceptos integran el «total de la remuneración» (vacaciones, incapacidades, comisiones, pagos en especie, auxilio de transporte, prestaciones) | **NO verificado** (UGPP, jurisprudencia de unificación) |
| Tratamiento del salario integral (70 %) frente al 40 % | **NO verificado**: no se aplica un cálculo específico |
| Si la regla aplica a la base de la exoneración (art. 114-1 ET) | **NO verificado**: hoy no aplica |
| Excepciones (aportes voluntarios, beneficios en especie, etc.) | **NO investigadas** |

## 5. Pruebas de frontera (salario 3.000.000)

| Pagos no salariales | Total | 40 % del total | Exceso | IBC |
|---:|---:|---:|---:|---:|
| 1.999.999 | 4.999.999 | 1.999.999,6 | 0 | 3.000.000 |
| 2.000.000 (exactamente 40 %) | 5.000.000 | 2.000.000 | **0** | 3.000.000 |
| 2.000.001 (+1 peso) | 5.000.001 | 2.000.000,4 | 0,6 | 3.000.000,6 |
| 3.000.000 | 6.000.000 | 2.400.000 | 600.000 | 3.600.000 |

## 6. Decisión

No se dejó como cálculo «definitivo»: el resultado sigue siendo **provisional** y se advierte en cada corrida (`PENDING_TREATMENTS`), en el manifiesto y en la
matriz de fuentes. Antes de usarlo para pagar aportes reales, una persona con criterio profesional debe validar el alcance del «total de la remuneración»
contra las instrucciones de la UGPP y la jurisprudencia de unificación, y decidir el tratamiento del salario integral.
