"""Figuras da busca e confirmação; populações apresentadas separadamente."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.evaluation.boosting_report import MODEL_NAMES
from src.visualization.plots import GOLD, MUTED, NAVY, ReportPlots


class BoostingPlots(ReportPlots):
    def comparison(self, table: pd.DataFrame) -> None:
        names = {
            key: value.replace(" · ", "\n")
            for key, value in MODEL_NAMES.items()
            if key in set(table["model"])
        }
        figure, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
        for axis, metric, label in zip(
            axes, ["average_precision_risk", "roc_auc_risk"], ["Average precision", "ROC-AUC"]
        ):
            means = table.groupby("model")[metric].mean().reindex(names)
            colors = [GOLD if key.startswith("boosting") else NAVY for key in names]
            bars = axis.bar(list(names.values()), means, color=colors)
            axis.bar_label(bars, labels=[f"{value:.4f}" for value in means], padding=5, fontsize=9)
            for index, model in enumerate(names):
                axis.scatter(
                    index + np.array([-0.07, 0, 0.07]),
                    table.loc[table["model"].eq(model), metric],
                    s=15,
                    color="black",
                    zorder=3,
                )
            axis.set(ylabel=label, ylim=(0, 0.85))
            axis.tick_params(axis="x", labelsize=8)
        figure.suptitle("2023 · confirmação na base completa, mesmos folds municipais")
        figure.text(
            0.08,
            -0.015,
            "Médias e pontos por fold; seleção prévia em amostra. CV não aninhada; não é teste temporal.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "07_comparacao_modelos_2023")

    def search(self, table: pd.DataFrame) -> None:
        figure, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)
        for axis, variant in zip(axes, ("rede_uf", "completa")):
            subset = table.loc[table["variant"].eq(variant)]
            summary = subset.groupby(["max_leaf_nodes", "max_iter"])["average_precision_risk"].agg(
                ["mean", "std"]
            )
            labels = [f"{leaves} / {iterations}" for leaves, iterations in summary.index]
            x = np.arange(len(labels))
            axis.errorbar(x, summary["mean"], yerr=summary["std"], fmt="o", color=NAVY, capsize=4)
            selected = subset.loc[subset["selected"]].iloc[0]
            winner = summary.index.get_loc((selected["max_leaf_nodes"], selected["max_iter"]))
            axis.scatter(
                winner, summary.iloc[winner]["mean"], marker="*", s=160, color=GOLD, zorder=4
            )
            axis.set(
                xticks=x,
                xticklabels=labels,
                xlabel="Folhas máximas / iterações",
                title="Rede / UF" if variant == "rede_uf" else "Seis atributos",
            )
            axis.tick_params(axis="x", labelsize=9)
        axes[0].set_ylabel("Average precision de risco")
        figure.suptitle("2023 · busca em amostra fixa de alunos, agrupada por município")
        figure.text(
            0.08,
            -0.015,
            "Média ± desvio entre folds; não é intervalo de confiança. Estrela: configuração selecionada.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "08_busca_boosting_2023")
