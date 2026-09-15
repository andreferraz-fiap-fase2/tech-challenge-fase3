"""Pontos de operação: prevalência da curva, seleção por capacidade e F2 trivial."""

import pandas as pd
import pytest

from src.domain.contract import ContractError
from src.evaluation.operating_points import (
    curve_prevalence,
    nearest_flag_rate,
    operating_points,
    trivial_f2,
)


def curve() -> pd.DataFrame:
    """Curva sintética de 100 casos, 40 positivos, com quatro limiares."""
    rows = [
        {"threshold": 0.9, "tp": 4, "fp": 1, "fn": 36, "tn": 59},
        {"threshold": 0.6, "tp": 16, "fp": 4, "fn": 24, "tn": 56},
        {"threshold": 0.3, "tp": 32, "fp": 28, "fn": 8, "tn": 32},
        {"threshold": 0.1, "tp": 40, "fp": 55, "fn": 0, "tn": 5},
    ]
    frame = pd.DataFrame(rows)
    frame["recall"] = frame["tp"] / (frame["tp"] + frame["fn"])
    frame["precision"] = frame["tp"] / (frame["tp"] + frame["fp"])
    frame["flag_rate"] = (frame["tp"] + frame["fp"]) / 100
    frame["f2"] = (
        5 * frame["precision"] * frame["recall"] / (4 * frame["precision"] + frame["recall"])
    )
    return frame


def test_prevalence_is_read_from_the_curve() -> None:
    assert curve_prevalence(curve()) == pytest.approx(0.40)


def test_curve_missing_columns_is_refused() -> None:
    with pytest.raises(ContractError, match="Curva sem"):
        curve_prevalence(pd.DataFrame({"threshold": [0.5]}))


def test_mixed_populations_are_refused() -> None:
    mixed = curve()
    mixed.loc[0, "tn"] = 500
    with pytest.raises(ContractError, match="Prevalências"):
        curve_prevalence(mixed)


def test_nearest_flag_rate_picks_the_closest_row() -> None:
    assert nearest_flag_rate(curve(), 0.20)["threshold"] == pytest.approx(0.6)
    assert nearest_flag_rate(curve(), 0.95)["threshold"] == pytest.approx(0.1)


def test_flag_target_outside_the_unit_interval_is_refused() -> None:
    with pytest.raises(ContractError, match="Alvo"):
        nearest_flag_rate(curve(), 0.0)


def test_lift_compares_precision_against_prevalence() -> None:
    table = operating_points(curve(), chosen_threshold=0.1)
    first = table.iloc[0]
    assert first["lift_sobre_prevalencia"] == pytest.approx(first["precision"] / 0.40)


def test_frozen_threshold_is_the_last_row_and_is_not_moved() -> None:
    table = operating_points(curve(), chosen_threshold=0.1)
    frozen = table.iloc[-1]
    assert frozen["criterio"] == "limiar F2 congelado"
    assert frozen["threshold"] == pytest.approx(0.1)


def test_trivial_rule_f2_matches_the_closed_form() -> None:
    # Sinalizar todos: recall 1, precisão = prevalência.
    assert trivial_f2(0.40) == pytest.approx(5 * 0.40 / (4 * 0.40 + 1))
    assert trivial_f2(0.416142) == pytest.approx(0.780881, abs=1e-6)


def test_degenerate_prevalence_is_refused() -> None:
    with pytest.raises(ContractError, match="Prevalência"):
        trivial_f2(0.0)
