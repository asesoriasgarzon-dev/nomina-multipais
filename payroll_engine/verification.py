"""Estado de verificación de cada dato normativo, con las cuatro dimensiones SEPARADAS:

  source_verified          la fuente es oficial y consta autoridad, referencia legal, URL y fecha de verificación
  interpretation_verified  la interpretación fue validada (no basta con que la fuente sea oficial)
  implementation_verified  la regla está IMPLEMENTED (ejecutable de punta a punta; PARTIAL/NOT_IMPLEMENTED no cuentan)
  professional_validated   una PERSONA con criterio profesional la firmó (validated_by + validated_at). Este sistema nunca
                           lo marca por sí mismo.

Una fuente OFICIAL no implica una interpretación correcta ni una implementación completa."""


def flags(doc):
    source = doc.get("source") or {}
    verification = doc.get("verification") or {}
    professional = verification.get("professional_validation") == "VALIDATED" and bool(verification.get("validated_by")) \
        and bool(verification.get("validated_at"))
    return {
        "source_verified": source.get("status") == "OFFICIAL" and all(source.get(k) for k in
                                                                       ("authority", "legal_reference", "official_url", "verified_at")),
        "interpretation_verified": verification.get("interpretation_status") == "VALIDATED",
        "implementation_verified": doc.get("implementation_status") == "IMPLEMENTED",
        "professional_validated": professional,
    }


def registry(ruleset):
    """Registro de fuentes de las reglas (no de validación) de un país: una fila por regla, con los campos completos."""
    rows = []
    for rule in ruleset.rules:
        source = rule.get("source") or {}
        verification = rule.get("verification") or {}
        rows.append({
            "country": rule["country"], "jurisdiction": rule["jurisdiction"], "rule_code": rule["rule_id"],
            "effective_from": rule["effective"]["from"], "effective_to": rule["effective"].get("to"),
            "source_title": source.get("legal_reference"), "source_authority": source.get("authority"),
            "source_reference": source.get("legal_reference"), "official_url": source.get("official_url") or source.get("secondary_url"),
            "source_status": source.get("status"), "interpretation_status": verification.get("interpretation_status"),
            "implementation_status": rule.get("implementation_status"),
            "verified_by": source.get("verified_by") or ("lectura asistida por IA de la fuente (no es validación profesional)"
                                                         if source.get("verified_at") else None),
            "verification_date": source.get("verified_at"),
            "notes": " ".join(x for x in (rule.get("notes"), verification.get("note"), source.get("note")) if x) or None,
            "open_question": bool(verification.get("open_question")),
            **flags(rule),
        })
    return rows
