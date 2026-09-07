"""Comparação pareada e leitura dos coeficientes numéricos, sem inferência causal."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.visualization.plots import GOLD, MUTED, NAVY, ReportPlots

MODEL_NAMES = {
    "dummy_prior": "Baseline",
    "rede_uf": "Logística\nrede / UF",
    "completa": "Logística\nseis atributos",
}


class LogisticPlots(ReportPlots):
    """Exporta figuras da rodada logística; exemplo: `LogisticPlots(path).comparison(table)`."""

    def comparison(self, table: pd.DataFrame) -> None:
        figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
        for axis, metric, label in zip(
            axes, ("average_precision_risk", "roc_auc_risk"), ("Average precision", "ROC-AUC")
        ):
            groups = table.groupby("model")[metric].agg(["mean", "std"]).reindex(MODEL_NAMES)
            bars = axis.bar(list(MODEL_NAMES.values()), groups["mean"], color=[MUTED, NAVY, GOLD])
            axis.bar_label(bars, labels=[f"{v:.4f}" for v in groups["mean"]], padding=5)
            for index, model in enumerate(MODEL_NAMES):
                axis.scatter(
                    index + np.array([-0.07, 0, 0.07]),
                    table.loc[table["model"].eq(model), metric],
                    color="black",
                    s=17,
                    zorder=3,
                )
            axis.set(ylabel=label, ylim=(0, 0.85))
        figure.suptitle("2023 · ganho sobre o baseline nos mesmos municípios de validação")
        figure.text(
            0.1,
            -0.02,
            "Barras: média dos 3 folds. Pontos: cada fold. Classe de interesse: não alfabetizado.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "05_comparacao_logistica_2023")

    def numeric_coefficients(self, coefficients: pd.DataFrame) -> None:
        names = {
            "log__populacao_2021": "População 2021 · log1p",
            "log__pib_per_capita_2020": "PIB per capita 2020 · log1p",
            "shares__participacao_agropecuaria_2020": "Agropecuária no VAB 2020",
            "shares__participacao_servicos_publicos_2020": "Serviços públicos no VAB 2020",
        }
        selected = coefficients.loc[
            coefficients["variant"].eq("completa") & coefficients["term"].isin(names)
        ]
        summary = selected.groupby("term")["coefficient_risk"].agg(["mean", "std"]).reindex(names)
        figure, axis = plt.subplots(figsize=(9, 4))
        axis.errorbar(
            summary["mean"],
            list(names.values()),
            xerr=summary["std"],
            fmt="o",
            color=NAVY,
            capsize=5,
        )
        axis.axvline(0, color=MUTED, linewidth=1)
        axis.set(
            xlabel="Log-odds de não alfabetização\npor +1 desvio-padrão do atributo transformado",
            title="Logística com seis atributos · associações condicionais em 2023",
        )
        figure.text(
            0.1,
            -0.035,
            "Média ± desvio entre folds; não é intervalo de confiança. Coeficientes não demonstram causalidade.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "06_coeficientes_numericos_2023")
