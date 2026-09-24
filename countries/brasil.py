from datetime import date

from .base import CountryConfig, PayrollEngine


def BrasilConfig() -> CountryConfig:
    return CountryConfig(
        code="BR", name="Brasil", currency="BRL", idioma_default="pt",
        salario_minimo=1_621,
        jornada_semanal_horas=44,
        vacaciones_dias_anuales=30,
        prima_o_aguinaldo="13º salário (2 pagos: 50% hasta 30-nov, saldo hasta 20-dic)",
        nombre_liquidacion="Rescisão (TRCT — Termo de Rescisão do Contrato de Trabalho)",
        fuente="NORMATIVA_PAISES.md sección Brasil. Fuentes oficiales: planalto.gov.br, "
        "gov.br/previdencia, TST. Asume régimen tributario GENERAL — Simples Nacional/CPRB "
        "cambian por completo el % patronal, no implementados en este motor.",
        campos_extra={
            "inss_empleado_tramos": [
                (0, 1621.00, 0.075),
                (1621.01, 2902.84, 0.090),
                (2902.85, 4354.27, 0.120),
                (4354.28, 8475.55, 0.140),
            ],
            "inss_patronal_regimen_general": 0.20,
            "rat_empleador": 0.02,  # promedio del rango 1%-3% según actividad/FAP — parametrizar
            "sistema_s_empleador": 0.058,
            "fgts_empleador": 0.08,
            "multa_fgts_despido_sin_causa": 0.40,
            "indemnizacion_despido": "aviso previo 30 dias + 3 dias/año (tope 90) + multa 40% FGTS total",
            "pago_periodicidad": "mensual (hasta 5º dia util do mes seguinte)",
        },
    )


def _inss_empleado(base: float, tramos) -> float:
    """INSS del funcionário: progresivo por tramos (como un impuesto), no
    plano — se paga la tasa de cada tramo solo sobre la porción de salario
    que cae en él, tope en el techo del último tramo."""
    tope = tramos[-1][1]
    base = min(base, tope)
    total = 0.0
    for desde, hasta, tasa in tramos:
        if base > desde:
            porcion = min(base, hasta) - desde
            total += porcion * tasa
        else:
            break
    return total


class BrasilPayrollEngine(PayrollEngine):
    """Motor de folha de pagamento Brasil, basado en NORMATIVA_PAISES.md.

    Simplificaciones deliberadas:
    - Asume régimen tributario GENERAL para el empleador (INSS patronal 20%
      + RAT + Sistema S); Simples Nacional/CPRB tributan distinto y no están
      implementados.
    - RAT (Riesgo Ambiental del Trabajo) usa una tasa fija de ejemplo (2%);
      en la realidad depende de la actividad y el FAP de cada empresa.
    - FGTS se muestra como aporte patronal informativo (no es un descuento
      del funcionário, se deposita en su cuenta en Caixa) — no se modela la
      cuenta vinculada real, solo el monto mensual depositado.
    """

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

    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        extra = config.campos_extra
        salario_contrato = float(empleado.get("salario_contrato", 0))
        dias_trabajados = float(novedades.get("dias_trabajados", 30))
        bonos = float(novedades.get("bonos_comisiones", 0))
        prestamos = float(novedades.get("prestamos_avances", 0))
        irrf = float(novedades.get("retencion_impuesto_renta", 0))

        salario_devengado = salario_contrato / 30 * dias_trabajados
        total_devengado = salario_devengado + bonos

        base_inss = salario_devengado + bonos
        inss_emp = _inss_empleado(base_inss, extra["inss_empleado_tramos"])
        total_deducciones = inss_emp + prestamos + irrf
        neto_pagado = total_devengado - total_deducciones

        inss_patronal = base_inss * extra["inss_patronal_regimen_general"]
        rat = base_inss * extra["rat_empleador"]
        sistema_s = base_inss * extra["sistema_s_empleador"]
        fgts = base_inss * extra["fgts_empleador"]
        total_aportes_patronales = inss_patronal + rat + sistema_s + fgts

        decimo_terceiro_prov = salario_devengado / 12
        ferias_prov = salario_devengado / 12 * (4 / 3)
        total_provisiones = decimo_terceiro_prov + ferias_prov

        return {
            "devengado": {
                "valor_salario_devengado": salario_devengado,
                "bonos_comisiones": bonos,
            },
            "deducciones": {
                "aporte_pension_empleado": inss_emp,
                "prestamos_avances": prestamos,
                "retencion_impuesto_renta": irrf,
            },
            "aportes_patronales": {
                "pension_empleador": inss_patronal,
                "aporte_riesgo_laboral_empleador": rat,
                "aporte_capacitacion_empleador": sistema_s,
                "fondo_garantia_empleador": fgts,
            },
            "provisiones": {
                "prima": decimo_terceiro_prov,
                "vacaciones": ferias_prov,
            },
            "total_devengado": total_devengado,
            "total_deducciones": total_deducciones,
            "neto_pagado": neto_pagado,
            "total_aportes_patronales": total_aportes_patronales,
            "total_provisiones": total_provisiones,
        }

    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Rescisão: 13º proporcional + férias proporcionales +1/3 + aviso
        prévio + multa de 40% sobre el FGTS acumulado durante TODA la
        relación laboral (no solo el último período) cuando el despido es
        sin justa causa."""
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

        decimo_terceiro = salario_base * dias_periodo / 360
        ferias_proporcionais = salario_diario * dias_vacaciones_pendientes * (4 / 3)

        antiguedad_dias = (fecha_retiro - fecha_ingreso).days + 1
        antiguedad_anos = antiguedad_dias / 365
        meses_trabajados = antiguedad_dias / 30

        indemnizacion = 0.0
        aplica_indemnizacion = tipo_terminacion == "sin_justa_causa"
        if aplica_indemnizacion:
            aviso_previo = salario_base + salario_diario * 3 * antiguedad_anos
            aviso_previo = min(aviso_previo, salario_base + salario_diario * 60)  # tope 90 días totales
            fgts_acumulado = salario_base * config.campos_extra["fgts_empleador"] * meses_trabajados
            multa_fgts = fgts_acumulado * config.campos_extra["multa_fgts_despido_sin_causa"]
            indemnizacion = aviso_previo + multa_fgts

        conceptos = {
            "salarios_pendientes": salarios_pendientes,
            "prima_servicios": decimo_terceiro,
            "vacaciones_pendientes": ferias_proporcionais,
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
