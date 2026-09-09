"""Protocolo explícito da busca limitada em 2023."""

from dataclasses import dataclass
from math import isfinite
from typing import cast

from src.domain.contract import ContractError, JsonObject
from src.domain.logistic import VARIANTS


@dataclass(frozen=True)
class BoostingCandidate:
    name: str
    max_iter: int
    max_leaf_nodes: int


@dataclass(frozen=True)
class BoostingSettings:
    sample_per_fold: int
    candidates: tuple[BoostingCandidate, ...]
    learning_rate: float = 0.05
    min_samples_leaf: int = 100
    l2_regularization: float = 1.0
    random_state: int = 42
    threads: int = 1

    @classmethod
    def from_definition(cls, config: JsonObject) -> "BoostingSettings":
        expected = {
            "variants": list(VARIANTS),
            "development_year": 2023,
            "test_2024_evaluated": False,
            "early_stopping": False,
            "sample_weight_fit": False,
            "class_weight": None,
            "threshold_risk": 0.5,
            "sampling": "lowest_sha256_seed_year_student_per_fixed_fold",
            "selection": "mean_average_precision_risk_then_fewer_leaves_then_fewer_iterations",
        }
        for key, value in expected.items():
            if config.get(key) != value:
                raise ContractError(f"Configuração {key}={config.get(key)}; esperado {value}")
        candidates = tuple(
            BoostingCandidate(str(c["name"]), int(c["max_iter"]), int(c["max_leaf_nodes"]))
            for c in cast(list[JsonObject], config["candidates"])
        )
        settings = cls(
            int(config["sample_per_fold"]),
            candidates,
            float(config["learning_rate"]),
            int(config["min_samples_leaf"]),
            float(config["l2_regularization"]),
            int(config["random_state"]),
            int(config["threads"]),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.sample_per_fold < 1 or self.min_samples_leaf < 1 or self.threads < 1:
            raise ContractError("Amostra, folha mínima e threads devem ser positivos")
        if not isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ContractError("Learning rate deve ser finito e positivo")
        if not isfinite(self.l2_regularization) or self.l2_regularization < 0:
            raise ContractError("Regularização deve ser finita e não negativa")
        if not self.candidates or len({c.name for c in self.candidates}) != len(self.candidates):
            raise ContractError("Candidatos devem ter nomes únicos e lista não vazia")
        if any(c.max_iter < 1 or c.max_leaf_nodes < 2 for c in self.candidates):
            raise ContractError("Candidatos precisam de iterações positivas e ao menos duas folhas")
