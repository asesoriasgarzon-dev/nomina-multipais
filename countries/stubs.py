"""Configuración de contextos SIN motor de nómina local.

México, Perú, Chile, Brasil, Argentina, Ecuador y Colombia calculan sobre el motor normativo (ver
`countries/normative_engines.py`). Aquí solo quedan EE. UU. (estructura preparada: sin reglas estatales ni locales
investigadas) y Hong Kong (la matriz: consolida, no genera nómina propia por diseño; `local_payroll_engine=false`).

Estos objetos son solo ETIQUETAS de interfaz. Los datos normativos de cada contexto (incluida su falta de motor) viven
en config/payroll/<PAIS>/2026/manifest.json.
"""

from .base import CountryConfig

STUB_CONFIGS = {
    "US": CountryConfig(
        code="US", name="Estados Unidos", currency="USD", idioma_default="en",
        nombre_liquidacion="Final Pay / Severance",
    ),
    "HK": CountryConfig(
        code="HK", name="Hong Kong GSR Technology Limited (matriz)", currency="HKD",
        idioma_default="zh-hk", es_matriz=True,
    ),
}
