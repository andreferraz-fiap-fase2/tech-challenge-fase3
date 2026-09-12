"""Ajuste final em todo 2023 após congelamento, sem leitura de 2024."""

from typing import cast

import numpy as np

from src.domain.boosting import BoostingCandidate, BoostingSettings
from src.domain.contract import ContractError, JsonObject
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.boosting import BoostingModel
from src.modeling.prediction import pipeline_risk
from src.usecase.freeze import DECISION
from src.usecase.logistic import verify_logistic_inputs

FINAL_MODEL = "artifacts/modelo_final.joblib"
FIT_REPORT = "reports/ajuste_final.json"


def run_final_fit(store: FileStore) -> JsonObject:
    """Persiste a pipeline e confere sua releitura; exemplo: `run_final_fit(store)`."""
    if (store.root / FIT_REPORT).exists():
        raise ContractError("Ajuste final já existe; esperado execução única com decisão congelada")
    decision = store.read_json(DECISION)
    verify_logistic_inputs(store, decision)
    config = store.read_json("config/experimento-boosting.json")
    selected = cast(JsonObject, decision["candidate"])
    candidate = BoostingCandidate(
        str(selected["name"]), int(selected["max_iter"]), int(selected["max_leaf_nodes"])
    )
    model = BoostingModel("completa", candidate, BoostingSettings.from_definition(config))
    frame = store.load_development()
    model.fit(frame, frame["alfabetizado"])
    models = ModelStore(store.root)
    models.save(FINAL_MODEL, model.pipeline)
    sample = frame.sample(min(100, len(frame)), random_state=42)
    np.testing.assert_allclose(
        model.predict_risk(sample),
        pipeline_risk(models.load(FINAL_MODEL), sample),
        rtol=0,
        atol=1e-12,
    )
    report: JsonObject = {
        "training_year": 2023,
        "training_rows": len(frame),
        "test_2024_read": False,
        "decision_sha256": store.digest(DECISION),
        "model_sha256": store.digest(FINAL_MODEL),
        "model_path": FINAL_MODEL,
        "roundtrip_max_absolute_tolerance": 1e-12,
        "training_prior_non_literate": float(1 - frame["alfabetizado"].mean()),
    }
    store.write_json(FIT_REPORT, report)
    return report
