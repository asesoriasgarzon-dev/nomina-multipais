"""Formulario y ejemplos DEMO de Argentina para la interfaz.

Este módulo NO contiene reglas legales. El cálculo mensual y la liquidación corren sobre `payroll_engine` con los
datos versionados de config/payroll/AR/2026/ (adaptadores en countries/normative_engines.py). El motor heredado
que vivía aquí se movió a tests/payroll_2026/legacy_fixtures/ solo como fixture de regresión."""

from .base import CountryConfig, FormSpec


def ArgentinaConfig() -> CountryConfig:
    return CountryConfig(
        code='AR',
        name='Argentina',
        currency='ARS',
        idioma_default='es',
        nombre_liquidacion='Liquidación final',
    )


class ArgentinaForm(FormSpec):
    """Campos del formulario de novedades y escenarios DEMO (datos ficticios; no son valores legales)."""

    NOVEDADES_CAMPOS = [
        ("dias_trabajados", "dias_trabajados", "0.5", "30"),
        ("bonos_comisiones", "bonos_comisiones", "0.01", "0"),
        ("prestamos_avances", "prestamos_avances", "0.01", "0"),
        ("retencion_impuesto_renta", "retencion_impuesto_renta", "0.01", "0"),
    ]

    EJEMPLO_NOVEDADES = {
        "nombre": "Empleado Argentina Demo",
        "identificacion": "DEMO-AR-001",
        "salario_contrato": "700000",
        "dias_trabajados": "30",
        "bonos_comisiones": "30000",
    }

    EJEMPLO_LIQUIDACION = {
        "nombre": "Empleado Argentina Demo",
        "identificacion": "DEMO-AR-002",
        "salario_contrato": "700000",
        "fecha_ingreso": "2023-01-15",
        "fecha_retiro": "2026-09-20",
        "tipo_contrato": "indefinido",
        "tipo_terminacion": "sin_justa_causa",
        "dias_vacaciones_pendientes": "10",
    }
