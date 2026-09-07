"""Materializa o grão individual e separa preditores de alvo, peso e auditoria."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.domain.contract import ContractError, ExperimentContract, JsonObject
from src.preprocessing.validation import (
    join_context,
    require_unique,
    validate_labels,
    verify_original_matches_batch,
)

METADATA = (
    "ano",
    "id_aluno",
    "id_escola",
    "id_municipio",
    "nome_municipio",
    "nome_uf",
    "regiao",
    "peso_aluno",
    "alfabetizado",
    "particao",
    "fold_validacao",
)


@dataclass
class GoldResult:
    frame: pd.DataFrame
    audit: JsonObject


def eligible_batch(silver: pd.DataFrame) -> tuple[pd.DataFrame, JsonObject]:
    """Aplica filtros com contagens sucessivas; exemplo: `eligible_batch(silver)`."""
    unknown_origins = set(silver["origem"].dropna()) - {"batch", "streaming"}
    if unknown_origins or silver["origem"].isna().any():
        raise ContractError(f"Origem={unknown_origins}; esperado batch/streaming sem nulos")
    current = silver.loc[silver["origem"].eq("batch")].copy()
    audit: JsonObject = {
        "silver_rows": len(silver),
        "simulated_removed": len(silver) - len(current),
    }
    audit["batch_rows"] = len(current)
    filters = _eligibility_filters(current)
    for label, mask in filters.items():
        current = current.loc[mask.reindex(current.index).fillna(False)].copy()
        audit[label] = len(current)
    validate_labels(current)
    return current, audit


def _eligibility_filters(frame: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "after_network_series": frame["rede_nome"].isin(["Estadual", "Municipal"])
        & frame["serie"].astype("string").eq("2"),
        "after_presence": frame["presente"].eq(True),
        "after_finite_score": pd.Series(
            np.isfinite(frame["proficiencia"].to_numpy(dtype=float)), index=frame.index
        ),
        "eligible_rows": frame["alfabetizado"].notna(),
    }


def assign_partition(frame: pd.DataFrame, folds: pd.DataFrame, year: int) -> pd.DataFrame:
    """Usa exclusivamente o mapa congelado de 2023; exemplo: `assign_partition(gold, folds, 2023)`."""
    assigned = frame.copy()
    assigned["particao"] = "desenvolvimento" if year == 2023 else "teste_reservado"
    assigned["fold_validacao"] = pd.Series(pd.NA, index=assigned.index, dtype="Int8")
    if year != 2023:
        return assigned
    require_unique(folds, ["id_municipio"], "folds")
    mapping = folds.set_index("id_municipio")["fold"]
    assigned["fold_validacao"] = assigned["id_municipio"].map(mapping).astype("Int8")
    if not assigned["fold_validacao"].isin([0, 1, 2]).all():
        raise ContractError("Fold inválido; esperado cada município de 2023 em um de 0/1/2")
    return assigned


def build_gold(
    original: pd.DataFrame,
    silver: pd.DataFrame,
    context: pd.DataFrame,
    municipalities: pd.DataFrame,
    states: pd.DataFrame,
    folds: pd.DataFrame,
    year: int,
    contract: ExperimentContract,
) -> GoldResult:
    """Constrói uma partição a partir de entradas já lidas e verificadas."""
    if set(silver["ano"]) != {year} or year not in (2023, 2024):
        raise ContractError(
            f"Anos na Silver={set(silver['ano'])}, partição={year}; esperado único 2023/2024"
        )
    batch = silver.loc[silver["origem"].eq("batch")]
    verify_original_matches_batch(original.loc[original["ano"].eq(year)], batch)
    eligible, audit = eligible_batch(silver)
    enriched = join_context(eligible, municipalities, "id_municipio")
    enriched = join_context(enriched, states, "sigla_uf")
    enriched = join_context(enriched, context, "id_municipio")
    _validate_enrichment(enriched, contract)
    assigned = assign_partition(enriched, folds, year)
    output = _gold_columns(assigned, contract)
    audit.update(
        {
            "year": year,
            "gold_rows": len(output),
            "municipalities": int(output["id_municipio"].nunique()),
            "features": list(contract.features),
        }
    )
    return GoldResult(output, audit)


def _validate_enrichment(frame: pd.DataFrame, contract: ExperimentContract) -> None:
    if not frame["sigla_uf"].eq(frame["sigla_uf_ibge"]).all():
        raise ContractError(
            "UF divergente entre IBGE e diretório; esperado correspondência por município"
        )
    numeric = frame[list(contract.numeric)].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ContractError(
            "Contexto contém nulo/infinito; esperado seis atributos completos no snapshot"
        )
    if (frame[["populacao_2021", "pib_per_capita_2020"]] <= 0).any().any():
        raise ContractError("População/PIB per capita inválidos; esperado valores positivos")
    shares = frame[list(contract.numeric[2:])]
    if ((shares < 0) | (shares > 100)).any().any():
        raise ContractError("Participação econômica inválida; esperado percentual de 0 a 100")


def _gold_columns(frame: pd.DataFrame, contract: ExperimentContract) -> pd.DataFrame:
    output = frame[list(METADATA + contract.features)].copy()
    output["alfabetizado"] = output["alfabetizado"].astype("int8")
    require_unique(output, ["ano", "id_aluno"], "Gold")
    return output.sort_values(["id_municipio", "id_aluno"]).reset_index(drop=True)


def select_predictors(frame: pd.DataFrame, contract: ExperimentContract) -> pd.DataFrame:
    """Seleciona uma allowlist explícita; exemplo: `select_predictors(gold, contract)`."""
    if contract.features != ExperimentContract().features:
        raise ContractError(
            f"Lista de preditores alterada: {contract.features}; esperado contrato v0.1"
        )
    return frame.loc[:, list(contract.features)].copy()
