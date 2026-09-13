"""Consome uma única vez o teste reservado, depois da decisão e do ajuste final."""

from datetime import UTC, datetime

import numpy as np
import pandas as pd

from src.domain.contract import ContractError, ExperimentContract, JsonObject
from src.evaluation.temporal import calibration_table, score_population
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.prediction import pipeline_risk
from src.usecase.final_fit import FINAL_MODEL, FIT_REPORT
from src.usecase.freeze import DECISION, TEST_GOLD
from src.usecase.logistic import verify_logistic_inputs

TEMPORAL_REPORT = "reports/teste_temporal_2024.json"
PREDICTIONS = "artifacts/previsoes_teste_2024.parquet"


def verify_final_artifacts(store: FileStore) -> tuple[JsonObject, JsonObject]:
    """Bloqueia alteração da decisão ou pipeline; exemplo: `verify_final_artifacts(store)`."""
    decision, fit = store.read_json(DECISION), store.read_json(FIT_REPORT)
    verify_logistic_inputs(store, decision)
    for relative, expected in (
        (DECISION, fit["decision_sha256"]),
        (FINAL_MODEL, fit["model_sha256"]),
        (TEST_GOLD, decision["test_gold_sha256"]),
    ):
        if store.digest(relative) != expected:
            raise ContractError(f"SHA-256 divergente em {relative}; esperado {expected}")
    return decision, fit


def load_reserved_test(store: FileStore) -> pd.DataFrame:
    """Valida ano, chave e população reservada; exemplo: `load_reserved_test(store)`."""
    frame = store.read_parquet(TEST_GOLD)
    if set(frame["ano"]) != {2024} or set(frame["particao"]) != {"teste_reservado"}:
        raise ContractError("Partição inválida; esperado teste_reservado de 2024")
    if frame.duplicated(["ano", "id_aluno"]).any():
        raise ContractError("Chaves duplicadas; esperado uma linha por ano/aluno")
    return frame


def evaluate_locked_test(store: FileStore, expected_rows: int) -> JsonObject:
    """Avalia sem ajuste e sem sobrescrever saída; exemplo: `evaluate_locked_test(store, n)`."""
    if (store.root / TEMPORAL_REPORT).exists() or (store.root / PREDICTIONS).exists():
        raise ContractError("Teste já executado; esperado saída vazia para avaliação ou reprodução")
    decision, fit = verify_final_artifacts(store)
    frame = load_reserved_test(store)
    if len(frame) != expected_rows:
        raise ContractError(f"Linhas={len(frame)}; esperado {expected_rows}")
    development = store.load_development()
    seen = frame["id_municipio"].isin(development["id_municipio"].unique()).to_numpy()
    pipeline = ModelStore(store.root).load(FINAL_MODEL)
    risk = pipeline_risk(pipeline, frame)
    threshold = float(decision["risk_threshold"])
    slices: JsonObject = {}
    for name, mask in (
        ("todos", np.ones(len(frame), dtype=bool)),
        ("municipios_conhecidos", seen),
        ("municipios_novos", ~seen),
    ):
        if mask.any():
            slices[name] = score_population(frame.loc[mask], risk[mask], threshold)
    report: JsonObject = {
        "test_year": 2024,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "decision_sha256": store.digest(DECISION),
        "model_sha256": store.digest(FINAL_MODEL),
        "test_gold_sha256": store.digest(TEST_GOLD),
        "threshold": threshold,
        "slices": slices,
        "baseline_prior_2023": score_population(
            frame, np.full(len(frame), float(fit["training_prior_non_literate"])), threshold
        ),
        "test_used_for_tuning": False,
    }
    predictions = frame[["ano", "id_aluno", "id_municipio"]].assign(
        municipio_conhecido_2023=seen,
        p_nao_alfabetizado=risk,
        p_alfabetizado=1 - risk,
        sinalizado_f2=risk >= threshold,
    )
    store.write_parquet(PREDICTIONS, predictions)
    report["predictions_sha256"] = store.digest(PREDICTIONS)
    store.write_csv("reports/calibracao_teste_2024.csv", calibration_table(frame, risk))
    store.write_json(TEMPORAL_REPORT, report)
    return report


def run_temporal(store: FileStore) -> JsonObject:
    """Entrada real mantém contagem do contrato; exemplo: `run_temporal(store)`."""
    return evaluate_locked_test(store, ExperimentContract().expected_rows(2024))
