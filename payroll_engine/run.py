"""Payroll Run: orquesta el pipeline normativo.

  ENTRADA → VALIDACIÓN → RESOLUCIÓN DE REGLAS → GRAFO → BASES/CÁLCULO → REDONDEO
  → RESULTADO → EXPLICACIÓN → AUDITORÍA → SNAPSHOT

El núcleo no conoce ninguna regla de país: todo sale de los datos normativos
(RuleSetData). Una corrida = INPUT SNAPSHOT + NORMATIVE SNAPSHOT + ENGINE VERSION,
lo que la hace reproducible aunque las reglas cambien después."""

import copy
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, localcontext

from . import ENGINE_VERSION
from .audit import AuditTrail, jsonable, trace_hash
from .bases import compute_base
from .conditions import evaluate, referenced_reference_codes
from .context import EvalContext
from .dates import in_effect, parse_date, days_inclusive
from .errors import (CapabilityError, ConflictingRulesError, IncompleteRunError, InputValidationError,
                     MissingDependencyError, MissingRuleError, SchemaError, StraddleError)
from .graph import build_graph
from .loader import RuleSetData, load_country, sha256_of
from .mechanisms import MECHANISMS
from .money import CALCULATION_PRECISION, D, fmt, is_number_like
from .references import ReferenceResolver
from .resolver import DEFAULT_RUN_TYPES, process_type, select_rules
from .schema import RUN_TYPES

PARTY = {"EARNING": "EMPLOYEE", "EMPLOYEE_DEDUCTION": "EMPLOYEE",
         "EMPLOYER_CONTRIBUTION": "EMPLOYER", "ACCRUAL": "EMPLOYER", "INFO": None}


def normalize_payload(payload):
    p = copy.deepcopy(payload)
    p.setdefault("run_type", "REGULAR")
    for key in ("employee", "employment", "time", "amounts"):
        p.setdefault(key, {})
    if (p["run_type"] == "TERMINATION" or p.get("base_run_type") == "TERMINATION") and not p.get("period"):
        term = p.get("termination_date") or p.get("dates", {}).get("termination_date")
        if term:
            try:
                end = date.fromisoformat(str(term))
                p["period"] = {"start": end.replace(day=1).isoformat(), "end": end.isoformat()}
            except ValueError:
                pass   # validate_payload reporta la fecha
    return p


def validate_termination(p, dates, manifest):
    """Entrada mínima de una terminación. Las causas y tipos de contrato válidos los declara el
    manifiesto del país (data); aquí solo se exige que existan y sean coherentes."""
    issues = []
    if "termination_date" not in dates:
        issues.append("falta 'termination_date' (fecha de terminación)")
    hire = p["employment"].get("hire_date")
    hire_date = None
    if not hire:
        issues.append("falta employment.hire_date (fecha de ingreso)")
    else:
        try:
            hire_date = date.fromisoformat(str(hire))
        except ValueError:
            issues.append(f"employment.hire_date inválida: {hire!r}")
    if hire_date and "termination_date" in dates and dates["termination_date"] < hire_date:
        issues.append("la fecha de terminación es anterior a la de ingreso")
    spec = manifest.get("termination") or {}
    cause = (p.get("termination") or {}).get("cause")
    if not cause:
        issues.append("falta termination.cause (causa de terminación)")
    elif spec.get("causes") is not None and cause not in spec["causes"]:
        issues.append(f"termination.cause {cause!r} no está soportada para {manifest['country']}; "
                      f"permitidas: {spec['causes']}")
    contract = p["employment"].get("contract_type")
    if not contract:
        issues.append("falta employment.contract_type (tipo de contrato)")
    elif spec.get("contract_types") is not None and contract not in spec["contract_types"]:
        issues.append(f"employment.contract_type {contract!r} no soportado para {manifest['country']}; "
                      f"permitidos: {spec['contract_types']}")
    if contract in spec.get("requires_contract_end_for", []) and not p["employment"].get("contract_end_date"):
        issues.append(f"employment.contract_end_date es obligatorio para el contrato {contract}")
    for name in ("salary_history", "vacation_history", "benefit_history"):
        value = p.get(name)
        if value is not None and not isinstance(value, (list, dict)):
            issues.append(f"{name} debe ser una lista (o un objeto)")
    if issues:
        raise InputValidationError("entrada de terminación inválida", details=issues)


def validate_payload(p):
    issues = []
    if not p.get("country"):
        issues.append("falta 'country'")
    if p["run_type"] not in RUN_TYPES:
        issues.append(f"run_type inválido: {p['run_type']!r} (permitidos {RUN_TYPES})")
    if p.get("base_run_type") not in (None, "REGULAR", "TERMINATION"):
        issues.append(f"base_run_type inválido: {p['base_run_type']!r} (permitidos REGULAR, TERMINATION)")
    period = p.get("period") or {}
    if not period.get("start") or not period.get("end"):
        issues.append("falta period.start / period.end")
    for section in ("time", "amounts"):
        for key, value in p[section].items():
            if isinstance(value, float):
                issues.append(f"{section}.{key}: no se permite float para valores legales (use texto)")
            elif isinstance(value, bool) or value is None or not is_number_like(value):
                issues.append(f"{section}.{key}: valor no numérico ({value!r})")
            elif D(value) < 0:
                issues.append(f"{section}.{key}: no puede ser negativo ({value})")
    salary = p["employment"].get("monthly_salary")
    if salary is not None:
        if isinstance(salary, float) or isinstance(salary, bool) or not is_number_like(salary):
            issues.append(f"employment.monthly_salary: valor no numérico ({salary!r})")
        elif D(salary) < 0:
            issues.append(f"employment.monthly_salary: no puede ser negativo ({salary})")
    if issues:
        raise InputValidationError("entrada inválida", details=issues)


def build_dates(p):
    period = p["period"]
    start = parse_date(period["start"], what="period.start")
    end = parse_date(period["end"], what="period.end")
    if end < start:
        raise InputValidationError("period.end es anterior a period.start")
    dates = {"period_start": start, "period_end": end, "period_days": days_inclusive(start, end)}
    for key in ("pay_date", "accrual_date", "event_date", "termination_date"):
        value = p.get(key) or p.get("dates", {}).get(key)
        if value:
            dates[key] = parse_date(value, what=key)
    return dates


class PayrollRun:
    def __init__(self, **fields):
        self.__dict__.update(fields)

    def to_dict(self, *, include_documents=False):
        data = {k: v for k, v in self.__dict__.items() if k != "_documents"}
        if include_documents:
            data["normative_documents"] = self._documents
        return jsonable(data)

    def line(self, concept):
        for line in self.result["lines"]:
            if line["concept"] == concept:
                return line
        return None

    def amount(self, concept):
        line = self.line(concept)
        return line["amount"] if line else None


class PayrollEngine:
    def __init__(self, ruleset=None, *, root=None):
        self._ruleset = ruleset
        self._root = root

    # -- API pública --------------------------------------------------------
    def run(self, payload, *, ruleset=None, strict=False, user=None, calculation_timestamp=None):
        with localcontext() as ctx:
            ctx.prec = CALCULATION_PRECISION
            return self._run(payload, ruleset or self._ruleset, strict, user, calculation_timestamp)

    # -- implementación -----------------------------------------------------
    def _load(self, country):
        try:
            return load_country(country) if self._root is None else load_country(country, self._root)
        except SchemaError as exc:
            if "no existe paquete" in exc.message:
                raise CapabilityError(f"{country} no tiene datos normativos cargados", details=[exc.message]) from exc
            raise

    def _run(self, payload, ruleset, strict, user, calculation_timestamp):
        p = normalize_payload(payload)
        validate_payload(p)
        country = p["country"]
        ruleset = ruleset or self._load(country)
        manifest = ruleset.manifest
        if not manifest.get("local_payroll_engine"):
            raise CapabilityError(
                f"{country} no tiene motor de nómina local (contexto: consolidación={manifest.get('consolidation_context')}). "
                "Habilitarlo exige una investigación normativa independiente.")
        process = process_type(p)
        if process == "TERMINATION" and not any(str(r.get("category", "")).startswith("TERMINATION") for r in ruleset.rules):
            raise CapabilityError(
                f"{country}: la terminación/liquidación no está implementada en el motor normativo (no hay reglas de categoría "
                "TERMINATION_*); el módulo de liquidación heredado no tiene datos normativos validados.")
        if p["run_type"] in ("ADJUSTMENT", "HISTORICAL_RECALCULATION") and not p.get("original_run_uid"):
            raise InputValidationError(f"run_type {p['run_type']} requiere 'original_run_uid' (la corrida que corrige o recalcula)")
        dates = build_dates(p)
        if process == "TERMINATION":
            validate_termination(p, dates, manifest)
        chain = p.get("jurisdictions") or [manifest.get("jurisdiction_default", "NATIONAL")]
        audit = AuditTrail()
        warnings = []

        refs = ReferenceResolver(ruleset.references, country, chain, ruleset.series)
        selected, discarded = select_rules(ruleset, chain, dates, p, refs)
        audit.discarded_rules = discarded
        if not [s for s in selected if s.kind != "VALIDATION"]:
            raise MissingRuleError(f"no hay reglas vigentes para {country} en {chain} el {dates['period_end']}")
        for sel in selected:
            if sel.straddle_note:
                warnings.append({"type": "CHANGE_WITHIN_PERIOD", "message": sel.straddle_note})
        used_refs = {}
        bases_values, lines_by_concept, line_records = {}, {}, []

        def make_ctx(on_date):
            ctx = EvalContext(payload=p, dates=dates, refs=refs, on_date=on_date,
                              bases=bases_values, lines=lines_by_concept)
            ctx.used_refs = used_refs
            return ctx

        # 1. validaciones normativas (datos), antes de calcular
        for sel in [s for s in selected if s.kind == "VALIDATION"]:
            for seg in sel.segments:
                ctx = make_ctx(seg.on_date)
                try:
                    violated, rec = evaluate(seg.rule.get("conditions"), ctx)
                except MissingDependencyError as exc:
                    raise SchemaError(f"la regla de validación {seg.rule['rule_id']} no puede usar bases: {exc}") from exc
                audit.validations.append({"rule_id": seg.rule["rule_id"], "violated": violated, "conditions": rec})
                if violated and seg.rule.get("severity", "ERROR") == "ERROR":
                    raise InputValidationError(
                        seg.rule["message"], details=[f"{seg.rule['rule_id']}: {seg.rule['message']}"])
                if violated:
                    warnings.append({"type": "VALIDATION_WARNING", "rule_id": seg.rule["rule_id"],
                                     "message": seg.rule["message"]})

        # 2. reglas sin implementar: no se ejecutan ni se disimulan
        executable, pending = [], []
        for sel in selected:
            if sel.kind == "VALIDATION":
                continue
            not_impl = [seg.rule for seg in sel.segments if seg.rule["implementation_status"] == "NOT_IMPLEMENTED"]
            if not_impl:
                pending.append({"rule_id": not_impl[0]["rule_id"], "concept": sel.concept,
                                "note": not_impl[0].get("notes")})
            else:
                executable.append(sel)
        for item in pending:
            warnings.append({"type": "RULE_NOT_IMPLEMENTED", "rule_id": item["rule_id"],
                             "message": f"regla aplicable NOT_IMPLEMENTED: {item['rule_id']}"
                                        + (f" ({item['note']})" if item.get("note") else "")})
        if pending and strict:
            raise IncompleteRunError("hay reglas aplicables NOT_IMPLEMENTED", details=[r["rule_id"] for r in pending])

        # 3. bases vigentes y grafo
        base_defs = {}
        for base in ruleset.bases:
            if process not in base.get("run_types", DEFAULT_RUN_TYPES):
                continue   # las bases de terminación no existen en la corrida mensual y viceversa
            if base["country"] == country and in_effect(base["effective"], dates["period_end"]):
                if base["base"] in base_defs:
                    raise ConflictingRulesError(f"la base {base['base']} tiene más de una definición vigente")
                base_defs[base["base"]] = base
        for code, base_def in base_defs.items():
            treatments = [t for c in ruleset.concepts.values() for t in c.get("treatments", []) if t["base"] == code]
            for ref_code in referenced_reference_codes(base_def.get("limits")) | referenced_reference_codes(treatments):
                changes = refs.change_dates(ref_code, dates["period_start"], dates["period_end"])
                if changes:
                    raise StraddleError(
                        f"la base {code} usa la referencia {ref_code}, que cambia el {changes[0]} dentro del período "
                        f"{dates['period_start']}..{dates['period_end']}; las bases no declaran política de partición")
        graph = build_graph(executable, base_defs, ruleset.concepts)
        order = graph.order()
        audit.execution_order = order
        audit.selected_rules = [{"rule_id": seg.rule["rule_id"], "version": seg.rule["version"], "node": s.node_key,
                                 "on_date": seg.on_date} for s in selected for seg in s.segments]

        # 4. ejecución en orden de dependencias
        for node_id in order:
            node = graph.nodes[node_id]
            if node["type"] == "base":
                base_def = node["ref"]
                value = compute_base(base_def, ruleset.concepts, line_records, make_ctx(dates["period_end"]), p)
                bases_values[base_def["base"]] = value
                for w in value["warnings"]:
                    warnings.append({"type": "BASE_WARNING", "base": base_def["base"], "message": w})
                audit.add_base(_base_record(value))
                continue
            sel = node["ref"]
            self._execute_rule(sel, ruleset, make_ctx, line_records, lines_by_concept, bases_values,
                               audit, warnings)

        # 5. resultado
        totals = _totals(line_records)
        for line in line_records:
            if line.get("input_type") == "EXTERNAL_INPUT":
                warnings.append({"type": "EXTERNAL_INPUT", "concept": line["concept"],
                                 "message": f"{line['concept']}: valor digitado por el usuario; el motor no lo calcula"})
        flagged = {}
        for line in line_records:
            src, ver_ = line.get("source") or {}, line.get("verification") or {}
            reasons = []
            if src.get("status") in ("PENDING", "CONFLICTING"):
                reasons.append(f"fuente {src['status']}")
            if ver_.get("interpretation_status") == "CONFLICTING":
                reasons.append("interpretación CONFLICTING")
            if ver_.get("open_question"):
                reasons.append("interpretación con pregunta abierta")
            if reasons and line["role"] != "INFO":
                flagged.setdefault(line["rule_id"], (line["concept"], reasons))
        for rule_id, (concept, reasons) in sorted(flagged.items()):
            warnings.append({"type": "UNVERIFIED_RULE", "rule_id": rule_id, "concept": concept,
                             "message": f"{concept}: regla ejecutada con {' y '.join(reasons)} (PENDING_VERIFICATION)"})
        pending_treatments = [f"{entry['concept']}→{rec['base']}" for rec in audit.bases
                              for entry in rec["contributions"]
                              if entry.get("status") == "PENDING_VERIFICATION" and entry.get("contributed") not in ("0", None)]
        if pending_treatments:
            warnings.append({"type": "PENDING_TREATMENTS", "items": pending_treatments,
                             "message": f"{len(pending_treatments)} tratamientos de base pendientes de verificación normativa "
                                        f"({', '.join(pending_treatments[:4])}{'…' if len(pending_treatments) > 4 else ''})"})
        status = "INCOMPLETE" if pending else ("COMPLETE_WITH_WARNINGS" if warnings else "COMPLETE")
        executed_rules = [seg.rule for sel in executable for seg in sel.segments]
        summary = _verification_summary(executed_rules, used_refs)

        result = {
            "currency": manifest["currency"],
            "lines": [{k: line[k] for k in ("line_id", "concept", "role", "party", "amount", "label_key", "label", "category",
                                            "rule_id", "rule_version")}
                      for line in line_records],
            "totals": totals,
        }
        for line in line_records:
            audit.add_line(_line_trace(line))
        input_snapshot = {
            "payload": p, "dates": dates, "jurisdictions": chain,
        }
        input_snapshot["hash"] = sha256_of(jsonable({k: input_snapshot[k] for k in ("payload", "dates", "jurisdictions")}))
        normative_snapshot = {
            "country": country, "ruleset_version": ruleset.ruleset_version,
            "content_hash": ruleset.content_hash,
            "rules_used": [{"rule_id": r["rule_id"], "version": r["version"]} for r in executed_rules],
            "references_used": sorted(used_refs),
        }
        trace = audit.to_dict()
        result_j = jsonable({"result": result, "status": status, "country": country, "period": p["period"]})
        run = PayrollRun(
            run_id=str(uuid.uuid4()), run_type=p["run_type"], original_run_uid=p.get("original_run_uid"),
            status=status, country=country,
            jurisdictions=chain, period=p["period"], anchor_dates=dates,
            employee=p["employee"], engine_version=ENGINE_VERSION,
            ruleset_version=ruleset.ruleset_version,
            calculation_timestamp=(calculation_timestamp or datetime.now(timezone.utc)).isoformat(),
            user=user, input_snapshot=input_snapshot, normative_snapshot=normative_snapshot,
            result=result, trace=trace, warnings=warnings, pending_rules=pending,
            verification_summary=summary, result_hash=sha256_of(result_j), trace_hash=trace_hash(trace),
            manifest=manifest, _documents=ruleset.documents(),
        )
        return run

    def _execute_rule(self, sel, ruleset, make_ctx, line_records, lines_by_concept, bases_values, audit, warnings):
        primary = sel.primary
        concept_def = ruleset.concepts[primary["concept"]]
        total = Decimal(0)
        segments_info, operands, cond_rec, exc_records, details, formula = [], [], None, [], {}, ""
        applied_any = False
        outcome_note = None
        for seg in sel.segments:
            rule = seg.rule
            ctx = make_ctx(seg.on_date)
            ok, cond_rec = evaluate(rule.get("conditions"), ctx)
            if not ok:
                audit.add_evaluation({"rule_id": rule["rule_id"], "concept": rule["concept"], "outcome": "NOT_APPLICABLE",
                                      "reason": "CONDICION_FALSE", "on_date": seg.on_date, "conditions": cond_rec})
                outcome_note = "CONDICION_FALSE"
                continue
            zeroed, skip = False, False
            for exc in rule.get("exceptions", []):
                hit, rec = evaluate(exc["conditions"], ctx)
                exc_records.append({"reason": exc.get("reason"), "effect": exc["effect"], "result": hit,
                                    "conditions": rec, "source": exc.get("source")})
                if hit and exc["effect"] == "NOT_APPLICABLE":
                    skip = True
                elif hit:
                    zeroed = True
            if skip:
                audit.add_evaluation({"rule_id": rule["rule_id"], "concept": rule["concept"], "outcome": "NOT_APPLICABLE",
                                      "reason": "EXCEPCION", "on_date": seg.on_date, "conditions": cond_rec,
                                      "exceptions": exc_records})
                outcome_note = "EXCEPCION"
                continue
            fn, _ = MECHANISMS[rule["calculation"]["mechanism"]]
            ctx.capture()
            result = fn(ctx, rule["calculation"]["params"])
            operands += ctx.capture()
            for note in (result.details or {}).get("warnings", []):
                warnings.append({"type": "MECHANISM_WARNING", "rule_id": rule["rule_id"], "message": note})
            amount = Decimal(0) if zeroed else result.amount
            if seg.fraction_den != 1 or seg.fraction_num != 1:
                amount = amount * seg.fraction_num / seg.fraction_den
            total += amount
            applied_any = True
            formula = result.formula
            details = result.details
            segments_info.append({"rule_id": rule["rule_id"], "version": rule["version"], "on_date": seg.on_date,
                                  "fraction": f"{seg.fraction_num}/{seg.fraction_den}", "amount": amount,
                                  "formula": result.formula, "details": result.details})
            audit.add_evaluation({"rule_id": rule["rule_id"], "concept": rule["concept"], "outcome": "APPLIED",
                                  "on_date": seg.on_date, "conditions": cond_rec, "exceptions": exc_records,
                                  "operands": operands})
        if not applied_any:
            return
        rounding_kind = primary["calculation"].get("rounding", "currency")
        rounded, rounding_rec = ruleset.rounding.apply(total, rounding_kind)
        line_id = f"L{len(line_records) + 1:03d}"
        base_code = details.get("base")
        line = {
            "line_id": line_id, "concept": primary["concept"], "role": concept_def["role"],
            "party": PARTY[concept_def["role"]], "amount": rounded, "label_key": concept_def.get("label_key"),
            "label": concept_def.get("label"),
            "rule_id": primary["rule_id"], "rule_version": primary["version"], "rule_key": primary["rule_key"],
            "jurisdiction": primary["jurisdiction"], "category": primary["category"], "anchor": primary["anchor"],
            "mechanism": primary["calculation"]["mechanism"], "formula": formula, "details": details,
            "operands": operands, "conditions": cond_rec, "exceptions": exc_records,
            "rounding": rounding_rec, "segments": segments_info, "source": primary.get("source"),
            "verification": primary.get("verification"), "effective": primary["effective"],
            "implementation_status": primary["implementation_status"],
            "input_type": primary.get("input_type"),
            "base_ref": _base_ref(bases_values.get(base_code)) if base_code else None,
            "concept_source": concept_def.get("source"),
        }
        line_records.append(line)
        lines_by_concept[line["concept"]] = lines_by_concept.get(line["concept"], Decimal(0)) + rounded


def _base_ref(base):
    if base is None:
        return None
    return {"code": base["base"], "value": base["value"], "limits": base["limits"],
            "cap_applied": base["cap_applied"], "raw_sum": base["raw_sum"]}


def _base_record(value):
    return {"base": value["base"], "value": value["value"], "raw_sum": value["raw_sum"], "limits": value["limits"],
            "cap_applied": value["cap_applied"], "contributions": value["contributions"],
            "exclusions": value["exclusions"], "warnings": value["warnings"], "source": value.get("source")}


def _line_trace(line):
    keys = ("line_id", "concept", "role", "party", "amount", "rule_id", "rule_version", "rule_key", "jurisdiction",
            "category", "anchor", "mechanism", "formula", "details", "operands", "conditions", "exceptions",
            "rounding", "segments", "source", "verification", "effective", "implementation_status",
            "base_ref", "concept_source", "input_type")
    return {k: line.get(k) for k in keys}


def _totals(lines):
    def total(role):
        return sum((l["amount"] for l in lines if l["role"] == role), Decimal(0))
    devengado, deducciones = total("EARNING"), total("EMPLOYEE_DEDUCTION")
    aportes, provisiones = total("EMPLOYER_CONTRIBUTION"), total("ACCRUAL")
    return {"total_devengado": devengado, "total_deducciones": deducciones,
            "neto_pagado": devengado - deducciones, "total_aportes_patronales": aportes,
            "total_provisiones": provisiones, "costo_empleador": devengado + aportes + provisiones}


def _verification_summary(rules, used_refs):
    def count(items, getter):
        out = {}
        for item in items:
            key = getter(item) or "N/A"
            out[key] = out.get(key, 0) + 1
        return out
    return {
        "rules": len(rules),
        "source_status": count(rules, lambda r: (r.get("source") or {}).get("status")),
        "interpretation_status": count(rules, lambda r: (r.get("verification") or {}).get("interpretation_status")),
        "professional_validation": count(rules, lambda r: (r.get("verification") or {}).get("professional_validation")),
        "implementation_status": count(rules, lambda r: r.get("implementation_status")),
        "references": count(used_refs.values(), lambda r: (r.get("source") or {}).get("status")),
    }


def reproduce(stored_run, documents, *, root=None):
    """Recalcula una corrida guardada con SUS reglas históricas (snapshot normativo) y su
    entrada original; compara el hash del resultado. No consulta config/ actual."""
    ruleset = RuleSetData.from_documents(documents)
    payload = stored_run["input_snapshot"]["payload"]
    fresh = PayrollEngine(root=root).run(payload, ruleset=ruleset)
    return {
        "same": fresh.result_hash == stored_run["result_hash"],
        "stored_hash": stored_run["result_hash"], "recomputed_hash": fresh.result_hash,
        "engine_version_stored": stored_run["engine_version"], "engine_version_now": ENGINE_VERSION,
        "recomputed": fresh,
    }
