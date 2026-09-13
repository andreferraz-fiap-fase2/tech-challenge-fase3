"""Entradas públicas e critérios da demonstração contextual, sem dados de alunos."""

import math
import re
from dataclasses import dataclass

from src.domain.contract import ContractError, JsonObject


@dataclass(frozen=True)
class ProfileRequest:
    """Identifica um contexto municipal e uma rede presentes no desenvolvimento de 2023."""

    municipality: str
    network: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9]{7}", self.municipality):
            raise ContractError("Município inválido; informe o código IBGE com sete dígitos")
        if self.network not in {"Municipal", "Estadual"}:
            raise ContractError("Rede inválida; esperado Municipal ou Estadual")


def probability_decision(risk: float, threshold: float) -> JsonObject:
    """Distingue a probabilidade da decisão operacional que prioriza sensibilidade."""
    if not math.isfinite(risk) or not 0 <= risk <= 1:
        raise ContractError("Probabilidade inválida; esperado número finito entre zero e um")
    if not math.isfinite(threshold) or not 0 < threshold < 1:
        raise ContractError("Limiar inválido; esperado número finito entre zero e um")
    return {
        "p_alfabetizado": 1 - risk,
        "p_nao_alfabetizado": risk,
        "decisao_f2": {
            "limiar_risco": threshold,
            "sinalizado_para_atencao": risk >= threshold,
            "classificacao": "não alfabetizado" if risk >= threshold else "alfabetizado",
            "regra": "classificar como não alfabetizado quando P(não alfabetizado) >= limiar",
        },
        "referencia_0_5": {
            "limiar_risco": 0.5,
            "classificacao": "não alfabetizado" if risk >= 0.5 else "alfabetizado",
            "uso": "comparação didática; não substitui a política F2 congelada",
        },
    }
