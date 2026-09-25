"""COMPARACIÓN: motor heredado (fixture) vs motor normativo (reglas versionadas).

IMPORTANTE: coincidir con el heredado NO prueba que el resultado sea jurídicamente correcto (el heredado no es la
verdad). Esta comparación solo detecta cambios NO intencionales en la migración. La corrección jurídica se prueba
con cálculos esperados independientes (tests de cada país) y las diferencias intencionales se declaran aquí con su
causa y su fuente; el resumen legible está en docs/LEGACY_VS_NORMATIVE.md."""

from decimal import Decimal

import pytest

from countries import normative_engines as N
from countries.colombia_normative import ColombiaNormativeEngine

from .legacy_fixtures.argentina import ArgentinaConfig, ArgentinaPayrollEngine
from .legacy_fixtures.brasil import BrasilConfig, BrasilPayrollEngine
from .legacy_fixtures.chile import ChileConfig, ChilePayrollEngine
from .legacy_fixtures.colombia import ColombiaConfig, ColombiaPayrollEngine
from .legacy_fixtures.ecuador import EcuadorConfig, EcuadorPayrollEngine
from .legacy_fixtures.mexico import MexicoConfig, MexicoPayrollEngine
from .legacy_fixtures.peru import PeruConfig, PeruPayrollEngine

LEGACY_CONFIG = {"CO": ColombiaConfig, "MX": MexicoConfig, "PE": PeruConfig, "CL": ChileConfig, "BR": BrasilConfig,
                 "AR": ArgentinaConfig, "EC": EcuadorConfig}

SMMLV = Decimal("1750905")
SECTIONS = ("devengado", "deducciones", "aportes_patronales", "provisiones")


def both(cc, new_cls, old_cls, salary, nov, periodo="2026-09"):
    cfg = LEGACY_CONFIG[cc]()      # configuración HEREDADA (fixture): la de producción ya no lleva parámetros legales
    emp = {"salario_contrato": str(salary), "nombre": "x", "identificacion": "y"}
    new = new_cls().calcular(emp, dict(nov, _periodo=periodo), cfg)
    old = old_cls().calcular(emp, dict(nov), cfg)
    new.pop("_run", None)
    return new, old


def d(x):
    return Decimal(str(x)).quantize(Decimal("0.01"))


# ====================================================================== Colombia
def test_co_sin_diferencia_normativa_los_resultados_son_identicos():
    new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, 3_000_000, {"dias_trabajados": "30"})
    for section in ("devengado", "deducciones", "aportes_patronales"):
        for key in old[section]:
            assert abs(new[section][key] - old[section][key]) <= 0.006, (section, key)
    assert abs(new["total_devengado"] - old["total_devengado"]) <= 0.006
    assert abs(new["neto_pagado"] - old["neto_pagado"]) <= 0.006


def test_co_diferencia_intencional_auxilio_de_transporte_solo_hasta_2_smmlv():
    new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, 8_000_000,
                    {"dias_trabajados": "28", "incapacidad_dias_empresa": "2", "retencion_fuente": "69001"})
    assert d(old["devengado"]["auxilio_transporte"]) == Decimal("232488.67")     # heredado: pagaba auxilio a 8 M
    assert "auxilio_transporte" not in new["devengado"]                          # normativo: 8 M > 2 SMMLV
    assert d(old["total_devengado"]) == Decimal("8054710.89") and d(new["total_devengado"]) == Decimal("7822222.23")
    assert d(new["neto_pagado"]) == Decimal("7049221.23") and d(old["neto_pagado"]) == Decimal("7281709.89")
    assert d(old["total_devengado"] - new["total_devengado"]) == Decimal("232488.66")   # exactamente el auxilio


def test_co_diferencia_intencional_exoneracion_menos_de_10_smmlv_y_no_25_smmlv():
    new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, 20_000_000, {"dias_trabajados": "30"})
    assert old["aportes_patronales"]["salud_empleador"] == 0 and old["aportes_patronales"]["sena"] == 0
    assert new["aportes_patronales"]["salud_empleador"] == 1_700_000.0            # 8,5% de 20 M
    assert new["aportes_patronales"]["sena"] == 400_000.0 and new["aportes_patronales"]["icbf"] == 600_000.0


def test_co_diferencia_intencional_topes_de_25_smmlv_tambien_para_el_empleador_y_el_fsp():
    new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, 50_000_000, {"dias_trabajados": "30"})
    cap = 25 * SMMLV
    assert old["aportes_patronales"]["pension_empleador"] == 6_000_000.0          # heredado: sin tope
    assert d(new["aportes_patronales"]["pension_empleador"]) == d(cap * Decimal("0.12"))
    assert old["deducciones"]["aporte_fsp_empleado"] == 1_000_000.0
    assert d(new["deducciones"]["aporte_fsp_empleado"]) == d(cap * Decimal("0.02"))
    # el trabajador ya estaba limitado al tope en el motor heredado: sin cambio
    assert d(new["deducciones"]["aporte_salud_empleado"]) == d(old["deducciones"]["aporte_salud_empleado"])


def test_co_diferencia_intencional_una_sola_base_para_vacaciones_compensadas():
    new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, 3_000_000,
                    {"dias_trabajados": "20", "vac_compensadas_dias": "10"})
    ibc = Decimal("3000000") / 30 * 20 + Decimal("3000000") / 30 * 10
    assert d(new["deducciones"]["aporte_salud_empleado"]) == d(ibc * Decimal("0.04"))
    # heredado: trabajador sobre 3 M (incluía compensadas) pero empleador sobre 2 M (las excluía)
    assert abs(old["aportes_patronales"]["pension_empleador"] - 240_000.0) < 0.01
    assert d(new["aportes_patronales"]["pension_empleador"]) == d(ibc * Decimal("0.12"))


def test_co_diferencia_intencional_provisiones_con_razones_exactas_y_auxilio_en_la_base():
    new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, 3_000_000, {"dias_trabajados": "30"})
    assert abs(old["provisiones"]["prima"] - 249_900.0) < 0.01                    # 3 M × 0,0833 (aproximación)
    assert d(new["provisiones"]["prima"]) == d((Decimal("3000000") + Decimal("249095")) / 12)
    assert abs(old["provisiones"]["vacaciones"] - 125_100.0) < 0.01               # 3 M × 0,0417
    assert d(new["provisiones"]["vacaciones"]) == Decimal("125000.00")            # 15/360 exacto


def test_co_diferencia_intencional_ajuste_trm_ahora_es_una_linea_visible():
    new, old = both("CO", ColombiaNormativeEngine, ColombiaPayrollEngine, 3_000_000, {"dias_trabajados": "30", "ajuste_trm": "100000"})
    assert "ajuste_trm" not in old["devengado"]                                   # heredado: sumaba al total sin mostrarlo
    assert new["devengado"]["ajuste_trm"] == 100_000.0
    assert abs(sum(new["devengado"].values()) - new["total_devengado"]) < 0.01     # ahora las líneas suman el total
    assert abs(sum(old["devengado"].values()) - old["total_devengado"]) > 1        # antes NO sumaban


# ====================================================================== otros países
PAIRS = {
    "MX": (N.MexicoNormativeEngine, MexicoPayrollEngine, {"dias_trabajados": "30", "bonos_percepciones": "2000", "isr_retenido": "3500"}, [30_000, 9_582.47, 250_000]),
    "PE": (N.PeruNormativeEngine, PeruPayrollEngine, {"dias_trabajados": "30", "asignacion_familiar": "113", "bonos_comisiones": "300"}, [2_500, 1_130, 40_000]),
    "CL": (N.ChileNormativeEngine, ChilePayrollEngine, {"dias_trabajados": "30", "gratificacion_legal": "50000"}, [900_000, 553_553, 3_000_000]),
    "BR": (N.BrasilNormativeEngine, BrasilPayrollEngine, {"dias_trabajados": "30", "bonos_comisiones": "200"}, [3_500, 1_621, 20_000]),
    "AR": (N.ArgentinaNormativeEngine, ArgentinaPayrollEngine, {"dias_trabajados": "30", "bonos_comisiones": "30000"}, [700_000, 383_800, 5_000_000]),
    "EC": (N.EcuadorNormativeEngine, EcuadorPayrollEngine, {"dias_trabajados": "30", "bonos_comisiones": "50"}, [850, 482, 12_000]),
}


@pytest.mark.parametrize("cc", sorted(PAIRS))
@pytest.mark.parametrize("salary_idx", [0, 1, 2])
def test_paises_migrados_son_equivalentes_al_heredado_salvo_redondeo(cc, salary_idx):
    new_cls, old_cls, nov, salaries = PAIRS[cc]
    new, old = both(cc, new_cls, old_cls, salaries[salary_idx], nov)
    for section in SECTIONS:
        assert set(new[section]) == set(old[section]), (cc, section)
        for key in old[section]:
            assert abs(new[section][key] - old[section][key]) <= 0.06, (cc, section, key, new[section][key], old[section][key])
    for key in ("total_devengado", "total_deducciones", "neto_pagado", "total_aportes_patronales", "total_provisiones"):
        assert abs(new[key] - old[key]) <= 0.06, (cc, key)


@pytest.mark.parametrize("cc", sorted(PAIRS))
def test_paises_migrados_dias_parciales_equivalentes(cc):
    new_cls, old_cls, nov, salaries = PAIRS[cc]
    new, old = both(cc, new_cls, old_cls, salaries[0], dict(nov, dias_trabajados="15"))
    assert abs(new["neto_pagado"] - old["neto_pagado"]) <= 0.06
    assert abs(new["total_aportes_patronales"] - old["total_aportes_patronales"]) <= 0.06


def test_mx_incapacidad_equivalente():
    new_cls, old_cls, nov, salaries = PAIRS["MX"]
    new, old = both("MX", new_cls, old_cls, 30_000, dict(nov, dias_incapacidad="5"))
    assert abs(new["neto_pagado"] - old["neto_pagado"]) <= 0.06
