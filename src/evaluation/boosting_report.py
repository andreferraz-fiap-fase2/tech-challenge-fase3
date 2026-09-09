"""Relatório comparável de desenvolvimento, explicitando a seleção de parâmetros."""

from typing import cast

import pandas as pd

from src.domain.contract import JsonObject

MODEL_NAMES = {
    "dummy_prior": "Baseline",
    "rede_uf": "Logística · rede/UF",
    "completa": "Logística · seis atributos",
    "boosting_rede_uf": "Boosting · rede/UF",
    "boosting_completa": "Boosting · seis atributos",
}


def boosting_markdown(table: pd.DataFrame, report: JsonObject) -> str:
    rows = [
        "| Modelo | AP média ± DP | ROC-AUC | Brier | Recall em 0,5 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for model, group in table.groupby("model", sort=False):
        ap = group["average_precision_risk"]
        rows.append(
            f"| {MODEL_NAMES[str(model)]} | {ap.mean():.4f} ± {ap.std():.4f} | "
            f"{group['roc_auc_risk'].mean():.4f} | {group['brier_risk'].mean():.4f} | "
            f"{group['recall_risk'].mean():.2%} |"
        )
    selected = [
        f"- {model['variant']}: `{cast(JsonObject, model['candidate'])['name']}`."
        for model in cast(list[JsonObject], report["models"])
    ]
    return "\n".join(
        [
            "# Gradient Boosting e busca limitada · desenvolvimento de 2023",
            "",
            "Busca em amostra fixa, sem rótulos na seleção de alunos. Vencedor por AP de risco média, "
            "separado por variante. Confirmação na Gold completa, nos mesmos três folds municipais.",
            "",
            *rows,
            "",
            "DP = desvio entre folds, não intervalo de confiança. AP não é acurácia nem "
            "precisão no limiar 0,5. Classe de interesse: não alfabetizado.",
            "",
            "## Configurações selecionadas",
            "",
            *selected,
            "",
            f"Amostra: {cast(JsonObject, report['sample'])['rows']:,} avaliações, "
            f"{cast(JsonObject, report['sample'])['municipalities']:,} municípios. "
            "Seis candidatos por variante; parâmetros completos no protocolo e JSON.",
            "",
            "## Limites e próximos passos",
            "",
            "A busca reutiliza uma amostra dos folds da confirmação: CV não aninhada, "
            "sujeita a otimismo por seleção. Nenhum resultado desta tabela é de teste temporal. "
            "A Gold de 2024 não foi avaliada. Não há modelo final nem limiar operacional escolhido.",
            "",
            "Atributos territoriais produzem risco contextual, sem demonstrar causas individuais. "
            "O ganho da variante completa deve ser comparado à variante rede/UF do mesmo algoritmo. "
            "Pesos não entram no ajuste; métricas ponderadas suplementares estão no JSON.",
            "",
            "Próxima etapa: consolidar escolha com 2023, interpretar previsões e definir/congelar "
            "o limiar antes de uma avaliação temporal única em 2024.",
            "",
            "[Protocolo](boosting_protocolo.md) · [Busca por fold](boosting_busca_2023.csv) · "
            "[Confirmação por fold](modelos_comparacao_2023.csv)",
            "",
            "![Comparação dos modelos](../images/07_comparacao_modelos_2023.png)",
            "",
            "![Busca em amostra](../images/08_busca_boosting_2023.png)",
            "",
        ]
    )
