"""Resumos descritivos calculados exclusivamente no desenvolvimento de 2023."""

import pandas as pd

from src.domain.contract import ContractError, ExperimentContract, JsonObject


def require_development(frame: pd.DataFrame) -> None:
    """Recusa mistura de ciclos; exemplo: `require_development(gold_2023)`."""
    if set(frame["ano"]) != {2023} or frame["fold_validacao"].isna().any():
        raise ContractError(
            "Conjunto de desenvolvimento inválido; esperado 2023 com folds completos"
        )
    if set(frame["fold_validacao"]) != {0, 1, 2}:
        raise ContractError(f"Folds={set(frame['fold_validacao'])}; esperado exatamente 0, 1 e 2")
    if frame.groupby("id_municipio")["fold_validacao"].nunique().gt(1).any():
        raise ContractError("Município em múltiplos folds; esperado um único fold por município")


def group_summary(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Resume contagens e taxas, mantendo pesos explícitos; exemplo: `group_summary(df, 'regiao')`."""
    tagged = frame.assign(
        risk=1 - frame["alfabetizado"],
        weighted_risk=(1 - frame["alfabetizado"]) * frame["peso_aluno"],
    )
    grouped = (
        tagged.groupby(column, observed=True)
        .agg(
            alunos=("id_aluno", "size"),
            municipios=("id_municipio", "nunique"),
            nao_alfabetizados=("risk", "sum"),
            soma_pesos=("peso_aluno", "sum"),
            soma_risco_ponderado=("weighted_risk", "sum"),
        )
        .reset_index()
    )
    grouped["taxa_nao_alfabetizado_pct"] = 100 * grouped["nao_alfabetizados"] / grouped["alunos"]
    grouped["taxa_nao_alfabetizado_ponderada_pct"] = (
        100 * grouped["soma_risco_ponderado"] / grouped["soma_pesos"]
    )
    return grouped.drop(columns="soma_risco_ponderado")


def numeric_summary(frame: pd.DataFrame, contract: ExperimentContract) -> pd.DataFrame:
    """Cada município contribui uma vez; exemplo: `numeric_summary(gold, contract)`."""
    contexts = frame.drop_duplicates("id_municipio")
    summary = contexts[list(contract.numeric)].describe(percentiles=[0.25, 0.5, 0.75]).T
    summary["ausentes"] = contexts[list(contract.numeric)].isna().sum()
    return summary.reset_index(names="atributo")


def eda_overview(frame: pd.DataFrame, contract: ExperimentContract) -> JsonObject:
    """Registra universo e unidade das estatísticas; exemplo: `eda_overview(df, contract)`."""
    require_development(frame)
    return {
        "year": 2023,
        "rows": len(frame),
        "municipalities": int(frame["id_municipio"].nunique()),
        "school_codes_within_year": int(frame["id_escola"].nunique()),
        "literate": int(frame["alfabetizado"].sum()),
        "non_literate": int((1 - frame["alfabetizado"]).sum()),
        "non_literate_pct": float(100 * (1 - frame["alfabetizado"]).mean()),
        "feature_missing": {name: int(frame[name].isna().sum()) for name in contract.features},
        "distinct_feature_profiles": len(frame[list(contract.features)].drop_duplicates()),
        "numeric_distribution_unit": "one row per municipality, not repeated per student",
        "test_2024_evaluated": False,
    }
