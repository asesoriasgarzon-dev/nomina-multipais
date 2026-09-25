"""Motores de MX, PE, CL, BR, AR y EC sobre el motor normativo (payroll_engine).

Solo ADAPTADORES: traducen las novedades del formulario heredado a la entrada del
motor. No contienen fórmulas ni tasas: todo está en config/payroll/<PAIS>/2026.
La liquidación (corrida TERMINATION) también corre sobre el motor normativo.
El formulario y los ejemplos DEMO vienen de countries/<pais>.py (sin reglas legales)."""

from decimal import Decimal

from payroll_engine.errors import InputValidationError
from payroll_engine.legacy_adapter import period_bounds, to_legacy_result
from payroll_engine.run import PayrollEngine as NormativeEngine

from .base import PayrollEngine

from .argentina import ArgentinaForm
from .brasil import BrasilForm
from .chile import ChileForm
from .ecuador import EcuadorForm
from .mexico import MexicoForm
from .peru import PeruForm


class NormativeLiquidationMixin:
    """`liquidar` sobre el motor normativo (corrida TERMINATION). Solo adapta la entrada del formulario y la
    salida; las reglas viven en config/payroll/<PAIS>/2026/rules_termination.json."""

    COUNTRY = None

    def liquidar(self, empleado, datos, config):
        from payroll_engine.legacy_adapter import termination_payload, to_liquidation_result
        from payroll_engine.loader import load_country
        ruleset = load_country(self.COUNTRY)
        payload = termination_payload(self.COUNTRY, ruleset.manifest, empleado, datos)
        run = NormativeEngine().run(payload)
        result = to_liquidation_result(run)
        result["_run"] = run
        return result


def _text(value, default="0"):
    if value in (None, ""):
        return default
    return str(value).strip()


def make_normative_engine(form_cls, country, amount_map, time_map, derive=None, name=None):
    class _Engine(NormativeLiquidationMixin, form_cls, PayrollEngine):
        COUNTRY = country

        def build_payload(self, empleado, novedades, periodo):
            start, end = period_bounds(periodo)
            time = {key: _text(novedades.get(form_key), "30" if key == "worked_days" else "0")
                    for form_key, key in time_map.items()}
            if derive:
                derive(time)
            return {
                "country": country, "jurisdictions": ["NATIONAL"], "run_type": "REGULAR",
                "period": {"start": start, "end": end},
                "employee": {"id": _text(empleado.get("identificacion"), ""), "name": _text(empleado.get("nombre"), "")},
                "employment": {"monthly_salary": _text(empleado.get("salario_contrato"), "0")},
                "time": time,
                "amounts": {code: _text(novedades.get(form_key)) for form_key, code in amount_map.items()},
            }

        def calcular_periodo(self, empleado, novedades, config, periodo):
            run = NormativeEngine().run(self.build_payload(empleado, novedades, periodo))
            result = to_legacy_result(run)
            result["_run"] = run
            return result

        def calcular(self, empleado, novedades, config):
            periodo = novedades.get("_periodo")
            if not periodo:
                raise InputValidationError("el motor normativo necesita el período (AAAA-MM)")
            return self.calcular_periodo(empleado, novedades, config, periodo)

    _Engine.__name__ = _Engine.__qualname__ = name or f"{country}NormativeEngine"
    return _Engine


def _mx_derive(time):
    time["paid_days"] = str(max(Decimal(time["worked_days"]) - Decimal(time["incapacity_days"]), Decimal(0)))


MexicoNormativeEngine = make_normative_engine(
    MexicoForm, "MX",
    {"bonos_percepciones": "BONUS", "descuento_infonavit_credito": "HOUSING_CREDIT",
     "prestamos_descuentos": "LOANS", "isr_retenido": "ISR_WITHHOLDING"},
    {"dias_trabajados": "worked_days", "dias_incapacidad": "incapacity_days"}, derive=_mx_derive)
PeruNormativeEngine = make_normative_engine(
    PeruForm, "PE",
    {"bonos_comisiones": "BONUS", "asignacion_familiar": "FAMILY_ALLOWANCE", "prestamos_avances": "LOANS",
     "retencion_impuesto_renta": "INCOME_TAX_5TH"}, {"dias_trabajados": "worked_days"})
ChileNormativeEngine = make_normative_engine(
    ChileForm, "CL",
    {"bonos_comisiones": "BONUS", "gratificacion_legal": "LEGAL_GRATIFICATION", "prestamos_avances": "LOANS",
     "retencion_impuesto_renta": "SINGLE_TAX"}, {"dias_trabajados": "worked_days"})
BrasilNormativeEngine = make_normative_engine(
    BrasilForm, "BR",
    {"bonos_comisiones": "BONUS", "prestamos_avances": "LOANS", "retencion_impuesto_renta": "IRRF"},
    {"dias_trabajados": "worked_days"})
ArgentinaNormativeEngine = make_normative_engine(
    ArgentinaForm, "AR",
    {"bonos_comisiones": "BONUS", "prestamos_avances": "LOANS", "retencion_impuesto_renta": "INCOME_TAX_4TH"},
    {"dias_trabajados": "worked_days"})
EcuadorNormativeEngine = make_normative_engine(
    EcuadorForm, "EC",
    {"bonos_comisiones": "BONUS", "prestamos_avances": "LOANS", "retencion_impuesto_renta": "INCOME_TAX"},
    {"dias_trabajados": "worked_days"})
