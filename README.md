# Nómina Multipaís (prototipo)

Prototipo para el reto de **Hong Kong GSR Technology Limited** (la matriz):
reemplazar 14 (potencialmente 150) Excels de nómina por país, cada uno con su
propia estructura y algoritmo, por un formulario web único que cada contador
local llena, con un motor de cálculo propio por país y un panel consolidado
para la casa matriz — todo en el idioma del usuario (español para
Latinoamérica, portugués para Brasil, inglés para EE.UU./Puerto Rico, **chino
tradicional** para Hong Kong).

Nota: Hong Kong no es lingüísticamente lo mismo que China continental —
cantonés hablado, chino **tradicional** (繁體中文) escrito, inglés como
segundo idioma oficial. China continental usa mandarín y chino
**simplificado** (简体中文). Por eso hay dos locales de chino separados:
`zh` (simplificado, para una eventual filial en China continental) y `zh-hk`
(tradicional, el que usa por defecto la matriz de Hong Kong).

## Cómo correrlo

```bash
pip install -r requirements.txt
python app.py
```

Abre `http://localhost:5057`. Cambia de idioma con los enlaces ES/EN/PT/简体/繁體
del encabezado (independiente del país que se esté consultando: HQ en Hong
Kong puede ver la nómina de Colombia en chino tradicional).

## Motor normativo 2026 (cálculo mensual, liquidación y horas extra)

El cálculo **mensual**, la **liquidación/terminación** y las **horas extra y recargos** de los 7 países con motor ya **no** viven en
fórmulas de código: los ejecuta `payroll_engine/` leyendo datos normativos versionados de `config/payroll/<PAIS>/2026/`
(`manifest.json`, `references*.json`, `series*.json`, `concepts*.json`, `bases*.json`, `rules.json`, `rules_termination.json`,
`rules_overtime.json`, `rounding.json`).

```
NORMA → config/payroll (JSON) → validación de esquema → Rule Resolver (vigencia, ancla, prioridad, tipo de corrida)
      → Dependency Graph → Bases Engine → mecanismos tipados (Decimal) → redondeo por línea
      → resultado → explicación → audit trail → snapshot (entrada + normativa + versión del motor)
```

- **El JSON describe la norma; el código ejecuta el mecanismo.** No hay lenguaje de fórmulas: el JSON guarda tasas, topes, tablas,
  umbrales, referencias (SMMLV, UMA, SMVM, UF…), ventanas jurídicas (semestres, año de servicio…), condiciones, vigencias y tratamientos por base;
  los mecanismos (`mechanisms.py`, `mechanisms_termination.py`) son código tipado y genérico (`service_period_proration`,
  `tiered_service_amount`, `service_quantity`, `remaining_term_amount`, `history_value`, `accrued_in_window`, `hours_at_multipliers`…).
- **Sin `if país`**: el núcleo no contiene códigos de país ni cifras legales (`tests/payroll_2026/test_architecture.py`, `test_hardcoding_y_legado.py`).
  El código heredado se movió a `tests/payroll_2026/legacy_fixtures/` (solo pruebas de regresión: **no es fuente de verdad**);
  `countries/<pais>.py` solo tiene formulario, ejemplos DEMO y etiquetas; `CountryConfig` ya no tiene parámetros legales.
- **Series temporales**: referencias con vigencia (SMMLV, UMA…) y series por fecha (UF diaria del SII, sin extrapolar) resueltas por la fecha ancla.
- **Terminación**: la corrida `TERMINATION` recibe fecha de ingreso, de terminación, tipo de contrato, causa, salario e historiales; cada país declara en su
  manifiesto las causas y contratos soportados. Cada beneficio tiene su propia ventana (p. ej. Perú: CTS por semestre mayo-octubre/noviembre-abril y
  gratificación por meses calendario completos enero-junio/julio-diciembre; Argentina: SAC por semestre).
- **Estado real, no "Motor activo"**: la UI lee el *Capability Manifest*. Componentes críticos por país: nómina mensual, horas extra, recargos,
  vacaciones, seguridad social, prestaciones, terminación, impuesto, auditoría y recálculo histórico. **Ningún país es «implementado»** (falta
  validación profesional humana y el impuesto es un valor digitado); Colombia y los otros 6 son `parcial`; EE. UU. no tiene motor;
  Hong Kong es contexto de consolidación (`local_payroll_engine=false`).
- **Auditoría, reproducibilidad y recálculo**: cada cálculo guarda una corrida inmutable (`payroll_runs`) con su snapshot de entrada, el snapshot
  normativo por hash y la versión del motor. `/run/<id>` muestra líneas, explicación y estado de verificación de cada regla; `/run/<id>/verify`
  recalcula con las reglas históricas y compara hashes; `/run/<id>/recalculate` recalcula con las reglas actuales y explica cada diferencia
  (sin generar ajustes).
- **Fuentes y verificación (cuatro dimensiones separadas)**: `source_verified`, `interpretation_verified`, `implementation_verified` y
  `professional_validated` (`payroll_engine/verification.py`, `docs/SOURCES_REGISTRY_2026.md`). Fuente oficial ≠ interpretación correcta. Una regla
  ejecutada con fuente PENDING/CONFLICTING o con pregunta abierta produce la advertencia `UNVERIFIED_RULE`.

Documentación (generada desde los datos, no editar a mano): `docs/MASTER_PAYROLL_RULES_2026.md`, `docs/LATAM_LABOR_PROFILE_2026.md`,
`docs/ENGINE_RULE_GAP_ANALYSIS.md`, `docs/KILLCRITIC_PAYROLL_2026.md`, `docs/HARDCODING_INVENTORY.md`, `docs/LEGACY_VS_NORMATIVE.md`,
`docs/SOURCES_REGISTRY_2026.md`; auditoría escrita a mano: `docs/CO_LEY_1393_AUDITORIA.md`.

```bash
pip install -r requirements-dev.txt
python -m pytest                              # suite completa (usa una base de datos temporal)
python tools/generate_payroll_docs.py         # regenera docs/ (ejecuta las pruebas)
```

**Cómo incorporar una norma nueva**: editar el JSON del país (nueva versión con `effective.from`, nunca sobrescribir la vigente) → el validador de
esquema la revisa → agregar la prueba de frontera (-1 / exacto / +1) con el esperado calculado de forma independiente → regenerar docs. Si la regla necesita
un mecanismo que no existe, se agrega en `mechanisms*.py` (genérico, sin país).

**Lo que NO está hecho** (no afirmar lo contrario): **impuesto** de los 7 países (valor digitado `EXTERNAL_INPUT`), **validación profesional** de
cualquier regla, fuentes aún SECUNDARIAS/PENDING (tasas de seguridad social de Colombia, UMA, RMV de Perú, SM/INSS de Brasil, intereses de cesantías…), Ley 1393
con alcance sin verificar (cálculo PROVISIONAL), indemnización moratoria, jubilación patronal, salarios vencidos, PTU, INSS/IRRF de la rescisión, EE. UU. estatal/local,
nómina local de Hong Kong, autenticación/CSRF y separación física de datos demo/reales.

## Arquitectura (formulario, países e interfaz)

- `countries/base.py` — `CountryConfig` (solo etiquetas: nombre, moneda, idioma, nombre legal de la liquidación), `FormSpec` (campos del formulario y
  ejemplos DEMO) e interfaz `PayrollEngine`.
- `countries/colombia.py`, `mexico.py`, `peru.py`, `chile.py`, `brasil.py`, `argentina.py`, `ecuador.py` — formulario (`NOVEDADES_CAMPOS`) y ejemplos DEMO.
  **Sin reglas legales**: el motor es `countries/normative_engines.py` / `colombia_normative.py` (adaptadores formulario → `PayrollRun` → pantalla).
- `countries/stubs.py` — EE. UU. y HK (Hong Kong GSR Technology Limited, la matriz) sin motor de nómina local.
- `i18n/{es,en,pt,zh,zh-hk}.json` — diccionarios de traducción de la interfaz
  (`zh` = simplificado/China continental, `zh-hk` = tradicional/Hong Kong).
- `geolocation.py` — detecta el idioma según la ubicación real del visitante
  (ver sección "Geolocalización por IP" más abajo).
- `models.py` — persistencia en SQLite (`instance/nomina.db`) de cada nómina
  calculada, para alimentar el panel consolidado (`/dashboard`).
- `app.py` — rutas Flask: selector de país (`/`), página del país
  (`/pais/<pais>` — plantilla genérica `pais_home.html` con los dos
  submódulos: Novedades y Liquidación), formulario de novedades
  (`/novedades/<pais>`), resultado (`/resultado/<id>`), formulario de
  liquidación (`/liquidacion/<pais>`), resultado de liquidación
  (`/liquidacion/resultado/<id>`), panel consolidado (`/dashboard`, incluye
  nóminas y liquidaciones), exportar Excel (`/dashboard/export.xlsx`) y PDF
  (`/dashboard/export.pdf`) — ambos en el idioma actual de quien los descarga.

**Principio de diseño clave**: la plantilla es genérica en la ESTRUCTURA
(mismas rutas, mismos dos submódulos, mismo layout para cualquier país), pero
las ETIQUETAS de cada formulario pueden y deben usar la jerga real de cada
país (Colombia dice "EPS"/"AFC"/"retención en la fuente" porque así lo conoce
un contador colombiano) — generalizar esas palabras no aporta nada y le resta
precisión a quien digita. Lo que sí tiene que ser genérico y consistente es
el RESULTADO consolidado (`/dashboard` y sus exportaciones): columnas como
"total devengado", "neto pagado", "total aportes patronales" son las mismas
sin importar el país de origen — eso es lo que le permite a Diego entender y
consolidar los 14 países sin tener que aprenderse la jerga de cada uno.
- `exports.py` — genera los archivos de exportación con `openpyxl` (Excel) y
  `reportlab` (PDF). Para el PDF en chino (tradicional `zh-hk` o simplificado
  `zh`) usa las fuentes CID que trae `reportlab` — sin esto el PDF no puede
  dibujar caracteres chinos. **Ojo con un bug real de reportlab**: su tabla
  interna (`defaultUnicodeEncodings`) asocia la fuente china tradicional
  `MSung-Light` a la codificación `UniGB-UCS2-H`, que es de chino
  **simplificado** — usarla tal cual produce texto con los glifos
  equivocados. `exports.py` la corrige registrando esa fuente manualmente con
  la codificación correcta `UniCNS-UCS2-H` (verificado extrayendo el texto
  del PDF generado con PyMuPDF antes y después del fix).

## Cómo agregar un país nuevo

1. Crear `countries/<pais>.py` con una función que devuelva su `CountryConfig`
   y una clase que implemente `PayrollEngine.calcular()` Y `liquidar()` (usa
   `colombia.py` como plantilla — `campos_extra` del stub ya trae la fórmula
   de indemnización investigada, lista para traducir a código).
2. En `countries/__init__.py`, importar esa clase/config y moverla del bloque
   de `STUB_CONFIGS` al `REGISTRY` principal.
3. No hay que tocar el formulario, el dashboard ni los idiomas — el sistema ya
   está armado para que sumar un país sea solo escribir su fórmula.

## Ficha de personal y alertas (control anti-fraude)

Cada país tiene una tercera pantalla, "Personal" (`/personal/<pais>`), que es
su ficha maestra de empleados: identificación, nombre, cargo, salario base,
fecha de ingreso, estado. Se carga por Excel (botón "Descargar plantilla" +
subir el archivo lleno, `personal.py`) o agregando un empleado a la vez desde
un formulario. Al recargar el Excel, un empleado con la misma identificación
se actualiza (no se duplica).

`alertas.py` cruza esa ficha contra todas las nóminas y liquidaciones
guardadas, y expone el resultado en `/alertas` (enlace en el encabezado,
visible en cualquier idioma). Se decidió deliberadamente **no bloquear** la
captura cuando algo no cuadra (romper el flujo de trabajo real por un dato
faltante es peor que la alerta) — se permite igual y queda marcado para que
Diego lo revise. Alertas que genera hoy:

- **Empleado no encontrado en la ficha**: la nómina o liquidación trae una
  identificación que no está en la ficha de ese país.
- **Salario no coincide con la ficha**: el salario digitado difiere más de
  15% del `salario_base` registrado (umbral configurable en `alertas.py`).
- **Posible doble liquidación**: hay más de una liquidación para la misma
  identificación en el mismo país.
- **Nómina posterior a la liquidación**: existe una nómina con periodo
  posterior a la fecha de retiro ya registrada para ese empleado — el caso
  clásico de "le siguieron pagando después de que se fue".

Las alertas se calculan al vuelo en cada visita a `/alertas` (no se
persisten), para no arrastrar alertas "viejas" después de que alguien
corrija un dato. Probado end-to-end con datos de prueba disparando los 4
tipos de alerta a propósito — todas se detectaron correctamente.

## Módulo de liquidación (riesgo jurídico de despidos)

Aparte de la nómina mensual, cada país tiene una segunda pantalla
(`/liquidacion/<pais>`) para calcular la liquidación final cuando termina un
contrato — con o sin justa causa, renuncia o mutuo acuerdo. Es el cálculo de
mayor riesgo legal del sistema: aplicar la indemnización a una renuncia, o
usar la fórmula de un tipo de contrato que no corresponde, es la causa más
común de demandas laborales por liquidación (ver advertencias en
`NORMATIVA_PAISES.md`, especialmente Ecuador con sus dos indemnizaciones
acumulativas y Argentina con la Ley 27.802).

- Cada país tiene su propio nombre legal para este documento
  (`config.nombre_liquidacion`): "Finiquito" en México/Chile, "Liquidación de
  beneficios sociales" en Perú, "Rescisão (TRCT)" en Brasil, "Liquidación
  final" en Argentina, "Acta de finiquito" en Ecuador — se muestra tal cual en
  la interfaz, sin traducirlo, porque es terminología legal, no una etiqueta
  de UI.
- La liquidación corre sobre el motor normativo (corrida `TERMINATION`): el formulario ofrece solo las causas y tipos de contrato que el manifiesto de cada país
  declara soportados, valida la entrada (400 con el motivo) y guarda la corrida auditable (`/run/<id>`). Cubre por país: **CO** cesantías, intereses, prima,
  vacaciones e indemnización del art. 64 (indefinido <10 / ≥10 SMMLV, término fijo, obra o labor); **PE** CTS, gratificación, bonificación 9 %, vacaciones e
  indemnización; **AR** SAC por semestre, vacaciones, art. 245 (texto Ley 27.802), preaviso e integración; **MX** aguinaldo, vacaciones, prima vacacional, 3 meses +
  20 días, prima de antigüedad; **CL** art. 163 con tope de 90 UF (serie UF del SII), aviso, feriado proporcional; **BR** 13.º, férias + 1/3, aviso previo, FGTS y
  multa; **EC** décimos acumulados, vacaciones, despido intempestivo y desahucio. Lo que no calcula figura en «Brechas conocidas» de cada país.
- El campo «Salarios pendientes» del formulario incluye el salario de los días del mes de terminación (el motor no lo agrega aparte para no contarlo dos veces);
  «Días de vacaciones pendientes» son los de períodos anteriores (los del año en curso se calculan solos).
- El panel consolidado (`/dashboard`) lista también las liquidaciones
  procesadas, con el tipo de terminación y si incluyó indemnización o no —
  para que quede visible y auditable qué se liquidó y por qué.

## Simplificaciones deliberadas de este prototipo (documentadas para continuar)

- **Retención en la fuente (Colombia)**: se recibe como valor manual, igual que
  en el Excel de origen. El cálculo automático por tabla UVT queda pendiente.
- **Cesantías (Colombia)**: el Excel de referencia tenía la celda de cesantías
  copiada de la celda de prima (parecía un error de plantilla, dos fórmulas
  distintas dando el mismo resultado por casualidad). Aquí se calculan de forma
  independiente, ambas al 8.33%, que es lo correcto legalmente.
- **Planilla PILA (columnas AQ:AW del Excel)**: es un cruce de verificación para
  el pago de aportes, no afecta el neto del empleado ni las provisiones. No se
  implementó en este prototipo.
- **Geolocalización por IP** (`geolocation.py`): en la página de inicio y el
  panel consolidado (donde no hay un país de contexto todavía), el idioma se
  detecta automáticamente según la IP del visitante vía `ip-api.com` (gratis,
  sin API key). En un formulario de país específico (`/novedades/<pais>`,
  `/liquidacion/<pais>`) manda el idioma legal de ESE país, no la ubicación
  física de quien lo llena — un contador brasileño de viaje sigue llenando el
  formulario de Brasil en portugués. Limitaciones a tener en cuenta: no
  funciona en desarrollo local (IP privada, sin geolocalizar — cae a
  `Accept-Language`/español), depende de un servicio externo de terceros (si
  falla o se agota el límite gratuito, cae igual al siguiente criterio, nunca
  rompe la página), y la precisión de geolocalización por IP no es perfecta
  (VPNs, proxies corporativos). Para producción con más tráfico, considerar
  una base de datos local tipo MaxMind GeoLite2 en vez de la API gratuita.
- **Cifras legales**: viven en `config/payroll/<PAIS>/2026/` con su fuente y estado de
  verificación. Solo las marcadas OFFICIAL tienen respaldo oficial verificado; el resto es SECONDARY
  o PENDING. Ninguna tiene validación profesional: verifícalas antes de usarlas con un cliente real.
- **Los diccionarios `i18n/*.json` se cargan una sola vez al iniciar el
  proceso** (`app.py`), no en cada request. El recargador de Flask (`debug=True`)
  detecta cambios en archivos `.py`, pero no en estos `.json` — si editas una
  traducción, reinicia el servidor para verla reflejada.
- **Liquidación**: el salario base sale del historial mensual (`salary_history`) cuando existe (Colombia: último salario o promedio del año si varió en los 3 últimos
  meses, art. 253 CST); el formulario web no tiene el historial (usa el salario del contrato o el «salario base de liquidación»); la API del motor sí lo acepta.

## Origen de los datos

- `Planilla nomina 2026-08 ejemplo.xlsx` (aportado por el usuario): estructura
  y fórmulas de la nómina de Colombia de la empresa cliente.
- Infografía comparativa laboral LATAM 2026 (aportada por el usuario): salario
  mínimo, jornada semanal, vacaciones y tipo de prima/aguinaldo de México, Perú,
  Chile, Brasil, Argentina y Ecuador.
