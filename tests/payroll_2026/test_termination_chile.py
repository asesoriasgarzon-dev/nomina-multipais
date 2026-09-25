"""Chile — término de contrato y horas extraordinarias. Esperado desde el Código del Trabajo (BCN, texto vigente):
arts. 163 (indemnización por años de servicio), 172 (base y tope de 90 UF), 161/162 (aviso), 67-73 (feriado) y 32 (horas
extraordinarias) y desde el criterio de la Dirección del Trabajo para el valor hora."""

from decimal import Decimal

import pytest

from payroll_engine.errors import InputValidationError

from .term_helpers import D, info, line_trace, lines, monthly, q, term

UF_AUG_31 = D("40873.77")                               # UF del 31-ago-2026 (SII); pago el 15-sep-2026
CAP = UF_AUG_31 * 90


def cl(end, hire="2015-03-10", cause="DISMISSAL_BUSINESS_NEEDS", salary="2000000", **kw):
    kw.setdefault("pay_date", end)
    return term("CL", hire, end, cause, salary, **kw)


@pytest.mark.parametrize("hire,end,years", [
    ("2020-01-01", "2026-06-30", 6),                  # 6 años y 6 meses exactos: la fracción NO es superior a 6 meses
    ("2020-01-01", "2026-07-01", 7),                  # 6 meses y un día: suma un año
    ("2020-01-01", "2026-06-29", 6),
    ("2024-03-01", "2026-09-15", 3),                  # 2 años, 6 meses y 15 días: 6 meses y 15 días > 6 meses -> 3
    ("2025-09-01", "2026-09-15", 1),                  # 1 año y 15 días: la fracción no supera 6 meses
])
def test_indemnizacion_un_mes_por_ano_y_fraccion_superior_a_seis_meses(hire, end, years):
    run = cl(end, hire=hire, salary="2000000")
    assert lines(run)["CL_INDEMNIZACION_ANOS_SERVICIO"] == q(D(2_000_000) / 30 * 30 * years)


def test_indemnizacion_exige_contrato_vigente_de_un_ano_o_mas():
    assert "CL_INDEMNIZACION_ANOS_SERVICIO" not in lines(cl("2026-09-15", hire="2025-09-17"))         # 11 meses y 30 días
    assert "CL_INDEMNIZACION_ANOS_SERVICIO" in lines(cl("2026-09-15", hire="2025-09-16"))            # exactamente 1 año
    assert "CL_INDEMNIZACION_ANOS_SERVICIO" in lines(cl("2026-09-15", hire="2025-09-15"))            # 1 año y 1 día


def test_indemnizacion_tope_de_330_dias():
    run = cl("2026-09-15", hire="2005-01-01", salary="2000000")           # 21 años: 630 días -> 330
    assert lines(run)["CL_INDEMNIZACION_ANOS_SERVICIO"] == q(D(2_000_000) / 30 * 330)
    assert line_trace(run, "CL_INDEMNIZACION_ANOS_SERVICIO")["details"]["cap_applied"] is True


def test_indemnizacion_base_topada_a_90_uf_del_ultimo_dia_del_mes_anterior():
    run = cl("2026-09-15", hire="2015-03-10", salary="6000000")           # 11 años, 6 meses, 6 días -> 12 años -> 330 días (tope)
    assert lines(run)["CL_INDEMNIZACION_ANOS_SERVICIO"] == q(CAP / 30 * 330)
    assert lines(run)["CL_INDEMNIZACION_AVISO_PREVIO"] == q(CAP)


def test_aviso_previo_una_remuneracion_mensual_si_no_se_dio_aviso_de_30_dias():
    with_notice = cl("2026-09-15", termination={"notice_given": True})
    assert "CL_INDEMNIZACION_AVISO_PREVIO" not in lines(with_notice)
    without = cl("2026-09-15", salary="2000000")
    assert lines(without)["CL_INDEMNIZACION_AVISO_PREVIO"] == D("2000000.00")


@pytest.mark.parametrize("cause,applies", [("DISMISSAL_BUSINESS_NEEDS", True), ("DISMISSAL_DESAHUCIO", True), ("RESIGNATION", False),
                                            ("DISMISSAL_WITH_CAUSE", False), ("MUTUAL_AGREEMENT", False), ("DEATH", False)])
def test_indemnizacion_solo_por_necesidades_de_la_empresa_o_desahucio(cause, applies):
    run = cl("2026-09-15", cause=cause)
    assert (lines(run).get("CL_INDEMNIZACION_ANOS_SERVICIO", 0) > 0) is applies


def test_despido_sin_causa_generico_no_es_una_causal_de_chile():
    with pytest.raises(InputValidationError) as err:
        cl("2026-09-15", cause="DISMISSAL_WITHOUT_CAUSE")
    assert "no está soportada para CL" in " ".join(err.value.details)


# ------------------------------------------------------------------------------------------- feriado proporcional (art. 73)
def test_feriado_15_dias_habiles_proporcionales_convertidos_a_dias_corridos():
    run = cl("2026-09-15", hire="2026-03-10", salary="1500000")
    days = D(15) * 190 / 365                                 # 10-mar .. 15-sep = 190 días
    assert lines(run)["CL_FERIADO_PROPORCIONAL"] == q(D(1_500_000) / 30 * days * D(7) / 5)
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "CL_FERIADO_PROPORCIONAL" for w in run.warnings) is True


@pytest.mark.parametrize("prior_years,completed_here,days", [
    (0, 5, 15), (10, 0, 15), (10, 3, 16), (12, 3, 16),        # antes de 10 años de trabajo total: 15; con 10: +1 por cada 3 años nuevos
    (0, 13, 16),                                              # 13 años en la empresa: 10 + 3 -> 1 día adicional
    (10, 6, 17),
    (25, 0, 15),                                              # los años previos cuentan hasta 10: 10 + 0 nuevos
])
def test_dias_de_feriado_con_progresivo_del_articulo_68(prior_years, completed_here, days):
    hire = f"{2026 - completed_here}-01-01" if completed_here else "2026-01-01"
    run = cl("2026-09-15", hire=hire, employment={"prior_years": prior_years})
    assert info(run, "CL_T_VACATION_DAYS") == days


# ------------------------------------------------------------------------------------------- horas extraordinarias
@pytest.mark.parametrize("period,weekly,hour", [(("2026-03-01", "2026-03-31"), 44, D(800_000) / (D(44) * 30 / 7)),
                                                 (("2026-06-01", "2026-06-30"), 42, D(800_000) / 180)])
def test_hora_extraordinaria_formula_de_la_direccion_del_trabajo_con_recargo_50(period, weekly, hour):
    run = monthly("CL", 800_000, period, time={"overtime_hours": "10"})
    assert run.line("CL_OVERTIME")["amount"] == q(hour * D("1.5") * 10)


def test_hora_extraordinaria_ejemplo_oficial_42_horas_800000():
    run = monthly("CL", 800_000, ("2026-06-01", "2026-06-30"), time={"overtime_hours": "1"})
    assert D(line_trace(run, "CL_OVERTIME")["details"]["hour_value"]) == D("800000") / 180
    assert run.line("CL_OVERTIME")["amount"] == D("6666.67")           # 4.444,44 × 1,5 (ejemplo de la DT)


def test_el_cambio_de_jornada_del_26_de_abril_de_2026_se_prorratea_por_dias():
    run = monthly("CL", 800_000, ("2026-04-01", "2026-04-30"), time={"overtime_hours": "10"})
    before = D(800_000) / (D(44) * 30 / 7) * D("1.5") * 10
    after = D(800_000) / 180 * D("1.5") * 10
    expected = (before * 25 + after * 5) / 30                          # 1-25 abr con 44 h; 26-30 abr con 42 h
    assert abs(run.line("CL_OVERTIME")["amount"] - expected) <= D("0.01")
    assert [s["fraction"] for s in line_trace(run, "CL_OVERTIME")["segments"]] == ["25/30", "5/30"]


# ------------------------------------------------------------------------------------------- estado y entrada
def test_fuentes_oficiales_del_codigo_del_trabajo_y_la_uf_del_sii():
    run = cl("2026-09-15", salary="6000000")
    src = {l["concept"]: l["source"] for l in run.trace["lines"]}
    assert src["CL_INDEMNIZACION_ANOS_SERVICIO"]["status"] == "OFFICIAL" and "bcn.cl" in src["CL_INDEMNIZACION_ANOS_SERVICIO"]["official_url"]
    assert set(r for r in run.normative_snapshot["references_used"] if r.startswith("CL.UF")) == {"CL.UF.2026@2026-08-31"}


def test_sin_pay_date_el_tope_usa_la_fecha_de_terminacion():
    run = term("CL", "2015-03-10", "2026-09-15", "DISMISSAL_BUSINESS_NEEDS", "6000000")
    assert D(next(b for b in run.trace["bases"] if b["base"] == "CL.INDEMNITY_BASE")["value"]) == CAP


def test_fecha_fuera_de_la_serie_uf_falla_en_vez_de_inventar_la_uf():
    from payroll_engine.errors import MissingReferenceError
    with pytest.raises(MissingReferenceError):
        cl("2026-11-20", salary="6000000")                              # el mes previo (oct-2026) aún no tiene UF completa


@pytest.mark.parametrize("hours,warns", [(2, False), (3, True)])
def test_cl_limite_de_dos_horas_extraordinarias_por_dia_es_advertencia(hours, warns):
    run = monthly("CL", 800_000, ("2026-06-01", "2026-06-30"), time={"overtime_hours": "1", "max_overtime_hours_in_a_day": str(hours)})
    assert any(w["type"] == "VALIDATION_WARNING" and "art. 31" in w["message"] for w in run.warnings) is warns
