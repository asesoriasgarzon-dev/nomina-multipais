from .colombia import ColombiaConfig, ColombiaPayrollEngine
from .mexico import MexicoConfig, MexicoPayrollEngine
from .peru import PeruConfig, PeruPayrollEngine
from .chile import ChileConfig, ChilePayrollEngine
from .brasil import BrasilConfig, BrasilPayrollEngine
from .argentina import ArgentinaConfig, ArgentinaPayrollEngine
from .ecuador import EcuadorConfig, EcuadorPayrollEngine
from .stubs import STUB_CONFIGS

REGISTRY = {
    "CO": {"config": ColombiaConfig(), "engine": ColombiaPayrollEngine()},
    "MX": {"config": MexicoConfig(), "engine": MexicoPayrollEngine()},
    "PE": {"config": PeruConfig(), "engine": PeruPayrollEngine()},
    "CL": {"config": ChileConfig(), "engine": ChilePayrollEngine()},
    "BR": {"config": BrasilConfig(), "engine": BrasilPayrollEngine()},
    "AR": {"config": ArgentinaConfig(), "engine": ArgentinaPayrollEngine()},
    "EC": {"config": EcuadorConfig(), "engine": EcuadorPayrollEngine()},
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


def estado_contexto(code: str) -> str:
    """Estado REAL de un contexto — nunca se marca 'activo' o 'cargado' a
    mano, se deriva de si existe motor y si hay parámetros legales cargados,
    para que la demo nunca muestre un estado que no corresponda al código.

    - "activo": tiene motor de cálculo (`PayrollEngine` implementado).
    - "matriz": es la casa matriz (Hong Kong), no un país con nómina local.
    - "cargado": tiene parámetros legales (`CountryConfig`) pero sin motor.
    - "preparacion": ni parámetros legales ni motor (placeholder puro).
    """
    entry = get_country(code)
    config = entry["config"]
    if config.es_matriz:
        return "matriz"
    if entry["engine"] is not None:
        return "activo"
    if config.salario_minimo:
        return "cargado"
    return "preparacion"


def resumen_internacional() -> dict:
    """Conteos para el resumen 'Global Payroll' de la portada — siempre
    calculados a partir de REGISTRY, nunca hardcodeados, para que agregar o
    quitar un país actualice el resumen automáticamente.

    `primer_matriz` / `primer_preparacion` dan un código de país concreto
    para que la tarjeta correspondiente pueda enlazar directo a él cuando
    hay exactamente uno (el caso normal hoy) — sin hardcodear "HK"/"US" en
    la plantilla, así sigue siendo correcto si el registro cambia."""
    estados = {code: estado_contexto(code) for code in REGISTRY}
    return {
        "total_contextos": len(REGISTRY),
        "paises_con_reglas": sum(1 for e in estados.values() if e in ("activo", "cargado")),
        "paises_en_preparacion": sum(1 for e in estados.values() if e == "preparacion"),
        "matrices": sum(1 for e in estados.values() if e == "matriz"),
        "motores_activos": sum(1 for e in estados.values() if e == "activo"),
        "primer_matriz": next((c for c, e in estados.items() if e == "matriz"), None),
        "primer_preparacion": next((c for c, e in estados.items() if e == "preparacion"), None),
    }
