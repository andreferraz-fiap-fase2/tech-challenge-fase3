"""Adaptador da Regressão Logística com pipeline completa e convergência obrigatória."""

import warnings

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from src.domain.contract import ContractError
from src.domain.logistic import FeatureVariant, LogisticSettings, variant_features
from src.preprocessing.tabular import build_preprocessor


class LogisticModel:
    """Um objeto por variante/fold; exemplo: `LogisticModel('completa', settings).fit(X, y)`."""

    def __init__(self, variant: FeatureVariant, settings: LogisticSettings) -> None:
        self.features = variant_features(variant)
        self.settings = settings
        estimator = LogisticRegression(
            C=settings.c,
            solver="lbfgs",
            penalty="l2",
            max_iter=settings.max_iter,
            tol=settings.tolerance,
            random_state=settings.random_state,
            class_weight=None,
        )
        self.pipeline = Pipeline(
            [("preprocessing", build_preprocessor(variant)), ("classifier", estimator)]
        )

    def fit(self, predictors: pd.DataFrame, literacy: pd.Series) -> None:
        if set(literacy) != {0, 1}:
            raise ContractError(f"Classes={set(literacy)}; esperado ambas as classes 0/1")
        with threadpool_limits(limits=self.settings.threads), warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            try:
                self.pipeline.fit(predictors[list(self.features)], literacy)
            except ConvergenceWarning as exc:
                raise ContractError(
                    f"Regressão não convergiu com {self.settings}; esperado convergência"
                ) from exc

    def predict_risk(self, predictors: pd.DataFrame) -> NDArray[np.float64]:
        with threadpool_limits(limits=self.settings.threads):
            probabilities = self.pipeline.predict_proba(predictors[list(self.features)])
        risk_index = list(self.pipeline.classes_).index(0)
        return probabilities[:, risk_index].astype(np.float64)

    def coefficients(self) -> pd.DataFrame:
        names = self.pipeline.named_steps["preprocessing"].get_feature_names_out()
        classifier = self.pipeline.named_steps["classifier"]
        values = np.r_[classifier.coef_[0], classifier.intercept_[0]]
        return pd.DataFrame(
            {
                "term": [*names, "intercept"],
                "coefficient_literacy": values,
                "coefficient_risk": -values,
            }
        )

    def iterations(self) -> int:
        return int(self.pipeline.named_steps["classifier"].n_iter_[0])
