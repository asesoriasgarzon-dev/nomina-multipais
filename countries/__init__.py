from payroll_engine import capabilities

from .colombia import ColombiaConfig
from .colombia_normative import ColombiaNormativeEngine
from .mexico import MexicoConfig
from .peru import PeruConfig
from .chile import ChileConfig
from .brasil import BrasilConfig
from .argentina import ArgentinaConfig
from .ecuador import EcuadorConfig
from .normative_engines import (
    MexicoNormativeEngine, PeruNormativeEngine, ChileNormativeEngine,
    BrasilNormativeEngine, ArgentinaNormativeEngine, EcuadorNormativeEngine,
)
from .stubs import STUB_CONFIGS

# El cálculo mensual de los 7 países con motor corre sobre payroll_engine + config/payroll/.
# countries/<pais>.py solo aporta el formulario, los ejemplos DEMO y las etiquetas; el motor heredado (código)
# vive únicamente como fixture de regresión en tests/payroll_2026/legacy_fixtures/.
REGISTRY = {
    "CO": {"config": ColombiaConfig(), "engine": ColombiaNormativeEngine()},
    "MX": {"config": MexicoConfig(), "engine": MexicoNormativeEngine()},
    "PE": {"config": PeruConfig(), "engine": PeruNormativeEngine()},
    "CL": {"config": ChileConfig(), "engine": ChileNormativeEngine()},
    "BR": {"config": BrasilConfig(), "engine": BrasilNormativeEngine()},
    "AR": {"config": ArgentinaConfig(), "engine": ArgentinaNormativeEngine()},
    "EC": {"config": EcuadorConfig(), "engine": EcuadorNormativeEngine()},
}

for code, config in STUB_CONFIGS.items():
    REGISTRY[code] = {"config": config, "engine": None}


def get_country(code: str):
    entry = REGISTRY.get(code.upper())
    if entry is None:
        raise KeyError(f"País no registrado: {code}")
    return entry


def list_countries():
    return REGISTRY


def capability_info(code: str) -> dict:
    """Estado, cobertura y fechas de un contexto, leídos del Capability Manifest y de los datos
    normativos (nunca de valores escritos a mano en la UI)."""
    get_country(code)
    return capabilities.describe(code.upper())


def estado_contexto(code: str) -> str:
    """Estado REAL derivado del Capability Manifest: implementado | parcial | pendiente_validacion |
    no_implementado | consolidacion. Nunca se afirma 'activo' porque exista una clase."""
    try:
        return capability_info(code)["state"]
    except Exception:
        return "no_implementado"


def resumen_internacional() -> dict:
    """Conteos de la portada, siempre calculados de los manifiestos y datos normativos.

    `primer_matriz` / `primer_preparacion` dan un código concreto para enlazar cuando hay exactamente
    uno (sin hardcodear "HK"/"US" en la plantilla)."""
    infos = {code: capability_info(code) for code in REGISTRY}
    estados = {code: info["state"] for code, info in infos.items()}
    return {
        "total_contextos": len(REGISTRY),
        "paises_con_reglas": sum(1 for i in infos.values() if i["coverage"]["rules_implemented"] + i["coverage"]["rules_partial"] > 0),
        "paises_en_preparacion": sum(1 for e in estados.values() if e == "no_implementado"),
        "matrices": sum(1 for e in estados.values() if e == "consolidacion"),
        "motores_activos": sum(1 for e in estados.values() if e in ("implementado", "parcial", "pendiente_validacion")),
        "motores_parciales": sum(1 for e in estados.values() if e in ("parcial", "pendiente_validacion")),
        "motores_completos": sum(1 for code, i in infos.items() if i["complete_engine"]),
        "primer_matriz": next((c for c, e in estados.items() if e == "consolidacion"), None),
        "primer_preparacion": next((c for c, e in estados.items() if e == "no_implementado"), None),
    }
