"""La app real (Flask) sobre el motor normativo: flujo completo, errores tipificados, auditoría,
reproducibilidad y honestidad de la interfaz. Usa una base de datos temporal (tests/conftest.py)."""

import pytest

import app as application
from payroll_engine.loader import load_country
import models
from countries import REGISTRY, resumen_internacional

CO_DEMO = {"nombre": "Empleado Colombia Demo", "identificacion": "DEMO-CO-001", "periodo": "2026-09", "salario_contrato": "8000000",
           "es_demo": "1", "tipo_salario": "ORDINARY", "dias_trabajados": "28", "ajuste_trm": "0", "incapacidad_dias_empresa": "2",
           "incapacidad_valor_eps": "0", "vac_disfrutadas_dias": "0", "vac_no_habiles_dias": "0", "vac_compensadas_dias": "0",
           "bonos_comisiones": "0", "bonificaciones_no_salariales": "0", "descuento_afc": "0", "aportes_voluntarios_pension": "0",
           "prestamos_avances": "0", "retencion_fuente": "69001"}


@pytest.fixture()
def client():
    application.app.config["TESTING"] = True
    return application.app.test_client()


def post_run(client, cc="CO", data=None, lang="es"):
    """Envía un formulario de novedades y devuelve (nomina_id, run guardado)."""
    response = client.post(f"/novedades/{cc}?lang={lang}", data=data if data is not None else CO_DEMO)
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    nomina_id = int(response.headers["Location"].rsplit("/", 1)[1])
    return nomina_id, models.obtener_payroll_run_por_nomina(nomina_id)


def page(client, url, lang="es"):
    sep = "&" if "?" in url else "?"
    response = client.get(f"{url}{sep}lang={lang}")
    return response, response.get_data(as_text=True)


def test_portada_muestra_el_estado_real_y_nunca_motor_activo(client):
    response, body = page(client, "/")
    assert response.status_code == 200
    assert "Motor activo" not in body
    assert "Motor parcial (sin validación profesional)" in body
    assert "Consolidación (sin nómina local)" in body and "Sin motor (estructura preparada)" in body


def test_resumen_global_sale_de_los_manifiestos():
    resumen = resumen_internacional()
    assert resumen["total_contextos"] == 9 and resumen["motores_activos"] == 7
    assert resumen["paises_con_reglas"] == 7          # EE. UU. tiene reglas cargadas pero todas NOT_IMPLEMENTED: no cuenta
    assert resumen["matrices"] == 1 and resumen["primer_matriz"] == "HK" and resumen["primer_preparacion"] == "US"


@pytest.mark.parametrize("cc", ["CO", "MX", "PE", "CL", "BR", "AR", "EC", "US", "HK"])
def test_cada_pais_muestra_el_panel_de_capacidades_con_datos_reales(client, cc):
    response, body = page(client, f"/pais/{cc}")
    assert response.status_code == 200
    assert "Estado real del motor y cobertura normativa" in body and "Fecha normativa" in body
    assert "2026-09-24" in body and load_country(cc).ruleset_version in body


def test_co_muestra_cobertura_y_capacidades(client):
    _, body = page(client, "/pais/CO")
    assert "Motor normativo (reglas versionadas)" in body
    assert "Parcial" in body and "Pendiente de validación" in body
    assert "sin validación profesional" in body


def test_hk_no_es_nomina_local(client):
    response, body = page(client, "/pais/HK")
    assert "Consolidación (sin nómina local)" in body and "Sin motor de nómina" in body
    for route in ("novedades", "liquidacion", "personal"):
        r = client.get(f"/{route}/HK")
        assert r.status_code == 302 and r.headers["Location"].endswith("/pais/HK")


def test_us_pagina_pendiente_con_su_estado_real(client):
    response, body = page(client, "/novedades/US")
    assert response.status_code == 200 and "Sin motor (estructura preparada)" in body and "Estado real del motor" in body


def test_formulario_de_colombia_ofrece_tipo_de_salario_integral(client):
    _, body = page(client, "/novedades/CO")
    assert 'name="tipo_salario"' in body and "Integral" in body and "Ordinario" in body


def test_flujo_completo_colombia_demo_con_auditoria_y_reproduccion(client):
    nomina_id, run = post_run(client)
    _, body = page(client, f"/resultado/{nomina_id}")
    assert "7049226.26" in body                       # neto normativo (sin auxilio: 8 M > 2 SMMLV)
    assert "232488.67" not in body                    # el auxilio que el motor heredado pagaba a 8 M
    assert "Ver auditoría y explicación" in body and "WITHHOLDING_TAX_CALC" in body

    run_url = f"/run/{run['db_id']}"
    _, run_body = page(client, run_url)
    assert "Auditoría del cálculo" in run_body and "L001" in run_body and "Reglas evaluadas que no aplicaron" in run_body
    _, explain_body = page(client, f"{run_url}?line=L001")
    assert "CO.BASE_SALARY.1" in explain_body
    verify = client.get(f"{run_url}/verify").get_json()
    assert verify["same"] is True and verify["stored_hash"] == verify["recomputed_hash"]


def test_el_auxilio_de_transporte_no_aparece_para_8_millones(client):
    nomina_id, _ = post_run(client)
    nomina = models.obtener_nomina(nomina_id)
    assert "auxilio_transporte" not in nomina["resultado"]["devengado"]
    assert nomina["resultado"]["neto_pagado"] == pytest.approx(7049226.26, abs=0.01)   # retención CALCULADA (art. 383 ET) en vez de los 69.001 digitados


def test_la_ficha_de_una_corrida_guarda_snapshots_y_versiones(client):
    _, run = post_run(client)
    assert run["engine_version"] == "1.1.0" and run["ruleset_version"] == "CO-2026.2.1"
    assert run["input_snapshot"]["payload"]["employment"]["monthly_salary"] == "8000000"
    assert models.obtener_snapshot_normativo(run["normative_snapshot"]["content_hash"])["manifest"]["country"] == "CO"
    assert run["es_demo"] is True


@pytest.mark.parametrize("mod,needle", [
    ({"dias_trabajados": "45"}, "superan 30"),
    ({"salario_contrato": "-1000"}, "negativo"),
    ({"dias_trabajados": "abc"}, "numéricos"),
    ({"tipo_salario": "INTEGRAL", "salario_contrato": "20000000", "dias_trabajados": "30", "incapacidad_dias_empresa": "0"}, "13 SMMLV"),
    ({"periodo": "2025-12"}, "no hay reglas vigentes"),
])
def test_errores_tipificados_en_vez_de_500(client, mod, needle):
    response = client.post("/novedades/CO?lang=es", data=dict(CO_DEMO, **mod))
    body = response.get_data(as_text=True)
    assert response.status_code == 400 and "No se pudo calcular" in body and needle in body
    assert 'value="Empleado Colombia Demo"' in body                # el formulario conserva lo digitado


def test_integral_en_la_frontera_de_13_smmlv_desde_la_app(client):
    ok = dict(CO_DEMO, tipo_salario="INTEGRAL", salario_contrato="22761765", dias_trabajados="30", incapacidad_dias_empresa="0")
    assert client.post("/novedades/CO?lang=es", data=ok).status_code == 302
    bad = dict(ok, salario_contrato="22761764")
    assert client.post("/novedades/CO?lang=es", data=bad).status_code == 400


@pytest.mark.parametrize("cc", ["MX", "PE", "CL", "BR", "AR", "EC"])
def test_los_demos_de_cada_pais_calculan_con_el_motor_normativo(client, cc):
    example = REGISTRY[cc]["engine"].EJEMPLO_NOVEDADES
    data = {k: v for k, v in example.items()}
    data.update({"periodo": "2026-09", "es_demo": "1"})
    response = client.post(f"/novedades/{cc}?lang=es", data=data)
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    nomina_id = int(response.headers["Location"].rsplit("/", 1)[1])
    run = models.obtener_payroll_run_por_nomina(nomina_id)
    assert run["country"] == cc and run["ruleset_version"] == load_country(cc).ruleset_version
    assert client.get(f"/run/{run['db_id']}/verify").get_json()["same"] is True


def test_chile_aplica_el_tope_imponible_en_uf_y_ya_no_queda_incompleta(client):
    example = REGISTRY["CL"]["engine"].EJEMPLO_NOVEDADES
    data = dict(example, periodo="2026-09", es_demo="1")
    response = client.post("/novedades/CL?lang=es", data=data)
    _, body = page(client, response.headers["Location"])
    assert "INCOMPLETA" not in body and "CL.CAP_90_UF" not in body


@pytest.mark.parametrize("lang", ["es", "en", "pt", "zh", "zh-hk"])
def test_las_paginas_nuevas_no_muestran_claves_sin_traducir(client, lang):
    _, run = post_run(client, lang=lang)
    run_url = f"/run/{run['db_id']}"
    for url in ("/", "/pais/CO", "/pais/US", "/pais/HK", run_url, f"{run_url}?line=L001", "/novedades/CO"):
        response, body = page(client, url, lang)
        assert response.status_code == 200, (lang, url)
        for raw in ("cap_", "estado_parcial", "run_title", "run_status_", "exp_rule", "capname_", "opt_ordinary", "form_errors"):
            assert raw not in body, (lang, url, raw)


def test_corrida_inexistente(client):
    assert client.get("/run/99999").status_code == 302
    assert client.get("/run/99999/verify").status_code == 404
