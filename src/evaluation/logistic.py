"""Métricas e comparação pareada de variantes no desenvolvimento."""

from typing import cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from src.domain.contract import ContractError, JsonObject
from src.evaluation.metrics import risk_metrics


def validation_scores(frame: pd.DataFrame, risk: NDArray[np.float64]) -> JsonObject:
    """Avalia as duas ponderações sobre as mesmas previsões; exemplo: `validation_scores(val, risk)`."""
    labels = frame["alfabetizado"].to_numpy(dtype=np.int8)
    weights = frame["peso_aluno"].to_numpy(dtype=float)
    return {
        "unweighted": risk_metrics(labels, risk),
        "weighted_evaluation_only": risk_metrics(labels, risk, weights),
    }


def comparison_table(baseline: JsonObject, variants: list[JsonObject]) -> pd.DataFrame:
    """Expõe cada fold e sua referência comum; exemplo: `comparison_table(dummy, variants)`."""
    rows: list[JsonObject] = []
    expected = {f["fold"]: f["validation_rows"] for f in cast(list[JsonObject], baseline["folds"])}
    for label, report in [("dummy_prior", baseline), *[(str(v["variant"]), v) for v in variants]]:
        for fold in cast(list[JsonObject], report["folds"]):
            if expected.get(fold["fold"]) != fold["validation_rows"]:
                raise ContractError(
                    f"Fold {fold['fold']} com {fold['validation_rows']} avaliações; esperado {expected}"
                )
            rows.append(
                {
                    "model": label,
                    "fold": fold["fold"],
                    **cast(JsonObject, fold["unweighted"]),
                    "fit_seconds": fold.get("fit_seconds"),
                    "predict_seconds": fold.get("predict_seconds"),
                }
            )
    return pd.DataFrame(rows).drop(columns="confusion_tn_fp_fn_tp")


def enrichment_deltas(comparison: pd.DataFrame) -> pd.DataFrame:
    """Diferença pareada nos mesmos municípios; exemplo: `enrichment_deltas(table)`."""
    metrics = ["average_precision_risk", "roc_auc_risk", "brier_risk"]
    indexed = comparison.set_index(["model", "fold"])
    difference = indexed.loc["completa", metrics] - indexed.loc["rede_uf", metrics]
    return difference.rename(columns={m: f"delta_{m}" for m in metrics}).reset_index()
