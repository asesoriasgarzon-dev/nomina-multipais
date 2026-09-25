"""Rule Resolver. Selecciona qué versión de cada regla aplica según país,
jurisdicción, fecha ancla (que DECLARA cada regla), filtros de aplicabilidad y
prioridad. Si una regla cambia dentro del período aplica la política que esa regla
declara (ERROR | USE_ANCHOR | SPLIT_BY_DAYS); nunca una política universal."""

from dataclasses import dataclass, field
from datetime import timedelta

from .conditions import applies_to, referenced_reference_codes
from .dates import in_effect, parse_schema_date
from .errors import ConflictingRulesError, MissingAnchorDateError, StraddleError


DEFAULT_RUN_TYPES = ["REGULAR", "SIMULATION", "ADJUSTMENT", "HISTORICAL_RECALCULATION"]


def process_type(payload):
    """Proceso cuyas reglas se aplican. ADJUSTMENT e HISTORICAL_RECALCULATION son MODOS de reproceso de otro proceso
    (`base_run_type`: REGULAR por defecto o TERMINATION); los demás tipos son su propio proceso."""
    run_type = payload.get("run_type", "REGULAR")
    if run_type in ("ADJUSTMENT", "HISTORICAL_RECALCULATION"):
        return payload.get("base_run_type", "REGULAR")
    return run_type


@dataclass
class Segment:
    rule: dict
    on_date: object
    fraction_num: int = 1
    fraction_den: int = 1
    days: int = 0


@dataclass
class SelectedRule:
    node_key: str
    segments: list = field(default_factory=list)
    straddle_note: str = None

    @property
    def primary(self):
        return self.segments[-1].rule

    @property
    def kind(self):
        return self.primary["kind"]

    @property
    def concept(self):
        return self.primary.get("concept")

    def versions(self):
        return [s.rule for s in self.segments]


def _anchor_date(rule, dates):
    anchor = rule["anchor"]
    value = dates.get(anchor)
    if value is None:
        raise MissingAnchorDateError(
            f"la regla {rule['rule_id']} usa la fecha ancla '{anchor}', que no está en la entrada")
    return value


def _pick(candidates, on_date, what):
    active = [r for r in candidates if in_effect(r["effective"], on_date)]
    if not active:
        return None
    active.sort(key=lambda r: -int(r["priority"]))
    if len(active) > 1 and int(active[0]["priority"]) == int(active[1]["priority"]):
        raise ConflictingRulesError(
            f"{what}: {len(active)} versiones vigentes el {on_date} con la misma prioridad",
            details=[r["rule_id"] for r in active])
    return active[0]


def _rule_reference_codes(rule):
    return referenced_reference_codes(rule.get("calculation", {}).get("params", {})) \
        | referenced_reference_codes(rule.get("conditions")) | referenced_reference_codes(rule.get("exceptions", []))


def _change_points(group, period_start, period_end, refs=None):
    """Fechas dentro de (inicio, fin] en las que cambia la versión de la regla O el valor de alguna
    referencia que la regla usa."""
    points = set()
    if refs is not None:
        for rule in group:
            for code in _rule_reference_codes(rule):
                points.update(refs.change_dates(code, period_start, period_end))
    for rule in group:
        start = parse_schema_date(rule["effective"]["from"], what="effective.from")
        end = parse_schema_date(rule["effective"].get("to"), what="effective.to")
        if period_start < start <= period_end:
            points.add(start)
        if end is not None and period_start <= end < period_end:
            points.add(end + timedelta(days=1))
    return sorted(points)


def select_rules(ruleset, chain, dates, payload, refs=None):
    """Devuelve (seleccionadas, descartadas). `dates` incluye period_start/period_end/period_days
    y las fechas ancla opcionales ya parseadas."""
    groups, discarded = {}, []
    for rule in ruleset.rules:
        if rule["country"] != ruleset.country:
            continue
        if rule["jurisdiction"] not in chain:
            discarded.append({"rule_id": rule["rule_id"], "reason": "JURISDICCION_FUERA_DE_LA_CADENA"})
            continue
        # las reglas de terminación solo corren en corridas TERMINATION y las mensuales nunca en ellas
        if process_type(payload) not in rule.get("run_types", DEFAULT_RUN_TYPES):
            continue
        if not applies_to(rule.get("applies_to"), payload):
            discarded.append({"rule_id": rule["rule_id"], "reason": "NO_APLICA_AL_TRABAJADOR"})
            continue
        groups.setdefault(f"{rule['rule_key']}@{rule['jurisdiction']}", []).append(rule)

    selected = []
    for node_key in sorted(groups):
        group = groups[node_key]
        anchor_rule = group[-1]
        on_date = _anchor_date(anchor_rule, dates)
        version = _pick(group, on_date, node_key)
        if version is None:
            for rule in group:
                discarded.append({"rule_id": rule["rule_id"], "reason": "SIN_VIGENCIA_EN_LA_FECHA_ANCLA",
                                  "anchor": rule["anchor"], "date": on_date.isoformat()})
            continue
        for rule in group:
            if rule is not version:
                discarded.append({"rule_id": rule["rule_id"], "reason": "OTRA_VERSION_VIGENTE",
                                  "selected": version["rule_id"]})
        sel = SelectedRule(node_key=node_key)
        anchor = version["anchor"]
        if anchor in ("period_start", "period_end"):
            points = _change_points(group, dates["period_start"], dates["period_end"], refs)
            if points:
                policy = version.get("straddle_policy", "USE_ANCHOR")
                if policy == "ERROR":
                    raise StraddleError(
                        f"la regla {node_key} (o una referencia que usa) cambia el {points[0]} dentro del período "
                        f"{dates['period_start']}..{dates['period_end']} y declara straddle_policy=ERROR")
                if policy == "USE_ANCHOR":
                    sel.straddle_note = (f"{node_key}: cambio normativo el {points[0]} dentro del período; "
                                         f"se usó la fecha ancla {on_date} (straddle_policy=USE_ANCHOR)")
                if policy == "SPLIT_BY_DAYS":
                    if len(points) > 1:
                        raise StraddleError(f"la regla {node_key} tiene más de un cambio dentro del período")
                    change = points[0]
                    before = _pick(group, change - timedelta(days=1), node_key)
                    after = _pick(group, change, node_key)
                    if before is None or after is None:
                        raise StraddleError(f"la regla {node_key} queda sin vigencia en parte del período")
                    total = dates["period_days"]
                    days_before = (change - dates["period_start"]).days
                    sel.segments = [
                        Segment(before, change - timedelta(days=1), days_before, total, days_before),
                        Segment(after, dates["period_end"], total - days_before, total, total - days_before),
                    ]
                    selected.append(sel)
                    continue
        sel.segments = [Segment(version, on_date)]
        selected.append(sel)

    # varias reglas que producen el mismo concepto en la misma jurisdicción: gana la prioridad
    by_concept, final = {}, []
    for sel in selected:
        if sel.kind == "VALIDATION":
            final.append(sel)
            continue
        by_concept.setdefault((sel.concept, sel.primary["jurisdiction"]), []).append(sel)
    for (concept, jurisdiction), group in sorted(by_concept.items()):
        group.sort(key=lambda s: -int(s.primary["priority"]))
        if len(group) > 1 and int(group[0].primary["priority"]) == int(group[1].primary["priority"]):
            raise ConflictingRulesError(
                f"reglas en conflicto para el concepto {concept} ({jurisdiction})",
                details=[s.primary["rule_id"] for s in group])
        final.append(group[0])
        for loser in group[1:]:
            discarded.append({"rule_id": loser.primary["rule_id"], "reason": "SUPERADA_POR_PRIORIDAD",
                              "selected": group[0].primary["rule_id"]})
    return final, discarded
