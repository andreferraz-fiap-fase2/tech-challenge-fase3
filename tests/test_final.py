"""Garantias da escolha pré-teste, empates e persistência do ajuste final."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import fbeta_score

from src.domain.contract import ContractError
from src.evaluation.threshold import decision_metrics, f2_curve
from src.infrastructure.files import FileStore
from src.pipeline import main
from src.usecase.final_fit import run_final_fit
from src.usecase.freeze import DECISION, GOLD, OOF, TEST_GOLD, run_freeze
from src.usecase.temporal import evaluate_locked_test


@pytest.fixture
def final_store(tmp_path: Path, development_students: pd.DataFrame) -> FileStore:
    store = FileStore(tmp_path)
    original = FileStore(Path(__file__).resolve().parents[1])
    frame = development_students
    store.write_parquet(GOLD, frame)
    keys = ["ano", "id_aluno", "id_municipio", "fold_validacao"]
    store.write_parquet(
        OOF, frame[keys].assign(p_risco_completa=[0.2, 0.3, 0.8, 0.7, 0.6, 0.2, 0.4, 0.7, 0.1])
    )
    for name in ("contrato-ml-aluno.json", "experimento-boosting.json"):
        store.write_json(f"config/{name}", original.read_json(f"config/{name}"))
    store.write_text("config/folds-municipios-2023.csv", "fixture: frozen municipality folds\n")
    config = store.read_json("config/experimento-boosting.json")
    config.update(min_samples_leaf=2, expected_sha256={GOLD: store.digest(GOLD)})
    store.write_json("config/experimento-boosting.json", config)
    store.write_csv(
        "reports/modelos_comparacao_2023.csv",
        pd.DataFrame(
            {
                "model": ["boosting_completa"] * 3,
                "fold": [0, 1, 2],
                "average_precision_risk": [0.9, 0.8, 0.7],
            }
        ),
    )
    store.write_json(
        "reports/boosting_development.json",
        {
            "models": [
                {
                    "variant": "boosting_completa",
                    "candidate": {"name": "small", "max_iter": 3, "max_leaf_nodes": 3},
                }
            ]
        },
    )
    return store


def test_threshold_curve_matches_direct_decisions_with_ties() -> None:
    y, p = np.array([0, 1, 0, 1, 0, 1]), np.array([0.5, 0.5, 0.8, 0.2, 0.5, 0.8])
    curve = f2_curve(y, p)
    assert len(curve) == 3
    for row in curve.itertuples():
        assert row.f2 == pytest.approx(fbeta_score(1 - y, p >= row.threshold, beta=2))
        assert row.flag_rate == pytest.approx(np.mean(p >= row.threshold))
    assert decision_metrics(y, p, 1.0)["precision"] == 0


@pytest.mark.parametrize("risk", [[-0.1, 0.5], [0.2, 1.1], [np.nan, 0.1]])
def test_invalid_probabilities_are_rejected(risk: list[float]) -> None:
    with pytest.raises(ContractError, match="Probabilidades"):
        f2_curve(np.array([0, 1]), np.array(risk))


def test_freeze_and_fit_require_only_2023(final_store: FileStore) -> None:
    decision = run_freeze(final_store)
    assert decision["test_2024_evaluated_at_freeze"] is False
    assert decision["risk_threshold"] == 0.6
    report = run_final_fit(final_store)
    assert report["training_rows"] == 9
    assert report["test_2024_read"] is False
    assert not (final_store.root / "data/gold/ml_aluno/ano=2024").exists()
    with pytest.raises(ContractError, match="já existe"):
        run_freeze(final_store)
    with pytest.raises(ContractError, match="já existe"):
        run_final_fit(final_store)


def test_misaligned_oof_keys_cannot_select_threshold(final_store: FileStore) -> None:
    oof = final_store.read_parquet(OOF).iloc[::-1]
    final_store.write_parquet(OOF, oof)
    with pytest.raises(ContractError, match="Chaves OOF"):
        run_freeze(final_store)
    assert not (final_store.root / DECISION).exists()


def test_changed_inputs_cannot_fit_frozen_model(final_store: FileStore) -> None:
    run_freeze(final_store)
    final_store.write_text("config/folds-municipios-2023.csv", "modified")
    with pytest.raises(ContractError, match="SHA-256"):
        run_final_fit(final_store)


def test_temporal_slices_and_reexecution_guard(final_store: FileStore) -> None:
    run_freeze(final_store)
    frame = final_store.load_development().assign(ano=2024, particao="teste_reservado")
    frame.loc[frame["id_municipio"].eq("m2"), "id_municipio"] = "new"
    final_store.write_parquet(TEST_GOLD, frame)
    decision = final_store.read_json(DECISION)
    decision["test_gold_sha256"] = final_store.digest(TEST_GOLD)
    final_store.write_json(DECISION, decision)
    run_final_fit(final_store)
    report = evaluate_locked_test(final_store, 9)
    assert report["slices"]["municipios_novos"]["rows"] == 3
    assert report["slices"]["municipios_conhecidos"]["rows"] == 6
    assert report["test_used_for_tuning"] is False
    with pytest.raises(ContractError, match="Teste já executado"):
        evaluate_locked_test(final_store, 9)


def test_decision_change_after_fit_is_blocked_before_test_read(final_store: FileStore) -> None:
    run_freeze(final_store)
    run_final_fit(final_store)
    decision = final_store.read_json(DECISION)
    decision["risk_threshold"] = 0.99
    final_store.write_json(DECISION, decision)
    with pytest.raises(ContractError, match="SHA-256"):
        evaluate_locked_test(final_store, 9)


def test_cli_preserves_frozen_development(
    final_store: FileStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    final_store.write_json(DECISION, {"frozen": True})
    for command in ("run-all", "logistic", "boosting"):
        monkeypatch.setattr("sys.argv", ["pipeline", "--root", str(final_store.root), command])
        with pytest.raises(ContractError, match="Entrega congelada"):
            main()
    assert final_store.read_json(DECISION) == {"frozen": True}
