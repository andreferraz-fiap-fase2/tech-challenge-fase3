"""Duas pipelines com hiperparâmetros idênticos; só muda o conjunto de atributos."""

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from src.domain.contract import ContractError
from src.domain.uf_ablation import AblationSettings, AblationVariant, ablation_features, split_roles
from src.preprocessing.uf_ablation import ablation_preprocessor


class UfAblationModel:
    """Isola o efeito da UF mantendo tudo o mais igual ao modelo congelado."""

    def __init__(self, variant: AblationVariant, settings: AblationSettings) -> None:
        self.features = ablation_features(variant)
        categorical, _ = split_roles(variant)
        classifier = HistGradientBoostingClassifier(
            max_iter=settings.max_iter,
            max_leaf_nodes=settings.max_leaf_nodes,
            learning_rate=settings.learning_rate,
            min_samples_leaf=settings.min_samples_leaf,
            l2_regularization=settings.l2_regularization,
            random_state=settings.random_state,
            early_stopping=False,
            class_weight=None,
            categorical_features=[True] * len(categorical)
            + [False] * (len(self.features) - len(categorical)),
        )
        self.settings = settings
        self.pipeline = Pipeline(
            [("preprocessing", ablation_preprocessor(variant)), ("classifier", classifier)]
        )

    def _predictors(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not set(self.features).issubset(frame.columns):
            raise ContractError(f"Preditores ausentes; esperado {self.features}")
        return frame[list(self.features)]

    def fit(self, frame: pd.DataFrame, literacy: pd.Series) -> None:
        if set(literacy) != {0, 1}:
            raise ContractError(f"Classes={set(literacy)}; esperado ambas as classes 0/1")
        with threadpool_limits(limits=self.settings.threads):
            self.pipeline.fit(self._predictors(frame), literacy)

    def predict_risk(self, frame: pd.DataFrame) -> NDArray[np.float64]:
        with threadpool_limits(limits=self.settings.threads):
            probabilities = self.pipeline.predict_proba(self._predictors(frame))
        return probabilities[:, list(self.pipeline.classes_).index(0)].astype(np.float64)
