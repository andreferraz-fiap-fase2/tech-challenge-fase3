"""Separação municipal, busca determinística e pipeline persistida do boosting."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from threadpoolctl import threadpool_limits

from src.domain.boosting import BoostingCandidate, BoostingSettings
from src.domain.contract import ContractError, ExperimentContract
from src.domain.logistic import variant_features
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.boosting import BoostingModel
from src.preprocessing.boosting import boosting_preprocessor
from src.preprocessing.search_sample import development_sample
from src.usecase.baseline import evaluate_baseline
from src.usecase.boosting import boosting_fold, run_boosting, search_variant


@pytest.fixture
def settings() -> BoostingSettings:
    return BoostingSettings(3, (BoostingCandidate("small", 3, 3),), min_samples_leaf=2)


def test_sample_is_order_and_label_independent(
    development_students: pd.DataFrame,
    settings: BoostingSettings,
) -> None:
    settings = replace(settings, sample_per_fold=2)
    original = development_sample(development_students, settings)
    changed = development_students.sample(frac=1, random_state=31).assign(alfabetizado=0)
    repeated = development_sample(changed, settings)
    assert original["id_aluno"].tolist() == repeated["id_aluno"].tolist()
    assert original.groupby("fold_validacao").size().tolist() == [2, 2, 2]
    assert original.groupby("id_municipio")["fold_validacao"].nunique().eq(1).all()


@pytest.mark.parametrize("problem", ["test_year", "duplicate_key", "split_municipality"])
def test_invalid_sample_is_rejected(
    development_students: pd.DataFrame,
    settings: BoostingSettings,
    problem: str,
) -> None:
    frame = development_students.copy()
    if problem == "test_year":
        frame["ano"] = 2024
    elif problem == "duplicate_key":
        frame.loc[1, "id_aluno"] = frame.loc[0, "id_aluno"]
    else:
        frame.loc[3, "id_municipio"] = "m0"
    with pytest.raises(ContractError):
        development_sample(frame, settings)


def test_preprocessing_learns_training_only(development_students: pd.DataFrame) -> None:
    train = development_students.assign(populacao_2021=[10, 20, np.nan] * 3)
    preprocessing = boosting_preprocessor("completa").fit(train)
    changed = train.iloc[[0]].assign(sigla_uf="XX", populacao_2021=np.nan)
    encoded = preprocessing.transform(changed)
    assert np.isnan(encoded[0, 1])
    assert encoded[0, 2] == 15
    assert "XX" not in preprocessing.named_transformers_["categorical"]["encoder"].categories_[1]


@pytest.mark.parametrize("variant", ["rede_uf", "completa"])
def test_pipeline_risk_allowlist_and_roundtrip(
    tmp_path: Path,
    development_students: pd.DataFrame,
    settings: BoostingSettings,
    variant: str,
) -> None:
    model = BoostingModel(variant, settings.candidates[0], settings)
    model.fit(development_students, development_students["alfabetizado"])
    assert tuple(model.pipeline.feature_names_in_) == variant_features(variant)
    estimator = model.pipeline.named_steps["classifier"]
    assert estimator.do_early_stopping_ is False
    assert estimator.is_categorical_.tolist() == [True, True] + [False] * (len(model.features) - 2)
    changed = development_students.assign(
        alfabetizado=0, peso_aluno=99, proficiencia=999, id_aluno="x"
    )
    np.testing.assert_allclose(
        model.predict_risk(changed), model.predict_risk(development_students)
    )
    store = ModelStore(tmp_path)
    store.save("model.joblib", model.pipeline)
    with threadpool_limits(limits=1):
        restored = store.load("model.joblib").predict_proba(changed[list(model.features)])[:, 0]
    np.testing.assert_allclose(restored, model.predict_risk(changed), atol=1e-12)
    assert np.isfinite(model.predict_risk(changed.assign(sigla_uf="XX", rede_nome=None))).all()


def test_validation_labels_cannot_change_fixed_candidate_predictions(
    development_students: pd.DataFrame,
    settings: BoostingSettings,
) -> None:
    original = boosting_fold(development_students, "completa", 0, settings.candidates[0], settings)
    changed = development_students.copy()
    changed.loc[changed["fold_validacao"].eq(0), "alfabetizado"] = [0, 0, 1]
    repeated = boosting_fold(changed, "completa", 0, settings.candidates[0], settings)
    np.testing.assert_allclose(original[1], repeated[1], atol=1e-12)


def test_search_ties_choose_simpler_candidate(
    development_students: pd.DataFrame,
    settings: BoostingSettings,
) -> None:
    settings = replace(
        settings, candidates=(BoostingCandidate("larger", 4, 4), *settings.candidates)
    )
    winner, search = search_variant(development_students, "completa", settings)
    assert winner.name == "small"
    assert search.loc[search["selected"], "name"].unique().tolist() == ["small"]


@pytest.mark.parametrize(
    "key,value",
    [("early_stopping", "auto"), ("sample_weight_fit", True), ("development_year", 2024)],
)
def test_configuration_rejects_protocol_changes(key: str, value: str | bool | int) -> None:
    config = FileStore(Path(__file__).resolve().parents[1]).read_json(
        "config/experimento-boosting.json"
    )
    config[key] = value
    with pytest.raises(ContractError, match=key):
        BoostingSettings.from_definition(config)


def test_search_and_confirmation_work_without_2024(
    tmp_path: Path,
    development_students: pd.DataFrame,
) -> None:
    store = FileStore(tmp_path)
    original = FileStore(Path(__file__).resolve().parents[1])
    config = original.read_json("config/experimento-boosting.json")
    config.update(
        sample_per_fold=3,
        min_samples_leaf=2,
        candidates=[
            {"name": "small", "max_iter": 3, "max_leaf_nodes": 3},
        ],
    )
    gold = "data/gold/ml_aluno/ano=2023/alunos.parquet"
    store.write_parquet(gold, development_students)
    config["expected_sha256"] = {gold: store.digest(gold)}
    store.write_json("config/experimento-boosting.json", config)
    store.write_json(
        "config/contrato-ml-aluno.json", original.read_json("config/contrato-ml-aluno.json")
    )
    baseline, _ = evaluate_baseline(development_students, ExperimentContract())
    store.write_json("reports/baseline_development.json", baseline)
    store.write_json("reports/logistica_development.json", {"models": []})
    result = run_boosting(store)
    assert result["test_2024_evaluated"] is False
    assert not (tmp_path / "data/gold/ml_aluno/ano=2024").exists()
    assert len(list((tmp_path / "artifacts/boosting").rglob("*.joblib"))) == 6
    oof = store.read_parquet("artifacts/boosting_oof_2023.parquet")
    assert len(oof) == len(development_students)
    assert not oof[["ano", "id_aluno"]].duplicated().any()
    assert oof.filter(like="p_risco").notna().all().all()
