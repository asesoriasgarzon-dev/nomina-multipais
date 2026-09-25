import json
import os

from markupsafe import Markup, escape

from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify

from countries import get_country, list_countries, estado_contexto, resumen_internacional, capability_info
from payroll_engine import explain as payroll_explain
from payroll_engine.errors import PayrollError
from payroll_engine.legacy_adapter import supported_form_options
from payroll_engine.loader import load_country
from payroll_engine.recalculate import historical_recalculation
from payroll_engine.run import reproduce as payroll_reproduce
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
if not os.environ.get("SECRET_KEY"):
    app.logger.warning("SECRET_KEY no está definida: se usa la clave de desarrollo. Defínala como variable de entorno en producción.")
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
    # estado (derivado del Capability Manifest): (css, icono, i18n título, i18n descripción)
    "implementado": ("estado-activo", "🟢", "estado_implementado_title", "estado_implementado_desc"),
    "parcial": ("estado-cargado", "🟡", "estado_parcial_title", "estado_parcial_desc"),
    "pendiente_validacion": ("estado-cargado", "🟠", "estado_pendiente_validacion_title", "estado_pendiente_validacion_desc"),
    "no_implementado": ("estado-preparacion", "🔵", "estado_no_implementado_title", "estado_no_implementado_desc"),
    "consolidacion": ("estado-matriz", "🟣", "estado_consolidacion_title", "estado_consolidacion_desc"),
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


def _concept_label(line):
    """Etiqueta de una línea del PayrollRun: clave i18n si existe; si no, el texto del concepto en el idioma actual
    (es como respaldo) y, por último, el código."""
    lang = getattr(request, "_lang", "es")
    if line.get("label_key"):
        return _translations[lang].get(line["label_key"], line["label_key"])
    label = line.get("label") or {}
    return label.get(lang) or label.get("es") or label.get("en") or line["concept"]


@app.context_processor
def inject_helpers():
    return {
        "t": lambda key: _translations[getattr(request, "_lang", "es")].get(key, key),
        "idioma_flag": _idioma_flag_html,
        "pais_flag": _pais_flag_html,
        "idioma_label": lambda lang: IDIOMA_LABEL.get(lang, lang.upper()),
        "estado_contexto": estado_contexto,
        "capability_info": capability_info,
        "estado_info": lambda code: ESTADO_INFO[estado_contexto(code)],
        "concept_label": _concept_label,
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
    engine = entry["engine"]
    if config.es_matriz:
        return render_template("matriz_home.html", config=config, pais=pais)
    return render_template(
        "pais_home.html", config=config, pais=pais, estado=estado_contexto(pais),
        tiene_ejemplo_novedades=bool(engine and engine.EJEMPLO_NOVEDADES),
        tiene_ejemplo_liquidacion=bool(engine and engine.EJEMPLO_LIQUIDACION),
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
        periodo = form.get("periodo", "")
        try:
            resultado = engine.calcular_periodo(empleado, novedades_data, config, periodo)
        except PayrollError as exc:
            return render_template(
                "novedades_form.html", config=config, pais=pais, campos=engine.NOVEDADES_CAMPOS,
                ejemplo=engine.EJEMPLO_NOVEDADES, errors=[f"{exc.code}: {exc.message}"] + [str(d) for d in exc.details],
                valores=form.to_dict(),
            ), 400
        run = resultado.pop("_run", None)
        nomina_id = models.guardar_nomina(pais, periodo, empleado, novedades_data, resultado)
        if run is not None:
            models.guardar_payroll_run(run.to_dict(), run._documents, nomina_id=nomina_id, es_demo=empleado["es_demo"])
        return redirect(url_for("resultado", nomina_id=nomina_id))

    return render_template(
        "novedades_form.html", config=config, pais=pais,
        campos=engine.NOVEDADES_CAMPOS, ejemplo=engine.EJEMPLO_NOVEDADES, errors=[], valores={},
    )


@app.route("/resultado/<int:nomina_id>")
def resultado(nomina_id):
    nomina = models.obtener_nomina(nomina_id)
    if nomina is None:
        return redirect(url_for("index"))
    config = get_country(nomina["pais"])["config"]
    run = models.obtener_payroll_run_por_nomina(nomina_id)
    return render_template("resultado.html", nomina=nomina, config=config, run=run)


@app.route("/run/<int:run_id>")
def payroll_run_view(run_id):
    run = models.obtener_payroll_run(run_id)
    if run is None:
        return redirect(url_for("index"))
    config = get_country(run["country"])["config"]
    explanation, explanation_text, evaluation = None, None, None
    line_id = request.args.get("line")
    rule_id = request.args.get("rule")
    try:
        if line_id:
            explanation = payroll_explain.explain_line(run, line_id)
            explanation_text = payroll_explain.render_text(explanation)
        if rule_id:
            evaluation = payroll_explain.explain_evaluation(run, rule_id)
    except KeyError:
        pass
    not_applied = [e for e in run["trace"]["evaluations"] if e["outcome"] == "NOT_APPLICABLE"]
    role_order = {"EARNING": 0, "EMPLOYEE_DEDUCTION": 1, "EMPLOYER_CONTRIBUTION": 2, "ACCRUAL": 3, "INFO": 4}
    ordered = sorted(run["result"]["lines"], key=lambda l: (role_order.get(l["role"], 9), l["rule_id"]))
    money_lines = [l for l in ordered if l["role"] != "INFO"]
    info_lines = [l for l in ordered if l["role"] == "INFO"]
    return render_template("payroll_run.html", run=run, config=config, explanation=explanation,
                           money_lines=money_lines, info_lines=info_lines,
                           explanation_text=explanation_text, evaluation=evaluation, not_applied=not_applied,
                           selected_line=line_id)


@app.route("/run/<int:run_id>/verify")
def payroll_run_verify(run_id):
    """Recalcula la corrida con SU snapshot normativo y SU entrada original; compara hashes."""
    run = models.obtener_payroll_run(run_id)
    if run is None:
        return jsonify({"error": "corrida inexistente"}), 404
    documents = models.obtener_snapshot_normativo(run["normative_snapshot"]["content_hash"])
    if documents is None:
        return jsonify({"same": False, "error": "snapshot normativo no disponible"}), 409
    result = payroll_reproduce(run, documents)
    result.pop("recomputed")
    return jsonify(result)


@app.route("/run/<int:run_id>/recalculate")
def payroll_run_recalculate(run_id):
    """Recalcula la corrida guardada con las reglas ACTUALES y devuelve la comparación (no guarda nada ni ajusta pagos)."""
    run = models.obtener_payroll_run(run_id)
    if run is None:
        return jsonify({"error": "corrida inexistente"}), 404
    try:
        result = historical_recalculation(run)
    except PayrollError as exc:
        return jsonify({"error": exc.message, "code": exc.code, "details": [str(d) for d in exc.details]}), 400
    comparison = result["comparison"]
    comparison["new_result_hash"] = result["run"].result_hash
    comparison["original_result_hash"] = run["result_hash"]
    return jsonify(comparison)


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
        try:
            resultado = engine.liquidar(empleado, datos, config)
        except PayrollError as exc:
            return render_template(
                "liquidacion_form.html", config=config, pais=pais, ejemplo=engine.EJEMPLO_LIQUIDACION,
                errors=[f"{exc.code}: {exc.message}"] + [str(d) for d in exc.details], valores=form.to_dict(),
                **_liquidacion_opciones(pais),
            ), 400
        run = resultado.pop("_run", None)
        if run is not None:
            resultado["run_db_id"] = models.guardar_payroll_run(run.to_dict(), run._documents, es_demo=empleado["es_demo"])
        liquidacion_id = models.guardar_liquidacion(pais, empleado, datos, resultado)
        return redirect(url_for("liquidacion_resultado", liquidacion_id=liquidacion_id))

    return render_template(
        "liquidacion_form.html", config=config, pais=pais, ejemplo=engine.EJEMPLO_LIQUIDACION, errors=[], valores={},
        **_liquidacion_opciones(pais),
    )


def _liquidacion_opciones(pais):
    """Causas y contratos del formulario que el país soporta (leídos del manifiesto normativo, no escritos aquí)."""
    causas, contratos = supported_form_options(load_country(pais.upper()).manifest)
    return {"opciones_terminacion": causas, "opciones_contrato": contratos}


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
