"""Busca na amostra e confirmação completa, sempre nos folds municipais de 2023."""

from dataclasses import asdict
from time import perf_counter
from typing import cast

import pandas as pd

from src.domain.boosting import BoostingCandidate, BoostingSettings
from src.domain.contract import ExperimentContract, JsonObject, JsonValue
from src.domain.logistic import VARIANTS, FeatureVariant
from src.evaluation.development import require_development
from src.evaluation.logistic import comparison_table, validation_scores
from src.evaluation.summary import summarize_folds
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.boosting import BoostingModel
from src.preprocessing.search_sample import development_sample
from src.usecase.logistic import verify_logistic_inputs


def boosting_fold(
    frame: pd.DataFrame,
    variant: FeatureVariant,
    fold: int,
    candidate: BoostingCandidate,
    settings: BoostingSettings,
    models: ModelStore | None = None,
) -> tuple[JsonObject, pd.Series]:
    require_development(frame)
    validation = frame["fold_validacao"].eq(fold)
    model = BoostingModel(variant, candidate, settings)
    start = perf_counter()
    model.fit(frame.loc[~validation], frame.loc[~validation, "alfabetizado"])
    fitted = perf_counter()
    risk = model.predict_risk(frame.loc[validation])
    predicted = perf_counter()
    if models is not None:
        models.save(f"artifacts/boosting/{variant}/fold_{fold}.joblib", model.pipeline)
    scores: JsonObject = {
        "fold": fold,
        "training_rows": int((~validation).sum()),
        "validation_rows": int(validation.sum()),
        "n_iterations": int(model.pipeline.named_steps["classifier"].n_iter_),
        "fit_seconds": fitted - start,
        "predict_seconds": predicted - fitted,
        **validation_scores(frame.loc[validation], risk),
    }
    return scores, pd.Series(risk, index=frame.index[validation])


def evaluate_boosting(
    frame: pd.DataFrame,
    variant: FeatureVariant,
    candidate: BoostingCandidate,
    settings: BoostingSettings,
    models: ModelStore | None = None,
) -> tuple[JsonObject, pd.Series]:
    folds, predictions = [], []
    for fold in (0, 1, 2):
        scores, risk = boosting_fold(frame, variant, fold, candidate, settings, models)
        folds.append(scores)
        predictions.append(risk)
    report: JsonObject = {
        "variant": f"boosting_{variant}",
        "candidate": cast(JsonObject, asdict(candidate)),
        "folds": cast(list[JsonValue], folds),
        "summary": summarize_folds(cast(list[JsonValue], folds)),
    }
    return report, pd.concat(predictions).reindex(frame.index)


def search_variant(
    sample: pd.DataFrame, variant: FeatureVariant, settings: BoostingSettings
) -> tuple[BoostingCandidate, pd.DataFrame]:
    rows: list[JsonObject] = []
    for candidate in settings.candidates:
        report, _ = evaluate_boosting(sample, variant, candidate, settings)
        for fold in cast(list[JsonObject], report["folds"]):
            rows.append(
                {
                    "variant": variant,
                    **asdict(candidate),
                    "fold": fold["fold"],
                    "training_rows": fold["training_rows"],
                    "validation_rows": fold["validation_rows"],
                    "fit_seconds": fold["fit_seconds"],
                    "predict_seconds": fold["predict_seconds"],
                    **cast(JsonObject, fold["unweighted"]),
                }
            )
    table = pd.DataFrame(rows).drop(columns="confusion_tn_fp_fn_tp")
    ranking = (
        table.groupby(["name", "max_leaf_nodes", "max_iter"], as_index=False)[
            "average_precision_risk"
        ]
        .mean()
        .sort_values(
            ["average_precision_risk", "max_leaf_nodes", "max_iter", "name"],
            ascending=[False, True, True, True],
        )
    )
    winner = next(c for c in settings.candidates if c.name == ranking.iloc[0]["name"])
    table["selected"] = table["name"].eq(winner.name)
    return winner, table


def run_boosting(store: FileStore) -> JsonObject:
    config = store.read_json("config/experimento-boosting.json")
    settings = BoostingSettings.from_definition(config)
    verify_logistic_inputs(store, config)
    ExperimentContract().validate_definition(store.read_json("config/contrato-ml-aluno.json"))
    frame = store.load_development()
    sample = development_sample(frame, settings)
    reports, searches = [], []
    predictions = frame[["ano", "id_aluno", "id_municipio", "fold_validacao"]].copy()
    for variant in VARIANTS:
        winner, search = search_variant(sample, variant, settings)
        searches.append(search)
        report, risk = evaluate_boosting(frame, variant, winner, settings, ModelStore(store.root))
        reports.append(report)
        predictions[f"p_risco_{variant}"] = risk
    return _save_outputs(store, config, sample, reports, pd.concat(searches), predictions)


def _save_outputs(
    store: FileStore,
    config: JsonObject,
    sample: pd.DataFrame,
    reports: list[JsonObject],
    search: pd.DataFrame,
    predictions: pd.DataFrame,
) -> JsonObject:
    sample_path = "artifacts/boosting_amostra_2023.parquet"
    store.write_parquet(sample_path, sample[["ano", "id_aluno", "id_municipio", "fold_validacao"]])
    report: JsonObject = {
        "status": "boosting_search_and_full_development_completed",
        "development_year": 2023,
        "test_2024_evaluated": False,
        "configuration": config,
        "selection_bias_note": "Non-nested development CV: selected on a subset of the same folds; not an unbiased final estimate.",
        "sample": {
            "rows": len(sample),
            "municipalities": int(sample["id_municipio"].nunique()),
            "keys_sha256": store.digest(sample_path),
            "folds": cast(
                list[JsonValue],
                sample.groupby("fold_validacao")
                .agg(rows=("id_aluno", "size"), municipalities=("id_municipio", "nunique"))
                .reset_index()
                .to_dict("records"),
            ),
        },
        "models": cast(list[JsonValue], reports),
    }
    logistic = cast(
        list[JsonObject], store.read_json("reports/logistica_development.json")["models"]
    )
    table = comparison_table(
        store.read_json("reports/baseline_development.json"), logistic + reports
    )
    store.write_json("reports/boosting_development.json", report)
    store.write_csv("reports/boosting_busca_2023.csv", search)
    store.write_csv("reports/modelos_comparacao_2023.csv", table)
    store.write_parquet("artifacts/boosting_oof_2023.parquet", predictions)
    return report
