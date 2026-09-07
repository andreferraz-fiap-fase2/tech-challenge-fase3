"""Regressões contra aprendizado da validação, colunas indevidas e artefatos incompletos."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

from src.domain.contract import ContractError, ExperimentContract
from src.domain.logistic import LogisticSettings, variant_features
from src.evaluation.logistic import comparison_table
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.logistic import LogisticModel
from src.preprocessing.tabular import build_preprocessor
from src.usecase.baseline import evaluate_baseline
from src.usecase.logistic import fit_validation_fold, run_logistic, verify_logistic_inputs


def test_imputation_scaling_and_categories_learn_only_training() -> None:
    train = pd.DataFrame(
        {
            "rede_nome": ["Municipal", "Estadual", pd.NA, None],
            "sigla_uf": ["RO"] * 4,
            "populacao_2021": [10, 20, np.nan, 40],
            "pib_per_capita_2020": [100.0] * 4,
            "participacao_agropecuaria_2020": [1, 2, 3, 4],
            "participacao_servicos_publicos_2020": [10.0] * 4,
        }
    )
    preprocessor = build_preprocessor("completa").fit(train)
    log = preprocessor.named_transformers_["log"]
    np.testing.assert_allclose(log["imputer"].statistics_, [20, 100])
    np.testing.assert_allclose(log["scaler"].mean_[0], np.log1p([10, 20, 20, 40]).mean())
    unknown = train.iloc[[0]].assign(sigla_uf="XX", populacao_2021=1e12, rede_nome=None)
    transformed = preprocessor.transform(unknown)
    assert np.isfinite(transformed.toarray()).all()
    assert "XX" not in preprocessor.named_transformers_["categorical"]["encoder"].categories_[1]
    np.testing.assert_allclose(log["imputer"].statistics_, [20, 100])


def test_entirely_missing_training_column_keeps_matrix_shape(
    development_students: pd.DataFrame,
) -> None:
    frame = development_students.assign(populacao_2021=np.nan, sigla_uf=None)
    preprocessor = build_preprocessor("completa").fit(frame)
    training = preprocessor.transform(frame)
    later = preprocessor.transform(frame.iloc[[0]].assign(populacao_2021=1500, sigla_uf="SP"))
    assert training.shape[1] == later.shape[1]
    assert np.isfinite(later.toarray() if issparse(later) else later).all()


@pytest.mark.parametrize("variant", ["rede_uf", "completa"])
def test_outcomes_and_identifiers_never_enter_fitted_model(
    development_students: pd.DataFrame, variant: str
) -> None:
    frame = development_students.assign(proficiencia=800, gap_meta=70)
    model = LogisticModel(variant, LogisticSettings())
    model.fit(frame, frame["alfabetizado"])
    assert tuple(model.pipeline.feature_names_in_) == variant_features(variant)
    risk = model.predict_risk(frame)
    changed = frame.assign(
        proficiencia=-200, gap_meta=-90, alfabetizado=0, id_aluno="changed", peso_aluno=9
    )
    np.testing.assert_allclose(model.predict_risk(changed), risk)


def test_unknown_variant_is_rejected() -> None:
    with pytest.raises(ContractError, match="Variante"):
        variant_features("proficiencia")


def test_validation_labels_do_not_change_held_out_probabilities(
    tmp_path: Path, development_students: pd.DataFrame
) -> None:
    models = ModelStore(tmp_path)
    original = fit_validation_fold(development_students, "completa", 0, LogisticSettings(), models)
    changed = development_students.copy()
    changed.loc[changed["fold_validacao"].eq(0), "alfabetizado"] = [0, 0, 1]
    repeated = fit_validation_fold(changed, "completa", 0, LogisticSettings(), models)
    np.testing.assert_allclose(original[1], repeated[1], atol=1e-12)


def test_serialized_artifact_includes_preprocessor_and_correct_risk(
    tmp_path: Path, development_students: pd.DataFrame
) -> None:
    model = LogisticModel("completa", LogisticSettings())
    model.fit(development_students, development_students["alfabetizado"])
    store = ModelStore(tmp_path)
    store.save("model.joblib", model.pipeline)
    restored = store.load("model.joblib")
    restored_risk = restored.predict_proba(development_students[list(model.features)])[
        :, list(restored.classes_).index(0)
    ]
    np.testing.assert_allclose(restored_risk, model.predict_risk(development_students), atol=1e-12)
    terms = model.coefficients()
    np.testing.assert_allclose(terms["coefficient_risk"], -terms["coefficient_literacy"])


def test_failed_convergence_is_not_reported_as_success(development_students: pd.DataFrame) -> None:
    model = LogisticModel("completa", LogisticSettings(max_iter=1, tolerance=1e-12))
    with pytest.raises(ContractError, match="não convergiu"):
        model.fit(development_students, development_students["alfabetizado"])


def test_modified_gold_prevents_comparison(tmp_path: Path) -> None:
    store = FileStore(tmp_path)
    store.write_text("gold.txt", "changed")
    with pytest.raises(ContractError, match="SHA-256"):
        verify_logistic_inputs(store, {"expected_sha256": {"gold.txt": "0" * 64}})


def test_comparison_cannot_request_test_file_hash(tmp_path: Path) -> None:
    with pytest.raises(ContractError, match="somente desenvolvimento"):
        verify_logistic_inputs(
            FileStore(tmp_path), {"expected_sha256": {"data/ano=2024/alunos.parquet": "unread"}}
        )


class DevelopmentOnlyStore(FileStore):
    """Qualquer tentativa de ler outra partição é uma falha do teste."""

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.parquet_reads: list[str] = []

    def read_parquet(self, relative: str) -> pd.DataFrame:
        self.parquet_reads.append(relative)
        assert relative == "data/gold/ml_aluno/ano=2023/alunos.parquet"
        return super().read_parquet(relative)


def test_complete_comparison_runs_without_test_partition(
    tmp_path: Path, development_students: pd.DataFrame
) -> None:
    store = DevelopmentOnlyStore(tmp_path)
    original = FileStore(Path(__file__).resolve().parents[1])
    for name in ("experimento-logistica", "contrato-ml-aluno"):
        store.write_json(f"config/{name}.json", original.read_json(f"config/{name}.json"))
    baseline, _ = evaluate_baseline(development_students, ExperimentContract())
    store.write_json("reports/baseline_development.json", baseline)
    gold = "data/gold/ml_aluno/ano=2023/alunos.parquet"
    store.write_parquet(gold, development_students)
    config = store.read_json("config/experimento-logistica.json")
    config["expected_sha256"] = {gold: store.digest(gold)}
    store.write_json("config/experimento-logistica.json", config)
    report = run_logistic(store)
    assert report["test_2024_evaluated"] is False
    assert store.parquet_reads == [gold]
    assert len(list((tmp_path / "artifacts/logistica").rglob("*.joblib"))) == 6
    assert len(store.read_csv("reports/logistica_comparacao_2023.csv")) == 9


def test_different_validation_populations_are_not_compared(
    development_students: pd.DataFrame,
) -> None:
    baseline, _ = evaluate_baseline(development_students, ExperimentContract())
    wrong = {"variant": "completa", "folds": [{"fold": 0, "validation_rows": 100}]}
    with pytest.raises(ContractError, match="avaliações"):
        comparison_table(baseline, [wrong])


def test_configuration_cannot_claim_weighted_fit() -> None:
    store = FileStore(Path(__file__).resolve().parents[1])
    config = store.read_json("config/experimento-logistica.json")
    config["sample_weight_fit"] = True
    with pytest.raises(ContractError, match="sample_weight_fit"):
        LogisticSettings.from_definition(config)
