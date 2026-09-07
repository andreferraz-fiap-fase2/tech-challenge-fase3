"""Figuras exportáveis da EDA, com unidades e populações explícitas."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

NAVY, GOLD, MUTED = "#183650", "#B78C31", "#596573"


class ReportPlots:
    """Adaptador de exportação de figuras; exemplo: `ReportPlots(path).target(development)`."""

    def __init__(self, destination: Path) -> None:
        self.destination = destination
        destination.mkdir(parents=True, exist_ok=True)
        plt.rcParams.update(
            {
                "font.family": "DejaVu Sans",
                "font.size": 11,
                "axes.spines.top": False,
                "axes.spines.right": False,
                "svg.hashsalt": "fiap-fase3",
            }
        )

    def save(self, figure: Figure, name: str) -> None:
        figure.tight_layout()
        figure.savefig(self.destination / f"{name}.png", dpi=160, bbox_inches="tight")
        figure.savefig(
            self.destination / f"{name}.svg", bbox_inches="tight", metadata={"Date": None}
        )
        plt.close(figure)

    def target(self, frame: pd.DataFrame) -> None:
        counts = [int(frame["alfabetizado"].sum()), int((1 - frame["alfabetizado"]).sum())]
        figure, axis = plt.subplots(figsize=(8, 4.5))
        bars = axis.bar(
            ["Alfabetizado", "Não alfabetizado"],
            np.array(counts) / len(frame) * 100,
            color=[NAVY, GOLD],
        )
        axis.bar_label(
            bars, labels=[f"{n:,} avaliações\n{n / len(frame):.1%}" for n in counts], padding=5
        )
        axis.set(
            ylim=(0, 75),
            ylabel="% de avaliações elegíveis",
            title="2023 · distribuição do alvo no desenvolvimento",
        )
        figure.text(
            0.1,
            -0.03,
            "Avaliações reais; redes Estadual/Municipal; sem ponderação amostral.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "01_alvo_2023")

    def regions(self, summary: pd.DataFrame) -> None:
        ordered = summary.sort_values("taxa_nao_alfabetizado_pct")
        figure, axis = plt.subplots(figsize=(9, 4.5))
        bars = axis.barh(ordered["regiao"], ordered["taxa_nao_alfabetizado_pct"], color=NAVY)
        axis.bar_label(
            bars,
            labels=[
                f"{rate:.1f}%  (n={n:,})"
                for rate, n in zip(ordered["taxa_nao_alfabetizado_pct"], ordered["alunos"])
            ],
            padding=5,
        )
        axis.set(
            xlim=(0, max(ordered["taxa_nao_alfabetizado_pct"]) * 1.4),
            xlabel="% não alfabetizado, sem ponderação",
            title="2023 · diferenças regionais entre avaliações elegíveis",
        )
        figure.text(
            0.1,
            -0.03,
            "Taxas do recorte disponível; não são estimativas oficiais nacionais nem efeitos causais.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "02_regioes_2023")

    def numeric(self, frame: pd.DataFrame) -> None:
        contexts = frame.drop_duplicates("id_municipio")
        columns = [
            "populacao_2021",
            "pib_per_capita_2020",
            "participacao_agropecuaria_2020",
            "participacao_servicos_publicos_2020",
        ]
        labels = [
            "População 2021 · log10(habitantes)",
            "PIB per capita 2020 · log10(R$)",
            "Agropecuária no VAB 2020 (%)",
            "Serviços públicos no VAB 2020 (%)",
        ]
        figure, axes = plt.subplots(2, 2, figsize=(11, 7))
        for index, (column, label, axis) in enumerate(zip(columns, labels, axes.flat)):
            values = np.log10(contexts[column]) if index < 2 else contexts[column]
            axis.hist(values, bins=35, color=NAVY if index < 2 else GOLD, edgecolor="white")
            axis.set(xlabel=label, ylabel="Municípios")
        figure.suptitle(
            f"Contexto histórico · {len(contexts):,} municípios no desenvolvimento de 2023", y=1.02
        )
        figure.text(
            0.08,
            -0.02,
            "Uma observação por município; log10 usado apenas na visualização. Pipeline usará log1p.",
            fontsize=9,
            color=MUTED,
        )
        self.save(figure, "03_contexto_municipal_2023")

    def folds(self, summary: pd.DataFrame) -> None:
        figure, axis = plt.subplots(figsize=(8, 4.5))
        bars = axis.bar(
            summary["fold_validacao"].astype(str), summary["taxa_nao_alfabetizado_pct"], color=NAVY
        )
        axis.bar_label(
            bars,
            labels=[
                f"{rate:.1f}%\nn={n:,}"
                for rate, n in zip(summary["taxa_nao_alfabetizado_pct"], summary["alunos"])
            ],
            padding=5,
        )
        axis.set(
            ylim=(0, 65),
            xlabel="Fold de validação (municípios exclusivos)",
            ylabel="% não alfabetizado",
            title="2023 · composição das divisões de validação",
        )
        self.save(figure, "04_folds_2023")
