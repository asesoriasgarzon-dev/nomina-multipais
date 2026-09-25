"""Adaptador hacia la interfaz heredada de la app (dict de 4 secciones + totales).

Los valores heredados son float (solo para mostrar y exportar, como antes); el
valor exacto y auditable vive en el PayrollRun (Decimal). Nada de reglas aquí:
solo agrupa líneas por sección y por clave de etiqueta."""

import calendar
from datetime import date

from .errors import InputValidationError

SECTIONS = {
    "devengado": "EARNING", "deducciones": "EMPLOYEE_DEDUCTION",
    "aportes_patronales": "EMPLOYER_CONTRIBUTION", "provisiones": "ACCRUAL",
}


def period_bounds(periodo):
    """'AAAA-MM' -> (inicio, fin) del mes calendario, en texto ISO."""
    try:
        year, month = periodo.split("-")
        first = date(int(year), int(month), 1)
    except (ValueError, AttributeError) as exc:
        raise InputValidationError(f"período inválido: {periodo!r} (se espera AAAA-MM)") from exc
    last = date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
    return first.isoformat(), last.isoformat()


def to_legacy_result(run, order=None):
    """order: {seccion: [label_key, ...]} para conservar el orden visual heredado."""
    out = {}
    for section, role in SECTIONS.items():
        grouped = {}
        for line in run.result["lines"]:
            if line["role"] == role and line["label_key"]:
                grouped[line["label_key"]] = grouped.get(line["label_key"], 0) + line["amount"]
        keys = list(grouped)
        if order and section in order:
            keys = [k for k in order[section] if k in grouped] + [k for k in keys if k not in order[section]]
        out[section] = {k: float(grouped[k]) for k in keys}
    totals = run.result["totals"]
    for key in ("total_devengado", "total_deducciones", "neto_pagado", "total_aportes_patronales",
                "total_provisiones", "costo_empleador"):
        out[key] = float(totals[key])
    out["motor"] = "normativo"
    out["run_status"] = run.status
    out["warnings"] = [w["message"] if isinstance(w, dict) else str(w) for w in run.warnings]
    return out


# ------------------------------------------------------------------ liquidación (terminación)
# Vocabulario del formulario heredado -> códigos del motor. Cada país puede corregir el mapa en su manifiesto
# (manifest.termination.form_cause_map): p. ej. en Chile "sin justa causa" del formulario es la causal de
# necesidades de la empresa (art. 161).
DEFAULT_CAUSE_MAP = {"renuncia": "RESIGNATION", "justa_causa": "DISMISSAL_WITH_CAUSE",
                     "sin_justa_causa": "DISMISSAL_WITHOUT_CAUSE", "mutuo_acuerdo": "MUTUAL_AGREEMENT",
                     "despido_indirecto": "INDIRECT_DISMISSAL", "necesidades_empresa": "DISMISSAL_BUSINESS_NEEDS",
                     "desahucio": "NOTICE_TERMINATION", "vencimiento_plazo": "FIXED_TERM_EXPIRY",
                     "terminacion_obra": "WORK_COMPLETION", "periodo_prueba": "PROBATION_END",
                     "jubilacion": "RETIREMENT", "muerte": "DEATH"}
DEFAULT_CONTRACT_MAP = {"indefinido": "INDEFINITE", "fijo": "FIXED_TERM", "obra_labor": "WORK_COMPLETION"}


def _text(value, default="0"):
    if value in (None, ""):
        return default
    return str(value).strip()


def termination_maps(manifest):
    spec = manifest.get("termination") or {}
    causes = {**DEFAULT_CAUSE_MAP, **spec.get("form_cause_map", {})}
    contracts = {**DEFAULT_CONTRACT_MAP, **spec.get("form_contract_map", {})}
    return causes, contracts


def supported_form_options(manifest):
    """Opciones del formulario (vocabulario heredado) que el país realmente soporta, leídas del manifiesto."""
    spec = manifest.get("termination") or {}
    causes, contracts = termination_maps(manifest)
    ok_causes = [k for k, v in causes.items() if spec.get("causes") is None or v in spec["causes"]]
    ok_contracts = [k for k, v in contracts.items() if spec.get("contract_types") is None or v in spec["contract_types"]]
    return ok_causes, ok_contracts


def termination_payload(country, manifest, empleado, datos):
    """Entrada de una corrida TERMINATION a partir del formulario de liquidación."""
    from datetime import timedelta
    causes, contracts = termination_maps(manifest)
    cause = causes.get(datos.get("tipo_terminacion"))
    contract = contracts.get(datos.get("tipo_contrato"))
    if cause is None or contract is None:
        raise InputValidationError("tipo de contrato o de terminación desconocido",
                                   details=[f"tipo_terminacion={datos.get('tipo_terminacion')!r}",
                                            f"tipo_contrato={datos.get('tipo_contrato')!r}"])
    salary = _text(datos.get("salario_base"), "") or _text(empleado.get("salario_contrato"), "0")
    employment = {"hire_date": _text(datos.get("fecha_ingreso"), ""), "monthly_salary": salary, "contract_type": contract}
    end = _text(datos.get("fecha_retiro"), "")
    remaining = _text(datos.get("dias_faltantes_contrato"))
    try:
        if contract != "INDEFINITE" and float(remaining) > 0 and end:
            employment["contract_end_date"] = (date.fromisoformat(end) + timedelta(days=int(float(remaining)))).isoformat()
    except ValueError as exc:
        raise InputValidationError("fecha de retiro o días faltantes inválidos") from exc
    payload = {
        "country": country, "jurisdictions": ["NATIONAL"], "run_type": "TERMINATION",
        "employee": {"id": _text(empleado.get("identificacion"), ""), "name": _text(empleado.get("nombre"), "")},
        "employment": employment, "termination_date": end, "pay_date": end,
        # el formulario tiene un solo campo de salarios pendientes: el usuario controla el salario del mes de terminación
        # (por eso no se calcula aparte: evitaría contarlo dos veces)
        "termination": {"cause": cause, "final_month_paid": True},
        "amounts": {"unpaid_salary": _text(datos.get("salarios_pendientes"))},
        "vacation_history": {"days_pending_prior": _text(datos.get("dias_vacaciones_pendientes"))},
    }
    return payload


def to_liquidation_result(run):
    """Resultado de una TERMINATION en la forma que usa la pantalla de liquidación: líneas con etiqueta,
    prestaciones, indemnización y total (neto = devengado − deducciones; los aportes patronales no se suman)."""
    lines, benefits, indemnity = [], 0, 0
    for line in run.result["lines"]:
        if line["role"] == "INFO":
            continue
        entry = {"concept": line["concept"], "label": line.get("label"), "label_key": line.get("label_key"),
                 "role": line["role"], "category": line.get("category"), "amount": float(line["amount"]),
                 "line_id": line["line_id"]}
        lines.append(entry)
        sign = -1 if line["role"] == "EMPLOYEE_DEDUCTION" else 1
        if line["role"] in ("EARNING", "EMPLOYEE_DEDUCTION"):
            if line.get("category") == "TERMINATION_INDEMNITY":
                indemnity += sign * line["amount"]
            else:
                benefits += sign * line["amount"]
    from datetime import date as _date
    hire = _date.fromisoformat(run.input_snapshot["payload"]["employment"]["hire_date"])
    from .temporal import service_time
    st = service_time(hire, run.anchor_dates["termination_date"])
    totals = run.result["totals"]
    return {
        "motor": "normativo", "run_type": "TERMINATION", "run_status": run.status,
        "lineas": lines,
        "total_prestaciones": float(benefits), "indemnizacion": float(indemnity),
        "aplica_indemnizacion": any(l["category"] == "TERMINATION_INDEMNITY" and l["amount"] != 0 for l in lines),
        "total_liquidacion": float(totals["neto_pagado"]),
        "costo_empleador_aportes": float(totals["total_aportes_patronales"]),
        "antiguedad_anos": round(float(st.years_decimal()), 2), "antiguedad_texto": st.as_text(),
        "warnings": [w["message"] if isinstance(w, dict) else str(w) for w in run.warnings],
    }
