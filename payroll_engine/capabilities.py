"""Capability Manifest: estado REAL de cada contexto, derivado de manifest.json y
del conteo de reglas — nunca de que exista un archivo con una clase. La UI lee de
aquí; no tiene valores legales ni estados escritos a mano."""

from .loader import DEFAULT_ROOT, available_countries, load_country

# Componentes críticos evaluados para todos los contextos, en este orden. Un país solo puede ser "implementado"
# si TODOS son IMPLEMENTED (y, además, hay validación profesional humana de sus reglas).
COMPONENTS = ("monthly_payroll", "overtime", "surcharges", "vacation", "social_security", "benefits",
              "termination", "tax", "audit", "historical_recalculation")
COMPONENT_SOURCE = {
    "monthly_payroll": "payroll_monthly", "overtime": "overtime_and_premiums", "surcharges": "surcharges",
    "vacation": "vacation", "social_security": "social_security", "benefits": "benefit_accruals",
    "termination": "termination", "tax": "income_tax_withholding",
}

STATE_BY_CAPABILITY = {
    "IMPLEMENTED": "implementado",
    "PARTIALLY_IMPLEMENTED": "parcial",
    "INCOMPLETE": "parcial",
    "PENDING_VALIDATION": "pendiente_validacion",
    "NOT_IMPLEMENTED": "no_implementado",
    "NOT_APPLICABLE": "no_aplica",
}


def overall_state(manifest):
    """Estado agregado del contexto para mostrar en la UI."""
    if manifest.get("consolidation_context") and not manifest.get("local_payroll_engine"):
        return "consolidacion"
    main = (manifest.get("capabilities") or {}).get("payroll_monthly", {}).get("status", "NOT_IMPLEMENTED")
    return STATE_BY_CAPABILITY.get(main, "no_implementado")


def components(manifest):
    """Matriz estándar de componentes críticos, derivada del manifiesto. Lo que un país no declara queda
    NOT_IMPLEMENTED (no se presume); 'audit' e 'historical_recalculation' dependen de si el país tiene motor local."""
    declared = manifest.get("capabilities") or {}
    local = bool(manifest.get("local_payroll_engine"))
    consolidation = bool(manifest.get("consolidation_context"))
    out = {}
    for name in COMPONENTS:
        if name in COMPONENT_SOURCE:
            cap = declared.get(COMPONENT_SOURCE[name])
            if cap is None:
                status = "NOT_APPLICABLE" if (consolidation and not local) else "NOT_IMPLEMENTED"
                out[name] = {"status": status, "note": "Sin capacidad declarada en el manifiesto."}
            else:
                out[name] = {"status": cap["status"], "note": cap.get("note", "")}
        elif name == "audit":
            if local:
                out[name] = {"status": "IMPLEMENTED",
                             "note": "Traza de ejecución, explicación, snapshot de entrada y normativo, y hashes; sin validación profesional."}
            else:
                out[name] = {"status": "NOT_APPLICABLE" if consolidation else "NOT_IMPLEMENTED",
                             "note": "Sin motor de nómina local: no hay corridas que auditar."}
        else:  # historical_recalculation
            if local:
                out[name] = {"status": "PARTIALLY_IMPLEMENTED",
                             "note": "reproduce() recalcula una corrida guardada con SU snapshot y compara hashes; historical_recalculation() la "
                                     "recalcula con las reglas actuales y compara línea a línea (causa: versión de regla/referencias). El ajuste "
                                     "contable (pagar la diferencia) y encadenar recálculos NO están implementados."}
            else:
                out[name] = {"status": "NOT_APPLICABLE" if consolidation else "NOT_IMPLEMENTED",
                             "note": "Sin motor de nómina local."}
    return out


def complete_engine(manifest):
    """True solo si todos los componentes críticos son IMPLEMENTED. Con las reglas actuales ningún país lo es."""
    return all(c["status"] == "IMPLEMENTED" for c in components(manifest).values())


def coverage(ruleset):
    rules = [r for r in ruleset.rules if r["kind"] != "VALIDATION"]
    by_impl = {"IMPLEMENTED": 0, "PARTIAL": 0, "NOT_IMPLEMENTED": 0}
    pending_professional = 0
    not_official = 0
    for rule in rules:
        by_impl[rule["implementation_status"]] += 1
        if (rule.get("verification") or {}).get("professional_validation") != "VALIDATED":
            pending_professional += 1
        if (rule.get("source") or {}).get("status") != "OFFICIAL":
            not_official += 1
    caps = ruleset.manifest.get("capabilities", {})
    cap_counts = {}
    for cap in caps.values():
        cap_counts[cap["status"]] = cap_counts.get(cap["status"], 0) + 1
    return {
        "rules_total": len(rules), "rules_implemented": by_impl["IMPLEMENTED"],
        "rules_partial": by_impl["PARTIAL"], "rules_not_implemented": by_impl["NOT_IMPLEMENTED"],
        "rules_pending_professional_validation": pending_professional,
        "rules_without_official_source": not_official,
        "capabilities": cap_counts, "capabilities_total": len(caps),
        "references": len(ruleset.references),
    }


def describe(country, root=DEFAULT_ROOT):
    """Todo lo que la UI necesita mostrar de un contexto, leído de los datos."""
    ruleset = load_country(country, root)
    manifest = ruleset.manifest
    return {
        "country": country, "state": overall_state(manifest),
        "normative_date": manifest.get("normative_date"), "ruleset_version": manifest.get("ruleset_version"),
        "execution_path": manifest.get("execution_path"),
        "local_payroll_engine": manifest.get("local_payroll_engine"),
        "consolidation_context": manifest.get("consolidation_context"),
        "capabilities": manifest.get("capabilities", {}), "known_gaps": manifest.get("known_gaps", []),
        "coverage": coverage(ruleset), "components": components(manifest),
        "complete_engine": complete_engine(manifest),
    }


def describe_all(root=DEFAULT_ROOT):
    return {c: describe(c, root) for c in available_countries(root)}
