"""Figuras finais do experimento e da leitura territorial."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

from src.visualization.plots import GOLD, MUTED, NAVY, ReportPlots

NAMES = {
    "sigla_uf": "UF",
    "rede_nome": "Rede de ensino",
    "populacao_2021": "População 2021",
    "pib_per_capita_2020": "PIB per capita 2020",
    "participacao_agropecuaria_2020": "Agropecuária / VAB",
    "participacao_servicos_publicos_2020": "Serviços públicos / VAB",
}


class FinalPlots(ReportPlots):
    """Gera PNG e SVG editável; exemplo: `FinalPlots(path).importance(table)`."""

    def threshold(self, table: pd.DataFrame, selected: float) -> None:
        figure, axis = plt.subplots(figsize=(9, 4.8))
        for name, label, color in (
            ("f2", "F2", NAVY),
            ("recall", "Recall", GOLD),
            ("flag_rate", "Alunos sinalizados", MUTED),
        ):
            axis.plot(table.threshold, table[name], label=label, color=color)
        axis.axvline(
            selected, color="black", linestyle="--", label=f"Limiar congelado: {selected:.4f}"
        )
        axis.set(
            xlabel="Limiar de risco",
            ylabel="Proporção / F2",
            xlim=(0, 1),
            ylim=(0, 1.03),
            title="2023 · F2 elevado exige sinalizar quase toda a população",
        )
        axis.legend(loc="upper right", fontsize=9)
        self.save(figure, "09_limiar_f2_2023")

    def importance(self, table: pd.DataFrame) -> None:
        ordered = table.sort_values("mean")
        figure, axis = plt.subplots(figsize=(9, 4.8))
        axis.barh(
            ordered.feature.map(NAMES), ordered["mean"], xerr=ordered["std"], color=NAVY, capsize=3
        )
        axis.axvline(0, color=MUTED, linewidth=1)
        axis.set(
            xlabel="Queda de average precision após permutação",
            title="2023 · UF concentra a dependência preditiva do modelo",
        )
        figure.text(
            0.08,
            -0.015,
            "Média ± desvio: 3 folds × 5 permutações; não é intervalo de confiança nem efeito causal.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "10_importancia_permutacao_2023")

    def temporal_curves(
        self, target: np.ndarray, risk: np.ndarray, calibration: pd.DataFrame
    ) -> None:
        figure, axes = plt.subplots(1, 3, figsize=(13, 4))
        fpr, tpr, _ = roc_curve(target, risk)
        precision, recall, _ = precision_recall_curve(target, risk)
        axes[0].plot(fpr, tpr, color=NAVY)
        axes[0].plot([0, 1], [0, 1], linestyle="--", color=MUTED)
        axes[0].set(xlabel="Falsos positivos", ylabel="Recall", title="ROC · 2024")
        axes[1].plot(recall, precision, color=NAVY)
        axes[1].axhline(target.mean(), linestyle="--", color=MUTED)
        axes[1].set(xlabel="Recall", ylabel="Precisão", title="Precisão-recall · 2024")
        axes[2].plot(calibration.mean_risk, calibration.observed_risk, "o-", color=GOLD)
        axes[2].plot([0, 1], [0, 1], linestyle="--", color=MUTED)
        axes[2].set(
            xlabel="Risco previsto médio", ylabel="Frequência observada", title="Calibração · 2024"
        )
        for axis in axes:
            axis.set(xlim=(0, 1), ylim=(0, 1))
        figure.text(
            0.07,
            -0.02,
            "Teste temporal reservado. Calibração apenas inspecionada; modelo e probabilidades não reajustados.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "11_curvas_teste_2024")

    def regions(self, table: pd.DataFrame) -> None:
        figure, axis = plt.subplots(figsize=(9, 4.7))
        x = np.arange(len(table))
        axis.bar(x - 0.18, 100 * table.risco_medio, width=0.36, color=NAVY, label="Risco previsto")
        axis.bar(
            x + 0.18,
            100 * table.risco_observado,
            width=0.36,
            color=GOLD,
            label="Não alfabetização observada",
        )
        axis.set(
            xticks=x,
            xticklabels=table.regiao,
            ylim=(0, 65),
            ylabel="% das avaliações elegíveis",
            title="2024 · erros diferentes entre regiões",
        )
        axis.legend(fontsize=9)
        self.save(figure, "12_regioes_teste_2024")

    def municipalities(self, table: pd.DataFrame) -> None:
        top = table.head(10).iloc[::-1]
        figure, axis = plt.subplots(figsize=(10, 5))
        labels = top.nome_municipio + " / " + top.sigla_uf
        axis.barh(labels, 100 * top.risco_medio, color=NAVY)
        axis.scatter(
            100 * top.risco_observado, labels, color=GOLD, label="Observado no recorte", zorder=3
        )
        axis.set(
            xlim=(0, 85),
            xlabel="Risco médio de não alfabetização (%)",
            title="2024 · maiores riscos previstos entre municípios com n ≥ 100",
        )
        axis.legend(loc="lower right", fontsize=9)
        figure.text(
            0.1,
            -0.015,
            "Ranking do modelo contextual; concentração em Sergipe reflete dependência de UF. Não é ranking oficial.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "13_municipios_risco_2024")

    def profiles(self, table: pd.DataFrame) -> None:
        table = table.set_index("regiao")
        figure, axis = plt.subplots(figsize=(9, 4.5))
        plot = axis.imshow(table.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        axis.set(
            xticks=range(4),
            xticklabels=[
                "População\nlog1p",
                "PIB per capita\nlog1p",
                "Agropecuária\nVAB",
                "Serviços públicos\nVAB",
            ],
            yticks=range(len(table)),
            yticklabels=table.index,
            title="2023 · perfis médios de contexto regional",
        )
        for i in range(len(table)):
            for j in range(4):
                axis.text(j, i, f"{table.iloc[i, j]:.2f}", ha="center", va="center", fontsize=10)
        figure.colorbar(plot, ax=axis, label="Desvios-padrão; igual peso por município")
        self.save(figure, "14_perfis_regionais_2023")
