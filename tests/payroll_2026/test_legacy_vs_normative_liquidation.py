"""Liquidación: LEGACY_RESULT vs NORMATIVE_RESULT vs EXPECTED_LEGAL_RESULT. Los defectos jurídicos conocidos del código heredado
(P0 de Perú y Argentina, P1 de Colombia) NO se conservan: el motor normativo debe coincidir con el resultado esperado por la norma
y diferir del heredado. Que el normativo iguale al heredado nunca se usa como prueba de corrección."""

from decimal import Decimal

import pytest

from .divergences import (ROWS, SCENARIOS, expected_ar, expected_co, expected_pe, liquidate, line_amount, q)

D = Decimal


# ---------------------------------------------------------------------------------------------------- Perú (P0)
def test_pe_el_heredado_usaba_la_misma_formula_para_cts_y_gratificacion_y_el_normativo_no():
    legacy, normative = liquidate("PE")
    assert legacy["conceptos"]["cesantias"] == legacy["conceptos"]["prima_servicios"]             # LEGACY: CTS == gratificación (P0)
    assert q(legacy["conceptos"]["cesantias"]) == q(D(3000) * 201 / 360)                          # 1-ene .. 20-jul, año calendario/360
    expected = expected_pe()
    assert line_amount(normative, "PE_CTS_TRUNCA") == expected["cts"]                             # EXPECTED_LEGAL_RESULT
    assert line_amount(normative, "PE_GRATIFICACION_TRUNCA") == expected["gratificacion"]
    assert line_amount(normative, "PE_CTS_TRUNCA") != q(legacy["conceptos"]["cesantias"])
    assert line_amount(normative, "PE_GRATIFICACION_TRUNCA") != q(legacy["conceptos"]["prima_servicios"])


# ---------------------------------------------------------------------------------------------------- Argentina (P0)
def test_ar_el_heredado_contaba_el_sac_desde_el_1_de_enero_y_el_normativo_por_semestre():
    legacy, normative = liquidate("AR")
    assert q(legacy["conceptos"]["prima_servicios"]) == q(D(1_000_000) / 2 * 258 / 180)           # LEGACY: 1-ene..15-sep (258 días)/180
    assert line_amount(normative, "AR_SAC_PROPORCIONAL") == expected_ar()["sac"]                  # EXPECTED: 2,5 meses/12
    assert line_amount(normative, "AR_SAC_PROPORCIONAL") < q(legacy["conceptos"]["prima_servicios"])


def test_ar_el_normativo_agrega_preaviso_integracion_y_vacaciones_proporcionales_que_el_heredado_no_tenia():
    legacy, normative = liquidate("AR")
    assert line_amount(normative, "AR_INTEGRACION_MES_DESPIDO") == q(D(1_000_000) / 30 * 15)
    assert line_amount(normative, "AR_VACACIONES_NO_GOZADAS") > 0 and legacy["conceptos"]["vacaciones_pendientes"] == 0


# ---------------------------------------------------------------------------------------------------- Colombia (P1)
def test_co_el_heredado_excluia_el_auxilio_de_transporte_de_cesantias_y_prima():
    legacy, normative = liquidate("CO")
    assert q(legacy["conceptos"]["cesantias"]) == q(D(2_000_000) * 255 / 360)                     # LEGACY: sin auxilio de transporte en la base
    expected = expected_co()
    assert line_amount(normative, "CO_CESANTIAS") == expected["cesantias"]
    assert line_amount(normative, "CO_CESANTIAS_INTERESES") == expected["intereses"]
    assert line_amount(normative, "CO_PRIMA") == expected["prima"]
    assert line_amount(normative, "CO_CESANTIAS") > q(legacy["conceptos"]["cesantias"])


def test_co_la_indemnizacion_del_art_64_coincide_con_el_heredado_y_con_la_norma():
    """Coincidencia SOLO porque ambos aplican el texto del art. 64 (30 días + 20 por año subsiguiente, salario < 10 SMMLV); se verifica
    contra el cálculo independiente, no contra el heredado."""
    legacy, normative = liquidate("CO")
    expected = q(D(2_000_000) / 30 * D(82))                                                        # 3 años 7 meses 6 días -> 30 + 20 × 2,6
    assert line_amount(normative, "CO_INDEMNIZACION_INDEFINIDO_MENOR_10") == expected
    assert q(legacy["indemnizacion"]) == expected


# ---------------------------------------------------------------------------------------------------- otros países
def test_cl_el_normativo_incluye_feriado_y_topa_la_indemnizacion_a_330_dias():
    legacy, normative = liquidate("CL")
    assert legacy["conceptos"]["vacaciones_pendientes"] == 0
    assert line_amount(normative, "CL_FERIADO_PROPORCIONAL") > 0
    assert line_amount(normative, "CL_INDEMNIZACION_ANOS_SERVICIO") == q(D(2_000_000) / 30 * 330)
    assert normative["indemnizacion"] == float(q(D(2_000_000) / 30 * 330) + D(2_000_000))         # + aviso previo (no se dio)


def test_mx_el_normativo_agrega_los_conceptos_de_la_lft_que_el_heredado_no_calculaba():
    legacy, normative = liquidate("MX")
    for concept in ("MX_VACACIONES", "MX_PRIMA_VACACIONAL", "MX_INDEMNIZACION_3_MESES", "MX_INDEMNIZACION_20_DIAS", "MX_PRIMA_ANTIGUEDAD_GENERAL"):
        assert line_amount(normative, concept) > 0
    assert normative["total_liquidacion"] > legacy["total_liquidacion"]


def test_br_el_normativo_calcula_los_conceptos_de_la_clt_con_sus_reglas_de_fraccion():
    legacy, normative = liquidate("BR")
    assert line_amount(normative, "BR_13O_PROPORCIONAL") == q(D(5000) * 9 / 12)                    # enero..septiembre (20 días en sep.)
    assert line_amount(normative, "BR_AVISO_PREVIO_INDENIZADO") == q(D(5000) / 30 * 45)
    assert normative["total_liquidacion"] != legacy["total_liquidacion"]


def test_ec_el_normativo_aplica_el_articulo_188_y_la_bonificacion_del_185():
    legacy, normative = liquidate("EC")
    assert line_amount(normative, "EC_INDEMNIZACION_DESPIDO_INTEMPESTIVO") == D("6000.00")          # 5 años y fracción -> 6 meses
    assert line_amount(normative, "EC_BONIFICACION_DESAHUCIO") > 0


# ---------------------------------------------------------------------------------------------------- documentación de diferencias
@pytest.mark.parametrize("cc", sorted(SCENARIOS))
def test_cada_pais_tiene_una_diferencia_documentada_con_razon_y_fuente(cc):
    rows = [r for r in ROWS if r[0] == cc]
    assert rows and all(r[2] and r[3] for r in rows)


def test_la_liquidacion_de_produccion_ya_no_ejecuta_codigo_heredado():
    import inspect
    from countries import REGISTRY
    for cc in SCENARIOS:
        source = inspect.getsource(type(REGISTRY[cc]["engine"]).liquidar)
        assert "termination_payload" in source
