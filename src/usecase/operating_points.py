"""Exporta pontos de operação de 2023 sem retreinar nem tocar a decisão congelada."""

from src.domain.contract import JsonObject
from src.evaluation.operating_points import curve_prevalence, operating_points, trivial_f2
from src.infrastructure.files import FileStore

CURVE = "reports/limiar_f2_2023.csv"
DECISION = "config/modelo-final.json"
OUTPUT = "reports/pontos_operacao_2023.csv"


def run_operating_points(store: FileStore) -> JsonObject:
    """Lê a curva publicada e tabula por capacidade; exemplo: `run_operating_points(store)`."""
    curve = store.read_csv(CURVE)
    decision = store.read_json(DECISION)
    chosen = float(decision["risk_threshold"])  # type: ignore[arg-type]
    table = operating_points(curve, chosen)
    store.write_csv(OUTPUT, table)
    prevalence = curve_prevalence(curve)
    frozen = table.iloc[-1]
    return {
        "year": 2023,
        "source": CURVE,
        "prevalence": prevalence,
        "trivial_f2_flag_everyone": trivial_f2(prevalence),
        "frozen_threshold": chosen,
        "frozen_f2": float(frozen["f2"]),
        "frozen_flag_rate": float(frozen["flag_rate"]),
        "retrained": False,
        "test_2024_read": False,
        "changes_frozen_decision": False,
    }
