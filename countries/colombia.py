"""Formulario y ejemplos DEMO de Colombia para la interfaz.

Este módulo NO contiene reglas legales. El cálculo mensual y la liquidación corren sobre `payroll_engine` con los
datos versionados de config/payroll/CO/2026/ (adaptadores en countries/normative_engines.py). El motor heredado
que vivía aquí se movió a tests/payroll_2026/legacy_fixtures/ solo como fixture de regresión."""

from .base import CountryConfig, FormSpec


def ColombiaConfig() -> CountryConfig:
    return CountryConfig(
        code='CO',
        name='Colombia',
        currency='COP',
        idioma_default='es',
        nombre_liquidacion='Liquidación de prestaciones sociales',
    )


class ColombiaForm(FormSpec):
    """Campos del formulario de novedades y escenarios DEMO (datos ficticios; no son valores legales)."""

    NOVEDADES_CAMPOS = [
        ("dias_trabajados", "dias_trabajados", "0.5", "30"),
        ("ajuste_trm", "ajuste_trm", "0.01", "0"),
        ("incapacidad_dias_empresa", "incapacidad_dias_empresa", "0.5", "0"),
        ("incapacidad_valor_eps", "incapacidad_valor_eps", "0.01", "0"),
        ("vac_disfrutadas_dias", "vac_disfrutadas_dias", "0.5", "0"),
        ("vac_no_habiles_dias", "vac_no_habiles_dias", "0.5", "0"),
        ("vac_compensadas_dias", "vac_compensadas_dias", "0.5", "0"),
        ("bonos_comisiones", "bonos_comisiones", "0.01", "0"),
        ("bonificaciones_no_salariales", "bonificaciones_no_salariales", "0.01", "0"),
        ("descuento_afc", "descuento_afc", "0.01", "0"),
        ("aportes_voluntarios_pension", "aportes_voluntarios_pension", "0.01", "0"),
        ("prestamos_avances", "prestamos_avances", "0.01", "0"),
        ("retencion_fuente", "retencion_fuente", "0.01", "0"),
    ]

    EJEMPLO_NOVEDADES = {
        "nombre": "Empleado Colombia Demo",
        "identificacion": "DEMO-CO-001",
        "salario_contrato": "8000000",
        "dias_trabajados": "28",
        "incapacidad_dias_empresa": "2",
        "retencion_fuente": "69001",
    }

    EJEMPLO_LIQUIDACION = {
        "nombre": "Empleado Colombia Demo",
        "identificacion": "DEMO-CO-002",
        "salario_contrato": "3000000",
        "fecha_ingreso": "2023-01-15",
        "fecha_retiro": "2026-09-20",
        "tipo_contrato": "indefinido",
        "tipo_terminacion": "sin_justa_causa",
        "dias_vacaciones_pendientes": "10",
    }
