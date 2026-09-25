"""MX, PE, CL, BR, AR, EC, US y HK: vigencias, referencias propias (sin copiar el modelo colombiano),
fronteras y honestidad del estado. Cada país tiene sus pruebas."""

from datetime import date
from decimal import Decimal

import pytest

from payroll_engine.capabilities import describe, describe_all
from payroll_engine.errors import CapabilityError, InputValidationError, MissingReferenceError
from payroll_engine.loader import load_country
from payroll_engine.references import ReferenceResolver
from payroll_engine.run import PayrollEngine
from tests.payroll_2026.helpers import amount, q

ENGINE = PayrollEngine()


def payload(cc, salary, period=("2026-09-01", "2026-09-30"), worked="30", time=None, amounts=None, jurisdictions=("NATIONAL",)):
    p = {"country": cc, "jurisdictions": list(jurisdictions), "run_type": "REGULAR",
         "period": {"start": period[0], "end": period[1]}, "employee": {"id": "E"},
         "employment": {"monthly_salary": str(salary)}, "time": {"worked_days": worked}, "amounts": {}}
    p["time"].update(time or {})
    p["amounts"].update(amounts or {})
    return p


def ref(cc, code, day):
    return ReferenceResolver(load_country(cc).references, cc, ["NATIONAL"]).resolve(code, day)


def base_value(run, code):
    return Decimal(next(b for b in run.trace["bases"] if b["base"] == code)["value"])


# ====================================================================== México
def mx(salary, period=("2026-09-01", "2026-09-30"), **kw):
    kw.setdefault("time", {"paid_days": "30"})
    return ENGINE.run(payload("MX", salary, period, **kw))


def test_mx_la_uma_cambia_el_1_de_febrero():
    assert ref("MX", "UMA_DAILY", date(2026, 1, 31)).value == Decimal("113.14")
    assert ref("MX", "UMA_DAILY", date(2026, 2, 1)).value == Decimal("117.31")
    jan = mx(30_000, ("2026-01-01", "2026-01-31"), worked="30", time={"paid_days": "30"})     # convención de 30 días
    feb = mx(30_000, ("2026-02-01", "2026-02-28"), worked="30", time={"paid_days": "30"})
    assert amount(jan, "IMSS_ER_FIXED") == q(Decimal("113.14") * 30 * Decimal("0.2040"))
    assert amount(feb, "IMSS_ER_FIXED") == q(Decimal("117.31") * 30 * Decimal("0.2040"))


def test_mx_periodo_que_cruza_el_cambio_de_uma_se_bloquea_porque_las_bases_no_tienen_politica_de_particion():
    from payroll_engine.errors import StraddleError
    with pytest.raises(StraddleError) as err:
        mx(30_000, ("2026-01-16", "2026-02-15"), worked="30")
    assert "UMA_DAILY" in str(err.value) and "SBC" in str(err.value)


@pytest.mark.parametrize("salary,capped", [(Decimal("87982.49"), False), (Decimal("87982.50"), False), (Decimal("87982.51"), True)])
def test_mx_tope_sbc_25_uma_frontera(salary, capped):
    run = mx(salary)
    assert base_value(run, "SBC") == min(salary, Decimal("87982.5"))
    assert next(b for b in run.trace["bases"] if b["base"] == "SBC")["cap_applied"] is capped


def test_mx_excedente_de_3_uma_y_cuota_fija():
    run = mx(30_000)
    excess = Decimal(30_000) - 3 * Decimal("117.31") * 30
    assert amount(run, "IMSS_EE_EXCESS") == q(excess * Decimal("0.004"))
    assert amount(run, "IMSS_ER_FIXED") == q(Decimal("117.31") * 30 * Decimal("0.2040"))
    below = mx(10_000)                                            # 10.000 < 3 UMA × 30 = 10.557,90: sin excedente
    assert amount(below, "IMSS_EE_EXCESS") == Decimal("0.00")


def test_mx_referencias_propias_salario_minimo_general_zlfn_y_uma():
    codes = {r["code"] for r in load_country("MX").references}
    assert {"SM_GENERAL_DAILY", "SM_ZLFN_DAILY", "UMA_DAILY"} <= codes
    assert ref("MX", "SM_ZLFN_DAILY", date(2026, 3, 1)).value > ref("MX", "SM_GENERAL_DAILY", date(2026, 3, 1)).value
    assert ref("MX", "SM_GENERAL_DAILY", date(2026, 3, 1)).record["source"]["status"] == "OFFICIAL"


def test_mx_isr_es_valor_digitado_no_motor_tributario():
    run = mx(30_000, amounts={"ISR_WITHHOLDING": "3500"})
    assert amount(run, "ISR_WITHHOLDING") == Decimal("3500.00")
    assert any(w["type"] == "EXTERNAL_INPUT" for w in run.warnings)
    assert describe("MX")["capabilities"]["income_tax_withholding"]["status"] == "NOT_IMPLEMENTED"


def test_mx_incapacidad_mayor_a_los_dias_trabajados_se_bloquea():
    with pytest.raises(InputValidationError):
        mx(30_000, worked="10", time={"paid_days": "0", "incapacity_days": "12"})


# ====================================================================== Perú
def pe(salary, **kw):
    return ENGINE.run(payload("PE", salary, **kw))


def test_pe_afp_y_essalud_sobre_la_remuneracion():
    run = pe(2_500, amounts={"FAMILY_ALLOWANCE": "113"})
    assert amount(run, "AFP_MANDATORY") == Decimal("250.00")
    assert amount(run, "AFP_INSURANCE") == Decimal("34.25") and amount(run, "AFP_COMMISSION") == Decimal("38.75")
    assert amount(run, "ESSALUD") == Decimal("225.00")
    assert amount(run, "GRATIFICATION_ACCRUAL") == q(Decimal(2500) / 6) and amount(run, "CTS_ACCRUAL") == q(Decimal(2500) / 12)


def test_pe_no_trata_la_gratificacion_como_el_13o_de_otro_pais():
    concepts = {c["concept"] for c in load_country("PE").concept_list}
    assert "GRATIFICATION_ACCRUAL" in concepts and "CTS_ACCRUAL" in concepts
    assert "THIRTEENTH_ACCRUAL" not in concepts and "SAC_ACCRUAL" not in concepts


def test_pe_limitaciones_declaradas_onp_renta_y_regimenes():
    gaps = " ".join(describe("PE")["known_gaps"])
    assert "ONP" in gaps and "quinta" in gaps and "MYPE" in gaps
    assert "CTS y gratificación por semestre" not in gaps          # ya no es una brecha: ver test_termination_peru


# ====================================================================== Chile
def cl(salary, period=("2026-09-01", "2026-09-30"), **kw):
    return ENGINE.run(payload("CL", salary, period, **kw))


def test_cl_ingreso_minimo_cambia_durante_2026():
    assert ref("CL", "MIN_INCOME", date(2026, 4, 30)).value == Decimal("539000")
    assert ref("CL", "MIN_INCOME", date(2026, 5, 1)).value == Decimal("553553")
    assert ref("CL", "MIN_INCOME", date(2026, 4, 30)).record["source"]["status"] == "OFFICIAL"
    assert ref("CL", "MIN_INCOME", date(2026, 5, 1)).record["source"]["status"] == "PENDING"     # sin norma oficial verificada


@pytest.mark.parametrize("day,hours", [(date(2026, 4, 25), "44"), (date(2026, 4, 26), "42"),
                                       (date(2028, 4, 25), "42"), (date(2028, 4, 26), "40")])
def test_cl_jornada_ley_21561_por_vigencia(day, hours):
    assert ref("CL", "WORKWEEK_HOURS", day).value == Decimal(hours)


def test_cl_sis_y_reforma_previsional_respetan_su_vigencia():
    """Tasas de la Superintendencia de Pensiones: SIS 1,54 % (ene-mar) y 1,62 % (desde abr); aporte de la reforma
    1 % (hasta jul-2026) y 3,5 % (desde ago-2026). Base bajo el tope: sin efecto de tope."""
    mar = cl(900_000, ("2026-03-01", "2026-03-31"))
    assert amount(mar, "SIS_EMPLOYER") == q(Decimal(900_000) * Decimal("0.0154"))
    assert amount(mar, "PENSION_REFORM_EMPLOYER") == q(Decimal(900_000) * Decimal("0.01"))
    apr = cl(900_000, ("2026-04-01", "2026-04-30"))
    assert amount(apr, "SIS_EMPLOYER") == q(Decimal(900_000) * Decimal("0.0162"))
    assert amount(apr, "PENSION_REFORM_EMPLOYER") == q(Decimal(900_000) * Decimal("0.01"))
    sep = cl(900_000)
    assert amount(sep, "PENSION_REFORM_EMPLOYER") == q(Decimal(900_000) * Decimal("0.035"))
    assert amount(sep, "SIS_EMPLOYER") == q(Decimal(900_000) * Decimal("0.0162"))


def test_cl_sis_desde_agosto_esta_marcado_como_posible_doble_conteo():
    """La SP dice que el 3,5 % de la reforma 'incluye la tasa para el financiamiento del SIS': la regla del SIS desde
    ago-2026 queda con interpretación CONFLICTING y la corrida lo advierte (no se presenta como cálculo cierto)."""
    sep = cl(900_000)
    assert sep.status == "COMPLETE_WITH_WARNINGS"
    assert any(w["type"] == "UNVERIFIED_RULE" and w["rule_id"] == "CL.SIS_EMPLOYER.3" for w in sep.warnings)
    jun = cl(900_000, ("2026-06-01", "2026-06-30"))
    assert not any(w.get("rule_id") == "CL.SIS_EMPLOYER.3" for w in jun.warnings)


def test_cl_periodo_que_cruza_el_cambio_de_sis_se_divide_por_dias():
    run = cl(900_000, ("2026-03-16", "2026-04-15"))          # 16 días con 1,54 % y 15 con 1,62 %
    expected = Decimal(900_000) * (Decimal("0.0154") * 16 + Decimal("0.0162") * 15) / 31
    assert abs(amount(run, "SIS_EMPLOYER") - expected) <= Decimal("0.01")
    assert run.status != "INCOMPLETE"


def test_cl_la_corrida_ya_no_es_incompleta_por_el_tope_de_90_uf():
    run = cl(900_000)
    assert run.status != "INCOMPLETE" and run.pending_rules == []
    assert not any(r["rule_key"] == "CL.CAP_90_UF" for r in load_country("CL").rules)


def test_cl_seguridad_social_sobre_remuneracion():
    run = cl(900_000, amounts={"LEGAL_GRATIFICATION": "50000"})
    assert amount(run, "AFP_CONTRIBUTION") == Decimal("90000.00") and amount(run, "HEALTH") == Decimal("63000.00")
    assert amount(run, "AFC_EMPLOYER") == q(Decimal(900_000) * Decimal("0.024"))


# ====================================================================== Brasil
def br(salary, **kw):
    return ENGINE.run(payload("BR", salary, **kw))


@pytest.mark.parametrize("salary,expected", [
    ("1621.00", "121.58"),            # fin del 1er tramo (7,5%)
    ("1621.01", "121.58"),
    ("2902.84", "236.94"),            # fin del 2º tramo
    ("4354.27", "411.11"),            # fin del 3er tramo
    ("8475.54", "988.09"),
    ("8475.55", "988.09"),            # techo del INSS
    ("8475.56", "988.09"),
    ("20000", "988.09"),
])
def test_br_inss_progresivo_frontera_de_tramos(salary, expected):
    assert amount(br(salary), "INSS_EMPLOYEE") == Decimal(expected)


def test_br_el_tope_solo_limita_al_empleado_no_a_la_contribucion_patronal():
    run = br("20000")
    assert base_value(run, "BR_INSS_EMPLOYEE_BASE") == Decimal("8475.55")
    assert amount(run, "INSS_EMPLOYER") == Decimal("4000.00")                    # 20% sin techo
    assert base_value(run, "BR_PAYROLL_BASE") == Decimal("20000")


def test_br_provisiones_13o_y_ferias_con_un_tercio():
    run = br("3600")
    assert amount(run, "THIRTEENTH_ACCRUAL") == Decimal("300.00")
    assert amount(run, "VACATION_ACCRUAL") == Decimal("400.00")                  # 1/12 × 4/3 = 1/9


# ====================================================================== Argentina
def ar(salary, period=("2026-09-01", "2026-09-30"), **kw):
    return ENGINE.run(payload("AR", salary, period, **kw))


def test_ar_el_smvm_cambia_cada_mes_y_no_hay_un_valor_anual_unico():
    refs = [r for r in load_country("AR").references if r["code"] == "SMVM"]
    assert len(refs) == 12
    assert ref("AR", "SMVM", date(2026, 8, 31)).value == Decimal("376600")
    assert ref("AR", "SMVM", date(2026, 9, 1)).value == Decimal("383800")
    assert ref("AR", "SMVM", date(2026, 12, 31)).value == Decimal("406400")
    with pytest.raises(MissingReferenceError):
        ref("AR", "SMVM", date(2027, 1, 1))                                       # sin dato: se bloquea, no se inventa


def test_ar_fuentes_del_smvm_oficial_desde_septiembre_secundaria_antes():
    by_month = {r["effective"]["from"][5:7]: r["source"]["status"] for r in load_country("AR").references if r["code"] == "SMVM"}
    assert all(by_month[m] == "OFFICIAL" for m in ("09", "10", "11", "12"))
    assert all(by_month[m] == "SECONDARY" for m in ("01", "02", "03", "04", "05", "06", "07", "08"))


@pytest.mark.parametrize("salary,warns", [("383799.99", True), ("383800", False), ("383800.01", False)])
def test_ar_aviso_de_salario_bajo_el_smvm_del_mes_frontera(salary, warns):
    run = ar(salary)
    assert any(w["type"] == "VALIDATION_WARNING" for w in run.warnings) is warns


def test_ar_aportes_y_provisiones():
    run = ar(700_000, amounts={"BONUS": "30000"})
    assert amount(run, "RETIREMENT_EMPLOYEE") == Decimal("77000.00") and amount(run, "PAMI_EMPLOYEE") == Decimal("21000.00")
    assert amount(run, "UNIFIED_CONTRIBUTION") == Decimal("126000.00")
    assert amount(run, "SAC_ACCRUAL") == q(Decimal(700_000) / 12)


# ====================================================================== Ecuador
def ec(salary, **kw):
    return ENGINE.run(payload("EC", salary, **kw))


def test_ec_sbu_2026_con_comunicado_oficial():
    r = ref("EC", "SBU", date(2026, 6, 1))
    assert r.value == Decimal("482") and r.record["source"]["status"] == "OFFICIAL"


def test_ec_iess_y_provisiones():
    run = ec(850, amounts={"BONUS": "50"})
    assert amount(run, "IESS_EMPLOYEE") == Decimal("80.33") and amount(run, "IESS_EMPLOYER") == Decimal("94.78")
    assert amount(run, "THIRTEENTH_ACCRUAL") == q(Decimal(850) / 12)
    assert amount(run, "FOURTEENTH_ACCRUAL") == q(Decimal(482) / 12)


def test_ec_defecto_conocido_decimo_cuarto_sin_prorrateo_esta_documentado():
    assert amount(ec(850, worked="15"), "FOURTEENTH_ACCRUAL") == q(Decimal(482) / 12)
    notes = next(r["notes"] for r in load_country("EC").rules if r["rule_key"] == "EC.FOURTEENTH_ACCRUAL")
    assert "sin prorrateo" in notes


# ====================================================================== Estados Unidos y Hong Kong
def test_us_no_tiene_motor_local_y_se_bloquea():
    with pytest.raises(CapabilityError):
        ENGINE.run(payload("US", 5000, jurisdictions=("FEDERAL",)))


def test_us_estructura_federal_state_local_y_exempt_non_exempt():
    manifest = load_country("US").manifest
    assert manifest["jurisdiction_levels"] == ["FEDERAL", "STATE", "LOCAL"]
    assert manifest["employee_classes"] == ["EXEMPT", "NON_EXEMPT"]
    caps = manifest["capabilities"]
    assert caps["state"]["status"] == "NOT_IMPLEMENTED" and caps["local"]["status"] == "NOT_IMPLEMENTED"


def test_us_reglas_federales_son_datos_no_implementados_y_solo_el_salario_minimo_tiene_fuente_oficial():
    rs = load_country("US")
    assert all(r["implementation_status"] == "NOT_IMPLEMENTED" and r["jurisdiction"] == "FEDERAL" for r in rs.rules)
    fed = ReferenceResolver(rs.references, "US", ["FEDERAL"])
    assert fed.resolve("FEDERAL_MIN_WAGE", date(2026, 9, 1)).value == Decimal("7.25")
    assert fed.resolve("FEDERAL_MIN_WAGE", date(2026, 9, 1)).record["source"]["status"] == "OFFICIAL"
    assert fed.resolve("SS_WAGE_BASE", date(2026, 9, 1)).record["source"]["status"] == "SECONDARY"
    overtime = next(r for r in rs.rules if r["rule_key"] == "US.FLSA_OVERTIME")
    assert overtime["applies_to"] == {"employment.exempt_status": ["NON_EXEMPT"]}


def test_hk_es_contexto_de_consolidacion_no_nomina_local():
    manifest = load_country("HK").manifest
    assert manifest["local_payroll_engine"] is False and manifest["consolidation_context"] is True
    assert describe("HK")["state"] == "consolidacion" and describe("HK")["coverage"]["rules_total"] == 0
    with pytest.raises(CapabilityError) as err:
        ENGINE.run(payload("HK", 5000))
    assert "consolidación" in str(err.value) and "investigación normativa independiente" in str(err.value)


# ====================================================================== estado real de cada contexto
def test_ningun_pais_esta_implementado_sin_validacion_profesional():
    for cc, info in describe_all().items():
        for name, cap in info["capabilities"].items():
            assert cap["status"] != "IMPLEMENTED", (cc, name)
        assert info["state"] != "implementado", cc


def test_estado_derivado_del_manifiesto():
    states = {cc: info["state"] for cc, info in describe_all().items()}
    assert states == {"CO": "parcial", "MX": "parcial", "PE": "parcial", "CL": "parcial", "BR": "parcial",
                      "AR": "parcial", "EC": "parcial", "US": "no_implementado", "HK": "consolidacion"}


def test_todos_los_paises_con_motor_declaran_impuesto_no_implementado():
    for cc in ("MX", "PE", "CL", "BR", "AR", "EC"):
        assert describe(cc)["capabilities"]["income_tax_withholding"]["status"] == "NOT_IMPLEMENTED"
    assert describe("CO")["capabilities"]["income_tax_withholding"]["status"] == "PARTIALLY_IMPLEMENTED"     # solo Colombia, procedimiento 1


def test_cobertura_se_calcula_de_los_datos():
    cov = describe("CO")["coverage"]
    assert cov["rules_total"] == cov["rules_implemented"] + cov["rules_partial"] + cov["rules_not_implemented"]
    assert cov["rules_pending_professional_validation"] == cov["rules_total"]                 # nadie ha validado nada
