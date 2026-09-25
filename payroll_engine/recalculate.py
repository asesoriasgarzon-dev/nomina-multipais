"""Recálculo histórico: recalcula una corrida GUARDADA con las reglas ACTUALES (o con otro snapshot) y explica qué cambió.

No corrige ni paga nada: entrega el resultado nuevo (run_type HISTORICAL_RECALCULATION, ligado a la corrida original) y una
comparación línea a línea con la causa de cada diferencia (versión de la regla, referencias usadas, hash normativo). El ajuste
contable (pagar la diferencia) es una decisión humana y NO se automatiza."""

import copy
from decimal import Decimal

from .errors import InputValidationError
from .loader import RuleSetData
from .money import D
from .run import PayrollEngine


def _lines(run_like):
    result = run_like["result"] if isinstance(run_like, dict) else run_like.result
    out = {}
    for line in result["lines"]:
        if line["role"] == "INFO":
            continue
        out[line["concept"]] = line
    return out


def _rule_of(run_like, concept):
    lines = run_like["trace"]["lines"] if isinstance(run_like, dict) else run_like.trace["lines"]
    for line in lines:
        if line["concept"] == concept:
            return {"rule_id": line["rule_id"], "version": line["rule_version"]}
    return None


def diff_runs(original, recalculated):
    """original: run guardado (dict) · recalculated: PayrollRun. Devuelve las diferencias por concepto."""
    a, b = _lines(original), _lines(recalculated)
    rows = []
    for concept in sorted(set(a) | set(b)):
        before = D(a[concept]["amount"]) if concept in a else None
        after = D(b[concept]["amount"]) if concept in b else None
        if before == after:
            continue
        rule_before, rule_after = _rule_of(original, concept), _rule_of(recalculated, concept)
        rows.append({
            "concept": concept, "before": None if before is None else str(before), "after": None if after is None else str(after),
            "difference": str((after or Decimal(0)) - (before or Decimal(0))),
            "kind": "ADDED" if before is None else ("REMOVED" if after is None else "CHANGED"),
            "rule_before": rule_before, "rule_after": rule_after,
            "rule_changed": rule_before != rule_after,
        })
    orig_norm = (original["normative_snapshot"] if isinstance(original, dict) else original.normative_snapshot)
    new_norm = recalculated.normative_snapshot
    return {
        "same_normative_content": orig_norm["content_hash"] == new_norm["content_hash"],
        "original_ruleset_version": orig_norm["ruleset_version"], "new_ruleset_version": new_norm["ruleset_version"],
        "references_original": sorted(orig_norm.get("references_used", [])), "references_new": sorted(new_norm.get("references_used", [])),
        "lines_changed": rows,
        "total_difference": str(sum((D(r["difference"]) for r in rows), Decimal(0))),
    }


def historical_recalculation(stored_run, *, ruleset=None, root=None, calculation_timestamp=None):
    """Recalcula `stored_run` (dict de un PayrollRun guardado) con `ruleset` (por defecto, las reglas actuales del país).

    Devuelve {"run": PayrollRun nuevo, "comparison": diff}. La entrada es EXACTAMENTE la original (input snapshot): solo cambia la
    norma. Si la corrida original ya era de tipo ADJUSTMENT/HISTORICAL_RECALCULATION se rechaza (no se encadenan recálculos)."""
    if stored_run.get("run_type") in ("ADJUSTMENT", "HISTORICAL_RECALCULATION"):
        raise InputValidationError("no se recalcula una corrida que ya es un ajuste o un recálculo: use la corrida original")
    payload = copy.deepcopy(stored_run["input_snapshot"]["payload"])
    payload["base_run_type"] = payload.get("base_run_type") or stored_run.get("run_type", "REGULAR")   # proceso que se reprocesa
    payload["run_type"] = "HISTORICAL_RECALCULATION"
    payload["original_run_uid"] = stored_run["run_id"]
    engine = PayrollEngine(root=root)
    new_run = engine.run(payload, ruleset=ruleset, calculation_timestamp=calculation_timestamp)
    return {"run": new_run, "comparison": diff_runs(stored_run, new_run)}


def recalculate_with_documents(stored_run, documents, **kwargs):
    """Recálculo con un snapshot normativo explícito (p. ej. para simular 'qué habría dado con las reglas de otra fecha')."""
    return historical_recalculation(stored_run, ruleset=RuleSetData.from_documents(documents), **kwargs)
