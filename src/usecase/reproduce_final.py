"""Repete ajuste e teste com a decisão já congelada, em saídas vazias."""

import argparse
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import numpy as np
import pandas as pd

from src.domain.contract import JsonObject
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.prediction import pipeline_risk
from src.usecase.final_fit import FINAL_MODEL, FIT_REPORT, run_final_fit
from src.usecase.freeze import DECISION, TEST_GOLD
from src.usecase.temporal import PREDICTIONS, TEMPORAL_REPORT, run_temporal


def reproduce_final(source: FileStore) -> JsonObject:
    """Replica o experimento congelado, sem nova seleção; exemplo: `reproduce_final(source)`."""
    decision = source.read_json(DECISION)
    with TemporaryDirectory(prefix="fiap-final-repro-") as directory:
        target = FileStore(Path(directory))
        for relative in [DECISION, *cast(JsonObject, decision["expected_sha256"])]:
            target.copy_verified(source.root / relative, relative, source.digest(relative))
        assert not (target.root / TEST_GOLD).exists()
        run_final_fit(target)
        assert not (target.root / TEST_GOLD).exists()
        target.copy_verified(source.root / TEST_GOLD, TEST_GOLD, source.digest(TEST_GOLD))
        run_temporal(target)
        original, repeated = source.read_json(TEMPORAL_REPORT), target.read_json(TEMPORAL_REPORT)
        original.pop("evaluated_at_utc")
        repeated.pop("evaluated_at_utc")
        assert original == repeated
        hashes: JsonObject = {}
        for relative in (FINAL_MODEL, FIT_REPORT, PREDICTIONS, "reports/calibracao_teste_2024.csv"):
            assert source.digest(relative) == target.digest(relative), relative
            hashes[relative] = target.digest(relative)
        frame = target.read_parquet(TEST_GOLD)
        predictions = target.read_parquet(PREDICTIONS)
        pd.testing.assert_frame_equal(
            frame[["ano", "id_aluno", "id_municipio"]],
            predictions[["ano", "id_aluno", "id_municipio"]],
        )
        sample = frame.sample(1000, random_state=42)
        risk = pipeline_risk(ModelStore(target.root).load(FINAL_MODEL), sample)
        np.testing.assert_allclose(
            risk, predictions.loc[sample.index, "p_nao_alfabetizado"], rtol=0, atol=1e-12
        )
    report: JsonObject = {
        "status": "passed",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "decision_sha256": source.digest(DECISION),
        "test_absent_during_final_training": True,
        "selection_repeated": False,
        "temporal_metrics_equality": "exact excluding execution timestamp",
        "identical_files_sha256": hashes,
        "test_rows": len(predictions),
        "reloaded_prediction_checks": 1000,
        "tolerance": 1e-12,
    }
    source.write_json("reports/reproducibilidade_final.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(reproduce_final(FileStore(args.root)))


if __name__ == "__main__":
    main()
