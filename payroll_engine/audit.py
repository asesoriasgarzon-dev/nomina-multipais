"""Audit Trail: registra lo que REALMENTE se ejecutó (entradas, reglas
seleccionadas y descartadas, evaluaciones de condiciones, bases con sus
inclusiones/exclusiones, operaciones, redondeos, topes, excepciones y resultado).
La explicación se genera desde este registro; nunca se inventa después."""

from decimal import Decimal

from .loader import sha256_of
from .money import fmt


def jsonable(value):
    """Convierte Decimals y fechas a texto estable (para persistir y calcular hashes)."""
    if isinstance(value, Decimal):
        return fmt(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


class AuditTrail:
    def __init__(self):
        self.selected_rules = []
        self.discarded_rules = []
        self.evaluations = []
        self.bases = []
        self.lines = []
        self.execution_order = []
        self.validations = []

    def add_evaluation(self, record):
        self.evaluations.append(record)

    def add_line(self, record):
        self.lines.append(record)

    def add_base(self, record):
        self.bases.append(record)

    def to_dict(self):
        return jsonable({
            "selected_rules": self.selected_rules, "discarded_rules": self.discarded_rules,
            "execution_order": self.execution_order, "validations": self.validations,
            "evaluations": self.evaluations, "bases": self.bases, "lines": self.lines,
        })


def trace_hash(trace_dict):
    return sha256_of(trace_dict)
