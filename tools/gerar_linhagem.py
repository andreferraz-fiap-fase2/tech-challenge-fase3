"""Autor: André Mohallem Ferraz. Diagrama exportável da origem das bases analíticas."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
NAVY, GOLD, GRAY = "#183650", "#B78C31", "#596573"


def box(axis: Axes, x: float, y: float, text: str, width: float = 3.8) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            1.05,
            boxstyle="round,pad=0.12",
            facecolor="#F1F4F6",
            edgecolor=NAVY,
            linewidth=1.1,
        )
    )
    axis.text(x + width / 2, y + 0.53, text, ha="center", va="center", fontsize=10, color=NAVY)


def arrow(axis: Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    axis.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13, color=GOLD))


def main() -> None:
    figure, axis = plt.subplots(figsize=(12, 8))
    axis.set(xlim=(-0.3, 12.6), ylim=(-0.6, 9.2))
    axis.axis("off")
    axis.text(
        0, 8.7, "Da Fase 2 à previsão de alfabetização", fontsize=20, color=NAVY, weight="bold"
    )
    box(axis, 0, 6.8, "Originais + Silver da Fase 2\nRegistros reais por aluno/ano")
    box(axis, 4.25, 6.8, "Auditoria e elegibilidade\nRótulo: proficiência ≥743")
    box(axis, 8.5, 6.8, "IBGE histórico\nPopulação e economia municipal")
    arrow(axis, (3.94, 7.32), (4.11, 7.32))
    box(axis, 4.25, 4.7, "Gold por aluno — adaptação\nAlvo, contexto e folds municipais")
    arrow(axis, (6.15, 6.65), (6.15, 5.9))
    arrow(axis, (10.4, 6.65), (7.3, 5.9))
    box(axis, 0, 2.6, "Modelo de referência 1.0\nTreino 2023 · teste temporal 2024")
    arrow(axis, (4.11, 4.85), (2.0, 3.8))
    box(axis, 8.5, 4.7, "Inep histórico — 2021\nTrês indicadores educacionais")
    box(axis, 8.5, 2.6, "Gold complementar — 2023\nEstudo exploratório de nove atributos")
    arrow(axis, (7.8, 4.55), (9.5, 3.8))
    arrow(axis, (10.4, 4.55), (10.4, 3.8))
    box(axis, 4.25, 0.5, "Gold municipal original da Fase 2\nReferências e metas")
    box(axis, 0, 0.5, "Análise territorial e de metas\nPosterior ao modelo")
    arrow(axis, (1.9, 2.45), (1.9, 1.7))
    arrow(axis, (4.11, 1.02), (3.94, 1.02))
    axis.text(
        8.5,
        1.3,
        "Comparação complementar somente em 2023.\nSem novo teste independente ou\npromoção automática do modelo.",
        color=GRAY,
        fontsize=10,
        va="top",
    )
    axis.text(
        0,
        -0.38,
        "André Mohallem Ferraz · FIAP Fase 3 · Contexto municipal × rede; sem vínculo escolar externo validado",
        fontsize=9,
        color=GRAY,
    )
    figure.tight_layout()
    for suffix in ("png", "svg"):
        options = {"metadata": {"Date": None}} if suffix == "svg" else {"dpi": 180}
        figure.savefig(ROOT / f"images/15_linhagem_gold.{suffix}", bbox_inches="tight", **options)
    plt.close(figure)


if __name__ == "__main__":
    main()
