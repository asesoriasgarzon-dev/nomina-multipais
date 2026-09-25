"""Reference Resolver: resuelve unidades de referencia (SMMLV, UMA, RMV, SBU, UF...)
por país, jurisdicción, fecha y código. Nunca asume que una referencia existe en
todos los países: si no existe para esa fecha lanza MissingReferenceError; si hay
dos vigentes a la vez en la misma jurisdicción lanza ConflictingReferenceError."""

from dataclasses import dataclass
from decimal import Decimal

from .dates import in_effect
from .errors import ConflictingReferenceError, MissingReferenceError
from .money import D


@dataclass(frozen=True)
class ResolvedReference:
    code: str
    value: Decimal
    unit: str
    ref_id: str
    record: dict


class ReferenceResolver:
    def __init__(self, references, country, jurisdiction_chain, series=()):
        self.country = country
        self.chain = list(jurisdiction_chain)
        self._series = {}
        for serie in series:
            if serie["country"] == country:
                self._series.setdefault(serie["code"], []).append(serie)
        self._by_code = {}
        for ref in references:
            if ref["country"] != country:
                continue
            self._by_code.setdefault(ref["code"], []).append(ref)

    def resolve(self, code, on_date, jurisdiction=None):
        candidates = self._by_code.get(code, [])
        levels = [jurisdiction] if jurisdiction else list(reversed(self.chain))
        for level in levels:
            found = [r for r in candidates
                     if r["jurisdiction"] == level and in_effect(r["effective"], on_date)]
            if len(found) > 1:
                raise ConflictingReferenceError(
                    f"referencia {code} ({self.country}/{level}) tiene {len(found)} valores vigentes el {on_date}",
                    details=[r["ref_id"] for r in found])
            if found:
                ref = found[0]
                return ResolvedReference(code=code, value=D(ref["value"]), unit=ref.get("unit", ""),
                                         ref_id=ref["ref_id"], record=ref)
        serie_hit = self._resolve_series(code, on_date, levels)
        if serie_hit is not None:
            return serie_hit
        raise MissingReferenceError(
            f"no existe la referencia {code} para {self.country} en {levels} vigente el {on_date}")

    def _resolve_series(self, code, on_date, levels):
        """Serie temporal (índice diario/mensual, p. ej. UF): valor EXACTO de la fecha ancla. Si la
        serie existe pero no cubre la fecha, se falla con el hueco explícito (no se extrapola)."""
        series = [s for s in self._series.get(code, []) if s["jurisdiction"] in levels]
        if not series:
            return None
        key = on_date.isoformat()
        for serie in series:
            if serie["granularity"] == "MONTHLY":
                key_m = key[:7] + "-01"
                if key_m in serie["points"]:
                    return self._series_ref(serie, key_m)
            elif key in serie["points"]:
                return self._series_ref(serie, key)
        cover = "; ".join(f"{s['series_id']}: {s['coverage']['from']}..{s['coverage']['to']}" for s in series)
        raise MissingReferenceError(
            f"la serie {code} ({self.country}) no tiene valor para {on_date} (cobertura declarada: {cover}). "
            "No se extrapola ni se usa el último valor conocido.")

    @staticmethod
    def _series_ref(serie, point_key):
        ref_id = f"{serie['series_id']}@{point_key}"
        record = {"ref_id": ref_id, "series_id": serie["series_id"], "code": serie["code"], "date": point_key,
                  "value": serie["points"][point_key], "unit": serie.get("unit", ""), "source": serie["source"],
                  "verification": serie.get("verification"), "effective": {"from": point_key, "to": point_key}}
        return ResolvedReference(code=serie["code"], value=D(serie["points"][point_key]), unit=serie.get("unit", ""),
                                 ref_id=ref_id, record=record)

    def change_dates(self, code, start, end):
        """Fechas dentro de (start, end] en las que empieza una versión distinta de la referencia
        (en cualquier nivel de la cadena de jurisdicciones)."""
        from .dates import parse_schema_date
        points = set()
        for ref in self._by_code.get(code, []):
            if ref["jurisdiction"] not in self.chain:
                continue
            begins = parse_schema_date(ref["effective"]["from"], what="effective.from")
            if start < begins <= end:
                points.add(begins)
        return sorted(points)
