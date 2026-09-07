"""Garante a orientação do risco e o isolamento da avaliação final."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.domain.contract import ContractError, ExperimentContract
from src.evaluation.development import numeric_summary, require_development
from src.evaluation.metrics import risk_metrics
from src.infrastructure.files import FileStore
from src.modeling.baseline import PriorBaseline
from src.usecase.baseline import evaluate_baseline


def test_prior_uses_training_frequencies_only() -> None:
    train = pd.DataFrame({"x": [1, 2, 3, 4]})
    validation = pd.DataFrame({"x": [10000, -10000]})
    risk = PriorBaseline().fit_predict(train, pd.Series([1, 1, 1, 0]), validation)
    np.testing.assert_allclose(risk, [0.25, 0.25])


def test_metrics_use_non_literate_as_risk_class() -> None:
    metrics = risk_metrics(np.array([1, 1, 0, 0], dtype=np.int8), np.array([0.1, 0.2, 0.8, 0.9]))
    assert metrics["roc_auc_risk"] == 1.0
    assert metrics["recall_risk"] == 1.0
    assert metrics["confusion_tn_fp_fn_tp"] == [2.0, 0.0, 0.0, 2.0]


def test_2024_is_rejected_by_development_analysis(development_students: pd.DataFrame) -> None:
    development_students.loc[0, "ano"] = 2024
    with pytest.raises(ContractError, match="2023"):
        require_development(development_students)


def test_municipality_cannot_cross_validation_folds(development_students: pd.DataFrame) -> None:
    development_students.loc[0, "fold_validacao"] = 1
    with pytest.raises(ContractError, match="múltiplos folds"):
        require_development(development_students)


def test_prior_does_not_use_validation_labels(development_students: pd.DataFrame) -> None:
    _, predictions = evaluate_baseline(development_students, ExperimentContract())
    np.testing.assert_allclose(
        predictions["p_nao_alfabetizado"], [0.5] * 3 + [1 / 3] * 3 + [0.5] * 3
    )


def test_numeric_distribution_counts_municipalities_once(
    development_students: pd.DataFrame,
) -> None:
    summary = numeric_summary(development_students, ExperimentContract())
    assert set(summary["count"]) == {3.0}


class RecordingStore(FileStore):
    def __init__(self, root: Path, frame: pd.DataFrame) -> None:
        super().__init__(root)
        self.frame = frame
        self.read_paths: list[str] = []

    def read_parquet(self, relative: str) -> pd.DataFrame:
        self.read_paths.append(relative)
        if "ano=2024" in relative:
            raise AssertionError("Teste temporal não deve ser acessado")
        return self.frame.copy()


def test_loader_accesses_only_development_file(
    tmp_path: Path, development_students: pd.DataFrame
) -> None:
    store = RecordingStore(tmp_path, development_students)
    loaded = store.load_development()
    assert len(loaded) == 9
    assert store.read_paths == ["data/gold/ml_aluno/ano=2023/alunos.parquet"]


def test_wrong_snapshot_hash_prevents_import(tmp_path: Path) -> None:
    source = tmp_path / "wrong.csv"
    source.write_text("unexpected")
    store = FileStore(tmp_path / "workspace")
    with pytest.raises(ContractError, match="SHA-256"):
        store.copy_verified(source, "data/input/copy.csv", "0" * 64)
    assert not (tmp_path / "workspace/data/input/copy.csv").exists()


@pytest.mark.parametrize("replacement", [1, 4])
def test_missing_or_unknown_folds_are_rejected(
    development_students: pd.DataFrame, replacement: int
) -> None:
    modified = development_students.replace({"fold_validacao": {2: replacement}})
    with pytest.raises(ContractError, match="exatamente 0, 1 e 2"):
        require_development(modified)


@pytest.mark.parametrize("label", [0, 1])
def test_single_class_metrics_fail_instead_of_saving_nan(label: int) -> None:
    with pytest.raises(ContractError, match="ambas as classes"):
        risk_metrics(np.array([label, label], dtype=np.int8), np.array([0.4, 0.4]))
