from datetime import date

from .legacy_base import CountryConfig, PayrollEngine


def MexicoConfig() -> CountryConfig:
    return CountryConfig(
        code="MX", name="México", currency="MXN", idioma_default="es",
        salario_minimo=9_582.47,
        jornada_semanal_horas=48,
        vacaciones_dias_anuales=12,
        prima_o_aguinaldo="Aguinaldo mínimo 15 días/año, antes del 20-dic",
        nombre_liquidacion="Finiquito (renuncia) / Liquidación (despido)",
        fuente="NORMATIVA_PAISES.md sección México. Fuentes oficiales: DOF (dof.gob.mx), "
        "gob.mx/conasami, LFT (diputados.gob.mx). Verificar prima de riesgo IMSS (varía por "
        "empresa) y tabla exacta de tramos ISR 2026 antes de producción.",
        campos_extra={
            "uma_diaria_2026": 117.31,
            "tope_sbc_diario_25_uma": 2_932.75,
            "imss_patronal": {
                "cuota_fija": 0.2040,          # sobre 1 UMA, siempre
                "excedente_3uma": 0.0110,
                "dinero": 0.0070,
                "pensionados": 0.0105,
                "invalidez_vida": 0.0175,
                "guarderias": 0.0100,
                "retiro": 0.0200,
                "cesantia_vejez": 0.0524,      # aprox. tramo medio de la tabla progresiva — simplificación documentada
                "riesgo_trabajo": 0.0050,      # clase I aprox. — varía por empresa/actividad
                "infonavit": 0.0500,
            },
            "imss_empleado": {
                "excedente_3uma": 0.0040,
                "dinero": 0.0025,
                "pensionados": 0.00375,
                "invalidez_vida": 0.00625,
                "cesantia_vejez": 0.01125,
            },
            "indemnizacion_despido": "3 meses salario + 20 dias/año + prima antigüedad 12 dias/año (tope 2 SM)",
            "pago_periodicidad": "semanal (obreros) o quincenal (resto); mensual es ilegal",
        },
    )


class MexicoPayrollEngine(PayrollEngine):
    """Motor de nómina México (IMSS), basado en NORMATIVA_PAISES.md.

    Simplificaciones deliberadas (documentadas para quien continúe esto):
    - El Salario Base de Cotización (SBC) se aproxima al salario diario
      ordinario por los días trabajados, SIN integrar aguinaldo/prima
      vacacional/otras prestaciones al SBC (la ley exige integrarlas; se
      omite por simplicidad de este prototipo).
    - Cesantía y vejez patronal usa una tasa fija aproximada (5.24%) en vez
      de la tabla progresiva real por rango salarial (Ley del Seguro Social,
      art. 168) — verificar el tramo exacto antes de producción.
    - Prima de riesgo de trabajo (0.5%) es un valor de ejemplo clase I; en la
      realidad la determina cada empresa según su siniestralidad.
    - ISR se recibe como valor manual, igual que la retención en la fuente de
      Colombia — el cálculo automático por tabla del Art. 96 LISR no está
      implementado.
    - El aguinaldo NO se calcula en esta nómina mensual (se paga aparte en
      diciembre); en su lugar se muestra su provisión mensual equivalente
      (15/360 ≈ 4.17%) para que el panel consolidado tenga una cifra de
      provisión comparable a la de los demás países.

    Nota de nomenclatura: las claves de los dicts que retorna `calcular()`
    usan etiquetas i18n NEUTRAS (aporte_salud_empleado, etc.), no las siglas
    colombianas (EPS/FSP/ARL/SENA/ICBF) que ya tienen su propia traducción
    fija en `i18n/*.json` — reciclarlas aquí mostraría "SENA"/"ICBF" en un
    resultado mexicano, que es incorrecto.
    """

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

    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        extra = config.campos_extra
        tope_sbc_diario = extra["tope_sbc_diario_25_uma"]

        salario_contrato = float(empleado.get("salario_contrato", 0))
        dias_trabajados = float(novedades.get("dias_trabajados", 30))
        dias_incapacidad = float(novedades.get("dias_incapacidad", 0))
        bonos = float(novedades.get("bonos_percepciones", 0))
        descuento_infonavit = float(novedades.get("descuento_infonavit_credito", 0))
        prestamos = float(novedades.get("prestamos_descuentos", 0))
        isr = float(novedades.get("isr_retenido", 0))

        salario_diario = salario_contrato / 30
        dias_pagados = max(dias_trabajados - dias_incapacidad, 0)
        salario_devengado = salario_diario * dias_pagados

        sbc_diario = min(salario_diario, tope_sbc_diario)
        sbc = sbc_diario * dias_trabajados
        uma_periodo = extra["uma_diaria_2026"] * dias_trabajados

        p = extra["imss_patronal"]
        e = extra["imss_empleado"]
        excedente = max(sbc - 3 * uma_periodo, 0)

        total_devengado = salario_devengado + bonos

        aporte_salud_emp = excedente * e["excedente_3uma"] + sbc * e["dinero"] + sbc * e["pensionados"]
        aporte_pension_emp = sbc * e["invalidez_vida"] + sbc * e["cesantia_vejez"]
        total_deducciones = aporte_salud_emp + aporte_pension_emp + isr + descuento_infonavit + prestamos
        neto_pagado = total_devengado - total_deducciones

        cuota_fija = uma_periodo * p["cuota_fija"]
        salud_empleador = cuota_fija + sbc * p["dinero"] + sbc * p["pensionados"] + sbc * p["guarderias"] + excedente * p["excedente_3uma"]
        pension_empleador = sbc * p["invalidez_vida"] + sbc * p["cesantia_vejez"] + sbc * p["retiro"]
        riesgo_laboral = sbc * p["riesgo_trabajo"]
        vivienda_empleador = sbc * p["infonavit"]
        total_aportes_patronales = salud_empleador + pension_empleador + riesgo_laboral + vivienda_empleador

        provision_aguinaldo = salario_devengado * 0.0417

        return {
            "devengado": {
                "valor_salario_devengado": salario_devengado,
                "bonos_comisiones": bonos,
            },
            "deducciones": {
                "aporte_salud_empleado": aporte_salud_emp,
                "aporte_pension_empleado": aporte_pension_emp,
                "descuento_credito_vivienda": descuento_infonavit,
                "prestamos_avances": prestamos,
                "retencion_impuesto_renta": isr,
            },
            "aportes_patronales": {
                "salud_empleador": salud_empleador,
                "pension_empleador": pension_empleador,
                "aporte_riesgo_laboral_empleador": riesgo_laboral,
                "aporte_vivienda_empleador": vivienda_empleador,
            },
            "provisiones": {
                "prima": provision_aguinaldo,
            },
            "total_devengado": total_devengado,
            "total_deducciones": total_deducciones,
            "neto_pagado": neto_pagado,
            "total_aportes_patronales": total_aportes_patronales,
            "total_provisiones": provision_aguinaldo,
        }

    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Finiquito (renuncia) / Liquidación (despido), LFT arts. 48-50, 76-80, 87, 162.

        Simplificación: aguinaldo y vacaciones proporcionales del año en
        curso se calculan desde el 1-ene (o ingreso, si es más reciente) del
        año de retiro hasta la fecha de retiro — igual convención que la
        liquidación de Colombia para el periodo "no consignado"."""
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

        aguinaldo_proporcional = salario_diario * 15 * dias_periodo / 365
        prima_vacacional = salario_diario * dias_vacaciones_pendientes * 0.25
        vacaciones_pendientes = salario_diario * dias_vacaciones_pendientes

        antiguedad_dias = (fecha_retiro - fecha_ingreso).days + 1
        antiguedad_anos = antiguedad_dias / 365

        indemnizacion = 0.0
        aplica_indemnizacion = tipo_terminacion == "sin_justa_causa"
        if aplica_indemnizacion:
            tres_meses = salario_diario * 90
            veinte_dias_anio = salario_diario * 20 * antiguedad_anos
            tope_prima_antiguedad = 2 * config.salario_minimo / 30
            salario_prima_antiguedad = min(salario_diario, tope_prima_antiguedad)
            prima_antiguedad = salario_prima_antiguedad * 12 * antiguedad_anos
            indemnizacion = tres_meses + veinte_dias_anio + prima_antiguedad

        conceptos = {
            "salarios_pendientes": salarios_pendientes,
            "prima_servicios": aguinaldo_proporcional,
            "vacaciones_pendientes": vacaciones_pendientes + prima_vacacional,
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
