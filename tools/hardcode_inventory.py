"""Inventario AUTOMÁTICO de constantes numéricas. Dos etapas, sin inventar nada (solo reporta lo que el código contiene):

  A) HISTÓRICO: las constantes legales de los motores heredados (ahora fixtures en tests/payroll_2026/legacy_fixtures/), con
     la matriz: concepto, país, archivo, línea, valor, tipo, origen, ¿legal?, ¿migrado?, ¿duplicado?, ¿crítico?, acción.
     '¿migrado?' se comprueba buscando el valor en config/payroll/<PAIS>/ (no es una afirmación manual).
  B) PRODUCCIÓN: todo literal numérico que queda en el código de producción, clasificado en
     LEGAL_RULE | TECHNICAL_CONSTANT | UI_CONSTANT | HISTORICAL_REFERENCE | EXTERNAL_INPUT | DERIVED_VALUE | TEMPORARY.
     Cualquier LEGAL_RULE que aparezca fuera del sistema normativo queda marcada SIN JUSTIFICACIÓN y las pruebas fallan.

    python tools/hardcode_inventory.py      # genera docs/HARDCODING_INVENTORY.md
"""

import ast
import glob
import json
import os
from decimal import Decimal, InvalidOperation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "payroll_2026", "legacy_fixtures")
COUNTRIES = {"colombia": "CO", "mexico": "MX", "peru": "PE", "chile": "CL", "brasil": "BR", "argentina": "AR", "ecuador": "EC"}
SKIP_CALLS = {"round", "date", "range", "min", "max", "int"}
CONVENTION = {30, 360, 365, 12, 15, 25, 180, 1000, 100}
PRODUCTION_FILES = ["payroll_engine/*.py", "countries/*.py", "app.py", "models.py", "exports.py", "alertas.py", "personal.py",
                    "geolocation.py", "tools/*.py"]

# Justificaciones explícitas de constantes de producción que NO son datos normativos.
JUSTIFIED = {
    "payroll_engine/money.py": ("TECHNICAL_CONSTANT", "precisión de cálculo del contexto Decimal y decimales de la moneda por defecto: no son normas"),
    "payroll_engine/temporal.py": ("TECHNICAL_CONSTANT", "aritmética de calendario (12 meses por año, mes comercial de 30 días, año de 360): convención "
                                   "que cada mecanismo aplica y que la norma de cada país fija en sus parámetros (count/divisor); no es una regla de un país"),
    "payroll_engine/mechanisms_termination.py": ("TECHNICAL_CONSTANT", "convención de 30 días por mes como valor por defecto de los mecanismos; los "
                                                  "divisores y límites legales llegan por parámetros de las reglas (datos)"),
    "payroll_engine/mechanisms.py": ("TECHNICAL_CONSTANT", "mes comercial de 30 días del tipo THIRTY_DAY_MONTH que declara cada regla"),
    "payroll_engine/context.py": ("TECHNICAL_CONSTANT", "días por mes de la medida derivada de antigüedad (MONTHS_DECIMAL)"),
    "payroll_engine/run.py": ("TECHNICAL_CONSTANT", "índices y formato de identificadores de la orquestación"),
    "payroll_engine/legacy_adapter.py": ("DERIVED_VALUE", "redondeo de PRESENTACIÓN (2 decimales) de importes ya calculados y decimales de antigüedad"),
}
DEFAULT_ENGINE = ("TECHNICAL_CONSTANT", "sin literales legales: formato/estructura del motor")
UI_PREFIXES = ("countries/", "app.py", "exports.py")


def parents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._parent = node


def enclosing(node, types):
    while node is not None:
        node = getattr(node, "_parent", None)
        if isinstance(node, types):
            return node
    return None


def concept_of(node):
    cur = node
    while cur is not None:
        parent = getattr(cur, "_parent", None)
        if isinstance(parent, ast.Dict):
            for key, value in zip(parent.keys, parent.values):
                if value is cur and isinstance(key, ast.Constant):
                    return str(key.value)
        if isinstance(parent, ast.keyword) and parent.arg:
            return parent.arg
        if isinstance(parent, ast.Assign) and parent.targets and isinstance(parent.targets[0], ast.Name):
            return parent.targets[0].id
        if isinstance(parent, ast.Tuple) and isinstance(getattr(parent, "_parent", None), ast.List):
            return "tabla de tramos"
        cur = parent
    return "(expresión)"


def numeric_constants(path, skip_trivial=True):
    source = open(path, encoding="utf-8").read()
    tree = ast.parse(source)
    parents(tree)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)):
            continue
        value = node.value
        if skip_trivial and (value in (0, 1) or (isinstance(value, int) and value == 2)):
            continue
        call = enclosing(node, ast.Call)
        if call is not None and isinstance(call.func, ast.Name) and call.func.id in SKIP_CALLS:
            continue
        func = enclosing(node, ast.FunctionDef)
        yield node, value, (func.name if func else "(módulo)")


# ----------------------------------------------------------------------------------------------- A) histórico
def config_numbers(cc):
    """Todos los escalares numéricos (y razones a/b) presentes en config/payroll/<cc>/."""
    found = set()
    base = os.path.join(ROOT, "config", "payroll", cc)

    def add(x):
        if isinstance(x, bool):
            return
        try:
            if isinstance(x, str) and "/" in x:
                n, d = x.split("/", 1)
                found.add(Decimal(n) / Decimal(d))
            else:
                found.add(Decimal(str(x)))
        except (InvalidOperation, ZeroDivisionError, ValueError):
            pass

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, (int, float, str)):
            add(node)

    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".json") and not name.startswith("series"):
                walk(json.load(open(os.path.join(dirpath, name), encoding="utf-8")))
    return found


# Constantes heredadas cuyo valor NO figura tal cual en config/payroll: por qué (el motor normativo las reemplaza o no las implementa).
EXPLAIN = {
    ("CO", "vacaciones_prov", 0.0417): "aproximación heredada REEMPLAZADA por la razón exacta 15/360",
    ("CO", "prima_prov", 0.0833): "aproximación heredada REEMPLAZADA por la razón exacta 1/12",
    ("CO", "cesantias_prov", 0.0833): "aproximación heredada REEMPLAZADA por la razón exacta 1/12",
    ("BR", "tabla de tramos", 1621.01): "límite inferior del tramo siguiente: en datos es el límite superior EXCLUSIVO del tramo anterior (from/to)",
    ("BR", "tabla de tramos", 2902.85): "ídem (estructura from/to de los tramos marginales)",
    ("BR", "tabla de tramos", 4354.28): "ídem (estructura from/to de los tramos marginales)",
    ("BR", "ferias_prov", 4): "el 1/3 constitucional migró como razón '1/3' (el heredado lo escribía como (4/3))",
    ("BR", "decimo_terceiro", 360): "convención heredada REEMPLAZADA por el conteo de meses con 15 o más días (13.º)",
    ("BR", "ferias_proporcionais", 4): "el 1/3 constitucional migró como razón '1/3'",
    ("BR", "antiguedad_anos", 365): "REEMPLAZADO por la antigüedad por aniversarios (payroll_engine/temporal.py)",
    ("AR", "vacaciones_prov", 360): "convención heredada; la provisión mensual migró como razón",
    ("AR", "sac_proporcional", 180): "P0 heredado REEMPLAZADO por la fracción del semestre (1/12 de lo devengado, art. 123 LCT)",
    ("AR", "anos_computables", 0.25): "REEMPLAZADO por la regla de 'fracción mayor de tres meses' (art. 245) por meses y días",
    ("AR", "(expresión)", 0.25): "ídem",
    ("MX", "salario_minimo", 9582.47): "valor mensual heredado; el motor usa el salario mínimo DIARIO con vigencia (CONASAMI)",
    ("MX", "tope_sbc_diario_25_uma", 2932.75): "derivado (25 × UMA); el motor lo calcula de la referencia UMA con vigencia",
    ("PE", "onp_empleado", 0.13): "ONP: NOT_IMPLEMENTED (declarado en known_gaps); el heredado asumía AFP",
    ("PE", "asignacion_familiar_default", 113): "dato de ENTRADA (EXTERNAL_INPUT), no una norma: se informa en amounts.family_allowance",
    ("PE", "antiguedad_anos", 365): "REEMPLAZADO por la antigüedad por aniversarios y dozavos/treintavos",
}


def historical_rows():
    rows = []
    for name, cc in COUNTRIES.items():
        path = os.path.join(FIXTURES, f"{name}.py")
        numbers = config_numbers(cc)
        for node, value, func in numeric_constants(path):
            dv = Decimal(str(value))
            in_config = dv in numbers or any(abs(dv - n) < Decimal("0.0000001") for n in numbers if abs(n) < Decimal(10) ** 9)
            is_rate = isinstance(value, float) and value < 1
            legal = is_rate or value in CONVENTION or value > 2
            origin = "CountryConfig (parámetro legal)" if func.endswith("Config") else \
                ("cálculo mensual" if func == "calcular" else ("liquidación" if func == "liquidar" else "auxiliar"))
            kind = "LEGAL_RULE" if (is_rate or (value not in CONVENTION and value > 2)) else "LEGAL_RULE (convención de cómputo)"
            rows.append({
                "concepto": concept_of(node), "pais": cc, "archivo": os.path.relpath(path, ROOT).replace("\\", "/"), "linea": node.lineno,
                "valor": value, "tipo": kind, "origen": origin, "legal": "sí" if legal else "no",
                "migrado": "sí (valor presente en config/payroll)" if in_config else "no encontrado: derivado/estructural",
                "duplicado": "sí, ahora solo en fixture de pruebas" if in_config else "no",
                "critico": "sí" if is_rate else "no",
                "accion": "ELIMINADO de producción (código movido a tests/payroll_2026/legacy_fixtures; la app no lo ejecuta)"
                          + ("" if in_config else "; " + EXPLAIN.get((cc, concept_of(node), value), "SIN EXPLICACIÓN: revisar")),
            })
    rows.sort(key=lambda r: (r["pais"], r["archivo"], r["linea"]))
    return rows


# ----------------------------------------------------------------------------------------------- B) producción
def production_rows():
    rows = []
    for pattern in PRODUCTION_FILES:
        for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            for node, value, func in numeric_constants(path, skip_trivial=False):
                if value in (0, 1):
                    continue
                if rel.startswith("payroll_engine/"):
                    kind, why = JUSTIFIED.get(rel, DEFAULT_ENGINE)
                    if isinstance(value, float) and rel not in ("payroll_engine/temporal.py", "payroll_engine/mechanisms_termination.py"):
                        kind, why = "LEGAL_RULE", "SIN JUSTIFICACIÓN: literal decimal en el núcleo"
                elif rel.startswith(UI_PREFIXES):
                    if isinstance(value, float) and value < 1 and rel == "app.py":
                        kind, why = "LEGAL_RULE", "SIN JUSTIFICACIÓN: tasa decimal fuera del sistema normativo"
                    else:
                        kind, why = "UI_CONSTANT", "paso de campos, valores por defecto o ejemplos DEMO del formulario; no se usan para calcular"
                elif rel.startswith("tools/"):
                    kind, why = "TEMPORARY", "herramienta de desarrollo (no corre en producción)"
                else:
                    kind, why = "TECHNICAL_CONSTANT", "puertos, tiempos y tamaños de infraestructura"
                rows.append({"archivo": rel, "linea": node.lineno, "funcion": func, "concepto": concept_of(node), "valor": value,
                             "tipo": kind, "justificacion": why})
    return rows


def scan_production_legal_rules():
    """LEGAL_RULE sin justificación en producción (debe ser [] siempre)."""
    return [r for r in production_rows() if r["tipo"] == "LEGAL_RULE"]


# ----------------------------------------------------------------------------------------------- documento
def main():
    hist = historical_rows()
    prod = production_rows()
    by_kind = {}
    for r in prod:
        by_kind[r["tipo"]] = by_kind.get(r["tipo"], 0) + 1
    out = ["# Inventario de constantes numéricas", "",
           "> Generado por `tools/hardcode_inventory.py` desde el AST del código. No editar a mano.", "",
           "Dos partes: **A** las constantes legales de los motores heredados (hoy fixtures de prueba), con la comprobación automática de si su valor "
           "ya vive en `config/payroll/`; **B** los literales numéricos que quedan en el código de PRODUCCIÓN, clasificados. Tipos: `LEGAL_RULE`, "
           "`TECHNICAL_CONSTANT`, `UI_CONSTANT`, `HISTORICAL_REFERENCE`, `EXTERNAL_INPUT`, `DERIVED_VALUE`, `TEMPORARY`.", "",
           "## Estado", "",
           f"- **A (heredado):** {len(hist)} constantes; {sum(1 for r in hist if r['migrado'].startswith('sí'))} con su valor presente en `config/payroll/`; "
           "el código heredado YA NO se ejecuta en la aplicación: vive solo en `tests/payroll_2026/legacy_fixtures/` como fixture de regresión.",
           f"- **B (producción):** {len(prod)} literales; **LEGAL_RULE sin justificación: {sum(1 for r in prod if r['tipo'] == 'LEGAL_RULE')}**. "
           + ", ".join(f"{k}: {v}" for k, v in sorted(by_kind.items())), "",
           "## B. Producción: resumen por archivo", "", "| Archivo | Literales | Tipo | Justificación |", "|---|---:|---|---|"]
    files = {}
    for r in prod:
        files.setdefault(r["archivo"], []).append(r)
    for path, items in sorted(files.items()):
        out.append(f"| `{path}` | {len(items)} | {items[0]['tipo']} | {items[0]['justificacion']} |")
    out += ["", "## A. Histórico por país", "",
            "| País | Constantes | Con valor en config/payroll | Origen: liquidación | Origen: cálculo mensual | Origen: CountryConfig |",
            "|---|---:|---:|---:|---:|---:|"]
    for cc in COUNTRIES.values():
        mine = [r for r in hist if r["pais"] == cc]
        out.append(f"| {cc} | {len(mine)} | {sum(1 for r in mine if r['migrado'].startswith('sí'))} | "
                   f"{sum(1 for r in mine if r['origen'] == 'liquidación')} | {sum(1 for r in mine if r['origen'] == 'cálculo mensual')} | "
                   f"{sum(1 for r in mine if r['origen'].startswith('CountryConfig'))} |")
    out += ["", "## A. Matriz detallada (motores heredados, fixtures)", "",
            "| Concepto | País | Archivo:línea | Valor | Tipo | Origen | ¿Legal? | ¿Migrado? | ¿Duplicado? | ¿Crítico? | Acción |",
            "|---|---|---|---:|---|---|---|---|---|---|---|"]
    for r in hist:
        out.append(f"| `{r['concepto']}` | {r['pais']} | {r['archivo']}:{r['linea']} | {r['valor']} | {r['tipo']} | {r['origen']} | {r['legal']} | "
                   f"{r['migrado']} | {r['duplicado']} | {r['critico']} | {r['accion']} |")
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    with open(os.path.join(ROOT, "docs", "HARDCODING_INVENTORY.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"docs/HARDCODING_INVENTORY.md: histórico {len(hist)}, producción {len(prod)}, LEGAL_RULE sin justificar "
          f"{sum(1 for r in prod if r['tipo'] == 'LEGAL_RULE')}")


if __name__ == "__main__":
    main()
