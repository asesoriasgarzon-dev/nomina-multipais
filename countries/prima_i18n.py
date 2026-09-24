"""Traducción de `CountryConfig.prima_o_aguinaldo` a los 5 idiomas de la UI.

Por qué existe este archivo: `prima_o_aguinaldo` en `stubs.py` es texto libre
en español (es la forma natural de guardar el dato investigado). Pero la
pantalla "Motor de nómina" de cada país se muestra en el idioma de quien la
ve — si un ejecutivo entra a Brasil en portugués y ese campo sale en español,
es exactamente el tipo de mezcla de idiomas que no debe pasar. Esta tabla
traduce el MISMO contenido ya investigado (no agrega ni cambia ningún dato
legal) a los idiomas que la interfaz soporta.

`traducir_prima(code, lang)` hace fallback al texto en español guardado en
`CountryConfig` si falta la traducción para ese idioma — nunca deja el campo
vacío, pero si ves texto en español en un idioma distinto significa que falta
agregarlo aquí.
"""

PRIMA_TRADUCIDA = {
    "MX": {
        "es": "Aguinaldo mínimo 15 días/año, antes del 20-dic",
        "en": "Minimum year-end bonus of 15 days' pay, before Dec 20",
        "pt": "13º salário mínimo de 15 dias/ano, antes de 20-dez",
        "zh": "最低年终奖15天工资/年，12月20日前发放",
        "zh-hk": "最低年終獎15天工資/年，12月20日前發放",
    },
    "PE": {
        "es": "Gratificaciones de julio y diciembre (1 remuneración c/u) + CTS en mayo/noviembre",
        "en": "July and December bonuses (1 month's pay each) + CTS severance fund in May/November",
        "pt": "Gratificações de julho e dezembro (1 remuneração cada) + CTS em maio/novembro",
        "zh": "7月和12月奖金（各1个月工资）+ 5月/11月CTS储备金",
        "zh-hk": "7月和12月獎金（各1個月工資）+ 5月/11月CTS儲備金",
    },
    "CL": {
        "es": "No hay aguinaldo legal general; gratificación legal si hay utilidades (25% remun. mensual, tope 4.75 IMM/año)",
        "en": "No general legal year-end bonus; legal profit-sharing bonus if the company has profits (25% of monthly pay, capped at 4.75 minimum wages/year)",
        "pt": "Não há 13º legal geral; gratificação legal se houver lucro (25% da remuneração mensal, limite de 4,75 salários mínimos/ano)",
        "zh": "无法定统一年终奖；若公司有利润则支付法定分红（月薪25%，上限4.75倍最低工资/年）",
        "zh-hk": "無法定統一年終獎；若公司有利潤則支付法定分紅（月薪25%，上限4.75倍最低工資/年）",
    },
    "BR": {
        "es": "13º salario (2 pagos: 50% hasta el 30-nov, saldo hasta el 20-dic)",
        "en": "13th-month salary (2 installments: 50% by Nov 30, balance by Dec 20)",
        "pt": "13º salário (2 pagamentos: 50% até 30-nov, saldo até 20-dez)",
        "zh": "第13薪（分2次支付：11月30日前付50%，12月20日前付余款）",
        "zh-hk": "第13薪（分2次支付：11月30日前付50%，12月20日前付餘款）",
    },
    "AR": {
        "es": "SAC (aguinaldo) semestral, 50% mejor remuneración del semestre",
        "en": "Semiannual SAC bonus, 50% of the best salary of the half-year",
        "pt": "SAC (13º) semestral, 50% do melhor salário do semestre",
        "zh": "半年一次的SAC奖金，为该半年最高工资的50%",
        "zh-hk": "半年一次的SAC獎金，為該半年最高工資的50%",
    },
    "EC": {
        "es": "Décimo tercero (hasta el 24-dic) y décimo cuarto (15-mar Costa / 15-ago Sierra)",
        "en": "13th-month bonus (by Dec 24) and 14th-month bonus (Mar 15 Coast / Aug 15 Highlands)",
        "pt": "13º salário (até 24-dez) e 14º salário (15-mar Costa / 15-ago Serra)",
        "zh": "第13薪（12月24日前）和第14薪（沿海地区3月15日／山区8月15日）",
        "zh-hk": "第13薪（12月24日前）和第14薪（沿海地區3月15日／山區8月15日）",
    },
}


def traducir_prima(code: str, lang: str, fallback: str) -> str:
    return PRIMA_TRADUCIDA.get(code, {}).get(lang, fallback)


# Mismo problema, mismo motivo: la fórmula de indemnización en campos_extra
# está en español libre y se mostraba tal cual en la pantalla de liquidación
# sin importar el idioma de quien la ve.
INDEMNIZACION_TRADUCIDA = {
    "MX": {
        "es": "3 meses salario + 20 días/año + prima antigüedad 12 días/año (tope 2 SM)",
        "en": "3 months' pay + 20 days/year + seniority bonus of 12 days/year (capped at 2x minimum wage)",
        "pt": "3 meses de salário + 20 dias/ano + prêmio de antiguidade de 12 dias/ano (limite de 2 salários mínimos)",
        "zh": "3个月工资 + 每年20天 + 工龄奖每年12天（上限为2倍最低工资）",
        "zh-hk": "3個月工資 + 每年20天 + 工齡獎每年12天（上限為2倍最低工資）",
    },
    "PE": {
        "es": "1.5 remuneraciones/año completo, tope 12 remuneraciones",
        "en": "1.5 months' pay per full year of service, capped at 12 months' pay",
        "pt": "1,5 remunerações por ano completo, limite de 12 remunerações",
        "zh": "每满一年支付1.5个月工资，上限为12个月工资",
        "zh-hk": "每滿一年支付1.5個月工資，上限為12個月工資",
    },
    "CL": {
        "es": "30 días/año de servicio, tope 11 años (330 días)",
        "en": "30 days' pay per year of service, capped at 11 years (330 days)",
        "pt": "30 dias por ano de serviço, limite de 11 anos (330 dias)",
        "zh": "每服务一年支付30天工资，上限11年（330天）",
        "zh-hk": "每服務一年支付30天工資，上限11年（330天）",
    },
    "BR": {
        "es": "aviso previo 30 días + 3 días/año (tope 90) + multa 40% FGTS total",
        "en": "30-day notice + 3 days/year (capped at 90) + 40% penalty on total FGTS balance",
        "pt": "aviso prévio de 30 dias + 3 dias/ano (limite de 90) + multa de 40% sobre o FGTS total",
        "zh": "提前30天通知 + 每年3天（上限90天）+ FGTS总额40%的罚金",
        "zh-hk": "提前30天通知 + 每年3天（上限90天）+ FGTS總額40%的罰款",
    },
    "AR": {
        "es": "1 mes mejor remuneración normal y habitual (excluye SAC/vacaciones/bonos) por año, tope 3x promedio convenio",
        "en": "1 month of the best regular monthly pay (excludes SAC/vacation/bonuses) per year, capped at 3x the collective agreement average",
        "pt": "1 mês da melhor remuneração normal e habitual (exclui SAC/férias/bônus) por ano, limite de 3x a média da convenção coletiva",
        "zh": "每年支付最佳月常规工资的1个月（不含SAC/假期/奖金），上限为集体协议平均值的3倍",
        "zh-hk": "每年支付最佳月常規工資的1個月（不含SAC/假期/獎金），上限為集體協議平均值的3倍",
    },
    "EC": {
        "es": "art. 188 (3 meses o 1 mes/año tope 25) + art. 185 (25% última remuneración/año completo)",
        "en": "art. 188 (3 months or 1 month/year, capped at 25) + art. 185 (25% of last pay per full year)",
        "pt": "art. 188 (3 meses ou 1 mês/ano, limite de 25) + art. 185 (25% da última remuneração/ano completo)",
        "zh": "第188条（3个月或每年1个月，上限25个月）+ 第185条（每满一年支付最后工资的25%）",
        "zh-hk": "第188條（3個月或每年1個月，上限25個月）+ 第185條（每滿一年支付最後工資的25%）",
    },
}

BASE_INDEMNIZACION_TRADUCIDA = {
    "EC": {
        "es": "mejor remuneración percibida en toda la relación laboral (no la última)",
        "en": "the best pay received during the entire employment relationship (not the last one)",
        "pt": "a melhor remuneração recebida durante todo o vínculo trabalhista (não a última)",
        "zh": "整个劳动关系期间获得的最高工资（不是最后一次工资）",
        "zh-hk": "整個勞動關係期間獲得的最高工資（不是最後一次工資）",
    },
}


def traducir_indemnizacion(code: str, lang: str, fallback: str) -> str:
    return INDEMNIZACION_TRADUCIDA.get(code, {}).get(lang, fallback)


def traducir_base_indemnizacion(code: str, lang: str, fallback: str) -> str:
    return BASE_INDEMNIZACION_TRADUCIDA.get(code, {}).get(lang, fallback)
