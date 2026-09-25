from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CountryConfig:
    """Etiquetas de un contexto para la interfaz. NO contiene parámetros legales (salario mínimo, tasas, jornada,
    topes...): esos viven versionados y con fuente en config/payroll/<PAIS>/<AÑO>/."""
    code: str
    name: str
    currency: str
    idioma_default: str
    # Nombre legal que usa cada país para el documento de liquidación final (finiquito, rescisão, TRCT...).
    nombre_liquidacion: str = "Liquidación"
    # True solo para la matriz (Hong Kong GSR Technology Limited): consolida lo que reportan los demás países.
    es_matriz: bool = False


class FormSpec:
    """Campos del formulario de novedades y escenarios DEMO de un país. Datos de interfaz, no reglas legales.

    NOVEDADES_CAMPOS: lista de (clave, clave_i18n_etiqueta, step_html, valor_por_defecto). EJEMPLO_*: valores
    ficticios que precarga el botón "Cargar datos de ejemplo"."""

    NOVEDADES_CAMPOS: list = []
    EJEMPLO_NOVEDADES: dict = {}
    EJEMPLO_LIQUIDACION: dict = {}


class PayrollEngine(FormSpec, ABC):
    """Interfaz que la app espera de un motor de país. Los motores reales son adaptadores del motor normativo
    (countries/normative_engines.py): traducen formulario -> PayrollRun -> resultado de pantalla, sin fórmulas."""

    def calcular_periodo(self, empleado: dict, novedades: dict, config: CountryConfig, periodo: str) -> dict:
        return self.calcular(empleado, novedades, config)

    @abstractmethod
    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        raise NotImplementedError

    @abstractmethod
    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        raise NotImplementedError
