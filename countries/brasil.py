"""Formulario y ejemplos DEMO de Brasil para la interfaz.

Este módulo NO contiene reglas legales. El cálculo mensual y la liquidación corren sobre `payroll_engine` con los
datos versionados de config/payroll/BR/2026/ (adaptadores en countries/normative_engines.py). El motor heredado
que vivía aquí se movió a tests/payroll_2026/legacy_fixtures/ solo como fixture de regresión."""

from .base import CountryConfig, FormSpec


def BrasilConfig() -> CountryConfig:
    return CountryConfig(
        code='BR',
        name='Brasil',
        currency='BRL',
        idioma_default='pt',
        nombre_liquidacion='Rescisão (TRCT — Termo de Rescisão do Contrato de Trabalho)',
    )


class BrasilForm(FormSpec):
    """Campos del formulario de novedades y escenarios DEMO (datos ficticios; no son valores legales)."""

    NOVEDADES_CAMPOS = [
        ("dias_trabajados", "dias_trabajados", "0.5", "30"),
        ("bonos_comisiones", "bonos_comisiones", "0.01", "0"),
        ("prestamos_avances", "prestamos_avances", "0.01", "0"),
        ("retencion_impuesto_renta", "retencion_impuesto_renta", "0.01", "0"),
    ]

    EJEMPLO_NOVEDADES = {
        "nombre": "Funcionário Demo Brasil",
        "identificacion": "DEMO-BR-001",
        "salario_contrato": "3500",
        "dias_trabajados": "30",
        "bonos_comisiones": "200",
    }

    EJEMPLO_LIQUIDACION = {
        "nombre": "Funcionário Demo Brasil",
        "identificacion": "DEMO-BR-002",
        "salario_contrato": "3500",
        "fecha_ingreso": "2023-01-15",
        "fecha_retiro": "2026-09-20",
        "tipo_contrato": "indefinido",
        "tipo_terminacion": "sin_justa_causa",
        "dias_vacaciones_pendientes": "10",
    }
