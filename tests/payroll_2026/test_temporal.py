"""Aritmética de fechas laborales (payroll_engine/temporal.py): antigüedad por aniversarios, meses comerciales,
meses calendario completos y ventanas jurídicas. Sin ninguna regla de país."""

from datetime import date
from decimal import Decimal

import pytest

from payroll_engine.errors import InputValidationError, SchemaError
from payroll_engine.temporal import (add_months, commercial_days_360, complete_calendar_months, count_units,
                                     months_with_min_days, resolve_window, service_time)


# --------------------------------------------------------------------------------------- add_months
@pytest.mark.parametrize("start,months,expected", [
    (date(2026, 1, 31), 1, date(2026, 2, 28)),
    (date(2028, 1, 31), 1, date(2028, 2, 29)),        # bisiesto
    (date(2026, 3, 31), -1, date(2026, 2, 28)),
    (date(2026, 11, 30), 3, date(2027, 2, 28)),
    (date(2026, 5, 15), 12, date(2027, 5, 15)),
])
def test_add_months_recorta_al_ultimo_dia_del_mes(start, months, expected):
    assert add_months(start, months) == expected


# --------------------------------------------------------------------------------------- service_time
@pytest.mark.parametrize("hire,end,ymd", [
    (date(2020, 1, 1), date(2020, 12, 31), (1, 0, 0)),          # año completo, extremos inclusivos
    (date(2020, 1, 1), date(2020, 12, 30), (0, 11, 30)),
    (date(2020, 1, 1), date(2021, 1, 1), (1, 0, 1)),
    (date(2024, 3, 10), date(2026, 7, 20), (2, 4, 11)),
    (date(2026, 8, 15), date(2026, 9, 30), (0, 1, 16)),
    (date(2020, 1, 31), date(2020, 2, 29), (0, 1, 1)),          # 31-ene + 1 mes = 29-feb (recortado) + 1 día inclusive
    (date(2026, 9, 15), date(2026, 9, 15), (0, 0, 1)),          # mismo día = un día de servicio
])
def test_service_time_por_aniversarios(hire, end, ymd):
    st = service_time(hire, end)
    assert (st.years, st.months, st.days) == ymd


def test_service_time_rechaza_fin_anterior_al_inicio():
    with pytest.raises(InputValidationError):
        service_time(date(2026, 9, 2), date(2026, 9, 1))


def test_fraccion_superior_a_n_meses_es_estricta():
    """'fracción SUPERIOR a seis meses': 6 meses exactos NO superan; 6 meses y un día SÍ."""
    exact = service_time(date(2020, 1, 1), date(2026, 6, 30))
    plus = service_time(date(2020, 1, 1), date(2026, 7, 1))
    assert (exact.months, exact.days) == (6, 0) and (plus.months, plus.days) == (6, 1)
    assert not exact.exceeds_fraction(6) and plus.exceeds_fraction(6)


# --------------------------------------------------------------------------------------- base 360
@pytest.mark.parametrize("start,end,days", [
    (date(2026, 1, 1), date(2026, 1, 31), 30),
    (date(2026, 2, 1), date(2026, 2, 28), 30),                  # fin de febrero cuenta como 30
    (date(2026, 1, 1), date(2026, 12, 31), 360),
    (date(2026, 1, 15), date(2026, 1, 31), 16),
    (date(2026, 7, 1), date(2026, 9, 15), 75),
    (date(2026, 3, 31), date(2026, 3, 31), 1),
    (date(2026, 1, 1), date(2026, 9, 15), 255),
])
def test_dias_360_comerciales(start, end, days):
    assert commercial_days_360(start, end) == days


# --------------------------------------------------------------------------------------- meses calendario completos
@pytest.mark.parametrize("start,end,months", [
    (date(2026, 1, 1), date(2026, 6, 30), 6),
    (date(2026, 1, 15), date(2026, 6, 30), 5),                  # el primer mes parcial no cuenta
    (date(2026, 1, 1), date(2026, 6, 29), 5),                   # el último mes parcial no cuenta
    (date(2026, 7, 1), date(2026, 7, 20), 0),
    (date(2026, 7, 1), date(2026, 7, 31), 1),
    (date(2026, 2, 1), date(2026, 2, 28), 1),
])
def test_meses_calendario_completos(start, end, months):
    assert complete_calendar_months(start, end) == months


@pytest.mark.parametrize("start,end,count", [
    (date(2026, 1, 17), date(2026, 1, 31), 1),                  # 15 días: cuenta
    (date(2026, 1, 18), date(2026, 1, 31), 0),                  # 14 días: no cuenta
    (date(2026, 1, 1), date(2026, 9, 14), 8),                   # septiembre con 14 días no suma
    (date(2026, 1, 1), date(2026, 9, 15), 9),
])
def test_meses_con_minimo_de_dias(start, end, count):
    assert months_with_min_days(start, end, 15)[0] == count


# --------------------------------------------------------------------------------------- ventanas jurídicas
SEMESTERS = {"type": "RECURRING_PERIODS", "periods": [{"start": "01-01", "end": "06-30"}, {"start": "07-01", "end": "12-31"}]}
CTS = {"type": "RECURRING_PERIODS", "periods": [{"start": "05-01", "end": "10-31"}, {"start": "11-01", "end": "04-30"}]}


@pytest.mark.parametrize("end,expected", [
    (date(2026, 6, 30), (date(2026, 1, 1), date(2026, 6, 30))),
    (date(2026, 7, 1), (date(2026, 7, 1), date(2026, 7, 1))),
    (date(2026, 12, 31), (date(2026, 7, 1), date(2026, 12, 31))),
])
def test_ventana_semestre_calendario(end, expected):
    start, stop, _ = resolve_window(SEMESTERS, date(2010, 1, 1), end)
    assert (start, stop) == expected


@pytest.mark.parametrize("end,start", [
    (date(2026, 4, 30), date(2025, 11, 1)),      # semestre nov-abr cruza el año
    (date(2026, 1, 10), date(2025, 11, 1)),
    (date(2026, 5, 1), date(2026, 5, 1)),        # el 1-may empieza el semestre mayo-octubre
    (date(2026, 10, 31), date(2026, 5, 1)),
    (date(2026, 11, 1), date(2026, 11, 1)),
])
def test_ventana_de_semestre_que_cruza_el_anio(end, start):
    assert resolve_window(CTS, date(2010, 1, 1), end)[0] == start


def test_la_ventana_se_recorta_por_la_fecha_de_ingreso():
    start, _, _ = resolve_window(SEMESTERS, date(2026, 8, 15), date(2026, 9, 30))
    assert start == date(2026, 8, 15)


def test_ventana_anio_de_servicio_desde_el_ultimo_aniversario():
    assert resolve_window({"type": "SERVICE_YEAR"}, date(2019, 3, 10), date(2026, 9, 15))[0] == date(2026, 3, 10)
    assert resolve_window({"type": "SERVICE_YEAR"}, date(2026, 3, 10), date(2026, 9, 15))[0] == date(2026, 3, 10)


def test_ventana_fin_de_febrero_en_anio_bisiesto():
    window = {"type": "RECURRING_PERIODS", "periods": [{"start": "03-01", "end": "02-END"}]}
    assert resolve_window(window, date(2020, 1, 1), date(2028, 2, 29))[:2] == (date(2027, 3, 1), date(2028, 2, 29))
    assert resolve_window(window, date(2020, 1, 1), date(2026, 9, 15))[:2] == (date(2026, 3, 1), date(2026, 9, 15))


def test_ventana_desconocida_o_fuera_de_periodo_falla():
    with pytest.raises(SchemaError):
        resolve_window({"type": "INVENTADA"}, date(2020, 1, 1), date(2026, 1, 1))
    with pytest.raises(SchemaError):
        resolve_window({"type": "RECURRING_PERIODS", "periods": [{"start": "03-01", "end": "03-31"}]}, date(2020, 1, 1), date(2026, 9, 1))


# --------------------------------------------------------------------------------------- unidades de conteo
def test_meses_y_dias_usa_treintavos():
    value, _ = count_units({"unit": "MONTHS_AND_DAYS"}, date(2026, 5, 1), date(2026, 7, 20))     # 2 meses y 20 días
    assert value == Decimal(2) + Decimal(20) / 30


def test_meses_redondeados_por_dias_umbral_15():
    assert count_units({"unit": "MONTHS_ROUNDED_BY_DAYS", "day_threshold": 15}, date(2026, 3, 17), date(2026, 9, 20))[0] == 6   # 6 m + 4 d
    assert count_units({"unit": "MONTHS_ROUNDED_BY_DAYS", "day_threshold": 15}, date(2026, 3, 1), date(2026, 9, 15))[0] == 7    # 6 m + 15 d


def test_unidad_de_conteo_desconocida_falla():
    with pytest.raises(SchemaError):
        count_units({"unit": "HORAS"}, date(2026, 1, 1), date(2026, 2, 1))
