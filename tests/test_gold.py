"""Regressões contra contaminação da população, junções e alvo."""

import pandas as pd
import pytest

from src.domain.contract import ContractError, ExperimentContract
from src.preprocessing.gold import assign_partition, build_gold, eligible_batch, select_predictors
from src.preprocessing.validation import join_context, verify_original_matches_batch


def test_gold_excludes_simulation_absences_private_and_unscored(
    raw_students: pd.DataFrame,
    silver_students: pd.DataFrame,
    context_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    result = build_gold(raw_students, silver_students, *context_inputs, 2023, ExperimentContract())
    assert result.frame["id_aluno"].tolist() == ["a", "b"]
    assert result.frame["alfabetizado"].tolist() == [1, 0]
    assert result.audit["simulated_removed"] == 1
    assert result.audit["after_presence"] == 3
    assert result.audit["eligible_rows"] == 2
    assert "proficiencia" not in result.frame
    assert result.frame["fold_validacao"].tolist() == [0, 1]


def test_silver_label_corruption_is_not_silently_used(
    raw_students: pd.DataFrame, silver_students: pd.DataFrame
) -> None:
    silver_students.loc[0, "alfabetizado"] = False
    with pytest.raises(ContractError, match="divergente"):
        verify_original_matches_batch(raw_students, silver_students.query("origem == 'batch'"))


def test_source_duplicate_is_blocked(
    raw_students: pd.DataFrame, silver_students: pd.DataFrame
) -> None:
    duplicated = pd.concat([raw_students, raw_students.iloc[[0]]])
    with pytest.raises(ContractError, match="Chave inválida"):
        verify_original_matches_batch(duplicated, silver_students.query("origem == 'batch'"))


@pytest.mark.parametrize("invalid", ["2", "Sim", ""])
def test_unknown_source_labels_are_not_coerced_to_false(
    raw_students: pd.DataFrame, silver_students: pd.DataFrame, invalid: str
) -> None:
    raw_students.loc[0, "alfabetizado"] = invalid
    with pytest.raises(ContractError, match="códigos 0/1"):
        verify_original_matches_batch(raw_students, silver_students.query("origem == 'batch'"))


def test_valid_evaluation_requires_consistent_threshold(silver_students: pd.DataFrame) -> None:
    silver_students.loc[0, "alfabetizado"] = False
    with pytest.raises(ContractError, match="proficiência >= 743"):
        eligible_batch(silver_students)


@pytest.mark.parametrize("weight", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_weights_block_weighted_population(
    silver_students: pd.DataFrame, weight: float
) -> None:
    silver_students.loc[0, "peso_aluno"] = weight
    with pytest.raises(ContractError, match="Peso inválido"):
        eligible_batch(silver_students)


def test_duplicate_context_cannot_multiply_students(
    context_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    context, municipalities, _, _ = context_inputs
    with pytest.raises(ContractError, match="Chave inválida"):
        join_context(municipalities, pd.concat([context, context.iloc[[0]]]), "id_municipio")


def test_missing_municipality_context_is_not_silently_dropped(
    context_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    context, municipalities, _, _ = context_inputs
    with pytest.raises(ContractError, match="1100023"):
        join_context(municipalities, context.iloc[[0]], "id_municipio")


def test_test_partition_has_no_validation_fold(
    context_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    _, municipalities, _, folds = context_inputs
    result = assign_partition(municipalities, folds, 2024)
    assert result["fold_validacao"].isna().all()
    assert set(result["particao"]) == {"teste_reservado"}


def test_predictor_allowlist_excludes_outcomes_and_weights(
    development_students: pd.DataFrame,
) -> None:
    frame = development_students.assign(proficiencia=800.0, gap_meta=10.0)
    selected = select_predictors(frame, ExperimentContract())
    assert selected.columns.tolist() == list(ExperimentContract().features)
    assert not {"alfabetizado", "proficiencia", "peso_aluno", "gap_meta", "id_aluno"} & set(
        selected
    )


def test_modified_predictor_contract_cannot_include_proficiency(
    development_students: pd.DataFrame,
) -> None:
    contract = ExperimentContract(numeric=("proficiencia",))
    with pytest.raises(ContractError, match="Lista de preditores alterada"):
        select_predictors(development_students.assign(proficiencia=800), contract)
