"""Configuración de países pendientes de motor de cálculo.

México, Perú, Chile, Brasil, Argentina y Ecuador ya tienen motor completo
(ver `countries/<pais>.py` y `countries/__init__.py`). Aquí solo quedan los
países sin parámetros legales reales todavía: EE.UU. (placeholder, sin datos
cargados) y Hong Kong (la matriz, no genera nómina propia por diseño).

Para agregar un país nuevo: crear `countries/<pais>.py` con un
`CountryConfig` y una clase que implemente `PayrollEngine.calcular()` y
`liquidar()` (usar cualquiera de los ya implementados como plantilla), y
registrarlo en `countries/__init__.py`. No hace falta tocar el resto del
sistema (formulario web, dashboard, idiomas) — esa es la prueba de que la
arquitectura escala de 14 a potencialmente 150 países sin reescritura.
"""

from .base import CountryConfig

STUB_CONFIGS = {
    "US": CountryConfig(
        code="US", name="Estados Unidos", currency="USD", idioma_default="en",
        salario_minimo=0, jornada_semanal_horas=40, vacaciones_dias_anuales=0,
        prima_o_aguinaldo="No aplica (varía por estado/empresa)",
        nombre_liquidacion="Final Pay / Severance",
        fuente="Pendiente de datos — placeholder para gerentes de marca en EE.UU./Puerto Rico.",
    ),
    "HK": CountryConfig(
        code="HK", name="Hong Kong GSR Technology Limited (matriz)", currency="HKD",
        idioma_default="zh-hk", es_matriz=True,
        salario_minimo=0, jornada_semanal_horas=0, vacaciones_dias_anuales=0,
        prima_o_aguinaldo="No aplica — es la matriz, no genera nómina propia",
        fuente="Nombre real de la matriz confirmado por el usuario (2026-09-22). Hong Kong "
        "es jurisdicción y lengua distintas de China continental: cantonés hablado, chino "
        "tradicional (繁體中文) escrito, inglés como segundo idioma oficial — por eso usa su "
        "propio locale 'zh-hk' (tradicional) y no 'zh' (simplificado, China continental).",
    ),
}
