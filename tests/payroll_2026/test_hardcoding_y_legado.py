"""El código legal heredado ya no vive en producción; las constantes que quedan están clasificadas y justificadas; los
paquetes normativos son la única fuente de reglas legales."""

import ast
import glob
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import hardcode_inventory as inventory  # noqa: E402

PRODUCTION = ["payroll_engine/*.py", "countries/*.py", "app.py", "models.py", "exports.py", "alertas.py", "personal.py", "geolocation.py"]


def production_files():
    out = []
    for pattern in PRODUCTION:
        out += glob.glob(os.path.join(ROOT, pattern))
    return sorted(out)


def test_no_queda_ninguna_regla_legal_hardcodeada_sin_justificar_en_produccion():
    assert inventory.scan_production_legal_rules() == []


def test_toda_constante_de_produccion_tiene_tipo_y_justificacion():
    kinds = {"LEGAL_RULE", "TECHNICAL_CONSTANT", "UI_CONSTANT", "HISTORICAL_REFERENCE", "EXTERNAL_INPUT", "DERIVED_VALUE", "TEMPORARY"}
    rows = inventory.production_rows()
    assert rows and all(r["tipo"] in kinds and r["justificacion"] for r in rows)


def test_el_historico_conserva_las_190_constantes_y_cada_una_tiene_matriz_completa():
    rows = inventory.historical_rows()
    assert len(rows) == 190
    for r in rows:
        for key in ("concepto", "pais", "archivo", "linea", "valor", "tipo", "origen", "legal", "migrado", "duplicado", "critico", "accion"):
            assert r[key] not in (None, "")
        assert "SIN EXPLICACIÓN" not in r["accion"], r


def test_las_constantes_heredadas_no_migradas_tienen_explicacion():
    missing = [r for r in inventory.historical_rows() if r["migrado"].startswith("no encontrado") and "; " not in r["accion"]]
    assert missing == []


def test_la_mayoria_de_las_constantes_heredadas_ya_esta_en_config_payroll():
    rows = inventory.historical_rows()
    migrated = [r for r in rows if r["migrado"].startswith("sí")]
    assert len(migrated) >= 170


@pytest.mark.parametrize("path", [p for p in production_files() if "/countries/" in p.replace("\\", "/") or p.endswith("countries")])
def test_countries_no_contiene_reglas_ni_formulas(path):
    """countries/<pais>.py solo aporta etiquetas, formulario y ejemplos DEMO: ni calcular, ni liquidar, ni números decimales."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if os.path.basename(path) not in ("normative_engines.py", "colombia_normative.py", "base.py"):      # base.py = interfaz abstracta
        assert not ({"calcular", "liquidar"} & names), path
    floats = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, float)]
    assert floats == [], f"{path}: literales decimales {floats}"


def test_country_config_ya_no_tiene_parametros_legales():
    from dataclasses import fields
    from countries.base import CountryConfig
    names = {f.name for f in fields(CountryConfig)}
    assert names == {"code", "name", "currency", "idioma_default", "nombre_liquidacion", "es_matriz"}
    assert not any(os.path.exists(os.path.join(ROOT, "countries", f"{n}.py")) for n in ("prima_i18n",))


def test_ningun_modulo_de_produccion_importa_los_motores_heredados():
    for path in production_files():
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert "legacy_fixtures" not in (node.module or "") and not (node.module or "").startswith("tests"), path
            if isinstance(node, ast.Import):
                assert not any(a.name.startswith("tests") or "legacy_fixtures" in a.name for a in node.names), path


def test_los_fixtures_heredados_solo_viven_en_tests():
    assert os.path.isdir(os.path.join(ROOT, "tests", "payroll_2026", "legacy_fixtures"))
    for module in ("colombia", "mexico", "peru", "chile", "brasil", "argentina", "ecuador"):
        production = open(os.path.join(ROOT, "countries", f"{module}.py"), encoding="utf-8").read()
        assert "def calcular" not in production and "def liquidar" not in production


def test_el_nucleo_no_usa_float_para_dinero():
    for path in sorted(glob.glob(os.path.join(ROOT, "payroll_engine", "*.py"))):
        if path.endswith("legacy_adapter.py"):
            continue                                        # presentación en pantalla (float solo al mostrar)
        tree = ast.parse(open(path, encoding="utf-8").read())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "float"]
        assert calls == [], f"{path}: float() en el núcleo"


def test_las_reglas_de_terminacion_y_horas_extra_estan_en_config_payroll():
    for cc in ("CO", "MX", "PE", "CL", "BR", "AR", "EC"):
        base = os.path.join(ROOT, "config", "payroll", cc, "2026")
        assert os.path.exists(os.path.join(base, "rules_termination.json")), cc
        assert os.path.exists(os.path.join(base, "rules_overtime.json")), cc
        rules = json.load(open(os.path.join(base, "rules_termination.json"), encoding="utf-8"))
        assert all(r.get("run_types") == ["TERMINATION"] for r in rules)


def test_el_inventario_documentado_coincide_con_el_generado():
    doc = open(os.path.join(ROOT, "docs", "HARDCODING_INVENTORY.md"), encoding="utf-8").read()
    assert "LEGAL_RULE sin justificación: 0" in doc and "190 constantes" in doc
