"""Colombia — Ley 1393/2010 art. 30 (auditoría) y horas extra / recargos (CST arts. 160, 168, 179 con Ley 2466/2025).

Ley 1393: 'los pagos laborales no constitutivos de salario ... no podrán ser superiores al 40% del total de la
remuneración' (para los arts. 18 y 204 de la Ley 100). Exceso = pagos no salariales − 40 % × (salario + pagos no
salariales). El alcance del 'total de la remuneración' NO está verificado: el resultado es PROVISIONAL y así se declara."""

from decimal import Decimal

import pytest

from payroll_engine.loader import load_country
from payroll_engine.capabilities import describe

from .helpers import amount, q, run_co
from .term_helpers import D, monthly, line_trace

SALARY = 3_000_000


def ibc(run):
    return next(b for b in run.trace["bases"] if b["base"] == "IBC")


# ------------------------------------------------------------------------------------ Ley 1393
@pytest.mark.parametrize("non_salary,excess", [
    (1_999_999, Decimal(0)),                                     # 40 % del total = 2.000.000 - 0,4: por debajo
    (2_000_000, Decimal(0)),                                     # EXACTAMENTE 40 %: no excede
    (2_000_001, D("2000001") - D("0.4") * D("5000001")),         # +1 peso: excede en 0,6
    (3_000_000, D(600_000)),
    (10_000_000, D("10000000") - D("0.4") * D("13000000")),
])
def test_co_ley_1393_fronteras_del_40_por_ciento(non_salary, excess):
    run = run_co(SALARY, amounts={"BONUS_NON_SALARY": str(non_salary)})
    assert D(ibc(run)["value"]) == D(SALARY) + excess
    assert excess >= 0


def test_ley_1393_el_limite_se_calcula_sobre_salario_mas_pagos_no_salariales():
    run = run_co(SALARY, amounts={"BONUS_NON_SALARY": "3000000"})
    special = next(c for c in ibc(run)["contributions"] if c.get("special") == "SHARE_EXCESS")
    assert special["total_remuneration"] == "6000000" and special["limit"] == "2400000" and special["non_salary_total"] == "3000000"


def test_ley_1393_el_exceso_solo_afecta_las_bases_de_salud_y_pension_no_arl_ni_parafiscales():
    run = run_co(SALARY, amounts={"BONUS_NON_SALARY": "3000000"})
    bases = {b["base"]: D(b["value"]) for b in run.trace["bases"]}
    assert bases["IBC"] == D(3_600_000)
    assert bases["RISK_BASE"] == D(SALARY) and bases["PARAFISCAL_BASE"] == D(SALARY) and bases["EXONERATION_BASE"] == D(SALARY)


def test_ley_1393_el_exceso_se_suma_una_sola_vez_aunque_haya_varias_lineas():
    run = run_co(SALARY, amounts={"BONUS_NON_SALARY": "3000000", "BONUS_SALARY": "500000"})
    special = [c for c in ibc(run)["contributions"] if c.get("special") == "SHARE_EXCESS"]
    assert len(special) == 1
    assert D(special[0]["total_remuneration"]) == D(SALARY) + 500_000 + 3_000_000


def test_ley_1393_el_bono_salarial_no_cuenta_como_pago_no_salarial():
    run = run_co(SALARY, amounts={"BONUS_SALARY": "5000000"})
    assert D(ibc(run)["value"]) == D(SALARY) + 5_000_000


def test_ley_1393_sin_pagos_no_salariales_no_hay_regla_especial():
    run = run_co(SALARY)
    assert not [c for c in ibc(run)["contributions"] if c.get("special") == "SHARE_EXCESS"]


def test_ley_1393_es_una_regla_colombiana_por_datos_y_no_un_if_de_pais_en_el_nucleo():
    concept = next(c for c in load_country("CO").concept_list if c["concept"] == "BONUS_NON_SALARY")
    treatment = next(t for t in concept["treatments"] if t["base"] == "IBC")
    assert treatment["special"] == "SHARE_EXCESS" and treatment["params"]["share"] == "0.40"
    assert "TRANSPORT_ALLOWANCE" not in treatment["params"]["total_of"]      # decisión documentada: el auxilio no integra el total


# ------------------------------------------------------------------------------------ estado de la interpretación
def test_ley_1393_esta_declarada_provisional_y_la_corrida_lo_advierte():
    concept = next(c for c in load_country("CO").concept_list if c["concept"] == "BONUS_NON_SALARY")
    assert concept["source"]["status"] == "OFFICIAL" and "Ley 1393" in concept["source"]["legal_reference"]
    assert concept["verification"]["interpretation_status"] == "UNREVIEWED" and concept["verification"]["open_question"] is True
    assert concept["verification"]["professional_validation"] == "PENDING"
    run = run_co(SALARY, amounts={"BONUS_NON_SALARY": "3000000"})
    pend = [w for w in run.warnings if w["type"] == "PENDING_TREATMENTS"]
    assert pend and any("BONUS_NON_SALARY→IBC" in item for item in pend[0]["items"])
    assert describe("CO")["capabilities"]["non_salary_share_40"]["status"] == "PENDING_VALIDATION"


def test_ley_1393_provisional_y_no_definitiva_en_el_manifiesto():
    note = describe("CO")["capabilities"]["non_salary_share_40"]["note"]
    assert "PROVISIONAL" in note and "UGPP" in note
    assert any("1393" in g for g in describe("CO")["known_gaps"])


# ------------------------------------------------------------------------------------ horas extra (mensual)
def ot(period, salary=3_000_000, **hours):
    return monthly("CO", salary, period, time={k: str(v) for k, v in hours.items()}, employment={"salary_type": "ORDINARY"},
                   extra={"employer": {"exonerated_art_114_1": True, "arl_class": "I"}})


def overtime(run):
    line = run.line("CO_OVERTIME")
    return line["amount"] if line else Decimal(0)


def test_extra_diurna_25_y_extra_nocturna_75_sobre_valor_hora_de_220_h_en_junio():
    run = ot(("2026-06-01", "2026-06-30"), hours_overtime_day=4, hours_overtime_night=2)
    hour = D(3_000_000) / 220                                    # 44 h semanales hasta el 14-jul-2026
    assert overtime(run) == q(hour * (D("1.25") * 4 + D("1.75") * 2))


def test_recargo_nocturno_35_solo_agrega_el_recargo_porque_la_hora_ordinaria_ya_esta_en_el_salario():
    run = ot(("2026-06-01", "2026-06-30"), hours_night_surcharge=10)
    assert overtime(run) == q(D(3_000_000) / 220 * D("0.35") * 10)


@pytest.mark.parametrize("period,surcharge", [(("2026-06-01", "2026-06-30"), "0.80"), (("2026-09-01", "2026-09-30"), "0.90")])
def test_recargo_dominical_80_hasta_junio_y_90_desde_el_1_de_julio_de_2026(period, surcharge):
    hours_per_month = 220 if period[1] == "2026-06-30" else 210
    run = ot(period, hours_sunday_day=8)
    assert overtime(run) == q(D(3_000_000) / hours_per_month * D(surcharge) * 8)


def test_recargo_dominical_por_referencia_con_vigencia_y_fuente_oficial():
    refs = sorted((r["effective"]["from"], r["value"]) for r in load_country("CO").references if r["code"] == "SUNDAY_HOLIDAY_SURCHARGE")
    assert refs == [("2025-07-01", "0.80"), ("2026-07-01", "0.90"), ("2027-07-01", "1.00")]
    assert all(r["source"]["status"] == "OFFICIAL" and "Ley 2466" in r["source"]["legal_reference"]
               for r in load_country("CO").references if r["code"] == "SUNDAY_HOLIDAY_SURCHARGE")


def test_combinaciones_dominical_con_nocturno_y_extra_se_suman_como_interpretacion_declarada():
    run = ot(("2026-09-01", "2026-09-30"), hours_sunday_night=2, hours_overtime_sunday_day=3, hours_overtime_sunday_night=1)
    hour = D(3_000_000) / 210
    expected = hour * ((D("0.35") + D("0.90")) * 2 + (D("1.25") + D("0.90")) * 3 + (D("1.75") + D("0.90")) * 1)
    assert overtime(run) == q(expected)
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "CO_OVERTIME" for w in run.warnings) is True


def test_el_cambio_de_jornada_del_15_de_julio_prorratea_por_dias_dentro_del_periodo():
    run = ot(("2026-07-01", "2026-07-31"), hours_overtime_day=10)
    before = D(3_000_000) / 220 * D("1.25") * 10                 # 1-14 jul: 14 días
    after = D(3_000_000) / 210 * D("1.25") * 10                  # 15-31 jul: 17 días
    expected = (before * 14 + after * 17) / 31
    assert abs(overtime(run) - expected) <= D("0.01")
    assert [s["fraction"] for s in line_trace(run, "CO_OVERTIME")["segments"]] == ["14/31", "17/31"]


def test_salario_integral_no_genera_horas_extra():
    run = monthly("CO", 30_000_000, ("2026-06-01", "2026-06-30"), time={"hours_overtime_day": "10"},
                  employment={"salary_type": "INTEGRAL"}, extra={"employer": {"exonerated_art_114_1": True, "arl_class": "I"}})
    assert overtime(run) == 0


@pytest.mark.parametrize("day,week,warns", [(2, 12, False), (3, 12, True), (2, 13, True), (0, 0, False)])
def test_limites_de_horas_extra_2_diarias_y_12_semanales_son_advertencias(day, week, warns):
    run = ot(("2026-06-01", "2026-06-30"), hours_overtime_day=1, max_overtime_hours_in_a_day=day, max_overtime_hours_in_a_week=week)
    assert any(w["type"] == "VALIDATION_WARNING" for w in run.warnings) is warns


def test_el_valor_hora_sale_de_la_referencia_de_jornada_no_de_una_constante():
    params = next(r for r in load_country("CO").rules if r["rule_key"] == "CO.OVERTIME")["calculation"]["params"]
    assert params["hourly"]["hours_per_month"] == {"reference": {"code": "WORKWEEK_HOURS", "multiple": "5"}}
