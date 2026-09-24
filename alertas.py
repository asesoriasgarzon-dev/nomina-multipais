"""Motor de alertas: cruza la ficha maestra de personal contra lo que se ha
digitado en novedades y liquidaciones. No bloquea nada (se decidió "permitir
pero alertar" en vez de exigir que el empleado ya esté en la ficha) — esto es
la capa de control/auditoría que Diego revisa, no un candado de captura.

Se calcula al vuelo en cada visita a /alertas (no se persiste): con el
volumen de datos de este sistema (nómina de ~15 empleados en 14 países) el
costo de recalcular es insignificante, y evita el problema de alertas
"viejas" quedando marcadas después de que alguien corrigió el dato.
"""

from datetime import date

import models

UMBRAL_DIFERENCIA_SALARIO = 0.15  # 15% — a partir de aquí se considera sospechoso


def _parse_fecha(s):
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _periodo_a_fecha(periodo):
    """Convierte el 'AAAA-MM' de un <input type=month> al primer día de ese mes."""
    try:
        anio, mes = periodo.split("-")
        return date(int(anio), int(mes), 1)
    except (ValueError, AttributeError, TypeError):
        return None


def generar_alertas():
    empleados_por_pais = {}
    for e in models.listar_empleados():
        empleados_por_pais.setdefault(e["pais"], {})[e["identificacion"]] = e

    nominas = models.listar_nominas()
    liquidaciones = models.listar_liquidaciones()

    liquidaciones_por_empleado = {}
    for liq in liquidaciones:
        ident = liq["empleado"].get("identificacion")
        if not ident:
            continue
        liquidaciones_por_empleado.setdefault((liq["pais"], ident), []).append(liq)

    alertas = []

    for key, liqs in liquidaciones_por_empleado.items():
        if len(liqs) > 1:
            pais, ident = key
            alertas.append({
                "tipo": "doble_liquidacion",
                "severidad": "alta",
                "pais": pais,
                "empleado": liqs[0]["empleado"].get("nombre", ident),
                "detalle": f"{len(liqs)} liquidaciones registradas para la identificación {ident} — verificar si es un duplicado o un reproceso.",
                "ref_tipo": "liquidacion",
                "ref_ids": [l["id"] for l in liqs],
            })

    for n in nominas:
        ident = n["empleado"].get("identificacion")
        pais = n["pais"]
        ficha = empleados_por_pais.get(pais, {}).get(ident) if ident else None

        if ident and ficha is None:
            alertas.append({
                "tipo": "empleado_no_encontrado",
                "severidad": "media",
                "pais": pais,
                "empleado": n["empleado"].get("nombre") or ident,
                "detalle": f"La identificación {ident} no está en la ficha de personal de {pais}.",
                "ref_tipo": "nomina",
                "ref_ids": [n["id"]],
            })
        elif ficha and ficha.get("salario_base") and n["empleado"].get("salario_contrato"):
            try:
                salario_ficha = float(ficha["salario_base"])
                salario_digitado = float(n["empleado"]["salario_contrato"])
                diff = abs(salario_digitado - salario_ficha) / salario_ficha if salario_ficha else 0
            except (TypeError, ValueError, ZeroDivisionError):
                diff = 0
            if diff > UMBRAL_DIFERENCIA_SALARIO:
                alertas.append({
                    "tipo": "salario_no_coincide",
                    "severidad": "media",
                    "pais": pais,
                    "empleado": n["empleado"].get("nombre") or ident,
                    "detalle": f"Salario digitado ({salario_digitado:,.0f}) difiere {diff:.0%} del registrado en la ficha ({salario_ficha:,.0f}).",
                    "ref_tipo": "nomina",
                    "ref_ids": [n["id"]],
                })

        if ident:
            # Se usa la fecha de retiro MÁS ANTIGUA entre todas sus
            # liquidaciones (si hay más de una, ese caso ya se marca aparte
            # como "doble_liquidacion") para no duplicar esta alerta.
            fechas_retiro = [
                _parse_fecha(liq["datos"].get("fecha_retiro"))
                for liq in liquidaciones_por_empleado.get((pais, ident), [])
            ]
            fechas_retiro = [f for f in fechas_retiro if f]
            periodo_nomina = _periodo_a_fecha(n.get("periodo"))
            if fechas_retiro and periodo_nomina and periodo_nomina > min(fechas_retiro):
                alertas.append({
                    "tipo": "nomina_tras_liquidacion",
                    "severidad": "alta",
                    "pais": pais,
                    "empleado": n["empleado"].get("nombre") or ident,
                    "detalle": f"Nómina del periodo {n.get('periodo')} es POSTERIOR a la fecha de retiro registrada ({min(fechas_retiro).isoformat()}) — posible pago a alguien que ya no debería estar activo.",
                    "ref_tipo": "nomina",
                    "ref_ids": [n["id"]],
                })

    for liq in liquidaciones:
        ident = liq["empleado"].get("identificacion")
        pais = liq["pais"]
        ficha = empleados_por_pais.get(pais, {}).get(ident) if ident else None
        if ident and ficha is None:
            alertas.append({
                "tipo": "empleado_no_encontrado",
                "severidad": "media",
                "pais": pais,
                "empleado": liq["empleado"].get("nombre") or ident,
                "detalle": f"La identificación {ident} no está en la ficha de personal de {pais}.",
                "ref_tipo": "liquidacion",
                "ref_ids": [liq["id"]],
            })

    orden_severidad = {"alta": 0, "media": 1, "baja": 2}
    alertas.sort(key=lambda a: orden_severidad.get(a["severidad"], 9))
    return alertas
