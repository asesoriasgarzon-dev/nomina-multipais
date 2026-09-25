"""Colombia sobre el motor normativo. Valores esperados calculados de forma independiente
(Decimal en la prueba). Cada regla crítica se prueba en la frontera: mínimo-1/mínimo/+1,
máximo-1/máximo/+1, un día antes / la fecha exacta / un día después.

Fuentes (ver config/payroll/CO/2026): SMMLV Decreto 1469/2025 y 159/2026; auxilio Decreto 1470/2025;
IBC/integral Ley 797/2003 art. 5; FSP Ley 797 art. 8; jornada Ley 2101/2021 art. 3."""

from datetime import date
from decimal import Decimal

import pytest

from payroll_engine.errors import InputValidationError
from payroll_engine.explain import explain_evaluation, explain_line, render_text
from payroll_engine.loader import load_country
from payroll_engine.references import ReferenceResolver
from payroll_engine.run import PayrollEngine, reproduce
from tests.payroll_2026.helpers import SMMLV, amount, co_payload, q, run_co

TWO = 2 * SMMLV                      # 3.501.810
CAP = 25 * SMMLV                     # 43.772.625
TEN = 10 * SMMLV                     # 17.509.050
THIRTEEN = 13 * SMMLV                # 22.761.765


def base_value(run, code):
    return Decimal(next(b for b in run.trace["bases"] if b["base"] == code)["value"])


# ============================================================ referencias 2026
def test_referencias_oficiales_2026():
    refs = ReferenceResolver(load_country("CO").references, "CO", ["NATIONAL"])
    assert refs.resolve("SMMLV", date(2026, 9, 24)).value == Decimal("1750905")
    assert refs.resolve("TRANSPORT_ALLOWANCE", date(2026, 9, 24)).value == Decimal("249095")
    assert 2 * SMMLV == Decimal("3501810") and 25 * SMMLV == Decimal("43772625") and 13 * SMMLV == Decimal("22761765")


def test_las_referencias_oficiales_tienen_respaldo_verificable():
    for ref in load_country("CO").references:
        src = ref["source"]
        if ref["code"] in ("SMMLV", "TRANSPORT_ALLOWANCE", "WORKWEEK_HOURS"):
            assert src["status"] == "OFFICIAL" and src["official_url"].startswith("https://") and src["legal_reference"]


# ============================================================ CO_TRANSPORT_BOUNDARY
@pytest.mark.parametrize("salary,eligible", [
    (TWO - 1, True),            # TRANSPORT_CO: 3.501.809 -> elegible
    (TWO, True),                # TRANSPORT_CO_001: 3.501.810 -> elegible
    (TWO + 1, False),           # TRANSPORT_CO_002: 3.501.811 -> no elegible
    (2 * TWO, False),           # TRANSPORT_CO_003: 7.003.620 -> no elegible
    (Decimal("3501810.01"), False),
    (Decimal("3501810.00"), True),
])
def test_co_transport_boundary(salary, eligible):
    run = run_co(salary)
    if eligible:
        assert amount(run, "TRANSPORT_ALLOWANCE") == Decimal("249095.00")
    else:
        assert run.line("TRANSPORT_ALLOWANCE") is None
        ev = [e for e in run.trace["evaluations"] if e["rule_id"] == "CO.TRANSPORT_ALLOWANCE.1"][0]
        assert ev["outcome"] == "NOT_APPLICABLE" and ev["conditions"]["right"] == "3501810"


def test_co_transport_no_usa_el_limite_de_4_smmlv():
    # 4 SMMLV = 7.003.620 estaba mal; también el punto medio entre 2 y 4 SMMLV no recibe auxilio
    assert run_co(3 * SMMLV).line("TRANSPORT_ALLOWANCE") is None
    assert run_co(4 * SMMLV - 1).line("TRANSPORT_ALLOWANCE") is None


@pytest.mark.parametrize("days,expected", [("30", "249095.00"), ("15", "124547.50"), ("1", "8303.17"), ("0", "0.00")])
def test_co_transport_prorrateo_por_dias_trabajados(days, expected):
    assert amount(run_co(3_000_000, worked=days), "TRANSPORT_ALLOWANCE") == Decimal(expected)


def test_co_transport_naturaleza_no_salarial_no_entra_al_ibc_pero_si_a_prestaciones():
    run = run_co(3_000_000)
    ibc = next(b for b in run.trace["bases"] if b["base"] == "IBC")
    assert "TRANSPORT_ALLOWANCE" in [e["concept"] for e in ibc["exclusions"]]
    assert base_value(run, "IBC") == Decimal("3000000")
    assert base_value(run, "BENEFIT_BASE") == Decimal("3249095")


def test_co_transport_explicacion_muestra_la_regla_de_2_smmlv():
    run = run_co(3_000_000)
    d = run.to_dict()
    line = next(l for l in d["trace"]["lines"] if l["concept"] == "TRANSPORT_ALLOWANCE")
    exp = explain_line(d, line["line_id"])
    assert exp["result"] == "249095" and exp["rule"]["rule_id"] == "CO.TRANSPORT_ALLOWANCE.1"
    refs = [o for o in exp["conditions"]["operands"] if o["kind"] == "reference"]
    assert refs[0]["ref_id"] == "CO.SMMLV.2026" and refs[0]["multiple"] == "2" and refs[0]["value"] == "3501810"
    assert exp["legal_source"]["status"] == "OFFICIAL" and "decreto_1470_2025" in exp["legal_source"]["official_url"]
    assert "249095 × 30 / 30" in exp["formula"]
    assert "Decreto 1470 de 2025" in render_text(exp)


# ============================================================ CO_SOCIAL_SECURITY_CAP
@pytest.mark.parametrize("salary,ibc,cap_applied", [
    (CAP - 1, CAP - 1, False),          # tope - 1: permanece igual
    (CAP, CAP, False),                  # igual al tope: permanece igual
    (CAP + 1, CAP, True),               # tope + 1: se limita
    (CAP * 2, CAP, True),
    (Decimal("1000000"), Decimal("1000000"), False),
])
def test_co_social_security_cap(salary, ibc, cap_applied):
    run = run_co(salary)
    assert base_value(run, "IBC") == ibc
    assert next(b for b in run.trace["bases"] if b["base"] == "IBC")["cap_applied"] is cap_applied
    assert amount(run, "HEALTH_EMPLOYEE") == q(ibc * Decimal("0.04"))
    assert amount(run, "PENSION_EMPLOYEE") == q(ibc * Decimal("0.04"))
    assert amount(run, "PENSION_EMPLOYER") == q(ibc * Decimal("0.12"))       # el tope también limita al empleador


def test_co_el_tope_es_una_regla_colombiana_por_referencia_y_multiplo():
    base = next(b for b in load_country("CO").bases if b["base"] == "IBC")
    assert base["limits"]["maximum"]["value"] == {"reference": {"code": "SMMLV", "multiple": "25"}}


def test_co_ibc_minimo_es_solo_advertencia_hasta_verificar_periodos_parciales():
    run = run_co(1_000_000, worked="30")
    assert any("BASE_BAJO_MINIMO" in w["message"] for w in run.warnings)
    assert base_value(run, "IBC") == Decimal("1000000")          # no se altera el valor


# ============================================================ CO_INTEGRAL_SALARY
def test_co_integral_salary_ibc_70_por_ciento():
    run = run_co(THIRTEEN, salary_type="INTEGRAL")
    assert base_value(run, "IBC") == Decimal("15933235.5")        # 22.761.765 × 70%
    assert amount(run, "HEALTH_EMPLOYEE") == q(Decimal("15933235.5") * Decimal("0.04"))


def test_co_integral_salary_70_por_ciento_sujeto_al_tope():
    run = run_co(70_000_000, salary_type="INTEGRAL")
    ibc = next(b for b in run.trace["bases"] if b["base"] == "IBC")
    assert ibc["raw_sum"] == "49000000"                           # 70% de 70.000.000
    assert ibc["value"] == "43772625" and ibc["cap_applied"] is True


@pytest.mark.parametrize("salary,ok", [(THIRTEEN - 1, False), (THIRTEEN, True), (THIRTEEN + 1, True)])
def test_co_integral_salary_minimo_13_smmlv_frontera(salary, ok):
    if ok:
        assert run_co(salary, salary_type="INTEGRAL").status in ("COMPLETE", "COMPLETE_WITH_WARNINGS")
    else:
        with pytest.raises(InputValidationError) as err:
            run_co(salary, salary_type="INTEGRAL")
        assert "13 SMMLV" in str(err.value)


def test_co_integral_sin_prima_ni_cesantias_pero_con_vacaciones_y_sin_auxilio():
    run = run_co(THIRTEEN, salary_type="INTEGRAL")
    assert run.line("PRIMA_ACCRUAL") is None and run.line("CESANTIAS_ACCRUAL") is None
    assert amount(run, "VACATION_ACCRUAL") == q(THIRTEEN * Decimal(15) / Decimal(360))
    assert run.line("TRANSPORT_ALLOWANCE") is None


def test_co_tipo_de_salario_desconocido_se_bloquea():
    with pytest.raises(InputValidationError):
        run_co(5_000_000, salary_type="MIXTO")


# ============================================================ CO_WORKWEEK_2026
@pytest.mark.parametrize("day,hours", [
    (date(2025, 7, 14), None), (date(2025, 7, 15), "44"),
    (date(2026, 7, 14), "44"),                                   # día anterior
    (date(2026, 7, 15), "42"),                                   # día exacto
    (date(2026, 7, 16), "42"),                                   # día posterior
    (date(2027, 1, 1), "42"),
])
def test_co_workweek_2026_resolucion_por_fecha(day, hours):
    refs = ReferenceResolver(load_country("CO").references, "CO", ["NATIONAL"])
    if hours is None:
        from payroll_engine.errors import MissingReferenceError
        with pytest.raises(MissingReferenceError):
            refs.resolve("WORKWEEK_HOURS", day)
    else:
        assert refs.resolve("WORKWEEK_HOURS", day).value == Decimal(hours)


@pytest.mark.parametrize("period,hours", [
    (("2026-07-01", "2026-07-14"), "220"),                       # 44 h x 5
    (("2026-07-16", "2026-07-31"), "210"),                       # 42 h x 5
])
def test_co_workweek_horas_mensuales_por_vigencia(period, hours):
    assert amount(run_co(3_000_000, period=period), "MONTHLY_WORK_HOURS") == Decimal(hours)


def test_co_workweek_periodo_que_cruza_el_15_de_julio_lo_advierte():
    run = run_co(3_000_000, period=("2026-07-01", "2026-07-31"))
    assert any(w["type"] == "CHANGE_WITHIN_PERIOD" for w in run.warnings)


# ============================================================ exoneración art. 114-1 ET
@pytest.mark.parametrize("salary,exempt", [(TEN - 1, True), (TEN, False), (TEN + 1, False), (Decimal("30000000"), False)])
def test_co_exoneracion_menos_de_10_smmlv(salary, exempt):
    run = run_co(salary, worked="30")
    ibc = min(salary, CAP)
    expected_health = Decimal("0.00") if exempt else q(ibc * Decimal("0.085"))
    assert amount(run, "HEALTH_EMPLOYER") == expected_health
    assert amount(run, "SENA") == (Decimal("0.00") if exempt else q(salary * Decimal("0.02")))
    assert amount(run, "ICBF") == (Decimal("0.00") if exempt else q(salary * Decimal("0.03")))


def test_co_exoneracion_la_linea_en_cero_explica_por_que():
    run = run_co(3_000_000)
    d = run.to_dict()
    line = next(l for l in d["trace"]["lines"] if l["concept"] == "HEALTH_EMPLOYER")
    exp = explain_line(d, line["line_id"])
    assert exp["result"] == "0" and any(e["result"] for e in exp["exceptions"])
    assert "art. 114-1" in render_text(exp)


def test_co_empleador_no_exonerado_paga_salud_sena_icbf():
    run = run_co(3_000_000, exonerated=False)
    assert amount(run, "HEALTH_EMPLOYER") == Decimal("255000.00")
    assert amount(run, "SENA") == Decimal("60000.00") and amount(run, "ICBF") == Decimal("90000.00")


def test_co_la_caja_de_compensacion_nunca_se_exonera():
    assert amount(run_co(3_000_000), "COMPENSATION_FUND") == Decimal("120000.00")
    assert amount(run_co(30_000_000), "COMPENSATION_FUND") == Decimal("1200000.00")


# ============================================================ FSP (Ley 797 art. 8)
@pytest.mark.parametrize("multiple,salary,rate", [
    ("3.9999", Decimal("6999000"), "0"),
    ("4", 4 * SMMLV - 1, "0"), ("4", 4 * SMMLV, "0.01"), ("4+", 4 * SMMLV + 1, "0.01"),
    ("16-", 16 * SMMLV - 1, "0.01"), ("16", 16 * SMMLV, "0.012"), ("17", 17 * SMMLV, "0.014"),
    ("18", 18 * SMMLV, "0.016"), ("19", 19 * SMMLV, "0.018"), ("20", 20 * SMMLV, "0.02"),
    ("25", 25 * SMMLV, "0.02"), ("30", 30 * SMMLV, "0.02"),
])
def test_co_fsp_tramos_en_la_frontera(multiple, salary, rate):
    run = run_co(salary)
    assert amount(run, "FSP_EMPLOYEE") == q(base_value(run, "IBC") * Decimal(rate))


def test_co_fsp_se_calcula_sobre_el_ibc_con_tope():
    run = run_co(50_000_000)
    assert amount(run, "FSP_EMPLOYEE") == q(CAP * Decimal("0.02"))


# ============================================================ ARL, aportes y provisiones
def test_co_arl_clase_i_por_referencia():
    run = run_co(3_000_000)
    assert amount(run, "ARL") == q(Decimal("3000000") * Decimal("0.00522"))


def test_co_arl_otras_clases_estan_pendientes_y_se_bloquean():
    with pytest.raises(InputValidationError):
        run_co(3_000_000, arl_class="III")


def test_co_provisiones_con_razones_exactas_y_auxilio_en_la_base():
    run = run_co(3_000_000)
    base = Decimal("3249095")                                     # salario + auxilio de transporte
    assert amount(run, "PRIMA_ACCRUAL") == q(base / 12)
    assert amount(run, "CESANTIAS_ACCRUAL") == q(base / 12)
    assert amount(run, "CESANTIAS_INTEREST_ACCRUAL") == q(base * Decimal("0.01"))
    assert amount(run, "VACATION_ACCRUAL") == q(Decimal("3000000") * Decimal(15) / Decimal(360))


# ============================================================ bases separadas y naturaleza
def test_co_bases_separadas_para_cada_proposito():
    run = run_co(3_000_000, worked="28",
                 time={"incapacity_employer_days": "2", "accounted_days": "30"},
                 amounts={"BONUS_SALARY": "500000", "BONUS_NON_SALARY": "100000"})
    salary = q(Decimal(3_000_000) / 30 * 28)
    incap = q(Decimal(3_000_000) / 30 * 2 * 2 / 3)
    ibc = base_value(run, "IBC")
    risk = base_value(run, "RISK_BASE")
    para = base_value(run, "PARAFISCAL_BASE")
    assert ibc == salary + incap + Decimal("500000")              # incluye incapacidad y bono salarial
    assert risk == salary + Decimal("500000")                     # ARL: sin incapacidad
    assert para == salary + Decimal("500000")                     # parafiscales: sin incapacidad
    assert len({ibc, risk}) == 2                                  # no es una única base genérica


def test_co_bono_no_salarial_bajo_40_por_ciento_no_cotiza():
    run = run_co(3_000_000, amounts={"BONUS_NON_SALARY": "1000000"})   # 25% del total: no excede
    assert base_value(run, "IBC") == Decimal("3000000")


def test_co_bono_no_salarial_sobre_40_por_ciento_integra_el_exceso_ley_1393():
    run = run_co(3_000_000, amounts={"BONUS_NON_SALARY": "3000000"})   # total 6.000.000; límite 40% = 2.400.000
    assert base_value(run, "IBC") == Decimal("3600000")                # 3.000.000 + exceso 600.000
    ibc = next(b for b in run.trace["bases"] if b["base"] == "IBC")
    special = [c for c in ibc["contributions"] if c.get("special") == "SHARE_EXCESS"][0]
    assert special["limit"] == "2400000" and special["excess_included"] == "600000"


def test_co_tratamientos_pendientes_de_verificacion_quedan_advertidos():
    run = run_co(3_000_000, worked="28", time={"incapacity_employer_days": "2", "accounted_days": "30"})
    pend = [w for w in run.warnings if w["type"] == "PENDING_TREATMENTS"]
    assert pend and any("INCAPACITY_EMPLOYER" in item for item in pend[0]["items"])


# ============================================================ validaciones de entrada (datos)
@pytest.mark.parametrize("worked,incap,vac,ok", [("30", "0", "0", True), ("28", "2", "0", True), ("29", "2", "0", False),
                                               ("31", "0", "0", False), ("15", "5", "10", True), ("15", "5", "11", False)])
def test_co_dias_validos(worked, incap, vac, ok):
    accounted = str(Decimal(worked) + Decimal(incap) + Decimal(vac))
    kwargs = dict(worked=worked, time={"incapacity_employer_days": incap, "vacation_days": vac, "accounted_days": accounted})
    if ok:
        run_co(3_000_000, **kwargs)
    else:
        with pytest.raises(InputValidationError):
            run_co(3_000_000, **kwargs)


def test_co_cero_dias_trabajados_y_salario_cero():
    run = run_co(3_000_000, worked="0")
    assert amount(run, "BASE_SALARY") == Decimal("0.00") and amount(run, "TRANSPORT_ALLOWANCE") == Decimal("0.00")
    zero = run_co(0)
    assert any(w["type"] == "VALIDATION_WARNING" for w in zero.warnings)   # salario bajo el mínimo: se advierte


@pytest.mark.parametrize("bad", [{"amounts": {"BONUS_SALARY": "-1"}}, {"amounts": {"BONUS_SALARY": None}},
                                 {"amounts": {"BONUS_SALARY": "abc"}}, {"time": {"worked_days": "-1"}}])
def test_co_valores_negativos_nulos_y_texto_se_bloquean(bad):
    payload = co_payload(3_000_000)
    for section, values in bad.items():
        payload[section].update(values)
    with pytest.raises(InputValidationError):
        PayrollEngine().run(payload)


def test_co_dato_de_entrada_faltante():
    payload = co_payload(3_000_000)
    del payload["time"]["worked_days"]
    with pytest.raises(InputValidationError):
        PayrollEngine().run(payload)


def test_co_salario_muy_alto_y_decimal():
    run = run_co(1_000_000_000)
    assert base_value(run, "IBC") == CAP
    assert amount(run_co(Decimal("3000000.555")), "BASE_SALARY") == Decimal("3000000.56")


# ============================================================ auditoría, explicación y reproducibilidad
def test_co_toda_linea_tiene_traza_con_regla_version_fuente_y_redondeo():
    run = run_co(8_000_000, worked="28", time={"incapacity_employer_days": "2", "accounted_days": "30"},
                 amounts={"WITHHOLDING_TAX": "69001"})
    d = run.to_dict()
    assert len(d["trace"]["lines"]) == len(d["result"]["lines"])
    for line in d["trace"]["lines"]:
        assert line["rule_id"] and line["rule_version"] and line["formula"] and line["rounding"] and line["source"]
        assert explain_line(d, line["line_id"])["result"] == line["amount"]


def test_co_la_explicacion_sale_de_la_ejecucion_real():
    run = run_co(8_000_000)
    d = run.to_dict()
    line = next(l for l in d["trace"]["lines"] if l["concept"] == "FSP_EMPLOYEE")
    exp = explain_line(d, line["line_id"])
    assert exp["base"]["code"] == "IBC" and exp["base"]["value"] == "8000000"
    assert exp["thresholds"]["lookup_value"].startswith("4.569")           # 8.000.000 / 1.750.905 (tramo 1%)
    assert exp["rate"] == "0.01" and exp["result"] == "80000"
    assert exp["legal_source"]["status"] == "OFFICIAL"
    ev = explain_evaluation(d, "CO.TRANSPORT_ALLOWANCE.1")
    assert ev["evaluations"][0]["conditions"]["result"] is False           # por qué NO hubo auxilio


def test_co_retencion_manual_se_marca_external_input_no_es_motor_tributario():
    run = run_co(8_000_000, amounts={"WITHHOLDING_TAX": "69001"})
    line = next(l for l in run.trace["lines"] if l["concept"] == "WITHHOLDING_TAX")
    assert line["input_type"] == "EXTERNAL_INPUT"
    assert any(w["type"] == "EXTERNAL_INPUT" for w in run.warnings)
    assert run.manifest["capabilities"]["income_tax_withholding"]["status"] == "PARTIALLY_IMPLEMENTED"     # solo procedimiento 1 en modo CALCULATED
    assert run.line("WITHHOLDING_TAX_CALC") is None                                                       # modo MANUAL por defecto: no se calcula


def test_co_historico_reproducible_aunque_cambie_una_tasa_despues():
    run = run_co(8_000_000)
    stored, docs = run.to_dict(), run._documents
    assert reproduce(stored, docs)["same"] is True
    import copy
    new_docs = copy.deepcopy(docs)
    for rule in new_docs["rules"]:
        if rule["rule_key"] == "CO.HEALTH_EMPLOYEE":
            rule["calculation"]["params"]["rate"] = "0.05"
    from payroll_engine.loader import RuleSetData
    changed = PayrollEngine().run(co_payload(8_000_000), ruleset=RuleSetData.from_documents(new_docs))
    assert changed.result_hash != run.result_hash
    assert reproduce(stored, docs)["same"] is True                # la corrida original sigue reproduciéndose


def test_co_totales_y_costo_empleador_son_consistentes():
    run = run_co(8_000_000)
    t = run.result["totals"]
    assert t["neto_pagado"] == t["total_devengado"] - t["total_deducciones"]
    assert t["costo_empleador"] == t["total_devengado"] + t["total_aportes_patronales"] + t["total_provisiones"]
