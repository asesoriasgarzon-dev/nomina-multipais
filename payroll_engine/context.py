"""Contexto de evaluación: resuelve operandos declarativos ({"input"}, {"reference"},
{"base"}, {"line"}, {"value"}) y registra qué se leyó, para el audit trail."""

from datetime import date, timedelta
from decimal import Decimal

from .errors import InputValidationError, MissingDependencyError, MissingInputError, SchemaError
from .money import D, fmt, is_number_like
from .temporal import month_end, service_time

SERVICE_MEASURES = ("COMPLETED_YEARS", "COMPLETED_MONTHS", "TOTAL_DAYS", "YEARS_DECIMAL", "MONTHS_DECIMAL")


class EvalContext:
    def __init__(self, *, payload, dates, refs, on_date, bases, lines):
        self.payload = payload          # entrada normalizada (dict)
        self.dates = dates              # dict de fechas ancla ya parseadas
        self.refs = refs                # ReferenceResolver
        self.on_date = on_date          # fecha con la que se resuelven referencias
        self.bases = bases              # code -> BaseValue (dict)
        self.lines = lines              # concepto -> Decimal acumulado
        self.log = []                   # operandos leídos en la evaluación actual
        self.used_refs = {}             # ref_id -> registro (para el snapshot)

    # -- lectura de la entrada -------------------------------------------------
    def input_value(self, path, default=None):
        node = self.payload
        for part in path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                if default is not None:
                    return default
                return None
        return node

    # -- operandos -------------------------------------------------------------
    def operand(self, spec):
        """Devuelve Decimal, str o bool según el operando."""
        if isinstance(spec, (str, int, Decimal)) and not isinstance(spec, bool):
            return D(spec)
        if isinstance(spec, bool):
            return spec
        if not isinstance(spec, dict):
            raise TypeError(f"operando inválido: {spec!r}")
        if "value" in spec:
            value = spec["value"]
            self.log.append({"kind": "value", "value": str(value)})
            return D(value) if is_number_like(value) else value
        if "input" in spec:
            raw = self.input_value(spec["input"], spec.get("default"))
            if raw is None:
                raise MissingInputError(f"falta el dato de entrada '{spec['input']}'")
            self.log.append({"kind": "input", "name": spec["input"], "value": str(raw)})
            if isinstance(raw, bool) or spec.get("as") == "text":
                return raw if isinstance(raw, bool) else str(raw)
            return D(raw) if is_number_like(raw) else raw
        if "reference" in spec:
            return self._reference(spec["reference"])
        if "service" in spec:
            return self._service(spec["service"])
        if "base" in spec:
            code = spec["base"]
            if code not in self.bases:
                raise MissingDependencyError(f"la base {code} no está calculada")
            value = self.bases[code]["value"]
            self.log.append({"kind": "base", "name": code, "value": fmt(value)})
            return value
        if "line" in spec:
            concept = spec["line"]
            value = self.lines.get(concept, Decimal(0))
            self.log.append({"kind": "line", "name": concept, "value": fmt(value)})
            return value
        raise TypeError(f"operando desconocido: {spec!r}")

    def num(self, spec):
        value = self.operand(spec)
        if isinstance(value, bool) or not isinstance(value, Decimal):
            raise TypeError(f"se esperaba un número y se obtuvo {value!r}")
        return value

    def _service(self, measure):
        """Antigüedad medida entre employment.hire_date y termination_date (para condiciones)."""
        if measure not in SERVICE_MEASURES:
            raise SchemaError(f"medida de antigüedad desconocida: {measure!r}; permitidas {SERVICE_MEASURES}")
        raw = self.input_value("employment.hire_date")
        end = self.dates.get("termination_date")
        if raw in (None, "") or end is None:
            raise MissingInputError("la antigüedad requiere employment.hire_date y termination_date")
        try:
            hire = raw if isinstance(raw, date) else date.fromisoformat(str(raw))
        except ValueError as exc:
            raise InputValidationError(f"employment.hire_date inválida: {raw!r}") from exc
        st = service_time(hire, end)
        value = {"COMPLETED_YEARS": Decimal(st.years), "COMPLETED_MONTHS": Decimal(st.total_months),
                 "TOTAL_DAYS": Decimal((end - hire).days + 1), "YEARS_DECIMAL": st.years_decimal(),
                 "MONTHS_DECIMAL": Decimal(st.total_months) + Decimal(st.days) / 30}[measure]
        self.log.append({"kind": "service", "name": measure, "value": fmt(value), "service": st.as_text()})
        return value

    def _reference_date(self, spec):
        """Fecha con la que se resuelve una referencia: por defecto la fecha ancla de la regla; con
        `date_rule` puede ser otra (p. ej. CL art. 172: UF del último día del mes anterior al pago)."""
        rule = spec.get("date_rule")
        if not rule:
            return self.on_date
        if rule.get("type") != "PREVIOUS_MONTH_END":
            raise SchemaError(f"date_rule desconocida: {rule.get('type')!r}")
        key = rule.get("of", "pay_date")
        base = self.dates.get(key) or self.dates.get("termination_date") or self.dates["period_end"]
        return month_end(base.replace(day=1) - timedelta(days=1))

    def _reference(self, spec):
        code = spec["code"]
        multiple = D(spec.get("multiple", 1))
        on_date = self._reference_date(spec)
        resolved = self.refs.resolve(code, on_date, spec.get("jurisdiction"))
        self.used_refs[resolved.ref_id] = resolved.record
        value = resolved.value * multiple
        self.log.append({"kind": "reference", "code": code, "ref_id": resolved.ref_id,
                         "reference_value": fmt(resolved.value), "multiple": fmt(multiple),
                         "value": fmt(value), "on_date": on_date.isoformat()})
        return value

    def capture(self):
        """Devuelve y limpia el registro de operandos leídos."""
        out, self.log = self.log, []
        return out
