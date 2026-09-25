"""México — finiquito/liquidación y horas extra. Esperado desde el texto de la LFT (Orden Jurídico Nacional, texto vigente
con última reforma DOF 30-sep-2024) y, para la jornada, del decreto DOF 1-may-2026 (extraído por lectura automática):
arts. 48/50 (indemnización), 76/79/80 (vacaciones y prima), 87 (aguinaldo), 89 (base), 162 (prima de antigüedad),
66-68 (horas extra) y 71 (prima dominical)."""

from datetime import date
from decimal import Decimal

import pytest

from payroll_engine.errors import StraddleError
from payroll_engine.loader import load_country
from payroll_engine.references import ReferenceResolver

from .term_helpers import D, info, line_trace, lines, monthly, q, term

DAILY = D(1000)                                       # salario mensual 30.000 / 30


def mx(end, hire="2019-03-10", cause="DISMISSAL_WITHOUT_CAUSE", salary="30000", contract="INDEFINITE", **kw):
    return term("MX", hire, end, cause, salary, contract, **kw)


def sdi(vac_days, extra=D(0)):
    """Salario diario integrado: cuota diaria + aguinaldo (15/365) + prima vacacional (25 % de los días de vacaciones / 365)."""
    return DAILY + q(DAILY * 15 / 365) + q(DAILY * vac_days * D("0.25") / 365) + extra


# ------------------------------------------------------------------------------------------- aguinaldo (art. 87)
@pytest.mark.parametrize("end,days", [("2026-09-15", 258), ("2026-12-31", 365), ("2026-01-01", 1)])
def test_aguinaldo_proporcional_15_dias_por_dias_del_ano_sobre_365(end, days):
    assert lines(mx(end, cause="RESIGNATION"))["MX_AGUINALDO_PROPORCIONAL"] == q(DAILY * 15 * days / 365)


def test_aguinaldo_ingreso_en_el_anio_cuenta_desde_el_ingreso():
    run = mx("2026-09-15", hire="2026-03-01", cause="RESIGNATION")           # 1-mar .. 15-sep = 199 días
    assert lines(run)["MX_AGUINALDO_PROPORCIONAL"] == q(DAILY * 15 * 199 / 365)


# ------------------------------------------------------------------------------------------- vacaciones y prima vacacional
@pytest.mark.parametrize("hire,days", [
    ("2026-03-01", 12),       # 0 años completos: año de servicio 1 = 12 días
    ("2025-03-01", 14),       # 1 año completo -> año 2
    ("2022-03-01", 20),       # 4 años completos -> año 5 = 20
    ("2021-03-01", 22),       # 5 años completos -> año 6 = 22
    ("2016-03-01", 24),       # 10 años completos -> año 11
    ("2011-03-01", 26),       # 15 completos -> año 16
    ("2006-03-01", 28),
    ("2001-03-01", 30),
])
def test_tabla_de_vacaciones_del_articulo_76(hire, days):
    run = mx("2026-09-15", hire=hire, cause="RESIGNATION")
    assert info(run, "MX_T_VACATION_DAYS") == days


def test_vacaciones_proporcionales_y_prima_vacacional_del_25_por_ciento():
    run = mx("2026-09-15")                                    # 7 años completos -> año 8 = 22 días; desde 2026-03-10: 190 días
    days = D(22) * 190 / 365
    assert lines(run)["MX_VACACIONES"] == q(DAILY * days)
    assert lines(run)["MX_PRIMA_VACACIONAL"] == q(lines(run)["MX_VACACIONES"] * D("0.25"))


def test_vacaciones_pendientes_y_disfrutadas():
    run = mx("2026-09-15", extra={"vacation_history": {"days_pending_prior": 6, "days_taken_current": 3}})
    assert lines(run)["MX_VACACIONES"] == q(DAILY * (D(22) * 190 / 365 + 6 - 3))


def test_la_tabla_de_vacaciones_cita_la_fuente_oficial_de_la_profedet():
    src = line_trace(mx("2026-09-15"), "MX_T_VACATION_DAYS")["source"]
    assert src["status"] == "OFFICIAL" and "PROFEDET" in src["authority"]


# ------------------------------------------------------------------------------------------- indemnización
def test_salario_integrado_incluye_aguinaldo_y_prima_vacacional_de_ley():
    run = mx("2026-09-15")
    base = next(b for b in run.trace["bases"] if b["base"] == "MX.SDI_BASE")
    assert D(base["value"]) == sdi(22)


def test_indemnizacion_de_tres_meses_y_veinte_dias_por_ano_en_plazo_indeterminado():
    run = mx("2026-09-15")                                    # 7 años, 6 meses, 6 días
    years = D(7) + D(6) / 12 + D(6) / 360
    assert lines(run)["MX_INDEMNIZACION_3_MESES"] == q(sdi(22) * 90)
    assert lines(run)["MX_INDEMNIZACION_20_DIAS"] == q(sdi(22) * 20 * years)


def test_extra_de_prestaciones_diarias_informadas_integran_el_salario():
    run = mx("2026-09-15", amounts={"extra_daily_benefits": "50"})
    assert lines(run)["MX_INDEMNIZACION_3_MESES"] == q((sdi(22) + 50) * 90)


@pytest.mark.parametrize("hire,end,units", [
    ("2026-03-01", "2026-08-31", D(90)),                 # menos de un año: mitad del tiempo (6 meses = 0,5 año -> 90 días de salario)
    ("2026-01-01", "2026-12-31", D(180)),                # exactamente un año: 6 meses por el primer año
    ("2024-09-15", "2026-09-15", D(180) + D(20) * (D(1) + D(1) / 360)),     # 2 años y 1 día: 6 meses + 20 días × 1,00278
])
def test_plazo_determinado_mitad_del_tiempo_si_es_menor_de_un_ano_y_seis_meses_mas_veinte_dias(hire, end, units):
    run = mx(end, hire=hire, contract="FIXED_TERM")
    assert "MX_INDEMNIZACION_20_DIAS" not in lines(run)
    base = D(next(b for b in run.trace["bases"] if b["base"] == "MX.SDI_BASE")["value"])
    assert lines(run)["MX_INDEMNIZACION_PLAZO_DETERMINADO"] == q(base * units)


@pytest.mark.parametrize("cause", ["RESIGNATION", "DISMISSAL_WITH_CAUSE", "MUTUAL_AGREEMENT", "DEATH", "RETIREMENT", "FIXED_TERM_EXPIRY"])
def test_sin_despido_injustificado_no_hay_indemnizacion_de_tres_meses(cause):
    run = mx("2026-09-15", cause=cause)
    assert lines(run).get("MX_INDEMNIZACION_3_MESES", 0) == 0 and lines(run).get("MX_INDEMNIZACION_20_DIAS", 0) == 0
    assert lines(run)["MX_AGUINALDO_PROPORCIONAL"] > 0             # aguinaldo y vacaciones se pagan siempre


# ------------------------------------------------------------------------------------------- prima de antigüedad (art. 162)
def test_prima_de_antiguedad_12_dias_por_ano_con_tope_de_dos_salarios_minimos_de_la_zona():
    run = mx("2026-09-15")
    years = D(7) + D(6) / 12 + D(6) / 360
    capped = 2 * D("315.04")                                   # salario diario 1000 > 630,08: rige el tope
    assert lines(run)["MX_PRIMA_ANTIGUEDAD_GENERAL"] == q(capped * 12 * years)
    zlfn = mx("2026-09-15", employment={"wage_zone": "ZLFN"})
    assert lines(zlfn)["MX_PRIMA_ANTIGUEDAD_ZLFN"] == q(2 * D("440.87") * 12 * years)
    assert "MX_PRIMA_ANTIGUEDAD_GENERAL" not in lines(zlfn)


def test_prima_de_antiguedad_sin_tope_si_el_salario_es_menor_al_doble_del_minimo():
    run = mx("2026-09-15", salary="15000")                     # 500 diarios < 630,08
    years = D(7) + D(6) / 12 + D(6) / 360
    assert lines(run)["MX_PRIMA_ANTIGUEDAD_GENERAL"] == q(D(500) * 12 * years)


@pytest.mark.parametrize("hire,paid", [("2011-09-15", True),   # 15 años y 1 día
                                        ("2011-09-16", True),   # 15 años exactos (16-sep-2011 .. 15-sep-2026)
                                        ("2011-09-17", False)])  # 14 años y 364 días
def test_prima_de_antiguedad_en_renuncia_solo_con_quince_anos(hire, paid):
    run = mx("2026-09-15", hire=hire, cause="RESIGNATION")
    assert (lines(run).get("MX_PRIMA_ANTIGUEDAD_GENERAL", 0) > 0) is paid


def test_prima_de_antiguedad_en_despido_o_separacion_justificada_sin_minimo_de_anos():
    for cause in ("DISMISSAL_WITH_CAUSE", "DISMISSAL_WITHOUT_CAUSE", "INDIRECT_DISMISSAL"):
        assert lines(mx("2026-09-15", hire="2024-01-01", cause=cause))["MX_PRIMA_ANTIGUEDAD_GENERAL"] > 0


def test_prima_de_antiguedad_solo_para_trabajadores_de_planta():
    assert lines(mx("2026-09-15", contract="FIXED_TERM", employment={"contract_end_date": "2026-12-31"})).get("MX_PRIMA_ANTIGUEDAD_GENERAL", 0) == 0


# ------------------------------------------------------------------------------------------- referencias (UMA / salarios mínimos)
def test_uma_cambia_el_1_de_febrero_y_el_salario_minimo_general_y_de_la_zlfn_son_referencias_distintas():
    cfg = load_country("MX")
    r = ReferenceResolver(cfg.references, "MX", ["NATIONAL"], cfg.series)
    assert r.resolve("UMA_DAILY", date(2026, 1, 31)).value == Decimal("113.14")
    assert r.resolve("UMA_DAILY", date(2026, 2, 1)).value == Decimal("117.31")
    assert r.resolve("SM_GENERAL_DAILY", date(2026, 6, 1)).value == Decimal("315.04")
    assert r.resolve("SM_ZLFN_DAILY", date(2026, 6, 1)).value == Decimal("440.87")
    assert r.resolve("SM_GENERAL_DAILY", date(2026, 6, 1)).record["source"]["status"] == "OFFICIAL"


@pytest.mark.parametrize("day,hours", [("2026-12-31", 48), ("2027-01-01", 46), ("2028-01-01", 44), ("2029-01-01", 42), ("2030-01-01", 40)])
def test_reduccion_gradual_de_la_jornada_semanal_2026_2030(day, hours):
    cfg = load_country("MX")
    r = ReferenceResolver(cfg.references, "MX", ["NATIONAL"], cfg.series)
    assert r.resolve("WORKWEEK_HOURS", date.fromisoformat(day)).value == hours


# ------------------------------------------------------------------------------------------- horas extra y prima dominical
def test_horas_extra_dobles_hasta_9_por_semana_y_triples_las_excedentes():
    run = monthly("MX", 30000, ("2026-09-01", "2026-09-30"), extra={"overtime_weekly_hours": [4, 10, 9]},
                  time={"incapacity_days": "0", "paid_days": "30"})
    hour = D(30000) / 240
    assert run.line("MX_OVERTIME")["amount"] == q(hour * (2 * 4 + (2 * 9 + 3 * 1) + 2 * 9))


def test_horas_extra_versiones_por_vigencia_antes_y_despues_de_la_reforma_del_1_de_mayo_de_2026():
    apr = monthly("MX", 30000, ("2026-04-01", "2026-04-30"), extra={"overtime_weekly_hours": [10]}, time={"incapacity_days": "0", "paid_days": "30"})
    jun = monthly("MX", 30000, ("2026-06-01", "2026-06-30"), extra={"overtime_weekly_hours": [10]}, time={"incapacity_days": "0", "paid_days": "30"})
    assert apr.line("MX_OVERTIME")["rule_id"] == "MX.OVERTIME.1" and jun.line("MX_OVERTIME")["rule_id"] == "MX.OVERTIME.2"
    assert apr.line("MX_OVERTIME")["amount"] == jun.line("MX_OVERTIME")["amount"]              # mismo tope de 9 h en 2026
    assert any(w["type"] == "UNVERIFIED_RULE" and w["rule_id"] == "MX.OVERTIME.2" for w in jun.warnings)


def test_un_periodo_que_cruza_la_reforma_de_horas_extra_se_bloquea():
    with pytest.raises(StraddleError):
        monthly("MX", 30000, ("2026-04-15", "2026-05-14"), extra={"overtime_weekly_hours": [4]}, time={"incapacity_days": "0", "paid_days": "30"})


def test_prima_dominical_25_por_ciento_sobre_el_salario_del_dia():
    run = monthly("MX", 30000, ("2026-09-01", "2026-09-30"), time={"sunday_hours": "16", "incapacity_days": "0", "paid_days": "30"})
    assert run.line("MX_SUNDAY_PREMIUM")["amount"] == q(D(30000) / 240 * D("0.25") * 16)
