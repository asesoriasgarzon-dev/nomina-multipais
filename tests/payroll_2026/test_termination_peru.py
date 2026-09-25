"""Perú — liquidación por cese: CTS, gratificación, vacaciones e indemnización, cada mecanismo con su propia ventana
jurídica (la CTS y la gratificación NO comparten fórmula). Esperado calculado aquí con Decimal desde el texto de la norma:
TUO CTS (D.S. 001-97-TR arts. 2, 9, 18, 21), D.S. 005-2002-TR art. 5, D.S. 012-92-TR art. 23 y TUO D.Leg. 728 art. 38."""

from decimal import Decimal

import pytest

from payroll_engine.errors import InputValidationError

from .term_helpers import D, info, line_trace, lines, q, term

BASIC, FAMILY, GRAT = D(3000), D(113), D(3113)
AMOUNTS = {"family_allowance": "113", "last_gratification": "3113"}
CTS_BASE = BASIC + FAMILY + GRAT / 6                 # art. 18: 1/6 de la última gratificación se suma a la remuneración computable
GRAT_BASE = BASIC + FAMILY                            # la gratificación no incluye el 1/6 de sí misma
IND_BASE = BASIC + FAMILY


def pe(end, hire="2024-03-10", cause="DISMISSAL_WITHOUT_CAUSE", **kw):
    kw.setdefault("amounts", AMOUNTS)
    return term("PE", hire, end, cause, "3000", **kw)


# ------------------------------------------------------------------------------------------- CTS trunca
@pytest.mark.parametrize("end,months,days", [
    ("2026-07-20", 2, 20),          # semestre mayo-octubre: 1-may .. 20-jul
    ("2026-09-30", 5, 0),
    ("2026-10-31", 6, 0),
    ("2026-04-30", 6, 0),           # semestre noviembre-abril: 1-nov .. 30-abr
    ("2026-01-31", 3, 0),
    ("2026-05-01", 0, 1),           # el 1-may empieza otro semestre: un solo día
    ("2026-11-15", 0, 15),
])
def test_cts_trunca_por_dozavos_y_treintavos_del_semestre(end, months, days):
    run = pe(end)
    expected = CTS_BASE * (D(months) / 12 + D(days) / 360)
    assert lines(run)["PE_CTS_TRUNCA"] == q(expected)


def test_cts_usa_un_sexto_de_la_ultima_gratificacion_en_la_base():
    run = pe("2026-09-30")
    base = next(b for b in run.trace["bases"] if b["base"] == "PE.CTS_BASE")
    assert D(base["value"]) == CTS_BASE
    contrib = next(c for c in base["contributions"] if c["concept"] == "PE_T_LAST_GRATIFICATION")
    assert D(contrib["contributed"]) == q(GRAT / 6) or abs(D(contrib["contributed"]) - GRAT / 6) < D("0.0001")
    without = pe("2026-09-30", amounts={"family_allowance": "113"})
    assert lines(without)["PE_CTS_TRUNCA"] < lines(run)["PE_CTS_TRUNCA"]


def test_cts_ingreso_a_mitad_de_semestre_se_recorta_por_la_fecha_de_ingreso():
    run = pe("2026-09-30", hire="2026-08-15")             # 15-ago .. 30-sep = 1 mes y 16 días
    assert lines(run)["PE_CTS_TRUNCA"] == q(CTS_BASE * (D(1) / 12 + D(16) / 360))


def test_cts_exige_un_mes_de_servicios():
    assert lines(pe("2026-09-30", hire="2026-09-10"))["PE_CTS_TRUNCA"] == 0                  # 21 días de servicio
    assert lines(pe("2026-09-30", hire="2026-08-31"))["PE_CTS_TRUNCA"] > 0                  # 1 mes exacto (31-ago .. 30-sep)


# ------------------------------------------------------------------------------------------- gratificación trunca
@pytest.mark.parametrize("end,months", [
    ("2026-06-30", 6), ("2026-07-20", 0), ("2026-07-31", 1), ("2026-09-30", 3), ("2026-12-31", 6), ("2026-01-31", 1),
    ("2026-06-29", 5),               # junio incompleto no cuenta
])
def test_gratificacion_trunca_es_un_sexto_por_mes_calendario_completo(end, months):
    run = pe(end)
    assert lines(run)["PE_GRATIFICACION_TRUNCA"] == q(GRAT_BASE * D(months) / 6)


def test_gratificacion_ingreso_a_mitad_de_mes_no_cuenta_el_mes_parcial():
    run = pe("2026-09-30", hire="2026-08-15")             # agosto parcial: solo septiembre completo
    assert lines(run)["PE_GRATIFICACION_TRUNCA"] == q(GRAT_BASE / 6)


def test_gratificacion_no_incluye_el_sexto_de_la_ultima_gratificacion():
    run = pe("2026-12-31")
    base = next(b for b in run.trace["bases"] if b["base"] == "PE.GRATIFICATION_BASE")
    assert D(base["value"]) == GRAT_BASE


def test_bonificacion_extraordinaria_9_por_ciento_solo_con_essalud():
    run = pe("2026-09-30")
    assert lines(run)["PE_BONIFICACION_EXTRAORDINARIA"] == q(lines(run)["PE_GRATIFICACION_TRUNCA"] * D("0.09"))
    eps = pe("2026-09-30", employment={"health_scheme": "EPS"})
    assert "PE_BONIFICACION_EXTRAORDINARIA" not in lines(eps) or lines(eps)["PE_BONIFICACION_EXTRAORDINARIA"] == 0
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "PE_BONIFICACION_EXTRAORDINARIA" for w in run.warnings)


def test_cts_y_gratificacion_son_mecanismos_distintos_con_ventanas_distintas():
    """El P0 heredado: la misma fórmula (año calendario/360) para ambos. Aquí difieren en ventana y en conteo."""
    run = pe("2026-09-30")
    cts, grat = line_trace(run, "PE_CTS_TRUNCA"), line_trace(run, "PE_GRATIFICACION_TRUNCA")
    assert cts["details"]["unit"] == "MONTHS_AND_DAYS" and grat["details"]["unit"] == "MONTHS_COMPLETE_CALENDAR"
    assert "2026-05-01 .. 2026-09-30" in cts["details"]["window"] and "2026-07-01 .. 2026-09-30" in grat["details"]["window"]
    assert lines(run)["PE_CTS_TRUNCA"] != lines(run)["PE_GRATIFICACION_TRUNCA"]


def test_ya_no_se_calcula_con_el_anio_calendario_sobre_360():
    """Legado: CTS = gratificación = salario × días del año / 360. Con cese el 30-sep-2026 daría 3000 × 273/360 = 2275."""
    run = pe("2026-09-30", hire="2020-01-01")
    legacy_style = q(D(3000) * 273 / 360)
    assert lines(run)["PE_CTS_TRUNCA"] != legacy_style and lines(run)["PE_GRATIFICACION_TRUNCA"] != legacy_style


# ------------------------------------------------------------------------------------------- vacaciones truncas
def test_vacaciones_truncas_dozavos_y_treintavos_desde_el_ultimo_aniversario():
    run = pe("2026-07-20")                                # ingreso 2024-03-10: desde 2026-03-10 son 4 meses y 11 días
    assert lines(run)["PE_VACACIONES_TRUNCAS"] == q(IND_BASE * (D(4) / 12 + D(11) / 360))


def test_vacaciones_truncas_no_incluyen_las_gratificaciones_periodicas():
    base = next(b for b in pe("2026-07-20").trace["bases"] if b["base"] == "PE.VACATION_BASE")
    assert D(base["value"]) == BASIC + FAMILY             # D.S. 012-92-TR art. 16: excluye las remuneraciones periódicas


def test_vacaciones_truncas_exigen_un_mes_de_servicios():
    assert lines(pe("2026-09-30", hire="2026-09-10"))["PE_VACACIONES_TRUNCAS"] == 0


def test_vacaciones_adquiridas_y_no_gozadas_se_pagan_a_un_treintavo_por_dia():
    run = pe("2026-07-20", extra={"vacation_history": {"days_pending_prior": 10}})
    assert lines(run)["PE_VACACIONES_ADQUIRIDAS"] == q(IND_BASE / 30 * 10)


# ------------------------------------------------------------------------------------------- indemnización
def test_indemnizacion_por_despido_arbitrario_una_y_media_por_ano_con_dozavos_y_treintavos():
    run = pe("2026-07-20")                                # 2 años, 4 meses, 11 días
    years = D(2) + D(4) / 12 + D(11) / 360
    assert lines(run)["PE_INDEMNIZACION_DESPIDO_ARBITRARIO"] == q(IND_BASE * D("1.5") * years)


def test_indemnizacion_tope_de_12_remuneraciones():
    run = pe("2026-07-20", hire="2000-01-01")
    assert lines(run)["PE_INDEMNIZACION_DESPIDO_ARBITRARIO"] == q(IND_BASE * 12)
    assert line_trace(run, "PE_INDEMNIZACION_DESPIDO_ARBITRARIO")["details"]["cap_applied"] is True


@pytest.mark.parametrize("hire,applies", [("2026-05-16", False),     # 2 meses y 30 días al 15-ago
                                           ("2026-05-15", True),      # 3 meses completos
                                           ("2026-06-01", False)])
def test_indemnizacion_solo_supera_el_periodo_de_prueba_de_3_meses(hire, applies):
    run = pe("2026-08-15", hire=hire)
    assert ("PE_INDEMNIZACION_DESPIDO_ARBITRARIO" in lines(run) and lines(run)["PE_INDEMNIZACION_DESPIDO_ARBITRARIO"] > 0) is applies


@pytest.mark.parametrize("cause", ["RESIGNATION", "DISMISSAL_WITH_CAUSE", "MUTUAL_AGREEMENT", "FIXED_TERM_EXPIRY", "DEATH"])
def test_sin_despido_arbitrario_no_hay_indemnizacion(cause):
    run = pe("2026-07-20", cause=cause)
    assert lines(run).get("PE_INDEMNIZACION_DESPIDO_ARBITRARIO", 0) == 0
    assert lines(run)["PE_CTS_TRUNCA"] > 0                # los beneficios sociales se pagan en cualquier causa


def test_plazo_fijo_indemniza_mes_y_medio_por_mes_restante_con_tope_12_y_fuente_pendiente():
    run = pe("2026-07-20", contract="FIXED_TERM", employment={"contract_end_date": "2026-12-31"})
    remaining = D(5) + D(11) / 30                         # 21-jul .. 31-dic = 5 meses y 11 días
    assert lines(run)["PE_INDEMNIZACION_PLAZO_FIJO"] == q(IND_BASE * D("1.5") * remaining)
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "PE_INDEMNIZACION_PLAZO_FIJO" for w in run.warnings)
    far = pe("2026-07-20", contract="FIXED_TERM", employment={"contract_end_date": "2030-12-31"})
    assert lines(far)["PE_INDEMNIZACION_PLAZO_FIJO"] == q(IND_BASE * 12)


def test_plazo_fijo_exige_fecha_de_fin():
    with pytest.raises(InputValidationError) as err:
        pe("2026-07-20", contract="FIXED_TERM")
    assert "contract_end_date" in " ".join(err.value.details)


# ------------------------------------------------------------------------------------------- entrada, régimen y fuentes
def test_regimen_distinto_al_general_se_bloquea():
    with pytest.raises(InputValidationError) as err:
        pe("2026-07-20", employment={"labor_regime": "MYPE"})
    assert "régimen laboral general" in err.value.message


def test_causa_y_contrato_deben_ser_los_soportados_por_el_pais():
    with pytest.raises(InputValidationError):
        pe("2026-07-20", cause="INDIRECT_DISMISSAL")
    with pytest.raises(InputValidationError):
        pe("2026-07-20", contract="WORK_COMPLETION")


def test_sin_fecha_de_ingreso_o_terminacion_o_causa_se_bloquea():
    with pytest.raises(InputValidationError):
        term("PE", "", "2026-07-20", "RESIGNATION", "3000")
    with pytest.raises(InputValidationError):
        term("PE", "2026-01-01", "2025-01-01", "RESIGNATION", "3000")


def test_las_fuentes_de_cts_gratificacion_y_vacaciones_son_oficiales_y_la_indemnizacion_de_plazo_fijo_no():
    run = pe("2026-07-20")
    rules = {l["concept"]: l["source"]["status"] for l in run.trace["lines"]}
    assert rules["PE_CTS_TRUNCA"] == rules["PE_GRATIFICACION_TRUNCA"] == rules["PE_VACACIONES_TRUNCAS"] == "OFFICIAL"
    assert rules["PE_INDEMNIZACION_DESPIDO_ARBITRARIO"] == "OFFICIAL"
    assert rules["PE_VACACIONES_INDEMNIZACION"] == "SECONDARY"


def test_el_total_es_la_suma_exacta_de_las_lineas_redondeadas():
    run = pe("2026-07-20", extra={"vacation_history": {"days_pending_prior": 3}})
    assert run.result["totals"]["neto_pagado"] == sum(lines(run).values())
