"""Métricas com a classe de interesse declarada: não alfabetizado."""

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.domain.contract import ContractError, JsonObject


def risk_metrics(
    literacy: NDArray[np.int8],
    risk: NDArray[np.float64],
    weights: NDArray[np.float64] | None = None,
) -> JsonObject:
    """Avalia risco no limiar 0,5; exemplo: `risk_metrics(y_alfabetizado, p_risco)`."""
    if set(literacy) != {0, 1}:
        raise ContractError(f"Classes={set(literacy)}; esperado ambas as classes 0/1 para ROC-AUC")
    target, predicted = 1 - literacy, (risk >= 0.5).astype(np.int8)
    matrix = confusion_matrix(target, predicted, labels=[0, 1], sample_weight=weights)
    return {
        "roc_auc_risk": float(roc_auc_score(target, risk, sample_weight=weights)),
        "average_precision_risk": float(
            average_precision_score(target, risk, sample_weight=weights)
        ),
        "brier_risk": float(brier_score_loss(target, risk, sample_weight=weights)),
        "recall_risk": float(
            recall_score(target, predicted, sample_weight=weights, zero_division=0)
        ),
        "precision_risk": float(
            precision_score(target, predicted, sample_weight=weights, zero_division=0)
        ),
        "f1_risk": float(f1_score(target, predicted, sample_weight=weights, zero_division=0)),
        "balanced_accuracy": float(
            balanced_accuracy_score(target, predicted, sample_weight=weights)
        ),
        "accuracy": float(np.average(target == predicted, weights=weights)),
        "risk_prevalence": float(np.average(target, weights=weights)),
        "confusion_tn_fp_fn_tp": [float(value) for value in matrix.ravel()],
    }
