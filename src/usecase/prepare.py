"""Importação e construção reproduzível da Gold, com manifestos do snapshot."""

from pathlib import Path
from typing import cast

import pandas as pd

from src.domain.contract import ContractError, ExperimentContract, JsonObject, JsonValue
from src.infrastructure.files import FileStore
from src.preprocessing.context import combine_context, parse_pib, parse_population
from src.preprocessing.gold import build_gold


def import_snapshot(store: FileStore, source: Path) -> JsonObject:
    """Importa apenas arquivos explicitamente declarados; exemplo: `import_snapshot(store, apoio)`."""
    manifest = store.read_json("config/snapshot.json")
    for entry in cast(list[JsonObject], manifest["files"]):
        store.copy_verified(
            source / str(entry["source"]),
            "data/input/" + str(entry["destination"]),
            str(entry["sha256"]),
        )
    store.write_json("reports/snapshot_import.json", manifest)
    return {"imported_files": len(cast(list[JsonValue], manifest["files"]))}


def verify_snapshot(store: FileStore) -> None:
    """Recusa entradas modificadas após a importação; exemplo: `verify_snapshot(store)`."""
    manifest = store.read_json("config/snapshot.json")
    for entry in cast(list[JsonObject], manifest["files"]):
        path = "data/input/" + str(entry["destination"])
        actual = store.digest(path)
        if actual != entry["sha256"]:
            raise ContractError(f"Hash de {path}={actual}; esperado {entry['sha256']}")


def build_all_gold(store: FileStore) -> JsonObject:
    """Constrói os dois anos sem calcular métricas de teste; exemplo: `build_all_gold(store)`."""
    verify_snapshot(store)
    contract = ExperimentContract()
    contract.validate_definition(store.read_json("config/contrato-ml-aluno.json"))
    context = _historical_context(store)
    original = store.read_parquet("data/input/fase2/alunos-original.parquet")
    municipalities = store.read_parquet("data/input/fase2/diretorio_municipio.parquet")
    states = store.read_parquet("data/input/fase2/diretorio_uf.parquet")
    folds = store.read_csv("config/folds-municipios-2023.csv")
    audits: list[JsonValue] = []
    for year in (2023, 2024):
        silver = store.read_parquet(f"data/input/fase2/alunos-silver-{year}.parquet")
        result = build_gold(
            original, silver, context, municipalities, states, folds, year, contract
        )
        _save_gold(store, result.frame, year, contract)
        audits.append(result.audit)
    report: JsonObject = {
        "status": "gold_built_test_not_evaluated",
        "context_municipalities": len(context),
        "partitions": audits,
    }
    store.write_json("reports/gold_build.json", report)
    return report


def _historical_context(store: FileStore) -> pd.DataFrame:
    pib = parse_pib(
        store.read_archive_member("data/input/ibge/pib-municipios-2010-2020.zip", ".txt")
    )
    population = parse_population(
        store.read_archive_member("data/input/ibge/populacao-dou-2021.ods", "content.xml")
    )
    context = combine_context(pib, population)
    store.write_parquet("data/gold/contexto_municipal.parquet", context)
    return context


def _save_gold(
    store: FileStore, frame: pd.DataFrame, year: int, contract: ExperimentContract
) -> None:
    if len(frame) != contract.expected_rows(year):
        raise ContractError(
            f"Gold {year}={len(frame)} linhas; esperado {contract.expected_rows(year)}"
        )
    path = f"data/gold/ml_aluno/ano={year}/alunos.parquet"
    store.write_parquet(path, frame)
