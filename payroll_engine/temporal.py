"""Aritmética de fechas laborales, sin ninguna regla de país.

Todo lo que el derecho laboral llama "antigüedad", "semestre", "fracción de mes" o "año de
servicio" se reduce a unas pocas operaciones de calendario. Aquí viven esas operaciones; QUÉ
ventana o QUÉ conteo usa cada norma lo declara el JSON del país (window/count), nunca este módulo.

Convenciones (todas explícitas y registradas en la auditoría):
  - Los rangos son INCLUSIVOS en ambos extremos.
  - Antigüedad por aniversarios: años/meses completos contados desde la fecha de inicio; los días
    restantes son días naturales.
  - COMMERCIAL_360: mes comercial de 30 días (el último día de cualquier mes cuenta como 30).
"""

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from .errors import InputValidationError, SchemaError


def add_months(d, months):
    """Suma meses calendario recortando el día al último del mes destino (31-ene + 1 mes = 28/29-feb)."""
    total = d.year * 12 + (d.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def is_month_end(d):
    return d.day == calendar.monthrange(d.year, d.month)[1]


def month_end(d):
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def days_inclusive(start, end):
    return (end - start).days + 1


@dataclass(frozen=True)
class ServiceTime:
    """Tiempo transcurrido entre start y end (inclusive), por aniversarios."""
    start: date
    end: date
    years: int
    months: int
    days: int

    @property
    def total_months(self):
        return self.years * 12 + self.months

    def years_decimal(self, days_per_month=30):
        """Años como Decimal: años + meses/12 + días/(12*días_por_mes)."""
        return (Decimal(self.years) + Decimal(self.months) / 12
                + Decimal(self.days) / (12 * Decimal(days_per_month)))

    def exceeds_fraction(self, months_threshold):
        """True si la fracción de año (meses, días) SUPERA `months_threshold` meses
        (superior a 6 meses = 6 meses y un día o más)."""
        return self.months > months_threshold or (self.months == months_threshold and self.days > 0)

    def as_text(self):
        return f"{self.years} años, {self.months} meses, {self.days} días"


def service_time(start, end):
    if end < start:
        raise InputValidationError(f"la fecha final {end} es anterior a la inicial {start}")
    stop = end + timedelta(days=1)          # exclusivo
    years = 0
    while add_months(start, 12 * (years + 1)) <= stop:
        years += 1
    months = 0
    while add_months(start, 12 * years + months + 1) <= stop:
        months += 1
    anchor = add_months(start, 12 * years + months)
    return ServiceTime(start, end, years, months, (stop - anchor).days)


def commercial_days_360(start, end):
    """Días entre start y end INCLUSIVE en base 360 (meses de 30; fin de mes = 30)."""
    if end < start:
        raise InputValidationError(f"la fecha final {end} es anterior a la inicial {start}")
    d1 = min(start.day, 30)
    d2 = 30 if is_month_end(end) or end.day == 31 else end.day
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1) + 1


def complete_calendar_months(start, end):
    """Meses calendario COMPLETOS dentro de [start, end]: el primer mes solo cuenta si start es día 1
    y el último solo si end es fin de mes."""
    if end < start:
        return 0
    first = start.year * 12 + start.month - 1
    last = end.year * 12 + end.month - 1
    count = last - first + 1
    if start.day != 1:
        count -= 1
    if not is_month_end(end):
        count -= 1
    return max(count, 0)


# -- ventanas -------------------------------------------------------------------------------
WINDOW_TYPES = ("FULL_SERVICE", "CALENDAR_YEAR", "RECURRING_PERIODS", "SERVICE_YEAR", "LAST_MONTHS")


def _md(text):
    """'MM-DD' o 'MM-END' (último día del mes, válido en años bisiestos)."""
    try:
        month, day = text.split("-")
        month = int(month)
        day = 0 if day.upper() == "END" else int(day)
        date(2001, month, day or 1)
    except (ValueError, AttributeError) as exc:
        raise SchemaError(f"fecha MM-DD inválida en la ventana: {text!r}") from exc
    return month, day


def _period_date(year, md):
    month, day = md
    return month_end(date(year, month, 1)) if day == 0 else date(year, month, day)


def resolve_window(spec, hire, end):
    """Devuelve (inicio, fin, descripción). `end` es la fecha de terminación (o ancla).
    La ventana se recorta siempre por la fecha de ingreso."""
    wtype = spec.get("type")
    if wtype == "FULL_SERVICE":
        start = hire
    elif wtype == "CALENDAR_YEAR":
        start = date(end.year, 1, 1)
    elif wtype == "RECURRING_PERIODS":
        start = None
        for year in (end.year, end.year - 1):
            for period in spec["periods"]:
                sm, sd = _md(period["start"])
                em, ed = _md(period["end"])
                p_start = _period_date(year, (sm, sd))
                p_end = _period_date(year if (em, 99 if ed == 0 else ed) >= (sm, sd) else year + 1, (em, ed))
                if p_start <= end <= p_end:
                    start = p_start
                    break
            if start:
                break
        if start is None:
            raise SchemaError(f"la fecha {end} no cae en ningún período de la ventana RECURRING_PERIODS")
    elif wtype == "SERVICE_YEAR":
        years = service_time(hire, end).years
        start = add_months(hire, 12 * years)
    elif wtype == "LAST_MONTHS":
        start = add_months(end + timedelta(days=1), -int(spec["months"]))
    else:
        raise SchemaError(f"tipo de ventana desconocido: {wtype!r}; permitidos {WINDOW_TYPES}")
    start = max(start, hire)
    if start > end:
        return start, end, f"{wtype}: vacía ({start} > {end})"
    return start, end, f"{wtype}: {start} .. {end}"


COUNT_UNITS = ("DAYS_ACTUAL", "DAYS_360", "MONTHS_COMPLETE_CALENDAR", "MONTHS_AND_DAYS", "MONTHS_ROUNDED_BY_DAYS",
               "MONTHS_WITH_MIN_DAYS")


def count_units(spec, start, end):
    """Cuenta unidades de tiempo en [start, end]. Devuelve (Decimal, texto). Para MONTHS_AND_DAYS el
    valor es meses + días/`days_per_month` (fracción de mes por treintavos, por defecto)."""
    unit = spec.get("unit")
    if end < start:
        return Decimal(0), "ventana vacía"
    if unit == "DAYS_ACTUAL":
        n = days_inclusive(start, end)
        return Decimal(n), f"{n} días"
    if unit == "DAYS_360":
        n = commercial_days_360(start, end)
        return Decimal(n), f"{n} días (base 360)"
    if unit == "MONTHS_COMPLETE_CALENDAR":
        n = complete_calendar_months(start, end)
        return Decimal(n), f"{n} meses calendario completos"
    if unit == "MONTHS_AND_DAYS":
        st = service_time(start, end)
        per = Decimal(spec.get("days_per_month", 30))
        value = Decimal(st.total_months) + Decimal(st.days) / per
        return value, f"{st.total_months} meses y {st.days} días (días/{per})"
    if unit == "MONTHS_ROUNDED_BY_DAYS":
        st = service_time(start, end)
        threshold = int(spec["day_threshold"])
        months = st.total_months + (1 if st.days >= threshold else 0)
        return Decimal(months), (f"{st.total_months} meses + {st.days} días "
                                 f"({'suma' if st.days >= threshold else 'no suma'} un mes: umbral {threshold} días)")
    if unit == "MONTHS_WITH_MIN_DAYS":
        return months_with_min_days(start, end, int(spec["day_threshold"]))
    raise SchemaError(f"unidad de conteo desconocida: {unit!r}; permitidas {COUNT_UNITS}")


def months_with_min_days(start, end, threshold):
    """Meses CALENDARIO del rango en los que se trabajaron `threshold` días o más (p. ej. 13.º de Brasil:
    la fracción igual o superior a 15 días de trabajo se cuenta como mes integral, mes por mes)."""
    count, rows = 0, []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        first = date(year, month, 1)
        last = month_end(first)
        worked = days_inclusive(max(start, first), min(end, last))
        if worked >= threshold:
            count += 1
        rows.append(f"{year}-{month:02d}:{worked}d")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return Decimal(count), f"{count} meses con ≥{threshold} días trabajados ({', '.join(rows)})"
