"""Brasil (rescisão) y Ecuador (liquidación). Esperado desde el texto oficial: Planalto (CLT arts. 129-147, 484-A, 487;
Lei 4.090/62; Lei 12.506/2011; Lei 8.036/90 arts. 15 y 18; CF art. 7º) y el Código del Trabajo del Ecuador (Codificación
2005-017, última modificación 2020: arts. 47, 49, 55, 69, 111, 113, 185, 188)."""

from decimal import Decimal

import pytest

from payroll_engine.errors import InputValidationError
from payroll_engine.loader import load_country

from .term_helpers import D, info, line_trace, lines, monthly, q, term

# =============================================================================================== BRASIL
SAL = D(5000)


def br(end, hire="2021-03-17", cause="DISMISSAL_WITHOUT_CAUSE", salary="5000", **kw):
    return term("BR", hire, end, cause, salary, **kw)


@pytest.mark.parametrize("end,months", [("2026-09-20", 9), ("2026-09-14", 8), ("2026-09-15", 9), ("2026-01-14", 0), ("2026-01-15", 1),
                                         ("2026-12-31", 12)])
def test_br_13o_un_doceavo_por_mes_con_15_dias_o_mas_de_trabajo(end, months):
    run = br(end)
    assert lines(run).get("BR_13O_PROPORCIONAL", 0) == q(SAL * months / 12)


def test_br_13o_ingreso_a_mitad_de_mes_solo_cuenta_si_hay_15_dias():
    assert lines(br("2026-12-31", hire="2026-03-17"))["BR_13O_PROPORCIONAL"] == q(SAL * 10 / 12)      # marzo: 15 días (17..31) cuenta
    assert lines(br("2026-12-31", hire="2026-03-18"))["BR_13O_PROPORCIONAL"] == q(SAL * 9 / 12)       # 14 días: no cuenta


@pytest.mark.parametrize("cause,paid", [("DISMISSAL_WITHOUT_CAUSE", True), ("INDIRECT_DISMISSAL", True), ("MUTUAL_AGREEMENT", True),
                                         ("FIXED_TERM_EXPIRY", True), ("RETIREMENT", True), ("DISMISSAL_WITH_CAUSE", False)])
def test_br_13o_no_se_paga_en_justa_causa(cause, paid):
    assert (lines(br("2026-09-20", cause=cause)).get("BR_13O_PROPORCIONAL", 0) > 0) is paid


def test_br_13o_en_pedido_de_dimision_tiene_fuente_pendiente_y_advertencia():
    run = br("2026-09-20", cause="RESIGNATION")
    assert lines(run)["BR_13O_PEDIDO_DEMISSAO"] == q(SAL * 9 / 12)
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "BR_13O_PEDIDO_DEMISSAO" for w in run.warnings)


@pytest.mark.parametrize("end,months", [("2026-09-20", 6), ("2026-09-30", 6), ("2026-10-01", 7), ("2026-10-02", 7), ("2026-03-30", 0)])
def test_br_ferias_proporcionales_un_doceavo_por_mes_o_fraccion_superior_a_14_dias(end, months):
    """Aniversario 17-mar: al 30-sep son 6 meses y 14 días (no suma); al 1-oct, 6 meses y 15 días (suma un mes)."""
    assert lines(br(end)).get("BR_FERIAS_PROPORCIONAIS", 0) == q(SAL * months / 12)


def test_br_ferias_frontera_14_y_15_dias():
    assert lines(br("2026-09-30"))["BR_FERIAS_PROPORCIONAIS"] == q(SAL * 6 / 12)              # fracción de 14 días
    assert lines(br("2026-10-01"))["BR_FERIAS_PROPORCIONAIS"] == q(SAL * 7 / 12)              # fracción de 15 días


def test_br_ferias_adicional_de_un_tercio_sobre_proporcionales_y_vencidas():
    run = br("2026-09-20", extra={"vacation_history": {"days_pending_prior": 30}})
    prop, vencidas = lines(run)["BR_FERIAS_PROPORCIONAIS"], lines(run)["BR_FERIAS_VENCIDAS"]
    assert vencidas == SAL
    assert lines(run)["BR_FERIAS_TERCO_PROPORCIONAIS"] == q(prop / 3) and lines(run)["BR_FERIAS_TERCO_VENCIDAS"] == q(vencidas / 3)


def test_br_justa_causa_paga_saldo_y_vencidas_pero_no_proporcionales():
    run = br("2026-09-20", cause="DISMISSAL_WITH_CAUSE", extra={"vacation_history": {"days_pending_prior": 30}})
    got = lines(run)
    assert "BR_FERIAS_PROPORCIONAIS" not in got and "BR_13O_PROPORCIONAL" not in got and "BR_AVISO_PREVIO_INDENIZADO" not in got
    assert got["BR_FERIAS_VENCIDAS"] == SAL and got["BR_SALDO_SALARIO"] == q(SAL * 20 / 30)


def test_br_ferias_menos_de_12_meses_sin_justa_causa_o_termino_de_contrato():
    run = br("2026-09-20", hire="2026-03-01", contract="FIXED_TERM", cause="FIXED_TERM_EXPIRY", employment={"contract_end_date": "2026-09-20"})
    assert lines(run)["BR_FERIAS_PROPORCIONAIS"] == q(SAL * 7 / 12)           # 1-mar .. 20-sep: 6 meses y 20 días
    assert lines(br("2026-09-20", hire="2026-03-01", cause="DISMISSAL_WITH_CAUSE")).get("BR_FERIAS_PROPORCIONAIS", 0) == 0


@pytest.mark.parametrize("hire,days", [("2026-03-01", 30), ("2025-09-22", 30), ("2025-09-21", 33), ("2016-09-20", 60),
                                        ("2006-09-20", 90), ("1980-01-01", 90)])
def test_br_aviso_previo_30_dias_mas_3_por_ano_hasta_90(hire, days):
    """Lei 12.506: 30 días hasta un año de servicio + 3 por año, máximo 60 adicionales (total 90)."""
    assert info(br("2026-09-20", hire=hire), "BR_T_NOTICE_DAYS") == days


def test_br_aviso_previo_indemnizado_solo_si_el_empleador_no_lo_concede():
    run = br("2026-09-20")                                      # 5 años completos: 45 días
    assert lines(run)["BR_AVISO_PREVIO_INDENIZADO"] == q(SAL / 30 * 45)
    assert "BR_AVISO_PREVIO_INDENIZADO" not in lines(br("2026-09-20", termination={"notice_given": True}))


def test_br_acuerdo_484a_aviso_por_mitad_y_multa_del_20_por_ciento():
    run = br("2026-09-20", cause="MUTUAL_AGREEMENT", amounts={"fgts_balance": "20000"})
    assert lines(run)["BR_AVISO_PREVIO_ACORDO"] == q(SAL / 30 * 45 / 2)
    assert lines(run)["BR_FGTS_MULTA_20"] == D("4000.00") and "BR_FGTS_MULTA_40" not in lines(run)


@pytest.mark.parametrize("cause,concept,amount", [("DISMISSAL_WITHOUT_CAUSE", "BR_FGTS_MULTA_40", "8000.00"),
                                                    ("INDIRECT_DISMISSAL", "BR_FGTS_MULTA_40", "8000.00"),
                                                    ("MUTUAL_AGREEMENT", "BR_FGTS_MULTA_20", "4000.00")])
def test_br_multa_del_fgts_40_y_20_sobre_el_saldo(cause, concept, amount):
    assert lines(br("2026-09-20", cause=cause, amounts={"fgts_balance": "20000"}))[concept] == D(amount)


def test_br_sin_saldo_del_fgts_la_multa_es_cero_y_lo_advierte():
    run = br("2026-09-20")
    assert lines(run)["BR_FGTS_MULTA_40"] == 0 and any(w["type"] == "VALIDATION_WARNING" for w in run.warnings)


def test_br_multa_no_aplica_en_renuncia_ni_justa_causa_y_el_aviso_no_cumplido_se_descuenta():
    for cause in ("RESIGNATION", "DISMISSAL_WITH_CAUSE"):
        assert lines(br("2026-09-20", cause=cause, amounts={"fgts_balance": "20000"})).get("BR_FGTS_MULTA_40", 0) == 0
    run = br("2026-09-20", cause="RESIGNATION")
    assert lines(run)["BR_AVISO_PREVIO_DESCUENTO"] == SAL and run.result["totals"]["total_deducciones"] == SAL


def test_br_deposito_fgts_8_por_ciento_es_costo_del_empleador_y_no_suma_al_neto():
    run = br("2026-09-20")
    assert lines(run)["BR_FGTS_RESCISAO"] == q(lines(run)["BR_SALDO_SALARIO"] * D("0.08"))
    assert run.result["totals"]["neto_pagado"] == sum(v for c, v in lines(run).items() if not c.startswith("BR_FGTS"))
    assert run.result["totals"]["total_aportes_patronales"] == lines(run)["BR_FGTS_RESCISAO"] + lines(run)["BR_FGTS_MULTA_40"]


def test_br_fuentes_oficiales_del_planalto():
    run = br("2026-09-20", amounts={"fgts_balance": "1"})
    src = {l["concept"]: l["source"] for l in run.trace["lines"]}
    for concept in ("BR_13O_PROPORCIONAL", "BR_FERIAS_PROPORCIONAIS", "BR_AVISO_PREVIO_INDENIZADO", "BR_FGTS_MULTA_40"):
        assert src[concept]["status"] == "OFFICIAL" and "planalto.gov.br" in src[concept]["official_url"]


def test_br_horas_extra_50_noturno_20_y_divisor_en_conflicto_declarado():
    run = monthly("BR", 5000, ("2026-09-01", "2026-09-30"), time={"overtime_hours_50": "10", "night_hours": "20", "holiday_hours": "8"})
    hour = D(5000) / 220
    assert run.line("BR_OVERTIME")["amount"] == q(hour * (D("1.5") * 10 + D("0.2") * 20 + D(1) * 8))
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "BR_OVERTIME" for w in run.warnings)
    ref = next(r for r in load_country("BR").references if r["code"] == "WORKWEEK_HOURS")
    assert ref["source"]["status"] == "OFFICIAL" and "Constituição" in ref["source"]["legal_reference"]


def test_br_causa_o_contrato_no_soportado_se_bloquea():
    with pytest.raises(InputValidationError):
        br("2026-09-20", cause="PROBATION_END")
    with pytest.raises(InputValidationError):
        br("2026-09-20", contract="WORK_COMPLETION")


# =============================================================================================== ECUADOR
SBU = D(482)


def ec(end, hire="2021-03-17", cause="DISMISSAL_WITHOUT_CAUSE", salary="1000", **kw):
    return term("EC", hire, end, cause, salary, **kw)


@pytest.mark.parametrize("hire,end,months", [
    ("2023-09-15", "2026-09-14", 3),          # exactamente 3 años: 3 meses
    ("2023-09-15", "2026-09-15", 4),          # 3 años y un día: un mes por año con fracción = año completo -> 4
    ("2025-01-01", "2026-06-30", 3),
    ("2020-09-15", "2026-09-15", 7),          # 6 años y un día -> 7
    ("2000-01-01", "2026-09-15", 25),         # tope de 25 meses
])
def test_ec_indemnizacion_despido_intempestivo_articulo_188(hire, end, months):
    assert lines(ec(end, hire=hire))["EC_INDEMNIZACION_DESPIDO_INTEMPESTIVO"] == SBU * 0 + D(1000) * months


def test_ec_bonificacion_por_desahucio_25_por_ciento_por_ano_de_servicio():
    run = ec("2026-09-15")                                      # 5 años, 5 meses, 30 días = 5,5 años
    years = D(5) + D(5) / 12 + D(30) / 360
    assert lines(run)["EC_BONIFICACION_DESAHUCIO"] == q(D(1000) * D("0.25") * years)
    for cause in ("NOTICE_TERMINATION", "MUTUAL_AGREEMENT"):
        assert lines(ec("2026-09-15", cause=cause))["EC_BONIFICACION_DESAHUCIO"] > 0
        assert "EC_INDEMNIZACION_DESPIDO_INTEMPESTIVO" not in lines(ec("2026-09-15", cause=cause))
    assert lines(ec("2026-09-15", cause="RESIGNATION")).get("EC_BONIFICACION_DESAHUCIO", 0) == 0


@pytest.mark.parametrize("emp,expected", [
    ({"thirteenth_accumulated": True}, True), ({"thirteenth_accumulated": False}, False), ({}, False)])
def test_ec_decimo_tercero_solo_si_esta_acumulado(emp, expected):
    """Por defecto el décimo tercero y cuarto se pagan mensualmente (art. 111 y 113): no se liquidan al terminar."""
    run = ec("2026-09-15", employment=emp)
    assert ("EC_DECIMO_TERCERO" in lines(run) and lines(run)["EC_DECIMO_TERCERO"] > 0) is expected


def test_ec_decimo_tercero_es_la_doceava_parte_de_lo_percibido_y_esta_marcado_conflicto_de_periodo():
    run = ec("2026-09-15", employment={"thirteenth_accumulated": True})            # 1-ene .. 15-sep = 8,5 meses de 1.000
    assert lines(run)["EC_DECIMO_TERCERO"] == q(D(8500) / 12)
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "EC_DECIMO_TERCERO" for w in run.warnings)
    history = [{"month": f"2026-{m:02d}", "amount": "1200"} for m in range(1, 10)]
    with_history = ec("2026-09-30", employment={"thirteenth_accumulated": True}, extra={"salary_history": history})
    assert lines(with_history)["EC_DECIMO_TERCERO"] == q(D(10800) / 12)


@pytest.mark.parametrize("region,end,concept,months", [
    ("SIERRA_AMAZONIA", "2026-09-15", "EC_DECIMO_CUARTO_SIERRA", D("1.5")),        # 1-ago .. 15-sep
    ("SIERRA_AMAZONIA", "2026-07-31", "EC_DECIMO_CUARTO_SIERRA", D(12)),           # 1-ago-2025 .. 31-jul-2026
    ("COSTA_GALAPAGOS", "2026-09-15", "EC_DECIMO_CUARTO_COSTA", D("6.5")),         # 1-mar .. 15-sep
    ("COSTA_GALAPAGOS", "2028-02-29", "EC_DECIMO_CUARTO_COSTA", D(12)),            # fin de febrero bisiesto
])
def test_ec_decimo_cuarto_por_region_es_un_doceavo_del_sbu_por_mes(region, end, concept, months):
    run = ec(end, employment={"fourteenth_accumulated": True, "region": region})
    assert lines(run)[concept] == q(SBU * months / 12)


def test_ec_decimo_cuarto_de_la_otra_region_no_se_calcula():
    run = ec("2026-09-15", employment={"fourteenth_accumulated": True, "region": "COSTA_GALAPAGOS"})
    assert "EC_DECIMO_CUARTO_SIERRA" not in lines(run)


@pytest.mark.parametrize("hire,days", [("2021-09-16", 15), ("2020-09-15", 16), ("2011-09-15", 25), ("1980-01-01", 30)])
def test_ec_vacaciones_15_dias_mas_uno_por_ano_excedente_de_cinco_hasta_30(hire, days):
    run = ec("2026-09-15", hire=hire)
    assert info(run, "EC_T_VACATION_DAYS") == days


def test_ec_vacaciones_proporcionales_y_valor():
    run = ec("2026-09-15")                                        # 15 días × 182/365 desde 17-mar-2026
    days = D(15) * 183 / 365
    assert lines(run)["EC_VACACIONES"] == q(D(1000) / 30 * days)


def test_ec_fuentes_oficiales_y_advertencia_de_copia_del_2020():
    run = ec("2026-09-15")
    src = line_trace(run, "EC_INDEMNIZACION_DESPIDO_INTEMPESTIVO")["source"]
    assert src["status"] == "OFFICIAL" and "2020" in src["note"]


def test_ec_horas_suplementarias_y_recargos():
    run = monthly("EC", 1200, ("2026-09-01", "2026-09-30"), time={"night_hours": "10", "overtime_hours_until_midnight": "4",
                                                              "overtime_hours_midnight_to_6": "2", "weekend_hours": "8"})
    hour = D(1200) / 240
    assert run.line("EC_OVERTIME")["amount"] == q(hour * (D("0.25") * 10 + D("1.5") * 4 + 2 * 2 + 2 * 8))


def test_ec_limite_semanal_de_horas_suplementarias_es_advertencia():
    run = monthly("EC", 1200, ("2026-09-01", "2026-09-30"), time={"overtime_hours_until_midnight": "1", "max_overtime_hours_in_a_week": "13"})
    assert any(w["type"] == "VALIDATION_WARNING" for w in run.warnings)


def test_ec_jornada_de_40_horas_es_referencia_oficial():
    ref = next(r for r in load_country("EC").references if r["code"] == "WORKWEEK_HOURS")
    assert ref["value"] == "40" and ref["source"]["status"] == "OFFICIAL"


@pytest.mark.parametrize("hours,warns", [(2, False), (3, True)])
def test_br_limite_de_dos_horas_extra_por_dia_es_advertencia(hours, warns):
    run = monthly("BR", 5000, ("2026-09-01", "2026-09-30"), time={"overtime_hours_50": "1", "max_overtime_hours_in_a_day": str(hours)})
    assert any(w["type"] == "VALIDATION_WARNING" and "art. 59" in w["message"] for w in run.warnings) is warns
