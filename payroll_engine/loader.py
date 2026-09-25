"""Carga y valida los paquetes normativos de config/payroll/<PAIS>/<AÑO>/.

Cada paquete contiene: manifest.json, references.json, concepts.json, bases.json,
rounding.json y uno o más rules*.json. Los datos entran solo por aquí y solo si
pasan el validador de esquema y las verificaciones de integridad cruzada."""

import glob
import hashlib
import json
import os

from .conditions import referenced_bases
from .dates import overlaps
from .errors import SchemaError
from .mechanisms import mechanism_bases
from .money import RoundingPolicy
from . import schema

DEFAULT_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "payroll")

_CACHE = {}


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_of(obj):
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


class RuleSetData:
    """Conjunto normativo inmutable de un país (uno o más años)."""

    def __init__(self, country, manifest, references, concepts, bases, rules, rounding, *,
                 check=True, check_conflicts=True, manifests=None, series=None):
        self.country = country
        self.series = list(series or [])
        self.manifest = manifest
        self.manifests = manifests or [manifest]
        self.references = list(references)
        self.concept_list = list(concepts)
        self.concepts = {c["concept"]: c for c in self.concept_list}
        self.bases = list(bases)
        self.rules = list(rules)
        self.rounding_data = rounding
        self.rounding = RoundingPolicy(rounding)
        if check:
            self.validate(check_conflicts=check_conflicts)

    # -- integridad ------------------------------------------------------------
    def validate(self, *, check_conflicts=True):
        issues = []
        for manifest in self.manifests:
            issues += schema.validate_manifest(manifest)
        issues += schema.validate_rounding(self.rounding_data, self.country)
        for ref in self.references:
            issues += schema.validate_reference(ref)
        for serie in self.series:
            issues += schema.validate_series(serie)
        for concept in self.concept_list:
            issues += schema.validate_concept(concept)
        for base in self.bases:
            issues += schema.validate_base(base)
        for rule in self.rules:
            issues += schema.validate_rule(rule)
        schema.raise_if(issues, f"datos normativos inválidos ({self.country})")

        issues = []
        base_codes = {b["base"] for b in self.bases}
        ids = set()
        for rule in self.rules:
            if rule["rule_id"] in ids:
                issues.append(f"rule_id duplicado: {rule['rule_id']}")
            ids.add(rule["rule_id"])
            if rule["country"] != self.country:
                issues.append(f"{rule['rule_id']}: country {rule['country']} no coincide con el paquete {self.country}")
            if rule["kind"] != "VALIDATION" and rule["concept"] not in self.concepts:
                issues.append(f"{rule['rule_id']}: el concepto {rule['concept']} no está definido en concepts.json")
            for code in mechanism_bases(rule.get("calculation", {}).get("params", {})) \
                    | referenced_bases(rule.get("conditions")) | referenced_bases(rule.get("exceptions", [])):
                if code not in base_codes:
                    issues.append(f"{rule['rule_id']}: referencia a la base inexistente {code}")
        for concept in self.concept_list:
            for tr in concept.get("treatments", []):
                if tr["base"] not in base_codes:
                    issues.append(f"concepto {concept['concept']}: tratamiento hacia base inexistente {tr['base']}")
        if check_conflicts:
            issues += self._conflicts()
        schema.raise_if(issues, f"integridad normativa fallida ({self.country})")

    def _conflicts(self):
        issues = []
        by_key = {}
        for rule in self.rules:
            by_key.setdefault((rule["rule_key"], rule["jurisdiction"]), []).append(rule)
        for (key, jurisdiction), group in by_key.items():
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    if overlaps(a["effective"], b["effective"]) and a["priority"] == b["priority"]:
                        issues.append(f"CONFLICTING_RULES {key}/{jurisdiction}: {a['rule_id']} y {b['rule_id']} "
                                      f"vigentes a la vez con la misma prioridad")
        refs = {}
        for ref in self.references:
            refs.setdefault((ref["code"], ref["jurisdiction"]), []).append(ref)
        for (code, jurisdiction), group in refs.items():
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    if overlaps(a["effective"], b["effective"]):
                        issues.append(f"CONFLICTING_REFERENCE {code}/{jurisdiction}: {a['ref_id']} y {b['ref_id']} se solapan")
        return issues

    # -- utilidades -------------------------------------------------------------
    def documents(self):
        return {
            "manifest": self.manifest, "references": self.references,
            "concepts": self.concept_list, "bases": self.bases,
            "rules": self.rules, "rounding": self.rounding_data,
            **({"series": self.series} if self.series else {}),
        }

    @property
    def content_hash(self):
        return sha256_of(self.documents())

    @property
    def ruleset_version(self):
        return self.manifest["ruleset_version"]

    @classmethod
    def from_documents(cls, docs, **kwargs):
        return cls(docs["manifest"]["country"], docs["manifest"], docs["references"], docs["concepts"],
                   docs["bases"], docs["rules"], docs["rounding"], series=docs.get("series"), **kwargs)


def load_country(country, root=DEFAULT_ROOT, *, use_cache=True):
    key = (os.path.abspath(root), country)
    if use_cache and key in _CACHE:
        return _CACHE[key]
    country_dir = os.path.join(root, country)
    if not os.path.isdir(country_dir):
        raise SchemaError(f"no existe paquete normativo para {country} en {root}")
    years = sorted(d for d in os.listdir(country_dir) if os.path.isdir(os.path.join(country_dir, d)))
    if not years:
        raise SchemaError(f"paquete normativo vacío para {country}")
    manifests, references, concepts, bases, rules, series = [], [], [], [], [], []
    rounding = None
    for year in years:
        pack = os.path.join(country_dir, year)
        manifests.append(_read(os.path.join(pack, "manifest.json")))
        rounding = _read(os.path.join(pack, "rounding.json"))
        # cada tipo de documento admite varios archivos (references*.json, rules_termination.json, ...)
        for target, prefix in ((references, "references"), (concepts, "concepts"), (bases, "bases"),
                               (rules, "rules"), (series, "series")):
            for path in sorted(glob.glob(os.path.join(pack, f"{prefix}*.json"))):
                target += _read(path)
    seen, merged_concepts = set(), []
    for concept in concepts:
        if concept["concept"] not in seen:
            seen.add(concept["concept"])
            merged_concepts.append(concept)
    data = RuleSetData(country, manifests[-1], references, merged_concepts, bases, rules, rounding,
                       manifests=manifests, series=series)
    if use_cache:
        _CACHE[key] = data
    return data


def available_countries(root=DEFAULT_ROOT):
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


def clear_cache():
    _CACHE.clear()
