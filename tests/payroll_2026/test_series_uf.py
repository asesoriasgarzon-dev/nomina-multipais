"""Series temporales de referencia (UF de Chile): resolución exacta por fecha ancla, sin extrapolar; tope de 90 UF de
las indemnizaciones (art. 172 CT) y topes imponibles de la Superintendencia de Pensiones con cambio en febrero."""

import copy
from datetime import date
from decimal import Decimal

import pytest

from payroll_engine import schema
from payroll_engine.errors import MissingReferenceError, StraddleError
from payroll_engine.loader import load_country
from payroll_engine.references import ReferenceResolver
from payroll_engine.run import PayrollEngine, reproduce

from .term_helpers import D, monthly, q, term


@pytest.fixture(scope="module")
def cl():
    return load_country("CL")


@pytest.fixture(scope="module")
def uf(cl):
    (serie,) = [s for s in cl.series if s["code"] == "UF"]
    return serie


def resolver(cl):
    return ReferenceResolver(cl.references, "CL", ["NATIONAL"], cl.series)


# ---------------------------------------------------------------------------------------- la serie
def test_la_serie_uf_tiene_fuente_oficial_del_sii_y_cobertura_declarada(uf):
    assert uf["source"]["status"] == "OFFICIAL" and uf["source"]["authority"].startswith("Servicio de Impuestos Internos")
    assert uf["source"]["official_url"] == "https://www.sii.cl/valores_y_fechas/uf/uf2026.htm"
    assert uf["coverage"] == {"from": "2026-01-01", "to": "2026-10-09"} and uf["granularity"] == "DAILY"
    assert len(uf["points"]) == 282                       # 1-ene .. 9-oct (los valores futuros aún no existen)
    assert schema.validate_series(uf) == []


@pytest.mark.parametrize("day,value", [("2026-01-01", "39731.79"), ("2026-04-30", "40120.20"), ("2026-05-01", "40133.50"),
                                       ("2026-08-31", "40873.77"), ("2026-10-09", "41130.94")])
def test_valores_conocidos_de_la_uf(uf, day, value):
    assert uf["points"][day] == value


def test_la_uf_no_tiene_huecos_dentro_de_la_cobertura(uf):
    days = sorted(uf["points"])
    first, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
    assert (last - first).days + 1 == len(days)


def test_la_uf_crece_de_forma_continua_salvo_deflacion_documentada(uf):
    values = [D(uf["points"][d]) for d in sorted(uf["points"])]
    assert all(abs(b - a) < Decimal(30) for a, b in zip(values, values[1:]))       # variación diaria pequeña: sin datos corruptos


def test_la_uf_se_resuelve_por_fecha_exacta(cl):
    r = resolver(cl)
    assert r.resolve("UF", date(2026, 3, 31)).value == Decimal("39841.72")
    resolved = r.resolve("UF", date(2026, 3, 31))
    assert resolved.ref_id == "CL.UF.2026@2026-03-31" and resolved.record["source"]["status"] == "OFFICIAL"


@pytest.mark.parametrize("day", [date(2025, 12, 31), date(2026, 10, 10), date(2027, 1, 1)])
def test_la_uf_no_se_extrapola_fuera_de_la_cobertura(cl, day):
    with pytest.raises(MissingReferenceError) as err:
        resolver(cl).resolve("UF", day)
    assert "No se extrapola" in err.value.message and "2026-10-09" in err.value.message


def test_una_serie_invalida_se_rechaza(uf):
    bad = copy.deepcopy(uf)
    bad["points"]["2026-02-01"] = "no-es-numero"
    assert any("no numérico" in i for i in schema.validate_series(bad))
    bad = copy.deepcopy(uf)
    bad["points"]["2027-05-05"] = "1"
    assert any("fuera de la cobertura" in i for i in schema.validate_series(bad))
    bad = copy.deepcopy(uf)
    bad["source"] = {"status": "OFFICIAL", "authority": "SII"}
    assert any("official_url" in i for i in schema.validate_series(bad))
    bad = copy.deepcopy(uf)
    bad["granularity"] = "HORARIA"
    assert any("granularity" in i for i in schema.validate_series(bad))


def test_la_serie_no_genera_puntos_de_cambio_dentro_del_periodo(cl):
    """Un índice diario se resuelve por fecha ancla: no bloquea períodos como lo haría un cambio de tasa."""
    assert resolver(cl).change_dates("UF", date(2026, 1, 1), date(2026, 9, 30)) == []


# ---------------------------------------------------------------------------------------- tope de 90 UF (art. 172)
def test_tope_de_indemnizacion_usa_la_uf_del_ultimo_dia_del_mes_anterior_al_pago():
    run = term("CL", "2015-03-10", "2026-09-15", "DISMISSAL_BUSINESS_NEEDS", "6000000", pay_date="2026-09-15")
    base = next(b for b in run.trace["bases"] if b["base"] == "CL.INDEMNITY_BASE")
    assert D(base["limits"]["maximum"]) == D("40873.77") * 90 and base["cap_applied"] is True      # UF del 31-ago-2026
    ref = [r for r in run.normative_snapshot["references_used"] if r.startswith("CL.UF.2026@")]
    assert ref == ["CL.UF.2026@2026-08-31"]


@pytest.mark.parametrize("pay_date,uf_day", [("2026-03-01", "2026-02-28"), ("2026-03-31", "2026-02-28"), ("2026-01-15", None),
                                              ("2026-09-15", "2026-08-31"), ("2026-10-09", "2026-09-30")])
def test_la_fecha_de_la_uf_es_el_fin_del_mes_previo_al_pago(pay_date, uf_day):
    if uf_day is None:          # el mes previo (dic-2025) queda fuera de la serie: falla en vez de inventar la UF
        with pytest.raises(MissingReferenceError):
            term("CL", "2015-03-10", pay_date, "DISMISSAL_BUSINESS_NEEDS", "6000000", pay_date=pay_date)
        return
    run = term("CL", "2015-03-10", pay_date, "DISMISSAL_BUSINESS_NEEDS", "6000000", pay_date=pay_date)
    assert [r for r in run.normative_snapshot["references_used"] if r.startswith("CL.UF.2026@")] == [f"CL.UF.2026@{uf_day}"]


def test_indemnizacion_frontera_del_tope_de_90_uf():
    cap = D("40873.77") * 90                              # 3.678.639,30 (pago el 15-sep-2026)
    below = term("CL", "2015-03-10", "2026-09-15", "DISMISSAL_BUSINESS_NEEDS", str(int(cap) - 1), pay_date="2026-09-15")
    exact_plus = term("CL", "2015-03-10", "2026-09-15", "DISMISSAL_BUSINESS_NEEDS", str(int(cap) + 1), pay_date="2026-09-15")
    b_below = next(b for b in below.trace["bases"] if b["base"] == "CL.INDEMNITY_BASE")
    b_above = next(b for b in exact_plus.trace["bases"] if b["base"] == "CL.INDEMNITY_BASE")
    assert b_below["cap_applied"] is False and D(b_below["value"]) == D(int(cap) - 1)
    assert b_above["cap_applied"] is True and D(b_above["value"]) == cap


# ---------------------------------------------------------------------------------------- topes imponibles mensuales
def test_tope_imponible_cambia_de_89_9_a_90_uf_el_1_de_febrero(cl):
    r = resolver(cl)
    assert r.resolve("TAX_CAP_UF_PENSION", date(2026, 1, 31)).value == Decimal("89.9")
    assert r.resolve("TAX_CAP_UF_PENSION", date(2026, 2, 1)).value == Decimal("90.0")
    assert r.resolve("TAX_CAP_UF_UNEMPLOYMENT", date(2026, 1, 31)).value == Decimal("135.1")
    assert r.resolve("TAX_CAP_UF_UNEMPLOYMENT", date(2026, 2, 1)).value == Decimal("135.2")
    src = r.resolve("TAX_CAP_UF_PENSION", date(2026, 2, 1)).record["source"]
    assert src["status"] == "OFFICIAL" and "Res. exenta SP N°27" in src["legal_reference"] and src["official_url"].startswith("https://www.dt.gob.cl")


def test_afp_y_salud_se_topan_a_90_uf_de_la_uf_del_ultimo_dia_del_periodo():
    run = monthly("CL", 9_000_000, ("2026-03-01", "2026-03-31"))
    cap = D("39841.72") * 90                               # UF del 31-mar-2026
    base = next(b for b in run.trace["bases"] if b["base"] == "CL_TAXABLE_BASE")
    assert D(base["value"]) == cap and base["cap_applied"] is True
    assert run.line("AFP_CONTRIBUTION")["amount"] == q(cap * D("0.10"))
    assert run.line("HEALTH")["amount"] == q(cap * D("0.07"))


def test_el_seguro_de_cesantia_tiene_su_propio_tope_de_135_2_uf():
    run = monthly("CL", 9_000_000, ("2026-03-01", "2026-03-31"))
    cap = D("39841.72") * D("135.2")
    base = next(b for b in run.trace["bases"] if b["base"] == "CL_UNEMPLOYMENT_BASE")
    assert D(base["value"]) == cap
    assert run.line("AFC_EMPLOYEE")["amount"] == q(cap * D("0.006"))
    assert run.line("AFC_EMPLOYER")["amount"] == q(cap * D("0.024"))


@pytest.mark.parametrize("delta,capped", [(-1, False), (0, False), (1, True)])
def test_frontera_del_tope_imponible_de_pension(delta, capped):
    cap = D("39841.72") * 90                               # 3.585.754,80 en marzo-2026
    salary = int(cap) + delta                              # 3.585.753 / 3.585.754 / 3.585.755
    run = monthly("CL", salary, ("2026-03-01", "2026-03-31"))
    base = next(b for b in run.trace["bases"] if b["base"] == "CL_TAXABLE_BASE")
    assert base["cap_applied"] is capped
    assert D(base["value"]) == (D(salary) if not capped else cap)


def test_enero_usa_el_tope_de_89_9_uf():
    run = monthly("CL", 9_000_000, ("2026-01-01", "2026-01-31"))
    base = next(b for b in run.trace["bases"] if b["base"] == "CL_TAXABLE_BASE")
    assert D(base["value"]) == D("39706.07") * D("89.9")


def test_un_periodo_que_cruza_el_cambio_del_tope_se_bloquea_y_no_se_oculta():
    with pytest.raises(StraddleError) as err:
        monthly("CL", 900_000, ("2026-01-16", "2026-02-15"))
    assert "TAX_CAP_UF_PENSION" in err.value.message and "2026-02-01" in err.value.message


def test_la_corrida_con_serie_es_reproducible_con_su_snapshot():
    run = monthly("CL", 9_000_000, ("2026-03-01", "2026-03-31"))
    docs = run._documents
    assert "series" in docs and len(docs["series"][0]["points"]) == 282     # el snapshot lleva la serie que se usó
    again = reproduce(run.to_dict(), docs)
    assert again["same"] is True
