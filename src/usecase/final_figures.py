"""Exporta figuras a partir das saídas congeladas, sem novos ajustes."""

from src.domain.contract import JsonObject
from src.infrastructure.files import FileStore
from src.usecase.freeze import DECISION, TEST_GOLD
from src.usecase.temporal import PREDICTIONS
from src.visualization.final import FinalPlots


def run_final_figures(store: FileStore) -> JsonObject:
    """Exporta seis figuras finais; exemplo: `run_final_figures(store)`."""
    plots = FinalPlots(store.root / "images")
    plots.threshold(
        store.read_csv("reports/limiar_f2_2023.csv"),
        float(store.read_json(DECISION)["risk_threshold"]),
    )
    plots.importance(store.read_csv("reports/importancia_permutacao_2023.csv"))
    test = store.read_parquet(TEST_GOLD)
    risk = store.read_parquet(PREDICTIONS)["p_nao_alfabetizado"].to_numpy()
    plots.temporal_curves(
        1 - test["alfabetizado"].to_numpy(),
        risk,
        store.read_csv("reports/calibracao_teste_2024.csv"),
    )
    plots.regions(store.read_csv("reports/regioes_teste_2024.csv"))
    plots.municipalities(store.read_csv("reports/municipios_risco_2024.csv"))
    plots.profiles(store.read_csv("reports/perfis_regionais_2023.csv"))
    return {"figures": 6, "model_refit": False}
