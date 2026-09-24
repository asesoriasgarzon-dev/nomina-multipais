from datetime import date

from .base import CountryConfig, PayrollEngine


def ColombiaConfig() -> CountryConfig:
    return CountryConfig(
        code="CO",
        name="Colombia",
        currency="COP",
        idioma_default="es",
        salario_minimo=1_750_905,
        jornada_semanal_horas=42,  # desde 15-jul-2026 (Ley 2101 de 2021)
        vacaciones_dias_anuales=15,  # días hábiles/año
        prima_o_aguinaldo="Prima de servicios: 30 días de salario/año, pagada en dos semestres",
        fuente="Planilla de nómina agosto 2026 (archivo de referencia) + infografía "
        "comparativa laboral LATAM 2026 aportada por el usuario. Verificar SMMLV "
        "y auxilio de transporte contra el decreto oficial vigente antes de producción.",
        nombre_liquidacion="Liquidación de prestaciones sociales",
        campos_extra={
            "auxilio_transporte": 249_095,
            "tope_aportes_seg_social_smmlv": 25,
            "arl_clase_i": 0.00522,
            "exonerado_aportes_default": True,  # Ley 1607/2012: salud, SENA, ICBF
            "fsp_brackets": [  # (desde, hasta_exclusive, tasa) en múltiplos de SMMLV
                (4, 16, 0.010),
                (16, 17, 0.012),
                (17, 18, 0.014),
                (18, 19, 0.016),
                (19, 20, 0.018),
                (20, None, 0.020),
            ],
        },
    )


def _fsp_rate(base_prestacional: float, smmlv: float, brackets) -> float:
    if smmlv <= 0:
        return 0.0
    multiplo = base_prestacional / smmlv
    for desde, hasta, tasa in brackets:
        if multiplo >= desde and (hasta is None or multiplo < hasta):
            return tasa
    return 0.0


def _dias_360(inicio: date, fin: date) -> int:
    """Días entre dos fechas bajo la convención de 'año comercial' de 360
    días (cada mes cuenta como 30 días) que usa Colombia para liquidar
    cesantías, intereses y prima — NO son días calendario reales. +1 porque
    tanto el día de inicio como el de fin del periodo se cuentan (práctica
    estándar de las calculadoras de liquidación colombianas)."""
    d1 = min(inicio.day, 30)
    d2 = min(fin.day, 30)
    return (fin.year - inicio.year) * 360 + (fin.month - inicio.month) * 30 + (d2 - d1) + 1


class ColombiaPayrollEngine(PayrollEngine):
    """Motor de nómina Colombia, portado formula a formula del Excel de
    referencia (hoja 'Nomina mensual'). Simplificaciones deliberadas frente
    al Excel original, documentadas para quien continúe este prototipo:

    - Retención en la fuente: se recibe como valor manual (novedades['retefuente']),
      igual que en el Excel fuente. El cálculo automático por tabla UVT queda
      pendiente (ver README).
    - Cesantías: el Excel original tenía `cesantias = prima` (referencia de
      celda copiada, aparente error de plantilla). Aquí se calcula de forma
      independiente con la misma tasa legal (8.33%), que es lo correcto.
    - No se genera el resumen PILA (columnas AQ:AW del Excel); es un
      cruce de verificación para la planilla de aportes, no afecta la nómina.
    """

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

    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        extra = config.campos_extra
        smmlv = config.salario_minimo
        aux_transporte_full = extra["auxilio_transporte"]
        tope = extra["tope_aportes_seg_social_smmlv"] * smmlv
        exonerado = novedades.get("exonerado_aportes", extra["exonerado_aportes_default"])
        arl_tasa = novedades.get("arl_tasa", extra["arl_clase_i"])

        salario_contrato = float(empleado.get("salario_contrato", 0))
        dias_trabajados = float(novedades.get("dias_trabajados", 30))
        ajuste_trm = float(novedades.get("ajuste_trm", 0))
        incapacidad_dias_empresa = float(novedades.get("incapacidad_dias_empresa", 0))
        incapacidad_valor_eps = float(novedades.get("incapacidad_valor_eps", 0))
        vac_disfrutadas_dias = float(novedades.get("vac_disfrutadas_dias", 0))
        vac_no_habiles_dias = float(novedades.get("vac_no_habiles_dias", 0))
        vac_compensadas_dias = float(novedades.get("vac_compensadas_dias", 0))
        bonos_comisiones = float(novedades.get("bonos_comisiones", 0))
        bonificaciones_no_salariales = float(novedades.get("bonificaciones_no_salariales", 0))
        descuento_afc = float(novedades.get("descuento_afc", 0))
        aportes_voluntarios_pension = float(novedades.get("aportes_voluntarios_pension", 0))
        prestamos_avances = float(novedades.get("prestamos_avances", 0))
        retencion_fuente = float(novedades.get("retencion_fuente", 0))

        valor_salario_devengado = salario_contrato / 30 * dias_trabajados
        incapacidad_empresa = salario_contrato / 30 * incapacidad_dias_empresa * (2 / 3)
        valor_vac_disfrutadas = salario_contrato / 30 * (vac_disfrutadas_dias + vac_no_habiles_dias)
        valor_vac_compensadas = salario_contrato / 30 * vac_compensadas_dias
        auxilio_transporte = aux_transporte_full / 30 * dias_trabajados

        base_prestacional = (
            ajuste_trm
            + valor_salario_devengado
            + valor_vac_disfrutadas
            + valor_vac_compensadas
            + bonos_comisiones
            + incapacidad_empresa
            + incapacidad_valor_eps
        )
        total_devengado = base_prestacional + bonificaciones_no_salariales + auxilio_transporte

        base_aportes = min(base_prestacional, tope)
        aporte_salud_empleado = base_aportes * 0.04
        aporte_pension_empleado = base_aportes * 0.04
        fsp_tasa = _fsp_rate(base_prestacional, smmlv, extra["fsp_brackets"])
        aporte_fsp_empleado = base_prestacional * fsp_tasa

        total_deducciones = (
            aporte_salud_empleado
            + aporte_pension_empleado
            + aporte_fsp_empleado
            + retencion_fuente
            + descuento_afc
            + aportes_voluntarios_pension
            + prestamos_avances
        )
        neto_pagado = total_devengado - total_deducciones

        base_empleador = (
            valor_salario_devengado
            + incapacidad_empresa
            + incapacidad_valor_eps
            + valor_vac_disfrutadas
            + bonos_comisiones
        )
        salud_empleador = 0.0 if exonerado and base_prestacional <= tope else base_empleador * 0.085
        pension_empleador = base_empleador * 0.12
        arl = (valor_salario_devengado + bonos_comisiones) * arl_tasa
        caja_compensacion = (base_prestacional - incapacidad_empresa - incapacidad_valor_eps) * 0.04
        sena = 0.0 if exonerado else base_empleador * 0.02
        icbf = 0.0 if exonerado else base_empleador * 0.03
        total_aportes_patronales = salud_empleador + pension_empleador + arl + caja_compensacion + sena + icbf

        vacaciones_prov = base_empleador * 0.0417
        prima_prov = base_empleador * 0.0833
        cesantias_prov = base_empleador * 0.0833
        intereses_cesantias_prov = base_empleador * 0.01
        total_provisiones = vacaciones_prov + prima_prov + cesantias_prov + intereses_cesantias_prov

        return {
            "devengado": {
                "valor_salario_devengado": valor_salario_devengado,
                "incapacidad_empresa": incapacidad_empresa,
                "incapacidad_valor_eps": incapacidad_valor_eps,
                "valor_vac_disfrutadas": valor_vac_disfrutadas,
                "valor_vac_compensadas": valor_vac_compensadas,
                "bonos_comisiones": bonos_comisiones,
                "bonificaciones_no_salariales": bonificaciones_no_salariales,
                "auxilio_transporte": auxilio_transporte,
            },
            "deducciones": {
                "aporte_salud_empleado": aporte_salud_empleado,
                "aporte_pension_empleado": aporte_pension_empleado,
                "aporte_fsp_empleado": aporte_fsp_empleado,
                "retencion_fuente": retencion_fuente,
                "descuento_afc": descuento_afc,
                "aportes_voluntarios_pension": aportes_voluntarios_pension,
                "prestamos_avances": prestamos_avances,
            },
            "aportes_patronales": {
                "salud_empleador": salud_empleador,
                "pension_empleador": pension_empleador,
                "arl": arl,
                "caja_compensacion": caja_compensacion,
                "sena": sena,
                "icbf": icbf,
            },
            "provisiones": {
                "vacaciones": vacaciones_prov,
                "prima": prima_prov,
                "cesantias": cesantias_prov,
                "intereses_cesantias": intereses_cesantias_prov,
            },
            "total_devengado": total_devengado,
            "total_deducciones": total_deducciones,
            "neto_pagado": neto_pagado,
            "total_aportes_patronales": total_aportes_patronales,
            "total_provisiones": total_provisiones,
        }

    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Liquidación final del contrato (Código Sustantivo del Trabajo,
        arts. 249 cesantías, 306 prima, 65/CST y Ley 995/2005 intereses de
        cesantías, art. 64 indemnización por despido sin justa causa).

        Simplificaciones deliberadas de este prototipo:
        - Solo liquida el período NO consignado a fondo de cesantías (desde
          el 1-ene del año de retiro, o desde el ingreso si es más reciente)
          — en Colombia las cesantías de años anteriores ya se consignaron
          por ley el 14 de febrero de cada año, así que no vuelven a
          liquidarse aquí.
        - Vacaciones pendientes se reciben como dato manual (días hábiles
          acumulados sin disfrutar), no se deriva de un historial de
          vacaciones tomadas mes a mes (eso está fuera de este prototipo).
        - Salario base de liquidación = salario de contrato; si el empleado
          tuvo salario variable, debería usarse el promedio del último año
          (art. 132 CST) — no implementado todavía.
        """
        salario_base = float(datos.get("salario_base") or empleado.get("salario_contrato", 0))
        fecha_ingreso = date.fromisoformat(datos["fecha_ingreso"])
        fecha_retiro = date.fromisoformat(datos["fecha_retiro"])
        tipo_contrato = datos.get("tipo_contrato", "indefinido")
        tipo_terminacion = datos.get("tipo_terminacion", "renuncia")
        dias_faltantes_contrato = float(datos.get("dias_faltantes_contrato", 0))
        dias_vacaciones_pendientes = float(datos.get("dias_vacaciones_pendientes", 0))
        salarios_pendientes = float(datos.get("salarios_pendientes", 0))
        smmlv = config.salario_minimo

        inicio_ano = date(fecha_retiro.year, 1, 1)
        fecha_inicio_cesantias = max(fecha_ingreso, inicio_ano)
        dias_cesantias = max(_dias_360(fecha_inicio_cesantias, fecha_retiro), 0)
        cesantias = salario_base * dias_cesantias / 360
        # Fórmula estándar colombiana: interés = 12% anual prorrateado por
        # los mismos días del periodo de cesantías (no es un doble conteo:
        # aproxima el interés sobre el saldo promedio del periodo).
        intereses_cesantias = cesantias * dias_cesantias * 0.12 / 360

        inicio_semestre = date(fecha_retiro.year, 1, 1) if fecha_retiro.month <= 6 else date(fecha_retiro.year, 7, 1)
        fecha_inicio_prima = max(fecha_ingreso, inicio_semestre)
        dias_prima = max(_dias_360(fecha_inicio_prima, fecha_retiro), 0)
        prima = salario_base * dias_prima / 360

        vacaciones = salario_base / 30 * dias_vacaciones_pendientes

        antiguedad_dias = max(_dias_360(fecha_ingreso, fecha_retiro), 0)
        antiguedad_anos = antiguedad_dias / 360

        indemnizacion = 0.0
        aplica_indemnizacion = tipo_terminacion == "sin_justa_causa"
        if aplica_indemnizacion:
            salario_diario = salario_base / 30
            if tipo_contrato == "indefinido":
                anos_adicionales = max(antiguedad_anos - 1, 0)
                if salario_base < 10 * smmlv:
                    dias_indemnizacion = 30 + anos_adicionales * 20
                else:
                    dias_indemnizacion = 20 + anos_adicionales * 15
                indemnizacion = salario_diario * dias_indemnizacion
            elif tipo_contrato == "fijo":
                indemnizacion = salario_diario * dias_faltantes_contrato
            else:  # obra_labor
                indemnizacion = salario_diario * max(dias_faltantes_contrato, 15)

        conceptos = {
            "salarios_pendientes": salarios_pendientes,
            "cesantias": cesantias,
            "intereses_cesantias": intereses_cesantias,
            "prima_servicios": prima,
            "vacaciones_pendientes": vacaciones,
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
