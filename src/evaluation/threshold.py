"""Seleção de limiar exclusivamente nas previsões fora de fold do desenvolvimento."""

import numpy as np
import pandas as pd

from src.domain.contract import ContractError, JsonObject


def check_probabilities(literacy: np.ndarray, risk: np.ndarray) -> None:
    """Valida entradas binárias e probabilidades; exemplo: `check_probabilities(y, p)`."""
    if len(literacy) != len(risk) or set(literacy) != {0, 1}:
        raise ContractError(
            "Alvo/probabilidades incompatíveis; esperado ambas as classes e mesma dimensão"
        )
    if not np.isfinite(risk).all() or ((risk < 0) | (risk > 1)).any():
        raise ContractError("Probabilidades inválidas; esperado valores finitos no intervalo [0,1]")


def f2_curve(literacy: np.ndarray, risk: np.ndarray) -> pd.DataFrame:
    """Agrupa empates antes de computar decisões p >= limiar; exemplo: `f2_curve(y, p)`."""
    check_probabilities(literacy, risk)
    grouped = (
        pd.DataFrame({"threshold": risk, "target": 1 - literacy})
        .groupby("threshold")["target"]
        .agg(["sum", "size"])
        .sort_index(ascending=False)
    )
    tp = grouped["sum"].cumsum()
    fp = grouped["size"].cumsum() - tp
    fn = grouped["sum"].sum() - tp
    tn = len(risk) - tp - fp - fn
    return pd.DataFrame(
        {
            "threshold": grouped.index,
            "tp": tp.to_numpy(),
            "fp": fp.to_numpy(),
            "fn": fn.to_numpy(),
            "tn": tn.to_numpy(),
            "f2": (5 * tp / (5 * tp + 4 * fn + fp)).to_numpy(),
            "recall": (tp / (tp + fn)).to_numpy(),
            "precision": (tp / (tp + fp)).to_numpy(),
            "flag_rate": ((tp + fp) / len(risk)).to_numpy(),
        }
    )


def decision_metrics(
    literacy: np.ndarray, risk: np.ndarray, threshold: float, weights: np.ndarray | None = None
) -> JsonObject:
    """Métricas do limiar, incluindo carga de triagem; exemplo: `decision_metrics(y, p, .3)`."""
    check_probabilities(literacy, risk)
    if not 0 <= threshold <= 1:
        raise ContractError(f"Limiar={threshold}; esperado [0,1]")
    weights = np.ones(len(risk)) if weights is None else np.asarray(weights, dtype=float)
    if len(weights) != len(risk) or not np.isfinite(weights).all() or (weights <= 0).any():
        raise ContractError("Pesos inválidos; esperado vetor positivo finito de mesma dimensão")
    target, flagged = literacy == 0, risk >= threshold
    tp, fp = float(weights[target & flagged].sum()), float(weights[~target & flagged].sum())
    fn, tn = float(weights[target & ~flagged].sum()), float(weights[~target & ~flagged].sum())
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "f2": 5 * tp / (5 * tp + 4 * fn + fp),
        "recall": tp / (tp + fn),
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "specificity": tn / (tn + fp),
        "flag_rate": (tp + fp) / weights.sum(),
        "accuracy": (tp + tn) / weights.sum(),
    }
