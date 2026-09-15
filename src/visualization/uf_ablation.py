"""Figura da ablação territorial, com pontos por fold visíveis."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.domain.uf_ablation import METRICS, VARIANTS
from src.evaluation.uf_ablation import VARIANT_NAMES
from src.visualization.plots import GOLD, MUTED, NAVY, ReportPlots


class AblationPlots(ReportPlots):
    """Exporta a comparação com e sem UF; exemplo: `AblationPlots(path).comparison(table, 0.41)`."""

    def comparison(self, table: pd.DataFrame, baseline_ap: float) -> None:
        labels = [
            VARIANT_NAMES[variant].replace(" (", "\n(").replace(", ", ",\n") for variant in VARIANTS
        ]
        figure, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
        for axis, metric, title in zip(
            axes, METRICS[:2], ["Average precision de risco", "ROC-AUC"]
        ):
            means = table.groupby("variant")[metric].mean().reindex(VARIANTS)
            bars = axis.bar(labels, means, color=[NAVY, GOLD])
            axis.bar_label(bars, labels=[f"{value:.6f}" for value in means], padding=5, fontsize=9)
            for index, variant in enumerate(VARIANTS):
                axis.scatter(
                    index + np.array([-0.07, 0.0, 0.07]),
                    table.loc[table["variant"].eq(variant), metric],
                    s=15,
                    color="black",
                    zorder=3,
                )
            axis.set(ylabel=title, ylim=(0, 0.85))
            axis.tick_params(axis="x", labelsize=8)
        references = [
            (axes[0], baseline_ap, f"Tracejado: baseline de prevalência, {baseline_ap:.6f}"),
            (axes[1], 0.5, "Tracejado: 0,5, ordenação ao acaso"),
        ]
        for axis, height, caption in references:
            axis.axhline(height, color=MUTED, linestyle="--", linewidth=1)
            axis.text(0.02, 0.96, caption, transform=axis.transAxes, fontsize=9, color=MUTED)
        figure.suptitle("2023 · quanto da ordenação do risco depende da UF")
        figure.text(
            0.08,
            -0.015,
            "Médias e pontos por fold, mesmos municípios e hiperparâmetros. "
            "Comparação descritiva; não é teste temporal nem de significância.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "18_ablacao_uf_2023")
