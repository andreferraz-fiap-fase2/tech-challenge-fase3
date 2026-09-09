"""Amostra sem consultar rótulos e independente da ordem das linhas."""

from hashlib import sha256

import pandas as pd

from src.domain.boosting import BoostingSettings
from src.domain.contract import ContractError
from src.evaluation.development import require_development


def development_sample(frame: pd.DataFrame, settings: BoostingSettings) -> pd.DataFrame:
    """Seleciona os menores hashes seed|ano|id_aluno em cada fold já congelado."""
    require_development(frame)
    keys = frame[["ano", "id_aluno"]]
    if keys.isna().any().any() or keys.duplicated().any() or not frame.index.is_unique:
        raise ContractError("Amostragem exige chaves e índice únicos, sem chave ausente")
    identity = (
        str(settings.random_state)
        + "|"
        + keys["ano"].astype(str)
        + "|"
        + keys["id_aluno"].astype(str)
    )
    ranked = frame.assign(_sample_hash=identity.map(lambda key: sha256(key.encode()).hexdigest()))
    sample = (
        ranked.sort_values(["fold_validacao", "_sample_hash", "id_aluno"])
        .groupby("fold_validacao", sort=True)
        .head(settings.sample_per_fold)
    )
    require_development(sample)
    return sample.drop(columns="_sample_hash")
