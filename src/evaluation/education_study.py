"""Admissão, EDA e métricas pareadas da expansão educacional de 2023."""

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from src.domain.contract import ContractError, JsonObject
from src.domain.education_study import EDUCATION_FEATURES, METRICS
from src.evaluation.development import require_development
from src.preprocessing.validation import require_unique

KEYS = ["id_municipio", "rede_nome"]


def require_study_development(frame: pd.DataFrame, folds: pd.DataFrame | None = None) -> None:
    """Confere ano, população individual e mapa municipal, sem olhar resultados futuros."""
    require_development(frame)
    require_unique(frame, ["ano", "id_aluno"], "Gold de desenvolvimento")
    if set(frame["particao"]) != {"desenvolvimento"} or not frame.index.is_unique:
        raise ContractError(
            "Partição ou índice inválido; esperado desenvolvimento com índice único"
        )
    if frame["alfabetizado"].isna().any() or set(frame["alfabetizado"]) != {0, 1}:
        raise ContractError("Alvo inválido; esperado duas classes completas em 2023")
    if folds is not None:
        require_unique(folds, ["id_municipio"], "mapa de folds")
        expected = frame["id_municipio"].map(folds.set_index("id_municipio")["fold"])
        if expected.isna().any() or not expected.eq(frame["fold_validacao"]).all():
            raise ContractError("Folds divergentes do mapa municipal original")


def join_education(
    frame: pd.DataFrame, context: pd.DataFrame, minimum_coverage: float = 0.95
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Left join preserva todas as linhas; cobertura é avaliada antes de qualquer ajuste."""
    require_study_development(frame)
    if set(context.columns) != set(KEYS + list(EDUCATION_FEATURES)):
        raise ContractError(
            "Colunas contextuais divergentes; esperado somente chaves e três atributos"
        )
    if any(name in frame.columns for name in EDUCATION_FEATURES):
        raise ContractError("Gold já contém expansão; esperado somente o contexto original")
    require_unique(context, KEYS, "contexto educacional")
    numeric = context[list(EDUCATION_FEATURES)].to_numpy(dtype=float)
    if np.isinf(numeric).any():
        raise ContractError("Contexto infinito; esperado número finito ou ausência")
    merged = frame.merge(context, how="left", on=KEYS, validate="many_to_one", sort=False)
    try:
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), merged[frame.columns])
    except AssertionError as exc:
        raise ContractError("Junção alterou população, ordem, alvo ou folds") from exc
    merged.index = frame.index
    contexts = merged.drop_duplicates(KEYS)
    coverage = pd.DataFrame(
        [
            {
                "attribute": name,
                "student_rows": len(merged),
                "student_nonmissing": int(merged[name].notna().sum()),
                "student_coverage": float(merged[name].notna().mean()),
                "context_rows": len(contexts),
                "context_nonmissing": int(contexts[name].notna().sum()),
                "context_coverage": float(contexts[name].notna().mean()),
            }
            for name in EDUCATION_FEATURES
        ]
    )
    if coverage["student_coverage"].lt(minimum_coverage).any():
        raise ContractError("Cobertura estudantil abaixo de 95%; comparação não admitida")
    return merged, coverage


def education_eda(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cada contexto participa uma vez nas distribuições e correlações não ponderadas."""
    require_study_development(frame)
    context = frame.drop_duplicates(KEYS)[KEYS + list(EDUCATION_FEATURES)]
    distribution = context[list(EDUCATION_FEATURES)].describe().T
    distribution["missing"] = context[list(EDUCATION_FEATURES)].isna().sum()
    rates = frame.groupby(KEYS, observed=True)["alfabetizado"].mean().rename("literacy_rate")
    context = context.merge(rates.reset_index(), on=KEYS, validate="one_to_one")
    correlations = []
    for name in EDUCATION_FEATURES:
        paired = context[[name, "literacy_rate"]].dropna()
        coefficient = paired[name].corr(paired["literacy_rate"])
        correlations.append(
            {"attribute": name, "complete_contexts": len(paired), "pearson_literacy": coefficient}
        )
    return distribution.reset_index(names="attribute"), pd.DataFrame(correlations)


def probability_scores(literacy: pd.Series, risk: np.ndarray) -> JsonObject:
    """Avalia somente as três métricas fixadas; nenhuma decisão por limiar é escolhida."""
    if set(literacy) != {0, 1} or len(literacy) != len(risk):
        raise ContractError("Alvo ou previsões inválidos para as métricas probabilísticas")
    if not np.isfinite(risk).all() or ((risk < 0) | (risk > 1)).any():
        raise ContractError("Probabilidade inválida; esperado intervalo [0,1]")
    target = 1 - literacy.to_numpy(dtype=np.int8)
    return {
        "average_precision_risk": float(average_precision_score(target, risk)),
        "roc_auc_risk": float(roc_auc_score(target, risk)),
        "brier_risk": float(brier_score_loss(target, risk)),
    }


def paired_results(scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Resume folds e diferenças pareadas; desvio entre folds não é intervalo de confiança."""
    summary = scores.groupby("variant")[list(METRICS)].agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    summary = summary.reset_index()
    base = scores.loc[scores["variant"].eq("ibge")].set_index("fold")
    expanded = scores.loc[scores["variant"].eq("ibge_inep")].set_index("fold")
    delta = expanded[list(METRICS)] - base[list(METRICS)]
    delta.columns = [f"delta_{name}" for name in METRICS]
    return summary, delta.reset_index()
