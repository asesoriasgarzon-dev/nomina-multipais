"""Escenarios SINTÉTICOS que obligan al núcleo a manejar lo que un solo país no ejercita:
demuestran que el núcleo no quedó diseñado solo para Colombia. Los valores son ficticios."""

from decimal import Decimal

import pytest

from payroll_engine.errors import (ConflictingRulesError, CycleError, IncompleteRunError, InputValidationError,
                                   MissingDependencyError, MissingReferenceError, MissingRuleError, SchemaError,
                                   StraddleError)
from payroll_engine.money import D, RoundingPolicy
from payroll_engine.run import PayrollEngine
from tests.payroll_2026 import synthetic as S

ENGINE = PayrollEngine()


def run(payload, **mods):
    return ENGINE.run(payload, ruleset=S.zz_ruleset(**mods) if mods else S.zz_ruleset())


def policy(name):
    def mutate(docs):
        for rule in docs["rules"]:
            if rule["rule_key"] == "ZZ.SS_EMP":
                rule["straddle_policy"] = name
    return mutate


# ------------------------------------------------------------------ Caso A
def test_caso_a_dos_jurisdicciones_con_distinta_tasa():
    a = run(S.payload(salary="3000", bonus="500", chain=("NATIONAL", "STATE_A")))
    b = run(S.payload(salary="3000", bonus="500", chain=("NATIONAL", "STATE_B")))
    assert a.amount("STATE_LEVY") == Decimal("70.00")       # 3500 × 2%
    assert b.amount("STATE_LEVY") == Decimal("105.00")      # 3500 × 3%
    only_national = run(S.payload(salary="3000", chain=("NATIONAL",)))
    assert only_national.line("STATE_LEVY") is None          # ninguna capa estatal en la cadena


# ------------------------------------------------------------------ Caso B
def test_caso_b_la_regla_cambia_a_mitad_de_periodo_split_por_dias():
    r = run(S.payload(period=("2026-06-16", "2026-07-15")), mutate=policy("SPLIT_BY_DAYS"))
    # 15 días con 4% y 15 días con 5% sobre 3000
    assert r.amount("SS_EMP") == Decimal("135.00")
    line = r.trace["lines"][[l["concept"] for l in r.trace["lines"]].index("SS_EMP")]
    assert [s["rule_id"] for s in line["segments"]] == ["ZZ.SS_EMP.1", "ZZ.SS_EMP.2"]


def test_caso_b_politica_error_bloquea_en_vez_de_inventar():
    with pytest.raises(StraddleError):
        run(S.payload(period=("2026-06-16", "2026-07-15")), mutate=policy("ERROR"))


def test_caso_b_use_anchor_usa_la_fecha_ancla_y_lo_advierte():
    r = run(S.payload(period=("2026-06-16", "2026-07-15")), mutate=policy("USE_ANCHOR"))
    assert r.amount("SS_EMP") == Decimal("150.00")           # 5% (vigente en period_end)
    assert any(w["type"] == "CHANGE_WITHIN_PERIOD" for w in r.warnings)


@pytest.mark.parametrize("period,expected", [
    (("2026-06-01", "2026-06-30"), "120.00"),   # un día antes del cambio: 4%
    (("2026-07-01", "2026-07-31"), "150.00"),   # exactamente en la fecha de cambio: 5%
    (("2026-08-01", "2026-08-31"), "150.00"),   # un día después: 5%
])
def test_cambio_de_vigencia_frontera_sin_tocar_codigo(period, expected):
    assert run(S.payload(period=period)).amount("SS_EMP") == Decimal(expected)


def test_cambio_de_referencia_dentro_del_periodo_se_detecta():
    def mutate(docs):
        docs["references"][0]["effective"]["to"] = "2026-06-30"
        docs["references"].append(S.reference("ZZ.MIN.NAT2", "MIN_WAGE", "1200", start="2026-07-01"))
        for rule in docs["rules"]:
            if rule["rule_key"] == "ZZ.TRANSPORT":
                rule["straddle_policy"] = "ERROR"
    with pytest.raises(StraddleError):
        run(S.payload(salary="1500", period=("2026-06-16", "2026-07-15")), mutate=mutate)


# ------------------------------------------------------------------ Caso C
def test_caso_c_concepto_entra_a_seguridad_social_pero_no_a_impuesto():
    r = run(S.payload(salary="3000", bonus="500"))
    bases = {b["base"]: b for b in r.trace["bases"]}
    assert bases["SS_BASE"]["raw_sum"] == "3500"
    excluded = [e["concept"] for e in bases["TAX_BASE"]["exclusions"]]
    assert "BONUS" in excluded
    assert r.amount("TAX") == Decimal("282.50")              # (3000 − 175) × 10%, sin el bono


# ------------------------------------------------------------------ Caso D
def test_caso_d_una_base_depende_de_otra_y_el_orden_es_correcto():
    r = run(S.payload(salary="3000", bonus="500"))
    order = r.trace["execution_order"]
    assert order.index("rule:ZZ.SS_EMP@NATIONAL") < order.index("base:TAX_BASE") < order.index("rule:ZZ.TAX@NATIONAL")
    tax_base = next(b for b in r.trace["bases"] if b["base"] == "TAX_BASE")
    assert any(c["mode"] == "SUBTRACT" and c["concept"] == "SS_EMP" for c in tax_base["contributions"])


def test_el_orden_de_ejecucion_es_determinista():
    orders = [run(S.payload(salary="3000")).trace["execution_order"] for _ in range(3)]
    assert orders[0] == orders[1] == orders[2]


def test_ciclo_de_dependencias_se_detecta():
    def mutate(docs):
        docs["concepts"].append(S.concept("LOOP", "EMPLOYEE_DEDUCTION", [{"base": "SS_BASE", "mode": "INCLUDE"}]))
        docs["rules"].append(S.rule("ZZ.LOOP.1", "ZZ.LOOP", "LOOP", "rate_on_base", {"base": "SS_BASE", "rate": "0.01"}))
    with pytest.raises(CycleError):
        run(S.payload(), mutate=mutate)


def test_dependencia_faltante_base_inexistente():
    def mutate(docs):
        docs["concepts"].append(S.concept("GHOSTC", "EMPLOYEE_DEDUCTION"))
        docs["rules"].append(S.rule("ZZ.GHOST.1", "ZZ.GHOST", "GHOSTC", "rate_on_base", {"base": "GHOST", "rate": "0.01"}))
    with pytest.raises(SchemaError):                          # el validador la rechaza al cargar
        S.zz_ruleset(mutate)
    with pytest.raises(MissingDependencyError):               # y el motor la rechaza si se salta el validador
        ENGINE.run(S.payload(), ruleset=S.zz_ruleset(mutate, check=False))


def test_linea_que_ninguna_regla_produce():
    def mutate(docs):
        docs["concepts"].append(S.concept("NEEDSC", "EMPLOYEE_DEDUCTION"))
        docs["rules"].append(S.rule("ZZ.NEEDS.1", "ZZ.NEEDS", "NEEDSC", "rate_on_base", {"base": "SS_BASE", "rate": "0.01"},
                                    conditions={"left": {"line": "NOBODY"}, "op": ">", "right": {"value": "0"}}))
    with pytest.raises(MissingDependencyError):
        ENGINE.run(S.payload(), ruleset=S.zz_ruleset(mutate, check=False))


# ------------------------------------------------------------------ Caso E
def test_caso_e_una_jurisdiccion_tiene_topes_distintos():
    nat = run(S.payload(salary="9000", chain=("NATIONAL",)))
    state = run(S.payload(salary="9000", chain=("NATIONAL", "STATE_A")))
    assert next(b for b in nat.trace["bases"] if b["base"] == "SS_BASE")["value"] == "5000"
    assert next(b for b in state.trace["bases"] if b["base"] == "SS_BASE")["value"] == "8000"
    assert nat.amount("SS_EMP") == Decimal("250.00") and state.amount("SS_EMP") == Decimal("400.00")
    assert next(b for b in nat.trace["bases"] if b["base"] == "SS_BASE")["cap_applied"] is True


@pytest.mark.parametrize("salary,expected", [("4999", "4999"), ("5000", "5000"), ("5001", "5000")])
def test_tope_frontera_menos_uno_igual_mas_uno(salary, expected):
    r = run(S.payload(salary=salary))
    assert next(b for b in r.trace["bases"] if b["base"] == "SS_BASE")["value"] == expected


# ------------------------------------------------------------------ Caso F
def test_caso_f_una_regla_no_aplica_y_queda_registrado_por_que():
    r = run(S.payload(salary="3000"))
    assert r.line("TRANSPORT") is None
    ev = [e for e in r.trace["evaluations"] if e["rule_id"] == "ZZ.TRANSPORT.1"][0]
    assert ev["outcome"] == "NOT_APPLICABLE" and ev["conditions"]["result"] is False
    assert ev["conditions"]["left"] == "3000" and ev["conditions"]["right"] == "2000"


@pytest.mark.parametrize("salary,eligible", [("1999", True), ("2000", True), ("2001", False)])
def test_umbral_de_elegibilidad_frontera(salary, eligible):
    assert (run(S.payload(salary=salary)).line("TRANSPORT") is not None) is eligible


# ------------------------------------------------------------------ Caso G
def test_caso_g_regla_not_implemented_no_se_disimula():
    r = run(S.payload())
    assert r.status == "INCOMPLETE"
    assert r.pending_rules[0]["rule_id"] == "ZZ.WITHHOLDING.1"
    assert any(w["type"] == "RULE_NOT_IMPLEMENTED" for w in r.warnings)
    assert r.line("INCOME_WITHHOLDING") is None               # no se inventa un valor


def test_caso_g_modo_estricto_bloquea():
    with pytest.raises(IncompleteRunError):
        ENGINE.run(S.payload(), ruleset=S.zz_ruleset(), strict=True)


# ------------------------------------------------------------------ conflictos y faltantes
def test_reglas_en_conflicto_mismo_concepto_misma_prioridad():
    def mutate(docs):
        docs["rules"].append(S.rule("ZZ.TAX.DUP", "ZZ.TAX_DUP", "TAX", "rate_on_base", {"base": "TAX_BASE", "rate": "0.20"}))
    with pytest.raises(ConflictingRulesError):
        ENGINE.run(S.payload(), ruleset=S.zz_ruleset(mutate))


def test_la_prioridad_resuelve_y_deja_constancia_de_la_descartada():
    def mutate(docs):
        docs["rules"].append(S.rule("ZZ.TAX.SPECIAL", "ZZ.TAX_SPECIAL", "TAX", "rate_on_base",
                                    {"base": "TAX_BASE", "rate": "0.20"}, priority=200))
    r = run(S.payload(salary="3000"), mutate=mutate)
    assert r.amount("TAX") == Decimal("570.00")               # 20% × (3000 − 150)
    assert {"rule_id": "ZZ.TAX.1", "reason": "SUPERADA_POR_PRIORIDAD", "selected": "ZZ.TAX.SPECIAL"} in r.trace["discarded_rules"]


def test_dos_versiones_vigentes_a_la_vez_misma_prioridad_conflicto():
    def mutate(docs):
        docs["rules"].append(S.rule("ZZ.SS_EMP.3", "ZZ.SS_EMP", "SS_EMP", "rate_on_base", {"base": "SS_BASE", "rate": "0.09"},
                                    start="2026-07-01", version="3"))
    with pytest.raises(SchemaError):                          # el validador lo rechaza al publicar
        S.zz_ruleset(mutate)
    with pytest.raises(ConflictingRulesError):                # y el resolvedor si se salta el validador
        ENGINE.run(S.payload(), ruleset=S.zz_ruleset(mutate, check_conflicts=False))


def test_referencia_faltante():
    def mutate(docs):
        docs["concepts"].append(S.concept("NEEDREFC", "EMPLOYEE_DEDUCTION"))
        docs["rules"].append(S.rule("ZZ.NEEDREF.1", "ZZ.NEEDREF", "NEEDREFC", "fixed_amount_prorated",
                                    {"amount": {"reference": {"code": "NOPE"}}}))
    with pytest.raises(MissingReferenceError):
        ENGINE.run(S.payload(), ruleset=S.zz_ruleset(mutate))


def test_referencias_en_conflicto():
    def mutate(docs):
        docs["references"].append(S.reference("ZZ.MIN.DUP", "MIN_WAGE", "999"))
    with pytest.raises(SchemaError):
        S.zz_ruleset(mutate)


def test_regla_faltante_sin_reglas_vigentes_en_la_fecha():
    with pytest.raises(MissingRuleError):
        run(S.payload(period=("2025-12-01", "2025-12-31")))


def test_pais_sin_datos_normativos():
    from payroll_engine.errors import CapabilityError
    with pytest.raises(CapabilityError):
        ENGINE.run({"country": "XX", "period": {"start": "2026-01-01", "end": "2026-01-31"}})


# ------------------------------------------------------------------ entradas
@pytest.mark.parametrize("mod", [
    {"salary": "-1"}, {"salary": "abc"}, {"salary": 3000.5},
])
def test_entradas_invalidas_se_bloquean(mod):
    with pytest.raises(InputValidationError):
        run(S.payload(**mod))


def test_valores_nulos_negativos_y_float_en_montos():
    for bad in ({"BONUS": None}, {"BONUS": "-5"}, {"BONUS": 1.5}, {"BONUS": "x"}):
        p = S.payload()
        p["amounts"] = bad
        with pytest.raises(InputValidationError):
            run(p)


def test_dato_de_entrada_faltante():
    p = S.payload()
    del p["employment"]["monthly_salary"]
    with pytest.raises(InputValidationError):
        run(p)


def test_cero_y_salario_muy_alto_y_decimal():
    zero = run(S.payload(salary="0"))
    assert zero.amount("SALARY") == Decimal("0.00") and zero.amount("SS_EMP") == Decimal("0.00")
    assert zero.result["totals"]["neto_pagado"] == zero.amount("TRANSPORT")     # solo el auxilio fijo elegible
    huge = run(S.payload(salary="999999999999"))
    assert next(b for b in huge.trace["bases"] if b["base"] == "SS_BASE")["value"] == "5000"
    dec = run(S.payload(salary="1234.567"))
    assert dec.amount("SALARY") == Decimal("1234.57")


def test_tipo_de_corrida_invalido():
    with pytest.raises(InputValidationError):
        run(S.payload(run_type="OTRO"))


# ------------------------------------------------------------------ Decimal y redondeo
def test_el_dinero_nunca_es_float():
    with pytest.raises(TypeError):
        D(1.5)
    r = run(S.payload(salary="3000", bonus="500"))
    for line in r.result["lines"]:
        assert isinstance(line["amount"], Decimal)
    assert all(isinstance(v, Decimal) for v in r.result["totals"].values())


def test_el_redondeo_queda_registrado_en_la_auditoria():
    r = run(S.payload(salary="1234.567"))
    rec = next(l for l in r.trace["lines"] if l["concept"] == "SALARY")["rounding"]
    assert rec["applied"] and rec["mode"] == "ROUND_HALF_UP" and rec["before"] == "1234.567" and rec["after"] == "1234.57"


def test_las_lineas_suman_exactamente_los_totales():
    r = run(S.payload(salary="1234.567", bonus="0.005"))
    lines = r.result["lines"]
    dev = sum((l["amount"] for l in lines if l["role"] == "EARNING"), Decimal(0))
    ded = sum((l["amount"] for l in lines if l["role"] == "EMPLOYEE_DEDUCTION"), Decimal(0))
    assert dev == r.result["totals"]["total_devengado"] and dev - ded == r.result["totals"]["neto_pagado"]


def test_politica_de_redondeo_explicita_y_configurable():
    policy_half_even = RoundingPolicy({"currency": {"precision": 0, "mode": "ROUND_HALF_EVEN"},
                                       "tax": {"precision": 0, "mode": "ROUND_DOWN"},
                                       "contribution": {"precision": 2, "mode": "ROUND_HALF_UP"},
                                       "display": {"precision": 2, "mode": "ROUND_HALF_UP"}})
    assert policy_half_even.apply(Decimal("2.5"), "currency")[0] == Decimal("2")
    assert policy_half_even.apply(Decimal("3.5"), "currency")[0] == Decimal("4")
    assert policy_half_even.apply(Decimal("9.99"), "tax")[0] == Decimal("9")
    with pytest.raises(SchemaError):
        RoundingPolicy({"currency": {"precision": 2, "mode": "INVENTADO"}})


# ------------------------------------------------------------------ snapshots y reproducibilidad
def test_snapshot_reproduce_aunque_cambie_la_regla_despues():
    from payroll_engine.run import reproduce
    original = S.zz_ruleset()
    r = ENGINE.run(S.payload(salary="3000", bonus="500", chain=("NATIONAL", "STATE_A")), ruleset=original)
    stored, docs = r.to_dict(), r._documents
    # una regla posterior cambia la tasa del SS: la corrida histórica NO debe cambiar
    def mutate(d):
        for rule in d["rules"]:
            if rule["rule_id"] == "ZZ.SS_EMP.2":
                rule["calculation"]["params"]["rate"] = "0.09"
    changed = ENGINE.run(S.payload(salary="3000", bonus="500", chain=("NATIONAL", "STATE_A")), ruleset=S.zz_ruleset(mutate))
    assert changed.result_hash != r.result_hash
    again = reproduce(stored, docs)
    assert again["same"] is True and again["recomputed_hash"] == r.result_hash


def test_el_snapshot_normativo_identifica_las_reglas_usadas():
    r = run(S.payload())
    used = {x["rule_id"] for x in r.normative_snapshot["rules_used"]}
    assert "ZZ.SS_EMP.2" in used and "ZZ.SS_EMP.1" not in used
    assert r.normative_snapshot["content_hash"] == S.zz_ruleset().content_hash
    assert r.engine_version and r.input_snapshot["hash"]


def test_el_hash_del_resultado_no_depende_del_momento_de_calculo():
    from datetime import datetime, timezone
    a = ENGINE.run(S.payload(), ruleset=S.zz_ruleset(), calculation_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    b = ENGINE.run(S.payload(), ruleset=S.zz_ruleset(), calculation_timestamp=datetime(2030, 1, 1, tzinfo=timezone.utc))
    assert a.result_hash == b.result_hash and a.calculation_timestamp != b.calculation_timestamp


# ------------------------------------------------------------------ anclas de fecha
@pytest.mark.parametrize("anchor,key", [("pay_date", "pay_date"), ("accrual_date", "accrual_date"),
                                        ("event_date", "event_date"), ("termination_date", "termination_date")])
def test_fecha_ancla_configurable_por_regla(anchor, key):
    def mutate(docs):
        for rule in docs["rules"]:
            if rule["rule_key"] == "ZZ.SS_EMP":
                rule["anchor"] = anchor
    p = S.payload(period=("2026-06-01", "2026-07-31"))
    p[key] = "2026-06-20"
    assert run(p, mutate=mutate).amount("SS_EMP") == Decimal("120.00")     # 4% vigente el 20-jun
    p[key] = "2026-07-20"
    assert run(p, mutate=mutate).amount("SS_EMP") == Decimal("150.00")     # 5% vigente el 20-jul


def test_fecha_ancla_ausente_se_rechaza():
    from payroll_engine.errors import MissingAnchorDateError
    def mutate(docs):
        for rule in docs["rules"]:
            if rule["rule_key"] == "ZZ.SS_EMP":
                rule["anchor"] = "pay_date"
    with pytest.raises(MissingAnchorDateError):
        run(S.payload(), mutate=mutate)


def test_ancla_period_start_y_period_end():
    def mutate(docs):
        for rule in docs["rules"]:
            if rule["rule_key"] == "ZZ.SS_EMP":
                rule["anchor"] = "period_start"
    assert run(S.payload(period=("2026-06-30", "2026-07-31")), mutate=mutate).amount("SS_EMP") == Decimal("120.00")


# ------------------------------------------------------------------ persistencia inmutable
def test_las_corridas_persistidas_son_inmutables(tmp_path, monkeypatch):
    import sqlite3
    import models
    monkeypatch.setattr(models, "DB_PATH", str(tmp_path / "t.db"))
    models.init_db()
    r = ENGINE.run(S.payload(), ruleset=S.zz_ruleset())
    rid = models.guardar_payroll_run(r.to_dict(), r._documents, nomina_id=None, es_demo=True)
    stored = models.obtener_payroll_run(rid)
    assert stored["result_hash"] == r.result_hash and stored["es_demo"] is True
    conn = models.get_db()
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE payroll_runs SET status = 'X' WHERE id = ?", (rid,))
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM payroll_runs WHERE id = ?", (rid,))
    conn.close()
    docs = models.obtener_snapshot_normativo(stored["normative_snapshot"]["content_hash"])
    assert docs["manifest"]["country"] == "ZZ"


# ------------------------------------------------------------------ tipos de corrida
def test_simulacion_es_una_corrida_valida_y_queda_marcada():
    r = run(S.payload(run_type="SIMULATION"))
    assert r.run_type == "SIMULATION" and r.result["lines"]


def test_terminacion_no_implementada_se_bloquea_y_no_se_simula():
    from payroll_engine.errors import CapabilityError
    with pytest.raises(CapabilityError) as err:
        run(S.payload(run_type="TERMINATION"))
    assert "no está implementada" in str(err.value)


@pytest.mark.parametrize("run_type", ["ADJUSTMENT", "HISTORICAL_RECALCULATION"])
def test_ajuste_y_recalculo_historico_exigen_la_corrida_original(run_type):
    with pytest.raises(InputValidationError):
        run(S.payload(run_type=run_type))
    r = run(S.payload(run_type=run_type, original_run_uid="abc-123"))
    assert r.original_run_uid == "abc-123" and r.run_type == run_type
