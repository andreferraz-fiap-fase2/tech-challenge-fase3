"""Comparação pareada entre o modelo congelado e sua versão sem UF."""

from typing import cast

import pandas as pd

from src.domain.contract import ContractError, JsonObject
from src.domain.uf_ablation import METRICS, PUBLISHED_REFERENCE, VARIANTS

VARIANT_NAMES = {
    "completa": "Seis atributos (modelo congelado)",
    "sem_uf": "Cinco atributos, sem UF",
}
TOLERANCE = 1e-12


def ablation_table(reports: list[JsonObject]) -> pd.DataFrame:
    """Uma linha por variante e fold; exemplo: `ablation_table(reports)`."""
    rows: list[JsonObject] = []
    for report in reports:
        for fold in cast(list[JsonObject], report["folds"]):
            rows.append(
                {
                    "variant": report["variant"],
                    "fold": fold["fold"],
                    **cast(JsonObject, fold["unweighted"]),
                }
            )
    return pd.DataFrame(rows).drop(columns="confusion_tn_fp_fn_tp")


def ablation_deltas(table: pd.DataFrame) -> pd.DataFrame:
    """Diferença nos mesmos folds e alunos; exemplo: `ablation_deltas(table)`."""
    indexed = table.set_index(["variant", "fold"])
    difference = indexed.loc["sem_uf", list(METRICS)] - indexed.loc["completa", list(METRICS)]
    return difference.rename(columns={m: f"delta_{m}" for m in METRICS}).reset_index()


def verify_reference(table: pd.DataFrame, published: pd.DataFrame) -> JsonObject:
    """Confere que a referência reproduz o resultado já publicado, fold a fold."""
    recomputed = table.loc[table["variant"].eq("completa")].set_index("fold")
    original = published.loc[published["model"].eq(PUBLISHED_REFERENCE)].set_index("fold")
    if set(recomputed.index) != set(original.index):
        raise ContractError(f"Folds={set(recomputed.index)}; esperado {set(original.index)}")
    gaps = {
        metric: float((recomputed[metric] - original[metric]).abs().max()) for metric in METRICS
    }
    if max(gaps.values()) > TOLERANCE:
        raise ContractError(f"Referência divergente em {gaps}; esperado abaixo de {TOLERANCE}")
    return {"reference_max_absolute_gap": gaps, "reference_reproduced": True}


def ablation_markdown(table: pd.DataFrame, deltas: pd.DataFrame, report: JsonObject) -> str:
    """Relatório legível com a leitura e os limites; exemplo: `ablation_markdown(t, d, r)`."""
    summary = table.groupby("variant")[list(METRICS)].mean().reindex(VARIANTS)
    rows = [
        "| Variante | AP média | ROC-AUC média | Brier médio ↓ |",
        "| --- | ---: | ---: | ---: |",
    ]
    for variant, values in summary.iterrows():
        rows.append(
            f"| {VARIANT_NAMES[str(variant)]} | {values[METRICS[0]]:.6f} | "
            f"{values[METRICS[1]]:.6f} | {values[METRICS[2]]:.6f} |"
        )
    loss = summary.loc["completa", METRICS[0]] - summary.loc["sem_uf", METRICS[0]]
    share = 100 * loss / (summary.loc["completa", METRICS[0]] - float(report["baseline_ap"]))
    by_fold = " · ".join(
        f"fold {int(row['fold'])}: {row[f'delta_{METRICS[0]}']:+.6f}"
        for _, row in deltas.iterrows()
    )
    return "\n".join(
        [
            "# Ablação da UF · desenvolvimento de 2023",
            "",
            "Responde a lacuna registrada na seção 6.2 do README: quanto da ordenação do risco "
            "depende da sigla da unidade federativa. As duas variantes usam os mesmos três folds "
            "municipais, os mesmos 1.502.809 alunos e hiperparâmetros idênticos aos do modelo "
            "congelado 1.0. A única diferença é a remoção de `sigla_uf` dos preditores.",
            "",
            *rows,
            "",
            f"Remover a UF custa **{loss:.6f} de AP média**, o equivalente a "
            f"**{share:.1f}% da vantagem** que o modelo congelado tem sobre o baseline de "
            f"prevalência ({float(report['baseline_ap']):.6f}). Por fold: {by_fold}.",
            "",
            "## Como ler",
            "",
            "A variante sem UF preserva rede de ensino e os quatro atributos do IBGE. "
            "O que ela perde é a capacidade de distinguir estados. A comparação é descritiva: "
            "não há teste de significância, intervalo de confiança nem novo recorte independente.",
            "",
            "A referência de seis atributos foi reajustada nesta rodada e reproduziu exatamente "
            "as métricas publicadas em `modelos_comparacao_2023.csv`, fold a fold. Isso confirma "
            "que a diferença observada vem da remoção do atributo e não do procedimento.",
            "",
            "## Limites",
            "",
            "O teste temporal de 2024 já havia sido observado quando esta ablação foi executada "
            "e não foi carregado. O modelo final, o limiar congelado e a avaliação temporal 1.0 "
            "permanecem os mesmos; esta análise é interpretativa e não promove nova candidata. "
            "Dependência preditiva não é efeito causal: a UF resume diferenças de rede, política "
            "e composição que o recorte não separa.",
            "",
            "[Protocolo](../config/experimento-ablacao-uf.json) · "
            "[Métricas por fold](ablacao_uf_2023.csv) · "
            "[Diferenças por fold](ablacao_uf_deltas_2023.csv)",
            "",
            "![Ablação da UF](../images/18_ablacao_uf_2023.png)",
            "",
        ]
    )
