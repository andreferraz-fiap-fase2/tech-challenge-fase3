"""Importância marginal em validação, respeitando a unidade dos atributos territoriais."""

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline

from src.domain.contract import ExperimentContract
from src.modeling.prediction import pipeline_risk


def permute_feature(frame: pd.DataFrame, feature: str, seed: int) -> pd.DataFrame:
    """Permuta território por município e rede por aluno; exemplo: `permute_feature(df, name, 42)`."""
    shuffled = frame.copy()
    generator = np.random.default_rng(seed)
    if feature == "rede_nome":
        shuffled[feature] = generator.permutation(frame[feature].to_numpy())
        return shuffled
    municipalities = frame.drop_duplicates("id_municipio").set_index("id_municipio")[feature]
    mapping = pd.Series(
        generator.permutation(municipalities.to_numpy()), index=municipalities.index
    )
    shuffled[feature] = frame["id_municipio"].map(mapping)
    return shuffled


def permutation_scores(pipeline: Pipeline, sample: pd.DataFrame, fold: int) -> pd.DataFrame:
    """Usa apenas o modelo que não treinou nos municípios da amostra; exemplo: `permutation_scores(model, val, 0)`."""
    y = 1 - sample["alfabetizado"].to_numpy()
    baseline = average_precision_score(y, pipeline_risk(pipeline, sample))
    rows = []
    for feature in ExperimentContract().features:
        for repeat in range(5):
            shuffled = permute_feature(sample, feature, 42 + fold * 100 + repeat)
            score = average_precision_score(y, pipeline_risk(pipeline, shuffled))
            rows.append(
                {
                    "fold": fold,
                    "feature": feature,
                    "repeat": repeat,
                    "baseline_ap": baseline,
                    "permuted_ap": score,
                    "decrease_ap": baseline - score,
                }
            )
    return pd.DataFrame(rows)
