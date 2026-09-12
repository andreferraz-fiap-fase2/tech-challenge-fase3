"""Probabilidade orientada a risco de uma pipeline completa persistida."""

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from src.domain.contract import ContractError, ExperimentContract


def pipeline_risk(pipeline: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    """Mantém a lista de seis preditores e a orientação da classe; exemplo: `pipeline_risk(model, df)`."""
    features = list(pipeline.feature_names_in_)
    if tuple(features) != ExperimentContract().features or set(pipeline.classes_) != {0, 1}:
        raise ContractError(
            f"Preditores/classes={features}/{pipeline.classes_}; esperado contrato completo 0/1"
        )
    with threadpool_limits(limits=1):
        return pipeline.predict_proba(frame[features])[:, list(pipeline.classes_).index(0)]
