"""Categorias nominais nativas e mediana numérica aprendidas no treino."""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from src.domain.contract import ExperimentContract
from src.domain.logistic import FeatureVariant, variant_features
from src.preprocessing.tabular import categorical_pipeline


def boosting_preprocessor(variant: FeatureVariant) -> ColumnTransformer:
    """Códigos serão marcados como categorias no estimador, sem ordem artificial."""
    variant_features(variant)
    contract = ExperimentContract()
    categorical = Pipeline(
        categorical_pipeline().steps[:-1]
        + [("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan))]
    )
    transforms = [("categorical", categorical, list(contract.categorical))]
    if variant == "completa":
        transforms.append(
            (
                "numeric",
                SimpleImputer(strategy="median", keep_empty_features=True),
                list(contract.numeric),
            )
        )
    return ColumnTransformer(transforms, remainder="drop", sparse_threshold=0.0)
