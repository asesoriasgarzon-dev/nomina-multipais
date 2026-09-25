"""Mecanismo tipado de impuesto sobre rentas de trabajo con depuración y tabla en unidades de referencia.

Genérico: no conoce ningún país. El JSON declara la unidad (p. ej. UVT), las deducciones con sus topes, la renta exenta
porcentual, el tope global y la tabla de tramos; aquí solo se ejecuta la aritmética y se deja cada paso en los detalles
para la auditoría y la explicación."""

from decimal import Decimal

from .errors import SchemaError
from .mechanisms import MechanismResult
from .money import fmt


def _units(value, unit):
    return value / unit


def depurated_table_tax(ctx, p):
    """impuesto = tabla( base gravable en unidades ) × valor de la unidad.

    params:
      income        operando: ingreso laboral bruto del mes (para topes porcentuales de deducciones)
      base          operando: ingreso menos los ingresos no constitutivos de renta (p. ej. aportes obligatorios)
      unit          operando: valor de la unidad de referencia en moneda
      deductions    [{"key", "amount": op, "cap_units": n?, "cap_share_of_income": n?, "enabled": op?}]  (cada una con su tope)
      other_exempt  [{"key", "amount": op}]  rentas exentas sin tope propio
      exempt_share  {"share": r, "annual_cap_units": n, "periods_per_year": n}  renta exenta porcentual, DESPUÉS de lo anterior
      global_cap    {"share": r, "annual_cap_units": n, "periods_per_year": n}  tope a deducciones + exentas
      table         [{"from": n, "to": n|null, "rate": r, "plus": n}]  impuesto = (base − from) × rate + plus, en unidades
    """
    unit = ctx.num(p["unit"])
    if unit <= 0:
        raise SchemaError("la unidad de referencia debe ser positiva")
    income = ctx.num(p["income"])
    base = ctx.num(p["base"])
    steps = {"income": fmt(income), "base_before_depuration": fmt(base), "unit_value": fmt(unit)}

    total_ded = Decimal(0)
    ded_rows = []
    for d in p.get("deductions", []):
        enabled = ctx.operand(d["enabled"]) if "enabled" in d else True
        amount = ctx.num(d["amount"]) if enabled else Decimal(0)
        cap = None
        if d.get("cap_units") is not None:
            cap = ctx.num(d["cap_units"]) * unit
        if d.get("cap_share_of_income") is not None:
            share_cap = income * ctx.num(d["cap_share_of_income"])
            cap = share_cap if cap is None else min(cap, share_cap)
        used = amount if cap is None else min(amount, cap)
        total_ded += used
        ded_rows.append({"key": d["key"], "requested": fmt(amount), "cap": None if cap is None else fmt(cap), "applied": fmt(used)})
    other = Decimal(0)
    other_rows = []
    for e in p.get("other_exempt", []):
        amount = ctx.num(e["amount"])
        other += amount
        other_rows.append({"key": e["key"], "amount": fmt(amount)})
    steps["deductions"] = ded_rows
    steps["other_exempt"] = other_rows

    after = max(base - total_ded - other, Decimal(0))
    exempt_pct = Decimal(0)
    if p.get("exempt_share"):
        spec = p["exempt_share"]
        cap = ctx.num(spec["annual_cap_units"]) * unit / ctx.num(spec["periods_per_year"])
        raw = after * ctx.num(spec["share"])
        exempt_pct = min(raw, cap)
        steps["exempt_share"] = {"raw": fmt(raw), "cap": fmt(cap), "applied": fmt(exempt_pct)}

    reductions = total_ded + other + exempt_pct
    cap_applied = False
    if p.get("global_cap"):
        spec = p["global_cap"]
        limit = min(base * ctx.num(spec["share"]),
                    ctx.num(spec["annual_cap_units"]) * unit / ctx.num(spec["periods_per_year"]))
        if reductions > limit:
            reductions, cap_applied = limit, True
        steps["global_cap"] = {"limit": fmt(limit), "reductions_before": fmt(total_ded + other + exempt_pct),
                               "applied": fmt(reductions), "cap_applied": cap_applied}

    taxable = max(base - reductions, Decimal(0))
    taxable_units = _units(taxable, unit)
    tax_units, row_used = Decimal(0), None
    for row in p["table"]:
        lo = ctx.num(row["from"])
        hi = ctx.num(row["to"]) if row.get("to") is not None else None
        if taxable_units > lo and (hi is None or taxable_units <= hi):
            tax_units = (taxable_units - lo) * ctx.num(row["rate"]) + ctx.num(row.get("plus", 0))
            row_used = {"from": fmt(lo), "to": None if hi is None else fmt(hi), "rate": fmt(ctx.num(row["rate"])),
                        "plus": fmt(ctx.num(row.get("plus", 0)))}
            break
    steps.update({"taxable_base": fmt(taxable), "taxable_units": fmt(taxable_units), "bracket": row_used,
                  "tax_units": fmt(tax_units), "reductions_total": fmt(reductions)})
    amount = tax_units * unit
    formula = (f"tabla({fmt(taxable_units)} unidades) = {fmt(tax_units)} unidades × {fmt(unit)}  "
               f"[base {fmt(base)} − deducciones/exentas {fmt(reductions)}]")
    return MechanismResult(amount, formula, steps)


TAX_MECHANISMS = {"depurated_table_tax": (depurated_table_tax, ("income", "base", "unit", "table"))}
