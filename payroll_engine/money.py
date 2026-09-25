"""Aritmética monetaria con Decimal y política de redondeo explícita.

Nunca se usa float para dinero legal. Los números entran como texto, entero o
Decimal; un float se rechaza. Los cocientes exactos se expresan como razón
("15/360") y se evalúan con la precisión de cálculo declarada."""

from decimal import (
    Decimal, InvalidOperation, localcontext,
    ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_DOWN, ROUND_UP, ROUND_CEILING, ROUND_FLOOR,
)

from .errors import SchemaError

CALCULATION_PRECISION = 28

_MODES = {
    "ROUND_HALF_UP": ROUND_HALF_UP,
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
    "ROUND_DOWN": ROUND_DOWN,
    "ROUND_UP": ROUND_UP,
    "ROUND_CEILING": ROUND_CEILING,
    "ROUND_FLOOR": ROUND_FLOOR,
}


def D(value):
    """Convierte a Decimal. Rechaza float (evita errores binarios silenciosos)."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise TypeError("bool no es un valor monetario")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        text = value.strip()
        if "/" in text:
            num, den = text.split("/", 1)
            with localcontext() as ctx:
                ctx.prec = CALCULATION_PRECISION
                return Decimal(num.strip()) / Decimal(den.strip())
        try:
            return Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"número inválido: {value!r}") from exc
    raise TypeError(f"tipo no permitido para dinero: {type(value).__name__} (use texto, int o Decimal)")


def is_number_like(value):
    try:
        D(value)
        return not isinstance(value, bool)
    except (TypeError, ValueError):
        return False


def fmt(value):
    """Texto canónico y estable de un Decimal (sin notación científica)."""
    if not isinstance(value, Decimal):
        value = D(value)
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


class RoundingPolicy:
    """Política de redondeo declarada en datos (rounding.json de cada país)."""

    KINDS = ("currency", "tax", "contribution", "display", "none")

    def __init__(self, data):
        self.data = data
        self.calculation_precision = int(data.get("calculation_precision", CALCULATION_PRECISION))
        self._kinds = {}
        for kind in ("currency", "tax", "contribution", "display"):
            spec = data.get(kind) or data.get(f"{kind}_rounding")
            if spec is None:
                spec = {"precision": data.get("currency_precision", 2),
                        "mode": data.get("rounding_mode", "ROUND_HALF_UP")}
            self._kinds[kind] = self._parse(kind, spec)

    @staticmethod
    def _parse(kind, spec):
        mode = spec.get("mode", "ROUND_HALF_UP")
        if mode not in _MODES:
            raise SchemaError(f"modo de redondeo inválido en '{kind}': {mode}")
        precision = int(spec.get("precision", 2))
        if precision < 0:
            raise SchemaError(f"precisión de redondeo inválida en '{kind}'")
        return {"mode": mode, "precision": precision}

    def apply(self, value, kind):
        """Devuelve (valor_redondeado, registro) — el registro va al audit trail."""
        if kind == "none":
            return value, {"kind": "none", "applied": False, "before": fmt(value), "after": fmt(value)}
        spec = self._kinds.get(kind)
        if spec is None:
            raise SchemaError(f"tipo de redondeo desconocido: {kind}")
        quantum = Decimal(1).scaleb(-spec["precision"])
        rounded = value.quantize(quantum, rounding=_MODES[spec["mode"]])
        return rounded, {
            "kind": kind, "applied": True, "mode": spec["mode"],
            "precision": spec["precision"], "before": fmt(value), "after": fmt(rounded),
        }
