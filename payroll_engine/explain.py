"""Explanation Engine. La explicación se CONSTRUYE del registro de ejecución real
(línea + base + regla + operandos leídos), nunca se redacta aparte. Cada campo
proviene de lo que el motor efectivamente hizo."""

from .audit import jsonable
from .money import fmt

LABELS_ES = {
    "country": "País", "jurisdiction": "Jurisdicción", "calculation_date": "Fecha de cálculo",
    "anchor_date": "Fecha ancla", "concept": "Concepto", "rule": "Regla utilizada", "base": "Base utilizada",
    "base_value": "Valor de la base", "formula": "Fórmula", "rate": "Tasa", "minimum": "Mínimo",
    "maximum": "Máximo", "cap": "Tope", "conditions": "Condiciones", "exceptions": "Excepciones",
    "result": "Resultado", "legal_source": "Norma / fuente", "rule_version": "Versión de la regla",
    "rounding": "Redondeo",
}


def _rate_from(details):
    for key in ("rate", "factor"):
        if key in details and details[key] not in (None, "1"):
            return details[key]
    return None


def explain_line(run_dict, line_id):
    """run_dict: PayrollRun.to_dict(). Devuelve la explicación estructurada de una línea."""
    trace_line = next((l for l in run_dict["trace"]["lines"] if l["line_id"] == line_id), None)
    if trace_line is None:
        raise KeyError(f"la corrida no tiene la línea {line_id}")
    details = trace_line.get("details") or {}
    base_ref = trace_line.get("base_ref")
    base_trace = None
    if base_ref:
        base_trace = next((b for b in run_dict["trace"]["bases"] if b["base"] == base_ref["code"]), None)
    limits = (base_ref or {}).get("limits", {})
    thresholds = {k: details[k] for k in ("threshold", "lookup_value", "bracket", "divisor", "days") if k in details}
    source = trace_line.get("source") or {}
    explanation = {
        "country": run_dict["country"],
        "jurisdiction": trace_line["jurisdiction"],
        "period": run_dict["period"],
        "anchor_date": next((s["on_date"] for s in trace_line.get("segments", [])), None),
        "calculation_date": run_dict["calculation_timestamp"],
        "concept": trace_line["concept"],
        "result": trace_line["amount"],
        "currency": run_dict["result"]["currency"],
        "rule": {
            "rule_id": trace_line["rule_id"], "rule_key": trace_line["rule_key"],
            "version": trace_line["rule_version"], "category": trace_line["category"],
            "effective_from": trace_line["effective"]["from"], "effective_to": trace_line["effective"].get("to"),
            "implementation_status": trace_line["implementation_status"],
        },
        "base": None if not base_ref else {
            "code": base_ref["code"], "value": base_ref["value"], "raw_sum": base_ref["raw_sum"],
            "cap_applied": base_ref["cap_applied"],
            "contributions": (base_trace or {}).get("contributions", []),
            "exclusions": (base_trace or {}).get("exclusions", []),
        },
        "formula": trace_line["formula"],
        "mechanism": trace_line["mechanism"],
        "rate": _rate_from(details),
        "minimum": limits.get("minimum"),
        "maximum": limits.get("maximum"),
        "cap": limits.get("maximum") if (base_ref or {}).get("cap_applied") else None,
        "thresholds": thresholds,
        "conditions": trace_line.get("conditions"),
        "exceptions": trace_line.get("exceptions"),
        "operands": trace_line.get("operands"),
        "rounding": trace_line.get("rounding"),
        "legal_source": {
            "status": source.get("status"), "authority": source.get("authority"),
            "legal_reference": source.get("legal_reference"), "official_url": source.get("official_url"),
            "verified_at": source.get("verified_at"), "note": source.get("note"),
        },
        "verification": trace_line.get("verification"),
        "segments": trace_line.get("segments"),
    }
    return jsonable(explanation)


def render_text(explanation, labels=LABELS_ES):
    """Texto legible generado ÚNICAMENTE con campos de la explicación estructurada."""
    e = explanation
    lines = [
        f"{labels['concept']}: {e['concept']} = {e['result']} {e['currency']}",
        f"{labels['country']}: {e['country']} · {labels['jurisdiction']}: {e['jurisdiction']} · "
        f"{labels['anchor_date']}: {e['anchor_date']}",
        f"{labels['rule']}: {e['rule']['rule_id']} (v{e['rule']['version']}, vigente desde {e['rule']['effective_from']}"
        + (f" hasta {e['rule']['effective_to']}" if e['rule']['effective_to'] else "") + ")",
        f"{labels['formula']}: {e['formula']}",
    ]
    if e["base"]:
        lines.append(f"{labels['base']}: {e['base']['code']} = {e['base']['value']}"
                     + (f" (limitada al tope {e['maximum']})" if e["cap"] else ""))
    if e["rate"]:
        lines.append(f"{labels['rate']}: {e['rate']}")
    if e["minimum"]:
        lines.append(f"{labels['minimum']}: {e['minimum']}")
    if e["maximum"]:
        lines.append(f"{labels['maximum']}: {e['maximum']}")
    hit = [x for x in (e["exceptions"] or []) if x.get("result")]
    if hit:
        lines.append(f"{labels['exceptions']} aplicadas: " + "; ".join(str(x.get("reason")) for x in hit))
    rounding = e.get("rounding") or {}
    if rounding.get("applied"):
        lines.append(f"{labels['rounding']}: {rounding['mode']} a {rounding['precision']} decimales "
                     f"({rounding['before']} → {rounding['after']})")
    src = e["legal_source"]
    if src.get("status") == "NOT_APPLICABLE":
        lines.append(f"{labels['legal_source']}: {src.get('note') or 'dato de entrada'} [NOT_APPLICABLE]")
    else:
        lines.append(f"{labels['legal_source']}: {src.get('legal_reference') or 'PENDING_VERIFICATION'} "
                     f"[{src.get('status')}] {src.get('official_url') or ''}".rstrip())
    return "\n".join(lines)


def explain_evaluation(run_dict, rule_id):
    """Explica por qué una regla NO produjo línea (no aplicó / excepción): sale del registro
    de evaluaciones real, con las condiciones y operandos que se evaluaron."""
    records = [e for e in run_dict["trace"]["evaluations"] if e["rule_id"] == rule_id]
    if not records:
        discarded = [d for d in run_dict["trace"]["discarded_rules"] if d["rule_id"] == rule_id]
        if discarded:
            return {"rule_id": rule_id, "outcome": "DESCARTADA", "reason": discarded[0]["reason"], "detail": discarded[0]}
        raise KeyError(f"la corrida no evaluó la regla {rule_id}")
    return {"rule_id": rule_id, "evaluations": records}
