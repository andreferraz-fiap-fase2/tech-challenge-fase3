"""Agregações territoriais do recorte disponível; taxas não são probabilidades de meta."""

from itertools import combinations

import numpy as np
import pandas as pd

from src.domain.contract import ContractError, ExperimentContract


def territory_summary(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    """Mantém denominadores e ponderações explícitos; exemplo: `territory_summary(df, ['regiao'])`."""
    tagged = frame.assign(
        observado=1 - frame["alfabetizado"],
        risco_ponderado=frame["p_risco"] * frame["peso_aluno"],
        observado_ponderado=(1 - frame["alfabetizado"]) * frame["peso_aluno"],
    )
    grouped = (
        tagged.groupby(groups, observed=True)
        .agg(
            avaliacoes=("id_aluno", "size"),
            municipios=("id_municipio", "nunique"),
            risco_medio=("p_risco", "mean"),
            risco_observado=("observado", "mean"),
            risco_ponderado=("risco_ponderado", "sum"),
            observado_ponderado=("observado_ponderado", "sum"),
            soma_pesos=("peso_aluno", "sum"),
        )
        .reset_index()
    )
    grouped["risco_ponderado"] /= grouped["soma_pesos"]
    grouped["observado_ponderado"] /= grouped["soma_pesos"]
    grouped["erro_risco_pp"] = 100 * (grouped["risco_medio"] - grouped["risco_observado"])
    return grouped


def goal_scenarios(municipalities: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Metas da Gold Fase 2 servem só à leitura posterior; exemplo: `goal_scenarios(mun, gold2)`."""
    targets = reference.loc[reference["ano"].eq(2024), ["id_municipio", "meta_alfabetizacao"]]
    if targets["id_municipio"].duplicated().any():
        raise ContractError("Metas duplicadas; esperado uma referência por município/2024")
    output = municipalities.merge(targets, on="id_municipio", how="left", validate="one_to_one")
    output["taxa_alfabetizacao_prevista_pct"] = 100 * (1 - output["risco_ponderado"])
    output["gap_referencia_meta_2024_pp"] = (
        output["taxa_alfabetizacao_prevista_pct"] - output["meta_alfabetizacao"]
    )
    output["gap_cenario_80pct_pp"] = output["taxa_alfabetizacao_prevista_pct"] - 80
    return output


def regional_patterns(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compara perfis de contexto com igual peso municipal; exemplo: `regional_patterns(gold2023)`."""
    context = frame.drop_duplicates("id_municipio").set_index("regiao")
    values = context[list(ExperimentContract().numeric)].astype(float)
    values.iloc[:, :2] = np.log1p(values.iloc[:, :2])
    standardized = (values - values.mean()) / values.std(ddof=0).replace(0, 1)
    profiles = standardized.groupby(level=0).mean()
    distances = [
        {
            "regiao_a": first,
            "regiao_b": second,
            "distancia_euclidiana": float(
                np.linalg.norm(profiles.loc[first] - profiles.loc[second])
            ),
        }
        for first, second in combinations(profiles.index, 2)
    ]
    return profiles.reset_index(), pd.DataFrame(distances).sort_values("distancia_euclidiana")
