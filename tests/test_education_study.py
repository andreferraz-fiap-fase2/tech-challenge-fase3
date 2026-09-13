"""Proteções do estudo complementar: população, vazamento, imputação e saídas."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.domain.contract import ContractError
from src.domain.education_study import (
    EDUCATION_FEATURES,
    study_features,
    validate_output_root,
    validate_study_definition,
)
from src.evaluation.education_study import (
    education_eda,
    join_education,
    paired_results,
    require_study_development,
)
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.education_study import EducationStudyModel
from src.usecase.education_study import study_fold, verify_hashes


@pytest.fixture
def education_context(development_students: pd.DataFrame) -> pd.DataFrame:
    context = development_students[["id_municipio", "rede_nome"]].drop_duplicates().copy()
    context[EDUCATION_FEATURES[0]] = [20.0, 25.0, 30.0]
    context[EDUCATION_FEATURES[1]] = [80.0, 85.0, 90.0]
    context[EDUCATION_FEATURES[2]] = [4.0, 4.5, 5.0]
    return context


def test_join_preserves_every_original_column_and_context_eda(
    development_students: pd.DataFrame, education_context: pd.DataFrame
) -> None:
    frame, coverage = join_education(development_students, education_context)
    pd.testing.assert_frame_equal(development_students, frame[development_students.columns])
    assert coverage["student_nonmissing"].tolist() == [9, 9, 9]
    assert coverage["context_nonmissing"].tolist() == [3, 3, 3]
    distribution, correlations = education_eda(frame)
    assert distribution["count"].tolist() == [3, 3, 3]
    assert correlations["complete_contexts"].tolist() == [3, 3, 3]


@pytest.mark.parametrize("problem", ["duplicate_context", "missing_coverage", "label_column"])
def test_invalid_join_rejected(
    development_students: pd.DataFrame, education_context: pd.DataFrame, problem: str
) -> None:
    if problem == "duplicate_context":
        education_context = pd.concat([education_context, education_context.iloc[:1]])
    elif problem == "missing_coverage":
        education_context.iloc[0, education_context.columns.get_loc(EDUCATION_FEATURES[0])] = np.nan
    else:
        education_context["alfabetizado"] = 1
    with pytest.raises(ContractError):
        join_education(development_students, education_context)


@pytest.mark.parametrize("problem", ["year", "duplicate_student", "split_municipality", "fold_map"])
def test_invalid_development_rejected(development_students: pd.DataFrame, problem: str) -> None:
    frame = development_students.copy()
    folds = (
        frame[["id_municipio", "fold_validacao"]]
        .drop_duplicates()
        .rename(columns={"fold_validacao": "fold"})
    )
    if problem == "year":
        frame.loc[0, "ano"] = 2024
    elif problem == "duplicate_student":
        frame.loc[1, "id_aluno"] = frame.loc[0, "id_aluno"]
    elif problem == "split_municipality":
        frame.loc[3, "id_municipio"] = frame.loc[0, "id_municipio"]
    else:
        folds["fold"] = (folds["fold"] + 1) % 3
    with pytest.raises(ContractError):
        require_study_development(frame, folds)


def test_imputation_and_categories_learned_only_from_training(
    development_students: pd.DataFrame, education_context: pd.DataFrame, tmp_path: Path
) -> None:
    frame, _ = join_education(development_students, education_context)
    frame.loc[frame["fold_validacao"].eq(0), EDUCATION_FEATURES[0]] = 999.0
    frame.loc[frame["fold_validacao"].eq(1), EDUCATION_FEATURES[0]] = np.nan
    model = EducationStudyModel("ibge_inep")
    train = frame.loc[frame["fold_validacao"].ne(0)]
    model.fit(train, train["alfabetizado"])
    imputer = model.pipeline["preprocessing"].named_transformers_["numeric"]
    assert imputer.statistics_[4] == 30.0
    validation = frame.loc[frame["fold_validacao"].eq(0)].assign(sigla_uf="XX")
    validation[EDUCATION_FEATURES[0]] = np.nan
    transformed = model.pipeline["preprocessing"].transform(validation[list(model.features)])
    assert np.isnan(transformed[:, 1]).all()
    assert (transformed[:, 6] == 30.0).all()
    assert np.isfinite(model.predict_risk(validation)).all()
    assert tuple(model.pipeline.feature_names_in_) == study_features("ibge_inep")
    estimator = model.pipeline["classifier"]
    assert estimator.do_early_stopping_ is False
    assert estimator.is_categorical_.tolist() == [True, True] + [False] * 7
    store = ModelStore(tmp_path)
    store.save("model.joblib", model.pipeline)
    assert tuple(store.load("model.joblib").feature_names_in_) == study_features("ibge_inep")


@pytest.mark.parametrize("variant", ["ibge", "ibge_inep"])
def test_metadata_and_validation_labels_do_not_change_predictions(
    development_students: pd.DataFrame, education_context: pd.DataFrame, variant: str
) -> None:
    frame, _ = join_education(development_students, education_context)
    _, original = study_fold(frame, variant, 0)
    changed = frame.assign(proficiencia=999, peso_aluno=999)
    selected = changed["fold_validacao"].eq(0)
    changed.loc[selected, "alfabetizado"] = 1 - changed.loc[selected, "alfabetizado"]
    _, repeated = study_fold(changed, variant, 0)
    np.testing.assert_array_equal(original, repeated)
    assert "proficiencia" not in study_features(variant)
    assert "alfabetizado" not in study_features(variant)
    assert "id_municipio" not in study_features(variant)


@pytest.mark.parametrize(
    "key,value",
    [
        ("development_year", 2024),
        ("education_features", ["proficiencia"]),
        ("max_iter", 200),
        ("threshold_search", True),
        ("calibration_fit", True),
    ],
)
def test_protocol_changes_rejected(key: str, value: object) -> None:
    root = FileStore(Path(__file__).resolve().parents[1])
    definition = root.read_json("config/estudo-educacional.json")
    definition[key] = value
    with pytest.raises(ContractError, match=key):
        validate_study_definition(definition)


def test_output_guard_rejects_internal_nonempty_and_symlink(tmp_path: Path) -> None:
    root = tmp_path / "experiment"
    root.mkdir()
    for path in (root, root / "output", tmp_path):
        with pytest.raises(ContractError):
            validate_output_root(root, path)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(ContractError):
        validate_output_root(root, alias / "output")
    output = tmp_path / "output"
    output.mkdir()
    assert validate_output_root(root, output) == output
    (output / "existing.txt").write_text("preservar")
    with pytest.raises(ContractError):
        validate_output_root(root, output)


def test_hash_change_blocks_execution(tmp_path: Path) -> None:
    source = FileStore(tmp_path)
    source.write_text("input.txt", "original")
    expected = {"input.txt": source.digest("input.txt")}
    verify_hashes(source, expected)
    source.write_text("input.txt", "modificado")
    with pytest.raises(ContractError, match="SHA-256"):
        verify_hashes(source, expected)


def test_six_fold_models_and_complete_oof_without_test_year(
    development_students: pd.DataFrame, education_context: pd.DataFrame, tmp_path: Path
) -> None:
    frame, _ = join_education(development_students, education_context)
    rows = []
    for variant in ("ibge", "ibge_inep"):
        parts = []
        for fold in (0, 1, 2):
            scores, prediction = study_fold(frame, variant, fold, ModelStore(tmp_path))
            rows.append(scores)
            parts.append(prediction)
        combined = pd.concat(parts).reindex(frame.index)
        assert len(combined) == len(frame)
        assert np.isfinite(combined).all()
    summary, delta = paired_results(pd.DataFrame(rows))
    assert set(summary["variant"]) == {"ibge", "ibge_inep"}
    assert delta["fold"].tolist() == [0, 1, 2]
    assert len(list(tmp_path.rglob("*.joblib"))) == 6
    assert not (tmp_path / "data/gold/ml_aluno/ano=2024").exists()
