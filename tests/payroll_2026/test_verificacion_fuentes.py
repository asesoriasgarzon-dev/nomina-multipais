"""Fuente oficial != interpretación correcta != implementación completa != validación profesional: cuatro dimensiones separadas."""

import copy

import pytest

from payroll_engine import verification
from payroll_engine.loader import load_country

COUNTRIES = ("CO", "MX", "PE", "CL", "BR", "AR", "EC", "US")
FIELDS = ("country", "jurisdiction", "rule_code", "effective_from", "effective_to", "source_title", "source_authority", "source_reference",
          "official_url", "source_status", "interpretation_status", "implementation_status", "verified_by", "verification_date", "notes",
          "source_verified", "interpretation_verified", "implementation_verified", "professional_validated")


def official_rule():
    rule = next(r for r in load_country("PE").rules if r["rule_key"] == "PE.CTS_TRUNCA")
    return copy.deepcopy(rule)


def test_una_fuente_oficial_no_implica_interpretacion_ni_implementacion_ni_validacion():
    rule = official_rule()
    f = verification.flags(rule)
    assert f["source_verified"] is True
    assert f["interpretation_verified"] is False and f["professional_validated"] is False
    assert f["implementation_verified"] is False                      # la regla es PARTIAL


def test_las_cuatro_dimensiones_se_activan_por_separado():
    rule = official_rule()
    rule["verification"]["interpretation_status"] = "VALIDATED"
    assert verification.flags(rule)["interpretation_verified"] is True and verification.flags(rule)["professional_validated"] is False
    rule["implementation_status"] = "IMPLEMENTED"
    assert verification.flags(rule)["implementation_verified"] is True
    rule["verification"].update({"professional_validation": "VALIDATED", "validated_by": "Abogada laboralista", "validated_at": "2026-09-25"})
    assert verification.flags(rule)["professional_validated"] is True


def test_la_validacion_profesional_exige_una_persona_y_fecha():
    rule = official_rule()
    rule["verification"]["professional_validation"] = "VALIDATED"
    assert verification.flags(rule)["professional_validated"] is False       # sin validated_by / validated_at no cuenta


def test_una_fuente_oficial_incompleta_no_cuenta_como_verificada():
    rule = official_rule()
    rule["source"].pop("official_url")
    assert verification.flags(rule)["source_verified"] is False


@pytest.mark.parametrize("cc", COUNTRIES)
def test_el_registro_de_fuentes_tiene_todos_los_campos_y_ninguna_validacion_profesional(cc):
    rows = verification.registry(load_country(cc))
    assert rows
    for row in rows:
        assert all(f in row for f in FIELDS)
        assert row["professional_validated"] is False
        if row["source_status"] == "OFFICIAL":
            assert row["source_authority"] and row["source_reference"] and row["official_url"] and row["verification_date"]
            assert "no es validación profesional" in row["verified_by"]


def test_las_reglas_con_pregunta_abierta_quedan_marcadas_en_el_registro():
    open_rows = [r for c in COUNTRIES for r in verification.registry(load_country(c)) if r["open_question"]]
    assert open_rows and all(r["interpretation_status"] in ("UNREVIEWED", "CONFLICTING") for r in open_rows)
    ids = {r["rule_code"] for r in open_rows}
    assert {"BR.OVERTIME.1", "MX.OVERTIME.2", "CL.FERIADO.1"} & ids
