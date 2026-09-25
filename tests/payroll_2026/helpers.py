"""Utilidades de prueba. El cálculo esperado se hace AQUÍ con Decimal, de forma independiente
de los mecanismos del motor (no se reutiliza código del motor para calcular lo esperado)."""

from decimal import Decimal, ROUND_HALF_UP

from payroll_engine.run import PayrollEngine

SMMLV = Decimal("1750905")
CENT = Decimal("0.01")


def q(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def co_payload(salary="3000000", worked="30", period=("2026-09-01", "2026-09-30"), salary_type="ORDINARY",
               time=None, amounts=None, exonerated=True, arl_class="I"):
    payload = {
        "country": "CO", "jurisdictions": ["NATIONAL"], "run_type": "REGULAR",
        "period": {"start": period[0], "end": period[1]},
        "employee": {"id": "E-1", "name": "Empleado de prueba"},
        "employer": {"exonerated_art_114_1": exonerated, "arl_class": arl_class},
        "employment": {"salary_type": salary_type, "monthly_salary": str(salary), "contract_type": "INDEFINITE"},
        "time": {"worked_days": str(worked)},
        "amounts": {},
    }
    payload["time"].update(time or {})
    payload["amounts"].update(amounts or {})
    return payload


def run_co(salary="3000000", **kwargs):
    return PayrollEngine().run(co_payload(salary, **kwargs))


def amount(run, concept):
    line = run.line(concept)
    return None if line is None else line["amount"]
