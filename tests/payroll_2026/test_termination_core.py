"""Mecanismos de terminación del núcleo, probados con un paquete SINTÉTICO 'ZZ' (cifras ficticias): prueban el mecanismo,
no una norma. Garantizan que las reglas de terminación son datos y que el núcleo no depende de ningún país."""

import copy
from decimal import Decimal

import pytest

from payroll_engine.errors import (CapabilityError, InputValidationError, MissingInputError, SchemaError)
from payroll_engine.loader import RuleSetData
from payroll_engine.run import PayrollEngine, reproduce

from .term_helpers import D, q

SRC = {"status": "NOT_APPLICABLE"}
VER = {"interpretation_status": "UNREVIEWED", "professional_validation": "PENDING"}
ROUNDING = {"calculation_precision": 28, "currency_precision": 2, "rounding_mode": "ROUND_HALF_UP"}
T = ["TERMINATION"]


def rule(key, concept, mech, params, *, kind="EARNING", conditions=None, run_types=T, anchor="termination_date"):
    doc = {"rule_id": f"ZZ.{key}.1", "rule_key": f"ZZ.{key}", "version": "1", "country": "ZZ", "jurisdiction": "NATIONAL",
           "concept": concept, "category": "TERMINATION_TEST", "kind": kind, "effective": {"from": "2026-01-01", "to": None},
           "anchor": anchor, "straddle_policy": "ERROR", "priority": 100, "run_types": run_types,
           "calculation": {"mechanism": mech, "params": params, "rounding": "none"}, "source": SRC, "verification": VER,
           "implementation_status": "IMPLEMENTED"}
    if conditions:
        doc["conditions"] = conditions
    return doc


def concept(code, role="EARNING"):
    return {"concept": code, "role": role, "label_key": None, "source": SRC, "verification": VER, "treatments": []}


SAL = {"input": "employment.monthly_salary"}


def engine_run(rules, *, hire="2020-01-10", end="2026-09-15", extra=None, cause="DISMISSAL_WITHOUT_CAUSE", salary="3000", employment=None):
    concepts = [concept(r["concept"], "INFO" if r["kind"] == "INFO" else "EARNING") for r in rules if r["kind"] != "VALIDATION"]
    docs = {"manifest": {"country": "ZZ", "year": 2026, "ruleset_version": "ZZ-T", "jurisdiction_default": "NATIONAL", "currency": "ZZC",
                         "local_payroll_engine": True, "consolidation_context": False, "execution_path": "NEW_ENGINE",
                         "normative_date": "2026-01-01", "capabilities": {"termination": {"status": "PARTIALLY_IMPLEMENTED"}}},
            "references": [], "concepts": concepts, "bases": [], "rules": rules, "rounding": ROUNDING}
    ruleset = RuleSetData.from_documents(docs)
    payload = {"country": "ZZ", "run_type": "TERMINATION", "termination_date": end,
               "employment": {"hire_date": hire, "monthly_salary": salary, "contract_type": "INDEFINITE"},
               "termination": {"cause": cause}, "amounts": {}}
    payload["employment"].update(employment or {})
    payload.update(extra or {})
    return PayrollEngine().run(payload, ruleset=ruleset)


def value(run, concept):
    for l in run.result["lines"]:
        if l["concept"] == concept:
            return l["amount"]
    raise KeyError(concept)


def one(mech, params, **kw):
    return value(engine_run([rule("R", "OUT", mech, params)], **kw), "OUT")


# ---------------------------------------------------------------------------------------- tiered_service_amount
TIER_PER_YEAR = lambda policy, **extra: {"base": SAL, "unit_days_per_month": "1", "tiers": [
    {"over_years": "0", "units_per_year": "1", "fraction": policy, **extra}]}


@pytest.mark.parametrize("policy,extra,expected", [
    ("PRORATA", {}, D(6) + D(8) / 12 + D(6) / 360),             # 2020-01-10 .. 2026-09-15 = 6 años, 8 meses, 6 días
    ("FLOOR", {}, D(6)),
    ("CEIL", {}, D(7)),
    ("THRESHOLD", {"threshold_months": 6}, D(7)),                  # 8 meses > 6
    ("THRESHOLD", {"threshold_months": 9}, D(6)),                  # 8 meses no supera 9
])
def test_politicas_de_fraccion_de_anos(policy, extra, expected):
    got = one("tiered_service_amount", TIER_PER_YEAR(policy, **extra))
    assert abs(got - D(3000) * expected) <= D("0.000001")


def test_tramos_fijos_y_por_ano_se_suman_y_respetan_minimo_y_maximo():
    tiers = [{"over_years": "0", "fixed_units": "30"}, {"over_years": "1", "units_per_year": "20", "count_from_years": "1", "fraction": "FLOOR"}]
    params = {"base": SAL, "unit_days_per_month": "30", "tiers": tiers}
    assert one("tiered_service_amount", params) == D(3000) / 30 * (30 + 20 * 5)              # 6,7 años: 30 + 20 × 5 (FLOOR de 5,7)
    assert one("tiered_service_amount", dict(params, max_units="100")) == D(3000) / 30 * 100
    assert one("tiered_service_amount", dict(params, min_units="500")) == D(3000) / 30 * 500
    short = one("tiered_service_amount", params, hire="2026-08-01")                          # menos de un año: solo el tramo fijo
    assert short == D(3000) / 30 * 30


def test_tramos_excluyentes_por_antiguedad_total():
    tiers = [{"over_years": "0", "up_to_years": "3", "fixed_units": "3"},
             {"over_years": "3", "units_per_year": "1", "count_from_years": "0", "fraction": "CEIL"}]
    params = {"base": SAL, "unit_days_per_month": "1", "tiers": tiers, "max_units": "25"}
    assert one("tiered_service_amount", params, hire="2023-09-16", end="2026-09-15") == D(3000) * 3      # exactamente 3 años
    assert one("tiered_service_amount", params, hire="2023-09-15", end="2026-09-15") == D(3000) * 4      # 3 años y un día
    assert one("tiered_service_amount", params, hire="1990-01-01") == D(3000) * 25                        # tope


def test_tope_relativo_de_la_base_con_piso_y_sin_dato():
    params = {"base": SAL, "unit_days_per_month": "1", "tiers": [{"over_years": "0", "units_per_year": "1", "fraction": "FLOOR"}],
              "base_cap": {"input": "amounts.cap", "multiple": "2", "floor_share": "0.8"}}
    run = engine_run([rule("R", "OUT", "tiered_service_amount", params)], extra={"amounts": {"cap": "1000"}})
    assert value(run, "OUT") == D(2400) * 6                                                        # tope 2.000 < piso 80 % de 3.000
    none = engine_run([rule("R", "OUT", "tiered_service_amount", params)])
    assert value(none, "OUT") == D(3000) * 6 and any(w["type"] == "MECHANISM_WARNING" for w in none.warnings)


# ---------------------------------------------------------------------------------------- service_quantity
@pytest.mark.parametrize("hire,end,expected", [("2026-03-01", "2026-09-15", 12), ("2025-03-01", "2026-09-15", 14), ("2020-01-10", "2026-09-15", 22)])
def test_service_quantity_tabla_por_anos_completos_con_offset(hire, end, expected):
    table = [{"min": 1, "max": 1, "value": "12"}, {"min": 2, "max": 2, "value": "14"}] + [{"min": n, "max": None, "value": "22"} for n in (3,)]
    assert one("service_quantity", {"table": table, "year_offset": 1}, hire=hire, end=end) == expected


def test_service_quantity_lineal_con_bloques_tope_y_anos_previos():
    lin = {"base_quantity": "15", "per_completed_year": "1", "after_years": 10, "block_years": 3}
    params = {"years_basis": "COMPLETED_YEARS_PLUS_PRIOR", "prior_cap": "10", "linear": lin}
    assert one("service_quantity", params, hire="2026-01-01", employment={"prior_years": 25}) == 15         # previos topados a 10; 0 nuevos
    assert one("service_quantity", params, hire="2017-01-01", employment={"prior_years": 10}) == 15 + 3     # 9 + 10 = 19 años -> 9 // 3 = 3
    capped = {"years_basis": "COMPLETED_YEARS", "linear": {"base_quantity": "30", "per_completed_year": "3", "max_total": "90"}}
    assert one("service_quantity", capped, hire="1970-01-01") == 90


def test_service_quantity_antiguedad_al_31_de_diciembre_y_tabla_continua():
    params = {"years_basis": "YEARS_AT_YEAR_END", "table_decimal": [{"up_to": "5", "value": "14"}, {"up_to": None, "value": "21"}]}
    assert one("service_quantity", params, hire="2022-01-01") == 14
    assert one("service_quantity", params, hire="2021-12-31") == 21


def test_service_quantity_sin_forma_de_calculo_es_un_error_de_esquema():
    with pytest.raises(SchemaError):
        one("service_quantity", {"years_basis": "COMPLETED_YEARS"})


# ---------------------------------------------------------------------------------------- service_period_proration
def test_proporcion_con_conteos_distintos_sobre_la_misma_ventana():
    window = {"type": "CALENDAR_YEAR"}
    days = one("service_period_proration", {"base": SAL, "window": window, "count": {"unit": "DAYS_ACTUAL", "divisor": "365"}})
    assert abs(days - D(3000) * 258 / 365) <= D("0.000001")
    commercial = one("service_period_proration", {"base": SAL, "window": window, "count": {"unit": "DAYS_360", "divisor": "360"}})
    assert abs(commercial - D(3000) * 255 / 360) <= D("0.000001")
    months = one("service_period_proration", {"base": SAL, "window": window,
                                              "count": {"unit": "MONTHS_AND_DAYS", "months_divisor": "12", "days_divisor": "360"}})
    assert abs(months - D(3000) * (D(8) / 12 + D(15) / 360)) <= D("0.000001")
    factor = one("service_period_proration", {"base": SAL, "window": window, "factor": "2", "count": {"unit": "DAYS_ACTUAL", "divisor": "365"}})
    assert abs(factor - days * 2) <= D("0.000001")


def test_antiguedad_minima_evita_el_derecho():
    params = {"base": SAL, "window": {"type": "FULL_SERVICE"}, "count": {"unit": "DAYS_ACTUAL", "divisor": "365"},
              "min_service": {"unit": "MONTHS_AND_DAYS", "value": "1"}}
    assert one("service_period_proration", params, hire="2026-09-01") == 0            # 15 días
    assert one("service_period_proration", params, hire="2026-08-15") > 0             # 1 mes y 1 día


# ---------------------------------------------------------------------------------------- remaining_term_amount
def test_tiempo_restante_en_dias_360_meses_y_dias_con_piso_y_tope():
    end = {"employment": {"contract_end_date": "2026-12-31"}}
    days = one("remaining_term_amount", {"base": SAL, "unit": "DAYS_360"}, employment=end["employment"])
    assert abs(days - D(3000) / 30 * 105) <= D("0.000001")                            # 16-sep .. 31-dic
    months = one("remaining_term_amount", {"base": SAL, "unit": "MONTHS_AND_DAYS", "multiplier": "1.5"}, employment=end["employment"])
    assert abs(months - D(3000) * (3 + D(16) / 30) * D("1.5")) <= D("0.000001")          # 3 meses y 16 días
    assert one("remaining_term_amount", {"base": SAL, "unit": "DAYS_360", "min_days": "200"}, employment=end["employment"]) == D(3000) / 30 * 200
    assert one("remaining_term_amount", {"base": SAL, "unit": "MONTHS_AND_DAYS", "max_months": "2"}, employment=end["employment"]) == D(6000)
    ended = one("remaining_term_amount", {"base": SAL}, employment={"contract_end_date": "2026-09-15"})
    assert ended == 0


def test_tiempo_restante_exige_fecha_de_fin():
    with pytest.raises(MissingInputError):
        one("remaining_term_amount", {"base": SAL})


# ---------------------------------------------------------------------------------------- history_value / accrued_in_window
HISTORY = [{"month": "2026-03", "amount": "100"}, {"month": "2026-04", "amount": "100"}, {"month": "2026-05", "amount": "100"},
           {"month": "2026-06", "amount": "200"}, {"month": "2026-07", "amount": "400"}, {"month": "2026-08", "amount": "400"},
           {"month": "2026-09", "amount": "300"}]


@pytest.mark.parametrize("method,window,expected", [("LAST", 12, D(300)), ("MAX", 12, D(400)), ("SUM", 12, D(1600)),
                                                    ("AVERAGE", 12, D(1600) / 7), ("AVERAGE", 3, D(1100) / 3),
                                                    ("AVERAGE_IF_VARIED", 12, D(1600) / 7)])
def test_history_value_metodos(method, window, expected):
    got = one("history_value", {"history_input": "salary_history", "method": method, "window_months": window, "vary_months": 3},
              extra={"salary_history": HISTORY})
    assert got == expected


def test_history_value_promedio_solo_si_vario_y_valor_de_respaldo():
    stable = [{"month": f"2026-0{m}", "amount": "500"} for m in range(5, 10)]
    assert one("history_value", {"history_input": "salary_history", "method": "AVERAGE_IF_VARIED", "vary_months": 3}, extra={"salary_history": stable}) == 500
    assert one("history_value", {"history_input": "salary_history", "method": "LAST", "fallback": SAL}) == 3000
    with pytest.raises(MissingInputError):
        one("history_value", {"history_input": "salary_history", "method": "LAST"})


def test_history_value_filas_invalidas_se_rechazan():
    with pytest.raises(InputValidationError):
        one("history_value", {"history_input": "salary_history", "method": "LAST"}, extra={"salary_history": [{"mes": "2026-09"}]})


def test_accrued_in_window_suma_historial_o_supone_remuneracion_constante():
    window = {"type": "RECURRING_PERIODS", "periods": [{"start": "01-01", "end": "06-30"}, {"start": "07-01", "end": "12-31"}]}
    params = {"window": window, "history_input": "salary_history", "fallback_monthly": SAL}
    assert one("accrued_in_window", params, extra={"salary_history": HISTORY}) == D(400 + 400 + 300)      # jul-sep
    fallback = engine_run([rule("R", "OUT", "accrued_in_window", params)])
    assert value(fallback, "OUT") == D(3000) * (2 + D(15) / 30) and any(w["type"] == "MECHANISM_WARNING" for w in fallback.warnings)


# ---------------------------------------------------------------------------------------- adjusted_quantity / date_measure
def test_cantidad_ajustada_con_piso_y_tope():
    assert one("adjusted_quantity", {"quantity": "10", "add": ["5"], "subtract": ["3"]}) == 12
    assert one("adjusted_quantity", {"quantity": "10", "subtract": ["30"]}) == 0                     # piso 0
    assert one("adjusted_quantity", {"quantity": "10", "add": ["50"], "max": "20"}) == 20


@pytest.mark.parametrize("measure,end,expected", [("DAYS_REMAINING_IN_MONTH", "2026-09-15", 15), ("DAYS_REMAINING_IN_MONTH", "2026-09-30", 0),
                                                  ("DAYS_REMAINING_IN_MONTH", "2028-02-10", 19), ("COMMERCIAL_DAYS_IN_MONTH", "2026-09-15", 15),
                                                  ("COMMERCIAL_DAYS_IN_MONTH", "2026-01-31", 30), ("COMMERCIAL_DAYS_IN_MONTH", "2026-02-28", 30),
                                                  ("SERVICE_MONTHS_AND_DAYS", "2026-09-15", D(80) + D(6) / 30)])
def test_date_measure(measure, end, expected):
    assert one("date_measure", {"measure": measure}, end=end) == expected


def test_date_measure_desconocida_falla():
    with pytest.raises(SchemaError):
        one("date_measure", {"measure": "INVENTADA"})


# ---------------------------------------------------------------------------------------- horas y recargos
def test_horas_a_multiplicadores_valor_hora_por_mensual_diario_o_tarifa():
    cats = [{"key": "a", "hours_input": "time.h_a", "components": ["1.25"]}, {"key": "b", "hours_input": "time.h_b", "components": ["1", "0.5"]}]
    extra = {"time": {"h_a": "4", "h_b": "2"}}
    monthly = engine_run([rule("R", "OUT", "hours_at_multipliers", {"hourly": {"monthly_base": SAL, "hours_per_month": "200"}, "categories": cats},
                               run_types=["TERMINATION"])], extra=extra)
    assert value(monthly, "OUT") == D(3000) / 200 * (D("1.25") * 4 + D("1.5") * 2)
    daily = one("hours_at_multipliers", {"hourly": {"daily_base": "100", "hours_per_day": "8"}, "categories": cats}, extra=extra)
    assert daily == D("12.5") * (D("1.25") * 4 + D("1.5") * 2)
    rate = one("hours_at_multipliers", {"hourly": {"hourly_rate": "20"}, "categories": cats}, extra=extra)
    assert rate == 20 * (D("1.25") * 4 + D("1.5") * 2)


def test_horas_por_tramos_semanales():
    params = {"hourly": {"hourly_rate": "10"}, "categories": [{"key": "w", "weekly_hours_input": "weekly", "tiers": [
        {"up_to_hours": "9", "multiplier": "2"}, {"multiplier": "3"}]}]}
    assert one("hours_at_multipliers", params, extra={"weekly": [4, 10, 12]}) == 10 * (2 * 4 + (2 * 9 + 3) + (2 * 9 + 3 * 3))


def test_horas_negativas_se_rechazan_y_hourly_incompleto_es_error_de_esquema():
    cats = [{"key": "a", "hours_input": "time.h", "components": ["1"]}]
    with pytest.raises(InputValidationError):
        one("hours_at_multipliers", {"hourly": {"hourly_rate": "1"}, "categories": cats}, extra={"time": {"h": "-1"}})
    with pytest.raises(SchemaError):
        one("hours_at_multipliers", {"hourly": {}, "categories": cats})


# ---------------------------------------------------------------------------------------- corrida TERMINATION del núcleo
def test_las_reglas_de_terminacion_no_corren_en_la_mensual_ni_las_mensuales_en_la_terminacion():
    monthly = rule("M", "MONTHLY_OUT", "pass_through", {"amount": "5"}, run_types=["REGULAR"], anchor="period_end")
    term_rule = rule("T", "TERM_OUT", "pass_through", {"amount": "7"})
    run = engine_run([monthly, term_rule])
    assert [l["concept"] for l in run.result["lines"]] == ["TERM_OUT"]
    docs_rules = [monthly, term_rule]
    concepts = [concept("MONTHLY_OUT"), concept("TERM_OUT")]
    docs = {"manifest": {"country": "ZZ", "year": 2026, "ruleset_version": "ZZ-T", "jurisdiction_default": "NATIONAL", "currency": "ZZC",
                         "local_payroll_engine": True, "consolidation_context": False, "execution_path": "NEW_ENGINE",
                         "normative_date": "2026-01-01", "capabilities": {"payroll_monthly": {"status": "PARTIALLY_IMPLEMENTED"}}},
            "references": [], "concepts": concepts, "bases": [], "rules": docs_rules, "rounding": ROUNDING}
    ruleset = RuleSetData.from_documents(docs)
    reg = PayrollEngine().run({"country": "ZZ", "run_type": "REGULAR", "period": {"start": "2026-09-01", "end": "2026-09-30"}}, ruleset=ruleset)
    assert [l["concept"] for l in reg.result["lines"]] == ["MONTHLY_OUT"]


def test_entrada_de_terminacion_incompleta_o_inconsistente_se_bloquea():
    rules = [rule("R", "OUT", "pass_through", {"amount": "1"})]
    with pytest.raises(InputValidationError):
        engine_run(rules, hire="2026-10-01")                                        # ingreso posterior a la terminación
    for missing in ("hire_date", "contract_type"):
        payload_extra = {"employment": {"hire_date": "2020-01-01", "monthly_salary": "1", "contract_type": "INDEFINITE"}}
        payload_extra["employment"].pop(missing)
        with pytest.raises(InputValidationError):
            docs = copy.deepcopy(rules)
            concepts = [concept("OUT")]
            manifest = {"country": "ZZ", "year": 2026, "ruleset_version": "ZZ-T", "jurisdiction_default": "NATIONAL", "currency": "ZZC",
                        "local_payroll_engine": True, "consolidation_context": False, "execution_path": "NEW_ENGINE",
                        "normative_date": "2026-01-01", "capabilities": {"termination": {"status": "PARTIALLY_IMPLEMENTED"}}}
            rs = RuleSetData.from_documents({"manifest": manifest, "references": [], "concepts": concepts, "bases": [], "rules": docs, "rounding": ROUNDING})
            PayrollEngine().run(dict({"country": "ZZ", "run_type": "TERMINATION", "termination_date": "2026-09-15",
                                      "termination": {"cause": "X"}}, **payload_extra), ruleset=rs)


def test_causas_y_contratos_validos_los_declara_el_manifiesto():
    rules = [rule("R", "OUT", "pass_through", {"amount": "1"})]
    concepts = [concept("OUT")]
    manifest = {"country": "ZZ", "year": 2026, "ruleset_version": "ZZ-T", "jurisdiction_default": "NATIONAL", "currency": "ZZC",
                "local_payroll_engine": True, "consolidation_context": False, "execution_path": "NEW_ENGINE", "normative_date": "2026-01-01",
                "capabilities": {"termination": {"status": "PARTIALLY_IMPLEMENTED"}},
                "termination": {"causes": ["RESIGNATION"], "contract_types": ["INDEFINITE"], "requires_contract_end_for": ["FIXED_TERM"]}}
    rs = RuleSetData.from_documents({"manifest": manifest, "references": [], "concepts": concepts, "bases": [], "rules": rules, "rounding": ROUNDING})
    ok = {"country": "ZZ", "run_type": "TERMINATION", "termination_date": "2026-09-15", "termination": {"cause": "RESIGNATION"},
          "employment": {"hire_date": "2020-01-01", "monthly_salary": "1", "contract_type": "INDEFINITE"}}
    assert PayrollEngine().run(ok, ruleset=rs).status in ("COMPLETE", "COMPLETE_WITH_WARNINGS")
    for change in ({"termination": {"cause": "DEATH"}}, {"employment": {"hire_date": "2020-01-01", "monthly_salary": "1", "contract_type": "FIXED_TERM"}}):
        with pytest.raises(InputValidationError):
            PayrollEngine().run(dict(ok, **change), ruleset=rs)


def test_la_terminacion_de_un_pais_sin_reglas_de_terminacion_o_sin_motor_se_bloquea():
    with pytest.raises(CapabilityError):
        PayrollEngine().run({"country": "US", "run_type": "TERMINATION", "termination_date": "2026-09-15",
                             "employment": {"hire_date": "2020-01-01", "monthly_salary": "1", "contract_type": "INDEFINITE"},
                             "termination": {"cause": "RESIGNATION"}})
    with pytest.raises(CapabilityError):
        PayrollEngine().run({"country": "HK", "run_type": "TERMINATION", "termination_date": "2026-09-15"})


def test_una_corrida_de_terminacion_es_reproducible_con_su_snapshot():
    run = engine_run([rule("R", "OUT", "service_period_proration",
                           {"base": SAL, "window": {"type": "FULL_SERVICE"}, "count": {"unit": "DAYS_ACTUAL", "divisor": "365"}})])
    again = reproduce(run.to_dict(), run._documents)
    assert again["same"] is True
    assert run.input_snapshot["payload"]["employment"]["hire_date"] == "2020-01-10"


def test_los_importes_de_los_mecanismos_de_terminacion_son_decimal_nunca_float():
    run = engine_run([rule("R", "OUT", "tiered_service_amount", TIER_PER_YEAR("PRORATA"))])
    assert all(isinstance(l["amount"], Decimal) for l in run.result["lines"])
    with pytest.raises(InputValidationError):
        engine_run([rule("R", "OUT", "pass_through", {"amount": "1"})], salary=3000.5)
