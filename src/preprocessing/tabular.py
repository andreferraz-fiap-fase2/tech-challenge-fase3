"""Pré-processamento ajustado junto ao estimador, exclusivamente no treino do fold."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src.domain.contract import ExperimentContract
from src.domain.logistic import FeatureVariant, variant_features


def normalize_categories(frame: pd.DataFrame) -> pd.DataFrame:
    """Unifica None/pd.NA/NaN sem aprender categorias; exemplo: `normalize_categories(Xcat)`."""
    return frame.astype(object).where(frame.notna(), np.nan)


def categorical_pipeline() -> Pipeline:
    """Encoding mantém categorias inéditas operáveis; exemplo: `categorical_pipeline()`."""
    return Pipeline(
        [
            (
                "missing_format",
                FunctionTransformer(normalize_categories, feature_names_out="one-to-one"),
            ),
            (
                "imputer",
                SimpleImputer(
                    strategy="constant", fill_value="__AUSENTE__", keep_empty_features=True
                ),
            ),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=True, drop=None)),
        ]
    )


def numeric_pipeline(logarithmic: bool) -> Pipeline:
    """Mediana precede log1p e escala; exemplo: `numeric_pipeline(True)`."""
    steps = [("imputer", SimpleImputer(strategy="median", keep_empty_features=True))]
    if logarithmic:
        steps.append(("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")))
    steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)


def build_preprocessor(variant: FeatureVariant) -> ColumnTransformer:
    """Seleciona explicitamente as colunas permitidas; exemplo: `build_preprocessor('completa')`."""
    variant_features(variant)
    contract = ExperimentContract()
    transforms = [("categorical", categorical_pipeline(), list(contract.categorical))]
    if variant == "completa":
        transforms.extend(
            [
                ("log", numeric_pipeline(True), list(contract.numeric[:2])),
                ("shares", numeric_pipeline(False), list(contract.numeric[2:])),
            ]
        )
    return ColumnTransformer(transforms, remainder="drop", sparse_threshold=1.0)
