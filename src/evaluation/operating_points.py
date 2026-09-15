"""Pontos de operação por capacidade de atendimento, derivados da curva de 2023."""

import pandas as pd

from src.domain.contract import ContractError, JsonObject

FLAG_TARGETS = (0.05, 0.10, 0.20, 0.30)
CURVE_COLUMNS = ("threshold", "tp", "fp", "fn", "tn", "f2", "recall", "precision", "flag_rate")


def curve_prevalence(curve: pd.DataFrame) -> float:
    """Prevalência implícita na curva, idêntica em toda linha; exemplo: `curve_prevalence(c)`."""
    missing = [name for name in CURVE_COLUMNS if name not in curve.columns]
    if missing:
        raise ContractError(f"Curva sem {missing}; esperado {list(CURVE_COLUMNS)}")
    positives = curve["tp"] + curve["fn"]
    total = positives + curve["fp"] + curve["tn"]
    ratios = (positives / total).round(12).unique()
    if len(ratios) != 1:
        raise ContractError(f"Prevalências {ratios}; esperado uma única população na curva")
    return float(ratios[0])


def nearest_flag_rate(curve: pd.DataFrame, target: float) -> pd.Series:
    """Linha cuja taxa de sinalização mais se aproxima do alvo; exemplo: `nearest_flag_rate(c, .1)`."""
    if not 0 < target <= 1:
        raise ContractError(f"Alvo={target}; esperado fração entre 0 e 1")
    return curve.iloc[(curve["flag_rate"] - target).abs().argmin()]


def operating_points(curve: pd.DataFrame, chosen_threshold: float) -> pd.DataFrame:
    """Tabela por capacidade mais o limiar congelado; exemplo: `operating_points(c, 0.15)`."""
    prevalence = curve_prevalence(curve)
    rows = [_row(nearest_flag_rate(curve, target), target, prevalence) for target in FLAG_TARGETS]
    frozen = curve.iloc[(curve["threshold"] - chosen_threshold).abs().argmin()]
    rows.append(_row(frozen, None, prevalence))
    return pd.DataFrame(rows)


def _row(entry: pd.Series, target: float | None, prevalence: float) -> JsonObject:
    return {
        "criterio": "limiar F2 congelado" if target is None else f"sinalizar {target:.0%}",
        "threshold": float(entry["threshold"]),
        "flag_rate": float(entry["flag_rate"]),
        "recall": float(entry["recall"]),
        "precision": float(entry["precision"]),
        "lift_sobre_prevalencia": float(entry["precision"]) / prevalence,
        "f2": float(entry["f2"]),
    }


def trivial_f2(prevalence: float) -> float:
    """F2 da regra que sinaliza todos, com recall 1; exemplo: `trivial_f2(0.416142)`."""
    if not 0 < prevalence < 1:
        raise ContractError(f"Prevalência={prevalence}; esperado entre 0 e 1")
    return 5 * prevalence / (4 * prevalence + 1)
