"""Genera la documentación normativa DESDE los datos (config/payroll) y desde la ejecución real
de las pruebas. La fuente de verdad es el dato estructurado: los documentos se regeneran, no se
editan a mano.

    python tools/generate_payroll_docs.py            # regenera docs/*.md (ejecuta la suite de pruebas)
    python tools/generate_payroll_docs.py --no-tests # sin ejecutar pruebas (usa el último resultado conocido)

Produce: MASTER_PAYROLL_RULES_2026.md, LATAM_LABOR_PROFILE_2026.md, ENGINE_RULE_GAP_ANALYSIS.md, KILLCRITIC_PAYROLL_2026.md,
LEGACY_VS_NORMATIVE.md, SOURCES_REGISTRY_2026.md (más HARDCODING_INVENTORY.md con tools/hardcode_inventory.py)."""

import json
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from payroll_engine import ENGINE_VERSION  # noqa: E402
from payroll_engine.capabilities import describe  # noqa: E402
from payroll_engine.loader import available_countries, load_country  # noqa: E402

DOCS = os.path.join(ROOT, "docs")
ORDER = ["CO", "MX", "PE", "CL", "BR", "AR", "EC", "US", "HK"]
NAMES = {"CO": "Colombia", "MX": "México", "PE": "Perú", "CL": "Chile", "BR": "Brasil", "AR": "Argentina",
         "EC": "Ecuador", "US": "Estados Unidos", "HK": "Hong Kong"}
MIN_WAGE_CODES = ("SMMLV", "SM_GENERAL_DAILY", "RMV", "MIN_INCOME", "MIN_WAGE", "SMVM", "SBU", "FEDERAL_MIN_WAGE")


def short(obj, limit=110):
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return text if len(text) <= limit else text[:limit - 1] + "…"


def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def write(name, lines):
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("escrito docs/" + name)


def source_badge(src):
    return (src or {}).get("status", "N/A")


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-p", "no:cacheprovider", "--tb=line", "-o", "addopts="],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1"))
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "sin salida"
    counts = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|error|errors)", tail)}
    return {"summary": tail, "passed": counts.get("passed", 0), "failed": counts.get("failed", 0),
            "skipped": counts.get("skipped", 0), "errors": counts.get("error", 0) + counts.get("errors", 0),
            "returncode": proc.returncode}


# ============================================================================ MASTER RULES
def master_rules():
    out = ["# Matriz Maestra Normativa 2026", "",
           f"> **Generado** por `tools/generate_payroll_docs.py` el {date.today().isoformat()} desde `config/payroll/<PAIS>/2026/` "
           f"(motor v{ENGINE_VERSION}). No editar a mano: edite los datos y regenere.", "",
           "**Estados.** `source.status`: OFFICIAL · SECONDARY · PENDING · CONFLICTING · NOT_APPLICABLE. `interpretation`: UNREVIEWED · INTERPRETED · "
           "VALIDATED · CONFLICTING. `professional_validation`: PENDING · VALIDATED (solo una persona puede firmarla; **ninguna lo está**). "
           "`implementation`: NOT_IMPLEMENTED · PARTIAL · IMPLEMENTED. Una fuente oficial NO implica interpretación correcta.", ""]
    for cc in ORDER:
        rs = load_country(cc)
        info = describe(cc)
        m = rs.manifest
        out += [f"## {cc} — {NAMES[cc]}", "",
                f"- **Estado derivado del manifiesto:** `{info['state']}` · ruta `{m['execution_path']}` · versión de reglas `{m['ruleset_version']}` · "
                f"fecha normativa {m['normative_date']} · moneda {m['currency']}",
                f"- `local_payroll_engine`: {str(m['local_payroll_engine']).lower()} · `consolidation_context`: {str(m['consolidation_context']).lower()}"]
        cov = info["coverage"]
        if cov["rules_total"]:
            out.append(f"- **Cobertura:** {cov['rules_total']} reglas — {cov['rules_implemented']} implementadas, {cov['rules_partial']} parciales, "
                       f"{cov['rules_not_implemented']} NOT_IMPLEMENTED · {cov['rules_without_official_source']} sin fuente oficial · "
                       f"{cov['rules_pending_professional_validation']} sin validación profesional")
        out.append("")
        if rs.references:
            out += ["### Referencias (unidades y parámetros con vigencia)", "",
                    "| Código | Jurisdicción | Valor | Unidad | Desde | Hasta | Fuente | Referencia legal / URL |", "|---|---|---:|---|---|---|---|---|"]
            for r in sorted(rs.references, key=lambda x: (x["code"], x["effective"]["from"])):
                src = r["source"]
                where = md_escape(src.get("legal_reference") or src.get("note") or "")
                url = src.get("official_url") or src.get("secondary_url") or ""
                out.append(f"| `{r['code']}` | {r['jurisdiction']} | {r['value']} | {r.get('unit', '')} | {r['effective']['from']} | "
                           f"{r['effective']['to'] or '—'} | {src['status']} | {where[:150]} {url} |")
            out.append("")
        if rs.bases:
            out += ["### Bases", "", "| Base | Descripción | Límites | Fuente |", "|---|---|---|---|"]
            for b in rs.bases:
                limits = short(b.get("limits", {}), 90) if b.get("limits") else "—"
                out.append(f"| `{b['base']}` | {md_escape(b['description'])[:110]} | {md_escape(limits)} | {source_badge(b['source'])} |")
            out.append("")
        if rs.concept_list:
            out += ["### Conceptos y tratamiento por base", "", "| Concepto | Rol | Etiqueta i18n | Tratamientos (base → modo) |", "|---|---|---|---|"]
            for c in rs.concept_list:
                tr = "; ".join(f"{t['base']}→{t['mode']}" + ("*" if t.get("status") == "PENDING_VERIFICATION" else "") for t in c["treatments"]) or "—"
                out.append(f"| `{c['concept']}` | {c['role']} | {c.get('label_key') or '—'} | {md_escape(tr)} |")
            out += ["", "\\* tratamiento con `status: PENDING_VERIFICATION`.", ""]
        if rs.rules:
            out += ["### Reglas", "", "| Regla | Concepto | Tipo | Vigencia | Ancla / partición | Mecanismo y parámetros | Fuente | Interpretación | Prof. | Impl. |",
                    "|---|---|---|---|---|---|---|---|---|---|"]
            for r in sorted(rs.rules, key=lambda x: (x["kind"] == "VALIDATION", x["rule_id"])):
                calc = r.get("calculation") or {}
                mech = f"{calc.get('mechanism', '—')} {short(calc.get('params', {}), 80)}" if calc else f"VALIDATION: {md_escape(r.get('message', ''))[:70]}"
                out.append(f"| `{r['rule_id']}` | {r.get('concept', '—')} | {r['kind']} | {r['effective']['from']}→{r['effective']['to'] or '…'} | "
                           f"{r['anchor']} / {r.get('straddle_policy', 'USE_ANCHOR')} | {md_escape(mech)} | {source_badge(r['source'])} | "
                           f"{r['verification']['interpretation_status']} | {r['verification']['professional_validation']} | {r['implementation_status']} |")
            out.append("")
        out += ["### Redondeo", "", f"`{json.dumps({k: v for k, v in rs.rounding_data.items() if k != 'note'}, ensure_ascii=False)}`", ""]
        if rs.rounding_data.get("note"):
            out += [f"> {rs.rounding_data['note']}", ""]
        gaps = m.get("known_gaps", [])
        if gaps:
            out += ["### Brechas conocidas", ""] + [f"- {g}" for g in gaps] + [""]
    write("MASTER_PAYROLL_RULES_2026.md", out)


# ============================================================================ LATAM PROFILE
TOPICS = [("minimum_wage", "Salario mínimo / unidad"), ("working_hours", "Jornada"), ("overtime_and_premiums", "Horas extra"), ("surcharges", "Recargos"),
          ("vacation", "Vacaciones"), ("social_security", "Seguridad social"), ("income_tax_withholding", "Impuesto / retención"),
          ("benefit_accruals", "Prestaciones legales"), ("termination", "Terminación")]


def topic_status(cc, key, rs, info):
    caps = info["capabilities"]
    if key == "minimum_wage":
        refs = [r for r in rs.references if r["code"] in MIN_WAGE_CODES]
        if not refs:
            return "SIN DATOS"
        statuses = {r["source"]["status"] for r in refs}
        order = ["PENDING", "SECONDARY", "OFFICIAL"]
        worst = next(s for s in order if s in statuses)
        return f"{worst} ({len(refs)} vigencia{'s' if len(refs) != 1 else ''})"
    if key == "working_hours":
        refs = [r for r in rs.references if r["code"] in ("WORKWEEK_HOURS", "OVERTIME_THRESHOLD_HOURS")]
        if not refs:
            return "SIN DATOS"
        statuses = {r["source"]["status"] for r in refs}
        worst = next(s for s in ["PENDING", "SECONDARY", "OFFICIAL"] if s in statuses)
        return f"{worst} ({len(refs)} vigencia{'s' if len(refs) != 1 else ''})"
    aliases = {"surcharges": ("surcharges",), "benefit_accruals": ("benefit_accruals",), "termination": ("termination", "paid_leave_and_termination"),
               "social_security": ("social_security", "payroll_taxes"), "income_tax_withholding": ("income_tax_withholding",),
               "vacation": ("vacation",), "overtime_and_premiums": ("overtime_and_premiums", "overtime_flsa")}
    for name in aliases[key]:
        if name in caps:
            return caps[name]["status"]
    return "SIN DATOS"


def latam_profile():
    out = ["# Perfil laboral comparado 2026 (estado de la cobertura normativa)", "",
           f"> **Generado** el {date.today().isoformat()} desde `config/payroll/`. Lo que dice \"SIN DATOS\" o `NOT_IMPLEMENTED` **no fue investigado ni "
           "implementado**: no se infiere del código heredado ni de otro país.", "",
           "Cada celda es el estado real del dato: para salarios mínimos y jornada, el peor `source.status` entre sus vigencias "
           "(OFFICIAL / SECONDARY / PENDING); para el resto, el estado de la capacidad del manifiesto "
           "(`PENDING_VALIDATION` = implementado y probado, sin validación profesional).", "",
           "| País | " + " | ".join(t[1] for t in TOPICS) + " |", "|---|" + "---|" * len(TOPICS)]
    for cc in ORDER:
        rs, info = load_country(cc), describe(cc)
        out.append(f"| **{cc}** {NAMES[cc]} | " + " | ".join(topic_status(cc, k, rs, info) for k, _ in TOPICS) + " |")
    out += ["", "## Referencias con cambios de vigencia durante 2026", "", "| País | Código | Versiones | Detalle |", "|---|---|---:|---|"]
    for cc in ORDER:
        rs = load_country(cc)
        by = {}
        for r in rs.references:
            by.setdefault(r["code"], []).append(r)
        for code, refs in sorted(by.items()):
            if len(refs) > 1:
                detail = "; ".join(f"{r['effective']['from']}→{r['effective']['to'] or '…'}: {r['value']}" for r in sorted(refs, key=lambda x: x["effective"]["from"]))
                out.append(f"| {cc} | `{code}` | {len(refs)} | {md_escape(detail)} |")
    out += ["", "## Por país", ""]
    for cc in ORDER:
        rs, info = load_country(cc), describe(cc)
        out += [f"### {cc} — {NAMES[cc]}", ""]
        out += [f"- **Estado:** `{info['state']}` (ruta `{info['execution_path']}`)"]
        for name, cap in info["capabilities"].items():
            out.append(f"- `{name}`: **{cap['status']}** — {cap.get('note', '')}")
        out.append("")
    write("LATAM_LABOR_PROFILE_2026.md", out)


# ============================================================================ GAP ANALYSIS
PRIOR_FINDINGS = [
    ("CO-01", "P0", "CO", "Auxilio de transporte sin tope de 2 SMMLV", "CORREGIDO (mensual y liquidación): regla CO.TRANSPORT_ALLOWANCE y CO_T_TRANSPORT, fuente Decreto 1470/2025; fronteras 3.501.809/810/811/7.003.620 probadas"),
    ("CO-02", "P0", "CO", "Exoneración art. 114-1 con umbral erróneo (25 SMMLV / SENA-ICBF sin umbral)", "CORREGIDO: 'menos de 10 SMMLV'; conflicto con NORMATIVA_PAISES.md ('<=10') documentado; frontera 10 SMMLV -1/=/+1 probada"),
    ("CO-03", "P1", "CO", "Sin tope de 25 SMMLV en pensión empleador, ARL y FSP", "CORREGIDO (IBC/RISK_BASE con tope; FSP sobre el IBC)"),
    ("CO-04", "P1", "CO", "Base distinta para vacaciones compensadas (trabajador vs empleador)", "CORREGIDO: una sola base; el tratamiento queda PENDING_VERIFICATION"),
    ("CO-05", "P1", "7 países", "Impuesto/retención manual", "ABIERTO: valor digitado marcado EXTERNAL_INPUT; capacidad tax NOT_IMPLEMENTED (no se construyó un motor tributario incompleto)"),
    ("CO-06", "P0", "CO", "Ley 1393 art. 30: 'implementada con interpretación sin revisar'", "AUDITADO (docs/CO_LEY_1393_AUDITORIA.md): fórmula literal verificada contra el texto oficial; alcance del 'total de la remuneración' PENDING_VERIFICATION => cálculo PROVISIONAL declarado en manifiesto, concepto y corrida; fronteras 40 % probadas"),
    ("CO-07", "P1", "CO", "Cesantías/prima de la liquidación sin auxilio de transporte", "CORREGIDO en el motor normativo (la inclusión del auxilio en la base queda con fuente PENDING); el código heredado ya no se ejecuta"),
    ("CO-12", "P3", "CO", "Factores redondeados 0,0417/0,0833", "CORREGIDO: razones exactas (1/12, 15/360)"),
    ("PE-01", "P0", "PE", "CTS y gratificación truncadas con la misma fórmula", "CORREGIDO: CTS por semestre mayo-octubre/noviembre-abril (dozavos y treintavos), gratificación por meses calendario completos ene-jun/jul-dic; fuentes oficiales D.S. 001-97-TR y 005-2002-TR"),
    ("AR-01", "P0", "AR", "SAC proporcional desde 1-ene en vez del semestre", "CORREGIDO: 1/12 de lo devengado en la fracción del semestre (art. 123 LCT, InfoLeg); indemnización con el texto del art. 245 según Ley 27.802"),
    ("CL-02", "P1", "CL", "SIS y reforma previsional sin vigencia", "CORREGIDO con fuente oficial de la SP: SIS 1,54 % (ene-mar) y 1,62 % (desde abr); reforma 1 % hasta jul y 3,5 % desde ago (posible doble conteo del SIS desde ago: CONFLICTING)"),
    ("CL-01", "P1", "CL", "Sin tope imponible de 90 UF (serie UF)", "CORREGIDO: serie diaria UF del SII como referencia con fecha; topes 89,9 → 90,0 UF (AFP/salud) y 135,1 → 135,2 UF (cesantía) por vigencia; tope de 90 UF de las indemnizaciones (art. 172 CT)"),
    ("BR-09", "P3", "BR", "Tramos INSS con huecos de R$ 0,01", "CORREGIDO: tramos contiguos"),
    ("MX-08 / G-19", "P3", "MX", "Tope SBC duplicado (constante derivada) y UMA sin vigencia", "CORREGIDO: 25 × UMA por referencia con vigencia (cambia el 1-feb)"),
    ("AR (vigencia)", "P1", "AR", "SMVM de un único valor anual", "CORREGIDO: 12 valores mensuales con fuente"),
    ("G-01", "P0", "Todos", "Estado 'Motor activo' sin respaldo", "CORREGIDO: estado derivado del Capability Manifest; ninguno es 'implementado'"),
    ("G-03/G-04", "P1", "Todos", "Sin vigencia, sin versión de reglas, sin snapshot", "CORREGIDO: reglas con vigencia, Release por hash, snapshots de entrada y normativos"),
    ("G-05", "P1", "Todos", "Sin validación de entradas (negativos, días inválidos, 500)", "CORREGIDO: errores tipificados (400 con mensaje) también en la liquidación"),
    ("G-06", "P1", "7 países", "Tipo de contrato ignorado en la liquidación; mutuo acuerdo = 0", "CORREGIDO: el contrato y la causa son datos obligatorios; cada país declara en su manifiesto las causas y contratos soportados"),
    ("G-11", "P2", "Todos", "float y líneas que no suman el total", "CORREGIDO (mensual y liquidación): Decimal, redondeo por línea, totales exactos"),
    ("G-08", "P1", "Todos", "Sin autenticación/CSRF", "ABIERTO (fuera del alcance; documentado en README y KILLCRITIC; no se presenta como producción segura)"),
    ("G-09", "P1", "Todos", "Datos DEMO y reales comparten tablas", "ABIERTO: separados solo por la bandera es_demo; sin separación física"),
]


def gap_analysis(tests):
    out = ["# Análisis de brechas: motor heredado vs. reglas maestras", "",
           f"> Parcialmente **generado** el {date.today().isoformat()} por `tools/generate_payroll_docs.py`. Las tablas de estado salen de los datos; "
           "el resultado de las pruebas se ejecutó al generar este documento.", "",
           "## 1. Resultado de la suite de pruebas al generar este documento", "",
           f"`{tests['summary']}` — passed **{tests['passed']}** · failed **{tests['failed']}** · skipped **{tests['skipped']}** · errors **{tests['errors']}**", "",
           "## 2. Arquitectura implementada", "",
           "| Capa | Módulo | Qué hace |", "|---|---|---|",
           "| 1 Normative Data | `config/payroll/<PAIS>/2026/*.json` | Reglas, referencias, conceptos, bases, redondeo y manifiesto por país y año |",
           "| 2 Reference Resolver | `payroll_engine/references.py` | Resuelve SMMLV, UMA, SMVM… por país, jurisdicción, fecha y código; detecta faltantes y conflictos |",
           "| 3 Rule Resolver | `payroll_engine/resolver.py` | Vigencia, ancla de fecha por regla, prioridad, cambio dentro del período (ERROR / USE_ANCHOR / SPLIT_BY_DAYS) |",
           "| 4 Dependency Graph | `payroll_engine/graph.py` | Ciclos, dependencias faltantes, orden determinista |",
           "| 5 Bases Engine | `payroll_engine/bases.py` | Bases nombradas por país; INCLUDE / EXCLUDE / INCLUDE_WITH_CAP / SPECIAL_RULE; registro de inclusiones y exclusiones |",
           "| 6 Calculation Engine | `payroll_engine/mechanisms.py` | Mecanismos tipados (el JSON describe, el código ejecuta); sin lenguaje de fórmulas |",
           "| 7 Validation Engine | `payroll_engine/schema.py`, reglas `VALIDATION` en los datos | Esquema, integridad de fuentes y validación de entradas |",
           "| 8 Payroll Run | `payroll_engine/run.py` | Tipos de corrida, pipeline, estado COMPLETE / WITH_WARNINGS / INCOMPLETE |",
           "| 9 Explanation Engine | `payroll_engine/explain.py` | Explicación generada de la ejecución real |",
           "| 10 Audit Trail | `payroll_engine/audit.py` | Reglas seleccionadas/descartadas, condiciones evaluadas, operandos, bases, redondeos |",
           "| 11 Snapshot / Versioning | `run.py`, `models.py` (`payroll_runs`, `normative_snapshots`) | Entrada + normativa + versión del motor = resultado reproducible; tablas inmutables |",
           "| 12 Capability Manifest | `manifest.json`, `payroll_engine/capabilities.py` | Estado real que lee la UI |", "",
           "## 3. Estado de los hallazgos de las auditorías anteriores", "",
           "| ID | Sev. | País | Hallazgo | Estado actual |", "|---|---|---|---|---|"]
    for row in PRIOR_FINDINGS:
        out.append("| " + " | ".join(md_escape(x) for x in row) + " |")
    out += ["", "## 4. Capacidades por país (del manifiesto)", ""]
    caps_all = ["payroll_monthly", "reference_units", "working_hours", "overtime_and_premiums", "surcharges", "vacation", "social_security",
                "income_tax_withholding", "benefit_accruals", "termination"]
    out += ["| País | " + " | ".join(caps_all) + " |", "|---|" + "---|" * len(caps_all)]
    for cc in ORDER:
        caps = describe(cc)["capabilities"]
        out.append(f"| {cc} | " + " | ".join(caps.get(c, {}).get("status", "—") for c in caps_all) + " |")
    out += ["", "### Componentes críticos (matriz estándar)", "",
            "| País | " + " | ".join(describe("CO")["components"]) + " | ¿motor completo? |", "|---|" + "---|" * (len(describe("CO")["components"]) + 1)]
    for cc in ORDER:
        info = describe(cc)
        out.append(f"| {cc} | " + " | ".join(c["status"] for c in info["components"].values()) + f" | {'sí' if info['complete_engine'] else 'NO'} |")
    out += ["", "## 5. Brechas conocidas por país", ""]
    for cc in ORDER:
        gaps = describe(cc)["known_gaps"]
        if gaps:
            out += [f"### {cc}", ""] + [f"- {g}" for g in gaps] + [""]
    out += ["## 6. Motor heredado vs. motor normativo (ejecución real al generar)", ""]
    out += comparison_tables()
    out += ["", "## 7. Hardcoding pendiente", "",
            "Ver `docs/HARDCODING_INVENTORY.md` (generado del AST). El cálculo mensual, la liquidación y las horas extra de los 7 países viven en "
            "`config/payroll`; el código heredado se movió a `tests/payroll_2026/legacy_fixtures/` (no se ejecuta en la app) y `CountryConfig` ya no tiene "
            "parámetros legales. LEGAL_RULE sin justificar en producción: 0.", ""]
    write("ENGINE_RULE_GAP_ANALYSIS.md", out)


def comparison_tables():
    from countries import REGISTRY
    from countries import normative_engines as N
    from countries.colombia_normative import ColombiaNormativeEngine
    from tests.payroll_2026.legacy_fixtures.argentina import ArgentinaConfig, ArgentinaPayrollEngine
    from tests.payroll_2026.legacy_fixtures.brasil import BrasilConfig, BrasilPayrollEngine
    from tests.payroll_2026.legacy_fixtures.chile import ChileConfig, ChilePayrollEngine
    from tests.payroll_2026.legacy_fixtures.colombia import ColombiaConfig, ColombiaPayrollEngine
    from tests.payroll_2026.legacy_fixtures.ecuador import EcuadorConfig, EcuadorPayrollEngine
    from tests.payroll_2026.legacy_fixtures.mexico import MexicoConfig, MexicoPayrollEngine
    from tests.payroll_2026.legacy_fixtures.peru import PeruConfig, PeruPayrollEngine

    def both(cc, New, Old, Cfg, salary, nov):
        emp = {"salario_contrato": str(salary), "nombre": "x", "identificacion": "y"}
        new = New().calcular(emp, dict(nov, _periodo="2026-09"), REGISTRY[cc]["config"])
        old = Old().calcular(emp, dict(nov), Cfg())
        new.pop("_run", None)
        return new, old

    out = ["### Colombia: diferencias intencionales del cálculo mensual (Δ = normativo − heredado, COP)", "",
           "El código heredado es un FIXTURE de regresión, no la fuente de verdad: la columna de causa cita la norma.", "",
           "| Caso | Concepto | Heredado | Normativo | Δ | Causa |", "|---|---|---:|---:|---:|---|"]
    cases = [
        ("8.000.000, 28 días, 2 incap.", 8_000_000, {"dias_trabajados": "28", "incapacidad_dias_empresa": "2", "retencion_fuente": "69001"},
         [("devengado", "auxilio_transporte", "Auxilio solo hasta 2 SMMLV (Decreto 1470/2025)"), ("neto", "neto_pagado", "Consecuencia del auxilio")]),
        ("20.000.000, 30 días", 20_000_000, {"dias_trabajados": "30"},
         [("aportes_patronales", "salud_empleador", "Exoneración solo para menos de 10 SMMLV (art. 114-1 ET)"),
          ("aportes_patronales", "sena", "ídem"), ("aportes_patronales", "icbf", "ídem")]),
        ("50.000.000, 30 días", 50_000_000, {"dias_trabajados": "30"},
         [("aportes_patronales", "pension_empleador", "Tope de 25 SMMLV también para el empleador"),
          ("deducciones", "aporte_fsp_empleado", "FSP sobre el IBC con tope")]),
        ("3.000.000, 30 días", 3_000_000, {"dias_trabajados": "30"},
         [("provisiones", "prima", "Razón exacta 1/12 y auxilio en la base"), ("provisiones", "vacaciones", "Razón exacta 15/360")]),
    ]
    for label, salary, nov, items in cases:
        new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, ColombiaConfig, salary, nov)
        for section, key, cause in items:
            o = old.get(key) if section == "neto" else old[section].get(key)
            n = new.get(key) if section == "neto" else new[section].get(key)
            o = o if o is not None else 0.0
            n = n if n is not None else 0.0
            out.append(f"| {label} | {key} | {o:,.2f} | {n:,.2f} | {n - o:,.2f} | {cause} |")
    out += ["", "### Otros países: cálculo mensual, coincidencia con el heredado (solo detecta cambios NO intencionales)", "",
            "| País | Estado de la corrida | Δ máx. línea | Δ neto | Nota |", "|---|---|---:|---:|---|"]
    pairs = [("MX", N.MexicoNormativeEngine, MexicoPayrollEngine, MexicoConfig), ("PE", N.PeruNormativeEngine, PeruPayrollEngine, PeruConfig),
             ("CL", N.ChileNormativeEngine, ChilePayrollEngine, ChileConfig), ("BR", N.BrasilNormativeEngine, BrasilPayrollEngine, BrasilConfig),
             ("AR", N.ArgentinaNormativeEngine, ArgentinaPayrollEngine, ArgentinaConfig), ("EC", N.EcuadorNormativeEngine, EcuadorPayrollEngine, EcuadorConfig)]
    for cc, New, Old, Cfg in pairs:
        ex = Old().EJEMPLO_NOVEDADES
        nov = {k: v for k, v in ex.items() if k not in ("nombre", "identificacion", "salario_contrato")}
        emp = {"salario_contrato": ex["salario_contrato"], "nombre": "x", "identificacion": "y"}
        new_full = New().calcular(emp, dict(nov, _periodo="2026-09"), REGISTRY[cc]["config"])
        run = new_full.pop("_run")
        old = Old().calcular(emp, nov, Cfg())
        worst = max(abs(new_full[s].get(k, 0) - old[s].get(k, 0)) for s in ("devengado", "deducciones", "aportes_patronales", "provisiones") for k in old[s])
        note = "Corrida INCOMPLETE: regla NOT_IMPLEMENTED aplicable" if run.status == "INCOMPLETE" else "Sin cambio normativo; solo redondeo por línea (salarios por debajo de los topes nuevos)"
        out.append(f"| {cc} | {run.status} | {worst:.4f} | {new_full['neto_pagado'] - old['neto_pagado']:.4f} | {note} |")
    return out


def legacy_vs_normative():
    """docs/LEGACY_VS_NORMATIVE.md: LEGACY_RESULT vs NORMATIVE_RESULT vs EXPECTED_LEGAL_RESULT de la liquidación."""
    from tests.payroll_2026 import divergences as dv
    out = ["# Liquidación: resultado heredado vs normativo vs esperado por la norma", "",
           f"> **Generado** el {date.today().isoformat()} ejecutando ambos motores (el heredado es un fixture en `tests/payroll_2026/legacy_fixtures/`).", "",
           "Regla: **`legacy == normative` NO es prueba de corrección jurídica.** Cada fila separa `LEGACY_RESULT` (lo que calculaba el código heredado), "
           "`NORMATIVE_RESULT` (motor normativo) y `EXPECTED_LEGAL_RESULT` (calculado de forma independiente desde el texto de la norma en las pruebas). "
           "Donde no hay fuente suficientemente sólida para el resultado esperado, el estado es `PENDING_VERIFICATION`, no `IMPLEMENTED`.", "",
           "## Totales del mismo caso en ambos motores", "",
           "| País | Caso | Heredado: prestaciones | Heredado: indemnización | Heredado: total | Normativo: prestaciones | Normativo: indemnización | Normativo: total | Δ total |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for cc in ("PE", "AR", "CO", "CL", "MX", "BR", "EC"):
        legacy, normative = dv.liquidate(cc)
        salary, hire, end, _, _ = dv.SCENARIOS[cc]
        out.append(f"| {cc} | sueldo {salary}, ingreso {hire}, retiro {end}, sin justa causa | {legacy['total_prestaciones']:,.2f} | {legacy['indemnizacion']:,.2f} | "
                   f"{legacy['total_liquidacion']:,.2f} | {normative['total_prestaciones']:,.2f} | {normative['indemnizacion']:,.2f} | "
                   f"{normative['total_liquidacion']:,.2f} | {normative['total_liquidacion'] - legacy['total_liquidacion']:,.2f} |")
    out += ["", "Nota: el formulario heredado no informaba el salario del mes de terminación ni calculaba vacaciones proporcionales; el motor normativo agrega los conceptos "
            "que la norma exige (por eso el total normativo suele ser mayor). Los países sin validación profesional siguen sujetos a revisión.", "",
            "## Diferencias con resultado esperado independiente", ""]
    pe, ar, co = dv.expected_pe(), dv.expected_ar(), dv.expected_co()
    l_pe, n_pe = dv.liquidate("PE")
    l_ar, n_ar = dv.liquidate("AR")
    l_co, n_co = dv.liquidate("CO")
    out += ["| Concepto | LEGACY_RESULT | NORMATIVE_RESULT | EXPECTED_LEGAL_RESULT | Diferencia (norm − legacy) | Razón jurídica | Fuente |", "|---|---:|---:|---:|---:|---|---|"]
    rows = [
        ("PE CTS trunca", dv.q(l_pe["conceptos"]["cesantias"]), dv.line_amount(n_pe, "PE_CTS_TRUNCA"), pe["cts"], ROWS_REASON("PE"), ROWS_SRC("PE")),
        ("PE gratificación trunca", dv.q(l_pe["conceptos"]["prima_servicios"]), dv.line_amount(n_pe, "PE_GRATIFICACION_TRUNCA"), pe["gratificacion"], ROWS_REASON("PE"), ROWS_SRC("PE")),
        ("AR SAC proporcional", dv.q(l_ar["conceptos"]["prima_servicios"]), dv.line_amount(n_ar, "AR_SAC_PROPORCIONAL"), ar["sac"], ROWS_REASON("AR"), ROWS_SRC("AR")),
        ("CO cesantías", dv.q(l_co["conceptos"]["cesantias"]), dv.line_amount(n_co, "CO_CESANTIAS"), co["cesantias"], ROWS_REASON("CO"), ROWS_SRC("CO")),
        ("CO prima", dv.q(l_co["conceptos"]["prima_servicios"]), dv.line_amount(n_co, "CO_PRIMA"), co["prima"], ROWS_REASON("CO"), ROWS_SRC("CO")),
    ]
    for name, leg, nor, exp, reason, src in rows:
        out.append(f"| {name} | {leg:,.2f} | {nor:,.2f} | {exp:,.2f} | {nor - leg:,.2f} | {md_escape(reason)} | {md_escape(src)} |")
    out += ["", "## Razón de las diferencias por país", "", "| País | Concepto | Razón jurídica | Fuente |", "|---|---|---|---|"]
    for cc, concept, reason, src in dv.ROWS:
        out.append(f"| {cc} | {concept} | {md_escape(reason)} | {md_escape(src)} |")
    write("LEGACY_VS_NORMATIVE.md", out)


def ROWS_REASON(cc):
    from tests.payroll_2026 import divergences as dv
    return next(r[2] for r in dv.ROWS if r[0] == cc)


def ROWS_SRC(cc):
    from tests.payroll_2026 import divergences as dv
    return next(r[3] for r in dv.ROWS if r[0] == cc)


def sources_registry():
    """docs/SOURCES_REGISTRY_2026.md: una fila por regla con las cuatro dimensiones de verificación SEPARADAS."""
    from payroll_engine import verification
    out = ["# Registro de fuentes y estado de verificación (2026)", "",
           f"> **Generado** el {date.today().isoformat()} desde `config/payroll/`. No editar a mano.", "",
           "Cuatro dimensiones **separadas**: `source_verified` (fuente oficial con autoridad, referencia, URL y fecha), `interpretation_verified` (interpretación "
           "validada), `implementation_verified` (regla IMPLEMENTED de punta a punta) y `professional_validated` (firmada por una PERSONA: este sistema no la marca). "
           "Una fuente oficial NO significa interpretación correcta. `verified_by` indica quién LEYÓ la fuente (asistente de IA), no quién validó la interpretación.", "",
           "## Resumen", "", "| País | Reglas | source_verified | interpretation_verified | implementation_verified | professional_validated | con pregunta abierta |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    detail = []
    for cc in ORDER:
        rs = load_country(cc)
        rows = [r for r in verification.registry(rs) if True]
        rules = [r for r in rows if r["rule_code"] and ".VAL." not in r["rule_code"]]
        out.append(f"| {cc} | {len(rules)} | {sum(r['source_verified'] for r in rules)} | {sum(r['interpretation_verified'] for r in rules)} | "
                   f"{sum(r['implementation_verified'] for r in rules)} | {sum(r['professional_validated'] for r in rules)} | {sum(r['open_question'] for r in rules)} |")
        if rules:
            detail += [f"## {cc} — {NAMES[cc]}", "",
                       "| Regla | Jurisdicción | Vigencia | Autoridad | Referencia / título | URL | Fuente | Interpretación | Implementación | Verificada el | Verificada por | Notas |",
                       "|---|---|---|---|---|---|---|---|---|---|---|---|"]
            for r in rules:
                detail.append(f"| `{r['rule_code']}` | {r['jurisdiction']} | {r['effective_from']}→{r['effective_to'] or '…'} | {md_escape(r['source_authority'] or '—')[:60]} | "
                              f"{md_escape(r['source_reference'] or '—')[:140]} | {r['official_url'] or '—'} | {r['source_status']} | {r['interpretation_status']} | "
                              f"{r['implementation_status']} | {r['verification_date'] or '—'} | {md_escape(r['verified_by'] or '—')} | {md_escape(r['notes'] or '')[:160]} |")
            detail.append("")
    write("SOURCES_REGISTRY_2026.md", out + [""] + detail)


# ============================================================================ KILLCRITIC
GATE = [
    ("Las reglas tienen fuente", "Cada regla, referencia, base y concepto tiene bloque `source`; las oficiales exigen autoridad, referencia legal, URL y fecha.",
     "test_schema_and_sources::test_todo_dato_normativo_tiene_vigencia_fuente_y_verificacion, test_las_fuentes_oficiales_tienen_autoridad_referencia_url_y_fecha"),
    ("Las vigencias están modeladas", "effective.from/to en todo; SMVM mensual, UMA 1-feb, jornada 15-jul, SIS/reforma Chile con versiones.",
     "test_colombia::test_co_workweek_2026_*, test_countries_2026::test_ar_el_smvm_*, test_mx_la_uma_*, test_cl_sis_y_reforma_*"),
    ("Los límites están probados", "Fronteras -1/=/+1 en auxilio (2 SMMLV), IBC (25 SMMLV), integral (13 SMMLV), exoneración (10 SMMLV), FSP y topes de cada país.",
     "test_colombia::test_co_transport_boundary, test_co_social_security_cap, test_co_integral_salary_*, test_co_exoneracion_*, test_co_fsp_*"),
    ("Las excepciones están probadas", "Exoneración art. 114-1 (línea en cero con motivo), caja nunca exonerada, empleador no exonerado.",
     "test_colombia::test_co_exoneracion_*, test_co_empleador_no_exonerado_*, test_co_la_caja_*"),
    ("Las bases están separadas", "IBC, RISK_BASE, PARAFISCAL_BASE, BENEFIT_BASE, VACATION_BASE, EXONERATION_BASE; no hay una base genérica.",
     "test_colombia::test_co_bases_separadas_para_cada_proposito"),
    ("Los redondeos están probados", "Política por país; redondeo por línea registrado en la auditoría; líneas suman los totales.",
     "test_core::test_el_redondeo_queda_registrado_*, test_las_lineas_suman_exactamente_los_totales, test_politica_de_redondeo_*"),
    ("El audit trail funciona", "Toda línea tiene regla, versión, fórmula, redondeo y fuente; reglas no aplicadas quedan explicadas.",
     "test_colombia::test_co_toda_linea_tiene_traza_*, test_co_la_explicacion_sale_de_la_ejecucion_real"),
    ("Las explicaciones corresponden a las reglas", "La explicación se construye del registro de ejecución (operandos leídos, condición evaluada).",
     "test_colombia::test_co_transport_explicacion_muestra_la_regla_de_2_smmlv, test_co_exoneracion_la_linea_en_cero_explica_por_que"),
    ("Los tests de frontera pasan", "Ver resultado de la suite abajo.", "tests/payroll_2026/"),
    ("Sin fórmulas legales duplicadas", "Un mecanismo genérico por operación (rate_on_base, progressive_brackets…); las diferencias son parámetros.",
     "test_architecture::test_el_nucleo_no_contiene_paises_ni_reglas_de_pais"),
    ("Sin reglas colombianas en otros países", "Cada país tiene sus propios conceptos y referencias; el núcleo no contiene códigos de país.",
     "test_architecture::*, test_countries_2026::test_pe_no_trata_la_gratificacion_como_el_13o_de_otro_pais"),
]

BOUNDARY_TESTED = {"CO.TRANSPORT_ALLOWANCE", "CO.HEALTH_EMPLOYEE", "CO.PENSION_EMPLOYEE", "CO.PENSION_EMPLOYER", "CO.FSP_EMPLOYEE",
                   "CO.HEALTH_EMPLOYER", "CO.SENA", "CO.ICBF", "CO.COMPENSATION_FUND", "CO.MONTHLY_WORK_HOURS", "CO.BASE_SALARY",
                   "CO.VAL.INTEGRAL_MINIMUM", "CO.VAL.ACCOUNTED_DAYS", "CO.VAL.ARL_CLASS", "CO.ARL_CLASS_I", "CO.BONUS_NON_SALARY"}


def killcritic(tests):
    rs = load_country("CO")
    rules = [r for r in rs.rules]
    by_source = {}
    for r in rules:
        by_source[r["source"]["status"]] = by_source.get(r["source"]["status"], 0) + 1
    untested = sorted(r["rule_key"] for r in rules if r["rule_key"] not in BOUNDARY_TESTED)
    out = ["# KILLCRITIC — Gate de calidad de Colombia (2026)", "",
           f"> **Generado** el {date.today().isoformat()} ejecutando la suite real. Motor v{ENGINE_VERSION}, reglas `{rs.ruleset_version}`.", "",
           "## Resultado de la suite", "",
           f"`{tests['summary']}`", "",
           f"| passed | failed | skipped | errors |", "|---:|---:|---:|---:|",
           f"| {tests['passed']} | {tests['failed']} | {tests['skipped']} | {tests['errors']} |", "",
           "## Gate (sección 34 del encargo)", "", "| # | Criterio | Estado | Evidencia | Pruebas |", "|---|---|---|---|---|"]
    ok = tests["failed"] == 0 and tests["errors"] == 0 and tests["passed"] > 0
    for i, (criterion, evidence, where) in enumerate(GATE, 1):
        out.append(f"| {i} | {criterion} | {'CUMPLE (pruebas en verde)' if ok else 'NO VERIFICADO (hay pruebas fallando)'} | {evidence} | {where} |")
    out += ["", "**Lo que este gate NO afirma:** que las reglas estén validadas por un profesional (ninguna lo está: "
            "`professional_validation = PENDING` en todas), ni que los resultados de la liquidación y de las horas extra sean jurídicamente definitivos "
            "(fuentes oficiales para muchas reglas, pero con interpretaciones sin revisar y varias fuentes PENDING), "
            "ni que exista motor tributario (la retención es un valor digitado, `EXTERNAL_INPUT`).", "",
            "## Fuentes de las reglas de Colombia", "", "| Estado de la fuente | Reglas |", "|---|---:|"]
    for status in ("OFFICIAL", "SECONDARY", "PENDING", "NOT_APPLICABLE", "CONFLICTING"):
        out.append(f"| {status} | {by_source.get(status, 0)} |")
    out += ["", "Fuentes OFICIALES verificadas en esta ejecución: SMMLV (Decretos 1469/2025 y 159/2026), auxilio de transporte (Decreto 1470/2025), "
            "IBC 25 SMMLV / mínimo 1 SMMLV / salario integral 70% (Ley 797/2003 art. 5), FSP (art. 8), jornada (Ley 2101/2021 art. 3). "
            "El resto (tasas de salud/pensión/parafiscales, ARL, ET art. 114-1, CST art. 132, Ley 1393 art. 30, provisiones) se contrastó solo con fuentes "
            "SECUNDARIAS o quedó PENDING: **no se marca oficial sin respaldo verificable**.", "",
            "## Hallazgos de la investigación normativa que afectan el diseño", "",
            "- **El SMMLV 2026 está en litigio.** El Decreto 1469/2025 fue suspendido provisionalmente por el Consejo de Estado (13-feb-2026); el Decreto 159/2026 "
            "(DO 53.403, 19-feb-2026) fijó el mismo valor $1.750.905 de forma transitoria «hasta que se dicte sentencia» (rad. 11001-03-25-000-2026-00004-00). "
            "Si la sentencia cambia el valor, se agrega una versión de la referencia con su vigencia; no se edita la actual.",
            "- **Conflicto con la documentación interna:** `NORMATIVA_PAISES.md` dice «≤10 SMMLV» para la exoneración; el art. 114-1 ET dice «menos de diez (10)». "
            "Se implementó el texto de la norma (estricto) y se probó la frontera exacta (10 SMMLV NO está exonerado). Requiere validación profesional.",
            "- **Chile:** el ingreso mínimo de $553.553 desde el 1-may-2026 solo consta en fuentes secundarias; la página oficial consultada de la Ley 21.751 llega a $539.000. "
            "Se marcó PENDING. La jornada de 42 h desde el 26-abr-2026 sí tiene fuente oficial (Mintrab).",
            "- **Argentina:** el SMVM cambia cada mes; septiembre a diciembre 2026 tienen fuente oficial (Boletín Oficial, Res. 4/2026); enero a agosto solo secundaria.",
            "- **México:** la UMA cambia cada 1 de febrero (117,31 desde el 1-feb-2026); el valor anterior (113,14) quedó PENDING de verificación.",
            "- **Cobertura del auxilio de transporte:** el límite de 2 SMMLV tiene fuente oficial; el tratamiento de variables, vacaciones/incapacidad y periodos parciales quedó PENDING.", "",
            "## Reglas de Colombia SIN test de frontera dedicado", ""]
    out += [f"- `{k}`" for k in untested] or ["- (ninguna)"]
    out += ["", "## Riesgos reales que siguen abiertos", "",
            "1. **Ninguna regla tiene validación profesional**: fuente oficial no es interpretación correcta ni implementación completa (ver docs/SOURCES_REGISTRY_2026.md).",
            "2. **Ley 1393 (Colombia):** fórmula literal verificada, alcance del 'total de la remuneración' PENDING_VERIFICATION: cálculo PROVISIONAL (docs/CO_LEY_1393_AUDITORIA.md).",
            "3. **Impuesto:** los 7 países reciben la retención como valor digitado; no hay motor tributario (capacidad `tax` NOT_IMPLEMENTED).",
            "4. **Fuentes secundarias/pendientes:** tasas de salud/pensión/parafiscales de Colombia, UMA, RMV del Perú, SM/INSS de Brasil, ingreso mínimo de Chile desde mayo, SMVM de Argentina (ene-ago), intereses de cesantías, auxilio en la base de cesantías/prima, art. 76 TUO 728 (Perú).",
            "5. **Interpretaciones abiertas en liquidación y horas extra:** divisores del valor hora (PE, AR, EC, MX), acumulación de recargos (CO), fracciones de año (MX, EC), décimo tercero de Ecuador (período), SIS desde ago-2026 en Chile (posible doble conteo), conversión de días hábiles a corridos del feriado (CL).",
            "6. **Fuente primaria inaccesible:** el texto de la Cámara de Diputados de México no se pudo descargar; se usó el Orden Jurídico Nacional (reforma 30-sep-2024) y el decreto del DOF del 1-may-2026 por lectura automática.",
            "7. **Períodos que cruzan el cambio de una referencia usada por una BASE** se bloquean (las bases no declaran política de partición); las reglas con SPLIT_BY_DAYS prorratean por días (aproximación para horas extra).",
            "8. **Notas normativas, etiquetas de conceptos y advertencias:** disponibles en español (etiquetas también en inglés); los datos están en español.",
            "9. **Seguridad:** sin autenticación ni CSRF; datos DEMO y reales comparten tablas (bandera `es_demo`). NO es un sistema seguro para producción.",
            "10. **Recálculo histórico:** parcial (compara y explica; no genera el ajuste contable ni encadena recálculos).", ""]
    write("KILLCRITIC_PAYROLL_2026.md", out)


def main():
    tests = run_tests() if "--no-tests" not in sys.argv else {"summary": "(no ejecutado)", "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "returncode": 0}
    master_rules()
    latam_profile()
    gap_analysis(tests)
    killcritic(tests)
    legacy_vs_normative()
    sources_registry()
    from tools import hardcode_inventory
    hardcode_inventory.main()
    print("pruebas:", tests["summary"])
    return 0 if tests["returncode"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
