"""Avaliação temporal com probabilidades e limiares previamente congelados."""

import numpy as np
import pandas as pd

from src.domain.contract import JsonObject
from src.evaluation.metrics import risk_metrics
from src.evaluation.threshold import decision_metrics


def score_population(frame: pd.DataFrame, risk: np.ndarray, threshold: float) -> JsonObject:
    """Expõe qualidade probabilística e custo dos dois limiares; exemplo: `score_population(df, p, .3)`."""
    y = frame["alfabetizado"].to_numpy(dtype=np.int8)
    result: JsonObject = {
        "rows": len(frame),
        "municipalities": int(frame["id_municipio"].nunique()),
    }
    for name, weights in (
        ("unweighted", None),
        ("weighted_evaluation_only", frame["peso_aluno"].to_numpy(dtype=float)),
    ):
        metrics = risk_metrics(y, risk, weights)
        result[name] = {
            "probabilities": {
                k: metrics[k]
                for k in ("average_precision_risk", "roc_auc_risk", "brier_risk", "risk_prevalence")
            },
            "selected_threshold": decision_metrics(y, risk, threshold, weights),
            "reference_0_5": decision_metrics(y, risk, 0.5, weights),
        }
    return result


def calibration_table(frame: pd.DataFrame, risk: np.ndarray) -> pd.DataFrame:
    """Bins fixos, sem reajuste da probabilidade após teste; exemplo: `calibration_table(df, p)`."""
    return (
        pd.DataFrame(
            {
                "bin": pd.cut(risk, bins=np.linspace(0, 1, 11), include_lowest=True),
                "predicted": risk,
                "observed": 1 - frame["alfabetizado"].to_numpy(),
            }
        )
        .groupby("bin", observed=True)
        .agg(
            rows=("predicted", "size"),
            mean_risk=("predicted", "mean"),
            observed_risk=("observed", "mean"),
        )
        .reset_index()
    )
