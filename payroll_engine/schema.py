"""Validador de esquema de los datos normativos. Es la puerta de entrada de la
Matriz Normativa: ningún dato entra al motor sin pasar por aquí. Además de la
forma, impone reglas de integridad de la verificación: una fuente no puede
marcarse OFFICIAL sin autoridad, referencia legal, URL y fecha de verificación, y
una validación profesional no puede marcarse VALIDATED sin persona y fecha."""

from .conditions import OPERATORS
from .dates import ANCHORS, parse_schema_date
from .errors import SchemaError
from .mechanisms import MECHANISMS
from .money import RoundingPolicy, is_number_like

SOURCE_STATUS = ("OFFICIAL", "SECONDARY", "PENDING", "CONFLICTING", "NOT_APPLICABLE")
INTERPRETATION_STATUS = ("UNREVIEWED", "INTERPRETED", "VALIDATED", "CONFLICTING")
PROFESSIONAL_VALIDATION = ("PENDING", "VALIDATED")
IMPLEMENTATION_STATUS = ("NOT_IMPLEMENTED", "PARTIAL", "IMPLEMENTED")
CAPABILITY_STATUS = ("IMPLEMENTED", "PARTIALLY_IMPLEMENTED", "INCOMPLETE", "PENDING_VALIDATION",
                     "NOT_IMPLEMENTED", "NOT_APPLICABLE")
EXECUTION_PATHS = ("NEW_ENGINE", "LEGACY_ENGINE", "NONE")
RULE_KINDS = ("EARNING", "EMPLOYEE_DEDUCTION", "EMPLOYER_CONTRIBUTION", "ACCRUAL", "INFO", "VALIDATION")
CONCEPT_ROLES = ("EARNING", "EMPLOYEE_DEDUCTION", "EMPLOYER_CONTRIBUTION", "ACCRUAL", "INFO")
TREATMENT_MODES = ("INCLUDE", "EXCLUDE", "INCLUDE_WITH_CAP", "SPECIAL_RULE")
STRADDLE_POLICIES = ("ERROR", "USE_ANCHOR", "SPLIT_BY_DAYS")
ENFORCEMENTS = ("ENFORCE", "WARN_ONLY")
ROUNDING_KINDS = ("currency", "tax", "contribution", "display", "none")
RUN_TYPES = ("REGULAR", "SIMULATION", "ADJUSTMENT", "HISTORICAL_RECALCULATION", "TERMINATION")
BASE_RUN_TYPES = ("REGULAR", "TERMINATION")


def _req(doc, keys, where, issues):
    for key in keys:
        if key not in doc or doc[key] in (None, ""):
            if key in doc and doc[key] is None and key in ("to",):
                continue
            issues.append(f"{where}: falta '{key}'")


def _check_effective(eff, where, issues):
    if not isinstance(eff, dict) or "from" not in eff:
        issues.append(f"{where}: 'effective' requiere 'from' (y 'to' o null)")
        return
    try:
        start = parse_schema_date(eff["from"], what=f"{where}.effective.from")
        end = parse_schema_date(eff.get("to"), what=f"{where}.effective.to")
    except SchemaError as exc:
        issues.append(str(exc))
        return
    if start is None:
        issues.append(f"{where}: effective.from es obligatorio")
    if start and end and end < start:
        issues.append(f"{where}: effective.to anterior a effective.from")


def check_source(src, where, issues):
    if not isinstance(src, dict):
        issues.append(f"{where}: falta el bloque 'source'")
        return
    status = src.get("status")
    if status not in SOURCE_STATUS:
        issues.append(f"{where}: source.status inválido ({status!r}); permitidos {SOURCE_STATUS}")
        return
    if status == "OFFICIAL":
        for key in ("authority", "legal_reference", "official_url", "verified_at"):
            if not src.get(key):
                issues.append(f"{where}: source OFFICIAL requiere '{key}' (no se declara oficial sin respaldo verificable)")
    if src.get("verified_at"):
        try:
            parse_schema_date(src["verified_at"], what=f"{where}.source.verified_at")
        except SchemaError as exc:
            issues.append(str(exc))


def check_verification(ver, where, issues, *, required=True):
    if ver is None:
        if required:
            issues.append(f"{where}: falta el bloque 'verification'")
        return
    interp = ver.get("interpretation_status")
    prof = ver.get("professional_validation")
    if interp not in INTERPRETATION_STATUS:
        issues.append(f"{where}: verification.interpretation_status inválido ({interp!r})")
    if prof not in PROFESSIONAL_VALIDATION:
        issues.append(f"{where}: verification.professional_validation inválido ({prof!r})")
    if prof == "VALIDATED" and not (ver.get("validated_by") and ver.get("validated_at")):
        issues.append(f"{where}: professional_validation VALIDATED requiere 'validated_by' y 'validated_at' (persona humana)")


def _check_condition(cond, where, issues):
    if cond in (None, {}):
        return
    if not isinstance(cond, dict):
        issues.append(f"{where}: condición mal formada")
        return
    if "all" in cond or "any" in cond:
        for item in cond.get("all", cond.get("any", [])):
            _check_condition(item, where, issues)
    elif "not" in cond:
        _check_condition(cond["not"], where, issues)
    elif {"left", "op", "right"} <= set(cond):
        if cond["op"] not in OPERATORS:
            issues.append(f"{where}: operador no permitido {cond['op']!r}")
    else:
        issues.append(f"{where}: condición no reconocida {cond!r}")


def validate_reference(ref):
    issues, where = [], f"reference[{ref.get('ref_id', '?')}]"
    _req(ref, ("ref_id", "code", "country", "jurisdiction", "value", "effective"), where, issues)
    if "value" in ref and not is_number_like(ref["value"]):
        issues.append(f"{where}: value no es numérico")
    _check_effective(ref.get("effective"), where, issues)
    check_source(ref.get("source"), where, issues)
    check_verification(ref.get("verification"), where, issues)
    return issues


def validate_series(serie):
    """Serie temporal de referencia (p. ej. UF diaria): un valor por fecha, con fuente y cobertura."""
    issues, where = [], f"series[{serie.get('series_id', '?')}]"
    _req(serie, ("series_id", "code", "country", "jurisdiction", "granularity", "points", "coverage"), where, issues)
    if serie.get("granularity") not in ("DAILY", "MONTHLY"):
        issues.append(f"{where}: granularity debe ser DAILY o MONTHLY")
    points = serie.get("points") or {}
    for day, value in points.items():
        try:
            parse_schema_date(day, what=f"{where}.points")
        except SchemaError as exc:
            issues.append(str(exc))
            break
        if not is_number_like(value):
            issues.append(f"{where}: valor no numérico en {day}: {value!r}")
            break
    cov = serie.get("coverage") or {}
    if points and cov.get("from") and cov.get("to"):
        if min(points) < cov["from"] or max(points) > cov["to"]:
            issues.append(f"{where}: hay puntos fuera de la cobertura declarada {cov['from']}..{cov['to']}")
    check_source(serie.get("source"), where, issues)
    check_verification(serie.get("verification"), where, issues)
    return issues


def validate_concept(concept):
    issues, where = [], f"concept[{concept.get('concept', '?')}]"
    _req(concept, ("concept", "role"), where, issues)
    if concept.get("role") not in CONCEPT_ROLES:
        issues.append(f"{where}: role inválido ({concept.get('role')!r})")
    for i, tr in enumerate(concept.get("treatments", [])):
        tw = f"{where}.treatments[{i}]"
        _req(tr, ("base", "mode"), tw, issues)
        if tr.get("mode") not in TREATMENT_MODES:
            issues.append(f"{tw}: mode inválido ({tr.get('mode')!r})")
        if tr.get("mode") == "INCLUDE_WITH_CAP" and "cap" not in tr:
            issues.append(f"{tw}: INCLUDE_WITH_CAP requiere 'cap'")
        if tr.get("mode") == "SPECIAL_RULE" and "special" not in tr:
            issues.append(f"{tw}: SPECIAL_RULE requiere 'special'")
        if "effective" in tr:
            _check_effective(tr["effective"], tw, issues)
        _check_condition(tr.get("conditions"), tw, issues)
    check_source(concept.get("source"), where, issues)
    check_verification(concept.get("verification"), where, issues)
    return issues


def validate_base(base):
    issues, where = [], f"base[{base.get('base', '?')}]"
    _req(base, ("base", "country", "effective"), where, issues)
    _check_effective(base.get("effective"), where, issues)
    for rt in base.get("run_types", []):
        if rt not in RUN_TYPES:
            issues.append(f"{where}: run_types contiene un tipo inválido ({rt!r})")
    for key in ("minimum", "maximum"):
        limit = (base.get("limits") or {}).get(key)
        if limit is not None and limit.get("enforcement", "ENFORCE") not in ENFORCEMENTS:
            issues.append(f"{where}: enforcement inválido en {key}")
    check_source(base.get("source"), where, issues)
    check_verification(base.get("verification"), where, issues)
    return issues


def validate_rule(rule):
    issues, where = [], f"rule[{rule.get('rule_id', '?')}]"
    _req(rule, ("rule_id", "rule_key", "version", "country", "jurisdiction", "category",
                "kind", "effective", "anchor", "priority", "implementation_status"), where, issues)
    if rule.get("kind") not in RULE_KINDS:
        issues.append(f"{where}: kind inválido ({rule.get('kind')!r})")
    if rule.get("anchor") not in ANCHORS:
        issues.append(f"{where}: anchor inválido ({rule.get('anchor')!r}); permitidos {ANCHORS}")
    if rule.get("implementation_status") not in IMPLEMENTATION_STATUS:
        issues.append(f"{where}: implementation_status inválido")
    for rt in rule.get("run_types", []):
        if rt not in RUN_TYPES:
            issues.append(f"{where}: run_types contiene un tipo inválido ({rt!r})")
    if rule.get("straddle_policy", "USE_ANCHOR") not in STRADDLE_POLICIES:
        issues.append(f"{where}: straddle_policy inválido")
    _check_effective(rule.get("effective"), where, issues)
    _check_condition(rule.get("conditions"), where, issues)
    for i, exc_ in enumerate(rule.get("exceptions", [])):
        _check_condition(exc_.get("conditions"), f"{where}.exceptions[{i}]", issues)
        if exc_.get("effect") not in ("NOT_APPLICABLE", "ZERO"):
            issues.append(f"{where}.exceptions[{i}]: effect debe ser NOT_APPLICABLE o ZERO")
    if rule.get("kind") == "VALIDATION":
        if rule.get("severity", "ERROR") not in ("ERROR", "WARNING") or not rule.get("message"):
            issues.append(f"{where}: VALIDATION requiere 'message' y severity ERROR|WARNING")
    else:
        _req(rule, ("concept",), where, issues)
        calc = rule.get("calculation") or {}
        mech = calc.get("mechanism")
        if mech not in MECHANISMS:
            issues.append(f"{where}: mecanismo desconocido {mech!r}; permitidos {sorted(MECHANISMS)}")
        else:
            for param in MECHANISMS[mech][1]:
                if param not in calc.get("params", {}):
                    issues.append(f"{where}: el mecanismo {mech} requiere el parámetro '{param}'")
        if calc.get("rounding", "currency") not in ROUNDING_KINDS:
            issues.append(f"{where}: rounding inválido")
    check_source(rule.get("source"), where, issues)
    check_verification(rule.get("verification"), where, issues)
    return issues


def validate_manifest(manifest):
    issues, where = [], f"manifest[{manifest.get('country', '?')}]"
    _req(manifest, ("country", "year", "ruleset_version", "currency", "local_payroll_engine",
                    "consolidation_context", "execution_path", "capabilities"), where, issues)
    if manifest.get("execution_path") not in EXECUTION_PATHS:
        issues.append(f"{where}: execution_path inválido")
    for name, cap in (manifest.get("capabilities") or {}).items():
        if cap.get("status") not in CAPABILITY_STATUS:
            issues.append(f"{where}: capacidad {name} con estado inválido ({cap.get('status')!r})")
    return issues


def validate_rounding(data, country):
    issues = []
    try:
        RoundingPolicy(data)
    except SchemaError as exc:
        issues.append(f"rounding[{country}]: {exc}")
    return issues


def raise_if(issues, message):
    if issues:
        raise SchemaError(message, details=issues)
