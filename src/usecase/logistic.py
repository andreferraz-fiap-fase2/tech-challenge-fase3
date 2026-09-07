"""Execução das duas variantes logísticas, com artefatos por fold e teste reservado."""

from time import perf_counter
from typing import cast

import pandas as pd

from src.domain.contract import ContractError, ExperimentContract, JsonObject, JsonValue
from src.domain.logistic import VARIANTS, FeatureVariant, LogisticSettings
from src.evaluation.development import require_development
from src.evaluation.logistic import comparison_table, enrichment_deltas, validation_scores
from src.evaluation.logistic_report import logistic_markdown
from src.evaluation.summary import summarize_folds
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.logistic import LogisticModel
from src.visualization.logistic import LogisticPlots


def verify_logistic_inputs(store: FileStore, config: JsonObject) -> None:
    """Confere Gold e protocolo congelados antes de modelar; exemplo: `verify_logistic_inputs(store, config)`."""
    for relative, expected in cast(JsonObject, config["expected_sha256"]).items():
        if "2024" in relative:
            raise ContractError(f"Entrada={relative}; esperado somente desenvolvimento de 2023")
        observed = store.digest(relative)
        if observed != expected:
            raise ContractError(f"SHA-256 de {relative}={observed}; esperado {expected}")


def fit_validation_fold(
    frame: pd.DataFrame,
    variant: FeatureVariant,
    fold: int,
    settings: LogisticSettings,
    models: ModelStore,
) -> tuple[JsonObject, pd.Series, pd.DataFrame]:
    """Uma pipeline nova aprende somente dois folds; exemplo: `fit_validation_fold(df, 'completa', 0, cfg, models)`."""
    validation = frame["fold_validacao"].eq(fold)
    model = LogisticModel(variant, settings)
    start = perf_counter()
    model.fit(frame.loc[~validation], frame.loc[~validation, "alfabetizado"])
    fitted = perf_counter()
    risk = model.predict_risk(frame.loc[validation])
    predicted = perf_counter()
    models.save(f"artifacts/logistica/{variant}/fold_{fold}.joblib", model.pipeline)
    scores = {
        "fold": fold,
        "training_rows": int((~validation).sum()),
        "validation_rows": int(validation.sum()),
        "n_iterations": model.iterations(),
        "converged": True,
        "encoded_features": len(model.coefficients()) - 1,
        "fit_seconds": fitted - start,
        "predict_seconds": predicted - fitted,
        **validation_scores(frame.loc[validation], risk),
    }
    return (
        scores,
        pd.Series(risk, index=frame.index[validation]),
        model.coefficients().assign(variant=variant, fold=fold),
    )


def evaluate_logistic_variant(
    frame: pd.DataFrame,
    variant: FeatureVariant,
    settings: LogisticSettings,
    models: ModelStore,
) -> tuple[JsonObject, pd.Series, pd.DataFrame]:
    """Validação completa de uma variante; exemplo: `evaluate_logistic_variant(df, 'rede_uf', cfg, models)`."""
    require_development(frame)
    folds, predictions, coefficients = [], [], []
    for fold in (0, 1, 2):
        scores, risk, terms = fit_validation_fold(frame, variant, fold, settings, models)
        folds.append(scores)
        predictions.append(risk)
        coefficients.append(terms)
    report: JsonObject = {
        "variant": variant,
        "folds": cast(list[JsonValue], folds),
        "summary": summarize_folds(cast(list[JsonValue], folds)),
    }
    return (
        report,
        pd.concat(predictions).reindex(frame.index),
        pd.concat(coefficients, ignore_index=True),
    )


def run_logistic(store: FileStore) -> JsonObject:
    """Lê somente a Gold de 2023; exemplo: `run_logistic(FileStore(root))`."""
    config = store.read_json("config/experimento-logistica.json")
    settings = LogisticSettings.from_definition(config)
    verify_logistic_inputs(store, config)
    ExperimentContract().validate_definition(store.read_json("config/contrato-ml-aluno.json"))
    frame = store.load_development()
    reports, predictions, coefficients = _execute_variants(frame, settings, ModelStore(store.root))
    report: JsonObject = {
        "status": "logistic_ablation_completed",
        "development_year": 2023,
        "test_2024_evaluated": False,
        "configuration": config,
        "models": cast(list[JsonValue], reports),
    }
    _save_logistic_outputs(store, report, reports, predictions, coefficients)
    return report


def _execute_variants(
    frame: pd.DataFrame,
    settings: LogisticSettings,
    models: ModelStore,
) -> tuple[list[JsonObject], pd.DataFrame, pd.DataFrame]:
    reports, coefficients = [], []
    predictions = frame[["ano", "id_aluno", "id_municipio", "fold_validacao"]].copy()
    for variant in VARIANTS:
        report, risk, terms = evaluate_logistic_variant(frame, variant, settings, models)
        predictions[f"p_risco_{variant}"] = risk
        reports.append(report)
        coefficients.append(terms)
    return reports, predictions, pd.concat(coefficients, ignore_index=True)


def _save_logistic_outputs(
    store: FileStore,
    report: JsonObject,
    variants: list[JsonObject],
    predictions: pd.DataFrame,
    coefficients: pd.DataFrame,
) -> None:
    table = comparison_table(store.read_json("reports/baseline_development.json"), variants)
    store.write_json("reports/logistica_development.json", report)
    store.write_csv("reports/logistica_comparacao_2023.csv", table)
    store.write_csv("reports/logistica_delta_enriquecimento_2023.csv", enrichment_deltas(table))
    store.write_csv("reports/logistica_coeficientes_2023.csv", coefficients)
    store.write_parquet("artifacts/logistica_oof_2023.parquet", predictions)
    store.write_text("reports/logistica_development.md", logistic_markdown(table))
    plots = LogisticPlots(store.root / "images")
    plots.comparison(table)
    plots.numeric_coefficients(coefficients)
