"""Formulario y ejemplos DEMO de México para la interfaz.

Este módulo NO contiene reglas legales. El cálculo mensual y la liquidación corren sobre `payroll_engine` con los
datos versionados de config/payroll/MX/2026/ (adaptadores en countries/normative_engines.py). El motor heredado
que vivía aquí se movió a tests/payroll_2026/legacy_fixtures/ solo como fixture de regresión."""

from .base import CountryConfig, FormSpec


def MexicoConfig() -> CountryConfig:
    return CountryConfig(
        code='MX',
        name='México',
        currency='MXN',
        idioma_default='es',
        nombre_liquidacion='Finiquito (renuncia) / Liquidación (despido)',
    )


class MexicoForm(FormSpec):
    """Campos del formulario de novedades y escenarios DEMO (datos ficticios; no son valores legales)."""

    NOVEDADES_CAMPOS = [
        ("dias_trabajados", "dias_trabajados", "0.5", "30"),
        ("dias_incapacidad", "incapacidad_dias_empresa", "0.5", "0"),
        ("bonos_percepciones", "bonos_comisiones", "0.01", "0"),
        ("descuento_infonavit_credito", "descuento_credito_vivienda", "0.01", "0"),
        ("prestamos_descuentos", "prestamos_avances", "0.01", "0"),
        ("isr_retenido", "retencion_impuesto_renta", "0.01", "0"),
    ]

    EJEMPLO_NOVEDADES = {
        "nombre": "Empleado México Demo",
        "identificacion": "DEMO-MX-001",
        "salario_contrato": "30000",
        "dias_trabajados": "30",
        "bonos_percepciones": "2000",
        "isr_retenido": "3500",
    }

    EJEMPLO_LIQUIDACION = {
        "nombre": "Empleado México Demo",
        "identificacion": "DEMO-MX-002",
        "salario_contrato": "30000",
        "fecha_ingreso": "2023-01-15",
        "fecha_retiro": "2026-09-20",
        "tipo_contrato": "indefinido",
        "tipo_terminacion": "sin_justa_causa",
        "dias_vacaciones_pendientes": "10",
    }
