"""Validador de esquema y control de fuentes: ninguna regla entra sin vigencia, fuente y estado de
verificación; no se puede declarar OFFICIAL sin respaldo ni VALIDATED sin una persona."""

import copy
from datetime import date

import pytest

from payroll_engine.errors import SchemaError
from payroll_engine.loader import RuleSetData, available_countries, load_country
from payroll_engine.schema import validate_reference, validate_rule
from tests.payroll_2026 import synthetic as S

COUNTRIES = ["CO", "MX", "PE", "CL", "BR", "AR", "EC", "US", "HK"]


def test_los_nueve_contextos_existen_y_no_hay_otros():
    assert sorted(available_countries()) == sorted(COUNTRIES)


@pytest.mark.parametrize("cc", COUNTRIES)
def test_todos_los_paquetes_cargan_y_pasan_el_validador(cc):
    rs = load_country(cc, use_cache=False)
    assert rs.manifest["country"] == cc and rs.content_hash


@pytest.mark.parametrize("cc", COUNTRIES)
def test_todo_dato_normativo_tiene_vigencia_fuente_y_verificacion(cc):
    rs = load_country(cc)
    for rule in rs.rules:
        assert rule["effective"]["from"], rule["rule_id"]
        assert rule["source"]["status"] in ("OFFICIAL", "SECONDARY", "PENDING", "CONFLICTING", "NOT_APPLICABLE")
        assert rule["verification"]["interpretation_status"] and rule["verification"]["professional_validation"]
        assert rule["implementation_status"] in ("NOT_IMPLEMENTED", "PARTIAL", "IMPLEMENTED")
    for ref in rs.references:
        assert ref["effective"]["from"] and ref["source"]["status"] and ref["verification"]["professional_validation"]


@pytest.mark.parametrize("cc", COUNTRIES)
def test_las_fuentes_oficiales_tienen_autoridad_referencia_url_y_fecha(cc):
    rs = load_country(cc)
    docs = rs.rules + rs.references + rs.concept_list + rs.bases
    for doc in docs:
        src = doc.get("source") or {}
        if src.get("status") == "OFFICIAL":
            assert src["authority"] and src["legal_reference"] and src["official_url"].startswith("https://"), doc
            assert date.fromisoformat(src["verified_at"]) <= date.today()


def test_ninguna_validacion_profesional_esta_marcada_como_realizada():
    """Claude no realiza validación profesional: todo queda PENDING hasta que una persona la firme."""
    for cc in COUNTRIES:
        rs = load_country(cc)
        for doc in rs.rules + rs.references + rs.concept_list + rs.bases:
            ver = doc.get("verification") or {}
            assert ver.get("professional_validation") == "PENDING", (cc, doc.get("rule_id") or doc.get("ref_id") or doc.get("concept"))
            assert "validated_by" not in ver


def test_las_reglas_que_reproducen_el_motor_heredado_estan_marcadas_pendientes():
    """Los datos migrados del motor heredado no se presentan como verificados oficialmente."""
    for cc in ("MX", "PE", "CL", "BR", "AR", "EC"):
        legacy_rules = [r for r in load_country(cc).rules if r["rule_key"].split(".")[-1] not in ("REMUNERATION", "SALARY_EARNED")
                        and r["kind"] not in ("VALIDATION",) and r["source"]["status"] == "PENDING"]
        assert legacy_rules, cc
        assert all(r["source"]["status"] != "OFFICIAL" for r in legacy_rules)


def test_la_vigencia_esta_modelada_donde_la_norma_cambia_en_2026():
    assert len([r for r in load_country("AR").references if r["code"] == "SMVM"]) == 12
    assert len([r for r in load_country("CL").references if r["code"] == "MIN_INCOME"]) == 2
    assert len([r for r in load_country("MX").references if r["code"] == "UMA_DAILY"]) == 2
    assert len([r for r in load_country("CO").references if r["code"] == "WORKWEEK_HOURS"]) == 2
    assert len([r for r in load_country("CL").rules if r["rule_key"] == "CL.SIS_EMPLOYER"]) == 3
    assert len([r for r in load_country("CL").references if r["code"] == "TAX_CAP_UF_PENSION"]) == 2


# ------------------------------------------------------------------ rechazos del validador
def test_no_se_puede_declarar_oficial_sin_respaldo():
    ref = copy.deepcopy(S.zz_docs()["references"][0])
    ref["source"] = {"status": "OFFICIAL", "authority": "X"}
    issues = validate_reference(ref)
    assert any("legal_reference" in i for i in issues) and any("official_url" in i for i in issues) and any("verified_at" in i for i in issues)


def test_no_se_puede_validar_profesionalmente_sin_una_persona():
    ref = copy.deepcopy(S.zz_docs()["references"][0])
    ref["verification"] = {"interpretation_status": "VALIDATED", "professional_validation": "VALIDATED"}
    assert any("validated_by" in i for i in validate_reference(ref))
    ref["verification"].update({"validated_by": "Abogada laboralista", "validated_at": "2026-09-24"})
    assert validate_reference(ref) == []


@pytest.mark.parametrize("mutation,needle", [
    (lambda r: r.update(anchor="fecha_inventada"), "anchor"),
    (lambda r: r["calculation"].update(mechanism="formula_libre"), "mecanismo"),
    (lambda r: r.update(kind="OTRO"), "kind"),
    (lambda r: r.update(implementation_status="LISTO"), "implementation_status"),
    (lambda r: r.update(straddle_policy="IGNORAR"), "straddle_policy"),
    (lambda r: r.update(effective={"from": "2026-05-01", "to": "2026-01-01"}), "anterior"),
    (lambda r: r.update(effective={"to": None}), "effective"),
    (lambda r: r.update(conditions={"left": {"value": "1"}, "op": "~", "right": {"value": "2"}}), "operador"),
    (lambda r: r.pop("source"), "source"),
    (lambda r: r.pop("verification"), "verification"),
])
def test_el_validador_rechaza_reglas_mal_formadas(mutation, needle):
    rule = copy.deepcopy(S.zz_docs()["rules"][2])
    mutation(rule)
    assert any(needle in issue for issue in validate_rule(rule)), validate_rule(rule)


def test_el_mecanismo_exige_sus_parametros():
    rule = copy.deepcopy(S.zz_docs()["rules"][2])
    rule["calculation"]["params"] = {"base": "SS_BASE"}
    assert any("rate" in i for i in validate_rule(rule))


def test_no_se_aceptan_ids_duplicados_ni_conceptos_sin_definir():
    docs = copy.deepcopy(S.zz_docs())
    docs["rules"].append(copy.deepcopy(docs["rules"][0]))
    with pytest.raises(SchemaError):
        RuleSetData.from_documents(docs)
    docs = copy.deepcopy(S.zz_docs())
    docs["rules"][0]["concept"] = "NO_EXISTE"
    with pytest.raises(SchemaError):
        RuleSetData.from_documents(docs)


def test_los_valores_numericos_de_las_referencias_deben_ser_numeros():
    ref = copy.deepcopy(S.zz_docs()["references"][0])
    ref["value"] = "mucho"
    assert any("numérico" in i for i in validate_reference(ref))
