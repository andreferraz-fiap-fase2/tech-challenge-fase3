"""Reexecução com saídas vazias e somente Gold 2023 no mesmo ambiente fixado."""

import argparse
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.domain.contract import JsonObject
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.usecase.boosting import run_boosting

GOLD = "data/gold/ml_aluno/ano=2023/alunos.parquet"
REPORT = "reports/boosting_development.json"
TIMINGS = ["fit_seconds", "predict_seconds"]


def copy_development_inputs(source: FileStore, target: FileStore) -> None:
    config = source.read_json("config/experimento-boosting.json")
    paths = set(cast(JsonObject, config["expected_sha256"])) | {
        "config/experimento-boosting.json",
        "reports/logistica_development.json",
    }
    for relative in sorted(paths):
        target.copy_verified(source.root / relative, relative, source.digest(relative))


def without_timings(report: JsonObject) -> JsonObject:
    for model in cast(list[JsonObject], report["models"]):
        for fold in cast(list[JsonObject], model["folds"]):
            for name in TIMINGS:
                fold.pop(name)
    return report


def verify_outputs(source: FileStore, target: FileStore) -> JsonObject:
    assert without_timings(source.read_json(REPORT)) == without_timings(target.read_json(REPORT))
    for relative in ("reports/boosting_busca_2023.csv", "reports/modelos_comparacao_2023.csv"):
        pd.testing.assert_frame_equal(
            source.read_csv(relative).drop(columns=TIMINGS),
            target.read_csv(relative).drop(columns=TIMINGS),
            check_exact=True,
        )
    files = [
        "artifacts/boosting_amostra_2023.parquet",
        "artifacts/boosting_oof_2023.parquet",
        "reports/boosting_development.md",
    ]
    files += [
        f"artifacts/boosting/{variant}/fold_{fold}.joblib"
        for variant in ("rede_uf", "completa")
        for fold in (0, 1, 2)
    ]
    files += [
        f"images/{name}.{extension}"
        for name in ("07_comparacao_modelos_2023", "08_busca_boosting_2023")
        for extension in ("png", "svg")
    ]
    hashes: JsonObject = {}
    for relative in files:
        assert source.digest(relative) == target.digest(relative), f"Divergência: {relative}"
        hashes[relative] = target.digest(relative)
    return hashes


def verify_persisted_predictions(store: FileStore) -> int:
    frame = store.load_development()
    oof = store.read_parquet("artifacts/boosting_oof_2023.parquet")
    keys = ["ano", "id_aluno", "id_municipio", "fold_validacao"]
    pd.testing.assert_frame_equal(frame[keys], oof[keys])
    assert not oof.duplicated(["ano", "id_aluno"]).any()
    assert np.isfinite(oof.filter(like="p_risco")).all().all()
    models = ModelStore(store.root)
    for variant in ("rede_uf", "completa"):
        for fold in (0, 1, 2):
            sample = frame.loc[frame["fold_validacao"].eq(fold)].sample(100, random_state=42)
            pipeline = models.load(f"artifacts/boosting/{variant}/fold_{fold}.joblib")
            with threadpool_limits(limits=1):
                risk = pipeline.predict_proba(sample[list(pipeline.feature_names_in_)])[:, 0]
            assert list(pipeline.classes_) == [0, 1]
            np.testing.assert_allclose(
                risk, oof.loc[sample.index, f"p_risco_{variant}"], rtol=0, atol=1e-12
            )
    return len(oof)


def reproduce(source: FileStore) -> JsonObject:
    with TemporaryDirectory(prefix="fiap-boosting-repro-") as directory:
        target = FileStore(Path(directory))
        copy_development_inputs(source, target)
        assert not (target.root / "data/gold/ml_aluno/ano=2024").exists()
        run_boosting(target)
        hashes = verify_outputs(source, target)
        rows = verify_persisted_predictions(target)
        assert not (target.root / "data/gold/ml_aluno/ano=2024").exists()
    report: JsonObject = {
        "status": "passed",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Fresh outputs, same locked environment, only Gold 2023 present",
        "test_2024_gold_absent": True,
        "test_2024_evaluated": False,
        "configuration_metrics_search_selection_equality": "exact excluding elapsed times",
        "identical_files_sha256": hashes,
        "oof_rows": rows,
        "oof_unique_keys": True,
        "reloaded_models": 6,
        "sample_predictions_compared_per_model": 100,
        "serialization_probability_absolute_tolerance": 1e-12,
    }
    source.write_json("reports/boosting_reproducibility.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    report = reproduce(FileStore(args.root))
    print(
        f"Reprodução {report['status']}: {len(cast(JsonObject, report['identical_files_sha256']))} arquivos idênticos"
    )


if __name__ == "__main__":
    main()
