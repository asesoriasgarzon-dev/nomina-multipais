"""Mecanismos de cálculo TIPADOS. El JSON describe la norma (parámetros, tasas,
tablas, umbrales); estos mecanismos ejecutan la operación. Son genéricos: ninguno
conoce un país. Cada uno devuelve el importe, una fórmula legible generada de la
ejecución real (para la explicación) y los detalles usados (para la auditoría)."""

from dataclasses import dataclass, field
from decimal import Decimal

from .errors import SchemaError
from .money import D, fmt


@dataclass
class MechanismResult:
    amount: Decimal
    formula: str
    details: dict = field(default_factory=dict)


def _divisor(ctx, proration):
    ptype = proration.get("type", "NONE")
    if ptype == "THIRTY_DAY_MONTH":
        return Decimal(30)
    if ptype == "CALENDAR_DAYS":
        return Decimal(ctx.dates["period_days"])
    if ptype == "FIXED_DIVISOR":
        return ctx.num(proration["divisor"])
    raise SchemaError(f"tipo de prorrateo desconocido: {ptype}")


def fixed_amount_prorated(ctx, p):
    amount = ctx.num(p["amount"])
    proration = p.get("proration", {"type": "NONE"})
    factor = ctx.num(p["factor"]) if "factor" in p else Decimal(1)
    if proration.get("type", "NONE") == "NONE":
        result = amount * factor
        return MechanismResult(result, f"{fmt(amount)} × {fmt(factor)}",
                               {"amount": fmt(amount), "factor": fmt(factor), "proration": "NONE"})
    days = ctx.num(proration["days"])
    divisor = _divisor(ctx, proration)
    result = amount * days / divisor * factor
    return MechanismResult(
        result, f"{fmt(amount)} × {fmt(days)} / {fmt(divisor)} × {fmt(factor)}",
        {"amount": fmt(amount), "days": fmt(days), "divisor": fmt(divisor),
         "factor": fmt(factor), "proration": proration["type"]})


def rate_on_base(ctx, p):
    base = ctx.num({"base": p["base"]})
    rate = ctx.num(p["rate"])
    factor = ctx.num(p["factor"]) if "factor" in p else Decimal(1)
    return MechanismResult(
        base * rate * factor, f"{p['base']} ({fmt(base)}) × {fmt(rate)}" + (f" × {fmt(factor)}" if "factor" in p else ""),
        {"base": p["base"], "base_value": fmt(base), "rate": fmt(rate), "factor": fmt(factor)})


def rate_on_excess(ctx, p):
    base = ctx.num({"base": p["base"]})
    threshold = ctx.num(p["threshold"])
    scale = ctx.num(p["scale_by"]) if "scale_by" in p else Decimal(1)
    limit = threshold * scale
    excess = max(base - limit, Decimal(0))
    rate = ctx.num(p["rate"])
    return MechanismResult(
        excess * rate,
        f"max({p['base']} ({fmt(base)}) − {fmt(limit)}, 0) × {fmt(rate)}",
        {"base": p["base"], "base_value": fmt(base), "threshold": fmt(limit),
         "excess": fmt(excess), "rate": fmt(rate)})


def rate_on_reference_amount(ctx, p):
    reference = ctx.num(p["amount"])
    scale = ctx.num(p["scale_by"]) if "scale_by" in p else Decimal(1)
    rate = ctx.num(p["rate"])
    return MechanismResult(
        reference * scale * rate, f"{fmt(reference)} × {fmt(scale)} × {fmt(rate)}",
        {"reference_amount": fmt(reference), "scale": fmt(scale), "rate": fmt(rate)})


def _bracket_bounds(ctx, bracket):
    lower = ctx.num(bracket["from"])
    upper = ctx.num(bracket["to"]) if bracket.get("to") is not None else None
    return lower, upper, ctx.num(bracket["rate"])


def progressive_brackets(ctx, p):
    """Tramos MARGINALES: cada tasa se aplica solo a la porción de base que cae en su tramo."""
    base = ctx.num({"base": p["base"]})
    total = Decimal(0)
    parts = []
    for bracket in p["brackets"]:
        lower, upper, rate = _bracket_bounds(ctx, bracket)
        if base <= lower:
            break
        portion = (min(base, upper) if upper is not None else base) - lower
        part = portion * rate
        total += part
        parts.append({"from": fmt(lower), "to": fmt(upper) if upper is not None else None,
                      "portion": fmt(portion), "rate": fmt(rate), "amount": fmt(part)})
    return MechanismResult(total, f"Σ tramos marginales sobre {p['base']} ({fmt(base)})",
                           {"base": p["base"], "base_value": fmt(base), "brackets": parts})


def bracket_rate_on_base(ctx, p):
    """Tasa determinada por el tramo en que cae un valor de búsqueda; se aplica a TODA la base."""
    base = ctx.num({"base": p["base"]})
    lookup = p["lookup"]
    if lookup["type"] == "BASE_MULTIPLE_OF_REFERENCE":
        reference = ctx.num({"reference": {"code": lookup["reference"]}})
        value = base / reference
    elif lookup["type"] == "BASE_VALUE":
        value = base
    else:
        raise SchemaError(f"lookup desconocido: {lookup['type']}")
    rate, chosen = ctx.num(p.get("default_rate", "0")), None
    for bracket in p["brackets"]:
        lower, upper, bracket_rate = _bracket_bounds(ctx, bracket)
        if value >= lower and (upper is None or value < upper):
            rate, chosen = bracket_rate, {"from": fmt(lower), "to": fmt(upper) if upper is not None else None}
            break
    return MechanismResult(
        base * rate, f"{p['base']} ({fmt(base)}) × tasa del tramo ({fmt(rate)}) [valor de búsqueda {fmt(value)}]",
        {"base": p["base"], "base_value": fmt(base), "lookup_value": fmt(value),
         "bracket": chosen, "rate": fmt(rate)})


def pass_through(ctx, p):
    amount = ctx.num(p["amount"])
    return MechanismResult(amount, f"valor informado: {fmt(amount)}", {"amount": fmt(amount)})


# nombre -> (función, parámetros obligatorios)
MECHANISMS = {
    "fixed_amount_prorated": (fixed_amount_prorated, ("amount",)),
    "rate_on_base": (rate_on_base, ("base", "rate")),
    "rate_on_excess": (rate_on_excess, ("base", "threshold", "rate")),
    "rate_on_reference_amount": (rate_on_reference_amount, ("amount", "rate")),
    "progressive_brackets": (progressive_brackets, ("base", "brackets")),
    "bracket_rate_on_base": (bracket_rate_on_base, ("base", "lookup", "brackets")),
    "pass_through": (pass_through, ("amount",)),
}


def mechanism_bases(params):
    """Bases que un mecanismo lee: el parámetro 'base', el 'lookup' y operandos anidados."""
    from .conditions import referenced_bases
    found = referenced_bases(params)
    if isinstance(params.get("base"), str):
        found.add(params["base"])
    lookup = params.get("lookup")
    if isinstance(lookup, dict) and isinstance(lookup.get("base"), str):
        found.add(lookup["base"])
    return found


# mecanismos de terminación/liquidación/vacaciones/horas extra (mismo contrato, módulo aparte)
from .mechanisms_termination import TERMINATION_MECHANISMS  # noqa: E402

MECHANISMS.update(TERMINATION_MECHANISMS)

from .mechanisms_tax import TAX_MECHANISMS  # noqa: E402

MECHANISMS.update(TAX_MECHANISMS)
