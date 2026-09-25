"""Evaluador de condiciones DECLARATIVAS. No es un lenguaje de fórmulas: solo
comparaciones y combinaciones booleanas sobre operandos tipados. Todo lo que
requiere aritmética, estado o iteración vive en mecanismos de código (mechanisms.py).

Forma:
  {"all": [c, ...]} | {"any": [c, ...]} | {"not": c}
  {"left": operando, "op": "<=", "right": operando}
Operadores: < <= > >= == != in not_in
"""

from decimal import Decimal

from .errors import SchemaError
from .money import D, fmt, is_number_like

OPERATORS = ("<", "<=", ">", ">=", "==", "!=", "in", "not_in")


def _coerce(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, Decimal)):
        return D(value)
    if isinstance(value, str) and is_number_like(value):
        return D(value)
    return value


def _compare(left, op, right):
    if op in ("in", "not_in"):
        members = right if isinstance(right, (list, tuple)) else [right]
        present = _coerce(left) in [_coerce(m) for m in members]
        return present if op == "in" else not present
    left, right = _coerce(left), _coerce(right)
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    if isinstance(left, str) or isinstance(right, str):
        raise TypeError(f"no se puede comparar texto con '{op}': {left!r} {right!r}")
    return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right}[op]


def evaluate(cond, ctx):
    """Devuelve (bool, registro). El registro alimenta el audit trail."""
    if cond in (None, {}):
        return True, {"type": "always", "result": True}
    if "all" in cond:
        parts = [evaluate(c, ctx) for c in cond["all"]]
        result = all(p[0] for p in parts)
        return result, {"type": "all", "result": result, "parts": [p[1] for p in parts]}
    if "any" in cond:
        parts = [evaluate(c, ctx) for c in cond["any"]]
        result = any(p[0] for p in parts)
        return result, {"type": "any", "result": result, "parts": [p[1] for p in parts]}
    if "not" in cond:
        inner, rec = evaluate(cond["not"], ctx)
        return (not inner), {"type": "not", "result": not inner, "part": rec}
    if "left" in cond and "op" in cond and "right" in cond:
        if cond["op"] not in OPERATORS:
            raise SchemaError(f"operador de condición no permitido: {cond['op']}")
        ctx.capture()
        left = _operand_or_list(cond["left"], ctx)
        right = _operand_or_list(cond["right"], ctx)
        result = _compare(left, cond["op"], right)
        return result, {
            "type": "compare", "op": cond["op"], "result": result,
            "left": _show(left), "right": _show(right), "operands": ctx.capture(),
        }
    raise SchemaError(f"condición mal formada: {cond!r}")


def _operand_or_list(spec, ctx):
    if isinstance(spec, list):
        return [ctx.operand(s) if isinstance(s, dict) else s for s in spec]
    return ctx.operand(spec)


def _show(value):
    if isinstance(value, Decimal):
        return fmt(value)
    if isinstance(value, list):
        return [_show(v) for v in value]
    return value


def _scan(node, key, found):
    """Busca operandos de un solo campo ({"base": X} / {"line": X}) en una estructura."""
    if isinstance(node, dict):
        if len(node) == 1 and key in node and isinstance(node[key], str):
            found.add(node[key])
        for value in node.values():
            _scan(value, key, found)
    elif isinstance(node, list):
        for item in node:
            _scan(item, key, found)


def referenced_bases(node):
    """Bases mencionadas como operando (para el grafo de dependencias)."""
    found = set()
    _scan(node, "base", found)
    return found


def referenced_lines(node):
    found = set()
    _scan(node, "line", found)
    return found


def applies_to(spec, payload):
    """Filtro simple por atributo: {"employment.salary_type": ["ORDINARY"], ...}.
    Solo restringe cuando el país realmente distingue ese atributo."""
    if not spec:
        return True
    for path, allowed in spec.items():
        node = payload
        for part in path.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if node not in allowed:
            return False
    return True


def referenced_reference_codes(node, found=None):
    """Códigos de referencia ({"reference": {"code": X}}) usados en una estructura."""
    found = set() if found is None else found
    if isinstance(node, dict):
        ref = node.get("reference")
        if isinstance(ref, dict) and isinstance(ref.get("code"), str):
            found.add(ref["code"])
        for value in node.values():
            referenced_reference_codes(value, found)
    elif isinstance(node, list):
        for item in node:
            referenced_reference_codes(item, found)
    return found
