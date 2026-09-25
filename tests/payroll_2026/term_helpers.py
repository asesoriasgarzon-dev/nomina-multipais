"""Utilidades de las pruebas de terminación, horas extra y series. Los valores esperados se calculan AQUÍ con
Decimal a partir del texto de la norma, sin reutilizar los mecanismos del motor."""

from decimal import Decimal, ROUND_HALF_UP

from payroll_engine.run import PayrollEngine

CENT = Decimal("0.01")


def q(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def D(value):
    return Decimal(str(value))


def term(country, hire, end, cause, salary="1000", contract="INDEFINITE", *, employment=None, termination=None,
         amounts=None, extra=None, pay_date=None):
    """Corrida TERMINATION mínima. `extra` agrega claves de primer nivel (salary_history, vacation_history...)."""
    payload = {
        "country": country, "jurisdictions": ["NATIONAL"], "run_type": "TERMINATION", "termination_date": end,
        "employment": {"hire_date": hire, "monthly_salary": str(salary), "contract_type": contract},
        "termination": {"cause": cause},
        "amounts": {},
    }
    if pay_date:
        payload["pay_date"] = pay_date
    payload["employment"].update(employment or {})
    payload["termination"].update(termination or {})
    payload["amounts"].update(amounts or {})
    payload.update(extra or {})
    return PayrollEngine().run(payload)


def lines(run):
    """concepto -> importe (solo líneas con dinero: excluye INFO)."""
    return {l["concept"]: l["amount"] for l in run.result["lines"] if l["role"] != "INFO"}


def info(run, concept):
    for l in run.result["lines"]:
        if l["concept"] == concept:
            return l["amount"]
    return None


def line_trace(run, concept):
    return next(l for l in run.trace["lines"] if l["concept"] == concept)


def monthly(country, salary, period, *, time=None, amounts=None, employment=None, extra=None):
    payload = {
        "country": country, "jurisdictions": ["NATIONAL"], "run_type": "REGULAR",
        "period": {"start": period[0], "end": period[1]},
        "employment": {"monthly_salary": str(salary)}, "time": {"worked_days": "30"}, "amounts": {},
    }
    payload["time"].update(time or {})
    payload["amounts"].update(amounts or {})
    payload["employment"].update(employment or {})
    payload.update(extra or {})
    return PayrollEngine().run(payload)
