"""Argentina — liquidación final. Esperado desde el texto vigente de la LCT (InfoLeg, texto actualizado con la Ley 27.802,
B.O. 6-mar-2026): art. 123 (SAC en la extinción: 1/12 de lo devengado en la fracción del semestre), arts. 150-156
(vacaciones), art. 245 (indemnización), arts. 231-233 (preaviso e integración del mes)."""

from decimal import Decimal

import pytest

from payroll_engine.errors import InputValidationError

from .term_helpers import D, info, line_trace, lines, q, term

SAL = D(1_000_000)


def ar(end, hire="2020-01-10", cause="DISMISSAL_WITHOUT_CAUSE", salary="1000000", **kw):
    return term("AR", hire, end, cause, salary, **kw)


# ------------------------------------------------------------------------------------------- SAC (art. 123)
@pytest.mark.parametrize("end,months", [
    ("2026-03-15", D("2.5")),           # 1.º semestre: 1-ene .. 15-mar
    ("2026-06-30", D(6)),
    ("2026-07-01", D(1) / 30),          # el 1-jul empieza el 2.º semestre: un solo día
    ("2026-09-15", D("2.5")),           # 2.º semestre: 1-jul .. 15-sep
    ("2026-12-31", D(6)),
])
def test_sac_proporcional_por_semestre_juridico(end, months):
    assert lines(ar(end))["AR_SAC_PROPORCIONAL"] == q(SAL * months / 12)


def test_sac_no_se_cuenta_desde_el_1_de_enero_en_el_segundo_semestre():
    """P0 heredado: desde 1-ene aunque el cese sea en septiembre (273/180 del semestre = más de un semestre)."""
    run = ar("2026-09-15")
    legacy = q(SAL / 2 * D(258) / 180)                         # heredado: 1-ene .. 15-sep = 258 días / 180
    assert lines(run)["AR_SAC_PROPORCIONAL"] != legacy
    assert lines(run)["AR_SAC_PROPORCIONAL"] == q(SAL * D("2.5") / 12)


def test_sac_ingreso_a_mitad_de_semestre():
    run = ar("2026-09-15", hire="2026-08-01")                  # 1-ago .. 15-sep = 1 mes y 15 días
    assert lines(run)["AR_SAC_PROPORCIONAL"] == q(SAL * D("1.5") / 12)
    run = ar("2026-03-31", hire="2026-02-10")                  # 10-feb .. 31-mar = 1 mes y 22 días (extremos inclusivos)
    assert lines(run)["AR_SAC_PROPORCIONAL"] == q(SAL * (D(1) + D(22) / 30) / 12)


def test_sac_egreso_a_mitad_de_semestre_y_con_historial_de_remuneraciones():
    history = [{"month": "2026-07", "amount": "1000000"}, {"month": "2026-08", "amount": "1200000"},
               {"month": "2026-09", "amount": "600000"}]           # septiembre parcial (15 días devengados)
    run = ar("2026-09-15", extra={"salary_history": history})
    assert lines(run)["AR_SAC_PROPORCIONAL"] == q(D(2_800_000) / 12)
    assert line_trace(run, "AR_T_SAC_ACCRUED")["details"]["source"] == "HISTORY"
    assert not any("sin historial" in w["message"] for w in run.warnings if w["type"] == "MECHANISM_WARNING" and "AR_T_SAC" in w.get("rule_id", ""))


def test_sac_sin_historial_supone_remuneracion_constante_y_lo_advierte():
    run = ar("2026-09-15")
    assert line_trace(run, "AR_T_SAC_ACCRUED")["details"]["source"] == "FALLBACK_MONTHLY"
    assert any(w["type"] == "MECHANISM_WARNING" and "remuneración constante" in w["message"] for w in run.warnings)


def test_el_sac_del_semestre_anterior_no_entra_si_el_cese_es_en_el_nuevo_semestre():
    history = [{"month": "2026-06", "amount": "9000000"}, {"month": "2026-07", "amount": "1000000"}]
    run = ar("2026-07-31", extra={"salary_history": history})
    assert lines(run)["AR_SAC_PROPORCIONAL"] == q(D(1_000_000) / 12)


# ------------------------------------------------------------------------------------------- vacaciones (arts. 150-156)
@pytest.mark.parametrize("hire,days", [
    ("2022-01-01", 14),              # al 31-dic-2026: exactamente 5 años -> 14 días
    ("2021-12-31", 21),              # 5 años y un día -> 21 días
    ("2017-01-01", 21),              # 10 años exactos
    ("2016-12-31", 28),              # 10 años y un día
    ("2007-01-01", 28),              # 20 años exactos
    ("2006-12-31", 35),
    ("2026-02-01", 14),
])
def test_escala_de_vacaciones_por_antiguedad_al_31_de_diciembre(hire, days):
    run = ar("2026-06-30", hire=hire, cause="RESIGNATION")
    assert info(run, "AR_T_VACATION_ENTITLEMENT_DAYS") == days


def test_vacaciones_proporcionales_y_valor_por_veinticincoavo():
    run = ar("2026-03-15")                                    # antigüedad al 31-dic-2026: 6 años -> 21 días
    prorated = D(21) * 74 / 365                               # 1-ene .. 15-mar = 74 días
    assert lines(run)["AR_VACACIONES_NO_GOZADAS"] == q(SAL / 25 * prorated)


def test_vacaciones_dias_pendientes_y_gozados():
    run = ar("2026-03-15", extra={"vacation_history": {"days_pending_prior": 7, "days_taken_current": 2}})
    due = D(21) * 74 / 365 + 7 - 2
    assert lines(run)["AR_VACACIONES_NO_GOZADAS"] == q(SAL / 25 * due)
    everything_taken = ar("2026-03-15", extra={"vacation_history": {"days_taken_current": 14}})
    assert lines(everything_taken)["AR_VACACIONES_NO_GOZADAS"] == 0


# ------------------------------------------------------------------------------------------- indemnización (art. 245)
@pytest.mark.parametrize("end,years", [
    ("2026-04-08", 6),               # 6 años, 2 meses y 30 días: la fracción NO supera 3 meses
    ("2026-04-09", 6),               # 6 años y 3 meses exactos: tampoco (la fracción debe ser MAYOR de tres meses)
    ("2026-04-10", 7),               # 3 meses y un día: suma un año
])
def test_indemnizacion_fraccion_mayor_de_tres_meses(end, years):
    run = ar(end, hire="2020-01-10")
    assert lines(run)["AR_INDEMNIZACION_ART_245"] == SAL * years


def test_indemnizacion_minimo_de_un_mes():
    run = ar("2026-09-15", hire="2026-01-10", employment={"probation_months": 0})
    assert lines(run)["AR_INDEMNIZACION_ART_245"] == SAL          # 8 meses de servicio -> 1 año (fracción > 3 meses)


@pytest.mark.parametrize("cct,salary,expected_base", [
    ("500000", "1000000", D(1_000_000)),      # 3 × 500.000 = 1.500.000 > salario: sin tope
    ("300000", "2000000", D(1_340_000)),      # 3 × 300.000 = 900.000 < 67 % de 2.000.000 = 1.340.000: rige el piso del 67 %
    ("600000", "2000000", D(1_800_000)),      # 3 × 600.000 = 1.800.000: rige el tope del convenio
])
def test_indemnizacion_tope_por_convenio_con_piso_del_67_por_ciento(cct, salary, expected_base):
    run = ar("2026-04-09", hire="2020-01-10", salary=salary, amounts={"cct_average_salary": cct})
    assert lines(run)["AR_INDEMNIZACION_ART_245"] == q(expected_base * 6)
    assert not any("tope de la base NO aplicado" in w["message"] for w in run.warnings)


def test_indemnizacion_sin_dato_del_convenio_no_aplica_el_tope_y_lo_advierte():
    run = ar("2026-04-09", hire="2020-01-10")
    assert any("falta el dato 'amounts.cct_average_salary'" in w["message"] for w in run.warnings)


def test_indemnizacion_usa_la_mejor_remuneracion_mensual_del_ultimo_ano_sin_el_sac():
    history = [{"month": f"2025-{m:02d}", "amount": "900000"} for m in range(5, 13)] + [{"month": "2026-01", "amount": "1500000"},
              {"month": "2026-02", "amount": "1000000"}, {"month": "2026-03", "amount": "1000000"}]
    run = ar("2026-04-09", hire="2020-01-10", extra={"salary_history": history})
    assert lines(run)["AR_INDEMNIZACION_ART_245"] == D(1_500_000) * 6
    assert line_trace(run, "AR_T_BEST_REMUNERATION")["details"]["method"] == "MAX"


def test_indemnizacion_solo_por_despido_sin_causa_de_contrato_indefinido_tras_el_periodo_de_prueba():
    for cause in ("RESIGNATION", "DISMISSAL_WITH_CAUSE", "MUTUAL_AGREEMENT", "DEATH"):
        assert "AR_INDEMNIZACION_ART_245" not in lines(ar("2026-04-09", cause=cause)) or lines(ar("2026-04-09", cause=cause))["AR_INDEMNIZACION_ART_245"] == 0
    in_probation = ar("2026-04-09", hire="2026-01-10")            # 2 meses y 30 días
    assert lines(in_probation).get("AR_INDEMNIZACION_ART_245", 0) == 0
    exactly_six = ar("2026-07-09", hire="2026-01-10")             # 6 meses exactos: aún dentro del período de prueba
    assert lines(exactly_six).get("AR_INDEMNIZACION_ART_245", 0) == 0
    beyond = ar("2026-07-10", hire="2026-01-10")                  # 6 meses y un día: superado
    assert lines(beyond)["AR_INDEMNIZACION_ART_245"] > 0


# ------------------------------------------------------------------------------------------- preaviso e integración
@pytest.mark.parametrize("end,hire,months", [("2026-03-15", "2020-01-10", 2), ("2026-03-15", "2021-03-16", 1), ("2026-03-15", "2021-03-15", 2)])
def test_preaviso_un_mes_hasta_cinco_anos_y_dos_meses_si_supera(end, hire, months):
    run = ar(end, hire=hire)
    assert lines(run)["AR_PREAVISO_SUSTITUTIVO"] == SAL * months


def test_preaviso_cinco_anos_exactos_es_un_mes_y_un_dia_mas_son_dos():
    exact = ar("2026-03-15", hire="2021-03-16")           # 16-mar-2021 .. 15-mar-2026 = 5 años exactos
    plus = ar("2026-03-16", hire="2021-03-16")            # 5 años y un día
    assert lines(exact)["AR_PREAVISO_SUSTITUTIVO"] == SAL and lines(plus)["AR_PREAVISO_SUSTITUTIVO"] == SAL * 2


def test_no_hay_preaviso_si_se_otorgo_ni_en_periodo_de_prueba():
    assert "AR_PREAVISO_SUSTITUTIVO" not in lines(ar("2026-03-15", termination={"notice_given": True}))
    assert lines(ar("2026-03-15", hire="2026-01-10")).get("AR_PREAVISO_SUSTITUTIVO", 0) == 0


@pytest.mark.parametrize("end,days", [("2026-03-15", 16), ("2026-03-31", 0), ("2026-02-27", 1), ("2026-09-15", 15)])
def test_integracion_del_mes_de_despido(end, days):
    run = ar(end)
    assert lines(run).get("AR_INTEGRACION_MES_DESPIDO", 0) == q(SAL / 30 * days)


def test_integracion_no_procede_con_preaviso():
    assert "AR_INTEGRACION_MES_DESPIDO" not in lines(ar("2026-03-15", termination={"notice_given": True}))


# ------------------------------------------------------------------------------------------- fuentes, total y entrada
def test_las_reglas_de_arg_tienen_fuente_oficial_infoleg_y_texto_de_la_ley_27802():
    run = ar("2026-03-15")
    src = {l["concept"]: l["source"] for l in run.trace["lines"]}
    for concept in ("AR_SAC_PROPORCIONAL", "AR_INDEMNIZACION_ART_245", "AR_PREAVISO_SUSTITUTIVO", "AR_VACACIONES_NO_GOZADAS"):
        assert src[concept]["status"] == "OFFICIAL" and "infoleg.gob.ar" in src[concept]["official_url"]
    assert "Ley 27.802" in src["AR_INDEMNIZACION_ART_245"]["legal_reference"]


def test_total_de_la_liquidacion_es_la_suma_de_las_lineas():
    run = ar("2026-03-15")
    assert run.result["totals"]["neto_pagado"] == sum(lines(run).values())


def test_causa_no_soportada_por_argentina_se_bloquea():
    with pytest.raises(InputValidationError):
        ar("2026-03-15", cause="INDIRECT_DISMISSAL")
