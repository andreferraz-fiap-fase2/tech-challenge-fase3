"""Congela modelo e limiar com 2023; recusa sobrescrever decisões finais."""

from datetime import UTC, datetime
from typing import cast

import pandas as pd

from src.domain.contract import ContractError, ExperimentContract, JsonObject
from src.evaluation.development import require_development
from src.evaluation.threshold import decision_metrics, f2_curve
from src.infrastructure.files import FileStore
from src.usecase.logistic import verify_logistic_inputs

DECISION = "config/modelo-final.json"
GOLD = "data/gold/ml_aluno/ano=2023/alunos.parquet"
OOF = "artifacts/boosting_oof_2023.parquet"
TEST_GOLD = "data/gold/ml_aluno/ano=2024/alunos.parquet"
TEST_SHA = "5d74435f5e314e333218c48096cd713d6d752e79f33086f4b3f2a7abeea5f8e7"


def selected_development(store: FileStore) -> tuple[pd.DataFrame, JsonObject]:
    """Confere vencedor e chaves OOF antes de escolher limiar; exemplo: `selected_development(store)`."""
    config = store.read_json("config/experimento-boosting.json")
    verify_logistic_inputs(store, config)
    table = store.read_csv("reports/modelos_comparacao_2023.csv")
    ranking = table.groupby("model")["average_precision_risk"].mean().sort_values(ascending=False)
    if ranking.index[0] != "boosting_completa":
        raise ContractError(
            f"Vencedor={ranking.index[0]}; esperado boosting_completa na rodada congelada"
        )
    frame = store.load_development()
    require_development(frame)
    oof = store.read_parquet(OOF)
    keys = ["ano", "id_aluno", "id_municipio", "fold_validacao"]
    if not frame[keys].equals(oof[keys]) or oof.duplicated(["ano", "id_aluno"]).any():
        raise ContractError("Chaves OOF incompatíveis; esperado igualdade exata com a Gold 2023")
    frame = frame.assign(p_risco=oof["p_risco_completa"])
    report = store.read_json("reports/boosting_development.json")
    chosen = next(
        m for m in cast(list[JsonObject], report["models"]) if m["variant"] == "boosting_completa"
    )
    return frame, chosen


def run_freeze(store: FileStore) -> JsonObject:
    """Escolhe F2 máximo com desempate pelo maior limiar; exemplo: `run_freeze(store)`."""
    if (store.root / DECISION).exists():
        raise ContractError("Decisão final já existe; esperado congelamento único sem sobrescrita")
    frame, chosen = selected_development(store)
    y, p = frame["alfabetizado"].to_numpy(), frame["p_risco"].to_numpy()
    curve = f2_curve(y, p)
    winner = curve.sort_values(["f2", "threshold"], ascending=False).iloc[0]
    dependencies = [
        GOLD,
        OOF,
        "config/experimento-boosting.json",
        "config/contrato-ml-aluno.json",
        "config/folds-municipios-2023.csv",
        "reports/modelos_comparacao_2023.csv",
        "reports/boosting_development.json",
    ]
    decision: JsonObject = {
        "version": "1.0",
        "author": "André Mohallem Ferraz",
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "model": "HistGradientBoostingClassifier",
        "variant": "completa",
        "candidate": chosen["candidate"],
        "features": list(ExperimentContract().features),
        "development_year": 2023,
        "test_year": 2024,
        "selection": "highest mean unweighted AP across fixed municipality folds in complete development",
        "threshold_policy": "maximize pooled development OOF F2; exact ties prefer higher threshold",
        "risk_threshold": float(winner["threshold"]),
        "calibration": "none; probabilities preserved",
        "development_oof": {
            "selected": decision_metrics(y, p, float(winner["threshold"])),
            "reference_0_5": decision_metrics(y, p, 0.5),
        },
        "expected_sha256": {path: store.digest(path) for path in dependencies},
        "test_gold_sha256": TEST_SHA,
        "test_2024_evaluated_at_freeze": False,
    }
    store.write_csv("reports/limiar_f2_2023.csv", curve)
    store.write_json(DECISION, decision)
    return decision
