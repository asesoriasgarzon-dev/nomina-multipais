"""Mecanismos TIPADOS para terminación, liquidación, vacaciones y horas extra.

Igual que mechanisms.py: ninguno conoce un país. El JSON declara la norma (ventanas, conteos,
tramos, tasas, límites); estos mecanismos ejecutan la aritmética y devuelven el importe, una
fórmula legible generada de la ejecución real y los detalles para la auditoría.

Cada mecanismo NO decide qué se paga: la regla (datos) decide si aplica (condiciones sobre causa
de terminación, tipo de contrato, antigüedad...). Aquí solo se calcula."""

import math
from datetime import date, timedelta
from decimal import Decimal

from .errors import InputValidationError, MissingInputError, SchemaError
from .mechanisms import MechanismResult
from .money import D, fmt
from .temporal import (COUNT_UNITS, add_months, commercial_days_360, count_units, resolve_window,
                       service_time)


# -- utilidades de contexto -------------------------------------------------------------------
def _date_input(ctx, path):
    raw = ctx.input_value(path)
    if raw in (None, ""):
        raise MissingInputError(f"falta el dato de entrada '{path}' (fecha AAAA-MM-DD)")
    try:
        return raw if isinstance(raw, date) else date.fromisoformat(str(raw))
    except ValueError as exc:
        raise InputValidationError(f"'{path}' no es una fecha válida: {raw!r}") from exc


def _hire_and_end(ctx):
    hire = _date_input(ctx, "employment.hire_date")
    end = ctx.dates.get("termination_date")
    if end is None:
        raise MissingInputError("falta 'termination_date' (fecha de terminación) para calcular por antigüedad")
    if end < hire:
        raise InputValidationError(f"la fecha de terminación {end} es anterior a la de ingreso {hire}")
    return hire, end


def _opt_num(ctx, spec, default="0"):
    return ctx.num(spec) if spec is not None else D(default)


# -- 1. proporción de un importe sobre una ventana de servicio --------------------------------
def service_period_proration(ctx, p):
    """importe = base × factor × fracción, con la fracción medida sobre una VENTANA de servicio.

    window: FULL_SERVICE | CALENDAR_YEAR | RECURRING_PERIODS(periods) | SERVICE_YEAR | LAST_MONTHS
    count : unit (DAYS_ACTUAL | DAYS_360 | MONTHS_COMPLETE_CALENDAR | MONTHS_AND_DAYS | MONTHS_ROUNDED_BY_DAYS)
            + divisor  (fracción = unidades / divisor)
            o bien months_divisor + days_divisor para MONTHS_AND_DAYS (meses/12 + días/360).
    min_service (opcional): antigüedad total mínima para que exista el derecho.
    """
    hire, end = _hire_and_end(ctx)
    base = ctx.num(p["base"])
    factor = _opt_num(ctx, p.get("factor"), "1")
    start, stop, window_text = resolve_window(p["window"], hire, end)
    count = p["count"]
    unit = count["unit"]
    if unit not in COUNT_UNITS:
        raise SchemaError(f"unidad de conteo desconocida: {unit}")
    details = {"window": window_text, "unit": unit, "base_value": fmt(base), "factor": fmt(factor)}

    minimum = p.get("min_service")
    if minimum:
        total, _ = count_units({"unit": minimum["unit"], **{k: v for k, v in minimum.items() if k not in ("unit", "value")}},
                               hire, end)
        need = ctx.num(minimum["value"])
        details["min_service"] = {"required": fmt(need), "found": fmt(total), "unit": minimum["unit"]}
        if total < need:
            return MechanismResult(
                Decimal(0), f"sin derecho: antigüedad {fmt(total)} < mínimo {fmt(need)} ({minimum['unit']})", details)

    if unit == "MONTHS_AND_DAYS" and "months_divisor" in count:
        st = service_time(start, stop) if stop >= start else None
        months = Decimal(st.total_months) if st else Decimal(0)
        days = Decimal(st.days) if st else Decimal(0)
        m_div, d_div = ctx.num(count["months_divisor"]), ctx.num(count["days_divisor"])
        fraction = months / m_div + days / d_div
        formula = (f"{p['base'] if isinstance(p['base'], str) else 'base'} ({fmt(base)}) × ({fmt(months)}/{fmt(m_div)} + "
                   f"{fmt(days)}/{fmt(d_div)})" + (f" × {fmt(factor)}" if factor != 1 else ""))
        details.update({"months": fmt(months), "days": fmt(days), "fraction": fmt(fraction)})
    else:
        units_value, text = count_units(count, start, stop)
        divisor = ctx.num(count["divisor"])
        fraction = units_value / divisor
        formula = (f"base ({fmt(base)}) × {fmt(units_value)}/{fmt(divisor)}" + (f" × {fmt(factor)}" if factor != 1 else "")
                   + f"  [{text}]")
        details.update({"units": fmt(units_value), "divisor": fmt(divisor), "fraction": fmt(fraction), "count": text})
    return MechanismResult(base * factor * fraction, formula, details)


# -- 2. cantidad (días/meses) por antigüedad: tabla o lineal -----------------------------------
def service_quantity(ctx, p):
    """Cantidad de días (vacaciones, preaviso...) según la antigüedad.

    years_basis: COMPLETED_YEARS (años cumplidos a la terminación) | YEARS_AT_YEAR_END (antigüedad que
                 tendría al 31-dic del año de terminación) | COMPLETED_YEARS_PLUS_PRIOR (suma los años
                 previos informados en employment.prior_years).
    table: [{"min": n, "max": m|null, "value": v}]  (años completos, inclusive) — o —
    table_decimal: [{"up_to": años|null, "value": v}] (antigüedad continua: 'no exceda de 5 años')
    linear: {"base_quantity": q, "per_completed_year": r, "after_years": a, "max_total": t}
    """
    hire, end = _hire_and_end(ctx)
    basis = p.get("years_basis", "COMPLETED_YEARS")
    ref_end = end
    if basis == "YEARS_AT_YEAR_END":
        ref_end = date(end.year, 12, 31)
    st = service_time(hire, ref_end)
    years = st.years
    prior = Decimal(0)
    if basis == "COMPLETED_YEARS_PLUS_PRIOR":
        prior = D(ctx.input_value("employment.prior_years", "0") or "0")
        if p.get("prior_cap") is not None:
            prior = min(prior, ctx.num(p["prior_cap"]))
    offset = int(p.get("year_offset", 0))   # 1 = tabla del año de servicio EN CURSO (años completos + 1)
    years_dec = st.years_decimal() + prior
    details = {"years_basis": basis, "service": st.as_text(), "reference_date": ref_end.isoformat()}
    value = None
    if "table" in p:
        n = int(years + int(prior)) + offset
        for row in p["table"]:
            lo, hi = int(row["min"]), row.get("max")
            if n >= lo and (hi is None or n <= int(hi)):
                value = ctx.num(row["value"])
                details["row"] = row
                break
        details["completed_years"] = n
    elif "table_decimal" in p:
        for row in p["table_decimal"]:
            up = row.get("up_to")
            if up is None or years_dec <= ctx.num(up):
                value = ctx.num(row["value"])
                details["row"] = row
                break
        details["years_decimal"] = fmt(years_dec)
    elif "linear" in p:
        lin = p["linear"]
        after = int(lin.get("after_years", 0))
        extra_years = max(int(years + int(prior)) - after, 0)
        if lin.get("block_years"):
            extra_years = extra_years // int(lin["block_years"])   # p. ej. 1 día por cada 3 años nuevos
        value = ctx.num(lin["base_quantity"]) + ctx.num(lin["per_completed_year"]) * extra_years
        if lin.get("max_total") is not None:
            value = min(value, ctx.num(lin["max_total"]))
        details.update({"completed_years": int(years + int(prior)), "extra_years": extra_years})
    else:
        raise SchemaError("service_quantity requiere table, table_decimal o linear")
    if value is None:
        value = Decimal(0)
    return MechanismResult(value, f"cantidad según antigüedad ({st.as_text()}): {fmt(value)}", details)


# -- 3. indemnización por tramos de antigüedad ------------------------------------------------
def tiered_service_amount(ctx, p):
    """Indemnización por antigüedad con tramos.

    base: importe mensual. unit_days_per_month: si las unidades son días (30) el valor unitario es
    base/30; si son meses (1), base.
    Cada tramo declara CUÁNDO aplica según la antigüedad total y CÓMO suma unidades:
      over_years / up_to_years : el tramo aplica si antigüedad > over_years y ≤ up_to_years
      fixed_units              : unidades fijas
      units_per_year           : unidades por año computable, contados desde `count_from_years`
                                 (por defecto = over_years), con `fraction`:
                                 PRORATA | CEIL (toda fracción = año completo) | FLOOR |
                                 THRESHOLD (+ threshold_months: la fracción suma un año solo si SUPERA ese umbral)
    Los tramos aplicables se SUMAN; para alternativas excluyentes basta con rangos que no se solapen.
    min_units / max_units: límites sobre el total de unidades.
    """
    hire, end = _hire_and_end(ctx)
    st = service_time(hire, end)
    base = ctx.num(p["base"])
    notes = []
    cap_info = None
    spec = p.get("base_cap")
    if spec:
        raw_cap = ctx.input_value(spec["input"])
        if raw_cap in (None, ""):
            notes.append(f"tope de la base NO aplicado: falta el dato '{spec['input']}' (PENDING_VERIFICATION del tope)")
        else:
            cap = D(raw_cap) * ctx.num(spec.get("multiple", 1))
            floor_share = ctx.num(spec.get("floor_share", 0)) * base
            cap = max(cap, floor_share)
            cap_info = {"cap": fmt(cap), "floor_share_of_base": fmt(floor_share)}
            if base > cap:
                base = cap
                cap_info["applied"] = True
    per_month = ctx.num(p.get("unit_days_per_month", 1))
    unit_value = base / per_month
    y = st.years_decimal()
    total = Decimal(0)
    parts = []
    for tier in p["tiers"]:
        over = ctx.num(tier.get("over_years", 0))
        up_to = ctx.num(tier["up_to_years"]) if tier.get("up_to_years") is not None else None
        label = f">{fmt(over)}" + (f" y ≤{fmt(up_to)}" if up_to is not None else "")
        if not (y > over and (up_to is None or y <= up_to)):
            parts.append({"tier": label, "applies": False})
            continue
        if "fixed_units" in tier:
            units = ctx.num(tier["fixed_units"])
            parts.append({"tier": label, "applies": True, "fixed_units": fmt(units)})
        else:
            per_year = ctx.num(tier["units_per_year"])
            count_from = ctx.num(tier["count_from_years"]) if "count_from_years" in tier else over
            fraction = tier.get("fraction", "PRORATA")
            counted = _count_years(fraction, tier, st, y - count_from)
            units = per_year * counted
            parts.append({"tier": label, "applies": True, "units_per_year": fmt(per_year),
                          "fraction_policy": fraction, "counted_years": fmt(counted), "units": fmt(units)})
        total += units
    raw_total = total
    if p.get("min_units") is not None:
        total = max(total, ctx.num(p["min_units"]))
    capped = False
    if p.get("max_units") is not None:
        cap = ctx.num(p["max_units"])
        if total > cap:
            total, capped = cap, True
    amount = total * unit_value
    details = {"service": st.as_text(), "base_value": fmt(base), "unit_value": fmt(unit_value), "tiers": parts,
               "units_raw": fmt(raw_total), "units": fmt(total), "cap_applied": capped}
    if cap_info:
        details["base_cap"] = cap_info
    if notes:
        details["warnings"] = notes
    formula = f"{fmt(total)} unidades × {fmt(unit_value)} (antigüedad {st.as_text()})"
    return MechanismResult(amount, formula, details)


def _count_years(policy, tier, st, span):
    """Años computables (`span` = años de servicio dentro del tramo) según la política de fracción."""
    if policy == "PRORATA":
        return span
    whole = Decimal(math.floor(span))
    has_fraction = span > whole
    if policy == "FLOOR":
        return whole
    if policy == "CEIL":
        return whole + (1 if has_fraction else 0)
    if policy == "THRESHOLD":
        if not has_fraction:
            return whole
        return whole + (1 if st.exceeds_fraction(int(tier["threshold_months"])) else 0)
    raise SchemaError(f"política de fracción desconocida: {policy!r}")


# -- 4. salarios del tiempo restante de un contrato a plazo -----------------------------------
def remaining_term_amount(ctx, p):
    """Contrato a plazo/obra: valor de lo que faltaba para cumplir el plazo.

    unit: DAYS_360  → base/30 × días comerciales restantes
          MONTHS_AND_DAYS → base × (meses + días/30)
    multiplier: por unidad de tiempo restante (1 por defecto; 1,5 en indemnizaciones por mes).
    min_days: piso en días (base/30 × min_days). max_months: tope en meses de base.
    """
    hire, end = _hire_and_end(ctx)
    term_end = _date_input(ctx, p.get("end_input", "employment.contract_end_date"))
    base = ctx.num(p["base"])
    multiplier = _opt_num(ctx, p.get("multiplier"), "1")
    if term_end <= end:
        return MechanismResult(Decimal(0), "el plazo ya se había cumplido", {"contract_end": term_end.isoformat()})
    start = end + timedelta(days=1)
    unit = p.get("unit", "DAYS_360")
    if unit == "DAYS_360":
        days = Decimal(commercial_days_360(start, term_end))
        months_equiv = days / 30
        amount = base / 30 * days * multiplier
        text = f"{fmt(days)} días restantes (base 360)"
    elif unit == "MONTHS_AND_DAYS":
        st = service_time(start, term_end)
        months_equiv = Decimal(st.total_months) + Decimal(st.days) / 30
        amount = base * months_equiv * multiplier
        text = f"{st.total_months} meses y {st.days} días restantes"
    else:
        raise SchemaError(f"unit desconocida en remaining_term_amount: {unit}")
    floor_days = ctx.num(p["min_days"]) if p.get("min_days") is not None else None
    floor_applied = False
    if floor_days is not None and amount < base / 30 * floor_days * multiplier:
        amount, floor_applied = base / 30 * floor_days * multiplier, True
    cap_applied = False
    if p.get("max_months") is not None:
        cap = base * ctx.num(p["max_months"])
        if amount > cap:
            amount, cap_applied = cap, True
    details = {"contract_end": term_end.isoformat(), "remaining": text, "multiplier": fmt(multiplier),
               "floor_applied": floor_applied, "cap_applied": cap_applied, "months_equivalent": fmt(months_equiv)}
    return MechanismResult(amount, f"base ({fmt(base)}) × {text} × {fmt(multiplier)}", details)


# -- 5. valor derivado de un historial mensual -------------------------------------------------
def history_value(ctx, p):
    """Toma un valor mensual de un historial informado (lista de {"month": "AAAA-MM", "amount": "..."}).

    method: LAST | AVERAGE | MAX | AVERAGE_IF_VARIED (último valor si no varió en `vary_months`
            meses; si varió, promedio de la ventana)
    window_months: meses hacia atrás desde el mes de terminación (inclusive).
    fallback: operando que se usa si no hay historial (se registra en el detalle).
    """
    _, end = _hire_and_end(ctx)
    raw = ctx.input_value(p["history_input"])
    entries = []
    for row in raw or []:
        try:
            year, month = (int(x) for x in str(row["month"]).split("-"))
            amount = D(row["amount"])
        except (KeyError, ValueError, TypeError) as exc:
            raise InputValidationError(f"{p['history_input']}: fila inválida {row!r} (se espera month AAAA-MM y amount)") from exc
        entries.append((year * 12 + month - 1, str(row["month"]), amount))
    end_idx = end.year * 12 + end.month - 1
    window = int(p.get("window_months", 12))
    if p.get("window"):     # ventana jurídica (p. ej. el semestre en curso), en vez de N meses hacia atrás
        hire, _ = _hire_and_end(ctx)
        w_start, w_end, _text = resolve_window(p["window"], hire, end)
        lo, hi = w_start.year * 12 + w_start.month - 1, w_end.year * 12 + w_end.month - 1
        window_rows = sorted([e for e in entries if lo <= e[0] <= hi])
    else:
        window_rows = sorted([e for e in entries if end_idx - window < e[0] <= end_idx])
    if not window_rows:
        if "fallback" not in p:
            raise MissingInputError(f"falta el historial '{p['history_input']}' (o su valor de respaldo)")
        value = ctx.num(p["fallback"])
        return MechanismResult(value, f"sin historial: se usa el valor de respaldo ({fmt(value)})",
                               {"history_input": p["history_input"], "source": "FALLBACK", "months_used": 0})
    amounts = [r[2] for r in window_rows]
    method = p["method"]
    if method == "LAST":
        value = amounts[-1]
    elif method == "AVERAGE":
        value = sum(amounts, Decimal(0)) / len(amounts)
    elif method == "MAX":
        value = max(amounts)
    elif method == "SUM":
        value = sum(amounts, Decimal(0))
    elif method == "AVERAGE_IF_VARIED":
        vary = int(p.get("vary_months", 3))
        tail = amounts[-vary:]
        varied = len(set(tail)) > 1
        value = (sum(amounts, Decimal(0)) / len(amounts)) if varied else amounts[-1]
    else:
        raise SchemaError(f"método de historial desconocido: {method!r}")
    details = {"history_input": p["history_input"], "method": method, "window_months": window,
               "months_used": len(window_rows), "months": [r[1] for r in window_rows],
               "values": [fmt(a) for a in amounts]}
    return MechanismResult(value, f"{method} de {len(window_rows)} meses del historial = {fmt(value)}", details)


# -- 6. cantidades ajustadas (sumas/restas informadas) -----------------------------------------
def adjusted_quantity(ctx, p):
    """cantidad = max(mínimo, base + Σ add − Σ subtract). Sirve p. ej. para días de vacaciones
    pendientes = devengados − disfrutados + adquiridos no pagados."""
    quantity = ctx.num(p["quantity"])
    adds = [ctx.num(x) for x in p.get("add", [])]
    subs = [ctx.num(x) for x in p.get("subtract", [])]
    raw = quantity + sum(adds, Decimal(0)) - sum(subs, Decimal(0))
    floor = ctx.num(p["min"]) if p.get("min") is not None else Decimal(0)
    cap = ctx.num(p["max"]) if p.get("max") is not None else None
    value = max(raw, floor)
    if cap is not None:
        value = min(value, cap)
    return MechanismResult(
        value, f"{fmt(quantity)} + {fmt(sum(adds, Decimal(0)))} − {fmt(sum(subs, Decimal(0)))} → {fmt(value)}",
        {"quantity": fmt(quantity), "added": [fmt(a) for a in adds], "subtracted": [fmt(s) for s in subs],
         "raw": fmt(raw), "floor": fmt(floor)})


# -- 7. horas extra y recargos -----------------------------------------------------------------
def hours_at_multipliers(ctx, p):
    """Horas × valor-hora × multiplicador, por categoría declarada en datos.

    hourly: {"monthly_base": operando, "hours_per_month": operando}  o {"daily_base": op, "hours_per_day": op}
            → valor hora = monthly_base / hours_per_month.
    categories: [{"key": "extra_diurna", "hours_input": "time.hours_extra_diurna",
                  "components": [operando, ...]}]   multiplicador = Σ componentes (p. ej. 1 + 0,25).
                 o con "tiers": [{"up_to_hours": 9, "multiplier": 2}, {"multiplier": 3}] sobre el
                 historial semanal de `weekly_hours_input`.
    subtract_base: si true, descuenta 1 × valor hora (cuando el salario mensual ya paga las horas ordinarias
                   y solo se debe el RECARGO). Por defecto false: se paga el multiplicador completo.
    """
    hourly = p["hourly"]
    if "monthly_base" in hourly:
        base = ctx.num(hourly["monthly_base"])
        hours_month = ctx.num(hourly["hours_per_month"])
        hour_value = base / hours_month
        hv_text = f"{fmt(base)} / {fmt(hours_month)}"
    elif "hourly_rate" in hourly:
        hour_value = ctx.num(hourly["hourly_rate"])
        hv_text = f"tarifa horaria {fmt(hour_value)}"
    elif "daily_base" in hourly:
        base = ctx.num(hourly["daily_base"])
        hours_day = ctx.num(hourly["hours_per_day"])
        hour_value = base / hours_day
        hv_text = f"{fmt(base)} / {fmt(hours_day)}"
    else:
        raise SchemaError("hourly requiere monthly_base+hours_per_month o daily_base+hours_per_day")
    total = Decimal(0)
    cats = []
    subtract = bool(p.get("subtract_base", False))
    for cat in p["categories"]:
        if "tiers" in cat:
            weeks = ctx.input_value(cat["weekly_hours_input"]) or []
            amount_cat, hours_cat, tier_rows = Decimal(0), Decimal(0), []
            for week in weeks:
                remaining = D(week)
                hours_cat += remaining
                previous = Decimal(0)
                for tier in cat["tiers"]:
                    limit = ctx.num(tier["up_to_hours"]) if tier.get("up_to_hours") is not None else None
                    portion = remaining if limit is None else min(remaining, max(limit - previous, Decimal(0)))
                    mult = ctx.num(tier["multiplier"])
                    amount_cat += portion * hour_value * (mult - (1 if subtract else 0))
                    tier_rows.append({"week_hours": fmt(D(week)), "portion": fmt(portion), "multiplier": fmt(mult)})
                    remaining -= portion
                    previous = limit if limit is not None else previous
                    if remaining <= 0:
                        break
            total += amount_cat
            cats.append({"key": cat["key"], "hours": fmt(hours_cat), "tiers": tier_rows, "amount": fmt(amount_cat)})
            continue
        hours = D(ctx.input_value(cat["hours_input"], "0") or "0")
        if hours < 0:
            raise InputValidationError(f"{cat['hours_input']}: horas negativas")
        mult = sum((ctx.num(c) for c in cat["components"]), Decimal(0))
        effective = mult - (1 if subtract else 0)
        amount_cat = hours * hour_value * effective
        total += amount_cat
        cats.append({"key": cat["key"], "hours": fmt(hours), "multiplier": fmt(mult), "amount": fmt(amount_cat)})
    used = [c for c in cats if c["hours"] != "0"]
    return MechanismResult(total, f"valor hora ({hv_text} = {fmt(hour_value)}) × horas × multiplicador por categoría",
                           {"hour_value": fmt(hour_value), "categories": used or cats})


def date_measure(ctx, p):
    """Cantidad derivada de la fecha de terminación (no de dinero). measures:
       DAYS_REMAINING_IN_MONTH   días que faltan hasta el último día del mes (integración del mes de despido)
       COMMERCIAL_DAYS_IN_MONTH  días del mes hasta la terminación en base 30 (fin de mes = 30)
       SERVICE_MONTHS_AND_DAYS   antigüedad total en meses + días/30
       WINDOW_UNITS              unidades de tiempo (count) de una ventana jurídica (window)"""
    from .temporal import month_end
    _, end = _hire_and_end(ctx)
    measure = p["measure"]
    if measure == "DAYS_REMAINING_IN_MONTH":
        value = Decimal((month_end(end) - end).days)
        text = f"{fmt(value)} días hasta el fin de mes ({end})"
    elif measure == "COMMERCIAL_DAYS_IN_MONTH":
        value = Decimal(30 if (month_end(end) == end or end.day > 30) else end.day)
        text = f"{fmt(value)} días comerciales del mes hasta {end}"
    elif measure == "WINDOW_UNITS":
        hire, _ = _hire_and_end(ctx)
        start, stop, window_text = resolve_window(p["window"], hire, end)
        value, count_text = count_units(p["count"], start, stop)
        text = f"{count_text} en la ventana {window_text}"
    elif measure == "SERVICE_MONTHS_AND_DAYS":
        hire, _ = _hire_and_end(ctx)
        st = service_time(hire, end)
        value = Decimal(st.total_months) + Decimal(st.days) / 30
        text = f"{st.total_months} meses y {st.days} días"
    else:
        raise SchemaError(f"measure desconocida: {measure!r}")
    return MechanismResult(value, text, {"measure": measure})


def accrued_in_window(ctx, p):
    """Σ de remuneraciones DEVENGADAS en una ventana (p. ej. la fracción del semestre trabajada, art. 123 LCT
    Argentina; el año calendario del décimo tercero de Ecuador).
    Si hay historial mensual informado con meses dentro de la ventana, se SUMA. Si no, se usa el
    respaldo: importe mensual × (meses + días/30) de la ventana."""
    hire, end = _hire_and_end(ctx)
    start, stop, window_text = resolve_window(p["window"], hire, end)
    lo, hi = start.year * 12 + start.month - 1, stop.year * 12 + stop.month - 1
    rows = []
    for row in ctx.input_value(p["history_input"]) or []:
        try:
            y, m = (int(x) for x in str(row["month"]).split("-"))
            rows.append((y * 12 + m - 1, str(row["month"]), D(row["amount"])))
        except (KeyError, ValueError, TypeError) as exc:
            raise InputValidationError(f"{p['history_input']}: fila inválida {row!r}") from exc
    in_window = sorted(r for r in rows if lo <= r[0] <= hi)
    if in_window:
        total = sum((r[2] for r in in_window), Decimal(0))
        return MechanismResult(total, f"Σ devengado en la ventana ({window_text}) = {fmt(total)}",
                               {"window": window_text, "source": "HISTORY", "months": [r[1] for r in in_window],
                                "values": [fmt(r[2]) for r in in_window]})
    monthly = ctx.num(p["fallback_monthly"])
    st = service_time(start, stop) if stop >= start else None
    equiv = (Decimal(st.total_months) + Decimal(st.days) / 30) if st else Decimal(0)
    return MechanismResult(monthly * equiv, f"{fmt(monthly)} × {fmt(equiv)} meses de la ventana ({window_text})",
                           {"window": window_text, "source": "FALLBACK_MONTHLY", "monthly": fmt(monthly),
                            "months_equivalent": fmt(equiv),
                            "warnings": [f"sin historial mensual en '{p['history_input']}': se supuso remuneración constante"]})


TERMINATION_MECHANISMS = {
    "date_measure": (date_measure, ("measure",)),
    "accrued_in_window": (accrued_in_window, ("window", "history_input", "fallback_monthly")),
    "service_period_proration": (service_period_proration, ("base", "window", "count")),
    "service_quantity": (service_quantity, ()),
    "tiered_service_amount": (tiered_service_amount, ("base", "tiers")),
    "remaining_term_amount": (remaining_term_amount, ("base",)),
    "history_value": (history_value, ("history_input", "method")),
    "adjusted_quantity": (adjusted_quantity, ("quantity",)),
    "hours_at_multipliers": (hours_at_multipliers, ("hourly", "categories")),
}
