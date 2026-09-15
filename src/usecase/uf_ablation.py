"""Mede a dependência da UF reajustando o modelo congelado sem esse atributo."""

from time import perf_counter
from typing import cast

import pandas as pd

from src.domain.contract import ContractError, JsonObject, JsonValue
from src.domain.uf_ablation import (
    METRICS,
    VARIANTS,
    AblationSettings,
    AblationVariant,
    ablation_features,
    validate_ablation_definition,
)
from src.evaluation.development import require_development
from src.evaluation.logistic import validation_scores
from src.evaluation.summary import summarize_folds
from src.evaluation.uf_ablation import (
    ablation_deltas,
    ablation_markdown,
    ablation_table,
    verify_reference,
)
from src.infrastructure.files import FileStore
from src.modeling.uf_ablation import UfAblationModel
from src.visualization.uf_ablation import AblationPlots

DEFINITION = "config/experimento-ablacao-uf.json"
PUBLISHED = "reports/modelos_comparacao_2023.csv"
OUTPUTS = (
    "reports/ablacao_uf_2023.csv",
    "reports/ablacao_uf_deltas_2023.csv",
    "reports/ablacao_uf_2023.json",
    "reports/ablacao_uf_2023.md",
)


def ablation_fold(
    frame: pd.DataFrame, variant: AblationVariant, fold: int, settings: AblationSettings
) -> JsonObject:
    """Treina em dois folds e avalia no terceiro; exemplo: `ablation_fold(df, 'sem_uf', 0, s)`."""
    validation = frame["fold_validacao"].eq(fold)
    model = UfAblationModel(variant, settings)
    start = perf_counter()
    model.fit(frame.loc[~validation], frame.loc[~validation, "alfabetizado"])
    risk = model.predict_risk(frame.loc[validation])
    return {
        "fold": fold,
        "training_rows": int((~validation).sum()),
        "validation_rows": int(validation.sum()),
        "elapsed_seconds": perf_counter() - start,
        **validation_scores(frame.loc[validation], risk),
    }


def evaluate_variant(
    frame: pd.DataFrame, variant: AblationVariant, settings: AblationSettings
) -> JsonObject:
    """Percorre os três folds fixos; exemplo: `evaluate_variant(df, 'completa', settings)`."""
    folds = [ablation_fold(frame, variant, fold, settings) for fold in (0, 1, 2)]
    return {
        "variant": variant,
        "features": list(ablation_features(variant)),
        "folds": cast(list[JsonValue], folds),
        "summary": summarize_folds(cast(list[JsonValue], folds)),
    }


def baseline_average_precision(published: pd.DataFrame) -> float:
    """Lê a referência constante já publicada; exemplo: `baseline_average_precision(csv)`."""
    rows = published.loc[published["model"].eq("dummy_prior"), METRICS[0]]
    if len(rows) != 3:
        raise ContractError(f"Baseline com {len(rows)} folds; esperado exatamente 3")
    return float(rows.mean())


def _require_absent(store: FileStore) -> None:
    existing = [path for path in OUTPUTS if (store.root / path).exists()]
    if existing:
        raise ContractError(f"Saídas já existem: {existing}; esperado execução única")


def run_uf_ablation(store: FileStore) -> JsonObject:
    """Compara seis atributos contra cinco sem UF; exemplo: `run_uf_ablation(store)`."""
    _require_absent(store)
    settings = validate_ablation_definition(store.read_json(DEFINITION))
    frame = store.load_development()
    require_development(frame)
    reports = [evaluate_variant(frame, variant, settings) for variant in VARIANTS]
    table = ablation_table(reports)
    deltas = ablation_deltas(table)
    published = store.read_csv(PUBLISHED)
    integrity = verify_reference(table, published)
    result: JsonObject = {
        "year": 2023,
        "rows": len(frame),
        "removed_feature": "sigla_uf",
        "baseline_ap": baseline_average_precision(published),
        "models": cast(list[JsonValue], reports),
        "test_2024_read": False,
        "promotes_new_final_model": False,
        **integrity,
    }
    store.write_csv(OUTPUTS[0], table)
    store.write_csv(OUTPUTS[1], deltas)
    store.write_json(OUTPUTS[2], result)
    store.write_text(OUTPUTS[3], ablation_markdown(table, deltas, result))
    AblationPlots(store.root / "images").comparison(table, float(result["baseline_ap"]))
    return result
