"""Colombia — retención en la fuente de nómina mensual (procedimiento 1). Esperado calculado AQUÍ desde el texto oficial:
tabla del art. 383 ET (en UVT), deducciones del art. 387, tope del 40 % (art. 388), renta exenta 25 % con 790 UVT anuales
(art. 206 num. 10) y UVT 2026 = $52.374 (Res. DIAN 238/2025). Fuentes aún PENDING: tope de 1.340 UVT, intereses de vivienda."""

from decimal import Decimal

import pytest

from payroll_engine.loader import load_country
from payroll_engine.run import PayrollEngine, reproduce

from .helpers import co_payload, q

UVT = Decimal(52374)
SMMLV = Decimal(1750905)
TABLE = [(0, 95, 0, 0), (95, 150, "0.19", 0), (150, 360, "0.28", 10), (360, 640, "0.33", 69), (640, 945, "0.35", 162),
         (945, 2300, "0.37", 268), (2300, None, "0.39", 770)]


def tax_uvt(units):
    for lo, hi, rate, plus in TABLE:
        if units > lo and (hi is None or units <= hi):
            return (units - Decimal(lo)) * Decimal(rate) + Decimal(plus)
    return Decimal(0)


def run(salary, mode="CALCULATED", employment=None, amounts=None, **kw):
    p = co_payload(str(salary), amounts=amounts, **kw)
    p["employment"]["withholding_mode"] = mode
    p["employment"].update(employment or {})
    return PayrollEngine().run(p)


def expected(salary):
    """Retención esperada para un salario ordinario de 30 días, sin auxilio, con los aportes obligatorios de ley."""
    salary = Decimal(salary)
    ibc = min(salary, 25 * SMMLV)
    health, pension = q(ibc * Decimal("0.04")), q(ibc * Decimal("0.04"))
    fsp_rate = Decimal(0)
    for lo, hi, rate in ((4, 16, "0.01"), (16, 17, "0.012"), (17, 18, "0.014"), (18, 19, "0.016"), (19, 20, "0.018"), (20, None, "0.02")):
        if salary / SMMLV >= lo and (hi is None or salary / SMMLV < hi):
            fsp_rate = Decimal(rate)
    net = salary - health - pension - q(ibc * fsp_rate)
    exempt = min(net * Decimal("0.25"), 790 * UVT / 12)
    reductions = min(exempt, net * Decimal("0.40"), 1340 * UVT / 12)
    return q(tax_uvt((net - reductions) / UVT) * UVT)


def withheld(r):
    return r.line("WITHHOLDING_TAX_CALC")["amount"]


def details(r):
    return next(l for l in r.trace["lines"] if l["concept"] == "WITHHOLDING_TAX_CALC")["details"]


@pytest.mark.parametrize("salary", [3_000_000, 5_000_000, 8_000_000, 15_000_000, 30_000_000, 60_000_000])
def test_retencion_calculada_coincide_con_el_esperado_independiente(salary):
    assert abs(withheld(run(salary)) - expected(salary)) <= Decimal("0.02")


@pytest.mark.parametrize("salary", [1_500_000, 2_000_000, 2_500_000])
def test_ingresos_bajos_no_retienen(salary):
    assert withheld(run(salary)) == 0


def test_frontera_de_95_uvt_de_la_base_gravable():
    """Base gravable = neto × 0,75 (el 25 % no llega a su tope): con 95 UVT exactas no retiene; un poco más, sí."""
    net = Decimal(95) * UVT / Decimal("0.75")
    salary = int(net / Decimal("0.92"))                  # aportes de 8 % (salud + pensión) para salarios < 4 SMMLV
    assert withheld(run(salary)) <= Decimal("2")
    assert withheld(run(salary + 100_000)) > withheld(run(salary))


def test_la_tabla_es_la_del_articulo_383_y_la_uvt_2026_es_oficial():
    rule = next(r for r in load_country("CO").rules if r["rule_key"] == "CO.WITHHOLDING_TAX_CALC")
    table = [(r["from"], r["to"], r["rate"], r["plus"]) for r in rule["calculation"]["params"]["table"]]
    assert table == [("0", "95", "0", "0"), ("95", "150", "0.19", "0"), ("150", "360", "0.28", "10"), ("360", "640", "0.33", "69"),
                     ("640", "945", "0.35", "162"), ("945", "2300", "0.37", "268"), ("2300", None, "0.39", "770")]
    uvt = next(r for r in load_country("CO").references if r["code"] == "UVT")
    assert uvt["value"] == "52374" and uvt["source"]["status"] == "OFFICIAL" and "238" in uvt["source"]["legal_reference"]


def test_deduccion_por_dependientes_10_por_ciento_con_maximo_32_uvt():
    r = run(30_000_000, employment={"has_dependents": True})
    ded = {d["key"]: d for d in details(r)["deductions"]}
    assert Decimal(ded["dependientes_art_387"]["applied"]) == 32 * UVT              # 10 % de 30 M = 3 M > 32 UVT
    assert withheld(r) < withheld(run(30_000_000))
    low = {d["key"]: d for d in details(run(5_000_000, employment={"has_dependents": True}))["deductions"]}
    assert Decimal(low["dependientes_art_387"]["applied"]) == Decimal("500000")     # 10 % de 5 M < 32 UVT


def test_salud_prepagada_hasta_16_uvt_y_sin_dependientes_no_deduce():
    ded = {d["key"]: d for d in details(run(20_000_000, amounts={"prepaid_health": "2000000"}))["deductions"]}
    assert Decimal(ded["salud_prepagada_art_387"]["applied"]) == 16 * UVT
    assert Decimal(ded["dependientes_art_387"]["applied"]) == 0


def test_renta_exenta_del_25_por_ciento_tiene_tope_de_790_uvt_anuales():
    ex = details(run(60_000_000))["exempt_share"]
    assert Decimal(ex["cap"]) == 790 * UVT / 12 and Decimal(ex["applied"]) == 790 * UVT / 12


def test_tope_global_del_40_por_ciento_y_afc_se_suma_a_las_exentas():
    assert withheld(run(10_000_000, amounts={"AFC_DEDUCTION": "2000000"})) < withheld(run(10_000_000))
    assert details(run(10_000_000, amounts={"AFC_DEDUCTION": "9000000"}))["global_cap"]["cap_applied"] is True


def test_modo_manual_conserva_el_valor_digitado_y_calculado_lo_reemplaza():
    manual = run(8_000_000, mode="MANUAL", amounts={"WITHHOLDING_TAX": "69001"})
    assert manual.line("WITHHOLDING_TAX")["amount"] == Decimal("69001.00") and manual.line("WITHHOLDING_TAX_CALC") is None
    calc = run(8_000_000, amounts={"WITHHOLDING_TAX": "69001"})
    assert calc.line("WITHHOLDING_TAX") is None and withheld(calc) != Decimal("69001.00")


def test_la_retencion_calculada_esta_marcada_provisional_y_no_es_external_input():
    r = run(8_000_000)
    assert not any(w["type"] == "EXTERNAL_INPUT" and w.get("concept") == "WITHHOLDING_TAX_CALC" for w in r.warnings)
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "WITHHOLDING_TAX_CALC" for w in r.warnings)
    src = next(l for l in r.trace["lines"] if l["concept"] == "WITHHOLDING_TAX_CALC")["source"]
    assert src["status"] == "OFFICIAL" and "383" in src["legal_reference"]


def test_la_explicacion_muestra_cada_paso():
    d = details(run(8_000_000))
    for key in ("income", "base_before_depuration", "unit_value", "deductions", "exempt_share", "global_cap", "taxable_units", "bracket", "tax_units"):
        assert key in d
    assert d["bracket"]["rate"] == "0.19"


def test_el_integral_tambien_se_calcula_y_el_total_suma_las_lineas():
    r = run(30_000_000, salary_type="INTEGRAL")
    assert withheld(r) > 0
    assert r.result["totals"]["total_deducciones"] == sum(l["amount"] for l in r.result["lines"] if l["role"] == "EMPLOYEE_DEDUCTION")


def test_la_corrida_con_retencion_es_reproducible():
    r = run(15_000_000)
    assert reproduce(r.to_dict(), r._documents)["same"] is True


def test_el_formulario_web_ofrece_retencion_calculada_por_defecto_y_el_demo_queda_cerca_del_valor_digitado_original(monkeypatch):
    """DEMO de 8 M (28 días + 2 de incapacidad): la retención calculada difiere del valor digitado histórico (69.001) en pesos."""
    import app as application
    client = application.app.test_client()
    body = client.get("/novedades/CO?lang=es").get_data(as_text=True)
    assert "Calcular (art. 383 ET, provisional)" in body and "Valor digitado abajo" in body
    from .test_app_integration import CO_DEMO
    response = client.post("/novedades/CO?lang=es", data=CO_DEMO)
    import models
    run = models.obtener_payroll_run_por_nomina(int(response.headers["Location"].rsplit("/", 1)[1]))
    line = next(l for l in run["result"]["lines"] if l["concept"] == "WITHHOLDING_TAX_CALC")
    assert abs(Decimal(str(line["amount"])) - Decimal(69001)) < Decimal(10)
