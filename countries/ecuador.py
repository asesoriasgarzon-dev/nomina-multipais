from datetime import date

from .base import CountryConfig, PayrollEngine


def EcuadorConfig() -> CountryConfig:
    return CountryConfig(
        code="EC", name="Ecuador", currency="USD", idioma_default="es",
        salario_minimo=482,
        jornada_semanal_horas=40,
        vacaciones_dias_anuales=15,
        prima_o_aguinaldo="Décimo tercero (hasta 24-dic) y décimo cuarto (15-mar Costa / 15-ago Sierra)",
        nombre_liquidacion="Acta de finiquito",
        fuente="NORMATIVA_PAISES.md sección Ecuador. Fuentes oficiales: trabajo.gob.ec, "
        "iess.gob.ec, finanzas.gob.ec. La indemnización por despido intempestivo tiene DOS "
        "rubros acumulativos (art. 188 + art. 185) — liquidar solo uno es el error más común.",
        campos_extra={
            "iess_empleador": 0.1115,
            "iess_empleado": 0.0945,
            "fondo_reserva_empleador": 0.0833,
            "iece_secap_empleador": 0.01,
            "indemnizacion_despido": "art.188 (3 meses o 1 mes/año tope 25) + art.185 (25% ultima remun/año completo)",
            "base_indemnizacion": "mejor remuneracion percibida en toda la relacion laboral (no la ultima)",
            "pago_periodicidad": "mensual (sueldo) o semanal (salario/jornaleros)",
        },
    )


class EcuadorPayrollEngine(PayrollEngine):
    """Motor de nómina Ecuador (IESS), basado en NORMATIVA_PAISES.md.

    Simplificaciones deliberadas:
    - El Fondo de Reserva (8.33% patronal, desde el 2º año continuo) se
      provisiona SIEMPRE desde el primer mes en este prototipo — no hay
      lógica de antigüedad para activarlo/desactivarlo automáticamente.
    - Décimo tercero y décimo cuarto se muestran como provisión mensual
      combinada, no como los dos pagos anuales reales en sus fechas propias.
    - Base de indemnización: usa el salario del formulario como "mejor
      remuneración", sin comparar contra un historial real de remuneraciones
      de toda la relación laboral (la Resolución 02-2025 de la Corte
      Nacional de Justicia exige la mejor histórica, no necesariamente la
      última) — habría que integrarlo con el historial de nóminas guardadas.
    """

    NOVEDADES_CAMPOS = [
        ("dias_trabajados", "dias_trabajados", "0.5", "30"),
        ("bonos_comisiones", "bonos_comisiones", "0.01", "0"),
        ("prestamos_avances", "prestamos_avances", "0.01", "0"),
        ("retencion_impuesto_renta", "retencion_impuesto_renta", "0.01", "0"),
    ]

    EJEMPLO_NOVEDADES = {
        "nombre": "Empleado Ecuador Demo",
        "identificacion": "DEMO-EC-001",
        "salario_contrato": "850",
        "dias_trabajados": "30",
        "bonos_comisiones": "50",
    }
    EJEMPLO_LIQUIDACION = {
        "nombre": "Empleado Ecuador Demo",
        "identificacion": "DEMO-EC-002",
        "salario_contrato": "850",
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
        renta = float(novedades.get("retencion_impuesto_renta", 0))

        remuneracion = salario_contrato / 30 * dias_trabajados
        total_devengado = remuneracion + bonos

        aporte_iess_emp = remuneracion * extra["iess_empleado"]
        total_deducciones = aporte_iess_emp + prestamos + renta
        neto_pagado = total_devengado - total_deducciones

        iess_patronal = remuneracion * extra["iess_empleador"]
        capacitacion = remuneracion * extra["iece_secap_empleador"]
        fondo_reserva = remuneracion * extra["fondo_reserva_empleador"]
        total_aportes_patronales = iess_patronal + capacitacion

        decimo_tercero_prov = remuneracion / 12
        decimo_cuarto_prov = config.salario_minimo / 12
        total_provisiones = decimo_tercero_prov + decimo_cuarto_prov + fondo_reserva

        return {
            "devengado": {
                "valor_salario_devengado": remuneracion,
                "bonos_comisiones": bonos,
            },
            "deducciones": {
                "aporte_pension_empleado": aporte_iess_emp,
                "prestamos_avances": prestamos,
                "retencion_impuesto_renta": renta,
            },
            "aportes_patronales": {
                "pension_empleador": iess_patronal,
                "aporte_capacitacion_empleador": capacitacion,
            },
            "provisiones": {
                "prima": decimo_tercero_prov + decimo_cuarto_prov,
                "fondo_garantia_empleador": fondo_reserva,
            },
            "total_devengado": total_devengado,
            "total_deducciones": total_deducciones,
            "neto_pagado": neto_pagado,
            "total_aportes_patronales": total_aportes_patronales,
            "total_provisiones": total_provisiones,
        }

    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Acta de finiquito: DOS indemnizaciones acumulativas cuando el
        despido es intempestivo — art. 188 (Código del Trabajo) + art. 185
        (bonificación por desahucio) — más décimos proporcionales y
        vacaciones pendientes."""
        salario_base = float(datos.get("salario_base") or empleado.get("salario_contrato", 0))
        fecha_ingreso = date.fromisoformat(datos["fecha_ingreso"])
        fecha_retiro = date.fromisoformat(datos["fecha_retiro"])
        tipo_terminacion = datos.get("tipo_terminacion", "renuncia")
        dias_vacaciones_pendientes = float(datos.get("dias_vacaciones_pendientes", 0))
        salarios_pendientes = float(datos.get("salarios_pendientes", 0))
        salario_diario = salario_base / 30

        inicio_ano = date(fecha_retiro.year, 1, 1)
        fecha_inicio = max(fecha_ingreso, inicio_ano)
        dias_periodo = (fecha_retiro - fecha_inicio).days + 1
        decimo_tercero_prop = salario_base * dias_periodo / 360
        decimo_cuarto_prop = config.salario_minimo * dias_periodo / 360

        vacaciones_pendientes = salario_diario * dias_vacaciones_pendientes

        antiguedad_dias = (fecha_retiro - fecha_ingreso).days + 1
        antiguedad_anos_exactos = antiguedad_dias / 365
        anos_completos = int(antiguedad_anos_exactos)

        indemnizacion = 0.0
        aplica_indemnizacion = tipo_terminacion == "sin_justa_causa"
        if aplica_indemnizacion:
            if antiguedad_anos_exactos <= 3:
                art188 = salario_base * 3
            else:
                art188 = min(salario_base * antiguedad_anos_exactos, salario_base * 25)
            art185 = salario_base * 0.25 * anos_completos
            indemnizacion = art188 + art185

        conceptos = {
            "salarios_pendientes": salarios_pendientes,
            "prima_servicios": decimo_tercero_prop + decimo_cuarto_prop,
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
