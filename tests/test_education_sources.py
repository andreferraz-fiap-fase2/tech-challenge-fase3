"""Contratos de origem, temporalidade e integração das fontes educacionais."""

import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest
from openpyxl import Workbook

from src.domain.contract import ContractError
from src.infrastructure.education_sources import EducationSources, load_education_context
from src.infrastructure.files import FileStore
from src.preprocessing.education import (
    EDUCATION_FEATURES,
    combine_education_context,
    parse_education_xlsx,
)

HEADERS = [
    "NU_ANO_CENSO",
    "SG_UF",
    "CO_MUNICIPIO",
    "NO_CATEGORIA",
    "NO_DEPENDENCIA",
    "FUN_CAT_0",
    "FUN_AI_CAT_0",
    "FUN_AF_CAT_0",
]


def workbook_bytes(rows: list[list[object]], headers: list[str] | None = None) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "MUNICIPIO"
    sheet.append(["Título editorial"])
    sheet.append(HEADERS if headers is None else headers)
    for row in rows:
        sheet.append(row)
    sheet.append(["Fonte: Censo da Educação Básica 2021/INEP."])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_selects_initial_years_total_location_and_separate_networks() -> None:
    rows = [
        [2021, "RO", 1100015, "Total", "Municipal", 99, "20,5", 98],
        [2021, "RO", 1100015, "Total", "Estadual", 99, 23, 98],
        [2021, "RO", 1100015, "Urbana", "Municipal", 99, 70, 98],
        [2021, "RO", 1100015, "Total", "Pública", 99, 80, 98],
        [2021, "RO", 1100015, "Total", "Privada", 99, 90, 98],
    ]
    frame = parse_education_xlsx(workbook_bytes(rows), "ATU")
    assert frame["id_municipio"].tolist() == ["1100015", "1100015"]
    assert frame["rede_nome"].tolist() == ["Estadual", "Municipal"]
    assert frame[EDUCATION_FEATURES[0]].tolist() == [23.0, 20.5]


def test_keeps_unavailable_values_without_using_total_or_final_years() -> None:
    frame = parse_education_xlsx(
        workbook_bytes(
            [
                [2021, "RO", 1100015, "Total", "Estadual", 90, "--", 99],
                [2021, "RO", 1100015, "Total", "Municipal", 90, None, 99],
            ]
        ),
        "DSU",
    )
    assert frame[EDUCATION_FEATURES[1]].isna().all()


@pytest.mark.parametrize(
    ("position", "value", "error"),
    [
        (0, 2023, "Ano"),
        (1, "SP", "UF"),
        (2, 110001, "Código"),
        (3, "Ignorada", "Localização/rede"),
        (4, "Distrital", "Localização/rede"),
        (6, "texto", "não numérico"),
        (6, 100.1, "intervalo"),
        (6, float("inf"), "intervalo"),
    ],
)
def test_rejects_invalid_year_keys_categories_or_values(
    position: int, value: object, error: str
) -> None:
    row: list[object] = [2021, "RO", 1100015, "Total", "Municipal", 99, 90, 98]
    # XLSX cannot store infinity; a text marker exercises the same source failure.
    row[position] = "inf" if value == float("inf") else value
    with pytest.raises(ContractError, match=error):
        parse_education_xlsx(workbook_bytes([row]), "DSU")


def test_duplicate_municipality_network_is_blocked() -> None:
    row: list[object] = [2021, "RO", 1100015, "Total", "Municipal", 99, 90, 98]
    with pytest.raises(ContractError, match="duplicada"):
        parse_education_xlsx(workbook_bytes([row, row]), "DSU")


def test_missing_initial_years_header_does_not_fall_back_to_other_stage() -> None:
    headers = [name.replace("FUN_AI_CAT_0", "ETAPA_DESCONHECIDA") for name in HEADERS]
    with pytest.raises(ContractError, match="Anos Iniciais"):
        parse_education_xlsx(workbook_bytes([], headers), "ATU")


def test_context_outer_join_preserves_absent_network_and_prevents_row_multiplication() -> None:
    frames = {
        indicator: parse_education_xlsx(
            workbook_bytes([[2021, "RO", 1100015, "Total", network, 30, value, 35]]), indicator
        )
        for indicator, network, value in [
            ("ATU", "Municipal", 20),
            ("DSU", "Municipal", 90),
            ("HAD", "Estadual", 4.5),
        ]
    }
    result = combine_education_context(frames).set_index("rede_nome")
    assert len(result) == 2
    assert pd.isna(result.loc["Municipal", EDUCATION_FEATURES[2]])
    assert result.loc["Estadual", EDUCATION_FEATURES[2]] == 4.5
    frames["ATU"] = pd.concat([frames["ATU"], frames["ATU"]], ignore_index=True)
    with pytest.raises(ContractError, match="duplicada"):
        combine_education_context(frames)


def fixture_store(tmp_path: Path) -> FileStore:
    manifest = json.loads(Path("config/fontes-educacionais.json").read_text(encoding="utf-8"))
    for source in manifest["fontes"]:
        payload = workbook_bytes([[2021, "RO", 1100015, "Total", "Municipal", 30, 4, 35]])
        source["membro_bytes"] = len(payload)
        source["membro_sha256"] = hashlib.sha256(payload).hexdigest()
        archive_buffer = BytesIO()
        with ZipFile(archive_buffer, "w") as archive:
            archive.writestr(source["membro"], payload)
        archive_bytes = archive_buffer.getvalue()
        source["bytes"] = len(archive_bytes)
        source["sha256"] = hashlib.sha256(archive_bytes).hexdigest()
        target = tmp_path / source["caminho"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive_bytes)
    target = tmp_path / "config/fontes-educacionais.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest), encoding="utf-8")
    return FileStore(tmp_path)


def test_loader_checks_integrity_and_has_no_dependency_on_student_outcomes(tmp_path: Path) -> None:
    store = fixture_store(tmp_path)
    result = load_education_context(store)
    assert result.shape == (1, 5)
    assert result["rede_nome"].tolist() == ["Municipal"]
    source = store.root / "data/input/inep/ATU_2021_MUNICIPIOS.zip"
    source.write_bytes(source.read_bytes() + b"changed")
    with pytest.raises(ContractError, match="SHA-256"):
        load_education_context(store)


def test_rejects_publication_after_cutoff(tmp_path: Path) -> None:
    store = fixture_store(tmp_path)
    manifest = store.read_json("config/fontes-educacionais.json")
    manifest["fontes"][0]["publicado_em_pagina"] = "2023-01-01T00:00:00"
    store.write_json("config/fontes-educacionais.json", manifest)
    with pytest.raises(ContractError, match="posterior"):
        EducationSources(store)
