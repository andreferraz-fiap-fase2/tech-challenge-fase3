"""Duas pipelines fixas, sem busca, para a comparação exploratória de 2023."""

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from src.domain.contract import ContractError
from src.domain.education_study import EducationVariant, study_features
from src.preprocessing.boosting import boosting_preprocessor


class EducationStudyModel:
    """Mantém hiperparâmetros idênticos entre variantes e aprende imputação no treino."""

    def __init__(self, variant: EducationVariant) -> None:
        self.features = study_features(variant)
        preprocessing = boosting_preprocessor("completa")
        name, transformer, _ = preprocessing.transformers[1]
        preprocessing.transformers[1] = (name, transformer, list(self.features[2:]))
        classifier = HistGradientBoostingClassifier(
            max_iter=100,
            max_leaf_nodes=7,
            learning_rate=0.05,
            min_samples_leaf=100,
            l2_regularization=1.0,
            random_state=42,
            early_stopping=False,
            class_weight=None,
            categorical_features=[True, True] + [False] * (len(self.features) - 2),
        )
        self.pipeline = Pipeline([("preprocessing", preprocessing), ("classifier", classifier)])

    def _predictors(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not set(self.features).issubset(frame.columns):
            raise ContractError("Preditores ausentes; esperado conjunto completo da variante")
        return frame[list(self.features)]

    def fit(self, frame: pd.DataFrame, literacy: pd.Series) -> None:
        if set(literacy) != {0, 1}:
            raise ContractError("Alvo inválido; esperado ambas as classes 0/1")
        with threadpool_limits(limits=1):
            self.pipeline.fit(self._predictors(frame), literacy)

    def predict_risk(self, frame: pd.DataFrame) -> NDArray[np.float64]:
        with threadpool_limits(limits=1):
            probabilities = self.pipeline.predict_proba(self._predictors(frame))
        return probabilities[:, list(self.pipeline.classes_).index(0)].astype(np.float64)
