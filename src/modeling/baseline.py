"""Baseline de frequência, ajustado apenas nos municípios de treino de cada fold."""

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.dummy import DummyClassifier

from src.domain.contract import ContractError


class PriorBaseline:
    """Adaptador do DummyClassifier; exemplo: `PriorBaseline().fit_predict(Xtr, ytr, Xval)`."""

    def fit_predict(
        self,
        train: pd.DataFrame,
        labels: pd.Series,
        validation: pd.DataFrame,
    ) -> NDArray[np.float64]:
        if set(labels) != {0, 1}:
            raise ContractError(f"Classes de treino={set(labels)}; esperado 0 e 1")
        model = DummyClassifier(strategy="prior", random_state=42)
        model.fit(train, labels)
        risk_column = list(model.classes_).index(0)
        return model.predict_proba(validation)[:, risk_column].astype(np.float64)
