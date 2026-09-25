"""Bases Engine. Una base NO es una lista universal: cada jurisdicción declara las
suyas (IBC, SBC, salário-de-contribuição, wage bases...). El tratamiento de un
concepto frente a cada base (INCLUDE / EXCLUDE / INCLUDE_WITH_CAP / SPECIAL_RULE) se
declara en los datos y depende de país, vigencia, régimen y condiciones. El motor
solo determina la base y deja constancia de por qué cada concepto entró o no."""

from decimal import Decimal

from .conditions import applies_to as _applies_to_filter, evaluate
from .dates import in_effect
from .errors import ConflictingRulesError
from .money import D, fmt


def select_treatment(concept, base_code, ctx, payload):
    """Elige el tratamiento (concepto -> base) vigente y aplicable. Devuelve (tratamiento|None, descartados)."""
    candidates, discarded = [], []
    for tr in concept.get("treatments", []):
        if tr["base"] != base_code:
            continue
        if "effective" in tr and not in_effect(tr["effective"], ctx.on_date):
            discarded.append({"treatment": tr, "reason": "FUERA_DE_VIGENCIA"})
            continue
        if not _applies_to_filter(tr.get("applies_to"), payload):
            discarded.append({"treatment": tr, "reason": "NO_APLICA_AL_TRABAJADOR"})
            continue
        ok, rec = evaluate(tr.get("conditions"), ctx)
        if not ok:
            discarded.append({"treatment": tr, "reason": "CONDICION_FALSA", "evaluation": rec})
            continue
        candidates.append(tr)
    if not candidates:
        return None, discarded
    candidates.sort(key=lambda t: -int(t.get("priority", 0)))
    if len(candidates) > 1 and int(candidates[0].get("priority", 0)) == int(candidates[1].get("priority", 0)):
        raise ConflictingRulesError(
            f"tratamientos en conflicto para {concept['concept']} → {base_code}",
            details=[f"{t['mode']} (prioridad {t.get('priority', 0)})" for t in candidates])
    return candidates[0], discarded + [{"treatment": t, "reason": "SUPERADO_POR_PRIORIDAD"} for t in candidates[1:]]


def compute_base(base_def, concepts, line_records, ctx, payload):
    """line_records: lista de líneas ya emitidas (dicts con concept, amount Decimal, line_id).
    Devuelve el BaseValue y su detalle de contribuciones/exclusiones."""
    total = Decimal(0)
    contributions, exclusions = [], []
    pending_special = []
    for line in line_records:
        concept = concepts.get(line["concept"])
        if concept is None:
            continue
        treatment, discarded = select_treatment(concept, base_def["base"], ctx, payload)
        if treatment is None:
            exclusions.append({"line_id": line["line_id"], "concept": line["concept"], "amount": fmt(line["amount"]),
                               "mode": "EXCLUDE", "reason": "SIN_TRATAMIENTO_DECLARADO",
                               "discarded": [d["reason"] for d in discarded]})
            continue
        mode = treatment["mode"]
        record = {"line_id": line["line_id"], "concept": line["concept"], "amount": fmt(line["amount"]),
                  "mode": mode, "note": treatment.get("note"),
                  "status": treatment.get("status", "IMPLEMENTED")}
        if mode == "EXCLUDE":
            record["reason"] = treatment.get("reason", "EXCLUIDO_POR_TRATAMIENTO")
            exclusions.append(record)
        elif mode in ("INCLUDE", "INCLUDE_WITH_CAP"):
            fraction = D(treatment.get("fraction", 1))
            amount = line["amount"] * fraction
            if mode == "INCLUDE_WITH_CAP":
                cap = ctx.num(treatment["cap"])
                if amount > cap:
                    record["cap_applied"] = fmt(cap)
                    amount = cap
            record.update({"fraction": fmt(fraction), "contributed": fmt(amount)})
            contributions.append(record)
            total += amount
        else:  # SPECIAL_RULE: se resuelve después de conocer todas las líneas
            pending_special.append((line, treatment, record))

    for line, treatment, record in pending_special:
        special = treatment["special"]
        if special != "SHARE_EXCESS":
            raise ConflictingRulesError(f"regla especial desconocida: {special}")
        params = treatment.get("params", {})
        share = D(params["share"])
        group = params["non_salary_concepts"]
        total_concepts = params["total_of"]
        all_lines = {}
        for l in line_records:
            all_lines[l["concept"]] = all_lines.get(l["concept"], Decimal(0)) + l["amount"]
        non_salary = sum((all_lines.get(c, Decimal(0)) for c in group), Decimal(0))
        remuneration = sum((all_lines.get(c, Decimal(0)) for c in total_concepts), Decimal(0))
        limit = share * remuneration
        excess_total = max(non_salary - limit, Decimal(0))
        first_of_group = next((c for c in group if c in all_lines), None)
        amount = excess_total if line["concept"] == first_of_group else Decimal(0)
        record.update({"special": special, "share": fmt(share), "non_salary_total": fmt(non_salary),
                       "total_remuneration": fmt(remuneration), "limit": fmt(limit),
                       "excess_included": fmt(amount), "contributed": fmt(amount)})
        (contributions if amount > 0 else exclusions).append(record)
        total += amount

    for concept_code in base_def.get("subtract_lines", []):
        subtract = sum((l["amount"] for l in line_records if l["concept"] == concept_code), Decimal(0))
        if subtract:
            contributions.append({"line_id": None, "concept": concept_code, "amount": fmt(subtract),
                                  "mode": "SUBTRACT", "contributed": fmt(-subtract)})
            total -= subtract

    raw_total = total
    limits, warnings = {}, []
    limit_spec = base_def.get("limits") or {}
    cap_applied = False
    if "maximum" in limit_spec:
        spec = limit_spec["maximum"]
        cap = ctx.num(spec["value"])
        if "scale_by" in spec:
            cap = cap * ctx.num(spec["scale_by"])
        limits["maximum"] = fmt(cap)
        if total > cap and spec.get("enforcement", "ENFORCE") == "ENFORCE":
            total, cap_applied = cap, True
        elif total > cap:
            warnings.append(f"BASE_SOBRE_MAXIMO_NO_APLICADO: {fmt(total)} > {fmt(cap)}")
    if "minimum" in limit_spec:
        spec = limit_spec["minimum"]
        floor = ctx.num(spec["value"])
        if "scale_by" in spec:
            floor = floor * ctx.num(spec["scale_by"])
        limits["minimum"] = fmt(floor)
        if total < floor:
            if spec.get("enforcement", "ENFORCE") == "ENFORCE":
                total = floor
            else:
                warnings.append(f"BASE_BAJO_MINIMO_SIN_APLICAR ({spec.get('status', 'PENDING_VERIFICATION')}): "
                                f"{fmt(total)} < {fmt(floor)}")
    return {
        "base": base_def["base"], "value": total, "raw_sum": raw_total, "limits": limits,
        "cap_applied": cap_applied, "contributions": contributions, "exclusions": exclusions,
        "warnings": warnings, "description": base_def.get("description"),
        "source": base_def.get("source"),
    }
