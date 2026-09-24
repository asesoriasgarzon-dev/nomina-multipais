import json
import os

from markupsafe import Markup, escape

from flask import Flask, render_template, request, redirect, url_for, session, send_file

from countries import get_country, list_countries, estado_contexto, resumen_internacional
from countries.prima_i18n import traducir_prima, traducir_indemnizacion, traducir_base_indemnizacion
import models
import exports
import geolocation
import personal
import alertas

app = Flask(__name__)
# En producción (Railway) se toma de la variable de entorno SECRET_KEY.
# El valor de respaldo solo aplica en desarrollo local — nunca se sube un
# secreto real al repositorio.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
models.init_db()

BASE_DIR = os.path.dirname(__file__)
I18N_DIR = os.path.join(BASE_DIR, "i18n")
SUPPORTED_LANGS = ["es", "en", "pt", "zh", "zh-hk"]

_translations = {}
for lang in SUPPORTED_LANGS:
    with open(os.path.join(I18N_DIR, f"{lang}.json"), encoding="utf-8") as f:
        _translations[lang] = json.load(f)

# Bandera por IDIOMA, no por país. Se renderiza como imagen (flagcdn.com),
# NO como emoji: el emoji de bandera (secuencia de "regional indicator
# symbols") depende de que el sistema operativo/navegador tenga esas fuentes
# instaladas, y en la práctica muchos entornos (Linux, algunos navegadores)
# lo muestran como texto plano ("US", "BR"...) en vez de la bandera —
# verificado en el navegador de pruebas de este proyecto. La imagen se ve
# igual en cualquier lado.
IDIOMA_FLAG_IMG = {
    "es": "es",
    "en": "us",
    "pt": "br",
    "zh": "cn",
    "zh-hk": "hk",
}


def _idioma_flag_html(lang):
    cc = IDIOMA_FLAG_IMG.get(lang)
    if not cc:
        return Markup("")
    return Markup(
        f'<img src="https://flagcdn.com/24x18/{escape(cc)}.png" '
        f'width="24" height="18" alt="{escape(lang)}" class="flag-img">'
    )


# Bandera por PAÍS — deliberadamente separada de IDIOMA_FLAG_IMG. Mezclarlas
# fue un error de una iteración anterior (España para "todo el español"
# aparecía en la tarjeta de México, Perú, etc. y podía leerse como "la
# bandera del país"). La tarjeta de cada país debe usar SU PROPIA bandera;
# el idioma se indica aparte, como texto, no como otra bandera.
PAIS_FLAG_IMG = {
    "CO": "co", "MX": "mx", "PE": "pe", "CL": "cl", "BR": "br",
    "AR": "ar", "EC": "ec", "US": "us", "HK": "hk",
}

IDIOMA_LABEL = {"es": "ES", "en": "EN", "pt": "PT", "zh": "简体", "zh-hk": "繁體中文"}


def _pais_flag_html(code):
    cc = PAIS_FLAG_IMG.get(code.upper())
    if not cc:
        return Markup("")
    return Markup(
        f'<img src="https://flagcdn.com/24x18/{escape(cc)}.png" '
        f'width="24" height="18" alt="{escape(code)}" class="flag-img">'
    )


ESTADO_INFO = {
    # nivel: (badge_css, "🟢"/etc., i18n key del título, i18n key de la descripción)
    "activo": ("estado-activo", "🟢", "estado_activo_title", "estado_activo_desc"),
    "cargado": ("estado-cargado", "🟡", "estado_cargado_title", "estado_cargado_desc"),
    "preparacion": ("estado-preparacion", "🔵", "estado_preparacion_title", "estado_preparacion_desc"),
    "matriz": ("estado-matriz", "🟣", "estado_matriz_title", "estado_matriz_desc"),
}


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def resolve_language(country_code=None):
    """Resuelve el idioma de la página, en este orden:
    1. ?lang= en la URL (permite forzar el idioma, útil para HQ en Hong Kong
       viendo el dashboard en mandarín aunque el dato sea de Colombia).
    2. Idioma guardado en sesión (incluye lo que haya detectado el paso 3 o 4
       en una visita anterior de la misma sesión, para no repetir la consulta
       de geolocalización en cada request).
    3. Si hay país de contexto (se está llenando el formulario de un país
       específico, ej. /novedades/BR): el idioma legal de ESE país, sin
       importar dónde esté físicamente quien lo llena — un contador
       brasileño de viaje en Bogotá sigue llenando el formulario de Brasil
       en portugués, no en español.
    4. Si NO hay país de contexto (página de inicio o panel consolidado):
       geolocalización por IP del visitante — "que al abrir el link, se abra
       en el idioma de donde está la persona en ese momento".
    5. Cabecera Accept-Language del navegador (si la geolocalización no
       pudo determinar nada, ej. en desarrollo local con IP privada).
    6. Español, como último recurso.
    """
    lang = request.args.get("lang")
    if lang in SUPPORTED_LANGS:
        session["lang"] = lang
        return lang
    if "lang" in session and session["lang"] in SUPPORTED_LANGS:
        return session["lang"]

    if country_code:
        try:
            country_lang = get_country(country_code)["config"].idioma_default
            if country_lang in SUPPORTED_LANGS:
                return country_lang
        except KeyError:
            pass
    else:
        geo_lang = geolocation.idioma_por_ip(_client_ip())
        if geo_lang in SUPPORTED_LANGS:
            session["lang"] = geo_lang
            return geo_lang

    best = request.accept_languages.best_match(SUPPORTED_LANGS)
    return best or "es"


@app.context_processor
def inject_helpers():
    return {
        "t": lambda key: _translations[getattr(request, "_lang", "es")].get(key, key),
        "idioma_flag": _idioma_flag_html,
        "pais_flag": _pais_flag_html,
        "idioma_label": lambda lang: IDIOMA_LABEL.get(lang, lang.upper()),
        "estado_contexto": estado_contexto,
        "estado_info": lambda code: ESTADO_INFO[estado_contexto(code)],
        "prima_localizada": lambda code, texto: traducir_prima(code, request._lang, texto),
        "indemnizacion_localizada": lambda code, texto: traducir_indemnizacion(code, request._lang, texto),
        "base_indemnizacion_localizada": lambda code, texto: traducir_base_indemnizacion(code, request._lang, texto),
    }


@app.before_request
def set_lang():
    country_code = request.view_args.get("pais") if request.view_args else None
    request._lang = resolve_language(country_code)


@app.route("/")
def index():
    return render_template("index.html", countries=list_countries(), resumen=resumen_internacional())


@app.route("/pais/<pais>")
def pais_home(pais):
    try:
        entry = get_country(pais)
    except KeyError:
        return redirect(url_for("index"))
    config = entry["config"]
    if config.es_matriz:
        return render_template("matriz_home.html", config=config, pais=pais)
    return render_template(
        "pais_home.html", config=config, pais=pais, estado=estado_contexto(pais)
    )


@app.route("/personal/<pais>", methods=["GET", "POST"])
def personal_pais(pais):
    try:
        entry = get_country(pais)
    except KeyError:
        return redirect(url_for("index"))
    config = entry["config"]

    if config.es_matriz:
        return redirect(url_for("pais_home", pais=pais))

    if request.method == "POST":
        form = request.form
        models.upsert_empleado(
            pais,
            identificacion=form.get("identificacion", "").strip(),
            nombre=form.get("nombre", "").strip(),
            cargo=form.get("cargo", "").strip(),
            salario_base=form.get("salario_base") or None,
            fecha_ingreso=form.get("fecha_ingreso") or None,
            estado=form.get("estado", "activo"),
        )
        return redirect(url_for("personal_pais", pais=pais))

    empleados = models.listar_empleados(pais)
    return render_template("personal.html", config=config, pais=pais, empleados=empleados)


@app.route("/personal/<pais>/plantilla.xlsx")
def personal_plantilla(pais):
    buf = personal.build_template_excel()
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"plantilla-personal-{pais}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/personal/<pais>/cargar", methods=["POST"])
def personal_cargar(pais):
    archivo = request.files.get("archivo")
    if archivo and archivo.filename:
        empleados = personal.parse_empleados_excel(archivo)
        for e in empleados:
            if e["identificacion"]:
                models.upsert_empleado(pais, **e)
    return redirect(url_for("personal_pais", pais=pais))


@app.route("/alertas")
def alertas_view():
    return render_template("alertas.html", alertas=alertas.generar_alertas())


@app.route("/novedades/<pais>", methods=["GET", "POST"])
def novedades(pais):
    try:
        entry = get_country(pais)
    except KeyError:
        return redirect(url_for("index"))

    config = entry["config"]
    engine = entry["engine"]

    if config.es_matriz:
        return redirect(url_for("pais_home", pais=pais))

    if engine is None:
        return render_template("pendiente.html", config=config, pais=pais)

    if request.method == "POST":
        form = request.form
        empleado = {
            "nombre": form.get("nombre", ""),
            "identificacion": form.get("identificacion", ""),
            "salario_contrato": form.get("salario_contrato", "0"),
            "es_demo": form.get("es_demo") == "1",
        }
        novedades_data = {
            key: form.get(key, default) for key, _, _, default in engine.NOVEDADES_CAMPOS
        }
        resultado = engine.calcular(empleado, novedades_data, config)
        periodo = form.get("periodo", "")
        nomina_id = models.guardar_nomina(pais, periodo, empleado, novedades_data, resultado)
        return redirect(url_for("resultado", nomina_id=nomina_id))

    return render_template(
        "novedades_form.html", config=config, pais=pais,
        campos=engine.NOVEDADES_CAMPOS, ejemplo=engine.EJEMPLO_NOVEDADES,
    )


@app.route("/resultado/<int:nomina_id>")
def resultado(nomina_id):
    nomina = models.obtener_nomina(nomina_id)
    if nomina is None:
        return redirect(url_for("index"))
    config = get_country(nomina["pais"])["config"]
    return render_template("resultado.html", nomina=nomina, config=config)


@app.route("/dashboard")
def dashboard():
    nominas = models.listar_nominas()
    liquidaciones = models.listar_liquidaciones()
    todos_empleados = models.listar_empleados()

    resumen = resumen_internacional()
    tabla_paises = []
    for code, entry in list_countries().items():
        if entry["config"].es_matriz:
            continue
        n_empleados = sum(1 for e in todos_empleados if e["pais"] == code)
        n_nominas = sum(1 for n in nominas if n["pais"] == code)
        tabla_paises.append({
            "code": code,
            "name": entry["config"].name,
            "currency": entry["config"].currency,
            "estado": estado_contexto(code),
            "empleados": n_empleados,
            "nominas": n_nominas,
        })

    return render_template(
        "dashboard.html",
        nominas=nominas,
        liquidaciones=liquidaciones,
        resumen=resumen,
        tabla_paises=tabla_paises,
        total_empleados=len(todos_empleados),
    )


@app.route("/liquidacion/<pais>", methods=["GET", "POST"])
def liquidacion(pais):
    try:
        entry = get_country(pais)
    except KeyError:
        return redirect(url_for("index"))

    config = entry["config"]
    engine = entry["engine"]

    if config.es_matriz:
        return redirect(url_for("pais_home", pais=pais))

    if engine is None:
        return render_template("liquidacion_pendiente.html", config=config, pais=pais)

    if request.method == "POST":
        form = request.form
        empleado = {
            "nombre": form.get("nombre", ""),
            "identificacion": form.get("identificacion", ""),
            "salario_contrato": form.get("salario_contrato", "0"),
            "es_demo": form.get("es_demo") == "1",
        }
        datos = {
            "fecha_ingreso": form.get("fecha_ingreso"),
            "fecha_retiro": form.get("fecha_retiro"),
            "tipo_contrato": form.get("tipo_contrato", "indefinido"),
            "tipo_terminacion": form.get("tipo_terminacion", "renuncia"),
            "dias_faltantes_contrato": form.get("dias_faltantes_contrato", "0"),
            "dias_vacaciones_pendientes": form.get("dias_vacaciones_pendientes", "0"),
            "salarios_pendientes": form.get("salarios_pendientes", "0"),
            "salario_base": form.get("salario_base", ""),
        }
        resultado = engine.liquidar(empleado, datos, config)
        liquidacion_id = models.guardar_liquidacion(pais, empleado, datos, resultado)
        return redirect(url_for("liquidacion_resultado", liquidacion_id=liquidacion_id))

    return render_template(
        "liquidacion_form.html", config=config, pais=pais, ejemplo=engine.EJEMPLO_LIQUIDACION
    )


@app.route("/liquidacion/resultado/<int:liquidacion_id>")
def liquidacion_resultado(liquidacion_id):
    liq = models.obtener_liquidacion(liquidacion_id)
    if liq is None:
        return redirect(url_for("index"))
    config = get_country(liq["pais"])["config"]
    return render_template("liquidacion_resultado.html", liq=liq, config=config)


def _t():
    return lambda key: _translations[request._lang].get(key, key)


@app.route("/dashboard/export.xlsx")
def dashboard_export_xlsx():
    nominas = models.listar_nominas()
    buf = exports.build_excel(nominas, _t(), _t()("dashboard_title"))
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"nomina-consolidado-{request._lang}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/dashboard/export.pdf")
def dashboard_export_pdf():
    nominas = models.listar_nominas()
    buf = exports.build_pdf(nominas, _t(), _t()("dashboard_title"), request._lang)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"nomina-consolidado-{request._lang}.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5057)
