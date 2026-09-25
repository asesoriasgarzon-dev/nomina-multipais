from datetime import date

from .legacy_base import CountryConfig, PayrollEngine


def PeruConfig() -> CountryConfig:
    return CountryConfig(
        code="PE", name="Perú", currency="PEN", idioma_default="es",
        salario_minimo=1_130,
        jornada_semanal_horas=48,
        vacaciones_dias_anuales=30,
        prima_o_aguinaldo="Gratificaciones de julio y diciembre (1 remuneración c/u) + CTS en mayo/noviembre",
        nombre_liquidacion="Liquidación de beneficios sociales",
        fuente="NORMATIVA_PAISES.md sección Perú. Fuentes oficiales: gob.pe/mtpe, SBS "
        "(sbs.gob.pe), SUNAT. El trabajador elige ONP (pensión pública) o AFP (privada), nunca "
        "ambas — este motor asume AFP por defecto (ver simplificación documentada).",
        campos_extra={
            "essalud_empleador": 0.09,
            "onp_empleado": 0.13,
            "afp_aporte_obligatorio": 0.10,
            "afp_seguro": 0.0137,
            "afp_comision_promedio": 0.0155,  # promedio de mercado — varía por AFP, parametrizar en producción
            "asignacion_familiar_default": 113,  # 10% de la RMV, fijo, con hijos menores de 18
            "indemnizacion_despido": "1.5 remuneraciones/año completo, tope 12 remuneraciones",
            "pago_periodicidad": "mensual",
        },
    )


class PeruPayrollEngine(PayrollEngine):
    """Motor de nómina Perú, basado en NORMATIVA_PAISES.md.

    Simplificaciones deliberadas:
    - Asume que el empleado está afiliado a AFP (privada), no a ONP —el
      sistema es excluyente por trabajador y aquí no hay un selector; para
      un empleado en ONP, la deducción de pensión sería 13% plano en vez de
      la fórmula AFP de abajo.
    - Comisión de AFP fija aproximada (1.55%); en la realidad varía por
      administradora (SBS la regula) — parametrizar antes de producción.
    - Gratificación y CTS se muestran como PROVISIÓN mensual (igual criterio
      que las prestaciones sociales de Colombia), no como el depósito real
      bianual — simplificación para que el panel consolidado tenga una
      cifra mensual comparable entre países.
    """

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

    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        extra = config.campos_extra
        salario_contrato = float(empleado.get("salario_contrato", 0))
        dias_trabajados = float(novedades.get("dias_trabajados", 30))
        bonos = float(novedades.get("bonos_comisiones", 0))
        asignacion_familiar = float(novedades.get("asignacion_familiar", 0))
        prestamos = float(novedades.get("prestamos_avances", 0))
        renta = float(novedades.get("retencion_impuesto_renta", 0))

        remuneracion = salario_contrato / 30 * dias_trabajados
        total_devengado = remuneracion + bonos + asignacion_familiar

        tasa_afp = extra["afp_aporte_obligatorio"] + extra["afp_seguro"] + extra["afp_comision_promedio"]
        aporte_pension_privada = remuneracion * tasa_afp
        total_deducciones = aporte_pension_privada + prestamos + renta
        neto_pagado = total_devengado - total_deducciones

        salud_empleador = remuneracion * extra["essalud_empleador"]
        total_aportes_patronales = salud_empleador

        gratificacion_prov = remuneracion / 6      # 2 gratificaciones/año = 1/6 mensual
        cts_prov = remuneracion / 12               # CTS ≈ 1 remuneración/año
        total_provisiones = gratificacion_prov + cts_prov

        return {
            "devengado": {
                "valor_salario_devengado": remuneracion,
                "bonos_comisiones": bonos,
                "asignacion_familiar": asignacion_familiar,
            },
            "deducciones": {
                "aporte_pension_privada_empleado": aporte_pension_privada,
                "prestamos_avances": prestamos,
                "retencion_impuesto_renta": renta,
            },
            "aportes_patronales": {
                "salud_empleador": salud_empleador,
            },
            "provisiones": {
                "prima": gratificacion_prov,
                "cesantias": cts_prov,
            },
            "total_devengado": total_devengado,
            "total_deducciones": total_deducciones,
            "neto_pagado": neto_pagado,
            "total_aportes_patronales": total_aportes_patronales,
            "total_provisiones": total_provisiones,
        }

    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Liquidación de beneficios sociales: CTS + gratificación truncada +
        vacaciones truncadas, más indemnización si el despido es arbitrario
        (D.Leg. 728 art. 38: 1.5 remuneraciones/año, tope 12)."""
        salario_base = float(datos.get("salario_base") or empleado.get("salario_contrato", 0))
        fecha_ingreso = date.fromisoformat(datos["fecha_ingreso"])
        fecha_retiro = date.fromisoformat(datos["fecha_retiro"])
        tipo_terminacion = datos.get("tipo_terminacion", "renuncia")
        dias_vacaciones_pendientes = float(datos.get("dias_vacaciones_pendientes", 0))
        salarios_pendientes = float(datos.get("salarios_pendientes", 0))
        remuneracion_diaria = salario_base / 30

        inicio_ano = date(fecha_retiro.year, 1, 1)
        fecha_inicio = max(fecha_ingreso, inicio_ano)
        dias_periodo = (fecha_retiro - fecha_inicio).days + 1

        cts_truncada = salario_base * dias_periodo / 360
        gratificacion_truncada = salario_base * dias_periodo / 360
        vacaciones_pendientes = remuneracion_diaria * dias_vacaciones_pendientes

        antiguedad_dias = (fecha_retiro - fecha_ingreso).days + 1
        antiguedad_anos = antiguedad_dias / 365

        indemnizacion = 0.0
        aplica_indemnizacion = tipo_terminacion == "sin_justa_causa"
        if aplica_indemnizacion:
            indemnizacion = min(salario_base * 1.5 * antiguedad_anos, salario_base * 12)

        conceptos = {
            "salarios_pendientes": salarios_pendientes,
            "cesantias": cts_truncada,
            "prima_servicios": gratificacion_truncada,
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
