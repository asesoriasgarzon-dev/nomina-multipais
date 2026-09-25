"""Utilidades de fecha. Vigencias: `from` y `to` son INCLUSIVAS (`to` nulo = abierta),
como en el esquema normativo (2026-01-01 .. 2026-09-30 / 2026-10-01 .. null)."""

from datetime import date, timedelta

from .errors import InputValidationError, SchemaError

ANCHORS = ("period_start", "period_end", "pay_date", "accrual_date", "event_date", "termination_date")


def parse_date(value, *, what="fecha"):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"{what} inválida: {value!r} (se espera AAAA-MM-DD)") from exc


def parse_schema_date(value, *, what):
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise SchemaError(f"{what} inválida: {value!r}") from exc


def in_effect(effective, on_date):
    """effective = {"from": "AAAA-MM-DD", "to": "AAAA-MM-DD"|None}."""
    start = parse_schema_date(effective.get("from"), what="effective.from")
    end = parse_schema_date(effective.get("to"), what="effective.to")
    if start is None:
        raise SchemaError("effective.from es obligatorio")
    return start <= on_date and (end is None or on_date <= end)


def overlaps(a, b):
    a_from = parse_schema_date(a["from"], what="effective.from")
    a_to = parse_schema_date(a.get("to"), what="effective.to") or date.max
    b_from = parse_schema_date(b["from"], what="effective.from")
    b_to = parse_schema_date(b.get("to"), what="effective.to") or date.max
    return a_from <= b_to and b_from <= a_to


def days_inclusive(start, end):
    return (end - start).days + 1


def day_before(d):
    return d - timedelta(days=1)
