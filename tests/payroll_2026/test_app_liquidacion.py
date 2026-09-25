"""La liquidación de la app corre sobre el motor normativo: formulario filtrado por país, errores tipificados, resultado con
líneas etiquetadas, auditoría reproducible y páginas sin claves de traducción faltantes."""

import re

import pytest

import app as application
import models
from countries import REGISTRY

COUNTRIES = ["CO", "MX", "PE", "CL", "BR", "AR", "EC"]


@pytest.fixture()
def client():
    application.app.config["TESTING"] = True
    return application.app.test_client()


def post_liq(client, cc, data=None, lang="es"):
    data = dict(REGISTRY[cc]["engine"].EJEMPLO_LIQUIDACION, es_demo="1") if data is None else data
    return client.post(f"/liquidacion/{cc}?lang={lang}", data=data)


def options(body):
    return re.findall(r'<option value="([a-z_]+)"', body)


@pytest.mark.parametrize("cc", COUNTRIES)
def test_el_ejemplo_demo_de_cada_pais_liquida_y_genera_auditoria_reproducible(client, cc):
    response = post_liq(client, cc)
    assert response.status_code == 302
    page = client.get(response.headers["Location"] + "?lang=es")
    body = page.get_data(as_text=True)
    assert page.status_code == 200 and "liq_engine_notice" not in body
    assert "Ninguna regla tiene validación profesional" in body
    run_id = re.search(r"/run/(\d+)", body).group(1)
    assert client.get(f"/run/{run_id}?lang=es").status_code == 200
    verify = client.get(f"/run/{run_id}/verify").get_json()
    assert verify["same"] is True
    run = models.obtener_payroll_run(int(run_id))
    assert run["run_type"] == "TERMINATION" and run["country"] == cc


@pytest.mark.parametrize("cc,expected_absent,expected_present", [
    ("CO", ["desahucio", "necesidades_empresa"], ["sin_justa_causa", "obra_labor", "despido_indirecto"]),
    ("CL", ["sin_justa_causa", "despido_indirecto"], ["necesidades_empresa", "mutuo_acuerdo"]),
    ("EC", ["necesidades_empresa"], ["desahucio", "sin_justa_causa"]),
    ("BR", ["obra_labor", "desahucio"], ["despido_indirecto", "sin_justa_causa"]),
])
def test_el_formulario_solo_ofrece_las_causas_y_contratos_que_el_pais_soporta(client, cc, expected_absent, expected_present):
    body = client.get(f"/liquidacion/{cc}?lang=es").get_data(as_text=True)
    found = options(body)
    assert all(o in found for o in expected_present)
    assert not any(o in found for o in expected_absent)


def test_una_causa_no_soportada_devuelve_400_con_el_error_y_conserva_lo_digitado(client):
    data = dict(REGISTRY["CL"]["engine"].EJEMPLO_LIQUIDACION, es_demo="1", tipo_terminacion="sin_justa_causa", nombre="Ana")
    response = post_liq(client, "CL", data)
    body = response.get_data(as_text=True)
    assert response.status_code == 400 and "no está soportada para CL" in body and 'value="Ana"' in body


def test_fechas_incoherentes_devuelven_error_sin_guardar(client):
    before = len(models.listar_liquidaciones())
    data = dict(REGISTRY["PE"]["engine"].EJEMPLO_LIQUIDACION, es_demo="1", fecha_ingreso="2026-12-31", fecha_retiro="2026-01-01")
    response = post_liq(client, "PE", data)
    assert response.status_code == 400 and len(models.listar_liquidaciones()) == before


def test_el_salario_pendiente_informado_no_se_cuenta_dos_veces(client):
    data = dict(REGISTRY["CO"]["engine"].EJEMPLO_LIQUIDACION, es_demo="1", salarios_pendientes="500000")
    response = post_liq(client, "CO", data)
    liq = models.obtener_liquidacion(int(response.headers["Location"].rsplit("/", 1)[1]))
    concepts = {l["concept"]: l["amount"] for l in liq["resultado"]["lineas"]}
    assert concepts["CO_SALARIOS_PENDIENTES"] == 500000.0 and "CO_SALARIO_MES_TERMINACION" not in concepts


def test_el_resultado_guardado_es_json_serializable_con_lineas_y_totales(client):
    response = post_liq(client, "AR")
    liq = models.obtener_liquidacion(int(response.headers["Location"].rsplit("/", 1)[1]))
    res = liq["resultado"]
    assert res["motor"] == "normativo" and res["run_status"] in ("COMPLETE", "COMPLETE_WITH_WARNINGS")
    assert res["total_liquidacion"] == pytest.approx(sum(l["amount"] * (-1 if l["role"] == "EMPLOYEE_DEDUCTION" else 1)
                                                        for l in res["lineas"] if l["role"] in ("EARNING", "EMPLOYEE_DEDUCTION")))
    assert isinstance(res["run_db_id"], int)


def test_una_liquidacion_heredada_ya_guardada_sigue_mostrandose(client):
    legacy = {"conceptos": {"cesantias": 100.0, "prima_servicios": 50.0}, "total_prestaciones": 150.0, "indemnizacion": 0.0,
              "aplica_indemnizacion": False, "total_liquidacion": 150.0, "antiguedad_anos": 1.0}
    liq_id = models.guardar_liquidacion("CO", {"nombre": "Vieja", "identificacion": "1", "salario_contrato": "1", "es_demo": True}, {}, legacy)
    body = client.get(f"/liquidacion/resultado/{liq_id}?lang=es").get_data(as_text=True)
    assert "motor heredado" in body and "150.00" in body


@pytest.mark.parametrize("lang", ["es", "en", "pt", "zh", "zh-hk"])
def test_las_paginas_de_liquidacion_no_muestran_claves_sin_traducir(client, lang):
    for cc in ("CO", "CL", "EC"):
        response = post_liq(client, cc, lang=lang)
        pages = [f"/liquidacion/{cc}", response.headers["Location"]]
        for url in pages:
            sep = "&" if "?" in url else "?"
            body = client.get(f"{url}{sep}lang={lang}").get_data(as_text=True)
            for raw in ("liq_engine_notice", "term_", "contrato_", "comp_", "cap_status", "run_status_", "costo_empleador"):
                assert raw not in body, (lang, url, raw)


def test_la_auditoria_de_una_liquidacion_muestra_etiquetas_por_idioma_y_el_concepto(client):
    response = post_liq(client, "PE")
    body = client.get(response.headers["Location"] + "?lang=en").get_data(as_text=True)
    assert "Truncated CTS" in body or "Truncated" in body
    run_id = re.search(r"/run/(\d+)", body).group(1)
    audit = client.get(f"/run/{run_id}?lang=es").get_data(as_text=True)
    assert "CTS trunca" in audit and "PE_CTS_TRUNCA" in audit


def test_us_y_hk_no_tienen_liquidacion_local(client):
    for cc in ("US", "HK"):
        response = client.get(f"/liquidacion/{cc}?lang=es")
        assert response.status_code in (200, 302)
        if response.status_code == 200:
            assert "formula_indemnizacion" not in response.get_data(as_text=True)
