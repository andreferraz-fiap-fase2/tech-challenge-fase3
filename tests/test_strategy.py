"""Unidade municipal da explicação, denominadores e comparação posterior com metas."""

import numpy as np
import pandas as pd
import pytest

from src.domain.contract import ContractError
from src.evaluation.interpretation import permute_feature
from src.evaluation.territory import goal_scenarios, regional_patterns, territory_summary


def test_territorial_permutation_keeps_one_value_per_municipality(
    development_students: pd.DataFrame,
) -> None:
    frame = development_students.assign(populacao_2021=[10] * 3 + [20] * 3 + [30] * 3)
    shuffled = permute_feature(frame, "populacao_2021", 42)
    assert shuffled.groupby("id_municipio")["populacao_2021"].nunique().eq(1).all()
    assert sorted(shuffled.populacao_2021) == sorted(frame.populacao_2021)
    pd.testing.assert_series_equal(shuffled.alfabetizado, frame.alfabetizado)
    pd.testing.assert_frame_equal(shuffled, permute_feature(frame, "populacao_2021", 42))


def test_weighted_territory_uses_weight_sum_not_student_count(
    development_students: pd.DataFrame,
) -> None:
    frame = development_students.iloc[:3].assign(
        p_risco=[0.1, 0.3, 0.9], peso_aluno=[1.0, 1.0, 2.0]
    )
    row = territory_summary(frame, ["id_municipio"]).iloc[0]
    assert row.risco_ponderado == pytest.approx(0.55)
    assert row.observado_ponderado == 0.5
    assert row.avaliacoes == 3
    assert row.soma_pesos == 4


def test_goal_gap_keeps_missing_targets_and_is_in_percentage_points() -> None:
    municipalities = pd.DataFrame({"id_municipio": ["a", "b"], "risco_ponderado": [0.3, 0.6]})
    reference = pd.DataFrame({"id_municipio": ["a"], "ano": [2024], "meta_alfabetizacao": [80.0]})
    output = goal_scenarios(municipalities, reference)
    assert output.iloc[0].gap_referencia_meta_2024_pp == pytest.approx(-10)
    assert np.isnan(output.iloc[1].gap_referencia_meta_2024_pp)
    with pytest.raises(ContractError, match="Metas duplicadas"):
        goal_scenarios(municipalities, pd.concat([reference, reference]))


def test_region_profiles_do_not_repeat_context_by_student_volume(
    development_students: pd.DataFrame,
) -> None:
    frame = development_students.assign(
        regiao=["N"] * 3 + ["S"] * 6, populacao_2021=[100] * 3 + [200] * 3 + [300] * 3
    )
    first, pairs = regional_patterns(frame)
    repeated, _ = regional_patterns(pd.concat([frame, frame.iloc[:3]]))
    pd.testing.assert_frame_equal(first, repeated)
    assert len(pairs) == 1
