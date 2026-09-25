"""Paquete normativo SINTÉTICO 'ZZ' para probar que el núcleo no está diseñado solo
para Colombia. No es un país del producto ni vive en config/payroll: solo existe en
las pruebas. Las cifras son ficticias y no representan ninguna norma real."""

import copy

from payroll_engine.loader import RuleSetData

SRC = {"status": "NOT_APPLICABLE"}
VER = {"interpretation_status": "UNREVIEWED", "professional_validation": "PENDING"}


def rule(rule_id, key, concept, mechanism, params, *, kind="EMPLOYEE_DEDUCTION", jurisdiction="NATIONAL",
         start="2026-01-01", end=None, anchor="period_end", priority=100, straddle="USE_ANCHOR",
         conditions=None, exceptions=None, impl="IMPLEMENTED", applies_to=None, version="1", rounding="currency"):
    doc = {
        "rule_id": rule_id, "rule_key": key, "version": version, "country": "ZZ", "jurisdiction": jurisdiction,
        "concept": concept, "category": "SYNTHETIC", "kind": kind, "effective": {"from": start, "to": end},
        "anchor": anchor, "straddle_policy": straddle, "priority": priority,
        "calculation": {"mechanism": mechanism, "params": params, "rounding": rounding},
        "source": SRC, "verification": VER, "implementation_status": impl,
    }
    if conditions:
        doc["conditions"] = conditions
    if exceptions:
        doc["exceptions"] = exceptions
    if applies_to:
        doc["applies_to"] = applies_to
    return doc


def reference(ref_id, code, value, *, jurisdiction="NATIONAL", start="2026-01-01", end=None):
    return {"ref_id": ref_id, "code": code, "country": "ZZ", "jurisdiction": jurisdiction, "unit": "ZZC",
            "value": value, "effective": {"from": start, "to": end}, "source": SRC, "verification": VER}


def concept(code, role, treatments=()):
    return {"concept": code, "role": role, "label_key": code.lower(), "source": SRC, "verification": VER,
            "treatments": [dict(t) for t in treatments]}


def base(code, *, limits=None, subtract=None):
    doc = {"base": code, "country": "ZZ", "description": code, "effective": {"from": "2026-01-01", "to": None},
           "source": SRC, "verification": VER}
    if limits:
        doc["limits"] = limits
    if subtract:
        doc["subtract_lines"] = subtract
    return doc


def manifest():
    return {"country": "ZZ", "year": 2026, "ruleset_version": "ZZ-TEST-1", "jurisdiction_default": "NATIONAL",
            "currency": "ZZC", "local_payroll_engine": True, "consolidation_context": False,
            "execution_path": "NEW_ENGINE", "normative_date": "2026-01-01",
            "capabilities": {"payroll_monthly": {"status": "PARTIALLY_IMPLEMENTED"}}}


ROUNDING = {"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP"}


def zz_docs():
    salary_input = {"amount": {"input": "employment.monthly_salary"}}
    return {
        "manifest": manifest(),
        "references": [
            reference("ZZ.MIN.NAT", "MIN_WAGE", "1000"),
            reference("ZZ.CAP.NAT", "SS_CAP", "5000"),
            reference("ZZ.CAP.A", "SS_CAP", "8000", jurisdiction="STATE_A"),
        ],
        "concepts": [
            concept("SALARY", "EARNING", [{"base": "SS_BASE", "mode": "INCLUDE"}, {"base": "TAX_BASE", "mode": "INCLUDE"}]),
            # entra a seguridad social pero NO al impuesto (caso C)
            concept("BONUS", "EARNING", [{"base": "SS_BASE", "mode": "INCLUDE"}, {"base": "TAX_BASE", "mode": "EXCLUDE"}]),
            concept("TRANSPORT", "EARNING"),
            concept("SS_EMP", "EMPLOYEE_DEDUCTION"),
            concept("TAX", "EMPLOYEE_DEDUCTION"),
            concept("STATE_LEVY", "EMPLOYER_CONTRIBUTION"),
            concept("INCOME_WITHHOLDING", "EMPLOYEE_DEDUCTION"),
        ],
        "bases": [
            base("SS_BASE", limits={"maximum": {"value": {"reference": {"code": "SS_CAP"}}, "enforcement": "ENFORCE"}}),
            base("TAX_BASE", subtract=["SS_EMP"]),          # una base depende de otra (caso D)
        ],
        "rules": [
            rule("ZZ.SALARY.1", "ZZ.SALARY", "SALARY", "pass_through", salary_input, kind="EARNING"),
            rule("ZZ.BONUS.1", "ZZ.BONUS", "BONUS", "pass_through",
                 {"amount": {"input": "amounts.BONUS", "default": "0"}}, kind="EARNING"),
            # tasa que cambia el 2026-07-01 (caso B)
            rule("ZZ.SS_EMP.1", "ZZ.SS_EMP", "SS_EMP", "rate_on_base", {"base": "SS_BASE", "rate": "0.04"},
                 end="2026-06-30", version="1"),
            rule("ZZ.SS_EMP.2", "ZZ.SS_EMP", "SS_EMP", "rate_on_base", {"base": "SS_BASE", "rate": "0.05"},
                 start="2026-07-01", version="2"),
            rule("ZZ.TAX.1", "ZZ.TAX", "TAX", "rate_on_base", {"base": "TAX_BASE", "rate": "0.10"}),
            # dos jurisdicciones con distinta tasa (caso A)
            rule("ZZ.LEVY.A", "ZZ.STATE_LEVY", "STATE_LEVY", "rate_on_base", {"base": "SS_BASE", "rate": "0.02"},
                 kind="EMPLOYER_CONTRIBUTION", jurisdiction="STATE_A"),
            rule("ZZ.LEVY.B", "ZZ.STATE_LEVY", "STATE_LEVY", "rate_on_base", {"base": "SS_BASE", "rate": "0.03"},
                 kind="EMPLOYER_CONTRIBUTION", jurisdiction="STATE_B"),
            # regla que no aplica según una condición (caso F)
            rule("ZZ.TRANSPORT.1", "ZZ.TRANSPORT", "TRANSPORT", "fixed_amount_prorated", {"amount": "100"},
                 kind="EARNING",
                 conditions={"left": {"input": "employment.monthly_salary"}, "op": "<=",
                             "right": {"reference": {"code": "MIN_WAGE", "multiple": "2"}}}),
            # regla NOT_IMPLEMENTED (caso G)
            rule("ZZ.WITHHOLDING.1", "ZZ.INCOME_WITHHOLDING", "INCOME_WITHHOLDING", "pass_through",
                 {"amount": "0"}, impl="NOT_IMPLEMENTED"),
        ],
        "rounding": ROUNDING,
    }


def zz_ruleset(mutate=None, **kwargs):
    docs = copy.deepcopy(zz_docs())
    if mutate:
        mutate(docs)
    return RuleSetData.from_documents(docs, **kwargs)


def payload(salary="3000", bonus="0", period=("2026-09-01", "2026-09-30"), chain=("NATIONAL",), **extra):
    data = {
        "country": "ZZ", "jurisdictions": list(chain), "period": {"start": period[0], "end": period[1]},
        "employee": {"id": "E1"}, "employment": {"monthly_salary": salary},
        "amounts": {"BONUS": bonus},
    }
    data.update(extra)
    return data
