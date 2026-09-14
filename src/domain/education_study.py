"""Contrato do estudo complementar; não modifica a decisão do experimento 1.0."""

from pathlib import Path
from typing import Literal

from src.domain.contract import ContractError, ExperimentContract, JsonObject

type EducationVariant = Literal["ibge", "ibge_inep"]

EDUCATION_FEATURES = (
    "alunos_por_turma_ai_2021",
    "docentes_superior_ai_2021",
    "horas_aula_ai_2021",
)
VARIANTS: tuple[EducationVariant, ...] = ("ibge", "ibge_inep")
PROTOCOL_COMMIT = "038bdcd29886909a3450df9c50d4c743c66d75be"
PROTOCOL_HASHES = {
    "config/estudo-educacional.json": "2e1e368960a8ef402803e3df05af48f8f2b98bd67a84944b7010cbc77df01625",
    "docs/Protocolo-Estudo-Educacional.md": "4e50452443c65686a360dc4b6f46ec2a183c305e952f8d56a88b7614e490c416",
}
METRICS = ("average_precision_risk", "roc_auc_risk", "brier_risk")


def study_features(variant: EducationVariant) -> tuple[str, ...]:
    """Expande somente a lista autorizada; exemplo: `study_features('ibge_inep')`."""
    if variant not in VARIANTS:
        raise ContractError("Variante não autorizada; esperado ibge ou ibge_inep")
    return ExperimentContract().features + (EDUCATION_FEATURES if variant == "ibge_inep" else ())


def validate_study_definition(definition: JsonObject) -> None:
    """Recusa mudanças silenciosas no protocolo previamente registrado."""
    required = {
        "development_year": 2023,
        "previous_test_2024_already_observed": True,
        "new_independent_test_available": False,
        "external_context_cutoff": "2022-12-31",
        "join": ["id_municipio", "rede_nome"],
        "education_features": list(EDUCATION_FEATURES),
        "minimum_student_coverage_per_feature": 0.95,
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


def validate_output_root(source_root: Path, output_root: Path) -> Path:
    """Permite somente saída vazia fora da árvore de origem; resolve links simbólicos."""
    source, output = source_root.resolve(), output_root.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ContractError("Saída deve ser externa e independente da raiz do experimento")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ContractError("Saída já contém arquivos; esperado diretório novo ou vazio")
    return output
