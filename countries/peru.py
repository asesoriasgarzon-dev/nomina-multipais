"""Formulario y ejemplos DEMO de Perú para la interfaz.

Este módulo NO contiene reglas legales. El cálculo mensual y la liquidación corren sobre `payroll_engine` con los
datos versionados de config/payroll/PE/2026/ (adaptadores en countries/normative_engines.py). El motor heredado
que vivía aquí se movió a tests/payroll_2026/legacy_fixtures/ solo como fixture de regresión."""

from .base import CountryConfig, FormSpec


def PeruConfig() -> CountryConfig:
    return CountryConfig(
        code='PE',
        name='Perú',
        currency='PEN',
        idioma_default='es',
        nombre_liquidacion='Liquidación de beneficios sociales',
    )


class PeruForm(FormSpec):
    """Campos del formulario de novedades y escenarios DEMO (datos ficticios; no son valores legales)."""

    NOVEDADES_CAMPOS = [
        ("dias_trabajados", "dias_trabajados", "0.5", "30"),
        ("bonos_comisiones", "bonos_comisiones", "0.01", "0"),
        ("asignacion_familiar", "asignacion_familiar", "0.01", "0"),
        ("prestamos_avances", "prestamos_avances", "0.01", "0"),
        ("retencion_impuesto_renta", "retencion_impuesto_renta", "0.01", "0"),
    ]

    EJEMPLO_NOVEDADES = {
        "nombre": "Empleado Perú Demo",
        "identificacion": "DEMO-PE-001",
        "salario_contrato": "2500",
        "dias_trabajados": "30",
        "asignacion_familiar": "113",
    }

    EJEMPLO_LIQUIDACION = {
        "nombre": "Empleado Perú Demo",
        "identificacion": "DEMO-PE-002",
        "salario_contrato": "2500",
        "fecha_ingreso": "2023-01-15",
        "fecha_retiro": "2026-09-20",
        "tipo_contrato": "indefinido",
        "tipo_terminacion": "sin_justa_causa",
        "dias_vacaciones_pendientes": "10",
    }
