"""Resumo comum para comparar métricas sob os mesmos folds."""

from typing import cast

import numpy as np

from src.domain.contract import JsonObject, JsonValue


def summarize_folds(results: list[JsonValue]) -> JsonObject:
    metrics = (
        "roc_auc_risk",
        "average_precision_risk",
        "brier_risk",
        "recall_risk",
        "precision_risk",
        "f1_risk",
        "accuracy",
        "balanced_accuracy",
    )
    summary: JsonObject = {}
    for weighting in ("unweighted", "weighted_evaluation_only"):
        group: JsonObject = {}
        for metric in metrics:
            values = [
                float(cast(JsonObject, cast(JsonObject, row)[weighting])[metric]) for row in results
            ]
            group[metric] = {
                "mean": float(np.mean(values)),
                "std_between_folds": float(np.std(values, ddof=1)),
            }
        summary[weighting] = group
    return summary
