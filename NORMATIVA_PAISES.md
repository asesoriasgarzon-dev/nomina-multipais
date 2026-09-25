# Normativa laboral y de seguridad social — referencia por país (2026)

> **AVISO (2026-09-25): este documento es un resumen histórico y NO es la fuente normativa del sistema.** Las reglas que ejecuta la aplicación viven,
> con vigencia, fuente y estado de verificación, en `config/payroll/<PAIS>/2026/` (ver `docs/MASTER_PAYROLL_RULES_2026.md` y `docs/SOURCES_REGISTRY_2026.md`).
> Discrepancias ya detectadas y resueltas a favor del texto oficial: Colombia exoneración art. 114-1 ET «menos de diez (10) SMMLV» (aquí dice «≤10»),
> auxilio de transporte hasta 2 SMMLV, Perú CTS/gratificación por semestre, Argentina SAC por semestre y art. 245 (Ley 27.802, B.O. 6-mar-2026, vigente
> desde su publicación; aquí se indica «vigente desde 1-jun-2026», que corresponde solo al Fondo de Asistencia Laboral, prorrogado al 1-nov-2026 por el
> Decreto 408/2026). Ante cualquier diferencia, prevalece `config/payroll`.

Este documento es la base legal para programar cada `countries/<pais>.py` del
proyecto. Compilado el 2026-09-23 mediante investigación con fuentes oficiales
(ministerios de trabajo, institutos de seguridad social, boletines/diarios
oficiales). **No reemplaza asesoría legal/contable local** — las cifras
(salario mínimo, topes, tablas de retención) cambian por decreto con
frecuencia intra-anual en varios de estos países; antes de facturarle a Hong
Kong GSR Technology Limited un cálculo real, cada país debe validarse contra
la fuente vigente al momento del período de nómina, igual que ya se hace con
el SMMLV/UVT de Colombia en este mismo proyecto.

Los puntos marcados 🔴 o "no verificado en fuente primaria" son datos que la
investigación dejó explícitamente sin confirmar — no están inventados, pero
tampoco deben codificarse como constante sin una segunda revisión.

---

## Índice
1. [Colombia](#colombia-recordatorio---ya-implementado) (recordatorio, ya implementado)
2. [México](#méxico)
3. [Perú](#perú)
4. [Chile](#chile)
5. [Brasil](#brasil)
6. [Argentina](#argentina)
7. [Ecuador](#ecuador)
8. [Tabla comparativa resumen](#tabla-comparativa-resumen)
9. [Vacíos pendientes de verificar antes de producción](#vacíos-pendientes-de-verificar-antes-de-producción)

---

## Colombia (recordatorio — ya implementado)

Ver `countries/colombia.py`. Jornada 42h (desde 15-jul-2026), SMMLV 2026
$1.750.905, auxilio de transporte $249.095, vacaciones 15 días hábiles/año,
prima de servicios 30 días/año en dos semestres. Aportes: salud 4%/4%
(tope 25 SMMLV), pensión 4%/12%, FSP escalonado 1%-2% (empleado, salarios
≥4 SMMLV), ARL solo empleador (0,522% clase I), caja de compensación 4%
empleador, exoneración de salud/SENA/ICBF para salarios ≤10 SMMLV (Ley 1607).
Provisiones: cesantías 8,33%, intereses cesantías 1%, prima 8,33%,
vacaciones 4,17%. Indemnización por despido sin justa causa: fórmula por
tipo de contrato y antigüedad (Código Sustantivo del Trabajo, art. 64).

---

## México

**Jornada:** diurna 8h/nocturna 7h/mixta 7,5h. 🔴 Reforma DOF 3-mar-2026:
reducción gradual 48h (2026) → 46h (2027) → 44h (2028) → 42h (2029) → 40h
(2030), sin reducir salario. Horas extra: primeras 9h/semana al 200%,
excedente al 300%.

**Contratos:** indeterminado (regla general), por obra/tiempo determinado
(solo si la naturaleza del trabajo lo exige), por temporada.

**Salario mínimo 2026:** general **$315,04 MXN/día** (~$9.582/mes); Zona
Libre Frontera Norte **$440,87/día**. UMA 2026: diaria $117,31, mensual
$3.566,22 (referencia para topes IMSS/ISR, no es el salario mínimo).

**Vacaciones:** 12 días el primer año (Ley "Vacaciones Dignas"), +2 por año
hasta 20, luego +2 cada 5 años. Pago: salario + prima vacacional mínima 25%.

**Aguinaldo:** mínimo 15 días de salario, una vez al año, antes del 20 de
diciembre. Irrenunciable.

**Seguridad social (IMSS + INFONAVIT)** — base: Salario Base de Cotización
(SBC), tope 25 UMA/día ($2.932,75 MXN):

| Concepto | % Empleador | % Empleado |
|---|---|---|
| Enfermedad/Maternidad (cuota fija, 1 UMA) | 20,40% | 0% |
| Enfermedad/Maternidad (excedente >3 UMA) | 1,10% | 0,40% |
| Enfermedad/Maternidad (prestaciones en dinero) | 0,70% | 0,25% |
| Enfermedad/Maternidad (gastos médicos pensionados) | 1,05% | 0,375% |
| Riesgos de Trabajo | variable por prima de riesgo propia (mín. ~0,50%) | 0% |
| Invalidez y Vida | 1,75% | 0,625% |
| Guarderías y Prestaciones Sociales | 1,00% | 0% |
| Retiro | 2,00% | 0% |
| Cesantía y Vejez (CEAV) | progresivo 3,150%–7,513% según rango salarial (en transición a 11,875% para 2030) | 1,125% |
| INFONAVIT (vivienda) | 5,00% | 0% |

🔴 Prima de riesgo de trabajo es específica por empresa (se declara ante el
IMSS), no hay "un" número. 🔴 % patronal exacto de CEAV por rango salarial:
verificar tabla de transición vigente contra el IMSS.

**Indemnización despido sin justa causa:** 3 meses de salario + 20 días por
año de servicio (si no opta por reinstalación) + prima de antigüedad de 12
días/año (salario topado a 2 SM, desde el primer año, independiente de la
causa).

**Pago de nómina:** máximo 1 semana (obreros) o 15 días/quincenal (resto);
**mensual es ilegal**. ISR: retención en la fuente obligatoria, tabla
progresiva de 11 tramos (1,92%–35%) según Art. 96 LISR — 🔴 montos exactos en
pesos de cada tramo 2026 no confirmados en fuente primaria, verificar contra
Resolución Miscelánea Fiscal / SAT.

---

## Perú

**Jornada:** 8h diarias/48h semanales. Nocturna 10pm-6am con sobretasa
mínima 35% sobre RMV. Horas extra: 25% (primeras 2h), 35% (resto).

**Contratos:** indeterminado (regla general); sujeto a modalidad/plazo fijo
(requiere causa objetiva, debe registrarse ante el MTPE en 15 días o se
presume indeterminado); part-time (<4h/día promedio, sin CTS ni indemnización).

**RMV 2026:** **S/ 1.130/mes** (D.S. 006-2024-TR, sin decreto sustitutorio
confirmado a la fecha — hay anuncios de S/1.230/S/1.300 pero 🔴 sin decreto
que los formalice, no tratarlos como vigentes). Asignación familiar: 10% de
RMV = S/113/mes fijo (con hijos menores de 18, o hasta 24 si estudian).

**Vacaciones:** 30 días calendario/año, sujeto a récord vacacional (260 o 210
días laborados según jornada de 6 o 5 días/semana).

**Gratificación (equivalente a 13er/14vo):** 2 veces al año (julio y
diciembre), cada una = 1 remuneración computable, prorrateada por meses
trabajados en el semestre. Bonificación extraordinaria 9% (sustituye el
aporte EsSalud que ya no se descuenta de las gratificaciones).

**CTS** (fondo de cesantía, no sueldo adicional): depositado 2 veces al año
(mayo/noviembre). Fórmula: (remuneración computable + 1/6 gratificación) ÷12
× meses trabajados.

**Seguridad social** — sistema **paralelo**, el trabajador elige pensión
pública (ONP) o privada (AFP), nunca ambas:

| Concepto | Entidad | % Empleador | % Empleado |
|---|---|---|---|
| Salud | EsSalud | **9%** | 0% |
| Pensión pública | ONP | 0% | 13% |
| Pensión privada | AFP (a elegir) | 0% | ~10% aporte + 1,37% seguro + comisión variable por AFP (1,47%–1,69%) ≈ **12,8%–13,1% total** |
| Riesgo laboral (solo actividades de alto riesgo) | SCTR | 100% empleador, tasa variable | 0% |
| CTS | Entidad financiera del trabajador | 100% empleador | 0% |

🔴 Comisión AFP varía por administradora — parametrizar, no hardcodear;
verificar contra SBS. 🔴 Prima de seguro 1,37% (Ley 32123) sin verificación
directa del texto legal.

**Indemnización despido arbitrario:** 1,5 remuneraciones/año completo, tope
12 remuneraciones (indeterminado). Plazo para reclamar: 6 meses.

**Pago de nómina:** mensual es lo habitual (a diferencia de México). Renta
5ta categoría (SUNAT): deducción fija 7 UIT/año (UIT 2026 = S/5.500 →
S/38.500 exentos), tramos 8%/14%/17%/20%/30% sobre el excedente. 🔴 Tabla de
tramos confirmada por fuentes secundarias coincidentes, no extraída
directamente de SUNAT — confirmar contra decreto/resolución vigente.

---

## Chile

**Jornada:** **42 horas semanales** desde el 26-abr-2026 (Ley 21.561,
"Ley de 40 Horas": 45h→44h→**42h (vigente)**→40h en 2028). Horas extra:
recargo 50%, máx. 2h/día, pactadas por escrito (vigencia máx. 3 meses).

**Contratos:** indefinido (regla general); plazo fijo (máx. 1 año, 2 para
gerentes/profesionales; segunda renovación o continuidad tácita = indefinido);
por obra/faena/servicio determinado (sin indemnización por años de servicio
al terminar por conclusión de la obra).

**Ingreso Mínimo Mensual (IMM) 2026** (Ley 21.830, desde 1-may-2026,
retroactivo): 18-65 años **$553.553 CLP**; <18 o >65 años **$412.938**; solo
efectos no remuneracionales **$356.815**.

**Vacaciones (feriado anual):** 15 días **hábiles** (lun-vie)/año tras 1 año
de antigüedad; 20 días en Magallanes/Aysén/Palena. Feriado progresivo: +1 día
cada 3 años tras 10 años cotizados (en cualquier empleador).

**Gratificación (NO hay aguinaldo legal general en Chile):** obligatoria solo
en empresas con utilidades, dos modalidades a elección del empleador: 30% de
la utilidad líquida repartida proporcionalmente, o **25% de las
remuneraciones mensuales devengadas, tope 4,75 IMM/año** (≈$2.629.377
CLP/año) — esta segunda es la más usada.

**Seguridad social** — base: renta imponible, tope 90 UF (135,2 UF para AFC):

| Concepto | % Empleador | % Empleado |
|---|---|---|
| AFP (pensión) | 0% | 10% + comisión variable 0,44%-1,45% según AFP |
| Salud (Fonasa/Isapre) | 0% | 7% (o más si el plan Isapre cuesta más) |
| SIS (Seguro Invalidez y Sobrevivencia) | **1,62%** (desde abr-2026) | 0% |
| AFC (cesantía) — contrato indefinido | 2,4% | 0,6% |
| AFC — contrato plazo fijo/obra | 3% | 0% (liberado) |
| Mutualidad Ley 16.744 (accidentes) | 0,90% + 0%-3,4% diferenciada + 0,015% | 0% |
| Nuevo aporte reforma previsional (Ley 21.735) | 3,5% desde ago-2026, sube a 8,5% en 2033 | 0% |

🔴 Comisión AFP no es un valor legal único — parametrizar por administradora.

**Indemnización despido sin justa causa:** 30 días de última remuneración por
año de servicio, tope 11 años (330 días); + 1 mes sustitutivo de aviso previo
si no se avisa con 30 días; +30%/50%/80% de recargo si el tribunal declara
injustificado el despido.

**Pago de nómina:** máximo 1 mes (mensual es lo habitual). Impuesto Único 2ª
Categoría: retenido en la misma liquidación, 8 tramos progresivos 4%-40%,
exento hasta 13,5 UTM.

---

## Brasil

**Jornada:** 8h diarias/**44h semanales** (sin cronograma de reducción legal
vigente, a diferencia de Chile). Horas extra: recargo mínimo 50%, hasta 100%
en domingos/feriados sin compensar.

**Contratos (CLT):** indeterminado (regla general); plazo determinado (máx.
2 años, 1 sola prórroga); contrato de experiencia (máx. 90 días, subtipo de
plazo determinado); intermitente (convocatoria ≥3 días de anticipación);
tiempo parcial (hasta 30h/semana sin extra, o 26h + 6h extra).

**Salario mínimo 2026:** **R$ 1.621,00/mes** (Decreto 12.797/2025, desde
1-ene-2026). Diario R$54,04, hora R$7,37.

**Férias (vacaciones):** 30 días corridos tras 12 meses, **+ 1/3
constitucional obligatorio** (vacaciones valen 4/3 del salario de esos días).
Abono pecuniário: puede vender hasta 10 días, exento de INSS/IRRF.

**13º salário (gratificação natalina):** remuneración mensual ÷12 × meses
trabajados. Pago en 2 cuotas: 50% sin descuentos hasta 30-nov; saldo con
INSS/IRRF descontados sobre el total, hasta 20-dic.

**Seguridad social** — INSS empleado, tabla progresiva 2026 (Portaria
Interministerial MPS/MF 13, ene-2026):

| Salario de contribución | Alícuota |
|---|---|
| Hasta R$1.621,00 | 7,5% |
| R$1.621,01–2.902,84 | 9,0% |
| R$2.902,85–4.354,27 | 12,0% |
| R$4.354,28–8.475,55 (techo) | 14,0% |

Cálculo progresivo por tramos (no plano).

| Concepto | % Empleador | % Empleado |
|---|---|---|
| INSS patronal (base) | 20% | — |
| RAT (riesgo laboral) | 1%-3% según actividad (ajustado por factor FAP) | — |
| "Sistema S" (Sesi/Senai/Sebrae/etc.) | ≈5,8% adicional, varía por sector | — |
| INSS empleado | — | 7,5%-14% progresivo (tabla arriba) |
| FGTS | **8%** mensual (también sobre el 13º) — va a cuenta del trabajador en Caixa, no es descuento | 0% |

Carga patronal total efectiva (régimen general): ~25%-28% de la nómina.
🔴 **Empresas en Simples Nacional o con CPRB/desoneração cotizan distinto** —
el régimen tributario del empleador debe ser un parámetro, no un valor fijo.

**Indemnización despido sin justa causa:** aviso prévio 30 días + 3
días/año completo (tope 90 días); multa 40% de TODO el FGTS depositado
durante el contrato (20% si es por acuerdo mutuo, 0% con justa causa/renuncia).

**Pago de nómina:** mensual obligatorio, hasta el 5º día útil del mes
siguiente. IRRF retenido en la nómina, tabla 2026 (Lei 15.270/2025): exento
hasta R$2.259,20; luego 7,5%/15%/22,5%/27,5% con deducciones por tramo.
🔴 Existe un "redutor" adicional que amplía la exención hasta ~R$5.000 cuya
fórmula exacta no se confirmó — verificar contra la Lei 15.270/2025 o
instrução normativa de Receita Federal antes de programarlo.

---

## Argentina

🔴 **Cambio legal reciente crítico**: Ley 27.802 "Ley de Modernización
Laboral" (sancionada 27-feb-2026, vigente desde 1-jun-2026) modificó
sustancialmente jornada, vacaciones e **indemnización por despido**. El
motor debe distinguir **fecha de inicio del contrato** (antes/después de
1-jun-2026) porque aplican fórmulas distintas.

**Jornada:** 8h/48h semanales (Ley 11.544/LCT). Extra: 50% días hábiles,
100% sábado tarde/domingo/feriado. Ley 27.802 permite banco de horas y
francos compensatorios en vez de pago de horas extra (con descansos mínimos
de 12h entre jornadas y 35h semanales).

**Contratos (LCT):** indeterminado (presunción legal); plazo fijo (máx. 5
años, forma escrita); de temporada; eventual; tiempo parcial. Período de
prueba: 6 meses.

**SMVM** (Resolución 4/2026, muy volátil, verificar siempre vigente):
$383.800 desde 1-sep-2026, subiendo mensualmente ($391.200 oct, $398.800 nov,
$406.400 dic-2026...).

**Vacaciones:** días corridos según antigüedad — 14 días (≤5 años), 21 (5-10
años), 28 (10-20 años), 35 (>20 años). Pago: sueldo mensual ÷25 × días.
🔴 Ley 27.802 permite fraccionar en períodos ≥7 días, aviso reducido a 30
días (antes 45).

**SAC (aguinaldo):** 50% de la mejor remuneración mensual del semestre, 2
cuotas (30-jun y 18-dic). 🔴 Ley 27.802 **excluye el SAC** (y vacaciones y
bonos no mensuales) de la base de cálculo de la indemnización por despido.

**Seguridad social:**

| Concepto | % Empleador | % Empleado |
|---|---|---|
| Contribución patronal unificada (jubilación+PAMI+FNE+Asig.Familiares) | 18% (general) o 20,40% (Servicios/Comercio grandes) | — |
| Jubilación (SIPA) | (incluido arriba) | 11% |
| INSSJP (PAMI) | (incluido arriba) | 3% |
| Obra social | 6% | 3% |
| ART (riesgos del trabajo) | 100% empleador, tasa variable por ART/actividad | — |

Total aporte empleado sobre bruto: 17%. 🔴 Desglose exacto por subsistema de
la contribución patronal unificada no confirmado en fuente oficial 2026 —
solo el total (18%/20,40%) está confirmado. Ley 27.802 crea además un Fondo
de Asistencia Laboral opcional (1%-2,5%) que puede sustituir la indemnización
tradicional, solo si el convenio colectivo lo prevé y el trabajador lo acepta
expresamente — por defecto sigue rigiendo el art. 245 LCT clásico.

**Indemnización despido sin justa causa (contratos desde 1-jun-2026):** 1 mes
de la mejor remuneración normal y habitual (excluye SAC/vacaciones/bonos no
mensuales) por año de servicio o fracción >3 meses, con tope de 3x el
promedio del convenio colectivo (piso 67% del cálculo sin tope). Contratos
**anteriores** al 1-jun-2026 siguen la fórmula clásica sin esas exclusiones.
Preaviso: 15 días/1 mes/2 meses según antigüedad.

**Pago de nómina:** mensual (mensualizados, hasta 4º día hábil siguiente) o
quincenal (jornalizados). Impuesto a las Ganancias 4ª categoría: retenido en
nómina si supera el mínimo no imponible, 🔴 actualizado semestralmente por
AFIP/ARCA, valor exacto 2º semestre 2026 no confirmado con certeza (fuentes
contradictorias) — consultar tabla oficial vigente al momento del cálculo.

---

## Ecuador

**Jornada:** 8h diarias/40h semanales (Código del Trabajo art. 47).
Suplementarias (6am-12am): 50%. Extraordinarias (12am-6am, sáb/dom/feriados):
100%. Máximo 4h extra/día, 12h/semana.

**Contratos:** indefinido (regla general; el plazo fijo general **fue
eliminado en 2015**, 🔴 verificar si subsisten excepciones sectoriales);
eventual (máx. 180 días/año); ocasional (máx. 30 días continuos); de
temporada; por obra/servicio/destajo. Prueba: hasta 90 días.

**SBU 2026:** **USD 482,00/mes** (Acuerdo MDT-2025-195, desde 1-ene-2026).

**Vacaciones:** 15 días corridos/año; +1 día por año adicional tras 5 años
(máx. 15 extra = 30 total). Pago: 1/24 de todo lo percibido en el año
(excluye décimos, utilidades, viáticos, alimentación, transporte, seguros).

**Décimo tercero:** 1/12 de sueldo+comisiones+bonos+extras percibidos entre
1-dic del año anterior y 30-nov del año en curso. Pago hasta 24-dic (o
mensualizado si no se pide acumular).

**Décimo cuarto:** 1 SBU completo (o proporcional). Pago: Costa/Galápagos
hasta 15-mar; Sierra/Amazonía hasta 15-ago.

**Seguridad social (IESS):**

| Concepto | % Empleador | % Empleado |
|---|---|---|
| Seguro General Obligatorio (salud, IVM, riesgos, cesantía) | 11,15% | 9,45% |
| Fondo de Reserva (desde 2º año continuo) | 8,33% (a elección del trabajador: mensualizado o acumulado en IESS) | — |
| IECE/SECAP (capacitación) | 1% (0,5%+0,5%) | — |

Total combinado Seguro General: 20,60%. 🔴 Porcentajes 9,45%/11,15%
consistentes entre fuentes de nómina pero no verificados directamente en
iess.gob.ec — confirmar antes de fijar como constante. 🔴 Vigencia actual del
1% IECE/SECAP tras fusión en SETEC (2011) no confirmada con norma vigente.

**Indemnización despido intempestivo — DOS rubros acumulativos (error común
liquidar solo uno):**
- Art. 188: hasta 3 años → 3 meses de remuneración; más de 3 años → 1
  mes/año, tope 25 meses.
- Art. 185 (bonificación por desahucio): 25% de la última remuneración por
  cada año **completo** (fracciones no cuentan para este rubro).
- Base de cálculo: la **mejor remuneración percibida en toda la relación
  laboral** (Resolución Corte Nacional de Justicia 02-2025), no
  necesariamente la última.

**Pago de nómina:** sueldo (empleados) máx. 1 mes; salario (jornaleros) máx.
1 semana. Retención IR en relación de dependencia: fracción básica exenta
2026 = USD 12.208/año (Resolución NAC-DGERCGC25-00000043), tabla progresiva
0%-37%. 🔴 Tabla completa tramo por tramo no confirmada, solo el umbral
exento y el rango de tarifas.

---

## Tabla comparativa resumen

| País | Jornada máx. semanal 2026 | Salario mínimo 2026 | Vacaciones/año | Prima/aguinaldo | Aporte empleado a pensión/salud (aprox.) | Aporte empleador (aprox., sin ARL/riesgo) |
|---|---|---|---|---|---|---|
| Colombia | 42h | $1.750.905 COP | 15 días hábiles | Prima 30 días/año (2 pagos) | Salud 4% + Pensión 4% + FSP 1-2% | Pensión 12% + Salud 8,5%* + CCF 4% |
| México | 48h (bajando a 40h en 2030) | $315,04 MXN/día | 12-20 días corridos | Aguinaldo 15 días mín. | ~4-5% (IMSS varios ramos) | ~15-25% (IMSS+INFONAVIT) |
| Perú | 48h | S/1.130/mes | 30 días corridos | Gratificación 2x sueldo/año | 13% (ONP) o ~13% (AFP) | EsSalud 9% |
| Chile | 42h (bajando a 40h en 2028) | $553.553 CLP | 15 días hábiles | Gratificación legal (si hay utilidad) | AFP 10%+com. + Salud 7% | SIS 1,62% + AFC 2,4% + reforma 3,5%+ |
| Brasil | 44h | R$1.621/mes | 30 días corridos +1/3 | 13º salário (2 pagos) | INSS 7,5%-14% progresivo | INSS 20% + RAT 1-3% + Sistema S ~5,8% + FGTS 8% |
| Argentina | 48h | $383.800 ARS (sep-2026) | 14-35 días corridos | SAC 2x sueldo/año | 17% (jubilación+PAMI+obra social) | 18%-20,40% + obra social 6% |
| Ecuador | 40h | USD 482/mes | 15-30 días corridos | Décimo 3º y 4º (2 pagos distintos) | IESS 9,45% | IESS 11,15% + Fondo Reserva 8,33% |

\* Colombia: salud empleador solo aplica sobre el excedente de 10 SMMLV para
empresas exoneradas (Ley 1607).

---

## Vacíos pendientes de verificar antes de producción

Antes de facturar un cálculo real a un cliente, cada uno de estos puntos debe
confirmarse contra la fuente oficial vigente en el momento del período de
nómina (no basta con este documento):

1. **México**: prima de riesgo de trabajo IMSS (varía por empresa); tabla
   exacta en pesos de los 11 tramos de ISR 2026; % patronal exacto de CEAV
   por rango salarial.
2. **Perú**: posible aumento de RMV a S/1.230/S/1.300 (sin decreto
   confirmado); comisión de AFP (varía por administradora, parametrizar);
   tasa de prima de seguro AFP 1,37%.
3. **Chile**: comisión variable de AFP por administradora (0,44%-1,45%).
4. **Brasil**: régimen tributario del empleador (general vs. Simples
   Nacional vs. CPRB) cambia por completo el cálculo del aporte patronal;
   fórmula exacta del "redutor" de IRRF 2026 (Lei 15.270/2025).
5. **Argentina**: desglose exacto por subsistema de la contribución
   patronal unificada; mínimo no imponible de Ganancias del 2º semestre
   2026; alícuota ART (no es un valor único); mecánica completa del Fondo
   de Asistencia Laboral de la Ley 27.802. **Punto crítico**: distinguir
   fecha de inicio de contrato (antes/después de 1-jun-2026) para aplicar
   la fórmula de indemnización correcta.
6. **Ecuador**: tasas IESS 9,45%/11,15% no verificadas directamente en
   iess.gob.ec; vigencia del 1% IECE/SECAP; tabla completa de retención de
   renta 2026; excepciones sectoriales al contrato a plazo fijo.

## Fuentes principales citadas por la investigación

México: DOF (dof.gob.mx), gob.mx/conasami, LFT (diputados.gob.mx). Perú:
gob.pe/mtpe, SBS (sbs.gob.pe), SUNAT. Chile: mintrab.gob.cl, dt.gob.cl,
Superintendencia de Pensiones (spensiones.cl), SUSESO, SII. Brasil:
planalto.gov.br, gov.br/previdencia, TST. Argentina: boletinoficial.gob.ar,
argentina.gob.ar/normativa, AFIP (afip.gob.ar). Ecuador: trabajo.gob.ec,
iess.gob.ec, finanzas.gob.ec.
