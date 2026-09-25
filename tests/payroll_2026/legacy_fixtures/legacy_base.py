from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class CountryConfig:
    """Parámetros legales de un país. Los valores deben verificarse contra la
    fuente oficial (ministerio de trabajo / gaceta) antes de usarse en producción.
    """
    code: str
    name: str
    currency: str
    idioma_default: str
    salario_minimo: float
    jornada_semanal_horas: float
    vacaciones_dias_anuales: float
    prima_o_aguinaldo: str
    fuente: str
    campos_extra: dict = field(default_factory=dict)
    # Nombre legal que usa cada país para el documento de liquidación final
    # del contrato (varía mucho: "finiquito" en México/Chile, "rescisão"/TRCT
    # en Brasil, "acta de finiquito" en Ecuador, etc.). Se muestra tal cual en
    # la interfaz para que quien procese la liquidación use el término correcto.
    nombre_liquidacion: str = "Liquidación"
    # True solo para la matriz (Hong Kong GSR Technology Limited): no es un
    # país con nómina local, es quien consolida lo que reportan los demás.
    # Se usa para que la UI la trate como "matriz/consolidación" en vez de
    # mostrarle los módulos de Novedades/Liquidación/Personal que no le
    # aplican (no tiene planilla propia).
    es_matriz: bool = False


class PayrollEngine(ABC):
    """Interfaz que debe implementar el motor de cálculo de cada país.

    Para agregar un país nuevo:
    1. Crear `countries/<pais>.py` con un `CountryConfig` y una clase que
       implemente `calcular()` y `liquidar()`, y defina `NOVEDADES_CAMPOS`.
    2. Registrarlo en `countries/__init__.py`.
    No se toca el resto de la aplicación (formulario, dashboard, i18n).

    NOVEDADES_CAMPOS: lista de (clave, clave_i18n_etiqueta, step_html, valor_por_defecto)
    que define los campos del formulario de "novedades" DE ESE PAÍS —
    cada país mantiene su propia terminología (Colombia sigue mostrando
    "EPS"/"AFC", no términos genéricos) en vez de forzar el formulario de un
    país sobre otro. `novedades_form.html` la recorre para dibujar el
    formulario, y `app.py` la usa para construir el dict de novedades desde
    el POST — así un país nuevo no requiere una plantilla HTML nueva.
    """

    NOVEDADES_CAMPOS: list = []

    # Escenarios DEMO para el botón "Cargar datos de ejemplo" — un dict con
    # los valores a precargar en cada formulario (llaves = nombres de campo
    # del HTML). Son datos ficticios de demostración, NO valores legales:
    # las tasas/fórmulas que se aplican sobre ellos son las reales del país.
    # Si están vacíos, el botón de ejemplo simplemente no se muestra.
    EJEMPLO_NOVEDADES: dict = {}
    EJEMPLO_LIQUIDACION: dict = {}

    def calcular_periodo(self, empleado: dict, novedades: dict, config: CountryConfig, periodo: str) -> dict:
        """Cálculo con el período (AAAA-MM). Los motores heredados lo ignoran; los motores
        normativos lo necesitan para resolver las reglas vigentes en esa fecha."""
        return self.calcular(empleado, novedades, config)

    @abstractmethod
    def calcular(self, empleado: dict, novedades: dict, config: CountryConfig) -> dict:
        """Recibe los datos del empleado y las novedades del mes, retorna un
        dict con las llaves: devengado, deducciones, aportes_patronales,
        provisiones, total_devengado, total_deducciones, neto_pagado,
        total_aportes_patronales, total_provisiones.
        Cada una de las primeras 4 es a su vez un dict {concepto: valor}.
        """
        raise NotImplementedError

    @abstractmethod
    def liquidar(self, empleado: dict, datos: dict, config: CountryConfig) -> dict:
        """Calcula la liquidación final al terminar el contrato: prestaciones
        proporcionales (cesantías/FGTS/CTS según el país, prima/aguinaldo
        proporcional, vacaciones pendientes) MÁS la indemnización por despido
        cuando `datos['tipo_terminacion']` así lo exige. Este es el cálculo
        de mayor riesgo jurídico del sistema — si se liquida con la fórmula
        equivocada (ej. aplicar indemnización a una renuncia, o usar la
        fórmula de un tipo de contrato que no corresponde), es exactamente
        el tipo de error que termina en demanda laboral.

        Retorna un dict con: conceptos (dict {concepto: valor}),
        total_prestaciones, indemnizacion, total_liquidacion,
        y aplica_indemnizacion (bool, para dejar explícito en la interfaz
        si el cálculo incluyó o no indemnización y por qué).
        """
        raise NotImplementedError
