from datetime import date

from .legacy_base import CountryConfig, PayrollEngine


def ArgentinaConfig() -> CountryConfig:
    return CountryConfig(
        code="AR", name="Argentina", currency="ARS", idioma_default="es",
        salario_minimo=383_800,
        jornada_semanal_horas=48,
        vacaciones_dias_anuales=14,
        prima_o_aguinaldo="SAC (aguinaldo) semestral, 50% mejor remuneración del semestre",
        nombre_liquidacion="Liquidación final",
        fuente="NORMATIVA_PAISES.md sección Argentina. Fuentes oficiales: boletinoficial.gob.ar, "
        "argentina.gob.ar/normativa, AFIP. Asume la contribución patronal unificada GENERAL "
        "(18%, no el 20,40% de Servicios/Comercio grandes) y aplica la Ley 27.802 (vigente "
        "desde 1-jun-2026) para toda liquidación, sin distinguir fecha de inicio del contrato.",
        campos_extra={
            "contribucion_patronal_unificada": 0.18,
            "obra_social_empleador": 0.06,
            "obra_social_empleado": 0.03,
            "jubilacion_empleado": 0.11,
            "pami_empleado": 0.03,
            "art_empleador": 0.015,  # aprox. actividad de bajo riesgo — varía por ART/actividad
            "ley_27802_vigencia": "2026-06-01",
            "indemnizacion_despido_desde_27802": "1 mes mejor remun. normal y habitual (excluye SAC/vacaciones/bonos) por año, tope 3x promedio convenio",
            "pago_periodicidad": "mensual (mensualizados) o quincenal (jornalizados)",
        },
    )


class ArgentinaPayrollEngine(PayrollEngine):
    """Motor de nómina Argentina, basado en NORMATIVA_PAISES.md.

    Simplificaciones deliberadas:
    - Contribución patronal unificada fija en 18% (régimen general); no
      distingue el 20,40% que aplica a empleadores grandes de
      Servicios/Comercio.
    - ART (riesgo del trabajo) usa una tasa fija de ejemplo (1.5%); en la
      realidad la fija cada aseguradora según la actividad.
    - La liquidación aplica siempre la fórmula de la Ley 27.802 (vigente
      desde 1-jun-2026); no distingue contratos iniciados antes de esa
      fecha, que seguirían la fórmula clásica del art. 245 LCT.
    - El tope de "3x el promedio del convenio colectivo" de la Ley 27.802 no
      se aplica (no hay dato de convenio colectivo en este prototipo).
    """

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

    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        extra = config.campos_extra
        salario_contrato = float(empleado.get("salario_contrato", 0))
        dias_trabajados = float(novedades.get("dias_trabajados", 30))
        bonos = float(novedades.get("bonos_comisiones", 0))
        prestamos = float(novedades.get("prestamos_avances", 0))
        ganancias = float(novedades.get("retencion_impuesto_renta", 0))

        remuneracion = salario_contrato / 30 * dias_trabajados
        total_devengado = remuneracion + bonos

        aporte_pension_emp = remuneracion * (extra["jubilacion_empleado"] + extra["pami_empleado"])
        aporte_salud_emp = remuneracion * extra["obra_social_empleado"]
        total_deducciones = aporte_pension_emp + aporte_salud_emp + prestamos + ganancias
        neto_pagado = total_devengado - total_deducciones

        pension_empleador = remuneracion * extra["contribucion_patronal_unificada"]
        salud_empleador = remuneracion * extra["obra_social_empleador"]
        riesgo_laboral = remuneracion * extra["art_empleador"]
        total_aportes_patronales = pension_empleador + salud_empleador + riesgo_laboral

        sac_prov = remuneracion / 12
        vacaciones_prov = remuneracion * config.vacaciones_dias_anuales / 360

        return {
            "devengado": {
                "valor_salario_devengado": remuneracion,
                "bonos_comisiones": bonos,
            },
            "deducciones": {
                "aporte_pension_empleado": aporte_pension_emp,
                "aporte_salud_empleado": aporte_salud_emp,
                "prestamos_avances": prestamos,
                "retencion_impuesto_renta": ganancias,
            },
            "aportes_patronales": {
                "pension_empleador": pension_empleador,
                "salud_empleador": salud_empleador,
                "aporte_riesgo_laboral_empleador": riesgo_laboral,
            },
            "provisiones": {
                "prima": sac_prov,
                "vacaciones": vacaciones_prov,
            },
            "total_devengado": total_devengado,
            "total_deducciones": total_deducciones,
            "neto_pagado": neto_pagado,
            "total_aportes_patronales": total_aportes_patronales,
            "total_provisiones": sac_prov + vacaciones_prov,
        }

    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Liquidación final bajo la Ley 27.802 (vigente desde 1-jun-2026):
        1 mes de la mejor remuneración normal y habitual por año de servicio
        o fracción >3 meses (excluye SAC/vacaciones/bonos de la base), más
        SAC y vacaciones proporcionales como conceptos separados."""
        salario_base = float(datos.get("salario_base") or empleado.get("salario_contrato", 0))
        fecha_ingreso = date.fromisoformat(datos["fecha_ingreso"])
        fecha_retiro = date.fromisoformat(datos["fecha_retiro"])
        tipo_terminacion = datos.get("tipo_terminacion", "renuncia")
        dias_vacaciones_pendientes = float(datos.get("dias_vacaciones_pendientes", 0))
        salarios_pendientes = float(datos.get("salarios_pendientes", 0))

        inicio_ano = date(fecha_retiro.year, 1, 1)
        fecha_inicio_sac = max(fecha_ingreso, inicio_ano)
        dias_periodo_sac = (fecha_retiro - fecha_inicio_sac).days + 1
        sac_proporcional = salario_base / 2 * (dias_periodo_sac / 180)

        vacaciones_pendientes = salario_base / 25 * dias_vacaciones_pendientes

        antiguedad_dias = (fecha_retiro - fecha_ingreso).days + 1
        antiguedad_anos_exactos = antiguedad_dias / 365

        indemnizacion = 0.0
        aplica_indemnizacion = tipo_terminacion == "sin_justa_causa"
        if aplica_indemnizacion:
            anos_enteros = int(antiguedad_anos_exactos)
            fraccion = antiguedad_anos_exactos - anos_enteros
            anos_computables = anos_enteros + 1 if fraccion > 0.25 else max(anos_enteros, 1)
            indemnizacion = salario_base * anos_computables

            if antiguedad_anos_exactos < 0.25:
                preaviso = salario_base / 2
            elif antiguedad_anos_exactos <= 5:
                preaviso = salario_base
            else:
                preaviso = salario_base * 2
            indemnizacion += preaviso

        conceptos = {
            "salarios_pendientes": salarios_pendientes,
            "prima_servicios": sac_proporcional,
            "vacaciones_pendientes": vacaciones_pendientes,
        }
        total_prestaciones = sum(conceptos.values())

        return {
            "conceptos": conceptos,
            "total_prestaciones": total_prestaciones,
            "indemnizacion": indemnizacion,
            "aplica_indemnizacion": aplica_indemnizacion,
            "total_liquidacion": total_prestaciones + indemnizacion,
            "antiguedad_anos": round(antiguedad_anos_exactos, 2),
        }
