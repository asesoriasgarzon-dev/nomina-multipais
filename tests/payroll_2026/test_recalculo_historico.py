"""Recálculo histórico: recalcular una corrida guardada con otras reglas y explicar la diferencia (sin ajustar nada)."""

import copy

import pytest

import app as application
import models
from payroll_engine.errors import InputValidationError
from payroll_engine.loader import RuleSetData, load_country
from payroll_engine.recalculate import diff_runs, historical_recalculation, recalculate_with_documents
from payroll_engine.run import PayrollEngine, reproduce

from .term_helpers import D, lines, monthly, term


def stored(run):
    return run.to_dict()


def test_recalculo_con_las_mismas_reglas_no_cambia_nada():
    run = term("PE", "2024-03-10", "2026-07-20", "DISMISSAL_WITHOUT_CAUSE", "3000")
    result = historical_recalculation(stored(run))
    assert result["run"].run_type == "HISTORICAL_RECALCULATION" and result["run"].original_run_uid == run.run_id
    assert result["comparison"]["lines_changed"] == [] and result["comparison"]["same_normative_content"] is True
    assert result["run"].result_hash == run.result_hash or lines(result["run"]) == lines(run)


def test_recalculo_con_una_norma_distinta_explica_cada_diferencia_y_su_regla():
    run = monthly("CL", 900_000, ("2026-06-01", "2026-06-30"))
    docs = copy.deepcopy(run._documents)
    for r in docs["rules"]:
        if r["rule_id"] == "CL.SIS_EMPLOYER.2":
            r["calculation"]["params"]["rate"] = "0.0200"                      # norma hipotética distinta
    result = recalculate_with_documents(stored(run), docs)
    row = next(r for r in result["comparison"]["lines_changed"] if r["concept"] == "SIS_EMPLOYER")
    assert row["kind"] == "CHANGED" and D(row["after"]) == D("18000.00") and D(row["before"]) == D("14580.00")
    assert D(row["difference"]) == D("3420.00")
    assert result["comparison"]["same_normative_content"] is False and D(result["comparison"]["total_difference"]) == D("3420.00")


def test_recalculo_detecta_lineas_agregadas_y_eliminadas():
    run = term("PE", "2024-03-10", "2026-07-20", "DISMISSAL_WITHOUT_CAUSE", "3000")
    reduced = copy.deepcopy(run._documents)
    reduced["rules"] = [r for r in reduced["rules"] if r["rule_key"] != "PE.VACACIONES_TRUNCAS"]
    removed = recalculate_with_documents(stored(run), reduced)
    assert {r["concept"]: r["kind"] for r in removed["comparison"]["lines_changed"]}["PE_VACACIONES_TRUNCAS"] == "REMOVED"
    old = PayrollEngine().run(run.input_snapshot["payload"], ruleset=RuleSetData.from_documents(reduced))
    added = recalculate_with_documents(stored(old), run._documents)
    assert {r["concept"]: r["kind"] for r in added["comparison"]["lines_changed"]}["PE_VACACIONES_TRUNCAS"] == "ADDED"


def test_la_entrada_es_exactamente_la_original_y_una_terminacion_sigue_siendo_terminacion():
    run = term("AR", "2020-01-10", "2026-03-15", "DISMISSAL_WITHOUT_CAUSE", "1000000")
    result = historical_recalculation(stored(run))
    new = result["run"]
    assert new.input_snapshot["payload"]["employment"] == run.input_snapshot["payload"]["employment"]
    assert new.input_snapshot["payload"]["base_run_type"] == "TERMINATION"
    assert lines(new) == lines(run)


def test_no_se_encadenan_recalculos_ni_se_recalcula_un_ajuste():
    run = term("PE", "2024-03-10", "2026-07-20", "DISMISSAL_WITHOUT_CAUSE", "3000")
    first = historical_recalculation(stored(run))["run"]
    with pytest.raises(InputValidationError):
        historical_recalculation(stored(first))


def test_hist_recalculation_exige_la_corrida_original():
    payload = copy.deepcopy(term("PE", "2024-03-10", "2026-07-20", "RESIGNATION", "3000").input_snapshot["payload"])
    payload["run_type"] = "HISTORICAL_RECALCULATION"
    with pytest.raises(InputValidationError):
        PayrollEngine().run(payload)
    payload["original_run_uid"] = "x"
    payload["base_run_type"] = "OTRO"
    with pytest.raises(InputValidationError):
        PayrollEngine().run(payload)


def test_reproducir_sigue_usando_el_snapshot_viejo_aunque_las_reglas_actuales_cambien():
    run = term("PE", "2024-03-10", "2026-07-20", "DISMISSAL_WITHOUT_CAUSE", "3000")
    assert reproduce(stored(run), run._documents)["same"] is True


def test_endpoint_de_recalculo_devuelve_la_comparacion_sin_guardar_nada():
    application.app.config["TESTING"] = True
    client = application.app.test_client()
    from countries import REGISTRY
    response = client.post("/liquidacion/PE?lang=es", data=dict(REGISTRY["PE"]["engine"].EJEMPLO_LIQUIDACION, es_demo="1"))
    liq = models.obtener_liquidacion(int(response.headers["Location"].rsplit("/", 1)[1]))
    run_id = liq["resultado"]["run_db_id"]
    before = models.obtener_payroll_run(run_id)
    payload = client.get(f"/run/{run_id}/recalculate").get_json()
    assert payload["same_normative_content"] is True and payload["lines_changed"] == []
    assert payload["original_result_hash"] == before["result_hash"]
    assert client.get("/run/999999/recalculate").status_code == 404
