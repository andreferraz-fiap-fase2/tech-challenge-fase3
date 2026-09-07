"""Validações de integridade anteriores à modelagem."""

import numpy as np
import pandas as pd

from src.domain.contract import ContractError

SOURCE_FIELDS = (
    "ano",
    "id_aluno",
    "id_escola",
    "id_municipio",
    "serie",
    "rede",
    "presente",
    "alfabetizado",
    "proficiencia",
    "peso_aluno",
)


def require_unique(frame: pd.DataFrame, keys: list[str], label: str) -> None:
    """Barra nulos/duplicatas de chave; exemplo: `require_unique(ctx, ['id_municipio'], 'IBGE')`."""
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ContractError(f"Chave inválida em {label}; esperado {keys} único e não nulo")


def normalize_original(original: pd.DataFrame) -> pd.DataFrame:
    """Normaliza somente representações conhecidas; exemplo: `normalize_original(raw)`."""
    normalized = original.rename(columns={"presenca": "presente"}).copy()
    for field in ("presente", "alfabetizado"):
        values = normalized[field].astype("string")
        unexpected = set(values.dropna()) - {"0", "1"}
        if unexpected:
            raise ContractError(f"{field}={unexpected}; esperado códigos 0/1 ou nulo")
        normalized[field] = values.map({"0": False, "1": True}).astype("boolean")
    return _ordered_source(normalized)


def _ordered_source(frame: pd.DataFrame) -> pd.DataFrame:
    selected = frame[list(SOURCE_FIELDS)].copy()
    for column in ("id_aluno", "id_escola", "id_municipio", "serie", "rede"):
        selected[column] = selected[column].astype("string")
    return selected.sort_values(["ano", "id_aluno"]).reset_index(drop=True)


def verify_original_matches_batch(original: pd.DataFrame, batch: pd.DataFrame) -> None:
    """Confere valores e chaves, não apenas volumes; exemplo: `verify_original_matches_batch(raw, batch)`."""
    require_unique(original, ["ano", "id_aluno"], "original")
    require_unique(batch, ["ano", "id_aluno"], "Silver batch")
    expected, actual = normalize_original(original), _ordered_source(batch)
    try:
        pd.testing.assert_frame_equal(expected, actual, check_dtype=False, check_exact=True)
    except AssertionError as exc:
        raise ContractError(
            "Silver batch divergente; esperado todos os campos idênticos à fonte"
        ) from exc


def validate_labels(frame: pd.DataFrame) -> None:
    """Confere alvo e peso sem transformá-los em features; exemplo: `validate_labels(eligible)`."""
    expected = frame["proficiencia"].ge(743)
    if not frame["alfabetizado"].isin([0, 1, False, True]).all():
        raise ContractError("Alvo inválido; esperado alfabetizado binário e não nulo")
    if not frame["alfabetizado"].eq(expected).all():
        raise ContractError("Alvo divergente; esperado equivalência com proficiência >= 743")
    weights = frame["peso_aluno"].to_numpy(dtype=float)
    if not (np.isfinite(weights) & (weights > 0)).all():
        raise ContractError("Peso inválido; esperado peso_aluno finito e positivo")


def join_context(left: pd.DataFrame, right: pd.DataFrame, key: str) -> pd.DataFrame:
    """Impede multiplicação e descarte silencioso; exemplo: `join_context(alunos, municipios, 'id_municipio')`."""
    require_unique(right, [key], "contexto")
    merged = left.merge(right, on=key, how="left", validate="many_to_one", indicator=True)
    missing = merged["_merge"].ne("both")
    if missing.any():
        keys = merged.loc[missing, key].drop_duplicates().head(5).tolist()
        raise ContractError(f"Contexto ausente em {key}={keys}; esperado cobertura completa")
    return merged.drop(columns="_merge")
