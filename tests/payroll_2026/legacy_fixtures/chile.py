from datetime import date

from .legacy_base import CountryConfig, PayrollEngine


def ChileConfig() -> CountryConfig:
    return CountryConfig(
        code="CL", name="Chile", currency="CLP", idioma_default="es",
        salario_minimo=553_553,
        jornada_semanal_horas=42,
        vacaciones_dias_anuales=15,
        prima_o_aguinaldo="No hay aguinaldo legal general; gratificación legal si hay utilidades (25% remun. mensual, tope 4.75 IMM/año)",
        nombre_liquidacion="Finiquito",
        fuente="NORMATIVA_PAISES.md sección Chile. Fuentes oficiales: mintrab.gob.cl, "
        "dt.gob.cl, Superintendencia de Pensiones (spensiones.cl), SUSESO, SII. Comisión de "
        "AFP varía por administradora (0.44%-1.45%) — parametrizar, no fijar.",
        campos_extra={
            "afp_aporte": 0.10,
            "afp_comision_promedio": 0.0100,  # promedio de mercado aprox. — varía por AFP, parametrizar en producción
            "salud_empleado": 0.07,
            "sis_empleador": 0.0162,
            "afc_empleador_indefinido": 0.024,
            "afc_empleado_indefinido": 0.006,
            "mutualidad_empleador": 0.0090,
            "reforma_previsional_empleador_2026": 0.035,
            "indemnizacion_despido": "30 dias/año de servicio, tope 11 años (330 dias)",
            "pago_periodicidad": "mensual (máximo legal)",
        },
    )


class ChilePayrollEngine(PayrollEngine):
    """Motor de nómina Chile, basado en NORMATIVA_PAISES.md.

    Simplificaciones deliberadas:
    - No se aplica el tope imponible de 90 UF: no hay un valor de UF (varía
      diariamente) confiable en este prototipo — se asume que el salario
      ingresado no lo supera. Verificar antes de producción con salarios altos.
    - Comisión de AFP fija aproximada (1%); en la realidad varía por
      administradora (0.44%-1.45%, ver NORMATIVA_PAISES.md).
    - Contrato asumido "indefinido" para las tasas de AFC (2.4% patronal /
      0.6% empleado); un contrato a plazo fijo tiene tasas distintas
      (3% patronal, 0% empleado) — no hay selector de tipo de contrato en
      la nómina mensual todavía.
    - Gratificación legal (solo si la empresa tiene utilidades) se recibe
      como valor manual, no se calcula automáticamente.
    - Vacaciones se provisionan mensualmente (15 días hábiles/año ≈ 4.17%)
      como aproximación — en la práctica se paga cuando se toman, no se
      provisiona contablemente mes a mes de forma obligatoria.
    """

    NOVEDADES_CAMPOS = [
        ("dias_trabajados", "dias_trabajados", "0.5", "30"),
        ("bonos_comisiones", "bonos_comisiones", "0.01", "0"),
        ("gratificacion_legal", "gratificacion_legal", "0.01", "0"),
        ("prestamos_avances", "prestamos_avances", "0.01", "0"),
        ("retencion_impuesto_renta", "retencion_impuesto_renta", "0.01", "0"),
    ]

    EJEMPLO_NOVEDADES = {
        "nombre": "Empleado Chile Demo",
        "identificacion": "DEMO-CL-001",
        "salario_contrato": "900000",
        "dias_trabajados": "30",
        "gratificacion_legal": "50000",
    }
    EJEMPLO_LIQUIDACION = {
        "nombre": "Empleado Chile Demo",
        "identificacion": "DEMO-CL-002",
        "salario_contrato": "900000",
        "fecha_ingreso": "2023-01-15",
        "fecha_retiro": "2026-09-20",
        "tipo_contrato": "indefinido",
        "tipo_terminacion": "sin_justa_causa",
        "dias_vacaciones_pendientes": "10",
    }

    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        extra = config.campos_extra
        salario_contrato = float(empleado.get("salario_contrato", 0))
        dias_trabajados = float(novedades.get("dias_trabajados", 30))
        bonos = float(novedades.get("bonos_comisiones", 0))
        gratificacion = float(novedades.get("gratificacion_legal", 0))
        prestamos = float(novedades.get("prestamos_avances", 0))
        renta = float(novedades.get("retencion_impuesto_renta", 0))

        remuneracion = salario_contrato / 30 * dias_trabajados
        total_devengado = remuneracion + bonos + gratificacion

        tasa_afp = extra["afp_aporte"] + extra["afp_comision_promedio"]
        aporte_pension_emp = remuneracion * (tasa_afp + extra["afc_empleado_indefinido"])
        aporte_salud_emp = remuneracion * extra["salud_empleado"]
        total_deducciones = aporte_pension_emp + aporte_salud_emp + prestamos + renta
        neto_pagado = total_devengado - total_deducciones

        pension_empleador = remuneracion * (extra["sis_empleador"] + extra["reforma_previsional_empleador_2026"])
        riesgo_laboral = remuneracion * extra["mutualidad_empleador"]
        fondo_cesantia_empleador = remuneracion * extra["afc_empleador_indefinido"]
        total_aportes_patronales = pension_empleador + riesgo_laboral + fondo_cesantia_empleador

        vacaciones_prov = remuneracion * 0.0417

        return {
            "devengado": {
                "valor_salario_devengado": remuneracion,
                "bonos_comisiones": bonos,
                "gratificacion_legal": gratificacion,
            },
            "deducciones": {
                "aporte_pension_privada_empleado": aporte_pension_emp,
                "aporte_salud_empleado": aporte_salud_emp,
                "prestamos_avances": prestamos,
                "retencion_impuesto_renta": renta,
            },
            "aportes_patronales": {
                "pension_empleador": pension_empleador,
                "aporte_riesgo_laboral_empleador": riesgo_laboral,
                "fondo_garantia_empleador": fondo_cesantia_empleador,
            },
            "provisiones": {
                "vacaciones": vacaciones_prov,
            },
            "total_devengado": total_devengado,
            "total_deducciones": total_deducciones,
            "neto_pagado": neto_pagado,
            "total_aportes_patronales": total_aportes_patronales,
            "total_provisiones": vacaciones_prov,
        }

    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Finiquito: vacaciones proporcionales/pendientes + indemnización por
        años de servicio (30 días/año, tope 11 años) cuando el despido es sin
        justa causa (necesidades de la empresa)."""
        salario_base = float(datos.get("salario_base") or empleado.get("salario_contrato", 0))
        fecha_ingreso = date.fromisoformat(datos["fecha_ingreso"])
        fecha_retiro = date.fromisoformat(datos["fecha_retiro"])
        tipo_terminacion = datos.get("tipo_terminacion", "renuncia")
        dias_vacaciones_pendientes = float(datos.get("dias_vacaciones_pendientes", 0))
        salarios_pendientes = float(datos.get("salarios_pendientes", 0))
        salario_diario = salario_base / 30

        vacaciones_pendientes = salario_diario * dias_vacaciones_pendientes

        antiguedad_dias = (fecha_retiro - fecha_ingreso).days + 1
        antiguedad_anos = antiguedad_dias / 365

        indemnizacion = 0.0
        aplica_indemnizacion = tipo_terminacion == "sin_justa_causa"
        if aplica_indemnizacion:
            anos_para_indemnizacion = min(antiguedad_anos, 11)
            indemnizacion = salario_base * anos_para_indemnizacion
            # + 1 mes de aviso previo sustitutivo si no se avisó con 30 días
            indemnizacion += salario_base

        conceptos = {
            "salarios_pendientes": salarios_pendientes,
            "vacaciones_pendientes": vacaciones_pendientes,
        }
        total_prestaciones = sum(conceptos.values())

        return {
            "conceptos": conceptos,
            "total_prestaciones": total_prestaciones,
            "indemnizacion": indemnizacion,
            "aplica_indemnizacion": aplica_indemnizacion,
            "total_liquidacion": total_prestaciones + indemnizacion,
            "antiguedad_anos": round(antiguedad_anos, 2),
        }
