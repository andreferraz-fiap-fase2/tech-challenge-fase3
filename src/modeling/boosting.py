"""HistGradientBoosting, sem parada automática que repartiria municípios."""

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from src.domain.boosting import BoostingCandidate, BoostingSettings
from src.domain.contract import ContractError
from src.domain.logistic import FeatureVariant, variant_features
from src.preprocessing.boosting import boosting_preprocessor


class BoostingModel:
    def __init__(
        self, variant: FeatureVariant, candidate: BoostingCandidate, settings: BoostingSettings
    ) -> None:
        self.features = variant_features(variant)
        self.settings = settings
        estimator = HistGradientBoostingClassifier(
            learning_rate=settings.learning_rate,
            max_iter=candidate.max_iter,
            max_leaf_nodes=candidate.max_leaf_nodes,
            min_samples_leaf=settings.min_samples_leaf,
            l2_regularization=settings.l2_regularization,
            early_stopping=False,
            categorical_features=[True, True] + [False] * (len(self.features) - 2),
            random_state=settings.random_state,
            class_weight=None,
        )
        self.pipeline = Pipeline(
            [
                ("preprocessing", boosting_preprocessor(variant)),
                ("classifier", estimator),
            ]
        )

    def fit(self, predictors: pd.DataFrame, literacy: pd.Series) -> None:
        if set(literacy) != {0, 1}:
            raise ContractError(f"Classes={set(literacy)}; esperado ambas as classes 0/1")
        with threadpool_limits(limits=self.settings.threads):
            self.pipeline.fit(predictors[list(self.features)], literacy)

    def predict_risk(self, predictors: pd.DataFrame) -> NDArray[np.float64]:
        with threadpool_limits(limits=self.settings.threads):
            probabilities = self.pipeline.predict_proba(predictors[list(self.features)])
        return probabilities[:, list(self.pipeline.classes_).index(0)].astype(np.float64)
