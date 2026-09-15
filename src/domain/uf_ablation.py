"""Contrato da ablação territorial; não altera a decisão congelada 1.0."""

from dataclasses import dataclass
from typing import Literal

from src.domain.contract import ContractError, ExperimentContract, JsonObject

type AblationVariant = Literal["completa", "sem_uf"]

REMOVED_FEATURE = "sigla_uf"
VARIANTS: tuple[AblationVariant, ...] = ("completa", "sem_uf")
METRICS = ("average_precision_risk", "roc_auc_risk", "brier_risk")
PUBLISHED_REFERENCE = "boosting_completa"


def ablation_features(variant: AblationVariant) -> tuple[str, ...]:
    """Remove somente a UF na variante ablacionada; exemplo: `ablation_features('sem_uf')`."""
    if variant not in VARIANTS:
        raise ContractError(f"Variante={variant}; esperado {VARIANTS}")
    features = ExperimentContract().features
    if variant == "completa":
        return features
    return tuple(name for name in features if name != REMOVED_FEATURE)


def split_roles(variant: AblationVariant) -> tuple[list[str], list[str]]:
    """Separa categóricos e numéricos preservando a ordem; exemplo: `split_roles('sem_uf')`."""
    contract = ExperimentContract()
    features = ablation_features(variant)
    categorical = [name for name in features if name in contract.categorical]
    numeric = [name for name in features if name in contract.numeric]
    if len(categorical) + len(numeric) != len(features):
        raise ContractError(f"Atributos {features}; esperado apenas papéis do contrato")
    return categorical, numeric


@dataclass(frozen=True)
class AblationSettings:
    """Hiperparâmetros idênticos ao modelo congelado; exemplo: `AblationSettings()`."""

    max_iter: int = 100
    max_leaf_nodes: int = 7
    learning_rate: float = 0.05
    min_samples_leaf: int = 100
    l2_regularization: float = 1.0
    random_state: int = 42
    threads: int = 1


def validate_ablation_definition(definition: JsonObject) -> AblationSettings:
    """Recusa mudanças silenciosas no protocolo registrado; exemplo: `validate_ablation_definition(cfg)`."""
    required = {
        "development_year": 2023,
        "previous_test_2024_already_observed": True,
        "new_independent_test_available": False,
        "removed_feature": REMOVED_FEATURE,
        "variants": list(VARIANTS),
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
        "primary_metric": METRICS[0],
        "secondary_metrics": list(METRICS[1:]),
    }
    for key, expected in required.items():
        if key not in definition or definition[key] != expected:
            raise ContractError(f"Protocolo divergente em {key}; esperado {expected}")
    return AblationSettings(
        int(definition["max_iter"]),  # type: ignore[arg-type]
        int(definition["max_leaf_nodes"]),  # type: ignore[arg-type]
        float(definition["learning_rate"]),  # type: ignore[arg-type]
        int(definition["min_samples_leaf"]),  # type: ignore[arg-type]
        float(definition["l2_regularization"]),  # type: ignore[arg-type]
        int(definition["random_state"]),  # type: ignore[arg-type]
        int(definition["threads"]),  # type: ignore[arg-type]
    )
