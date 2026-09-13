"""Explicações e correlações calculadas exclusivamente com desenvolvimento."""

import pandas as pd

from src.domain.contract import ContractError, ExperimentContract, JsonObject
from src.evaluation.development import require_development
from src.evaluation.interpretation import permutation_scores
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore


def run_interpretation(store: FileStore) -> JsonObject:
    """Relê a amostra congelada e os modelos de validação; exemplo: `run_interpretation(store)`."""
    frame = store.load_development()
    sample_keys = store.read_parquet("artifacts/boosting_amostra_2023.parquet")
    sample = sample_keys.merge(
        frame,
        on=["ano", "id_aluno", "id_municipio", "fold_validacao"],
        validate="one_to_one",
        how="left",
    )
    if sample["alfabetizado"].isna().any():
        raise ContractError("Amostra com chave ausente; esperado correspondência completa com 2023")
    require_development(sample)
    scores = []
    models = ModelStore(store.root)
    for fold in (0, 1, 2):
        pipeline = models.load(f"artifacts/boosting/completa/fold_{fold}.joblib")
        scores.append(
            permutation_scores(pipeline, sample.loc[sample["fold_validacao"].eq(fold)], fold)
        )
    details = pd.concat(scores, ignore_index=True)
    summary = (
        details.groupby("feature")["decrease_ap"]
        .agg(["mean", "std", "min", "max"])
        .sort_values("mean", ascending=False)
        .reset_index()
    )
    store.write_csv("reports/importancia_permutacao_2023.csv", summary)
    store.write_csv("reports/importancia_permutacao_repeticoes_2023.csv", details)
    contexts = frame.groupby("id_municipio").agg(
        {**{name: "first" for name in ExperimentContract().numeric}, "alfabetizado": "mean"}
    )
    contexts["risco_observado"] = 1 - contexts.pop("alfabetizado")
    correlations = contexts.corr(method="spearman").reset_index(names="feature")
    store.write_csv("reports/correlacoes_municipais_2023.csv", correlations)
    report: JsonObject = {
        "year": 2023,
        "rows": len(sample),
        "repetitions": 5,
        "folds": 3,
        "metric": "decrease in unweighted average precision of non-literate class",
        "permutation_unit": "municipality for contextual features; student for network",
        "causal_interpretation": False,
        "test_2024_read": False,
    }
    store.write_json("reports/interpretacao_2023.json", report)
    return report
