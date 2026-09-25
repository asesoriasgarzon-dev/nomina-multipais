"""Guardas de arquitectura: el núcleo no conoce ningún país, la UI no tiene valores legales
escritos y los adaptadores no contienen tasas. Si alguien reintroduce `if country == ...` o un
porcentaje en el código, estas pruebas fallan."""

import ast
import glob
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COUNTRY_CODES = {"CO", "MX", "PE", "CL", "BR", "AR", "EC", "US", "HK", "ZZ"}
COUNTRY_NAMES = {"Colombia", "México", "Perú", "Chile", "Brasil", "Argentina", "Ecuador", "Estados Unidos", "Hong Kong"}
LEGAL_TERMS = {"SMMLV", "UMA", "RMV", "SBU", "SMVM", "IBC", "SBC", "INSS", "FGTS", "AFP", "IMSS", "ISR", "IRRF"}


def _py(pattern):
    return sorted(glob.glob(os.path.join(ROOT, pattern), recursive=True))


def _string_constants(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.value, node.lineno


@pytest.mark.parametrize("path", _py("payroll_engine/*.py"))
def test_el_nucleo_no_contiene_paises_ni_reglas_de_pais(path):
    for value, line in _string_constants(path):
        assert value not in COUNTRY_CODES, f"{path}:{line} código de país '{value}' en el núcleo"
        assert value not in COUNTRY_NAMES and value not in LEGAL_TERMS, f"{path}:{line} '{value}' en el núcleo"


@pytest.mark.parametrize("path", _py("payroll_engine/*.py"))
def test_el_nucleo_no_ramifica_por_pais(path):
    source = open(path, encoding="utf-8").read()
    assert 'country ==' not in source and "country ==" not in source.replace('"', "'")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and comparator.value in COUNTRY_CODES:
                    pytest.fail(f"{path}:{node.lineno} compara contra un código de país")


@pytest.mark.parametrize("path", _py("payroll_engine/*.py"))
def test_el_nucleo_no_usa_float_para_dinero(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            pytest.fail(f"{path}:{node.lineno} literal float {node.value}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float":
            if not path.endswith("legacy_adapter.py"):
                pytest.fail(f"{path}:{node.lineno} conversión a float")


@pytest.mark.parametrize("path", ["countries/colombia_normative.py", "countries/normative_engines.py"])
def test_los_adaptadores_no_contienen_tasas_ni_montos_legales(path):
    tree = ast.parse(open(os.path.join(ROOT, path), encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            pytest.fail(f"{path}:{node.lineno} porcentaje/monto hardcodeado {node.value}")
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool) and node.value not in (0, 1):
            pytest.fail(f"{path}:{node.lineno} número hardcodeado {node.value}")


def test_la_ui_y_app_no_tienen_valores_legales_escritos():
    banned = ["1750905", "1.750.905", "249095", "249.095", "3501810", "43772625", "22761765", "117.31", "315.04", "8475.55", "7.25"]
    files = _py("templates/*.html") + [os.path.join(ROOT, "app.py")]
    for path in files:
        text = open(path, encoding="utf-8").read()
        for value in banned:
            assert value not in text, f"{path} contiene el valor legal {value}"


def test_la_ui_no_afirma_motor_activo():
    import app
    for key, (css, icon, title, desc) in app.ESTADO_INFO.items():
        assert "activo" not in key and "active" not in key
    for lang in ("es", "en", "pt", "zh", "zh-hk"):
        data = json.load(open(os.path.join(ROOT, "i18n", f"{lang}.json"), encoding="utf-8"))
        for key, (_, _, title_key, desc_key) in app.ESTADO_INFO.items():
            text = (data[title_key] + data[desc_key]).lower()
            assert "motor activo" not in text and "active engine" not in text and "motor ativo" not in text


def test_las_cinco_lenguas_tienen_las_mismas_claves():
    keys = {lang: set(json.load(open(os.path.join(ROOT, "i18n", f"{lang}.json"), encoding="utf-8"))) for lang in ("es", "en", "pt", "zh", "zh-hk")}
    reference = keys["es"]
    for lang, ks in keys.items():
        assert ks == reference, (lang, sorted(ks ^ reference)[:10])


def test_agregar_un_pais_no_exige_tocar_el_nucleo():
    """El paquete sintético ZZ (no registrado en config/) se ejecuta con el mismo núcleo sin ningún cambio."""
    from payroll_engine.run import PayrollEngine
    from tests.payroll_2026 import synthetic as S
    result = PayrollEngine().run(S.payload(), ruleset=S.zz_ruleset())
    assert result.country == "ZZ" and result.result["lines"]


def test_los_datos_normativos_estan_separados_por_pais_y_anio():
    for cc in ("CO", "MX", "PE", "CL", "BR", "AR", "EC", "US", "HK"):
        pack = os.path.join(ROOT, "config", "payroll", cc, "2026")
        assert os.path.isdir(pack), pack
        for name in ("manifest.json", "references.json", "concepts.json", "bases.json", "rules.json", "rounding.json"):
            assert os.path.isfile(os.path.join(pack, name)), (cc, name)
    assert not os.path.exists(os.path.join(ROOT, "config", "payroll_rules_2026.json"))          # sin un JSON gigante único
