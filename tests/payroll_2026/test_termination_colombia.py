"""Colombia — liquidación (terminación). Esperado desde el texto oficial del CST (Secretaría del Senado): art. 249/253
(cesantías), 306 (prima), 186/192 (vacaciones), 64 (indemnización, Ley 789/2002 art. 28); base 360 y auxilio de transporte."""

from decimal import Decimal

import pytest

from payroll_engine.errors import InputValidationError

from .term_helpers import D, info, line_trace, lines, q, term

SMMLV = D(1750905)
TRANSPORT = D(249095)
TEN = 10 * SMMLV
TWO = 2 * SMMLV


def co(end, hire="2023-02-10", cause="DISMISSAL_WITHOUT_CAUSE", salary="2000000", contract="INDEFINITE", **kw):
    return term("CO", hire, end, cause, salary, contract, **kw)


# ------------------------------------------------------------------------------------------- cesantías / intereses / prima
def test_cesantias_prima_e_intereses_con_base_360_y_auxilio_de_transporte():
    run = co("2026-09-15")
    base = D(2_000_000) + TRANSPORT
    cesantias = q(base * 255 / 360)                                   # 1-ene .. 15-sep = 255 días (base 360)
    assert lines(run)["CO_CESANTIAS"] == cesantias
    assert lines(run)["CO_CESANTIAS_INTERESES"] == q(cesantias * D("0.12") * 255 / 360)
    assert lines(run)["CO_PRIMA"] == q(base * 75 / 360)              # 1-jul .. 15-sep = 75 días


@pytest.mark.parametrize("salary,transport", [(TWO - 1, True), (TWO, True), (TWO + 1, False), (2 * TWO, False),
                                              (D(3_501_809), True), (D(3_501_810), True), (D(3_501_811), False), (D(7_003_620), False)])
def test_auxilio_de_transporte_en_la_base_de_cesantias_solo_hasta_2_smmlv(salary, transport):
    """Fronteras del enunciado: 3.501.809 y 3.501.810 elegibles; 3.501.811 y 7.003.620 no."""
    run = co("2026-09-15", salary=str(salary))
    base = next(b for b in run.trace["bases"] if b["base"] == "CO.CESANTIAS_BASE")
    expected = D(salary) + (TRANSPORT if transport else 0)
    assert D(base["value"]) == expected
    assert (info(run, "CO_T_TRANSPORT") == TRANSPORT) is transport


def test_no_se_paga_auxilio_de_transporte_por_encima_de_2_smmlv_y_no_existe_el_limite_de_4():
    run = co("2026-09-15", salary=str(3 * SMMLV))
    assert info(run, "CO_T_TRANSPORT") is None                        # 3 SMMLV: heredado lo pagaba (regla de 4 SMMLV)
    assert lines(run).get("CO_AUXILIO_TRANSPORTE_MES", 0) == 0


def test_salario_integral_no_causa_cesantias_intereses_ni_prima_pero_si_vacaciones():
    run = co("2026-09-15", salary="30000000", employment={"salary_type": "INTEGRAL"})
    got = lines(run)
    assert "CO_CESANTIAS" not in got and "CO_PRIMA" not in got and "CO_CESANTIAS_INTERESES" not in got
    assert got["CO_VACACIONES_PROPORCIONALES"] == q(D(30_000_000) * 216 / 720)


def test_cesantias_regimen_tradicional_se_bloquea():
    with pytest.raises(InputValidationError) as err:
        co("2026-09-15", employment={"cesantias_regime": "RETROACTIVO"})
    assert "Ley 50" in err.value.message


def test_cesantias_base_promedio_si_el_salario_vario_en_los_ultimos_3_meses():
    varied = [{"month": f"2026-{m:02d}", "amount": "1800000"} for m in range(1, 8)] + [
        {"month": "2026-08", "amount": "2000000"}, {"month": "2026-09", "amount": "2000000"}]
    run = co("2026-09-15", extra={"salary_history": varied})
    avg = sum((D(r["amount"]) for r in varied), Decimal(0)) / 9
    assert D(next(b for b in run.trace["bases"] if b["base"] == "CO.CESANTIAS_BASE")["value"]) == q(avg) + TRANSPORT     # la línea del salario base se redondea al emitirse
    stable = [{"month": f"2026-{m:02d}", "amount": "2000000"} for m in range(1, 10)]
    run = co("2026-09-15", extra={"salary_history": stable})
    assert D(next(b for b in run.trace["bases"] if b["base"] == "CO.CESANTIAS_BASE")["value"]) == D(2_000_000) + TRANSPORT


def test_prima_usa_el_semestre_en_curso_y_la_de_semestres_anteriores_es_dato_de_entrada():
    run = co("2026-05-31", amounts={"prima_unpaid_prior": "123456"})            # 1-ene .. 31-may = 150 días
    assert lines(run)["CO_PRIMA"] == q((D(2_000_000) + TRANSPORT) * 150 / 360)
    assert lines(run)["CO_PRIMA_ANTERIOR"] == D("123456.00")


# ------------------------------------------------------------------------------------------- vacaciones
def test_vacaciones_proporcionales_15_dias_habiles_por_360_dias_desde_el_ultimo_aniversario():
    run = co("2026-09-15")                                           # ingreso 10-feb: 216 días base 360 desde 2026-02-10
    assert lines(run)["CO_VACACIONES_PROPORCIONALES"] == q(D(2_000_000) * 216 / 720)


def test_vacaciones_no_incluyen_auxilio_de_transporte_y_las_pendientes_valen_salario_sobre_30():
    run = co("2026-09-15", extra={"vacation_history": {"days_pending_prior": 6}})
    base = next(b for b in run.trace["bases"] if b["base"] == "CO.VACATION_BASE")
    assert D(base["value"]) == D(2_000_000)
    assert lines(run)["CO_VACACIONES_PENDIENTES"] == q(D(2_000_000) / 30 * 6)


# ------------------------------------------------------------------------------------------- indemnización art. 64
@pytest.mark.parametrize("hire,end,units", [
    ("2026-01-01", "2026-06-30", 30),               # hasta un año: 30 días fijos (no proporcional)
    ("2026-01-01", "2026-12-31", 30),               # 1 año exacto
    ("2025-12-31", "2026-12-31", D(30) + D(20) / 360),        # 1 año y 1 día -> 20 días × (1/360)
    ("2023-02-10", "2026-09-15", 82),               # 3 años 7 meses 6 días: 30 + 20 × 2,6
])
def test_indemnizacion_indefinido_menor_de_10_smmlv(hire, end, units):
    run = co(end, hire=hire)
    assert lines(run)["CO_INDEMNIZACION_INDEFINIDO_MENOR_10"] == q(D(2_000_000) / 30 * D(units))


@pytest.mark.parametrize("salary,concept", [(TEN - 1, "CO_INDEMNIZACION_INDEFINIDO_MENOR_10"),
                                            (TEN, "CO_INDEMNIZACION_INDEFINIDO_MAYOR_IGUAL_10"),
                                            (TEN + 1, "CO_INDEMNIZACION_INDEFINIDO_MAYOR_IGUAL_10")])
def test_frontera_de_10_smmlv_en_la_indemnizacion(salary, concept):
    """CST art. 64: 'inferior a diez' vs 'igual o superior a diez' salarios mínimos."""
    run = co("2026-09-15", salary=str(salary))
    assert concept in lines(run) and len([c for c in lines(run) if c.startswith("CO_INDEMNIZACION")]) == 1


def test_indemnizacion_indefinido_de_10_smmlv_o_mas_20_dias_mas_15_por_ano():
    salary = D(30_000_000)
    run = co("2026-09-15", salary=str(salary))
    assert lines(run)["CO_INDEMNIZACION_INDEFINIDO_MAYOR_IGUAL_10"] == q(salary / 30 * (D(20) + D(15) * D("2.6")))


def test_indemnizacion_termino_fijo_tiempo_restante():
    run = co("2026-09-15", contract="FIXED_TERM", employment={"contract_end_date": "2026-12-31"})
    remaining = 105                                                  # 16-sep .. 31-dic base 360: 3 meses + 15 días
    assert lines(run)["CO_INDEMNIZACION_TERMINO_FIJO"] == q(D(2_000_000) / 30 * remaining)
    assert "CO_INDEMNIZACION_INDEFINIDO_MENOR_10" not in lines(run)


def test_indemnizacion_obra_o_labor_minimo_de_15_dias():
    run = co("2026-09-15", contract="WORK_COMPLETION", employment={"contract_end_date": "2026-09-20"})      # 5 días restantes
    assert lines(run)["CO_INDEMNIZACION_OBRA_LABOR"] == q(D(2_000_000) / 30 * 15)
    far = co("2026-09-15", contract="WORK_COMPLETION", employment={"contract_end_date": "2026-11-30"})     # 75 días
    assert lines(far)["CO_INDEMNIZACION_OBRA_LABOR"] == q(D(2_000_000) / 30 * 75)


@pytest.mark.parametrize("cause", ["RESIGNATION", "DISMISSAL_WITH_CAUSE", "MUTUAL_AGREEMENT", "PROBATION_END", "DEATH", "RETIREMENT",
                                   "FIXED_TERM_EXPIRY", "WORK_COMPLETION"])
def test_sin_terminacion_injusta_no_hay_indemnizacion_pero_si_prestaciones(cause):
    run = co("2026-09-15", cause=cause)
    assert not any(c.startswith("CO_INDEMNIZACION") and v != 0 for c, v in lines(run).items())
    assert lines(run)["CO_CESANTIAS"] > 0 and lines(run)["CO_PRIMA"] > 0


def test_terminacion_indirecta_por_culpa_del_empleador_tambien_indemniza():
    run = co("2026-09-15", cause="INDIRECT_DISMISSAL")
    assert lines(run)["CO_INDEMNIZACION_INDEFINIDO_MENOR_10"] > 0


def test_termino_fijo_requiere_la_fecha_de_fin():
    with pytest.raises(InputValidationError):
        co("2026-09-15", contract="FIXED_TERM")


# ------------------------------------------------------------------------------------------- salario del mes y auxilio
def test_salario_y_transporte_del_mes_de_terminacion_en_base_30():
    run = co("2026-09-15")
    assert lines(run)["CO_SALARIO_MES_TERMINACION"] == D("1000000.00") and lines(run)["CO_AUXILIO_TRANSPORTE_MES"] == q(TRANSPORT / 2)
    paid = co("2026-09-15", termination={"final_month_paid": True})
    assert "CO_SALARIO_MES_TERMINACION" not in lines(paid)


def test_mes_completo_al_terminar_el_ultimo_dia_del_mes():
    run = co("2026-09-30")
    assert lines(run)["CO_SALARIO_MES_TERMINACION"] == D("2000000.00")


# ------------------------------------------------------------------------------------------- estado de las fuentes
def test_fuentes_oficiales_del_cst_y_pendientes_declaradas():
    run = co("2026-09-15")
    status = {l["concept"]: l["source"]["status"] for l in run.trace["lines"]}
    for concept in ("CO_CESANTIAS", "CO_PRIMA", "CO_VACACIONES_PROPORCIONALES", "CO_INDEMNIZACION_INDEFINIDO_MENOR_10"):
        assert status[concept] == "OFFICIAL"
    assert status["CO_CESANTIAS_INTERESES"] == "PENDING"
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "CO_CESANTIAS_INTERESES" for w in run.warnings)
    assert any(w["type"] == "PENDING_TREATMENTS" for w in run.warnings)          # auxilio en la base: fuente pendiente


def test_el_total_es_la_suma_exacta_y_no_hay_float():
    run = co("2026-09-15")
    assert run.result["totals"]["neto_pagado"] == sum(lines(run).values())
    assert all(isinstance(l["amount"], Decimal) for l in run.result["lines"])
