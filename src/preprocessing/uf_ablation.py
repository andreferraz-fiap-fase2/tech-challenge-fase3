"""Mesmo pré-processamento do boosting congelado, com o conjunto de atributos variável."""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from src.domain.uf_ablation import AblationVariant, split_roles
from src.preprocessing.tabular import categorical_pipeline


def ablation_preprocessor(variant: AblationVariant) -> ColumnTransformer:
    """Reproduz `boosting_preprocessor('completa')` quando nada é removido."""
    categorical, numeric = split_roles(variant)
    encoder = Pipeline(
        categorical_pipeline().steps[:-1]
        + [("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan))]
    )
    transforms = [
        ("categorical", encoder, categorical),
        ("numeric", SimpleImputer(strategy="median", keep_empty_features=True), numeric),
    ]
    return ColumnTransformer(transforms, remainder="drop", sparse_threshold=0.0)
