"""Reprodução desde os oito arquivos de entrada, sem alterar a entrega congelada."""

import argparse
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import pandas as pd

from src.domain.contract import JsonObject
from src.infrastructure.files import FileStore
from src.usecase.baseline import run_baseline
from src.usecase.boosting import run_boosting
from src.usecase.eda import run_eda
from src.usecase.final_fit import FINAL_MODEL, FIT_REPORT, run_final_fit
from src.usecase.freeze import DECISION, TEST_GOLD
from src.usecase.logistic import run_logistic
from src.usecase.prepare import build_all_gold
from src.usecase.reproduce_boosting import without_timings
from src.usecase.temporal import PREDICTIONS, TEMPORAL_REPORT, run_temporal


def copy_input_snapshot(source: FileStore, target: FileStore) -> None:
    """Transfere somente entradas declaradas; exemplo: `copy_input_snapshot(src, dst)`."""
    for path in (source.root / "config").iterdir():
        if path.is_file():
            relative = "config/" + path.name
            target.copy_verified(path, relative, source.digest(relative))
    for entry in cast(list[JsonObject], source.read_json("config/snapshot.json")["files"]):
        relative = "data/input/" + str(entry["destination"])
        target.copy_verified(source.root / relative, relative, str(entry["sha256"]))


def compare_development(source: FileStore, computed: FileStore) -> None:
    """Compara resultados sem exigir tempos iguais; exemplo: `compare_development(src, computed)`."""
    for relative in ("reports/logistica_development.json", "reports/boosting_development.json"):
        assert without_timings(source.read_json(relative)) == without_timings(
            computed.read_json(relative)
        )
    for relative in ("reports/modelos_comparacao_2023.csv", "reports/boosting_busca_2023.csv"):
        pd.testing.assert_frame_equal(
            source.read_csv(relative).drop(columns=["fit_seconds", "predict_seconds"]),
            computed.read_csv(relative).drop(columns=["fit_seconds", "predict_seconds"]),
            check_exact=True,
        )


def assemble_frozen_inputs(source: FileStore, computed: FileStore, final: FileStore) -> None:
    """Combina dados recalculados com recibos históricos verificados; exemplo: `assemble_frozen_inputs(a,b,c)`."""
    decision = source.read_json(DECISION)
    final.copy_verified(source.root / DECISION, DECISION, source.digest(DECISION))
    for relative, expected in cast(JsonObject, decision["expected_sha256"]).items():
        owner = computed if relative.startswith(("data/", "artifacts/")) else source
        final.copy_verified(owner.root / relative, relative, str(expected))


def reproduce_all(source: FileStore) -> JsonObject:
    """Reconstroi Gold, desenvolvimento, ajuste e teste; exemplo: `reproduce_all(source)`."""
    with TemporaryDirectory(prefix="fiap-all-repro-") as directory:
        computed = FileStore(Path(directory) / "development")
        final = FileStore(Path(directory) / "frozen-final")
        copy_input_snapshot(source, computed)
        for name, operation in (
            ("gold", build_all_gold),
            ("eda", run_eda),
            ("baseline", run_baseline),
            ("logistic", run_logistic),
            ("boosting", run_boosting),
        ):
            operation(computed)
            print(f"Reprodução: {name} concluído", flush=True)
        compare_development(source, computed)
        assemble_frozen_inputs(source, computed, final)
        assert not (final.root / TEST_GOLD).exists()
        run_final_fit(final)
        assert not (final.root / TEST_GOLD).exists()
        final.copy_verified(
            computed.root / TEST_GOLD,
            TEST_GOLD,
            str(source.read_json(DECISION)["test_gold_sha256"]),
        )
        run_temporal(final)
        first, second = source.read_json(TEMPORAL_REPORT), final.read_json(TEMPORAL_REPORT)
        first.pop("evaluated_at_utc")
        second.pop("evaluated_at_utc")
        assert first == second
        hashes: JsonObject = {}
        for relative in (FINAL_MODEL, FIT_REPORT, PREDICTIONS, "reports/calibracao_teste_2024.csv"):
            assert source.digest(relative) == final.digest(relative), relative
            hashes[relative] = final.digest(relative)
    report: JsonObject = {
        "status": "passed",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "input_files": 8,
        "gold_rebuilt": True,
        "baseline_logistic_boosting_search_recomputed": True,
        "development_metrics_equal_excluding_times": True,
        "test_metrics_equal_excluding_timestamp": True,
        "decision_reselected": False,
        "test_absent_during_final_fit": True,
        "frozen_receipts": "Published development reports preserved after independent metric comparison; timestamps are historical provenance",
        "identical_final_files_sha256": hashes,
    }
    source.write_json("reports/reproducibilidade_completa.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(reproduce_all(FileStore(args.root)))


if __name__ == "__main__":
    main()
