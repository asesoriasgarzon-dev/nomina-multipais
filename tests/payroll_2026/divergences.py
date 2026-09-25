"""Diferencias entre la liquidación HEREDADA (fixture) y la NORMATIVA. Para cada caso se distinguen tres resultados:

  LEGACY_RESULT          lo que calculaba el código heredado (no es fuente de verdad)
  NORMATIVE_RESULT       lo que calcula el motor normativo
  EXPECTED_LEGAL_RESULT  lo que resulta de aplicar el texto de la norma, calculado aquí de forma independiente

`legacy == normative` NO prueba corrección jurídica. Si el resultado esperado no puede determinarse con una fuente
suficientemente sólida, la fila lo dice (PENDING_VERIFICATION) en vez de fingir una certeza."""

from decimal import Decimal, ROUND_HALF_UP

from countries import REGISTRY

from .legacy_fixtures.argentina import ArgentinaConfig, ArgentinaPayrollEngine
from .legacy_fixtures.brasil import BrasilConfig, BrasilPayrollEngine
from .legacy_fixtures.chile import ChileConfig, ChilePayrollEngine
from .legacy_fixtures.colombia import ColombiaConfig, ColombiaPayrollEngine
from .legacy_fixtures.ecuador import EcuadorConfig, EcuadorPayrollEngine
from .legacy_fixtures.mexico import MexicoConfig, MexicoPayrollEngine
from .legacy_fixtures.peru import PeruConfig, PeruPayrollEngine

D = Decimal


def q(x):
    return D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP)


LEGACY = {"PE": (PeruPayrollEngine, PeruConfig), "AR": (ArgentinaPayrollEngine, ArgentinaConfig), "CO": (ColombiaPayrollEngine, ColombiaConfig),
          "CL": (ChilePayrollEngine, ChileConfig), "MX": (MexicoPayrollEngine, MexicoConfig), "BR": (BrasilPayrollEngine, BrasilConfig),
          "EC": (EcuadorPayrollEngine, EcuadorConfig)}

# país -> (salario, ingreso, retiro, causa del formulario heredado, causa del formulario normativo)
SCENARIOS = {
    "PE": ("3000", "2024-03-10", "2026-07-20", "sin_justa_causa", "sin_justa_causa"),
    "AR": ("1000000", "2020-01-10", "2026-09-15", "sin_justa_causa", "sin_justa_causa"),
    "CO": ("2000000", "2023-02-10", "2026-09-15", "sin_justa_causa", "sin_justa_causa"),
    "CL": ("2000000", "2015-03-10", "2026-09-15", "sin_justa_causa", "necesidades_empresa"),
    "MX": ("30000", "2019-03-10", "2026-09-15", "sin_justa_causa", "sin_justa_causa"),
    "BR": ("5000", "2021-03-17", "2026-09-20", "sin_justa_causa", "sin_justa_causa"),
    "EC": ("1000", "2021-03-17", "2026-09-15", "sin_justa_causa", "sin_justa_causa"),
}


def liquidate(cc):
    """(legacy, normative) con la misma entrada de formulario (sin salarios ni vacaciones pendientes informados)."""
    salary, hire, end, cause_old, cause_new = SCENARIOS[cc]
    engine_cls, config_fn = LEGACY[cc]
    employee = {"nombre": "x", "identificacion": "y", "salario_contrato": salary}
    data = {"fecha_ingreso": hire, "fecha_retiro": end, "tipo_contrato": "indefinido", "tipo_terminacion": cause_old,
            "dias_faltantes_contrato": "0", "dias_vacaciones_pendientes": "0", "salarios_pendientes": "0", "salario_base": ""}
    legacy = engine_cls().liquidar(employee, data, config_fn())
    new_data = dict(data, tipo_terminacion=cause_new)
    normative = REGISTRY[cc]["engine"].liquidar(employee, new_data, REGISTRY[cc]["config"])
    normative.pop("_run", None)
    return legacy, normative


def line_amount(normative, concept):
    return next((D(str(l["amount"])) for l in normative["lineas"] if l["concept"] == concept), D(0))


# ---------------------------------------------------------------------------------------------------- resultados esperados
def expected_pe():
    """CTS: 1-may..20-jul = 2 meses y 20 días sobre 3.000 (art. 21 TUO CTS). Gratificación: julio no tiene un mes calendario completo
    (D.S. 005-2002-TR art. 5)."""
    cts = q(D(3000) * (D(2) / 12 + D(20) / 360))
    return {"cts": cts, "gratificacion": D("0.00")}


def expected_ar():
    """SAC: 1-ene..15-sep pertenece al 2.º semestre desde el 1-jul: 2,5 meses / 12 (art. 123 LCT)."""
    return {"sac": q(D(1_000_000) * D("2.5") / 12)}


def expected_co():
    base = D(2_000_000) + D(249_095)
    cesantias = q(base * 255 / 360)
    return {"cesantias": cesantias, "intereses": q(cesantias * D("0.12") * 255 / 360), "prima": q(base * 75 / 360)}


ROWS = [
    # país, concepto, motivo jurídico, fuente
    ("PE", "CTS y gratificación", "El heredado usaba la misma fórmula (año calendario/360) para ambas; la CTS es por semestre mayo-octubre / noviembre-abril "
     "(dozavos y treintavos) y la gratificación por meses calendario completos de enero-junio / julio-diciembre.",
     "TUO CTS D.S. 001-97-TR arts. 2 y 21; D.S. 005-2002-TR art. 5"),
    ("AR", "SAC proporcional", "El heredado contaba el SAC desde el 1-ene (año calendario) aunque el cese fuera en el 2.º semestre; el SAC se calcula por "
     "la fracción del semestre en curso (1/12 de lo devengado).", "LCT arts. 122-123 (InfoLeg)"),
    ("CO", "Cesantías, intereses y prima", "El heredado excluía el auxilio de transporte de la base de cesantías y prima; el normativo lo incluye "
     "(fuente de la inclusión PENDING_VERIFICATION) y liquida días base 360 desde el 1-ene / 1-jul.", "CST arts. 249, 253, 306; Ley 52/1975 (pendiente)"),
    ("CL", "Feriado proporcional, aviso previo y topes", "El heredado no calculaba el feriado proporcional y sumaba el aviso previo siempre; el normativo aplica el tope de "
     "330 días y de 90 UF y paga el aviso solo si no se dio.", "Código del Trabajo arts. 161, 163, 172, 73"),
    ("MX", "Aguinaldo, vacaciones, prima vacacional, prima de antigüedad", "El heredado solo daba aguinaldo (como 'prima'); el normativo agrega vacaciones, "
     "prima vacacional, indemnización de 3 meses + 20 días y prima de antigüedad con tope de 2 salarios mínimos.", "LFT arts. 48, 50, 76, 80, 87, 162"),
    ("BR", "13.º, vacaciones + 1/3, aviso, FGTS", "El heredado no calculaba vacaciones ni FGTS con el criterio de la CLT; el normativo aplica meses con 15+ días, "
     "fracción >14 días, aviso 30+3/año y multa del 40 %.", "Lei 4.090/62, CLT arts. 146-147, Lei 12.506/2011, Lei 8.036/90 art. 18"),
    ("EC", "Décimos, vacaciones, desahucio", "El heredado no distinguía décimo tercero/cuarto acumulados ni la bonificación del art. 185.",
     "Código del Trabajo arts. 111, 113, 185, 188"),
]
