"""Colombia sobre el motor normativo (payroll_engine + config/payroll/CO/2026).

Este módulo es solo un ADAPTADOR de la interfaz de la app: traduce las novedades del
formulario a la entrada del motor y el PayrollRun a la estructura heredada. NO
contiene reglas legales ni fórmulas: todo está en los datos normativos. La
liquidación (TERMINATION) también corre sobre el motor normativo."""

from payroll_engine.errors import InputValidationError
from payroll_engine.legacy_adapter import period_bounds, to_legacy_result
from payroll_engine.run import PayrollEngine as NormativeEngine

from .base import PayrollEngine
from .colombia import ColombiaForm
from .normative_engines import NormativeLiquidationMixin

LEGACY_ORDER = {
    "devengado": ["valor_salario_devengado", "incapacidad_empresa", "incapacidad_valor_eps", "valor_vac_disfrutadas",
                  "valor_vac_compensadas", "bonos_comisiones", "bonificaciones_no_salariales", "ajuste_trm",
                  "auxilio_transporte"],
    "deducciones": ["aporte_salud_empleado", "aporte_pension_empleado", "aporte_fsp_empleado", "retencion_fuente",
                    "descuento_afc", "aportes_voluntarios_pension", "prestamos_avances"],
    "aportes_patronales": ["salud_empleador", "pension_empleador", "arl", "caja_compensacion", "sena", "icbf"],
    "provisiones": ["vacaciones", "prima", "cesantias", "intereses_cesantias"],
}

AMOUNT_MAP = {
    "incapacidad_valor_eps": "INCAPACITY_EPS", "bonos_comisiones": "BONUS_SALARY",
    "bonificaciones_no_salariales": "BONUS_NON_SALARY", "ajuste_trm": "TRM_ADJUSTMENT",
    "retencion_fuente": "WITHHOLDING_TAX", "descuento_afc": "AFC_DEDUCTION",
    "aportes_voluntarios_pension": "VOLUNTARY_PENSION", "prestamos_avances": "LOANS_ADVANCES",
}


def _text(value, default="0"):
    if value in (None, ""):
        return default
    return str(value).strip()


class ColombiaNormativeEngine(NormativeLiquidationMixin, ColombiaForm, PayrollEngine):
    """Hereda formulario y ejemplos; el cálculo mensual y la liquidación corren sobre el motor normativo."""

    COUNTRY = "CO"

    NOVEDADES_CAMPOS = [("tipo_salario", "tipo_salario", "select:ORDINARY|INTEGRAL", "ORDINARY")] \
        + ColombiaForm.NOVEDADES_CAMPOS

    def build_payload(self, empleado, novedades, periodo):
        start, end = period_bounds(periodo)
        worked = _text(novedades.get("dias_trabajados"), "30")
        incap = _text(novedades.get("incapacidad_dias_empresa"))
        vac = _text(novedades.get("vac_disfrutadas_dias"))
        vac_nh = _text(novedades.get("vac_no_habiles_dias"))
        vac_comp = _text(novedades.get("vac_compensadas_dias"))
        try:
            from decimal import Decimal
            vacation_days = str(Decimal(vac) + Decimal(vac_nh))
            accounted = str(Decimal(worked) + Decimal(incap) + Decimal(vacation_days))
        except Exception as exc:
            raise InputValidationError("los días deben ser numéricos") from exc
        amounts = {code: _text(novedades.get(key)) for key, code in AMOUNT_MAP.items()}
        return {
            "country": "CO", "jurisdictions": ["NATIONAL"], "run_type": "REGULAR",
            "period": {"start": start, "end": end},
            "employee": {"id": _text(empleado.get("identificacion"), ""), "name": _text(empleado.get("nombre"), "")},
            "employer": {"exonerated_art_114_1": bool(novedades.get("exonerado_aportes", True)), "arl_class": "I"},
            "employment": {"salary_type": _text(novedades.get("tipo_salario"), "ORDINARY"),
                           "monthly_salary": _text(empleado.get("salario_contrato"), "0"),
                           "contract_type": "INDEFINITE"},
            "time": {"worked_days": worked, "incapacity_employer_days": incap, "vacation_days": vacation_days,
                     "vacation_compensated_days": vac_comp, "accounted_days": accounted},
            "amounts": amounts,
        }

    def calcular_periodo(self, empleado, novedades, config, periodo):
        payload = self.build_payload(empleado, novedades, periodo)
        run = NormativeEngine().run(payload)
        result = to_legacy_result(run, LEGACY_ORDER)
        result["_run"] = run
        return result

    def calcular(self, empleado, novedades, config):
        periodo = novedades.get("_periodo")
        if not periodo:
            raise InputValidationError("el motor normativo necesita el período (AAAA-MM)")
        return self.calcular_periodo(empleado, novedades, config, periodo)
