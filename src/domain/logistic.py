"""Configuração explícita da primeira comparação, sem busca de parâmetros."""

from dataclasses import dataclass
from typing import Literal

from src.domain.contract import ContractError, ExperimentContract, JsonObject

type FeatureVariant = Literal["rede_uf", "completa"]
VARIANTS: tuple[FeatureVariant, ...] = ("rede_uf", "completa")


def variant_features(variant: FeatureVariant) -> tuple[str, ...]:
    """Retorna apenas o grupo autorizado; exemplo: `variant_features('rede_uf')`."""
    if variant not in VARIANTS:
        raise ContractError(f"Variante={variant}; esperado {VARIANTS}")
    contract = ExperimentContract()
    return contract.categorical if variant == "rede_uf" else contract.features


@dataclass(frozen=True)
class LogisticSettings:
    """Parâmetros da rodada inicial; exemplo: `LogisticSettings.from_definition(config)`."""

    c: float = 1.0
    max_iter: int = 1000
    tolerance: float = 1e-6
    random_state: int = 42
    threads: int = 1

    @classmethod
    def from_definition(cls, config: JsonObject) -> "LogisticSettings":
        expected = {
            "solver": "lbfgs",
            "penalty": "l2",
            "class_weight": None,
            "sample_weight_fit": False,
            "threshold_risk": 0.5,
            "variants": list(VARIANTS),
            "test_2024_evaluated": False,
            "hyperparameter_search_performed": False,
        }
        for key, value in expected.items():
            if config.get(key) != value:
                raise ContractError(f"Configuração {key}={config.get(key)}; esperado {value}")
        result = cls(
            float(config["C"]),
            int(config["max_iter"]),
            float(config["tol"]),
            int(config["random_state"]),
            int(config["threads"]),
        )
        if result.c <= 0 or result.max_iter < 1 or result.tolerance <= 0 or result.threads < 1:
            raise ContractError(
                f"Parâmetros={result}; esperado C, iterações, tolerância e threads positivos"
            )
        return result
