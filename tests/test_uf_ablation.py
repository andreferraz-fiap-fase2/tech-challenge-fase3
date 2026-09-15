"""Ablação da UF: contrato, pré-processamento, modelo e verificação da referência."""

import pandas as pd
import pytest

from src.domain.contract import ContractError, ExperimentContract
from src.domain.uf_ablation import (
    AblationSettings,
    ablation_features,
    split_roles,
    validate_ablation_definition,
)
from src.evaluation.uf_ablation import ablation_deltas, ablation_table, verify_reference
from src.modeling.uf_ablation import UfAblationModel
from src.preprocessing.boosting import boosting_preprocessor
from src.preprocessing.uf_ablation import ablation_preprocessor


def definition() -> dict:
    return {
        "development_year": 2023,
        "previous_test_2024_already_observed": True,
        "new_independent_test_available": False,
        "removed_feature": "sigla_uf",
        "variants": ["completa", "sem_uf"],
        "folds": [0, 1, 2],
        "max_iter": 100,
        "max_leaf_nodes": 7,
        "learning_rate": 0.05,
        "min_samples_leaf": 100,
        "l2_regularization": 1.0,
        "random_state": 42,
        "threads": 1,
        "early_stopping": False,
        "hyperparameter_search": False,
        "threshold_search": False,
        "calibration_fit": False,
        "class_weight": None,
        "sample_weight_fit": False,
        "primary_metric": "average_precision_risk",
        "secondary_metrics": ["roc_auc_risk", "brier_risk"],
    }


def test_complete_variant_keeps_the_frozen_feature_set() -> None:
    assert ablation_features("completa") == ExperimentContract().features


def test_ablated_variant_removes_only_the_state_code() -> None:
    features = ablation_features("sem_uf")
    assert "sigla_uf" not in features
    assert set(features) == set(ExperimentContract().features) - {"sigla_uf"}


def test_unknown_variant_is_refused() -> None:
    with pytest.raises(ContractError, match="Variante"):
        ablation_features("sem_rede")  # type: ignore[arg-type]


def test_roles_keep_one_categorical_without_state() -> None:
    categorical, numeric = split_roles("sem_uf")
    assert categorical == ["rede_nome"]
    assert len(numeric) == 4


def test_definition_must_match_the_registered_protocol() -> None:
    assert validate_ablation_definition(definition()) == AblationSettings()
    with pytest.raises(ContractError, match="threshold_search"):
        validate_ablation_definition({**definition(), "threshold_search": True})


def test_reference_preprocessor_matches_the_published_boosting() -> None:
    mirrored = ablation_preprocessor("completa").transformers
    published = boosting_preprocessor("completa").transformers
    assert [(name, columns) for name, _, columns in mirrored] == [
        (name, columns) for name, _, columns in published
    ]


def test_model_marks_every_categorical_column(development_students: pd.DataFrame) -> None:
    model = UfAblationModel("sem_uf", AblationSettings())
    flags = model.pipeline.named_steps["classifier"].categorical_features
    assert flags == [True] + [False] * 4
    assert "sigla_uf" not in model.features


def test_model_refuses_frames_without_the_predictors() -> None:
    model = UfAblationModel("completa", AblationSettings())
    with pytest.raises(ContractError, match="Preditores ausentes"):
        model.predict_risk(pd.DataFrame({"rede_nome": ["Municipal"]}))


def test_model_refuses_single_class_targets(development_students: pd.DataFrame) -> None:
    model = UfAblationModel("sem_uf", AblationSettings())
    single = development_students.assign(alfabetizado=1)
    with pytest.raises(ContractError, match="Classes"):
        model.fit(single, single["alfabetizado"])


def scores(variant: str, values: list[float]) -> dict:
    return {
        "variant": variant,
        "folds": [
            {
                "fold": fold,
                "unweighted": {
                    "average_precision_risk": value,
                    "roc_auc_risk": 0.6,
                    "brier_risk": 0.22,
                    "confusion_tn_fp_fn_tp": [1.0, 1.0, 1.0, 1.0],
                },
            }
            for fold, value in enumerate(values)
        ],
    }


def test_deltas_are_paired_by_fold() -> None:
    table = ablation_table([scores("completa", [0.5, 0.6, 0.7]), scores("sem_uf", [0.4, 0.5, 0.6])])
    deltas = ablation_deltas(table)
    assert deltas["delta_average_precision_risk"].round(6).tolist() == [-0.1, -0.1, -0.1]


def published_frame(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": ["boosting_completa"] * 3,
            "fold": [0, 1, 2],
            "average_precision_risk": values,
            "roc_auc_risk": [0.6] * 3,
            "brier_risk": [0.22] * 3,
        }
    )


def test_reference_reproduction_is_confirmed_when_identical() -> None:
    table = ablation_table([scores("completa", [0.5, 0.6, 0.7])])
    assert verify_reference(table, published_frame([0.5, 0.6, 0.7]))["reference_reproduced"] is True


def test_reference_divergence_is_refused() -> None:
    table = ablation_table([scores("completa", [0.5, 0.6, 0.7])])
    with pytest.raises(ContractError, match="Referência divergente"):
        verify_reference(table, published_frame([0.5, 0.6, 0.9]))
