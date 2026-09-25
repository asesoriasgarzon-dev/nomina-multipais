"""Matriz de capacidades (componentes críticos), estados honestos por país y horas extra de Perú y Argentina."""

from decimal import Decimal

import pytest

from countries import REGISTRY, resumen_internacional
from payroll_engine import capabilities, schema
from payroll_engine.loader import load_country

from .term_helpers import D, monthly, q

COMPONENTS = ("monthly_payroll", "overtime", "surcharges", "vacation", "social_security", "benefits", "termination", "tax", "audit",
              "historical_recalculation")
COUNTRIES = ("CO", "MX", "PE", "CL", "BR", "AR", "EC")


# ---------------------------------------------------------------------------------------- matriz de componentes críticos
@pytest.mark.parametrize("cc", COUNTRIES + ("US", "HK"))
def test_cada_contexto_declara_los_diez_componentes_criticos(cc):
    comps = capabilities.describe(cc)["components"]
    assert tuple(comps) == COMPONENTS
    assert all(c["status"] in schema.CAPABILITY_STATUS for c in comps.values())


@pytest.mark.parametrize("cc", COUNTRIES)
def test_ningun_pais_es_implementado_ni_tiene_motor_completo(cc):
    info = capabilities.describe(cc)
    assert info["complete_engine"] is False and info["state"] != "implementado"
    assert info["components"]["tax"]["status"] == ("PARTIALLY_IMPLEMENTED" if cc == "CO" else "NOT_IMPLEMENTED")   # solo CO calcula (proc. 1)
    assert info["components"]["historical_recalculation"]["status"] == "PARTIALLY_IMPLEMENTED"     # sin ajuste contable ni encadenamiento
    assert info["components"]["audit"]["status"] == "IMPLEMENTED"


@pytest.mark.parametrize("cc", COUNTRIES)
def test_la_terminacion_ya_no_esta_declarada_como_heredada(cc):
    info = capabilities.describe(cc)
    assert info["components"]["termination"]["status"] == "PARTIALLY_IMPLEMENTED"
    assert not any("LIQUIDACIÓN heredada" in g for g in info["known_gaps"])
    assert "heredada" not in info["capabilities"]["termination"]["note"].lower()


def test_us_es_estructura_sin_motor_y_hk_es_consolidacion_sin_nomina_local():
    us, hk = capabilities.describe("US"), capabilities.describe("HK")
    assert us["state"] == "no_implementado" and us["local_payroll_engine"] is False
    assert all(c["status"] == "NOT_IMPLEMENTED" for c in us["components"].values())
    manifest = load_country("US").manifest
    assert manifest["jurisdiction_levels"] == ["FEDERAL", "STATE", "LOCAL"] and manifest["employee_classes"] == ["EXEMPT", "NON_EXEMPT"]
    assert hk["state"] == "consolidacion" and hk["local_payroll_engine"] is False and hk["consolidation_context"] is True
    assert all(c["status"] == "NOT_APPLICABLE" for c in hk["components"].values())


def test_resumen_global_cuenta_motores_parciales_y_ninguno_completo():
    resumen = resumen_internacional()
    assert resumen["motores_parciales"] == 7 and resumen["motores_completos"] == 0


def test_un_pais_solo_seria_completo_si_todos_los_componentes_lo_son():
    manifest = {"country": "ZZ", "local_payroll_engine": True, "consolidation_context": False,
                "capabilities": {"payroll_monthly": {"status": "IMPLEMENTED"}, "overtime_and_premiums": {"status": "IMPLEMENTED"},
                                 "surcharges": {"status": "IMPLEMENTED"}, "vacation": {"status": "IMPLEMENTED"},
                                 "social_security": {"status": "IMPLEMENTED"}, "benefit_accruals": {"status": "IMPLEMENTED"},
                                 "termination": {"status": "IMPLEMENTED"}, "income_tax_withholding": {"status": "IMPLEMENTED"}}}
    # aun con todo IMPLEMENTED, el recálculo histórico es parcial mientras no exista el ajuste contable ni el encadenamiento
    assert capabilities.complete_engine(manifest) is False
    assert capabilities.components(manifest)["historical_recalculation"]["status"] == "PARTIALLY_IMPLEMENTED"


def test_el_estado_incompleto_es_valido_en_el_esquema_de_capacidades():
    assert "INCOMPLETE" in schema.CAPABILITY_STATUS
    assert schema.validate_manifest({"country": "ZZ", "year": 2026, "ruleset_version": "x", "currency": "ZZC", "local_payroll_engine": True,
                                     "consolidation_context": False, "execution_path": "NEW_ENGINE",
                                     "capabilities": {"x": {"status": "INCOMPLETE"}}}) == []


@pytest.mark.parametrize("cc", COUNTRIES)
def test_nada_declara_validacion_profesional(cc):
    rs = load_country(cc)
    docs = rs.rules + rs.references + rs.concept_list + rs.bases + rs.series
    assert all((d.get("verification") or {}).get("professional_validation", "PENDING") != "VALIDATED" for d in docs)


@pytest.mark.parametrize("cc", COUNTRIES)
def test_las_reglas_de_terminacion_y_horas_extra_estan_como_datos_con_fuente_y_estado(cc):
    rs = load_country(cc)
    term_rules = [r for r in rs.rules if r.get("run_types") == ["TERMINATION"] and r["kind"] != "VALIDATION"]
    overtime = [r for r in rs.rules if r["category"] == "OVERTIME"]
    assert len(term_rules) >= 10 and overtime
    for r in term_rules + overtime:
        assert r["source"]["status"] in ("OFFICIAL", "SECONDARY", "PENDING", "NOT_APPLICABLE", "CONFLICTING")
        assert r["implementation_status"] in ("IMPLEMENTED", "PARTIAL", "NOT_IMPLEMENTED")
        assert r["verification"]["professional_validation"] == "PENDING"


def test_toda_regla_con_interpretacion_abierta_o_fuente_pendiente_advierte_en_la_corrida():
    run = monthly("BR", 5000, ("2026-09-01", "2026-09-30"), time={"overtime_hours_50": "1"})
    assert any(w["type"] == "UNVERIFIED_RULE" for w in run.warnings)


# ---------------------------------------------------------------------------------------- horas extra: Perú
def test_pe_sobretasa_25_las_dos_primeras_horas_y_35_las_siguientes():
    run = monthly("PE", 3000, ("2026-09-01", "2026-09-30"), time={"overtime_hours_first_2": "6", "overtime_hours_after_2": "4"})
    hour = D(3000) / 240
    assert run.line("PE_OVERTIME")["amount"] == q(hour * (D("1.25") * 6 + D("1.35") * 4))


def test_pe_divisor_del_valor_hora_esta_marcado_pendiente():
    run = monthly("PE", 3000, ("2026-09-01", "2026-09-30"), time={"overtime_hours_first_2": "2"})
    assert any(w["type"] == "UNVERIFIED_RULE" and w["concept"] == "PE_OVERTIME" for w in run.warnings)


# ---------------------------------------------------------------------------------------- horas extra: Argentina
def test_ar_horas_suplementarias_50_por_ciento_en_dia_comun_y_100_en_sabado_domingo_feriado():
    run = monthly("AR", 800_000, ("2026-09-01", "2026-09-30"), time={"overtime_hours_50": "10", "overtime_hours_100": "6"})
    hour = D(800_000) / 200
    assert run.line("AR_OVERTIME")["amount"] == q(hour * (D("1.5") * 10 + 2 * 6))


def test_ar_la_fuente_cita_el_texto_del_articulo_201_de_infoleg():
    run = monthly("AR", 800_000, ("2026-09-01", "2026-09-30"), time={"overtime_hours_50": "1"})
    src = next(l for l in run.trace["lines"] if l["concept"] == "AR_OVERTIME")["source"]
    assert src["status"] == "OFFICIAL" and "infoleg" in src["official_url"] and "art. 201" in src["legal_reference"]


# ---------------------------------------------------------------------------------------- páginas
@pytest.mark.parametrize("cc", COUNTRIES + ("US", "HK"))
def test_el_panel_muestra_los_componentes_criticos(cc):
    import app as application
    client = application.app.test_client()
    body = client.get(f"/pais/{cc}?lang=es").get_data(as_text=True)
    assert "Componentes críticos" in body and "Recálculo histórico" in body
    if cc in COUNTRIES:
        assert "Motor completo: ninguno" in body
